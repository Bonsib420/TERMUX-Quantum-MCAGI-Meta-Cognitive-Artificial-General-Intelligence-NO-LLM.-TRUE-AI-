#!/usr/bin/env python3
"""
■ QUANTUM MCAGI — Engine API
================================
Central engine + Flask web layer. Single file. Single port. Single process.
Restores the real CognitiveEngine interface that chat.py and routes_chat.py
depend on, AND exposes Flask web routes for the frontend.
Interface contract (do NOT break — chat.py and routes_chat.py call these):
api = get_api()
api.process_input(text, context=None, history=None, explain_mode=False) -> dict
api.get_status() -> dict
api.save_state() -> None
api.data_dir -> Path
api.memory -> LocalMemory
Web layer:
GET /
POST /chat
POST /memory
POST /growth
POST /dream
POST /research
POST /analyze
POST /evolve
POST /numerals
POST /cistercian
POST /image
POST /create
POST /explore
POST /settings
POST /theme

-> serves frontend index.html
-> real Markov + Hilbert generation
-> real memory query
-> real growth metrics
-> real dream state
-> real self-research
-> real text analyzer
-> evolution status (no autorun)
-> Cistercian
-> Cistercian
-> image generator
-> creative generation
-> explorer
-> system status
-> ack only

Run: python engine_api.py
Open: http://localhost:5000
"""
import os
import sys
import json
import time
import random
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
# ■■■ Path setup ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# Frontend lives one level up in /frontend (typical Quantum MCAGI layout)
FRONTEND_DIR = HERE.parent / "frontend"
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("engine_api")
# ■■■ Defensive engine imports ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Every import wrapped: a missing/broken engine should NOT crash the API.
# Each HAS_* flag tells the rest of the code whether to use that engine.
HAS_LANGUAGE = False
try:
from quantum_language_engine import QuantumLanguageEngine
HAS_LANGUAGE = True
log.info("✓ quantum_language_engine loaded")
except Exception as e:
log.warning(f"✗ quantum_language_engine unavailable: {e}")
HAS_MARKOV = False
try:
from markov_engine import MarkovEngine
HAS_MARKOV = True
log.info("✓ markov_engine loaded")
except Exception as e:
try:
# Fallback: chat.py history shows "markov.py" also exists
from markov import MarkovEngine
HAS_MARKOV = True
log.info("✓ markov (fallback) loaded")
except Exception as e2:
log.warning(f"✗ markov_engine unavailable: {e}")
HAS_ORCH_OR = False
try:
from orch_or_engine import OrchOREngine
HAS_ORCH_OR = True
log.info("✓ orch_or_engine loaded")
except Exception as e:
log.warning(f"✗ orch_or_engine unavailable: {e}")
HAS_MEMORY = False

try:
from memory import LocalMemory
HAS_MEMORY = True
log.info("✓ memory loaded")
except Exception as e:
log.warning(f"✗ memory unavailable: {e}")
HAS_DREAM = False
try:
from dream_state import DreamStateEngine
HAS_DREAM = True
log.info("✓ dream_state loaded")
except Exception as e:
log.warning(f"✗ dream_state unavailable: {e}")
HAS_RESEARCH = False
try:
from self_research import SelfResearchEngine
HAS_RESEARCH = True
log.info("✓ self_research loaded")
except Exception as e:
log.warning(f"✗ self_research unavailable: {e}")
HAS_TEXT_ANALYZER = False
try:
from text_analyzer import get_text_analyzer
HAS_TEXT_ANALYZER = True
log.info("✓ text_analyzer loaded")
except Exception as e:
log.warning(f"✗ text_analyzer unavailable: {e}")
HAS_CISTERCIAN = False
try:
from cistercian_engine import generate_cistercian
HAS_CISTERCIAN = True
log.info("✓ cistercian_engine loaded")
except Exception as e:
log.warning(f"✗ cistercian_engine unavailable: {e}")
HAS_PERSONALITY = False
try:
from personality_engine import get_personality_engine
HAS_PERSONALITY = True
log.info("✓ personality_engine loaded")
except Exception as e:
log.warning(f"✗ personality_engine unavailable: {e}")
HAS_KNOWLEDGE = False
try:
from knowledge_base import get_knowledge_base
HAS_KNOWLEDGE = True
log.info("✓ knowledge_base loaded")
except Exception as e:
log.warning(f"✗ knowledge_base unavailable: {e}")
HAS_EXAM = False
try:
from exam_system import ExamRunner, IntakeTracker
HAS_EXAM = True
except Exception:
pass
HAS_EVOLUTION = False
try:
from self_evolution_runner import run_evolution_status
HAS_EVOLUTION = True
except Exception:
try:
import self_evolution_runner # noqa
HAS_EVOLUTION = True
except Exception:
pass
HAS_INGEST = False
try:
from document_ingester import handle_ingest_command
HAS_INGEST = True
except Exception:
pass
HAS_LIBRARY = False
try:
from library import handle_library_command
HAS_LIBRARY = True
except Exception:
pass

