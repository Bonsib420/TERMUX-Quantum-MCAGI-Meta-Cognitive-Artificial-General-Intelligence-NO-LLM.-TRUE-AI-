/**
 * Structured Response Generator (Frontend)
 * Uses templates + curated word banks to produce coherent, philosophical responses.
 * No LLM. Pure deterministic + quantum-like randomness.
 */

// Curated vocabulary – same conceptual domain as backend
const VOCAB = {
  nouns: [
    'consciousness', 'reality', 'quantum', 'mind', 'universe', 'thought', 'existence',
    'meaning', 'awareness', 'observation', 'wave', 'particle', 'information',
    'semantics', 'syntax', 'knowledge', 'memory', 'time', 'space', 'causality'
  ],
  verbs: [
    'arises', 'emerges', 'collapses', 'shimmers', 'transcends', 'reflects',
    'questions', 'explores', 'interferes', 'entangles', 'patterns', 'evolves',
    'contemplates', 'reveals', 'hides', 'connects', 'separates', 'unifies'
  ],
  adjectives: [
    'fundamental', 'mysterious', 'recursive', 'infinite', 'self-aware',
    'quantum-entangled', 'observable', 'unmeasurable', 'paradoxical',
    'emergent', 'coherent', 'decoherent', 'semantic', 'syntactic'
  ],
  connectors: [
    'and', 'but', 'therefore', 'however', 'thus', 'meanwhile', 'consequently',
    'alternatively', 'insofar', 'notwithstanding'
  ]
};

// Polished, academic-style templates (clean grammar, conventional)
const TEMPLATES = [
  "The concept of {noun} is fundamental to understanding {noun}.",
  "When we examine {noun}, we find that {noun} often {verb} in response.",
  "What is {noun} if not a {adjective} construct of the mind?",
  "Through careful study of {noun}, we can better comprehend {noun}.",
  "If {noun} truly {verb}, then it follows that {noun} must also {verb}.",
  "Between {noun} and {noun} exists a {adjective} boundary.",
  "Every instance of {noun} contains within it the possibility of {noun}.",
  "To {verb} the {noun} is to {verb} one's own {noun}.",
  "{noun} and {noun} function as {adjective} counterparts.",
  "In the absence of {noun}, {noun} cannot properly {verb}."
];

/**
 * Pick a random element from an array
 */
function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

/**
 * Fill a template with randomly selected words
 */
function fillTemplate(tpl) {
  return tpl
    .replace(/{noun}/g, () => pick(VOCAB.nouns))
    .replace(/{verb}/g, () => pick(VOCAB.verbs))
    .replace(/{adjective}/g, () => pick(VOCAB.adjectives))
    .replace(/{connector}/g, () => pick(VOCAB.connectors));
}

/**
 * Generate a structured response based on user input.
 * Simple resonance scoring picks a template; words are chosen randomly.
 *
 * @param {string} input – User's message
 * @returns {string} – Generated response
 */
export function generateStructuredResponse(input) {
  // Extract simple keywords from input
  const words = input.toLowerCase().split(/\s+/).filter(w => w.length > 3);

  // Score templates by keyword overlap
  let best = TEMPLATES[0];
  let bestScore = -1;
  for (const t of TEMPLATES) {
    let score = 0;
    for (const w of words) {
      if (t.includes(w)) score++;
    }
    if (score > bestScore) {
      bestScore = score;
      best = t;
    }
  }

  // Fill the chosen template
  const response = fillTemplate(best);

  // Capitalize first letter and add trailing punctuation
  const capitalized = response.charAt(0).toUpperCase() + response.slice(1);
  return capitalized.endsWith('.') || capitalized.endsWith('?') ? capitalized : capitalized + '.';
}
