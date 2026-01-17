"""Semantic chunking for RAG preparation."""
import hashlib
import re
from typing import List, Optional
import tiktoken
from models import Chunk
from config import config
from logger import setup_logger


logger = setup_logger("chunker")


class SemanticChunker:
    """Semantic chunking with heading awareness for RAG."""
    
    def __init__(self):
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        self.chunk_size = config.chunk_size_tokens
        self.overlap_tokens = int(self.chunk_size * config.chunk_overlap_percent / 100)
        
    def chunk(
        self,
        text: str,
        doc_id: str,
        source_url: str,
        content_type: str,
        section_path: List[str],
        metadata: dict
    ) -> List[Chunk]:
        """
        Chunk text with heading awareness and overlap.
        
        Args:
            text: Markdown text to chunk
            doc_id: Document ID
            source_url: Source URL
            content_type: Content type
            section_path: Section path
            metadata: Additional metadata
            
        Returns:
            List of chunks
        """
        # First, split by headings
        sections = self._split_by_headings(text)
        
        # Then chunk each section
        chunks = []
        position = 0
        
        for heading, content in sections:
            section_chunks = self._chunk_section(
                content,
                heading,
                doc_id,
                source_url,
                content_type,
                section_path,
                metadata,
                position
            )
            chunks.extend(section_chunks)
            position += len(section_chunks)
            
        # Deduplicate chunks
        chunks = self._deduplicate_chunks(chunks)
        
        logger.info(f"Created {len(chunks)} chunks from document {doc_id}")
        return chunks
        
    def _split_by_headings(self, text: str) -> List[tuple]:
        """
        Split text by markdown headings.
        
        Returns:
            List of (heading, content) tuples
        """
        sections = []
        lines = text.split("\n")
        
        current_heading = None
        current_content = []
        
        for line in lines:
            # Detect markdown headings
            if re.match(r'^#{1,6}\s+', line):
                # Save previous section
                if current_heading or current_content:
                    sections.append((
                        current_heading,
                        "\n".join(current_content)
                    ))
                    
                # Start new section
                current_heading = line.lstrip("#").strip()
                current_content = []
            else:
                current_content.append(line)
                
        # Save last section
        if current_heading or current_content:
            sections.append((
                current_heading,
                "\n".join(current_content)
            ))
            
        return sections
        
    def _chunk_section(
        self,
        content: str,
        heading: Optional[str],
        doc_id: str,
        source_url: str,
        content_type: str,
        section_path: List[str],
        metadata: dict,
        start_position: int
    ) -> List[Chunk]:
        """Chunk a single section with overlap."""
        chunks = []
        
        # Tokenize content
        tokens = self.encoding.encode(content)
        
        # If section fits in one chunk, return it
        if len(tokens) <= self.chunk_size:
            if len(tokens) >= config.min_chunk_size_tokens:
                chunk = self._create_chunk(
                    content,
                    heading,
                    doc_id,
                    source_url,
                    content_type,
                    section_path,
                    metadata,
                    start_position
                )
                chunks.append(chunk)
            return chunks
            
        # Otherwise, split with overlap
        start = 0
        position = start_position
        
        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            
            # Decode tokens back to text
            chunk_text = self.encoding.decode(chunk_tokens)
            
            # Create chunk
            if len(chunk_tokens) >= config.min_chunk_size_tokens:
                chunk = self._create_chunk(
                    chunk_text,
                    heading,
                    doc_id,
                    source_url,
                    content_type,
                    section_path,
                    metadata,
                    position
                )
                chunks.append(chunk)
                position += 1
                
            # Move start with overlap
            start = end - self.overlap_tokens
            
            # Prevent infinite loop
            if start >= end:
                break
                
        return chunks
        
    def _create_chunk(
        self,
        text: str,
        heading: Optional[str],
        doc_id: str,
        source_url: str,
        content_type: str,
        section_path: List[str],
        metadata: dict,
        position: int
    ) -> Chunk:
        """Create a chunk object."""
        # Generate chunk ID
        chunk_id = hashlib.sha256(
            f"{doc_id}_{position}_{text[:100]}".encode()
        ).hexdigest()
        
        return Chunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            source_url=source_url,
            content_type=content_type,
            section_path=section_path,
            text=text.strip(),
            anchor_heading=heading,
            position=position,
            event_date=metadata.get("event_date"),
            published_date=metadata.get("published_date"),
            date_range_start=metadata.get("date_range_start"),
            date_range_end=metadata.get("date_range_end"),
            entity_type=metadata.get("entity_type"),
            working_group=metadata.get("working_group"),
            metadata=metadata
        )
        
    def _deduplicate_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Remove near-duplicate chunks based on content hash."""
        seen_hashes = set()
        unique_chunks = []
        
        for chunk in chunks:
            # Create content hash (first 200 chars for similarity)
            content_hash = hashlib.md5(chunk.text[:200].encode()).hexdigest()
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_chunks.append(chunk)
            else:
                logger.debug(f"Filtered duplicate chunk: {chunk.chunk_id}")
                
        duplicates_removed = len(chunks) - len(unique_chunks)
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate chunks")
            
        return unique_chunks