# noqa

# noqa

HAS_CISTERCIAN_MATH = False
try:
from cistercian_math import cistercian_compute
HAS_CISTERCIAN_MATH = True
except Exception:
pass

# noqa

HAS_QRAM = False
try:
from quantum_memory import PENNYLANE_QRAM_AVAILABLE
HAS_QRAM = bool(PENNYLANE_QRAM_AVAILABLE)
except Exception:
pass
HAS_HYBRID = False

try:
from hybrid_generator import create_hybrid_generator
HAS_HYBRID = True
except Exception:
pass
HAS_CHAOS = False
try:
from chaos_engine import get_chaos_engine
HAS_CHAOS = True
except Exception:
pass
HAS_QUOTE = False
try:
from quote_engine import get_quote_engine
HAS_QUOTE = True
except Exception:
pass
HAS_HIDDEN_THINKING = False
try:
from hidden_thinking import get_hidden_thinking
HAS_HIDDEN_THINKING = True
log.info("✓ hidden_thinking loaded")
except Exception as e:
log.warning(f"✗ hidden_thinking unavailable: {e}")
HAS_IMAGE = False
try:
from image_generator import generate_image # noqa
HAS_IMAGE = True
except Exception:
try:
from image_generator_v2 import generate_image # noqa
HAS_IMAGE = True
except Exception:
pass

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# CognitiveEngine — the real interface that chat.py + routes_chat.py expect
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
class CognitiveEngine:
"""
Central cognitive engine. Lazy-initialized singletons inside.
Restores the contract that chat.py and routes_chat.py depend on.
"""
def __init__(self):
self.data_dir = Path(os.path.expanduser("~/.quantum-mcagi"))
self.data_dir.mkdir(parents=True, exist_ok=True)
# ■■■ Pull brain from Google Drive (rclone) ■■■
try:
from cloud_brain import CloudBrain
CloudBrain().startup_pull()
log.info("✓ Cloud brain pulled from gdrive")
except Exception as e:
log.warning(f"✗ Cloud pull skipped: {e}")
# ■■■ Memory (loaded first; everything else may need it) ■■■
self.memory = None
if HAS_MEMORY:
try:
self.memory = LocalMemory(self.data_dir)
log.info(f"✓ Memory initialized at {self.data_dir}")
except Exception as e:
log.error(f"Memory init failed: {e}")
# ■■■ Language engine via singleton accessor ■■■
self.language = None
if HAS_LANGUAGE:
try:
try:
from quantum_language_engine import get_language_engine
self.language = get_language_engine()
except ImportError:
self.language = QuantumLanguageEngine()
log.info("✓ Language engine initialized (singleton)")
except Exception as e:
log.error(f"Language init failed: {e}")
# ■■■ Markov engine (separate instance for raw access) ■■■
self.markov = None
if HAS_MARKOV:
try:
self.markov = MarkovEngine()
log.info("✓ Markov engine initialized")
except Exception as e:
log.error(f"Markov init failed: {e}")
# ■■■ Orch OR ■■■
self.orch_or = None
if HAS_ORCH_OR:
try:
self.orch_or = OrchOREngine()
log.info("✓ Orch OR initialized")
except Exception as e:
log.error(f"Orch OR init failed: {e}")
# ■■■ Dream state ■■■

