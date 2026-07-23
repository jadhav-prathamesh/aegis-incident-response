# Regeneration Prompt: Contest AI Solution

## Objective

Regenerate the AI Solution document (`contest/source/Contest_AI_Solution.md`) from the codebase's AI/ML components.

## Inputs

- `src/agents/base.py` — LLM agent base, StateGraph, tools
- `src/agents/orchestrator.py` — LLM decision-making
- `src/agents/planner.py` — LLM structured output planning
- `src/core/embeddings.py` — Embedding service
- `src/core/vector_db.py` — Vector similarity search
- `src/core/knowledge_base.py` — Hybrid search (vector + lexical)

## Generation Instructions

1. Analyse the LLM integration:
   - Which LLM provider is used? (OpenRouter, local fallback)
   - What model is configured? (default: qwen2.5-32b-instruct)
   - How is the LLM invoked? (structured output, tool calling)
   - What is the fallback when LLM is unavailable? (rule-based)
2. Analyse the embedding approach:
   - Provider: OpenRouter or Sentence Transformers
   - Default model: text-embedding-3-small
   - Fallback: local transformer model
3. Analyse vector search:
   - Supported backends: ChromaDB, pgvector
   - Search methods: similarity, threshold
4. Document the machine learning pipeline:
   - Not implemented (Future Enhancement)
5. Output structured document with sections: AI Architecture, LLM Integration, Embeddings, Vector Search, Fallback Mechanisms, Limitations

## Verification

- [ ] LLM provider and model match config defaults
- [ ] Fallback mechanisms are accurately described
- [ ] Missing ML pipeline is clearly marked as not implemented
- [ ] No fabricated AI capabilities
