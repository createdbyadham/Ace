"""
Main chatbot service with RAG integration.

Combines ChromaDB retrieval, LLM generation, and conversation memory.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import chromadb
from openai import OpenAI

from core.config import settings
from .embeddings import EmbeddingService, get_embedding_service
from .memory import MemoryManager, memory_manager
from .models import ChatResponse
from .vectorstore import get_vectorstore
from .pdf_processor import PDFProcessor


class ChatbotService:
    """
    RAG-enabled chatbot service.
    
    Features:
    - PDF document ingestion
    - Semantic search via ChromaDB
    - LLM-powered responses via GitHub Models
    - Sliding window conversation memory
    """
    
    def __init__(
        self,
        collection: Optional[chromadb.Collection] = None,
        embedding_service: Optional[EmbeddingService] = None,
        memory: Optional[MemoryManager] = None,
    ):
        self.collection = collection or get_vectorstore()
        self.embeddings = embedding_service or get_embedding_service()
        self.memory = memory or memory_manager
        self.pdf_processor = PDFProcessor()
        
        # Initialize OpenAI client for GitHub Models
        self.client = OpenAI(
            base_url=settings.llm_endpoint,
            api_key=settings.github_token,
        )
    
    def upload_pdf(self, pdf_bytes: bytes, filename: str) -> Tuple[int, str]:
        """
        Process and store a PDF document.
        
        Returns:
            Tuple of (chunks_created, document_id)
        """
        # Process PDF into chunks
        chunks, metadatas, ids, doc_id = self.pdf_processor.process_pdf(pdf_bytes, filename)
        
        # Generate embeddings
        embeddings = self.embeddings.embed(chunks)
        
        # Store in ChromaDB
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        
        return len(chunks), doc_id
    
    def _retrieve_context(self, query: str, n_results: int = 5) -> Tuple[str, List[str]]:
        """
        Retrieve relevant context from vector store.
        
        Returns:
            Tuple of (context_string, source_filenames)
        """
        # Check if collection has any documents
        if self.collection.count() == 0:
            return "", []
        
        # Generate query embedding
        query_embedding = self.embeddings.embed_single(query)
        
        # Search for similar documents
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, self.collection.count()),
            include=["documents", "metadatas"],
        )
        
        if not results["documents"] or not results["documents"][0]:
            return "", []
        
        # Build context string
        context_parts = []
        sources = set()
        
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            context_parts.append(doc)
            if meta and "filename" in meta:
                sources.add(meta["filename"])
        
        context = "\n\n---\n\n".join(context_parts)
        return context, list(sources)
    
    def _build_system_prompt(self, context: str, history: str) -> str:
        """Build the system prompt with context and history."""
        base_prompt = """You are a helpful AI assistant with access to a knowledge base of uploaded documents. 
Your goal is to provide accurate, helpful responses based on the available context.

Guidelines:
- If the user's question can be answered using the provided context, use that information.
- If the context doesn't contain relevant information, say so honestly and provide general knowledge if applicable.
- Be conversational and helpful.
- When citing information from documents, mention the source if possible."""

        parts = [base_prompt]
        
        if context:
            parts.append(f"\n\n## Relevant Document Context:\n{context}")
        
        if history:
            parts.append(f"\n\n## Previous Conversation:\n{history}")
        
        return "\n".join(parts)
    
    def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        Process a chat message and generate a response.
        
        Args:
            message: User's message
            session_id: Optional session ID for memory continuity
            
        Returns:
            ChatResponse with response, session_id, and sources
        """
        # Get or create session
        session_id, _ = self.memory.get_or_create_session(session_id)
        
        # Retrieve relevant context
        context, sources = self._retrieve_context(message)
        
        # Get conversation history
        history = self.memory.get_history_as_string(session_id)
        
        # Build system prompt
        system_prompt = self._build_system_prompt(context, history)
        
        # Call LLM
        response = self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        
        ai_response = response.choices[0].message.content
        
        # Save to memory
        self.memory.add_interaction(session_id, message, ai_response)
        
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            sources=sources,
        )
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a conversation session."""
        return self.memory.clear_session(session_id)
    
    def get_document_count(self) -> int:
        """Get the number of document chunks in the vector store."""
        return self.collection.count()


def get_chatbot_service() -> ChatbotService:
    """Dependency injection helper."""
    return ChatbotService()


__all__ = ["ChatbotService", "get_chatbot_service"]