self.dream = None
if HAS_DREAM:
try:
self.dream = DreamStateEngine()
log.info("✓ Dream engine initialized")
except Exception as e:
log.error(f"Dream init failed: {e}")
# ■■■ Self-research ■■■
self.research = None
if HAS_RESEARCH:
try:
self.research = SelfResearchEngine()
log.info("✓ Research engine initialized")
except Exception as e:
log.error(f"Research init failed: {e}")
# ■■■ Hidden thinking (the real CLI brain orchestrator) ■■■
self.hidden = None
if HAS_HIDDEN_THINKING:
try:
# HiddenThinkingMode.__init__ ignores its 3 args and builds its own
# memory/markov/orch_or. Pass None to avoid coupling with shared_state.
self.hidden = get_hidden_thinking(None, None, None)
log.info("✓ Hidden thinking initialized (UnifiedQuantumBrain pipeline)")
except Exception as e:
log.error(f"Hidden thinking init failed: {e}")
# ■■■ Counters / state ■■■
self.start_time = time.time()
self.interaction_count = 0
if self.memory is not None:
try:
growth = getattr(self.memory, "growth", {}) or {}
self.interaction_count = int(growth.get("total_interactions", 0))
except Exception:
pass
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# process_input — the main contract. chat.py + routes_chat.py call this.
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
def process_input(
self,
text: str,
context: Optional[Dict] = None,
history: Optional[List] = None,
explain_mode: bool = False,
) -> Dict[str, Any]:
"""
Process user input through the real engines.
Returns: {"response": str, "concepts": [...], "explanation": dict|None}
"""
text = (text or "").strip()
if not text:
return {"response": "", "concepts": [], "explanation": None}
self.interaction_count += 1
response = None
concepts = []
explanation = None
# ■■ Hidden thinking pipeline (preferred — same as chat.py CLI) ■■
if self.hidden is not None:
try:
# process_with_thinking is async; run it synchronously
async def _run():
return await self.hidden.process_with_thinking(
text, context=None, explain_mode=explain_mode
)
# asyncio.run() requires no running loop; in Flask thread context that's fine
try:
result = asyncio.run(_run())
except RuntimeError:
# If a loop is already running (rare in Flask sync route), use new_event_loop
loop = asyncio.new_event_loop()
try:
result = loop.run_until_complete(_run())
finally:
loop.close()
if isinstance(result, dict) and result.get("response"):
return {
"response": result.get("response", ""),
"concepts": result.get("concepts", []),
"explanation": result.get("explanation"),
"confidence": result.get("confidence"),
"research_done": result.get("research_done", 0),
}
except Exception as e:
log.exception(f"Hidden thinking failed, falling back to QLE: {e}")
# ■■ Fallback: direct QuantumLanguageEngine pipeline ■■
if self.language is not None:
try:
growth_stage = 0
if self.memory is not None:
g = getattr(self.memory, "growth", {}) or {}
growth_stage = int(g.get("stage", 0))
try:
concepts = self.language.extract_concepts(text, max_concepts=5)

