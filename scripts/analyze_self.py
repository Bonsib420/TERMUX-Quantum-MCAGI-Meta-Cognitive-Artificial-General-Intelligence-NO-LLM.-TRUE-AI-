import sys, os
sys.path.insert(0, os.path.expanduser("~/Quantum_MCAGI_NO_LLM/backend"))

from quantum_language_engine import get_language_engine
from hybrid_generator import create_hybrid_generator

backend = os.path.expanduser("~/Quantum_MCAGI_NO_LLM/backend")
engine = get_language_engine()

print("Training MCAGI on its own codebase...")
for f in os.listdir(backend):
    if f.endswith(".py"):
        try:
            content = open(os.path.join(backend, f)).read()
            engine.learn_from_text(content)
            print(f"  ✓ {f}")
        except Exception as e:
            print(f"  ✗ {f}: {e}")

gen = create_hybrid_generator(engine)

def ask(question):
    concepts_raw = engine.extract_concepts(question)
    concepts = [c if isinstance(c, str) else c.get('concept', str(c)) for c in concepts_raw]
    concept_scores = {c: 1.0 for c in concepts}
    return gen.generate(question, concepts, concept_scores)

print("\n=== QUANTUM MCAGI SELF ANALYSIS ===\n")
for q in [
    "Analyze the overall architecture of this system",
    "What are the main bugs and issues in this codebase",
    "What is the game plan for the next evolution of this system",
]:
    print(f"Q: {q}")
    print(f"A: {ask(q)}\n")
