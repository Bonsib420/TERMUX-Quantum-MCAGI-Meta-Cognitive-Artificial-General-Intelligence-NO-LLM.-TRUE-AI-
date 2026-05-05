"""
Quantum MCAGI — Native Explanation Mode
Shows real algorithmic reasoning: TF-IDF scores, Orch OR patterns,
Markov candidates, Bloom's targeting, tone detection.

No LLM. No web search. Pure transparency into the pipeline.
"""


def explain_concepts(engine, user_input):
    """
    Generate a plain-text TF‑IDF concept extraction report for the given input.
    
    Creates a multi-line report that lists extracted concepts with their term frequency (tf),
    inverse document frequency (idf), and combined score, then appends corpus vocabulary and
    document counts.
    
    Parameters:
        engine: An object providing extract_concepts(text) and an `extractor` with
            `word_frequencies` (mapping of token to document frequency) and `total_documents`.
        user_input (str): The input text to analyze for concept extraction.
    
    Returns:
        report (str): A newline-joined string containing the TF‑IDF concept report.
    """
    concepts = engine.extract_concepts(user_input)
    
    # Get raw word frequencies for scoring
    words = user_input.lower().split()
    word_freq = {}
    for w in words:
        word_freq[w] = word_freq.get(w, 0) + 1
    
    lines = []
    lines.append("  --- CONCEPT EXTRACTION (TF-IDF) ---")
    
    if concepts:
        for i, c in enumerate(concepts):
            freq = word_freq.get(c, 0)
            # Estimate TF-IDF importance
            doc_freq = engine.extractor.word_frequencies.get(c, 1)
            total_docs = max(1, engine.extractor.total_documents)
            import math
            idf = math.log(total_docs / (1 + doc_freq)) if doc_freq > 0 else 0
            tf = freq / max(1, len(words))
            score = tf * idf if idf > 0 else tf
            lines.append(f"    {c}: tf={tf:.3f} idf={idf:.2f} score={score:.4f}")
    else:
        lines.append("    (no significant concepts extracted)")
    
    lines.append(f"    Total vocabulary: {len(engine.extractor.word_frequencies)} words")
    lines.append(f"    Corpus size: {engine.extractor.total_documents} documents")
    
    return "\n".join(lines)



def explain_orch_or(engine):
    """
    Builds a human-readable Orch OR diagnostic report.
    
    If the engine has an Orch OR module loaded, includes its status, conscious moments, last temperature, per-microtubule coherence/entropy/collapses, and optional gap junctions. Otherwise indicates a classical fallback.
    
    Parameters:
        engine: Engine object exposing '_has_orch_or' boolean and 'orch_or' with a `get_status()` method.
    
    Returns:
        report (str): Multi-line diagnostic string describing Orch OR status or a classical fallback message.
    """
    lines = []
    lines.append("  --- ORCH OR (Penrose-Hameroff) ---")
    
    has_orch = getattr(engine, '_has_orch_or', False)
    orch = getattr(engine, 'orch_or', None)
    
    if has_orch and orch:
        status = orch.get_status()
        lines.append(f"    Status: ACTIVE")
        lines.append(f"    Conscious moments: {status.get('conscious_moments', 0)}")
        lines.append(f"    Temperature: {status.get('last_temperature', 0):.3f}")
        
        mts = status.get('microtubules', {})
        for name, info in mts.items():
            coh = info.get('coherence', 0)
            ent = info.get('entropy', 0)
            col = info.get('collapses', 0)
            lines.append(f"    {name}: coherence={coh:.4f}  entropy={ent:.4f}  collapses={col}")
        
        gj = status.get('gap_junctions', {})
        if gj:
            lines.append(f"    Gap junctions:")
            for junc, strength in gj.items():
                lines.append(f"      {junc}: {strength}")
    else:
        lines.append("    Status: CLASSICAL FALLBACK")
        lines.append("    (Orch OR not loaded — using probabilistic selection)")
    
    return "\n".join(lines)