except Exception as e:
log.warning(f"extract_concepts failed: {e}")
concepts = []
understanding = {
"topic": concepts[0] if concepts else text[:50],
"understanding_score": min(1.0, len(concepts) * 0.2),
"gaps": [],
"related_concepts": [],
}
try:
questions = self.language.generate_questions(
text, growth_stage=growth_stage, known_concepts=concepts
)
except Exception as e:
log.warning(f"generate_questions failed: {e}")
questions = []
response = self.language.generate_response(
text, questions, understanding, concepts, growth_stage
)
try:
if hasattr(self.language, "learn_from_text"):
self.language.learn_from_text(text)
except Exception:
pass
except Exception as e:
log.exception(f"Language pipeline failed: {e}")
response = None
if not response:
response = "Engine alive but produced no output. Check logs."
# ■■ Orch OR conscious moment (counter, not list — recurring bug) ■■
if self.orch_or is not None:
try:
if hasattr(self.orch_or, "trigger_collapse"):
self.orch_or.trigger_collapse()
elif hasattr(self.orch_or, "tick"):
self.orch_or.tick()
# increment counter (NEVER append to a list — known bug pattern)
cm = getattr(self.orch_or, "conscious_moments", 0)
if isinstance(cm, int):
self.orch_or.conscious_moments = cm + 1
except Exception as e:
log.warning(f"Orch OR collapse failed: {e}")
# ■■ Persist interaction ■■
if self.memory is not None:
try:
if hasattr(self.memory, "log_interaction"):
self.memory.log_interaction(text, response)
elif hasattr(self.memory, "growth"):
self.memory.growth["total_interactions"] = self.interaction_count
if hasattr(self.memory, "save_all"):
self.memory.save_all()
except Exception as e:
log.warning(f"Memory log failed: {e}")
if explain_mode:
explanation = {
"engines_used": [
name for name, ok in [
("QuantumLanguageEngine", self.language is not None),
("MarkovEngine", self.markov is not None),
("OrchOR", self.orch_or is not None),
] if ok
],
"interaction_number": self.interaction_count,
"timestamp": datetime.utcnow().isoformat(),
}
return {"response": response, "concepts": concepts, "explanation": explanation}
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
def get_status(self) -> Dict[str, Any]:
"""System status — chat.py /status command depends on this shape."""
# Growth
growth = {"stage": 0, "name": "Nascent", "total_concepts": 0,
"total_interactions": self.interaction_count, "knowledge_track": {}}
if self.memory is not None:
try:
g = getattr(self.memory, "growth", None) or {}
growth["stage"] = g.get("stage", 0)
growth["name"] = g.get("name", "Nascent")
growth["total_concepts"] = g.get("total_concepts", 0)
growth["total_interactions"] = g.get("total_interactions", self.interaction_count)
growth["knowledge_track"] = g.get("knowledge_track", {})
except Exception:
pass
# Markov — read from hidden_thinking first (real chain), fall back to QLE
markov = {"states": 0, "transitions": 0}
try:
chain = None
# Priority 1: hidden_thinking.markov (the one chat.py uses, real 5M states)
if self.hidden is not None and hasattr(self.hidden, "markov"):
m = self.hidden.markov
# MarkovEngine has .chain (dict of states) and total_tokens

if hasattr(m, "chain"):
chain_dict = m.chain
if hasattr(chain_dict, "__len__"):
markov["states"] = len(chain_dict)
if hasattr(m, "total_tokens"):
markov["transitions"] = int(m.total_tokens or 0)
# Priority 2: language.markov (QLE seed corpus)
if markov["states"] == 0 and self.language is not None and hasattr(self.language, "markov"):
chain = self.language.markov
if chain is not None and hasattr(chain, "transitions"):
t = chain.transitions
if hasattr(t, "__len__"):
markov["states"] = len(t)
if hasattr(t, "values"):
markov["transitions"] = sum(
len(v) if hasattr(v, "__len__") else 1 for v in t.values()
)
except Exception:
pass
# Orch OR — prefer hidden_thinking's instance (real one used by chat.py)
orch_or = "unavailable (classical fallback)"
orch_target = None
if self.hidden is not None and hasattr(self.hidden, "orch_or"):
orch_target = self.hidden.orch_or
elif self.orch_or is not None:
orch_target = self.orch_or
if orch_target is not None:
try:
# collapse_events list (HiddenThinking style) or conscious_moments int (QLE style)
if hasattr(orch_target, "collapse_events"):
cm = len(orch_target.collapse_events)
else:
cm = getattr(orch_target, "conscious_moments", 0)
orch_or = f"active — {cm} conscious moments"
except Exception:
orch_or = "active"
# QRAM
qram = {"backend": "classical", "entries": 0}
if HAS_QRAM:
qram["backend"] = "pennylane"
return {
"growth": growth,
"markov": markov,
"orch_or": orch_or,
"qram": qram,
"uptime_seconds": int(time.time() - self.start_time),
"engines": {
"language": self.language is not None,
"markov": self.markov is not None,
"orch_or": self.orch_or is not None,
"dream": self.dream is not None,
"research": self.research is not None,
"memory": self.memory is not None,
},
}
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
def save_state(self) -> None:
"""Persist all engine state. Called by chat.py /save."""
if self.memory is not None and hasattr(self.memory, "save_all"):
try:
self.memory.save_all()
log.info("✓ Memory saved")
except Exception as e:
log.error(f"Memory save failed: {e}")
if self.language is not None:
for method in ("save_state", "save", "save_chain"):
if hasattr(self.language, method):
try:
getattr(self.language, method)()
log.info(f"✓ Language saved via {method}")
break
except Exception as e:
log.warning(f"language.{method} failed: {e}")

