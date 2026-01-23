"""
Flashcard Generation AI Agent.

Takes PDFs and generates flashcards using AI, then saves them to the database.
Supports both OpenAI API and the fine-tuned Ace model.
"""
from __future__ import annotations

import json
from typing import List, Literal, Tuple
from uuid import UUID

import asyncpg
from openai import OpenAI

from core.config import settings, ModelProvider
from domain.chatbot.pdf_processor import PDFProcessor
from .models import GeneratedCard, FlashcardGenerationResponse


class FlashcardAgent:
    """
    AI Agent that generates flashcards from PDF documents.
    
    Features:
    - Extracts text from multiple PDFs
    - Uses AI to generate high-quality flashcards
    - Supports both OpenAI API and fine-tuned Ace model
    - Distributes cards evenly across source documents
    - Creates deck and cards in database
    """
    
    def __init__(self, pool: asyncpg.Pool, model_provider: ModelProvider = "openai"):
        self._pool = pool
        self.pdf_processor = PDFProcessor()
        self.model_provider = model_provider
        
        # Initialize OpenAI client (always available as fallback)
        self.openai_client = OpenAI(
            base_url=settings.llm_endpoint,
            api_key=settings.github_token,
        )
        
        # Ace model is loaded lazily on demand
        self._ace_model = None
    
    @property
    def ace_model(self):
        """Lazy load Ace model when needed."""
        if self._ace_model is None:
            from domain.agents.ace_model import get_ace_model
            self._ace_model = get_ace_model()
        return self._ace_model
    
    def _extract_pdf_text(self, pdf_bytes: bytes, filename: str) -> str:
        """Extract text from a single PDF."""
        return self.pdf_processor.extract_text(pdf_bytes)
    
    def _calculate_cards_per_file(self, num_files: int, total_cards: int) -> List[int]:
        """
        Distribute cards evenly across files.
        
        Example: 10 cards, 3 files -> [4, 3, 3]
        """
        base_count = total_cards // num_files
        remainder = total_cards % num_files
        
        distribution = []
        for i in range(num_files):
            count = base_count + (1 if i < remainder else 0)
            distribution.append(count)
        
        return distribution
    
    def _generate_flashcards_from_text(
        self,
        text: str,
        num_cards: int,
        filename: str,
    ) -> List[GeneratedCard]:
        """
        Use AI to generate flashcards from text content.
        
        Uses the configured model provider (OpenAI or Ace).
        """
        if self.model_provider == "ace":
            return self._generate_flashcards_with_ace(text, num_cards, filename)
        else:
            return self._generate_flashcards_with_openai(text, num_cards, filename)
    
    def _generate_flashcards_with_ace(
        self,
        text: str,
        num_cards: int,
        filename: str,
    ) -> List[GeneratedCard]:
        """Generate flashcards using the fine-tuned Ace model."""
        cards_data = self.ace_model.generate_flashcards(text, num_cards, filename)
        
        cards = []
        for card_data in cards_data:
            cards.append(GeneratedCard(
                front=card_data["front"],
                back=card_data["back"],
                source_file=card_data.get("source_file", filename),
            ))
        
        return cards
    
    def _generate_flashcards_with_openai(
        self,
        text: str,
        num_cards: int,
        filename: str,
    ) -> List[GeneratedCard]:
        """Generate flashcards using OpenAI API."""
        # Truncate text if too long (keep first ~15k chars for context window)
        max_chars = 15000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Content truncated...]"
        
        prompt = f"""You are an expert educator creating flashcards for students.

Based on the following lecture/document content, create exactly {num_cards} high-quality flashcards.

Requirements:
- Each flashcard should test ONE specific concept, fact, or definition
- Front: A clear question or prompt
- Back: A concise, accurate answer
- Cover the most important concepts from the material
- Vary the types of questions (definitions, concepts, applications, comparisons)
- Make questions specific enough to have a clear answer
- Avoid yes/no questions

Document content:
---
{text}
---

Return your response as a JSON array with exactly {num_cards} objects, each with "front" and "back" keys.
Example format:
[
  {{"front": "What is photosynthesis?", "back": "The process by which plants convert sunlight, water, and CO2 into glucose and oxygen."}},
  {{"front": "What are the two stages of photosynthesis?", "back": "Light-dependent reactions and the Calvin cycle (light-independent reactions)."}}
]

Return ONLY the JSON array, no other text."""

        response = self.openai_client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates educational flashcards. Always respond with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=4000,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON response - handle markdown code blocks
        if content.startswith("```"):
            # Remove markdown code block
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])
        
        try:
            cards_data = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                cards_data = json.loads(json_match.group())
            else:
                raise ValueError(f"Failed to parse AI response as JSON: {content[:200]}")
        
        cards = []
        for card_data in cards_data[:num_cards]:  # Ensure we don't exceed requested count
            cards.append(GeneratedCard(
                front=card_data["front"],
                back=card_data["back"],
                source_file=filename,
            ))
        
        return cards
    
    async def generate_flashcards(
        self,
        owner_id: UUID,
        deck_title: str,
        deck_description: str | None,
        num_cards: int,
        pdf_files: List[Tuple[bytes, str]],  # List of (pdf_bytes, filename)
    ) -> FlashcardGenerationResponse:
        """
        Main agent method: Generate flashcards from PDFs and save to database.
        
        Args:
            owner_id: User ID who will own the deck
            deck_title: Title for the new deck
            deck_description: Optional description
            num_cards: Total number of cards to generate
            pdf_files: List of (pdf_bytes, filename) tuples
            
        Returns:
            FlashcardGenerationResponse with deck and card info
        """
        if not pdf_files:
            raise ValueError("At least one PDF file is required")
        
        # Calculate how many cards per file
        cards_per_file = self._calculate_cards_per_file(len(pdf_files), num_cards)
        
        # Extract text and generate cards from each PDF
        all_cards: List[GeneratedCard] = []
        source_files: List[str] = []
        
        for (pdf_bytes, filename), card_count in zip(pdf_files, cards_per_file):
            if card_count == 0:
                continue
                
            source_files.append(filename)
            
            # Extract text
            text = self._extract_pdf_text(pdf_bytes, filename)
            if not text.strip():
                raise ValueError(f"PDF '{filename}' contains no extractable text")
            
            # Generate cards
            cards = self._generate_flashcards_from_text(text, card_count, filename)
            all_cards.extend(cards)
        
        # Save to database
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                # Create deck
                deck_row = await conn.fetchrow(
                    """
                    INSERT INTO public.decks (owner_id, title, description)
                    VALUES ($1, $2, $3)
                    RETURNING deck_id, owner_id, title, created_at
                    """,
                    owner_id,
                    deck_title,
                    deck_description,
                )
                deck_id = deck_row["deck_id"]
                
                # Create cards - pass dict directly, asyncpg handles JSON encoding
                for card in all_cards:
                    content = {"front": card.front, "back": card.back}
                    await conn.execute(
                        """
                        INSERT INTO public.cards (deck_id, owner_id, content)
                        VALUES ($1, $2, $3)
                        """,
                        deck_id,
                        owner_id,
                        content,
                    )
        
        return FlashcardGenerationResponse(
            deck_id=deck_id,
            deck_title=deck_title,
            cards_created=len(all_cards),
            cards=all_cards,
            source_files=source_files,
            model_used=self.model_provider,
        )


__all__ = ["FlashcardAgent"]

