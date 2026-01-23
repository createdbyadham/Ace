"""
Ace Model - Fine-tuned LLM for educational content generation.

This module handles loading and inference with the khaled324/ace fine-tuned model
from HuggingFace, using Unsloth for optimized inference.

The model is trained to output JSON structured content for MCQs and flashcards.
"""
from __future__ import annotations

import json
import re
from typing import List, Optional
from functools import lru_cache

import torch


class AceModel:
    """
    Singleton wrapper for the fine-tuned Ace model.
    
    The model is loaded lazily on first use and cached for reuse.
    Requires GPU with CUDA support.
    """
    
    _instance: Optional["AceModel"] = None
    _model = None
    _tokenizer = None
    _initialized = False
    
    # Model configuration
    MODEL_NAME = "khaled324/ace"
    MAX_SEQ_LENGTH = 2048
    DTYPE = None  # Auto-detect
    LOAD_IN_4BIT = True
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _ensure_loaded(self):
        """Lazy load the model on first use."""
        if not self._initialized:
            self._load_model()
    
    def _load_model(self):
        """Load the fine-tuned model from HuggingFace."""
        try:
            from unsloth import FastLanguageModel
            
            self._model, self._tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.MODEL_NAME,
                max_seq_length=self.MAX_SEQ_LENGTH,
                dtype=self.DTYPE,
                load_in_4bit=self.LOAD_IN_4BIT,
            )
            
            FastLanguageModel.for_inference(self._model)
            self._initialized = True
            
        except ImportError as e:
            raise RuntimeError(
                "Unsloth is required for the Ace model. "
                "Install with: pip install unsloth"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to load Ace model: {e}") from e
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text from the fine-tuned model.
        
        Args:
            prompt: The formatted prompt string
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            Generated text response
        """
        self._ensure_loaded()
        
        inputs = self._tokenizer(prompt, return_tensors="pt").to("cuda")
        
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True if temperature > 0 else False,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        
        generated = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the response part (after the prompt)
        if prompt in generated:
            response = generated[len(prompt):].strip()
        else:
            # Try to find the response section
            response = generated
        
        return response
    
    def generate_mcq(
        self,
        text: str,
        num_questions: int,
        filename: str,
    ) -> List[dict]:
        """
        Generate MCQ questions from text content.
        
        Args:
            text: Source text content
            num_questions: Number of questions to generate
            filename: Source filename for reference
            
        Returns:
            List of question dictionaries
        """
        prompt = f"""Below is an instruction that describes a task.

### Instruction:
Based on the following educational content, create exactly {num_questions} multiple choice questions in JSON format.

Each question must have:
- "question": The question text
- "options": Array of exactly 4 answer options
- "correct_answer": Index (0-3) of the correct option
- "explanation": Brief explanation of the correct answer

### Input:
{text[:12000]}

### Response:
"""
        
        response = self.generate(prompt, max_new_tokens=3000, temperature=0.7)
        return self._parse_mcq_response(response, num_questions, filename)
    
    def generate_flashcards(
        self,
        text: str,
        num_cards: int,
        filename: str,
    ) -> List[dict]:
        """
        Generate flashcards from text content.
        
        Args:
            text: Source text content
            num_cards: Number of flashcards to generate
            filename: Source filename for reference
            
        Returns:
            List of flashcard dictionaries with 'front' and 'back' keys
        """
        prompt = f"""Below is an instruction that describes a task.

### Instruction:
Based on the following educational content, create exactly {num_cards} flashcards in JSON format.

Each flashcard must have:
- "front": A clear question or prompt
- "back": A concise, accurate answer

Focus on the most important concepts. Make questions specific with clear answers.

### Input:
{text[:12000]}

### Response:
"""
        
        response = self.generate(prompt, max_new_tokens=3000, temperature=0.7)
        return self._parse_flashcard_response(response, num_cards, filename)
    
    def _parse_mcq_response(
        self,
        response: str,
        num_questions: int,
        filename: str,
    ) -> List[dict]:
        """Parse MCQ JSON response from the model."""
        questions = self._extract_json_array(response)
        
        result = []
        for q in questions[:num_questions]:
            # Validate and normalize
            correct_idx = q.get("correct_answer", 0)
            if not isinstance(correct_idx, int) or correct_idx < 0 or correct_idx > 3:
                correct_idx = 0
            
            options = q.get("options", [])
            while len(options) < 4:
                options.append(f"Option {len(options) + 1}")
            options = options[:4]
            
            result.append({
                "question": q.get("question", ""),
                "options": options,
                "correct_answer": correct_idx,
                "explanation": q.get("explanation", ""),
                "source_file": filename,
            })
        
        return result
    
    def _parse_flashcard_response(
        self,
        response: str,
        num_cards: int,
        filename: str,
    ) -> List[dict]:
        """Parse flashcard JSON response from the model."""
        cards = self._extract_json_array(response)
        
        result = []
        for card in cards[:num_cards]:
            result.append({
                "front": card.get("front", ""),
                "back": card.get("back", ""),
                "source_file": filename,
            })
        
        return result
    
    def _extract_json_array(self, text: str) -> List[dict]:
        """Extract JSON array from model response."""
        # Try direct parse first
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # Remove markdown code blocks if present
        if "```" in text:
            # Find content between code blocks
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
        
        # Try to find JSON array in the text
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        # Last resort: try to find individual JSON objects
        objects = []
        for match in re.finditer(r'\{[^{}]*\}', text):
            try:
                obj = json.loads(match.group())
                objects.append(obj)
            except json.JSONDecodeError:
                continue
        
        if objects:
            return objects
        
        raise ValueError(f"Failed to parse JSON from model response: {text[:500]}")
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if the Ace model can be used (GPU + unsloth available)."""
        try:
            import torch
            if not torch.cuda.is_available():
                return False
            
            # Check if unsloth is installed
            import importlib.util
            if importlib.util.find_spec("unsloth") is None:
                return False
            
            return True
        except Exception:
            return False


# Singleton instance getter
def get_ace_model() -> AceModel:
    """Get the singleton Ace model instance."""
    return AceModel()


__all__ = ["AceModel", "get_ace_model"]