# ■■■ Singleton accessor (chat.py and routes_chat.py call this) ■■■■■■■■■■
_API_INSTANCE: Optional[CognitiveEngine] = None

def get_api() -> CognitiveEngine:
"""Singleton accessor. NEVER instantiate CognitiveEngine() directly elsewhere."""
global _API_INSTANCE
if _API_INSTANCE is None:
_API_INSTANCE = CognitiveEngine()
return _API_INSTANCE

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Flask web layer
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
CORS(app)
# ■■■ Serve frontend ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

@app.route("/", methods=["GET"])
def serve_index():
if (FRONTEND_DIR / "index.html").exists():
return send_from_directory(str(FRONTEND_DIR), "index.html")
return jsonify({"status": "QUANTUM MCAGI ENGINE ONLINE",
"version": "3.0",
"note": f"Frontend not found at {FRONTEND_DIR}"})

@app.route("/<path:filename>", methods=["GET"])
def serve_static(filename):
"""Serve frontend assets (CSS, JS, images)."""
if (FRONTEND_DIR / filename).exists():
return send_from_directory(str(FRONTEND_DIR), filename)
return ("Not found", 404)

# ■■■ Helpers ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
def _get_query() -> str:
data = request.get_json(silent=True) or {}
return (data.get("message") or data.get("query") or data.get("text") or "").strip()

def _ok(text: str, **extra) -> Any:
payload = {"response": text}
payload.update(extra)
return jsonify(payload)

def _err(msg: str, code: int = 500) -> Any:
return jsonify({"response": f"■■ {msg}", "error": True}), code

# ■■■ /chat — real engine ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
@app.route("/chat", methods=["POST"])
def chat_endpoint():
msg = _get_query()
if not msg:
return _err("Empty message", 400)
data = request.get_json(silent=True) or {}
explain = bool(data.get("explain_mode") or data.get("verbose"))
try:
result = get_api().process_input(msg, explain_mode=explain)
payload = {
"response": result.get("response", ""),
"concepts": result.get("concepts", []),
}
if result.get("confidence") is not None:
payload["confidence"] = result["confidence"]
if result.get("research_done") is not None:
payload["research_done"] = result["research_done"]
if explain and result.get("explanation"):
payload["explanation"] = result["explanation"]
return jsonify(payload)
except Exception as e:
log.exception("chat failed")
return _err(f"chat error: {e}")

# ■■■ /memory — real ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
@app.route("/memory", methods=["POST"])
def memory_endpoint():
api = get_api()
if api.memory is None:
return _ok("■ Memory engine not loaded.")
try:
g = getattr(api.memory, "growth", {}) or {}
interactions = g.get("total_interactions", api.interaction_count)
concepts = g.get("total_concepts", 0)
stage = g.get("stage", 0)
return _ok(
f"■ Memory snapshot:\n"
f" • Interactions: {interactions}\n"
f" • Concepts: {concepts}\n"
f" • Stage: {stage}\n"
f" • Data dir: {api.data_dir}"
)
except Exception as e:
return _err(f"memory error: {e}")