def explain_tone(tone_result):
    """
    Builds a human-readable report explaining tone detection results.
    
    The returned report enumerates detected fields (register, depth, deep_markers, word_count) and, when present, VADER-style sentiment scores (`positive`, `negative`, `neutral`, `compound`). It also appends a concise decision line derived from `depth` using these thresholds:
    - depth < 0.15: casual response
    - depth < 0.35: conversational
    - depth < 0.65: analytical pipeline
    - otherwise: full quantum generation
    
    Parameters:
        tone_result (dict): Mapping containing tone analysis outputs. Expected keys:
            - 'register' (str): Named register for the input (e.g., 'conversational', 'analytical').
            - 'depth' (float): Depth score used to choose processing path.
            - 'deep_markers' (int): Count of deep/complex markers.
            - 'word_count' (int): Number of words in the input.
            - 'sentiment' (dict, optional): VADER-like scores with keys 'positive', 'negative', 'neutral', 'compound'.
    
    Returns:
        str: Multiline report describing the tone detection results and the chosen processing decision.
    """
    lines = []
    lines.append("  --- TONE DETECTION (VADER + Heuristics) ---")
    lines.append(f"    Register: {tone_result.get('register', 'unknown')}")
    lines.append(f"    Depth: {tone_result.get('depth', 0):.3f}")
    lines.append(f"    Deep markers found: {tone_result.get('deep_markers', 0)}")
    lines.append(f"    Word count: {tone_result.get('word_count', 0)}")
    
    sentiment = tone_result.get('sentiment', {})
    if sentiment:
        lines.append(f"    VADER sentiment:")
        lines.append(f"      positive={sentiment.get('positive', 0):.3f}  "
                     f"negative={sentiment.get('negative', 0):.3f}  "
                     f"neutral={sentiment.get('neutral', 0):.3f}")
        lines.append(f"      compound={sentiment.get('compound', 0):.3f}")
    
    # Explain register decision
    depth = tone_result.get('depth', 0)
    if depth < 0.15:
        reason = "Short input, no deep markers -> casual response"
    elif depth < 0.35:
        reason = "Moderate depth, some substance -> conversational"
    elif depth < 0.65:
        reason = "Multiple deep markers or questions -> analytical pipeline"
    else:
        reason = "Heavy philosophical content -> full quantum generation"
    lines.append(f"    Decision: {reason}")
    
    return "\n".join(lines)



def explain_bloom(questions, growth_stage):
    """
    Format a Bloom's Taxonomy report listing generated questions and available levels.
    
    Parameters:
        questions (list): Sequence of question entries. Each item may be a string or a dict with keys:
            - 'question' (str): the question text (fallback: str(item) if missing)
            - 'level' (str|int, optional): taxonomy level label to display
        growth_stage (int): Current growth stage used to compute the highest available taxonomy level (0-based).
    
    Returns:
        str: Multi-line report containing a header, growth stage, available levels, number of questions,
             and each question on its own line (prefixed by its level when provided).
    """
    lines = []
    lines.append("  --- BLOOM'S TAXONOMY QUESTIONS ---")
    
    level_names = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create']
    max_level = min(growth_stage + 1, 5)
    lines.append(f"    Growth stage: {growth_stage}")
    lines.append(f"    Available levels: {' -> '.join(level_names[:max_level+1])}")
    lines.append(f"    Questions generated: {len(questions)}")
    
    for i, q in enumerate(questions):
        if isinstance(q, dict):
            qtext = q.get('question', str(q))
            level = q.get('level', 'unknown')
            lines.append(f"    [{level}] {qtext}")
        else:
            lines.append(f"    {q}")
    
    return "\n".join(lines)



