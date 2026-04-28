"""
Patch A — Two-Tier Ingestion
=============================
Wires FunctionWordEngine into QuantumLanguageEngine so every learned text
feeds BOTH tiers:
  • Tier 1 (content): existing markov + extractor + coherence
  • Tier 2 (function): NEW FunctionWordEngine.update_from_text()

Three insertions:
  1. Add `self.fwe` to QuantumLanguageEngine.__init__ near self.coherence
  2. Add fwe.update_from_text in learn_from_text
  3. Add fwe.save() in save_state

Plus auto-load existing dossier on init.

Safe — auto-backup, compile-check, auto-rollback on import failure.
"""

import os, time, py_compile, shutil, subprocess

TARGET = os.path.expanduser(
    "~/Quantum_MCAGI_NO_LLM_V⁰²/backend/quantum_language_engine.py"
)


def main():
    if not os.path.exists(TARGET):
        print(f"❌ Target not found: {TARGET}")
        return False

    s = open(TARGET).read()

    # Backup
    backup = TARGET + ".bak.fwe_ingestion." + str(int(time.time()))
    shutil.copy2(TARGET, backup)
    print(f"✓ Backup: {backup}")

    # ───── Insertion 1: __init__ wiring ─────
    OLD_INIT = """        self.markov = MarkovChain(order=2)
        self.extractor = ConceptExtractor()
        self.question_gen = QuestionGenerator(self.extractor)
        self.composer = ResponseComposer(self.markov, self.extractor)
        self.coherence = CoherenceScorer()"""

    NEW_INIT = """        self.markov = MarkovChain(order=2)
        self.extractor = ConceptExtractor()
        self.question_gen = QuestionGenerator(self.extractor)
        self.composer = ResponseComposer(self.markov, self.extractor)
        self.coherence = CoherenceScorer()
        # Tier 2: function-word dossier engine (graceful no-op if module missing)
        self.fwe = None
        try:
            from function_word_engine import FunctionWordEngine
            self.fwe = FunctionWordEngine(stopwords_set=ConceptExtractor.STOPWORDS)
            _fwe_path = os.path.expanduser("~/.quantum-mcagi/function_words.json")
            try:
                if os.path.exists(_fwe_path):
                    self.fwe.load(_fwe_path)
            except Exception:
                pass
        except ImportError:
            self.fwe = None"""

    if OLD_INIT not in s:
        print("❌ Insertion 1 anchor not found — file may have been modified")
        return False
    if NEW_INIT in s:
        print("✓ Insertion 1 already done")
    else:
        s = s.replace(OLD_INIT, NEW_INIT)
        print("✓ Insertion 1: __init__ wired")

    # ───── Insertion 2: learn_from_text hook ─────
    OLD_LEARN = """    def learn_from_text(self, text: str):
        \"\"\"Feed text to the Markov chain and concept extractor to improve generation.\"\"\"
        self.markov.train(text)
        self.extractor.update_corpus_stats(text)
        self.coherence.update(text)"""

    NEW_LEARN = """    def learn_from_text(self, text: str):
        \"\"\"Feed text to BOTH tiers: content (markov/extractor/coherence) and function (fwe).\"\"\"
        self.markov.train(text)
        self.extractor.update_corpus_stats(text)
        self.coherence.update(text)
        # Tier 2: feed FunctionWordEngine if available
        if self.fwe is not None:
            try:
                self.fwe.update_from_text(text)
            except Exception:
                pass"""

    if OLD_LEARN not in s:
        print("❌ Insertion 2 anchor not found — rolling back")
        open(TARGET, 'w').write(open(backup).read())
        return False
    if NEW_LEARN in s:
        print("✓ Insertion 2 already done")
    else:
        s = s.replace(OLD_LEARN, NEW_LEARN)
        print("✓ Insertion 2: learn_from_text wired")

    # ───── Insertion 3: save_state hook ─────
    OLD_SAVE = """        with open(os.path.join(directory, 'corpus_stats.json'), 'w') as f:
            json.dump(stats, f)"""

    NEW_SAVE = """        with open(os.path.join(directory, 'corpus_stats.json'), 'w') as f:
            json.dump(stats, f)
        # Tier 2: persist FunctionWordEngine dossier
        if getattr(self, 'fwe', None) is not None:
            try:
                _fwe_path = os.path.expanduser("~/.quantum-mcagi/function_words.json")
                self.fwe.save(_fwe_path)
            except Exception:
                pass"""

    if OLD_SAVE not in s:
        print("❌ Insertion 3 anchor not found — rolling back")
        open(TARGET, 'w').write(open(backup).read())
        return False
    if NEW_SAVE in s:
        print("✓ Insertion 3 already done")
    else:
        s = s.replace(OLD_SAVE, NEW_SAVE)
        print("✓ Insertion 3: save_state wired")

    # Write
    open(TARGET, 'w').write(s)

    # Compile-check
    try:
        py_compile.compile(TARGET, doraise=True)
        print("✓ File compiles cleanly")
    except py_compile.PyCompileError as e:
        print(f"❌ Compile failed — rolling back: {e}")
        open(TARGET, 'w').write(open(backup).read())
        return False

    # Import-check
    r = subprocess.run(
        ["python", "-c",
         "import sys; sys.path.insert(0, '.'); import quantum_language_engine; print('OK')"],
        cwd=os.path.dirname(TARGET),
        capture_output=True, text=True
    )
    if r.returncode != 0:
        print(f"❌ Import failed — rolling back:\n{r.stderr}")
        open(TARGET, 'w').write(open(backup).read())
        return False
    print("✓ Module imports cleanly")

    print()
    print("🎯 Patch A deployed: ingestion now feeds both tiers")
    print(f"   Rollback if needed: cp {backup} {TARGET}")
    return True


if __name__ == "__main__":
    main()
