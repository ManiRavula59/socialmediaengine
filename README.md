🚀 Social Media Insight Engine - 500K Tweet Analysis with 4 Parallel LLMs

Full-stack RAG system processing 500K tweets with 4 AI models running in parallel (NVIDIA Nemotron, StepFun Flash, Arcee Trinity Large & Mini).

Architecture:

Backend: FastAPI + SQLite + ChromaDB vector store for semantic retrieval

RAG Pipeline: Retrieve relevant tweets → Augment prompts with real data → Generate via 4 parallel LLMs → Confidence scoring → Winner selection

Frontend: React + MUI + Chart.js dashboard with Model Arena (side-by-side model comparison)

Key Features:
✅ Sentiment analysis (VADER) - 83K tweets/sec
✅ Semantic search - understands meaning, not keywords
✅ Real-time crisis detection + trending hashtags
✅ Model Arena - 4 models respond simultaneously with confidence scores
✅ 500K tweets indexed in ChromaDB for RAG retrieval
✅ Async parallel LLM calls - 2.8s avg response

Tech: FastAPI, React, ChromaDB, Sentence-Transformers, OpenRouter API