# ■■■ /growth — real metrics ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
@app.route("/growth", methods=["POST"])
def growth_endpoint():
try:
s = get_api().get_status()
g = s["growth"]
m = s["markov"]
return _ok(
f"■ Growth status:\n"
f" • Stage: {g['stage']} ({g['name']})\n"
f" • Concepts: {g['total_concepts']}\n"
f" • Interactions: {g['total_interactions']}\n"
f" • Markov states: {m['states']}\n"
f" • Markov transitions: {m['transitions']}\n"
f" • Orch OR: {s['orch_or']}"
)
except Exception as e:
return _err(f"growth error: {e}")
# ■■■ /dream — real ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
@app.route("/dream", methods=["POST"])

def dream_endpoint():
api = get_api()
if api.dream is None:
return _ok("■ Dream engine not loaded.")
try:
for method in ("generate_dream", "dream", "produce", "generate"):
if hasattr(api.dream, method):
out = getattr(api.dream, method)()
if isinstance(out, str) and out.strip():
return _ok(f"■ {out}")
if isinstance(out, dict):
return _ok(f"■ {out.get('text', out)}")
return _ok("■ Dream engine present but no method matched.")
except Exception as e:
return _err(f"dream error: {e}")

# ■■■ /research — real ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
@app.route("/research", methods=["POST"])
def research_endpoint():
api = get_api()
msg = _get_query()
if api.research is None:
return _ok("■ Research engine not loaded.")
try:
topic = msg or "consciousness"
for method in ("research_topic", "research", "investigate", "query"):
if hasattr(api.research, method):
out = getattr(api.research, method)(topic)
if isinstance(out, dict):
return _ok(f"■ Research on '{topic}':\n{out.get('summary', out)}")
if isinstance(out, str):
return _ok(f"■ {out}")
if isinstance(out, list):
bullets = "\n".join(f" • {x}" for x in out[:5])
return _ok(f"■ Research on '{topic}':\n{bullets}")
return _ok(f"■ Research engine present but no method matched.")
except Exception as e:
return _err(f"research error: {e}")

# ■■■ /analyze — real text analyzer ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
@app.route("/analyze", methods=["POST"])
def analyze_endpoint():
msg = _get_query() or "test"
if not HAS_TEXT_ANALYZER:
return _ok("■ Text analyzer not loaded.")
try:
analyzer = get_text_analyzer()
out = analyzer.analyze(msg)
return _ok(
f"■ Analysis:\n"
f" • Sentiment: {out.get('sentiment', 'unknown')}\n"
f" • Complexity: {out.get('complexity', 'unknown')}\n"
f" • Topics: {', '.join(out.get('topics', [])) or 'none'}\n"
f" • Word count: {out.get('word_count', 0)}"
)
except Exception as e:
return _err(f"analyze error: {e}")

# ■■■ /evolve — status only, no autorun ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
@app.route("/evolve", methods=["POST"])
def evolve_endpoint():
if not HAS_EVOLUTION:
return _ok("■ Evolution module not loaded.")
return _ok(
"■ Evolution engine: ARMED.\n"
" Use /evolve-run from CLI to actually trigger.\n"
" Web button is status-only for safety."
)

# ■■■ /numerals & /cistercian — real ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
@app.route("/numerals", methods=["POST"])
@app.route("/cistercian", methods=["POST"])
def cistercian_endpoint():
msg = _get_query()
if not HAS_CISTERCIAN:
return _ok("■ Cistercian engine not loaded.")
try:
try:
num = int(msg) if msg else random.randint(1, 9999)
except ValueError:
num = random.randint(1, 9999)
rendered = generate_cistercian(num)
return _ok(f"■ Cistercian numeral for {num}:\n{rendered}")
except Exception as e:
return _err(f"cistercian error: {e}")

# ■■■ /image — real ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
@app.route("/image", methods=["POST"])
def image_endpoint():
if not HAS_IMAGE:
return _ok("■ Image generator not loaded.")
msg = _get_query() or "quantum nebula"
try:
out = generate_image(msg)
if isinstance(out, dict):
return _ok(f"■ Generated: {out.get('path', out)}")

