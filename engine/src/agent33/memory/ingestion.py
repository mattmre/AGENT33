"""Document ingestion with chunking strategies."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    """A single text chunk."""

    text: str
    index: int
    metadata: dict[str, str | int]


class DocumentIngester:
    """Splits documents into overlapping chunks for embedding."""

    def ingest_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> list[Chunk]:
        """Split *text* into character-count-based chunks with overlap."""
        if not text:
            return []

        chunks: list[Chunk] = []
        start = 0
        idx = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            chunks.append(
                Chunk(
                    text=chunk_text,
                    index=idx,
                    metadata={"start": start, "end": min(end, len(text))},
                )
            )
            idx += 1
            start += chunk_size - overlap
        return chunks

    def ingest_markdown(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> list[Chunk]:
        """Split markdown text respecting heading boundaries.

        Each heading starts a new section. Sections larger than
        *chunk_size* are further split using :meth:`ingest_text`.
        """
        if not text:
            return []

        # Split on markdown headings (lines starting with #).
        heading_pattern = re.compile(r"^(#{1,6}\s+.*)$", re.MULTILINE)
        parts = heading_pattern.split(text)

        # Reassemble into sections: heading + body pairs.
        sections: list[str] = []
        current = ""
        for part in parts:
            if heading_pattern.match(part):
                if current.strip():
                    sections.append(current.strip())
                current = part + "\n"
            else:
                current += part
        if current.strip():
            sections.append(current.strip())

        # Chunk each section.
        chunks: list[Chunk] = []
        idx = 0
        for section in sections:
            if len(section) <= chunk_size:
                chunks.append(
                    Chunk(
                        text=section,
                        index=idx,
                        metadata={"source": "markdown"},
                    )
                )
                idx += 1
            else:
                sub_chunks = self.ingest_text(section, chunk_size, overlap)
                for sc in sub_chunks:
                    sc.index = idx
                    sc.metadata["source"] = "markdown"
                    chunks.append(sc)
                    idx += 1
        return chunks
