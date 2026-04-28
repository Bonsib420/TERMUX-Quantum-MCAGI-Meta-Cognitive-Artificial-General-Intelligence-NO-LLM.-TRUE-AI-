"""
One-shot importer that merges the Termux MCAGI_BACKUP brain
(downloaded from Google Drive into backend/imported_brain/) into the
Replit engine: TF-IDF, KnowledgeBase (Wolfram-style), and Markov chain.
"""
import json
import os
import sys
import re
BRAIN_DIR = os.path.join(os.path.dirname(__file__), 'imported_brain')

def load_json(path):
with open(path, 'r', encoding='utf-8') as f:
return json.load(f)

def import_facts_to_tfidf(engine):
"""fact_store.json -> TF-IDF (treats each fact as a sentence)."""
path = os.path.join(BRAIN_DIR, 'fact_store.json')
if not os.path.exists(path):
return 0, 0
facts = load_json(path)
sentences = []
bad_topic = re.compile(r'\[\[|\]\]|\|')
for topic, items in facts.items():
if bad_topic.search(topic) or len(topic) > 80:
continue
if not isinstance(items, list):
continue
for entry in items:
if isinstance(entry, list) and len(entry) >= 2:
verb, obj = entry[0], entry[1]
if not isinstance(obj, str) or len(obj) < 8 or len(obj) > 400:
continue
# Build a clean sentence
obj_clean = obj.strip().rstrip('.,;:').strip()
if not obj_clean:
continue
sentence = f"{topic.capitalize()} {verb} {obj_clean}."
sentences.append(sentence)
# Bulk feed to TF-IDF
bulk = ' '.join(sentences)
if bulk:
engine.tfidf.learn(bulk)
return len(sentences), len(facts)

def import_kg_to_knowledge_base(engine):
"""knowledge_graph.json (Wikidata-style) -> KnowledgeBase.topics."""
path = os.path.join(BRAIN_DIR, 'knowledge_graph.json')
if not os.path.exists(path):
return 0
kg = load_json(path)
added = 0
for topic, entry in kg.items():
if not isinstance(entry, dict):
continue
if topic in engine.knowledge.topics:
continue
desc = entry.get('_description', '').strip()
if not desc or len(desc) > 500:
continue
relations = entry.get('_relations', {}) or {}
subtopics = []
related = []
bad_id = re.compile(r'^[0-9]+(-[0-9]+)?$|^Q[0-9]+$|^P[0-9]+$')
def _ok(name):
return (isinstance(name, str) and 1 < len(name) < 60
and not bad_id.match(name)
and not re.search(r'\[\[|\]\]|\|', name))
for rel_name, rel_list in relations.items():
if not isinstance(rel_list, list):
continue
if rel_name in ('part_of', 'has_part', 'subclass_of', 'has_quality'):
subtopics.extend([r for r in rel_list if _ok(r)][:5])
else:
related.extend([r for r in rel_list if _ok(r)][:5])
engine.knowledge.topics[topic] = {
'description': desc,
'subtopics': subtopics[:8],
'related': related[:8],
}
added += 1
return added

def import_concepts_to_markov(engine, max_states=20000):
"""
Sample the Termux Markov chain into our chain.
The 252MB chain is too big to load directly — we sample top transitions.
"""
path = os.path.join(BRAIN_DIR, 'engine_state', 'markov_chain.json')

if not os.path.exists(path):
return 0
print(f" Loading Markov chain ({os.path.getsize(path)//1024//1024} MB)...")
raw = load_json(path)
if not isinstance(raw, dict):
return 0
# Termux wraps it: {order, chain, starters, total_tokens}
chain = raw.get('chain', raw)
starters_list = raw.get('starters', []) or []
if not isinstance(chain, dict):
return 0
target_order = raw.get('order', 2)
print(f" Termux chain order: {target_order}")
# Pick the matching chain in our engine
if target_order == 1:
target = engine.markov.chain_1
else:
target = engine.markov.chain_2
added = 0
state_items = list(chain.items())
state_items.sort(
key=lambda kv: sum(kv[1].values()) if isinstance(kv[1], dict) else 0,
reverse=True
)
bad_token = re.compile(r'\[\[|\]\]|\||={2,}|^\(.*\)$')
for state_key, transitions in state_items[:max_states]:
if not isinstance(transitions, dict):
continue
if bad_token.search(state_key):
continue
parts = tuple(state_key.split())
if len(parts) != target.order:
if len(parts) < target.order:
continue
parts = parts[-target.order:]
if parts not in target.chain:
target.chain[parts] = {}
for next_word, count in transitions.items():
if not isinstance(count, (int, float)):
continue
if not isinstance(next_word, str) or len(next_word) > 40:
continue
if bad_token.search(next_word):
continue
target.chain[parts][next_word] = (
target.chain[parts].get(next_word, 0) + int(count)
)
if parts[0] and parts[0][0].isupper() and hasattr(target, 'sentence_starters'):
target.sentence_starters.add(parts)
added += 1
if hasattr(target, 'sentence_starters'):
for s in starters_list:
if isinstance(s, str):
p = tuple(s.split())
if len(p) == target.order:
target.sentence_starters.add(p)
elif isinstance(s, list) and len(s) == target.order:
target.sentence_starters.add(tuple(s))
target.trained = True
return added

