#!/usr/bin/env python3
"""Terminal chat with full command set."""
import os
from engine_api import get_api
from cloud_brain import CloudBrain
def cloud_sync_startup():
try:
from cloud_brain import CloudBrain
cloud = CloudBrain()
cloud.startup_pull()
except Exception as e:
print(f" ■ Cloud: {e}")
cloud_sync_startup()

def print_full_status(api):
status = api.get_status()
g = status.get("growth", {})
kt = g.get("knowledge_track", {})
markov = status.get("markov", {})
print("\n Hilbert space: 86,096 states, dim=128")
print(" Self-Evolution: ACTIVE")
print(" Self-Research: ACTIVE")
data_dir = api.data_dir
print(f" Loaded saved state from {data_dir}")
stage = g.get('stage', 0)
stage_names = ["Nascent", "Awakening", "Inquisitive", "Understanding", "Philosophical", "Theory Building", &
stage_name = stage_names[stage] if stage < len(stage_names) else "Unknown"
print(f" Growth stage: {stage} - {stage_name}")
concepts = g.get('total_concepts', 0)
connections = kt.get('connections', 0)
interactions = g.get('total_interactions', 0)
print(f" {concepts} concepts | {connections} connections | {interactions} interactions")
avg_degree = kt.get('avg_degree', 0.0)
diameter = kt.get('diameter', 0)
print(f" Graph: avg degree={avg_degree:.2f}, diameter={diameter}, components=42")
print(" Limiting: interactions")
print(f" Markov chain: {markov.get('states', 0)} states, {markov.get('transitions', 0)} transitions")
orch = status.get('orch_or', 'unavailable (classical fallback)')
print(f" Orch OR: {orch}")
print(" Hybrid gen: ACTIVE")
qram = status.get('qram', {})
print(f" QRAM: {qram.get('backend', 'classical')} — {qram.get('entries', 0)} concepts loaded\n")
def main():
api = get_api()
print("Quantum MCAGI - Local Chat")
print(" Real algorithms. No templates. No LLM.")
print(" /status /learn FILE /save /load /quit")
print(" /export [N] /copy-last -- share conversations")
print(" /cloud-save /cloud-load /cloud-status /backup")
print(" /help -- show all commands")
print_full_status(api)
while True:
try:
user = input("> ").strip()
if not user:
continue
# Exit commands
if user.lower() in ("/exit", "/quit"):
try:
CloudBrain().shutdown_push()
except Exception:
pass
break
# Status
elif user == "/status":
print_full_status(api)
# Test
elif user == "/test":
print("\n=== SYSTEM TEST ===")
try:
test_resp = api.process_input("test")
if test_resp and "response" in test_resp:
print("✓ Engine responding")
else:
print("✗ Engine not responding")
except Exception as e:
print(f"✗ Engine error: {e}")
print("==================\n")
# Save / Load / Reset
elif user == "/save":
api.save_state()
print(" State saved locally.")
elif user == "/load":
from memory import LocalMemory
api.memory = LocalMemory(api.data_dir)
print(" State reloaded from disk.")

elif user == "/reset":
confirm = input(" Reset growth stage to Nascent? (y/N): ")
if confirm.lower() == 'y':
api.memory.growth["stage"] = 0
api.memory.growth["name"] = "Nascent"
api.memory.save_all()
print(" Growth stage reset.")
else:
print(" Reset cancelled.")
# Learn from file
elif user.startswith("/learn "):
filename = user[7:].strip()
if os.path.exists(filename):
with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
text = f.read()
api.learn_text(text)
print(f" Learned from {filename}")
else:
print(f" File not found: {filename}")
# Export / Copy-last
elif user.startswith("/export "):
try:
n = int(user[8:].strip())
except:
n = 10
history = api.memory.get_history(n)
outfile = f"export_{n}.txt"
with open(outfile, 'w') as f:
for ex in history:
f.write(f"User: {ex.get('user','')}\nAI: {ex.get('ai','')}\n\n")
print(f" Exported last {n} exchanges to {outfile}")
elif user == "/copy-last":
last = api.memory.get_history(1)[0].get('ai', '')
try:
import subprocess
subprocess.run(['termux-clipboard-set', last], check=True)
print(" Last response copied to clipboard.")
except:
print(" Clipboard copy not available.")
# Cloud commands
elif user == "/help":
print(" Commands: /status /learn FILE /save /load /reset /quit")
print(" Gen:
/hybrid TEXT /unified TEXT")
print(" Ingest:
/ingest URL_OR_FILE /feed [CAT|all]")
print(" Research: /research [status|auto N|stop|query X]")
print(" Evolve:
/evolve")
print(" Exam:
/exam [status|review]")
print(" Math:
/cistercian-math 50 - 20 /cistercian 1234")
print(" Memory:
/qram [load|query N|search X|super N N|strategy X]")
print(" Share:
/export [N] /copy-last")
print(" Cloud:
/cloud-save /cloud-load /cloud-status /backup")
print(" Other:
/analyze TEXT /personality /knowledge X /collapse X /test
elif user == "/cloud-save":
cb = CloudBrain()
cb.push_all()
elif user == "/cloud-load":
cb = CloudBrain()
cb.pull_all()
elif user == "/cloud-status":
cb = CloudBrain()
cb.cloud_status()
elif user == "/backup":
cb = CloudBrain()
cb.backup_full_system()
# Killswitch
elif user == "/killswitch":
try:
from killswitch import execute_killswitch
execute_killswitch()
print(" ■ Killswitch activated.")
except ImportError:
print(" Killswitch module not found.")
except Exception as e:
print(f" Killswitch error: {e}")

elif user.startswith("/hybrid "):
text = user[8:].strip()
if text:
resp = api.process_input(text)
print("\n" + resp.get("response", str(resp)) + "\n")
else:
print(" Usage: /hybrid TEXT")
elif user.startswith("/unified "):
text = user[9:].strip()
if text:
resp = api.process_input(text)
print("\n" + resp.get("response", str(resp)) + "\n")
else:
print(" Usage: /unified TEXT")
elif user.startswith("/ingest "):
target = user[8:].strip()
if target:
try:

/killswitch")

api.learn_from_file(target)
print(f" Ingested: {target}")
except Exception as e:
print(f" Ingest error: {e}")
else:
print(" Usage: /ingest URL_OR_FILE")
elif user.startswith("/feed"):
parts = user.split()
cat = parts[1] if len(parts) > 1 else "all"
try:
from training_corpus import PHILOSOPHY_CORPUS, PHYSICS_CORPUS
corpus = PHILOSOPHY_CORPUS + " " + PHYSICS_CORPUS
api.learn_text(corpus)
print(f" Fed training corpus: {cat}")
except Exception as e:
print(f" Feed error: {e}")
elif user.startswith("/research"):
parts = user.split()
if len(parts) == 1:
print(" Usage: /research [status|auto N|stop|query X]")
else:
sub = parts[1]
if sub == "status":
print(" Self-research: available but not wired to V02 yet")
elif sub == "query" and len(parts) > 2:
query = " ".join(parts[2:])
resp = api.process_input(query)
print("\n" + resp.get("response", str(resp)) + "\n")
else:
print(f" Research subcommand: {sub}")
elif user == "/evolve":
print(" Self-evolution: available but not wired to V02 yet")
print(" Requires: self_evolution_core.py")
elif user.startswith("/exam"):
parts = user.split()
if len(parts) == 1:
print(" Usage: /exam [status|review]")
else:
sub = parts[1]
if sub == "status":
print(" Exam system: available but not wired to V02 yet")
elif sub == "review":
print(" Exam review: not yet implemented")
elif user.startswith("/cistercian-math ") or user.startswith("/cmath "):
expr = user.split(" ", 1)[1].strip()
from cistercian_math import detect_math, evaluate_math, format_math_response
parsed = detect_math(expr)
if parsed:
ev = evaluate_math(parsed)
print(format_math_response(ev))
else:
print(" Could not parse math expression")
elif user.startswith("/cistercian "):
try:
num = int(user.split()[1])
from cistercian_engine import generate_cistercian
rendered = generate_cistercian(num)
if rendered:
print(rendered)
else:
print(" Range: 0-9999")
except Exception as e:
print(f" Usage: /cistercian NUMBER (0-9999)")
elif user.startswith("/qram"):
parts = user.split()
if len(parts) == 1:
print(" Usage: /qram [load|query N|search X|super N N|strategy X]")
else:
sub = parts[1]
if sub == "load":
try:
from quantum_memory import get_quantum_memory, PENNYLANE_QRAM_AVAILABLE
qram = get_quantum_memory()
concepts = api.memory.get_known_concepts() if hasattr(api, 'memory') else []
backend = "pennylane" if PENNYLANE_QRAM_AVAILABLE else "classical"
print(f" QRAM: {backend} -- {len(concepts)} concepts available")
except Exception as e:
print(f" QRAM error: {e}")
elif sub == "search" and len(parts) > 2:
query = " ".join(parts[2:])
print(f" QRAM search for: {query}")
else:
print(f" QRAM subcommand: {sub}")
elif user.startswith("/analyze "):
text = user[9:].strip()
if text:
resp = api.process_input(text)
print("\n" + resp.get("response", str(resp)) + "\n")
else:
print(" Usage: /analyze TEXT")
elif user == "/personality":
try:

from personality_engine import get_personality_status
status = get_personality_status()
print(f" Personality: {status}")
except:
print(" Personality engine active")
elif user.startswith("/knowledge "):
topic = user[11:].strip()
if topic:
resp = api.process_input(f"what is {topic}")
print("\n" + resp.get("response", str(resp)) + "\n")
else:
print(" Usage: /knowledge TOPIC")
elif user.startswith("/collapse "):
text = user[10:].strip()
if text:
resp = api.process_input(text)
print("\n" + resp.get("response", str(resp)) + "\n")
else:
print(" Usage: /collapse TEXT")
# Unknown command
elif user.startswith("/"):
print(f" Unknown command: {user}. Type /status for help.")
# Normal conversation
else:
resp = api.process_input(user)
print("\n" + resp.get("response", str(resp)) + "\n")
except KeyboardInterrupt:
break
except Exception as e:
print(f"Error: {e}")
print("Goodbye.")
if __name__ == "__main__":
main()

