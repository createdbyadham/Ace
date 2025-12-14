"""
MCQ Question Generation AI Agent.

Takes PDFs and generates multiple choice questions using AI, then saves them to the database.
"""
from __future__ import annotations

import json
from typing import List, Tuple
from uuid import UUID

import asyncpg
from openai import OpenAI

from core.config import settings
from domain.chatbot.pdf_processor import PDFProcessor
from domain.questions.models import MCQOption


class GeneratedMCQ:
    """A generated MCQ question."""
    def __init__(
        self,
        question_text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        correct_answer: str,
        explanation: str,
        source_file: str,
    ):
        self.question_text = question_text
        self.option_a = option_a
        self.option_b = option_b
        self.option_c = option_c
        self.option_d = option_d
        self.correct_answer = correct_answer
        self.explanation = explanation
        self.source_file = source_file
    
    def to_dict(self) -> dict:
        return {
            "question_text": self.question_text,
            "option_a": self.option_a,
            "option_b": self.option_b,
            "option_c": self.option_c,
            "option_d": self.option_d,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "source_file": self.source_file,
        }


class MCQGenerationResponse:
    """Response from MCQ generation."""
    def __init__(
        self,
        set_id: UUID,
        set_title: str,
        questions_created: int,
        questions: List[GeneratedMCQ],
        source_files: List[str],
    ):
        self.set_id = set_id
        self.set_title = set_title
        self.questions_created = questions_created
        self.questions = questions
        self.source_files = source_files
    
    def to_dict(self) -> dict:
        return {
            "set_id": str(self.set_id),
            "set_title": self.set_title,
            "questions_created": self.questions_created,
            "questions": [q.to_dict() for q in self.questions],
            "source_files": self.source_files,
        }


class MCQAgent:
    """
    AI Agent that generates MCQ questions from PDF documents.
    
    Features:
    - Extracts text from multiple PDFs
    - Uses AI to generate high-quality MCQ questions
    - Distributes questions evenly across source documents
    - Creates question set and questions in database
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
    
    def _calculate_questions_per_file(self, num_files: int, total_questions: int) -> List[int]:
        """
        Distribute questions evenly across files.
        
        Example: 10 questions, 3 files -> [4, 3, 3]
        """
        base_count = total_questions // num_files
        remainder = total_questions % num_files
        
        distribution = []
        for i in range(num_files):
            count = base_count + (1 if i < remainder else 0)
            distribution.append(count)
        
        return distribution
    
    def _generate_mcq_from_text(
        self,
        text: str,
        num_questions: int,
        filename: str,
    ) -> List[GeneratedMCQ]:
        """Use AI to generate MCQ questions from text content."""
        
        # Truncate text if too long
        max_chars = 15000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Content truncated...]"
        
        prompt = f"""You are an expert educator creating multiple choice questions for students.

Based on the following lecture/document content, create exactly {num_questions} high-quality MCQ questions.

Requirements for each question:
- Question: A clear, specific question that tests understanding
- Four options (A, B, C, D): All plausible, but only ONE is correct
- Correct Answer: The letter of the correct option (A, B, C, or D)
- Explanation: Brief explanation of why the correct answer is right

Guidelines:
- Test important concepts, not trivial details
- Make wrong options plausible (not obviously wrong)
- Avoid "all of the above" or "none of the above"
- Questions should have only ONE clearly correct answer
- Vary difficulty levels

Document content:
---
{text}
---

Return your response as a JSON array with exactly {num_questions} objects.
Each object must have these keys: "question", "option_a", "option_b", "option_c", "option_d", "correct_answer", "explanation"

Example format:
[
  {{
    "question": "What is the primary function of mitochondria?",
    "option_a": "Protein synthesis",
    "option_b": "Energy production (ATP)",
    "option_c": "Cell division",
    "option_d": "Waste removal",
    "correct_answer": "B",
    "explanation": "Mitochondria are known as the powerhouse of the cell because they produce ATP through cellular respiration."
  }}
]

Return ONLY the JSON array, no other text."""

        response = self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates educational MCQ questions. Always respond with valid JSON."},
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
            questions_data = json.loads(content)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                questions_data = json.loads(json_match.group())
            else:
                raise ValueError(f"Failed to parse AI response as JSON: {content[:200]}")
        
        questions = []
        for q_data in questions_data[:num_questions]:
            # Validate correct_answer
            correct = q_data.get("correct_answer", "A").upper()
            if correct not in ["A", "B", "C", "D"]:
                correct = "A"  # Default fallback
            
            questions.append(GeneratedMCQ(
                question_text=q_data["question"],
                option_a=q_data["option_a"],
                option_b=q_data["option_b"],
                option_c=q_data["option_c"],
                option_d=q_data["option_d"],
                correct_answer=correct,
                explanation=q_data.get("explanation", ""),
                source_file=filename,
            ))
        
        return questions
    
    async def generate_questions(
        self,
        owner_id: UUID,
        set_title: str,
        set_description: str | None,
        num_questions: int,
        pdf_files: List[Tuple[bytes, str]],  # List of (pdf_bytes, filename)
    ) -> MCQGenerationResponse:
        """
        Main agent method: Generate MCQ questions from PDFs and save to database.
        
        Args:
            owner_id: User ID who will own the question set
            set_title: Title for the new question set
            set_description: Optional description
            num_questions: Total number of questions to generate
            pdf_files: List of (pdf_bytes, filename) tuples
            
        Returns:
            MCQGenerationResponse with set and question info
        """
        if not pdf_files:
            raise ValueError("At least one PDF file is required")
        
        # Calculate how many questions per file
        questions_per_file = self._calculate_questions_per_file(len(pdf_files), num_questions)
        
        # Extract text and generate questions from each PDF
        all_questions: List[GeneratedMCQ] = []
        source_files: List[str] = []
        
        for (pdf_bytes, filename), question_count in zip(pdf_files, questions_per_file):
            if question_count == 0:
                continue
                
            source_files.append(filename)
            
            # Extract text
            text = self._extract_pdf_text(pdf_bytes)
            if not text.strip():
                raise ValueError(f"PDF '{filename}' contains no extractable text")
            
            # Generate questions
            questions = self._generate_mcq_from_text(text, question_count, filename)
            all_questions.extend(questions)
        
        # Save to database
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                # Create question set
                set_row = await conn.fetchrow(
                    """
                    INSERT INTO public.question_sets (owner_id, title, description)
                    VALUES ($1, $2, $3)
                    RETURNING set_id, owner_id, title, created_at
                    """,
                    owner_id,
                    set_title,
                    set_description,
                )
                set_id = set_row["set_id"]
                
                # Create questions
                for q in all_questions:
                    await conn.execute(
                        """
                        INSERT INTO public.questions 
                            (set_id, owner_id, question_text, option_a, option_b, option_c, option_d,
                             correct_answer, explanation, source_file)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        """,
                        set_id,
                        owner_id,
                        q.question_text,
                        q.option_a,
                        q.option_b,
                        q.option_c,
                        q.option_d,
                        q.correct_answer,
                        q.explanation,
                        q.source_file,
                    )
        
        return MCQGenerationResponse(
            set_id=set_id,
            set_title=set_title,
            questions_created=len(all_questions),
            questions=all_questions,
            source_files=source_files,
        )


__all__ = ["MCQAgent", "GeneratedMCQ", "MCQGenerationResponse"]

