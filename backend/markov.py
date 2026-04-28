"""Classical Markov chain – loads saved state from engine_state without printing."""
import random, re, json, os
from collections import defaultdict
class MarkovEngine:
def __init__(self, order=2, data_dir=None, silent=True):
self.order = order
self.chain = defaultdict(lambda: defaultdict(int))
self.starters = []
self.total_tokens = 0
self.trained = False
if data_dir is None:
data_dir = os.path.expanduser("~/.quantum-mcagi")
self.data_dir = data_dir
self.silent = silent
self._load_saved_state()
def _load_saved_state(self):
path = os.path.join(self.data_dir, "engine_state", "markov_chain.json")
if not os.path.exists(path):
if not self.silent:
print(f"No saved Markov chain found at {path}, training minimal seed.")
self.train("Tubulin proteins shift. Consciousness is quantum collapse.")
return
try:
with open(path, 'r') as f:
data = json.load(f)
if "chain" in data:
for key, trans in data["chain"].items():
prefix = tuple(key.split())
self.chain[prefix] = defaultdict(int, trans)
self.total_tokens = sum(sum(t.values()) for t in self.chain.values())
self.trained = True
if "starters" in data:
self.starters = [tuple(s.split()) for s in data["starters"]]
if not self.silent:
print(f"Loaded Markov chain: {len(self.chain)} states, {self.total_tokens} transitions")
except Exception as e:
print(f"Failed to load Markov chain: {e}")
def train(self, text):
sentences = re.split(r'(?<=[.!?])\s+', text.strip())
for sent in sentences:
tokens = sent.lower().split()
if len(tokens) < self.order + 1:
continue
prefix = tuple(tokens[:self.order])
if prefix not in self.starters:
self.starters.append(prefix)
for i in range(len(tokens) - self.order):
pre = tuple(tokens[i:i+self.order])
suf = tokens[i+self.order]
self.chain[pre][suf] += 1
self.total_tokens += 1
self.trained = True
def generate_from_concepts(self, concepts, length=30, wild=False):
"""Hilbert-primary, Markov-validating, FunctionWord-grammar generation.
Three-signal token selection per step:
1. Hilbert.sample_token(context) — semantic primary (Born-rule)
2. Markov.chain[prefix]
— adjacency validator
3. FunctionWordEngine
— grammar fit reranker
Falls through gracefully when any tier is missing or returns None.
"""
# Lazy-load helpers (cached on instance after first use)
if not hasattr(self, "_hilbert"):
try:
from hilbert_engine import get_hilbert_engine
self._hilbert = get_hilbert_engine(dim=128)
if not getattr(self._hilbert, "loaded", False):
self._hilbert = None
except Exception:
self._hilbert = None
if not hasattr(self, "_fwe"):
try:
from function_word_engine import FunctionWordEngine
fwe = FunctionWordEngine()
fwe_path = os.path.expanduser(
"~/.quantum-mcagi/function_words.json"
)
if os.path.exists(fwe_path):
fwe.load(fwe_path)
self._fwe = fwe
except Exception:
self._fwe = None
# ■■ Seed selection (unchanged) ■■
seed = None
for c in concepts:
for pre in self.chain:
if c.lower() in ' '.join(pre).lower():
seed = pre

break
if seed:
break
if not seed and self.starters:
seed = random.choice(self.starters)
if not seed:
return []
result = list(seed)
# Seed Hilbert ρ from input concepts so semantic field reflects intent
if self._hilbert and concepts:
for c in concepts[:3]:
try:
self._hilbert.evolve(c)
except Exception:
pass
# ■■ Generation loop ■■
for _ in range(length * 2):
nxt = None
# SIGNAL 1: Hilbert primary (semantic Born-rule)
if self._hilbert is not None:
try:
context = list(result[-3:]) # last 3 tokens for context
nxt = self._hilbert.sample_token(
context_tokens=context,
temperature=1.0,
top_k=20,
)
except Exception:
nxt = None
# SIGNAL 2: Markov adjacency validator
# If Hilbert returned a token, check if Markov has ever seen it
# follow this prefix. If yes -> good. If no -> still allow but
# fall back to Markov pick when Hilbert returns None.
markov_choices = self.chain.get(seed)
if nxt is None and markov_choices:
# Hilbert silent -> pure Markov pick
words = list(markov_choices.keys())
weights = list(markov_choices.values())
nxt = random.choices(words, weights=weights)[0]
# SIGNAL 3: FunctionWord grammar reranker (only if multiple Markov candidates)
if (nxt is not None and self._fwe is not None
and markov_choices and len(markov_choices) > 1):
try:
# Light-touch rerank: if nxt is a function word and the
# FWE dossier shows it rarely follows the current last
# content word, swap to a higher-fit candidate.
last_word = result[-1].lower() if result else ""
dossier = self._fwe.get_dossier(nxt)
if dossier and dossier.get("preceding_neighbors"):
prev_count = dossier["preceding_neighbors"].get(last_word, 0)
if prev_count == 0:
# Try another candidate from Markov pool
words = list(markov_choices.keys())
weights = list(markov_choices.values())
for _i in range(3):
alt = random.choices(words, weights=weights)[0]
alt_dossier = self._fwe.get_dossier(alt)
if (alt_dossier is None or
alt_dossier.get("preceding_neighbors", {}).get(
last_word, 0) > 0):
nxt = alt
break
except Exception:
pass
# If still no candidate, terminate gracefully
if nxt is None:
if len(result) < 6:
break
if not self.starters:
break
seed = random.choice(self.starters)
nxt = seed[-1]
result.append(nxt)
seed = tuple(result[-self.order:])
if len(result) >= length and nxt.endswith(('.', '!', '?')):
break
return result
def get_status(self):
return {'states': len(self.chain), 'transitions': self.total_tokens, 'trained': self.trained}
def __getitem__(self, key): return self.chain[key]
def get(self, key, default=None): return self.chain.get(key, default)
def __contains__(self, key): return key in self.chain
def keys(self): return self.chain.keys()

