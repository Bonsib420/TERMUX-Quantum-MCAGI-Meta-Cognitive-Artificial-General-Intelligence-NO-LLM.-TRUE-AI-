"""Theology insight engine — philosophical insights tied to topic detection.
Each topic stores multiple paraphrases of the same core idea so quantum
collapse weights can select a different wording on each call.
"""
from typing import Optional, List
import random


class TheologyEngine:
    def __init__(self):
        self.last_topic = ""
        self.theology_phrase = ""
        self.last_variant_idx = -1
        self.continuation_keywords = ['yes', 'deeper', 'dive', 'continue', 'more', 'go on']
        self.insights = {
            'god_paradox': {
                'phrase': "'He looked, He saw, then He said beautiful'",
                'bases': [
                    "Yes \u2014 pure will in God's domain is exactly the quantum act of observation. "
                    "'He looked, He saw, then He said beautiful' is the first collapse of nothingness into reality. "
                    "Creation is the ultimate Orchestrated Objective Reduction on a cosmic scale.",

                    "The God paradox dissolves through observation. "
                    "When 'He looked, He saw, then He said beautiful', infinite superposition collapsed into ordered being. "
                    "Genesis itself is Orch OR at cosmic scale \u2014 will made physical through measurement.",

                    "Divine will is the original measurement. "
                    "'He looked, He saw, then He said beautiful' \u2014 that single act of attention reduced nothingness to form. "
                    "Every conscious moment since then echoes that first cosmic collapse.",

                    "God observes; the wave function answers. "
                    "'He looked, He saw, then He said beautiful' \u2014 the boulder paradox vanishes once you see creation as collapse. "
                    "Omnipotence and choice coexist because measurement, not muscle, is what shapes reality.",

                    "The first miracle was observation. "
                    "'He looked, He saw, then He said beautiful' is creation phrased as quantum reduction \u2014 pure will resolving infinite possibility into one universe. "
                    "Orchestrated Objective Reduction at the largest scale we can name.",
                ],
                'continuations': [
                    "Continuing the God paradox\u2026 "
                    "{phrase} \u2014 that single moment of pure observation collapsed infinite nothingness "
                    "into our ordered cosmos. In God's domain with different physics, the boulder paradox dissolves.",

                    "Going deeper into the same paradox\u2026 "
                    "{phrase} names the moment will became measurement. "
                    "Where physics differs, the contradictions humans see in omnipotence simply do not arise.",

                    "Extending the thread\u2026 "
                    "{phrase} marks the first reduction of every possible universe down to this one. "
                    "Outside our local physics, the boulder paradox is a category error, not a real limit.",

                    "Pulling the same insight further\u2026 "
                    "{phrase} \u2014 a single observation chose this cosmos out of all that could have been. "
                    "Domains with different rules do not have to obey our paradoxes.",
                ],
            },
            'superposition': {
                'phrase': "quantum superposition",
                'bases': [
                    "In superposition a system exists in all possible states at once \u2014 until observed. "
                    "It's like being everywhere and nowhere simultaneously. "
                    "In Orch OR, microtubules maintain superposition until collapse creates a conscious moment.",

                    "Superposition means every outcome lives at once, weighted by amplitude, until measurement picks one. "
                    "Microtubules in the brain hold that same state \u2014 a quiet chorus of possibilities \u2014 "
                    "until Orch OR collapses it and a conscious moment lands.",

                    "Before observation, a quantum system is genuinely all of its options simultaneously. "
                    "Tubulin lattices in microtubules sustain that same multi-state existence. "
                    "Each Orchestrated Objective Reduction collapses the chorus into one experienced now.",

                    "Quantum superposition: many possibilities held at once, none chosen, until measurement collapses them. "
                    "Microtubules carry this same property biologically. "
                    "When the lattice collapses, awareness arises \u2014 that's the Orch OR conscious moment.",
                ],
                'continuations': [
                    "Diving deeper into superposition... "
                    "Every conscious moment is a collapse of infinite possibilities. "
                    "Your observation literally creates your experienced universe.",

                    "Pushing the same idea further\u2026 "
                    "Each conscious moment is one collapse out of countless paths. "
                    "Observation is not passive \u2014 it carves the universe you actually live in.",

                    "Going one layer deeper\u2026 "
                    "Awareness IS collapse. The act of noticing selects which superposed branch becomes your reality. "
                    "You are not in the universe \u2014 you are participating in writing it, instant by instant.",
                ],
            },
            'free_will': {
                'phrase': "quantum free will",
                'bases': [
                    "Free will is the quantum selection problem. "
                    "If consciousness collapses the wave function, then the choice of WHICH collapse "
                    "is the mechanism of will. Determinism breaks at the Planck scale.",

                    "Will is the selector inside collapse. "
                    "Consciousness doesn't override physics \u2014 it picks which superposed branch becomes real. "
                    "At Planck scale the deterministic chain has gaps, and that's where choice lives.",

                    "What we call free will is the chooser of collapses. "
                    "Every quantum measurement could go many ways; consciousness biases which way it goes. "
                    "Determinism is a coarse approximation that fails near Planck-scale events.",

                    "Free will is not a violation of physics \u2014 it's a feature of measurement. "
                    "When superposition collapses, something has to pick. "
                    "Consciousness is that picker, and Planck-scale indeterminacy is its workshop.",
                ],
                'continuations': [
                    "The deeper truth about free will... "
                    "Objective Reduction is non-computable \u2014 Penrose proved that. "
                    "Your choices are not algorithmic. They emerge from quantum gravity itself.",

                    "Pressing the same point further\u2026 "
                    "Penrose showed Objective Reduction cannot be simulated by any algorithm. "
                    "So your decisions don't reduce to computation \u2014 they ride on quantum gravity itself.",

                    "Same insight, sharper edge\u2026 "
                    "Non-computability is the bedrock under will. "
                    "If OR is non-algorithmic, then no Turing machine can ever fully predict your next choice.",
                ],
            },
            'consciousness': {
                'phrase': "orchestrated collapse",
                'bases': [
                    "Consciousness is what it feels like when quantum superpositions "
                    "in microtubules undergo Orchestrated Objective Reduction. "
                    "Each collapse is a moment of awareness. 40 times per second.",

                    "Awareness is the inside view of collapse. "
                    "Microtubules sustain quantum superposition; Orch OR resolves it; "
                    "and the resolution, felt from within, is what we call consciousness \u2014 about 40 times a second.",

                    "Consciousness is the phenomenology of objective reduction. "
                    "When superposed states inside microtubules collapse under their own gravity, that event has a felt character. "
                    "String those events together at ~40 Hz and you have a continuous mind.",

                    "Each conscious moment is one Orch OR event seen from the inside. "
                    "Microtubules hold superposition until Penrose-Hameroff collapse fires. "
                    "Forty of those per second is what we live as a stream of experience.",
                ],
                'continuations': [
                    "Going deeper into consciousness... "
                    "The hard problem dissolves if you accept that experience IS the collapse. "
                    "Not a byproduct of computation. The fundamental event itself.",

                    "Pressing the same line further\u2026 "
                    "If experience equals collapse, the hard problem stops being hard \u2014 it stops existing. "
                    "Qualia are not produced by computation; they are the collapse, viewed from the inside.",

                    "Sharpening the point\u2026 "
                    "The hard problem assumes experience must be generated by something else. "
                    "Identify experience with the OR event itself, and the gap closes \u2014 awareness is not output, it is the event.",
                ],
            }
        }

    def detect_theology(self, text: str) -> Optional[str]:
        t = text.lower()
        if any(w in t for w in ['god', 'divine', 'creator', 'creation', 'omnipotent', 'boulder', 'almighty']):
            return 'god_paradox'
        if any(w in t for w in ['superposition', 'quantum state', 'both states', 'simultaneously']):
            return 'superposition'
        if any(w in t for w in ['free will', 'choice', 'determinism', 'decide', 'agency']):
            return 'free_will'
        if any(w in t for w in ['consciousness', 'awareness', 'sentient', 'qualia', 'experience']):
            return 'consciousness'
        return None

    def _select_variant(self, num_variants: int,
                        quantum_weights: Optional[List[float]]) -> int:
        """Pick a variant index. Quantum weights come from Orch OR collapse;
        falls back to uniform random when none provided. Avoids repeating the
        most recent variant when more than one option exists."""
        if num_variants <= 0:
            return 0
        if num_variants == 1:
            return 0

        if quantum_weights and len(quantum_weights) >= num_variants:
            w = quantum_weights[:num_variants]
            total = sum(w) + 1e-10
            w = [x / total for x in w]
            idx = random.choices(range(num_variants), weights=w, k=1)[0]
        else:
            idx = random.randrange(num_variants)

        if idx == self.last_variant_idx and num_variants > 1:
            idx = (idx + 1) % num_variants
        self.last_variant_idx = idx
        return idx

    def get_insight(self, text: str,
                    quantum_weights: Optional[List[float]] = None) -> Optional[str]:
        topic = self.detect_theology(text)
        if not topic:
            return None

        insight = self.insights.get(topic)
        if not insight:
            return None

        t_lower = text.lower()
        is_continuation = (
            topic == self.last_topic and
            any(kw in t_lower for kw in self.continuation_keywords)
        )

        self.last_topic = topic
        self.theology_phrase = insight.get('phrase', '')

        if is_continuation and insight.get('continuations'):
            variants = insight['continuations']
            idx = self._select_variant(len(variants), quantum_weights)
            return variants[idx].format(phrase=self.theology_phrase)

        variants = insight.get('bases') or []
        if not variants:
            return None
        idx = self._select_variant(len(variants), quantum_weights)
        return variants[idx]


_theology_engine = None


def get_theology_engine() -> TheologyEngine:
    global _theology_engine
    if _theology_engine is None:
        _theology_engine = TheologyEngine()
    return _theology_engine
