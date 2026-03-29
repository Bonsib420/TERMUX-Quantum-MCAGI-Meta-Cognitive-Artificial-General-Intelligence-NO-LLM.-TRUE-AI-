# 🔮 Quantum MCAGI — Project Context for Claude

> **Purpose:** This document is the living briefing for Claude (and other AIs helping with development).
> Copy-paste this into Claude at the start of any conversation about this project.
> Auto-generated via `GET /api/dev/context` or the "📋 Dev Context" button.

---

## What Is This Project?

**Quantum MCAGI** (Meta-Cognitive Artificial General Intelligence) is a **true AI system built without LLMs**.
It runs on **Termux (Android)** — the developer works exclusively from a **Motorola Razr Ultra 2025** with no computer.

### Core Architecture
- **Backend:** FastAPI server with 83 Python modules
- **Frontend:** React/Vite SPA with Capacitor for Android APK
- **Quantum:** PennyLane quantum computing (via venv on Termux)
- **Consciousness:** Penrose Orch-OR model (`orch_or_core.py`)
- **Language:** Markov chain generation (no LLM dependency)
- **Self-Evolution:** Autonomous code modification (`self_evolution_core.py`)
- **Knowledge:** Wolfram Alpha/Cloud integration, autonomous research
- **Memory:** MongoDB (motor) with semantic, episodic, procedural, philosophical stores

### Key Dependencies
- PennyLane (quantum circuits) — requires venv for Termux/APK compatibility
- Wolfram Alpha / Wolfram Cloud (external knowledge)
- MongoDB (memory persistence)

---

## Growth Metrics (12-Track Simultaneous Advancement)

All tracks must be met simultaneously to advance. High watermark protection on diameter and avg_degree.

| Stage | Connections | Concepts | Avg Degree | Diameter | Domains | Markov States | Transitions | Comm Score | Questions | Insights | Interactions |
|-------|-------------|----------|------------|----------|---------|---------------|-------------|------------|-----------|----------|--------------|
| Nascent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Curious | 50 | 20 | 1.5 | 3 | 3 | 5,000 | 10,000 | 15 | 50 | 10 | 25 |
| Inquisitive | 200 | 50 | 2.5 | 6 | 6 | 20,000 | 80,000 | 25 | 200 | 50 | 100 |
| Understanding | 500 | 100 | 3.5 | 8 | 10 | 100,000 | 400,000 | 35 | 500 | 150 | 300 |
| Philosophical | 1,500 | 200 | 5.0 | 12 | 15 | 400,000 | 1,500,000 | 50 | 1,000 | 400 | 750 |
| Theory Building | 4,000 | 350 | 7.0 | 16 | 20 | 800,000 | 3,000,000 | 65 | 2,500 | 1,000 | 2,000 |
| Transcendent | 10,000 | 600 | 10.0 | 20 | 30 | 1,500,000 | 6,000,000 | 80 | 6,000 | 3,000 | 5,000 |

Defined in: `backend/quantum_cognitive_core.py` (GrowthTracker.GROWTH_STAGES) and `backend/chat.py` (LocalMemory.GROWTH_STAGES)

---

## Development Changelog

### 2026-03-29 — Growth Metrics + Chat Export
- Expanded growth stages from 5-column to 12-column (added markov_states, transitions, comm_score, questions, insights, interactions)
- All 12 tracks must be met simultaneously to advance
- High watermark protection on diameter and avg_degree — earned progress never regresses
- Added chat export endpoints: `GET /api/chat/export/{session_id}`, `GET /api/chat/export-current`
- Added "📤 Share w/ Claude" button in ChatInterface.jsx (copies markdown to clipboard)
- Added `/export` slash command

### 2026-03-29 — Project Context + Dev Export
- Created PROJECT_CONTEXT.md (this file) — living briefing document for Claude
- Added `GET /api/dev/context` endpoint — auto-generates current project state as markdown
- Added "📋 Dev Context" button in ChatInterface.jsx for quick project context copy
- Added dev changelog tracking in routes_extras.py

---

## Backend Modules (83 files)

### Core Cognitive
- `quantum_cognitive_core.py` — GrowthTracker + QuantumCognitiveCore (main integration)
- `quantum_core.py` — SemanticMemory, EpisodicMemory, ProceduralMemory, PhilosophicalMemory
- `unified_cognitive_engine.py` / `_pt2.py` — Unified cognitive processing
- `knowledge_base.py` — Knowledge management

### Language Generation (No LLM)
- `quantum_language_engine.py` — Markov chain + concept extraction + response composition
- `quantum_language_generator.py` — Text generation
- `quantum_language_composers.py` — Response composition
- `quantum_language_vocabulary.py` — Vocabulary management
- `quantum_grammar_engine.py` — Grammar rules
- `training_corpus.py` — Corpus management

### Quantum Computing
- `pennylane_quantum.py` — PennyLane quantum circuit integration
- `quantum_brain.py` / `unified_quantum_brain.py` — Quantum processing
- `quantum_gates.py` — Gate operations
- `quantum_integration.py` — Integration layer
- `xanadu_prebo.py` — Photochemistry simulation

### Consciousness (Orch-OR)
- `orch_or_core.py` — Penrose Orchestrated Objective Reduction
- `orch_or_integration.py` — Integration with cognitive core

### Self-Evolution
- `self_evolution_core.py` — Core evolution engine
- `self_evolution_runner.py` — Evolution execution
- `self_evolution_analysis.py` — Code analysis
- `self_evolution_transforms.py` — Code transformations
- `self_evolution_file_ops.py` — File operations
- `self_evolution_splitting.py` — Module splitting

### External Knowledge
- `wolfram_integration.py` / `wolfram_cloud.py` / `wolfram_enhanced.py` / `wolfram_fix.py`
- `self_research.py` — Autonomous research
- `search_compat.py` — Search compatibility

### Personality & Dreams
- `personality_engine.py` / `_ext.py` — Personality system
- `dream_state.py` — Dream engine
- `quote_engine.py` — Quote generation

### API Routes
- `routes_chat.py` — Chat, sessions, export
- `routes_cognitive.py` — Cognitive endpoints
- `routes_brain.py` — Brain/quantum endpoints
- `routes_extras.py` — Growth, covenant, safety, dreams, dictionary, research, cloud
- `routes_evaluation.py` — Response evaluation
- `routes_explorer.py` — Universal explorer
- `routes_image.py` — Image generation
- `routes_media.py` — Media handling

---

## How to Share This With Claude

1. **Quick copy:** Tap "📋 Dev Context" in the MCAGI chat interface → copies this to clipboard
2. **API:** `GET /api/dev/context` → returns this as JSON with `exported_text` field
3. **File:** Copy the contents of `PROJECT_CONTEXT.md` from the repo
4. **Paste into Claude** at the start of any conversation about this project

---

## Important Conventions

- **No LLMs:** This system generates language via Markov chains, not API calls to GPT/Claude
- **Termux-first:** Everything must work on Android/Termux
- **PennyLane via venv:** Required for quantum features; venv is gitignored
- **Growth stages defined in TWO places:** `quantum_cognitive_core.py` AND `chat.py` — keep in sync
- **Self-evolution:** The system modifies its own code — changes may appear between sessions
- **Multiple AI contributors:** Claude, Gemini, Copilot, ChatGPT, Deepseek, Grok, Manus, Emergent have all contributed
