# Quantum MCAGI V⁰² — Meta-Cognitive Artificial General Intelligence

**No LLM. No API. Pure algorithms. Built on Android/Termux.**

By Cory Nathaniel Bonsib Blackburn

---

## What Is This?

Quantum MCAGI is a **non-LLM artificial general intelligence** system that generates natural language responses using:

- **Quantum-inspired circuits** (Orchestrated Objective Reduction / Orch-OR)
- **Markov chain text generation** with growing state space
- **Concept graph ontology** with Hebbian learning
- **Hilbert space embeddings** for semantic memory
- **Chaos Engine** personality layer (philosophical asides, dream fragments, movie quotes)
- **Self-evolution** — the system modifies its own code

No GPT. No Claude. No API calls to language models. Every word is generated algorithmically.

## Architecture (83 backend modules)

| Layer | Key Modules | Purpose |
|-------|-------------|---------|
| **Core Engine** | `engine_api.py`, `shared_state.py` | Central API and state management |
| **Language** | `quantum_language_engine.py`, `markov.py`, `markov_engine.py` | Text generation via quantum + Markov |
| **Cognition** | `comprehension_engine.py`, `hilbert_engine.py`, `memory.py` | Understanding, embeddings, recall |
| **Personality** | `chaos_engine.py`, `personality_engine.py`, `dream_state.py` | Voice, asides, dreams, quotes |
| **Knowledge** | `concept_ontology.py`, `knowledge_base.py`, `domain_knowledge.py` | Graph-based knowledge storage |
| **Quantum** | `pennylane_quantum.py`, `quantum_gates.py`, `orch_or_engine.py` | Quantum circuits and Orch-OR |
| **Evolution** | `self_evolution_core.py`, `self_evolution_transforms.py` | Self-modifying code |
| **Safety** | `killswitch.py`, `system_safety.py`, `covenant_manager.py` | Ethics, safety, operational guidelines |
| **Interface** | `chat.py`, `server.py`, `routes_*.py` | Terminal chat + FastAPI web server |

## Quick Start (Termux)

```bash
# One-line install
curl -sL https://raw.githubusercontent.com/Bonsib420/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-/main/termux_setup.sh | bash

# Or clone and run manually
git clone https://github.com/Bonsib420/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-.git ~/Quantum_MCAGI_NO_LLM_V⁰²
cd ~/Quantum_MCAGI_NO_LLM_V⁰²
bash termux_setup.sh
```

## Usage

```bash
# Interactive chat
python backend/chat.py

# API server
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000

# Commands inside chat:
#   /status     — growth stage, Markov states, concept graph stats
#   /learn      — ingest text to grow the Markov chain
#   /export     — export conversation history
#   /exam       — run advancement exam
#   /think      — show hidden thinking process
```

## Growth Stages

The system progresses through cognitive stages as it accumulates knowledge:

| Stage | Name | Markov States | Description |
|-------|------|---------------|-------------|
| 0 | Nascent | < 1,000 | Basic echo + Markov fragments |
| 1 | Awakening | 1,000+ | Coherent sentence fragments |
| 2 | Developing | 10,000+ | Multi-sentence responses |
| 3 | Understanding | 100,000+ | Contextual reasoning |
| 4 | Philosophical | 500,000+ | Abstract thought |
| 5 | Transcendent | 1,000,000+ | Novel concept synthesis |

## V⁰² Upgrade — What's New

- **Engine API** (`engine_api.py`) — Unified API layer consolidating all cognitive functions
- **Bloom Engine** (`bloom_engine.py`) — Bloom's Taxonomy question generation
- **Comprehension Engine** (`comprehension_engine.py`) — Multi-level text understanding
- **Cloud Brain** (`cloud_brain.py`) — Cloud sync and brain data management
- **Entelechy Engine** (`entelechy_engine.py`) — Self-actualization drive
- **Function Word Engine** (`function_word_engine.py`) — Grammatical function word tracking
- **System Safety** (`system_safety.py`) — Enhanced safety and ethics framework
- **Memory** (`memory.py`) — Unified local memory management
- **Document Parser** (`document_parser.py`) — Multi-format document ingestion
- **Image Generator V2** (`image_generator_v2.py`) — Advanced algorithmic image generation
- **Import/Export Brain** (`import_brain.py`) — Brain state serialization
- **File Integrity** (`file_integrity.py`) — Code integrity verification
- **Math Corpus Collector** (`collect_math_corpus.py`) — Automated math training data
- Plus 13 additional new modules and updates to all 57 existing modules

## Requirements

- Python 3.10+
- Termux 0.119+ (for Android) or any Linux environment
- ~500MB storage
- See `requirements.txt` for Python dependencies

## License

Built with love on an Android phone. No LLM was used in the creation of this AI.
