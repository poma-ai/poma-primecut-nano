# poma-primecut-nano

**Chunk markdown documents without losing structure.**

Most RAG chunkers split text by tokens, sentences, or paragraphs — then your retrieval returns orphaned fragments with no context. A paragraph about "rate limiting" arrives without its parent heading ("API Authentication"), so the LLM hallucinates the rest.

poma-primecut-nano chunks by **heading hierarchy** and returns **self-contained retrieval units** that carry their full ancestor path. Your search results read like compressed versions of the original document — not a pile of disconnected snippets.

```
pip install poma-primecut-nano
```

---

## The problem: fragment soup

Every RAG pipeline chunks documents. Most do it wrong:

```
Standard chunker output for "rate limiting" query:

  ❌ "Requests are limited to 100/minute per API key.
     Exceeding this limit returns HTTP 429."

  (What section? What API? What authentication model? Lost.)
```

```
poma-primecut-nano output for the same query:

  ✅ API Reference
       Authentication
         All endpoints require Bearer token authentication.
         [...]
         Rate Limiting
           Requests are limited to 100/minute per API key.
           Exceeding this limit returns HTTP 429.
```

The second result carries context. The first requires the LLM to guess.

---

## How it works

Three steps. You own the middle one (search).

### Step 1: Chunk your document

```python
from poma_primecut_nano import chunk

chunks = chunk(markdown_text)
```

One call. Each chunk has: `chunk_index`, `content`, `depth`, `parent_chunk_index`.

### Step 2: Build chunksets (retrieval units)

```python
from poma_primecut_nano import chunks_to_chunksets

chunksets = chunks_to_chunksets(chunks)
# Each chunkset is a root-to-leaf path through the heading tree.
# Use chunkset["to_embed"] for your embedding model.
# Store chunkset["chunk_ids"] alongside the vector.
```

A chunkset for a deeply nested paragraph includes its parent heading, grandparent section, and document title — all in one retrieval unit. When your vector DB returns this chunkset, the LLM gets complete context.

### Step 3: Assemble results from search hits

After your vector search returns matching chunk IDs:

```python
from poma_primecut_nano import expand_chunk_ids, assemble_context

# Expand hits to include ancestor headings
expanded = expand_chunk_ids(chunks, hit_chunk_ids)

# Assemble into readable text with [...] gap markers
context = assemble_context(chunks, expanded)
```

The output is a coherent cheatsheet — multiple hits from the same document merged with `[...]` gap markers between non-contiguous sections.

---

## Works with everything

poma-primecut-nano is a pure chunking + assembly library. It has no opinion on how you search, embed, or store — bring whatever you already use:

| Vector DB | Embedding | Framework |
|-----------|-----------|-----------|
| FAISS | OpenAI | LangChain |
| Chroma | Cohere | LlamaIndex |
| Qdrant | Voyage | Haystack |
| Pinecone | BGE-M3 | Vercel AI SDK |
| Weaviate | Jina | custom |
| TurboPuffer | model2vec | none needed |
| pgvector | any | any |

These are examples — any vector DB, any embedding model, any framework (or none) will work. The chunker produces plain Python dicts; the assembler takes plain lists of IDs.

**Integration pattern:**

```python
from poma_primecut_nano import chunk, chunks_to_chunksets, expand_chunk_ids, assemble_context

# === Indexing ===
chunks = chunk(document_text)
chunksets = chunks_to_chunksets(chunks)

for cs in chunksets:
    vector = your_embedding_model.embed(cs["to_embed"])
    your_vector_db.upsert(id=cs["chunkset_index"], vector=vector, metadata={
        "chunk_ids": cs["chunk_ids"],
        "file": "docs/api.md",
    })

# === Retrieval ===
query_vector = your_embedding_model.embed(user_query)
results = your_vector_db.search(query_vector, top_k=10)

# Collect all chunk IDs from matching chunksets
hit_ids = [cid for r in results for cid in r.metadata["chunk_ids"]]

# Expand + assemble (chunks must be stored/cached per file)
expanded = expand_chunk_ids(chunks, hit_ids)
context = assemble_context(chunks, expanded)

# Feed to LLM
answer = llm.complete(f"Based on this context:\n{context}\n\nQuestion: {user_query}")
```

---

## API reference

### Chunking

| Function | Input | Output |
|----------|-------|--------|
| `chunk(text)` | Raw markdown string | List of `{chunk_index, content, depth, parent_chunk_index}` |

### Chunkset building

| Function | Input | Output |
|----------|-------|--------|
| `chunks_to_chunksets(chunks)` | Chunks with parent links | List of `{chunkset_index, chunk_ids, contents, to_embed}` |
| `chunks_to_chunksets_optimized(chunks)` | Same | Fewer, more distinct chunksets (collapse/merge algorithm) |
| `build_ancestor_maps(chunks)` | Same | `(parent_map, ancestors_map)` dicts |

### Result assembly

| Function | Input | Output |
|----------|-------|--------|
| `expand_chunk_ids(chunks, hit_ids)` | All chunks + search hit IDs | Expanded IDs including ancestors |
| `expand_chunk_ids_deep(chunks, hit_ids)` | Same | Smarter expansion: deepest-unique + subtrees |
| `assemble_context(chunks, expanded_ids)` | All chunks + expanded IDs | Readable text with `[...]` gap markers |

### Utility

| Function | Input | Output |
|----------|-------|--------|
| `normalize_for_embedding(text)` | Raw text | Clean text for embedding (HTML strip, NFKC, whitespace) |

---

## Optimized chunksets

`chunks_to_chunksets()` is simple and predictable: one chunkset per leaf chunk, with ancestors prepended.

`chunks_to_chunksets_optimized()` produces fewer, more distinct chunksets using a collapse/merge/sibling-fill algorithm:

1. **Collapse** contiguous same-depth chunks into blocks within a token budget
2. **Merge** adjacent blocks upward when they fit together
3. **Fill** preceding sibling blocks for richer context
4. **Deduplicate** by removing subset chunksets

This reduces embedding costs (fewer vectors) while improving retrieval quality (each chunkset is more self-contained). Ported from [POMA](https://poma-ai.com)'s production pipeline.

---

## What this is (and isn't)

poma-primecut-nano is the **chunking and assembly layer** extracted from [POMA](https://poma-ai.com)'s document processing platform. It works best on structured markdown — headings, lists, code blocks, tables.

It does **not** include: search, vector storage, embeddings, or LLM integration. Those are your choices.

### Garbage in, garbage out

Chunking quality depends on input quality. If your markdown has flat walls of text with no headings, there's no hierarchy to preserve. For best results:

- Use well-structured markdown with heading levels (`#`, `##`, `###`)
- Keep lists and code blocks properly indented
- If you're processing raw documents (PDFs, Word, scans), you need an **ingestion step** first

[POMA PrimeCut](https://poma-ai.com) converts any document into clean, hierarchically structured markdown — the ideal input for this library. Available as cloud API (pay-as-you-go from €0.003/page) and on-prem.

### Related projects

- **[poma-memory](https://github.com/poma-ai/poma-memory)** — Persistent context for AI coding agents. Uses poma-primecut-nano under the hood, adds BM25 + semantic search, SQLite persistence, incremental indexing, and an MCP server for Claude Code.
- **[POMA PrimeCut](https://poma-ai.com)** — Production document processing: OCR, ML-powered structural analysis, format conversion. Cloud and on-prem.

## License

MIT
