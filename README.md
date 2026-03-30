# Quantum MCAGI — Meta-Cognitive Artificial General Intelligence

> **No LLM. True AI.** Built on Quantum Physics ideas.
> Architecture: RQR³ · Orch-OR · Self-Evolving
> By Cory N.B. Blackburn

---

## Quick Start (Termux on Android)

### 1. Install dependencies

```bash
pkg update && pkg upgrade -y
pkg install python nodejs git
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 2. Run the Terminal Chat (fastest way to interact)

```bash
cd backend
python chat.py
```

This launches the **standalone chat interface** — no server, no database needed. Just you and the AI in your terminal.

### 3. Run the Full Web Server (API + Frontend)

```bash
bash start.sh
```

Then open in your browser: **http://localhost:8000/app/**

- API: http://localhost:8000/api/
- API docs: http://localhost:8000/docs

---

## Interacting with the AI

### Terminal Chat Commands

Once `python chat.py` is running, just type naturally to talk to the AI. It will respond using its quantum language engine, Markov chains, personality system, and chaos engine.

**Special commands:**

| Command | What it does |
|---------|-------------|
| `/status` | Full system status — growth stage, brain metrics, personality |
| `/learn FILE` | Feed a text file to the Markov chain to teach it |
| `/feed` | Batch-fetch 122 research URLs to grow the knowledge base |
| `/feed all` | Fetch all research feed categories |
| `/hybrid TEXT` | Direct hybrid quantum text generation |
| `/unified TEXT` | Word-by-word quantum generation |
| `/analyze TEXT` | Analyze text semantically |
| `/personality` | Show the AI's current personality profile |
| `/knowledge TOPIC` | Look up a topic in the knowledge base |
| `/collapse TOPIC` | Show quantum semantic collapse for a term |
| `/export` | Export full conversation as markdown |
| `/copy-last` | Print last AI response in a bordered box |
| `/cloud-save` | Save brain state to Wolfram Cloud |
| `/cloud-load` | Load & merge concepts from Wolfram Cloud |
| `/cloud-pull` | Pull full brain snapshot from all cloud providers |
| `/cloud-status` | Show cloud connection status |
| `/save` | Save all state to disk |
| `/load` | Load saved state from disk |
| `/reset` | Reset the engine |
| `/quit` | Save and exit |

### Testing the AI

**Start a conversation:**
```
🔮 You: Hello, who are you?
🔮 You: What do you know about quantum physics?
🔮 You: Tell me about consciousness
```

**Teach it something:**
```
🔮 You: /learn thanoquenesis_text.txt
🔮 You: /feed all
```

**Check its growth:**
```
🔮 You: /status
```

**Verbose mode** (shows debug info per response):
```bash
python chat.py --verbose
```

---

## Architecture

- **RQR³** — Recursive Quantum Resonance
- **Orch-OR** — Orchestrated Objective Reduction (consciousness model)
- **Self-Evolving** — No static weights, no fine-tuning
- **No LLM** — True AI built on quantum physics principles
- **Chaos Engine** — Personality with dream states, asides, and raw intrusions
- **Markov + Quantum** — Language generated from quantum-weighted Markov chains
- **Cloud Sync** — Auto-saves brain to Wolfram Cloud

### Project Structure

```
backend/          85+ Python modules — the AI brain
frontend/         React/Vite web interface
quantum_image_generator/  Zero-dependency procedural cosmic art
scripts/          Utility scripts
tests/            Cistercian numeral tests
docs/             Documentation
start.sh          Launch the full system
requirements.txt  Python dependencies
```

### Key Backend Modules

| Module | Purpose |
|--------|---------|
| `chat.py` | Terminal chat interface (standalone, no server needed) |
| `server.py` | FastAPI web server |
| `quantum_language_engine.py` | Core language generation engine |
| `quantum_brain.py` | Quantum brain architecture |
| `chaos_engine.py` | Personality: asides, quotes, dream intrusions |
| `dream_state.py` | Autonomous dream→research→cloud pipeline |
| `orch_or_core.py` | Orchestrated Objective Reduction consciousness |
| `self_evolution_core.py` | Self-evolution and adaptation |
| `cloud_provider.py` | Multi-provider cloud sync (Wolfram, local) |
| `document_ingester.py` | Smart document extraction (Wikipedia, arXiv, etc.) |
| `knowledge_node.py` | Multi-user knowledge network |

---

## Quantum Image Generator

Generate cosmic art from pure mathematics — zero external dependencies:

```bash
python -m quantum_image_generator --preset cosmic_vortex -o vortex.png
python -m quantum_image_generator --all --width 1024 --height 1024
```

Presets: `cosmic_vortex`, `nebula`, `galaxy`, `quantum_field`

---

## Download Release

Download the full 268MB release zip:

```bash
gh release download v1.0.0 \
  --repo Bonsib420/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI- \
  --pattern "*.zip"
```

Or visit: [**Releases**](https://github.com/Bonsib420/TERMUX-Quantum-MCAGI-Meta-Cognitive-Artificial-General-Intelligence-NO-LLM.-TRUE-AI-/releases)
