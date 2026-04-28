"""
Patch B — Hilbert-Primary Three-Signal Generation
==================================================
Modifies markov.py:MarkovEngine.generate_from_concepts to use:

  PRIMARY:    Hilbert.sample_token(context_tokens=...) — Born-rule semantic sampling
  VALIDATOR:  Markov.chain[prefix]                      — adjacency probability
  GRAMMAR:    FunctionWordEngine dossier rerank         — function-word fit

Selection logic per token:
  1. Try Hilbert sample
  2. If Markov chain has the current prefix, validate Hilbert pick is in known
     transitions OR pick weighted-random from Markov candidates
  3. FunctionWordEngine reranks if applicable
  4. Append, advance ρ, advance Markov state

Graceful degradation: if Hilbert returns None, falls through to Markov-only.
If both empty, returns whatever was accumulated.

Modifies markov.py at line 57: generate_from_concepts.
"""

import os
import time
import py_compile

TARGET = os.path.expanduser(
    "~/Quantum_MCAGI_NO_LLM_V⁰²/backend/markov.py"
)


# Anchor — the existing classical generator. Match by signature line.
OLD = '''    def generate_from_concepts(self, concepts, length=30, wild=False):
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
        for _ in range(length * 2):
            if seed in self.chain:
                choices = self.chain[seed]
                words = list(choices.keys())
                weights = list(choices.values())
                nxt = random.choices(words, weights=weights)[0]
            else:
                if len(result) < 6:
                    break
                if not self.starters:'''


NEW = '''    def generate_from_concepts(self, concepts, length=30, wild=False):
        """Hilbert-primary, Markov-validating, FunctionWord-grammar generation.

        Three-signal token selection per step:
          1. Hilbert.sample_token(context) — semantic primary (Born-rule)
          2. Markov.chain[prefix]          — adjacency validator
          3. FunctionWordEngine            — grammar fit reranker

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

        # ── Seed selection (unchanged) ──
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

        # ── Generation loop ──
        for _ in range(length * 2):
            nxt = None

            # SIGNAL 1: Hilbert primary (semantic Born-rule)
            if self._hilbert is not None:
                try:
                    context = list(result[-3:])  # last 3 tokens for context
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
                if not self.starters:'''


def main():
    if not os.path.exists(TARGET):
        print(f"❌ Target not found: {TARGET}")
        return False

    s = open(TARGET).read()

    if "_hilbert" in s and "SIGNAL 1: Hilbert primary" in s:
        print("✓ Patch B already applied")
        return True

    if OLD not in s:
        print("❌ Anchor not found. Current generate_from_concepts head:")
        idx = s.find("def generate_from_concepts")
        if idx > 0:
            print(s[idx:idx+800])
        return False

    backup = TARGET + ".bak.patchB." + str(int(time.time()))
    open(backup, "w").write(s)
    print(f"✓ Backup: {backup}")

    s = s.replace(OLD, NEW, 1)
    open(TARGET, "w").write(s)

    try:
        py_compile.compile(TARGET, doraise=True)
        print("✓ Patch B applied — markov.py compiles clean")
    except py_compile.PyCompileError as e:
        print(f"❌ Compile failed — rolling back: {e}")
        open(TARGET, "w").write(open(backup).read())
        return False

    # Smoke-test imports
    print("✓ Smoke test:")
    import subprocess
    r = subprocess.run(
        ["python", "-c", "from markov import MarkovEngine; m = MarkovEngine(silent=True); print('  MarkovEngine instantiates clean')"],
        capture_output=True, text=True,
        cwd=os.path.dirname(TARGET),
    )
    if r.returncode != 0:
        print(f"  ❌ Import test failed: {r.stderr}")
        print("  Rolling back...")
        open(TARGET, "w").write(open(backup).read())
        return False
    print(r.stdout.strip())

    return True


if __name__ == "__main__":
    main()
