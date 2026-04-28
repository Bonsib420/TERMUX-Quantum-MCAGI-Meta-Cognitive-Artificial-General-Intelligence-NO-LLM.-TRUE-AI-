"""
Spell Correction — Uses Markov vocabulary as dictionary.
Fixes typos before concept extraction so junk doesn't persist.
"""


def levenshtein(s1, s2):
    """levenshtein - Auto-documented by self-evolution."""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
        prev = curr
    return prev[-1]


def build_corrector(markov_chain):
    """build_corrector - Auto-documented by self-evolution."""
    vocab = set(markov_chain.keys())
    # Only words 3+ chars to avoid matching noise
    vocab = {w for w in vocab if len(w) >= 3 and w.isalpha()}
    return vocab


def correct_word(word, vocab, max_dist=None):
    """correct_word - Auto-documented by self-evolution."""
    w = word.lower()
    if max_dist is None:
        max_dist = 2 if len(w) <= 6 else 3
    if w in vocab:
        return word
    if len(w) < 3:
        return word
    if not w.isalpha():
        return word
    best = None
    best_dist = max_dist + 1
    for v in vocab:
        if abs(len(v) - len(w)) > max_dist:
            continue
        if v[0] != w[0]:
            continue
        d = levenshtein(w, v)
        if d < best_dist:
            best_dist = d
            best = v
    if best and best_dist <= max_dist:
        return best
    return word


def correct_text(text, vocab):
    """correct_text - Auto-documented by self-evolution."""
    words = text.split()
    corrected = []
    fixes = []
    for w in words:
        clean = w.strip('.,!?;:()[]"\'')
        fixed = correct_word(clean, vocab)
        if fixed != clean:
            fixes.append((clean, fixed))
            corrected.append(w.replace(clean, fixed))
        else:
            corrected.append(w)
    return ' '.join(corrected), fixes


if __name__ == "__main__":
    test_vocab = {'consciousness', 'quantum', 'reality', 'perceive', 'superposition', 'what', 'experience', 'existence', 'spacetime'}
    tests = ['whata', 'precive', 'superpositioning', 'consciousnes', 'quantm', 'realty']
    for t in tests:
        fixed = correct_word(t, test_vocab)
        print(f"  {t} -> {fixed}")
