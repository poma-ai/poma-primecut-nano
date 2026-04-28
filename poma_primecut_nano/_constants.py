"""Shared constants for poma-memory."""

# Default token limit for chunk splitting (matches poma-core)
TOKEN_LIMIT = 500

# Default chunkset target size in tokens
CHUNKSET_TARGET_TOKENS = 512

# Ellipsis marker for non-contiguous chunks in cheatsheets.
# U+2026 inside brackets — canonical POMA display ellipsis. Matches
# poma-core (placeholders.ELLIPSIS_BRACKETED), poma-sdk, and poma-grill.
# Note: NFKC normalization decomposes "[…]" → "[...]"; that side effect is
# expected for embedding/BM25 inputs, not for display output like cheatsheets.
ELLIPSIS_MARKER = "[…]"
