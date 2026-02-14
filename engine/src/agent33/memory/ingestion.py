"""Document ingestion with chunking strategies.

Provides both character-based and token-aware chunking.  The
:class:`TokenAwareChunker` estimates token counts using a word-based
heuristic (``words * 1.3``) and preserves sentence boundaries when
splitting, producing higher-quality chunks for embedding.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

# ── Sentence-boundary regex ──────────────────────────────────────────

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def _estimate_tokens(text: str) -> int:
    """Estimate token count using a word-based heuristic (words * 1.3)."""
    return math.ceil(len(text.split()) * 1.3)


@dataclass
class Chunk:
    """A single text chunk."""

    text: str
    index: int
    metadata: dict[str, str | int]


# ── Character-based chunking (legacy) ────────────────────────────────


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


# ── Token-aware chunking ─────────────────────────────────────────────


class TokenAwareChunker:
    """Token-aware text chunker with sentence boundary preservation.

    Unlike :class:`DocumentIngester` which uses raw character counts,
    this chunker estimates token counts and tries to split at sentence
    boundaries for higher-quality chunks suitable for embedding.

    Parameters
    ----------
    chunk_tokens:
        Target number of tokens per chunk (default 1200).
    overlap_tokens:
        Number of overlapping tokens between adjacent chunks (default 100).
    """

    def __init__(
        self,
        chunk_tokens: int = 1200,
        overlap_tokens: int = 100,
    ) -> None:
        self._chunk_tokens = max(1, chunk_tokens)
        self._overlap_tokens = min(overlap_tokens, chunk_tokens // 2)

    def chunk_text(self, text: str) -> list[Chunk]:
        """Split *text* into token-aware chunks with sentence preservation."""
        if not text or not text.strip():
            return []

        sentences = _SENTENCE_BOUNDARY.split(text)
        chunks: list[Chunk] = []
        current_sentences: list[str] = []
        current_tokens = 0
        idx = 0
        char_offset = 0

        for sentence in sentences:
            sentence_tokens = _estimate_tokens(sentence)

            # If a single sentence exceeds the limit, force-split it.
            if sentence_tokens > self._chunk_tokens and not current_sentences:
                forced = self._force_split(sentence, idx, char_offset)
                chunks.extend(forced)
                idx += len(forced)
                char_offset += len(sentence) + 1  # +1 for the split whitespace
                continue

            # Adding this sentence would exceed the chunk limit.
            if current_tokens + sentence_tokens > self._chunk_tokens and current_sentences:
                chunk_text = " ".join(current_sentences)
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        index=idx,
                        metadata={
                            "start_char": char_offset - len(chunk_text),
                            "tokens_est": current_tokens,
                            "strategy": "token_aware",
                        },
                    )
                )
                idx += 1

                # Keep overlap: walk backwards through sentences until
                # we have enough tokens for the overlap window.
                overlap_sents: list[str] = []
                overlap_tok = 0
                for prev in reversed(current_sentences):
                    prev_tok = _estimate_tokens(prev)
                    if overlap_tok + prev_tok > self._overlap_tokens:
                        break
                    overlap_sents.insert(0, prev)
                    overlap_tok += prev_tok

                current_sentences = overlap_sents
                current_tokens = overlap_tok

            current_sentences.append(sentence)
            current_tokens += sentence_tokens
            char_offset += len(sentence) + 1

        # Flush remaining sentences.
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(
                Chunk(
                    text=chunk_text,
                    index=idx,
                    metadata={
                        "start_char": max(0, char_offset - len(chunk_text) - 1),
                        "tokens_est": current_tokens,
                        "strategy": "token_aware",
                    },
                )
            )

        return chunks

    def chunk_markdown(self, text: str) -> list[Chunk]:
        """Split markdown text respecting heading boundaries.

        Each heading starts a new section.  Sections larger than the
        configured token limit are further split via :meth:`chunk_text`.
        """
        if not text or not text.strip():
            return []

        heading_pattern = re.compile(r"^(#{1,6}\s+.*)$", re.MULTILINE)
        parts = heading_pattern.split(text)

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

        chunks: list[Chunk] = []
        idx = 0
        for section in sections:
            section_tokens = _estimate_tokens(section)
            if section_tokens <= self._chunk_tokens:
                chunks.append(
                    Chunk(
                        text=section,
                        index=idx,
                        metadata={
                            "source": "markdown",
                            "tokens_est": section_tokens,
                            "strategy": "token_aware",
                        },
                    )
                )
                idx += 1
            else:
                sub_chunks = self.chunk_text(section)
                for sc in sub_chunks:
                    sc.index = idx
                    sc.metadata["source"] = "markdown"
                    chunks.append(sc)
                    idx += 1
        return chunks

    # ── Internal ─────────────────────────────────────────────────────

    def _force_split(
        self,
        text: str,
        start_idx: int,
        char_offset: int,
    ) -> list[Chunk]:
        """Split text that is too long for a single chunk by word boundaries."""
        words = text.split()
        chunks: list[Chunk] = []
        current_words: list[str] = []
        current_tokens = 0
        idx = start_idx

        for word in words:
            word_tokens = _estimate_tokens(word)
            if current_tokens + word_tokens > self._chunk_tokens and current_words:
                chunk_text = " ".join(current_words)
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        index=idx,
                        metadata={
                            "start_char": char_offset,
                            "tokens_est": current_tokens,
                            "strategy": "token_aware_forced",
                        },
                    )
                )
                idx += 1
                char_offset += len(chunk_text) + 1
                current_words = []
                current_tokens = 0

            current_words.append(word)
            current_tokens += word_tokens

        if current_words:
            chunk_text = " ".join(current_words)
            chunks.append(
                Chunk(
                    text=chunk_text,
                    index=idx,
                    metadata={
                        "start_char": char_offset,
                        "tokens_est": current_tokens,
                        "strategy": "token_aware_forced",
                    },
                )
            )

        return chunks