def import_concepts_seed(engine):
"""concepts.json -> ensure all concepts known to TF-IDF vocabulary."""
path = os.path.join(BRAIN_DIR, 'concepts.json')
if not os.path.exists(path):
return 0
concepts = load_json(path)
if not isinstance(concepts, dict):
return 0
# Build a long sentence so TF-IDF learns these as vocabulary
words = [c for c in concepts.keys() if isinstance(c, str) and 2 < len(c) < 30 and c.isalpha()]
if words:
# Feed in small batches as pseudo-sentences
batch_size = 50
for i in range(0, len(words), batch_size):
batch = words[i:i+batch_size]
engine.tfidf.learn(' '.join(batch) + '.')
return len(words)

def main():
print("=" * 60)
print("Importing Termux brain into Replit engine")
print("=" * 60)
if not os.path.exists(BRAIN_DIR):
print(f"ERROR: {BRAIN_DIR} not found")
sys.exit(1)
sys.path.insert(0, os.path.dirname(__file__))
from quantum_language_engine import QuantumLanguageEngine
print("\nInitialising fresh engine...")
engine = QuantumLanguageEngine()
print(f" Baseline TF-IDF docs: {engine.tfidf.extractor.total_documents}")

print(f"
print(f"

Baseline KB topics:
{len(engine.knowledge.topics)}")
Baseline Markov states: {len(engine.markov.chain) if hasattr(engine.markov,'chain') else '?'}")

print("\n[1/4] Importing knowledge graph (Wikidata-style topics)...")
kg_added = import_kg_to_knowledge_base(engine)
print(f" + {kg_added} new topics added to KnowledgeBase")
print(f" Total KB topics now: {len(engine.knowledge.topics)}")
print("\n[2/4] Importing fact_store -> TF-IDF...")
facts_added, topics = import_facts_to_tfidf(engine)
print(f" + {facts_added} fact-sentences from {topics} topics")
print("\n[3/4] Seeding TF-IDF vocabulary from concepts...")
concepts_added = import_concepts_seed(engine)
print(f" + {concepts_added} concept tokens seeded")
print("\n[4/4] Importing Markov chain (sampling top 20k states)...")
markov_added = import_concepts_to_markov(engine, max_states=20000)
print(f" + {markov_added} Markov states added")
print("\nFinal stats:")
print(f" TF-IDF docs:
{engine.tfidf.extractor.total_documents}")
print(f" KB topics:
{len(engine.knowledge.topics)}")
print(f" Markov states: {len(engine.markov.chain) if hasattr(engine.markov,'chain') else '?'}")
print(f" Vocab terms:
{len(engine.tfidf.extractor.word_frequencies)}")
# Persist by saving to a snapshot file the server can load on boot
snapshot = {
'kb_topics': engine.knowledge.topics,
'tfidf_word_frequencies': dict(engine.tfidf.extractor.word_frequencies),
'tfidf_doc_frequencies': dict(engine.tfidf.extractor.document_frequencies),
'tfidf_total_docs': engine.tfidf.extractor.total_documents,
'tfidf_total_words': engine.tfidf.extractor.total_words,
'markov_chain': {
' '.join(k): v for k, v in engine.markov.chain.items()
} if hasattr(engine.markov, 'chain') else {},
'markov_starters': [
' '.join(s) for s in getattr(engine.markov, 'sentence_starters', [])
],
}
out_path = os.path.join(os.path.dirname(__file__), 'runtime-data', 'imported_brain_snapshot.json')
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, 'w', encoding='utf-8') as f:
json.dump(snapshot, f)
size_mb = os.path.getsize(out_path) // 1024 // 1024
print(f"\nSnapshot saved: {out_path} ({size_mb} MB)")
print("\nDone. Restart the backend and the engine will auto-load this snapshot.")

if __name__ == '__main__':
main()