return _ok(f"■ {out}")
except Exception as e:
return _err(f"image error: {e}")

# ■■■ /create — creative generation via language engine ■■■■■■■■■■■■■■■■■■
@app.route("/create", methods=["POST"])
def create_endpoint():
msg = _get_query() or "create something new"
try:
result = get_api().process_input(f"Create: {msg}")
return _ok(f"■ {result.get('response', '')}")
except Exception as e:
return _err(f"create error: {e}")

# ■■■ /explore — knowledge base or memory walk ■■■■■■■■■■■■■■■■■■■■■■■■■■■
@app.route("/explore", methods=["POST"])
def explore_endpoint():
msg = _get_query()
if HAS_KNOWLEDGE and msg:
try:
kb = get_knowledge_base()
out = kb.get_topic_explanation(msg)
if out:
return _ok(f"■ {out}")
except Exception as e:
log.warning(f"knowledge: {e}")
# Fallback: dream-like associative
api = get_api()
if api.dream is not None:
try:
for method in ("generate_dream", "dream", "produce"):
if hasattr(api.dream, method):
return _ok(f"■ {getattr(api.dream, method)()}")
except Exception:
pass
return _ok("■ No exploration target. Send a message body to explore a topic.")

# ■■■ /settings — system status ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
@app.route("/settings", methods=["POST"])
def settings_endpoint():
try:
s = get_api().get_status()
engines = s["engines"]
active = [k for k, v in engines.items() if v]
inactive = [k for k, v in engines.items() if not v]
return _ok(
f"■■ System status:\n"
f" • Uptime: {s['uptime_seconds']}s\n"
f" • Active engines: {', '.join(active) or 'none'}\n"
f" • Inactive: {', '.join(inactive) or 'none'}\n"
f" • QRAM backend: {s['qram']['backend']}"
)
except Exception as e:
return _err(f"settings error: {e}")

# ■■■ /theme — ack only ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
@app.route("/theme", methods=["POST"])
def theme_endpoint():
return _ok("■ Theme: cyberpunk-neon (frontend-controlled).")

# ■■■ /status — for chat.py compatibility ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
@app.route("/status", methods=["GET", "POST"])
def status_endpoint():
return jsonify(get_api().get_status())

# ■■■ /save — persist state ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
@app.route("/save", methods=["POST"])
def save_endpoint():
try:
get_api().save_state()
return _ok("■ State saved.")
except Exception as e:
return _err(f"save error: {e}")

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
if __name__ == "__main__":
print("\n" + "■" * 60)
print(" ■■ QUANTUM MCAGI — UNIFIED ENGINE")
print("■" * 60)
api = get_api() # warm singleton
s = api.get_status()
print(f" Stage: {s['growth']['stage']} ({s['growth']['name']})")
print(f" Concepts: {s['growth']['total_concepts']} | "
f"Interactions: {s['growth']['total_interactions']}")
print(f" Markov: {s['markov']['states']} states, "
f"{s['markov']['transitions']} transitions")
print(f" Orch OR: {s['orch_or']}")
print(f" Frontend dir: {FRONTEND_DIR} "
f"({'EXISTS' if FRONTEND_DIR.exists() else 'MISSING'})")
print("■" * 60)
print(" ■ Open: http://localhost:5000")
print(" ■ Stop: Ctrl+C")
print("■" * 60 + "\n")
# Start watchdog: auto-save every 5 min, cloud sync every 20 min

try:
from system_safety import Watchdog
import atexit
def _cloud_push():
try:
from cloud_brain import CloudBrain
CloudBrain().push()
except Exception:
pass
_watchdog = Watchdog(save_fn=api.save_state, interval_seconds=300,
cloud_fn=_cloud_push, cloud_every_n_saves=4)
_watchdog.start()
atexit.register(_watchdog.stop)
except Exception as e:
print(f" ■ watchdog unavailable: {e}")
app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

