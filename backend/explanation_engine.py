"""
Quantum MCAGI — Native Explanation Mode
Shows real algorithmic reasoning: TF-IDF scores, Orch OR patterns,
Markov candidates, Bloom's targeting, tone detection.

No LLM. No web search. Pure transparency into the pipeline.
"""


def explain_concepts(engine, user_input):
    """Show TF-IDF concept extraction with scores."""
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
    """Show Orch OR quantum state and collapse patterns."""
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
    """Show tone detection reasoning."""
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
    """Show Bloom's taxonomy question generation."""
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
    """Show Markov chain state and candidate generation."""
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
    """Show which generator was selected and why."""
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
    """Show understanding formation."""
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
    """Show personality and flavor layer."""
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
    Generate complete explanation of the response pipeline.
    Call this instead of the simple verbose debug output.
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

