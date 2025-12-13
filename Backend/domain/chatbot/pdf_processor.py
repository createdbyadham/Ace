"""
PDF processing utilities for RAG.

Handles PDF extraction, chunking, and embedding generation.
"""
from __future__ import annotations

import hashlib
import uuid
from typing import List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from core.config import settings


class PDFProcessor:
    """Processes PDFs into chunks for vector storage."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
    
    def extract_text(self, pdf_bytes: bytes) -> str:
        """Extract text content from PDF bytes."""
        from io import BytesIO
        
        reader = PdfReader(BytesIO(pdf_bytes))
        text_parts = []
        
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        return "\n\n".join(text_parts)
    
    def chunk_text(self, text: str, filename: str) -> Tuple[List[str], List[dict], List[str]]:
        """
        Split text into chunks with metadata.
        
        Returns:
            Tuple of (chunks, metadatas, ids)
        """
        chunks = self.text_splitter.split_text(text)
        
        # Generate document ID from content hash
        doc_hash = hashlib.md5(text.encode()).hexdigest()[:12]
        doc_id = f"doc_{doc_hash}"
        
        ids = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            ids.append(chunk_id)
            metadatas.append({
                "filename": filename,
                "document_id": doc_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
            })
        
        return chunks, metadatas, ids, doc_id
    
    def process_pdf(self, pdf_bytes: bytes, filename: str) -> Tuple[List[str], List[dict], List[str], str]:
        """
        Full pipeline: extract text from PDF and chunk it.
        
        Returns:
            Tuple of (chunks, metadatas, ids, document_id)
        """
        text = self.extract_text(pdf_bytes)
        if not text.strip():
            raise ValueError("PDF appears to be empty or contains no extractable text")
        
        return self.chunk_text(text, filename)


__all__ = ["PDFProcessor"]