def explain_markov(engine, user_input):
    """
    Builds a brief diagnostic report of the Markov chain state and how it relates to the provided input.
    
    Parameters:
        engine: Object containing a `markov` attribute with `chain`, `total_tokens`, and `trained` fields.
        user_input (str): Text to compare against the Markov chain vocabulary.
    
    Returns:
        report (str): Multi-line string listing total states, transitions, training flag, up to the first 10 known words with their transition counts, and up to the first 10 unknown words.
    """
    lines = []
    lines.append("  --- MARKOV CHAIN ---")
    lines.append(f"    States: {len(engine.markov.chain)}")
    lines.append(f"    Transitions: {engine.markov.total_tokens}")
    lines.append(f"    Trained: {engine.markov.trained}")
    
    # Show what the chain knows about input words
    words = user_input.lower().split()
    known = []
    unknown = []
    for w in set(words):
        if w in engine.markov.chain:
            transitions = len(engine.markov.chain[w])
            known.append(f"{w}({transitions})")
        else:
            unknown.append(w)
    
    if known:
        lines.append(f"    Known words (transitions): {', '.join(known[:10])}")
    if unknown:
        lines.append(f"    Unknown words: {', '.join(unknown[:10])}")
    
    return "\n".join(lines)



def explain_generator(tone_result, has_hybrid):
    """
    Describe which text generator was selected and the rationale for that choice.
    
    Constructs a multi-line, human-readable report that names the chosen generator (either a hybrid quantum generator or the tone-aware composer), explains the reason based on the input register and hybrid availability, and summarizes the high-level process steps used by the selected generator.
    
    Parameters:
        tone_result (dict): Analysis result that should include a 'register' key (e.g., 'conversational', 'analytical', 'philosophical') used to determine selection.
        has_hybrid (bool): Whether the hybrid quantum generator capability is available.
    
    Returns:
        str: A newline-joined report describing the selected generator, the decision reason, and its process summary.
    """
    lines = []
    lines.append("  --- GENERATOR SELECTION ---")
    
    register = tone_result.get('register', 'conversational')
    
    if register in ('analytical', 'philosophical') and has_hybrid:
        lines.append("    Selected: HYBRID QUANTUM GENERATOR")
        lines.append("    Reason: Deep register + hybrid available")
        lines.append("    Process:")
        lines.append("      1. Markov generates 8 candidate sentences")
        lines.append("      2. TF-IDF scores each for topic relevance")
        lines.append("      3. Coherence + coverage + length scoring")
        lines.append("      4. Score = relevance*0.35 + coverage*0.25 + coherence*0.25 + length*0.15")
        lines.append("      5. Orch OR collapse biases selection (if active)")
        lines.append("      6. WordNet synonym swap on winner")
    else:
        lines.append("    Selected: TONE-AWARE COMPOSER")
        lines.append(f"    Reason: Register={register}" + 
                     (" (no hybrid available)" if not has_hybrid else ""))
        lines.append("    Process:")
        lines.append("      1. Markov-assisted opening sentence")
        lines.append("      2. Concept threading into structured response")
        lines.append("      3. Bloom's question appended if appropriate")
    
    return "\n".join(lines)



def explain_understanding(understanding, concepts, memory_concepts):
    """
    Format a human-readable report of the agent's understanding and how extracted concepts relate to memory.
    
    Parameters:
        understanding (dict): Mapping that may contain:
            - 'topic' (str): Topic label for this understanding.
            - 'understanding_score' (number): Numeric score; formatted to two decimals.
            - 'gaps' (list[str]): Missing knowledge items.
            - 'related_concepts' (list[dict|any]): Related items; each dict may include a 'concept' key.
        concepts (iterable[str]): Concepts extracted from the current input.
        memory_concepts (iterable[str]): Concepts already known/stored in memory.
    
    Returns:
        str: A multi-line textual report including Topic, Score, Known concepts, New concepts, Gaps, and Related concepts.
    """
    lines = []
    lines.append("  --- UNDERSTANDING ---")
    lines.append(f"    Topic: {understanding.get('topic', 'general')}")
    lines.append(f"    Score: {understanding.get('understanding_score', 0):.2f}")
    
    known = [c for c in concepts if c in memory_concepts]
    new = [c for c in concepts if c not in memory_concepts]
    
    if known:
        lines.append(f"    Known concepts: {', '.join(known)}")
    if new:
        lines.append(f"    New concepts: {', '.join(new)}")
    
    gaps = understanding.get('gaps', [])
    if gaps:
        lines.append(f"    Gaps: {', '.join(gaps)}")
    
    related = understanding.get('related_concepts', [])
    if related:
        lines.append(f"    Related: {', '.join(r.get('concept', str(r)) for r in related)}")
    
    return "\n".join(lines)



