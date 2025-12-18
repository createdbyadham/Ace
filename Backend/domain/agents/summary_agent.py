"""
Summary Generation AI Agent.

Takes PDFs and generates summaries using AI, then saves them to the database.
"""
from __future__ import annotations

import json
from typing import List, Tuple
from uuid import UUID

import asyncpg
from openai import OpenAI

from core.config import settings
from domain.chatbot.pdf_processor import PDFProcessor


class GeneratedSummary:
    """A generated summary."""
    def __init__(
        self,
        title: str,
        content: str,
        key_points: List[str],
        source_file: str,
    ):
        self.title = title
        self.content = content
        self.key_points = key_points
        self.source_file = source_file
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "content": self.content,
            "key_points": self.key_points,
            "source_file": self.source_file,
        }


class SummaryGenerationResponse:
    """Response from summary generation."""
    def __init__(
        self,
        summary_id: UUID,
        title: str,
        content: str,
        key_points: List[str],
        source_files: List[str],
        word_count: int,
    ):
        self.summary_id = summary_id
        self.title = title
        self.content = content
        self.key_points = key_points
        self.source_files = source_files
        self.word_count = word_count
    
    def to_dict(self) -> dict:
        return {
            "summary_id": str(self.summary_id),
            "title": self.title,
            "content": self.content,
            "key_points": self.key_points,
            "source_files": self.source_files,
            "word_count": self.word_count,
        }


class SummaryAgent:
    """
    AI Agent that generates summaries from PDF documents.
    
    Features:
    - Extracts text from multiple PDFs
    - Uses AI to generate comprehensive summaries
    - Combines content from multiple documents intelligently
    - Creates summary in database with key points
    """
    
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool
        self.pdf_processor = PDFProcessor()
        self.client = OpenAI(
            base_url=settings.llm_endpoint,
            api_key=settings.github_token,
        )
    
    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        """Extract text from a single PDF."""
        return self.pdf_processor.extract_text(pdf_bytes)
    
    def _generate_summary_from_text(
        self,
        text: str,
        title: str,
        summary_length: str,
        source_files: List[str],
    ) -> GeneratedSummary:
        """Use AI to generate a summary from text content."""
        
        # Truncate text if too long (keep first ~20k chars for context window)
        max_chars = 20000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Content truncated...]"
        
        length_instructions = {
            "brief": "Create a brief summary of about 200-300 words.",
            "medium": "Create a detailed summary of about 500-700 words.",
            "detailed": "Create a comprehensive summary of about 1000-1500 words.",
        }
        
        length_guide = length_instructions.get(summary_length, length_instructions["medium"])
        
        prompt = f"""You are an expert educator creating a summary for students.

Based on the following lecture/document content, create a high-quality summary.

Requirements:
- {length_guide}
- Cover all the main topics and concepts
- Use clear, educational language
- Organize information logically
- Include 5-10 key points/takeaways
- Make it useful for study and review

The content comes from these files: {', '.join(source_files)}

Document content:
---
{text}
---

Return your response as a JSON object with these keys:
- "content": The full summary text (with proper paragraphs separated by \\n\\n)
- "key_points": An array of 5-10 key points/takeaways

Example format:
{{
  "content": "Machine learning is a subset of artificial intelligence...\\n\\nThe main types of machine learning include...",
  "key_points": [
    "Machine learning enables computers to learn from data",
    "Three main types: supervised, unsupervised, and reinforcement learning",
    "Common algorithms include decision trees, neural networks, and SVMs"
  ]
}}

Return ONLY the JSON object, no other text."""

        response = self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates educational summaries. Always respond with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=4000,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON response - handle markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])
        
        try:
            summary_data = json.loads(content)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                summary_data = json.loads(json_match.group())
            else:
                raise ValueError(f"Failed to parse AI response as JSON: {content[:200]}")
        
        return GeneratedSummary(
            title=title,  # Always use the user-provided title
            content=summary_data.get("content", ""),
            key_points=summary_data.get("key_points", []),
            source_file=", ".join(source_files),
        )
    
    async def generate_summary(
        self,
        owner_id: UUID,
        title: str,
        summary_length: str,
        pdf_files: List[Tuple[bytes, str]],  # List of (pdf_bytes, filename)
    ) -> SummaryGenerationResponse:
        """
        Main agent method: Generate summary from PDFs and save to database.
        
        Args:
            owner_id: User ID who will own the summary
            title: Title for the summary
            summary_length: 'brief', 'medium', or 'detailed'
            pdf_files: List of (pdf_bytes, filename) tuples
            
        Returns:
            SummaryGenerationResponse with summary info
        """
        if not pdf_files:
            raise ValueError("At least one PDF file is required")
        
        # Extract text from all PDFs and combine
        all_text_parts: List[str] = []
        source_files: List[str] = []
        
        for pdf_bytes, filename in pdf_files:
            source_files.append(filename)
            
            # Extract text
            text = self._extract_pdf_text(pdf_bytes)
            if not text.strip():
                raise ValueError(f"PDF '{filename}' contains no extractable text")
            
            all_text_parts.append(f"=== Content from {filename} ===\n\n{text}")
        
        # Combine all text
        combined_text = "\n\n".join(all_text_parts)
        
        # Generate summary
        summary = self._generate_summary_from_text(
            combined_text,
            title,
            summary_length,
            source_files,
        )
        
        # Calculate word count
        word_count = len(summary.content.split())
        
        # Save to database
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO public.summaries (owner_id, title, content, key_points, source_files, word_count)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING summary_id, owner_id, title, content, key_points, source_files, word_count, created_at
                """,
                owner_id,
                summary.title,
                summary.content,
                summary.key_points,
                source_files,
                word_count,
            )
        
        return SummaryGenerationResponse(
            summary_id=row["summary_id"],
            title=row["title"],
            content=row["content"],
            key_points=row["key_points"],
            source_files=row["source_files"],
            word_count=row["word_count"],
        )


__all__ = ["SummaryAgent", "GeneratedSummary", "SummaryGenerationResponse"]

