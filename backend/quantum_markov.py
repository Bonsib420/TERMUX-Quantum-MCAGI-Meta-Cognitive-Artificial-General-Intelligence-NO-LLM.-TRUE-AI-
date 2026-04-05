"""
Quantum Markov Chain Module
============================
Exports the MarkovChain class for use throughout the system and for
installation verification.

The MarkovChain class implements variable-order (1–3) Markov chain
text generation with temperature-controlled weighted random selection.

Math: P(w_n | w_{n-1}, ..., w_{n-k}) = count(w_{n-k}...w_n) / count(w_{n-k}...w_{n-1})
"""

from quantum_language_composers import MarkovChain

__all__ = ["MarkovChain"]


def test_markov_chain() -> bool:
    """
    Module-level smoke test — verifies the MarkovChain can be trained
    and generates non-empty output.

    Returns:
        True if the test passes, False otherwise.
    """
    corpus = (
        "Quantum mechanics describes the behavior of matter at atomic scales. "
        "The wave function encodes all possible states of a system. "
        "Observation collapses the wave function to a definite outcome. "
        "Entanglement links two particles so their states are correlated. "
        "The Markov property states future states depend only on the present."
    )
    chain = MarkovChain(order=2)
    chain.train(corpus)
    if not chain.trained:
        return False
    result = chain.generate(max_words=20)
    return isinstance(result, str) and len(result) > 0


if __name__ == "__main__":
    passed = test_markov_chain()
    print("quantum_markov: OK" if passed else "quantum_markov: FAIL")
