"""poma-primecut-nano: Hierarchical document chunking for RAG pipelines.

Chunk markdown documents while preserving heading structure.
Build self-contained retrieval units (chunksets) that carry full context.
Assemble readable output from search hits with gap markers.

Use any vector DB, any embedding model, any framework.
"""

__version__ = "0.1.0"

from poma_primecut_nano.chunker import indent_light as _indent_light
from poma_primecut_nano.tree import parse_indented_text as _parse, normalize_depths as _normalize
from poma_primecut_nano.chunksets import (
    chunks_to_chunksets,
    chunks_to_chunksets_optimized,
    build_ancestor_maps,
)
from poma_primecut_nano.retrieval import (
    expand_chunk_ids,
    expand_chunk_ids_deep,
    assemble_context,
)
from poma_primecut_nano.normalize import normalize_for_embedding


def chunk(text: str) -> list[dict]:
    """Chunk markdown text into depth-annotated, parent-linked chunks.

    This is the main entry point. Takes raw markdown, returns structured
    chunks preserving the full heading hierarchy.

    Args:
        text: Raw markdown string.

    Returns:
        List of dicts, each with:
            chunk_index (int): Position in document
            content (str): Chunk text
            depth (int): Heading depth (0 = root)
            parent_chunk_index (int | None): Parent chunk, or None for root
    """
    indented = _indent_light(text)
    chunks = _parse(indented)
    return _normalize(chunks)


__all__ = [
    # Step 1: Chunk
    "chunk",
    # Step 2: Build chunksets (retrieval units)
    "chunks_to_chunksets",
    "chunks_to_chunksets_optimized",
    "build_ancestor_maps",
    # Step 3: After YOUR search, assemble results
    "expand_chunk_ids",
    "expand_chunk_ids_deep",
    "assemble_context",
    # Utility
    "normalize_for_embedding",
]