def explain_flavor(has_quotes, has_personality):
    """
    Describe which personality and flavor layers are active.
    
    Parameters:
        has_quotes (bool): When True, the quote-related flavor layers (quote engine, philosophical asides, dream fragments) are reported as potentially active.
        has_personality (bool): When True, the personality layer is reported as potentially active.
    
    Returns:
        str: A multi-line textual report showing the activation state and chance indications for quote and personality flavor layers.
    """
    lines = []
    lines.append("  --- PERSONALITY + FLAVOR ---")
    lines.append(f"    Quote engine: {'ACTIVE (20% chance)' if has_quotes else 'OFF'}")
    lines.append(f"    Personality: {'ACTIVE (30% chance)' if has_personality else 'OFF'}")
    lines.append(f"    Philosophical asides: {'15% chance' if has_quotes else 'OFF'}")
    lines.append(f"    Dream fragments: {'10% chance' if has_quotes else 'OFF'}")
    return "\n".join(lines)



def full_explanation(engine, user_input, concepts, questions, tone_result,
                     understanding, growth_stage, elapsed, memory_concepts,
                     has_hybrid=False, has_quotes=False, has_personality=False):
    """
                     Compose a full multi-section textual explanation of how the response was produced.
                     
                     Builds and returns a human-readable report that aggregates each internal explanation
                     section (concept extraction, tone detection, Markov state, Orch OR status, Bloom's
                     questions, understanding, generator selection, and flavor) followed by timing.
                     
                     Parameters:
                         engine: The engine instance providing extractors, markov, and other subsystems used
                             to generate per-section reports.
                         user_input (str): Original user input text used for concept and Markov analyses.
                         concepts (Iterable): Extracted concept tokens used in the understanding section.
                         questions (Iterable): Questions generated for Bloom's taxonomy reporting.
                         tone_result (dict): Tone analysis output used to build the tone and generator sections.
                         understanding (dict): Understanding summary including topic, score, gaps, and related concepts.
                         growth_stage (int): Growth stage used to determine available Bloom taxonomy levels.
                         elapsed (float): Total elapsed pipeline time in seconds to display in the timing section.
                         memory_concepts (Iterable): Previously known concepts used to compute known vs. new concepts.
                         has_hybrid (bool): Whether a hybrid (quantum) generator is available; affects generator selection wording.
                         has_quotes (bool): Whether the quote engine is enabled; affects flavor reporting.
                         has_personality (bool): Whether personality layers are enabled; affects flavor reporting.
                     
                     Returns:
                         str: The concatenated multi-section explanation report ready for display or logging.
                     """
    sections = []
    
    sections.append("")
    sections.append("  ========= HOW I REACHED THIS ANSWER =========")
    sections.append("")
    sections.append(explain_concepts(engine, user_input))
    sections.append("")
    sections.append(explain_tone(tone_result))
    sections.append("")
    sections.append(explain_markov(engine, user_input))
    sections.append("")
    sections.append(explain_orch_or(engine))
    sections.append("")
    sections.append(explain_bloom(questions, growth_stage))
    sections.append("")
    sections.append(explain_understanding(understanding, concepts, memory_concepts))
    sections.append("")
    sections.append(explain_generator(tone_result, has_hybrid))
    sections.append("")
    sections.append(explain_flavor(has_quotes, has_personality))
    sections.append("")
    sections.append(f"  --- TIMING ---")
    sections.append(f"    Total pipeline: {elapsed:.3f}s")
    sections.append("")
    sections.append("  =============================================")
    sections.append("")
    
    return "\n".join(sections)


