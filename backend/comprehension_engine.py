"""
Comprehension Engine — Quantum MCAGI
Understands WHAT the user is saying, not just which words they used.
Detects intent, extracts claims/arguments, identifies relationships between concepts,
and generates comprehension-aware response guidance.

No LLM. Pattern matching, structural analysis, and semantic decomposition.
"""

import re
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


QUESTION_STARTERS = {
    'what', 'how', 'why', 'when', 'where', 'who', 'which', 'whose',
    'is', 'are', 'was', 'were', 'do', 'does', 'did', 'can', 'could',
    'would', 'should', 'will', 'have', 'has', 'had',
}

CAUSAL_MARKERS = [
    (r'\bbecause\b', 'reason'),
    (r'\bsince\b', 'reason'),
    (r'\btherefore\b', 'conclusion'),
    (r'\bso\b', 'conclusion'),
    (r'\bthus\b', 'conclusion'),
    (r'\bhence\b', 'conclusion'),
    (r'\bcauses?\b', 'causation'),
    (r'\bleads?\s+to\b', 'causation'),
    (r'\bresults?\s+in\b', 'causation'),
    (r'\bmeans?\s+that\b', 'implication'),
    (r'\bimplies?\b', 'implication'),
    (r'\bif\b.*\bthen\b', 'conditional'),
]

OPINION_MARKERS = [
    r'\bi\s+think\b', r'\bi\s+believe\b', r'\bi\s+feel\b',
    r'\bin\s+my\s+opinion\b', r'\bto\s+me\b', r'\bfor\s+me\b',
    r'\bi\s+reckon\b', r'\bi\s+suspect\b', r'\bseems?\s+like\b',
    r'\bprobably\b', r'\bmaybe\b', r'\bperhaps\b',
    r'\bi\s+would\s+say\b', r'\bi\s+bet\b',
]

ASSERTION_MARKERS = [
    r'\bis\b', r'\bare\b', r'\bwas\b', r'\bwere\b',
    r'\bexists?\b', r'\bmust\b', r'\bhas\s+to\b',
    r'\balways\b', r'\bnever\b', r'\bevery\b', r'\ball\b', r'\bnone\b',
    r'\bclearly\b', r'\bobviously\b', r'\bcertainly\b',
]

CONTRAST_MARKERS = [
    r'\bbut\b', r'\bhowever\b', r'\balthough\b', r'\bthough\b',
    r'\byet\b', r'\bstill\b', r'\bdespite\b', r'\bin\s+contrast\b',
    r'\bon\s+the\s+other\s+hand\b', r'\bnevertheless\b',
    r'\binstead\b', r'\brather\b', r'\bwhereas\b',
]

AGREEMENT_MARKERS = [
    r'\byes\b', r'\byeah\b', r'\bright\b', r'\bexactly\b',
    r'\bagree\b', r'\btrue\b', r'\bcorrect\b', r'\babsolutely\b',
    r'\bdefinitely\b', r'\bfair\b', r'\bgood\s+point\b',
]

DISAGREEMENT_MARKERS = [
    r'\bno\b', r'\bnot\s+really\b', r'\bwrong\b', r'\bdisagree\b',
    r'\bbullshit\b', r'\bnonsense\b', r'\bactually\b',
    r'\bnot\s+true\b', r'\bthat\'s\s+not\b', r'\bnah\b',
]

RELATIONSHIP_PATTERNS = [
    (r'(\w+)\s+(?:is|are)\s+(?:a\s+)?(?:form|type|kind)\s+of\s+(\w+)', 'is_type_of'),
    (r'(\w+)\s+(?:is|are)\s+(?:like|similar\s+to)\s+(\w+)', 'analogous_to'),
    (r'(\w+)\s+(?:causes?|creates?|produces?)\s+(\w+)', 'causes'),
    (r'(\w+)\s+(?:depends?\s+on|requires?|needs?)\s+(\w+)', 'depends_on'),
    (r'(\w+)\s+(?:is|are)\s+(?:part|component)\s+of\s+(\w+)', 'part_of'),
    (r'(\w+)\s+(?:and|with)\s+(\w+)\s+(?:are|is)\s+(?:connected|related|linked)', 'connected_to'),
    (r'without\s+(\w+).*(?:no|not|can\'t)\s+.*(\w+)', 'required_for'),
    (r'(\w+)\s+(?:isn\'t|is\s+not|aren\'t|are\s+not)\s+(\w+)', 'negation'),
]


class ComprehensionEngine:
    """Understands user input beyond keyword extraction."""

    def __init__(self):
        self.conversation_thread = []
        self.active_claims = []
        self.active_topic_stack = []
        self.unresolved_questions = []

    def comprehend(self, user_input: str, concepts: List[str],
                   context: Optional[Dict] = None) -> Dict:
        text = user_input.strip()
        lower = text.lower()

        intent = self._detect_intent(text, lower, context)
        claims = self._extract_claims(text, lower)
        relationships = self._extract_relationships(lower)
        stance = self._detect_stance(lower, context)
        complexity = self._assess_complexity(text, lower, concepts)
        thread_position = self._assess_thread_position(text, lower, concepts, context)

        self._update_thread(user_input, intent, claims, concepts)

        engagement_directives = self._generate_directives(
            intent, claims, relationships, stance, complexity, thread_position, concepts, context
        )

        return {
            'intent': intent,
            'claims': claims,
            'relationships': relationships,
            'stance': stance,
            'complexity': complexity,
            'thread_position': thread_position,
            'directives': engagement_directives,
            'active_claims': self.active_claims[-5:],
            'topic_stack': self.active_topic_stack[-3:],
        }

    def _detect_intent(self, text: str, lower: str, context: Optional[Dict]) -> Dict:
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        intents = []
        for sent in sentences:
            sent_lower = sent.lower()
            words = sent_lower.split()
            if not words:
                continue

            if words[0] in QUESTION_STARTERS or sent.endswith('?'):
                q_type = self._classify_question(sent_lower, words)
                intents.append({'type': 'question', 'subtype': q_type, 'text': sent})
            elif any(re.search(p, sent_lower) for p in OPINION_MARKERS):
                intents.append({'type': 'opinion', 'text': sent})
            elif any(re.search(p, sent_lower) for p in CONTRAST_MARKERS):
                intents.append({'type': 'counterpoint', 'text': sent})
            elif len(words) <= 3 and any(re.search(p, sent_lower) for p in AGREEMENT_MARKERS):
                intents.append({'type': 'agreement', 'text': sent})
            elif any(re.search(p, sent_lower) for p in DISAGREEMENT_MARKERS):
                intents.append({'type': 'disagreement', 'text': sent})
            elif any(re.search(pat, sent_lower) for pat, _ in CAUSAL_MARKERS):
                intents.append({'type': 'argument', 'text': sent})
            elif len(words) <= 4:
                intents.append({'type': 'brief', 'text': sent})
            else:
                intents.append({'type': 'statement', 'text': sent})

        primary = intents[0] if intents else {'type': 'statement', 'text': text}
        return {
            'primary': primary['type'],
            'all': intents,
            'has_question': any(i['type'] == 'question' for i in intents),
            'has_argument': any(i['type'] == 'argument' for i in intents),
            'has_opinion': any(i['type'] == 'opinion' for i in intents),
            'has_counterpoint': any(i['type'] == 'counterpoint' for i in intents),
        }

    def _classify_question(self, sent_lower: str, words: List[str]) -> str:
        first = words[0] if words else ''
        if first == 'why':
            return 'causal'
        elif first == 'how':
            if len(words) > 1 and words[1] in ('much', 'many', 'long', 'far', 'often'):
                return 'quantitative'
            return 'mechanistic'
        elif first == 'what':
            if 'mean' in sent_lower or 'definition' in sent_lower:
                return 'definitional'
            if 'happen' in sent_lower or 'would' in sent_lower:
                return 'hypothetical'
            return 'factual'
        elif first == 'who':
            return 'identity'
        elif first in ('is', 'are', 'was', 'were', 'do', 'does', 'did', 'can', 'could'):
            return 'yes_no'
        elif first in ('would', 'should', 'could'):
            return 'hypothetical'
        return 'open'

    def _extract_claims(self, text: str, lower: str) -> List[Dict]:
        claims = []
        sentences = re.split(r'[.!?]+', text)

        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            sent_lower = sent.lower()

            if sent.endswith('?') or (sent_lower.split() and sent_lower.split()[0] in QUESTION_STARTERS):
                continue

            for pattern, marker_type in CAUSAL_MARKERS:
                if re.search(pattern, sent_lower):
                    claims.append({
                        'text': sent,
                        'type': marker_type,
                        'strength': 'strong' if marker_type in ('conclusion', 'causation') else 'moderate',
                    })
                    break
            else:
                has_strong_assertion = any(re.search(p, sent_lower) for p in
                    [r'\balways\b', r'\bnever\b', r'\bmust\b', r'\bclearly\b', r'\bobviously\b', r'\bcertainly\b'])

                if has_strong_assertion:
                    claims.append({
                        'text': sent,
                        'type': 'assertion',
                        'strength': 'strong',
                    })
                elif len(sent.split()) >= 5 and any(re.search(p, sent_lower) for p in ASSERTION_MARKERS[:4]):
                    has_opinion = any(re.search(p, sent_lower) for p in OPINION_MARKERS)
                    claims.append({
                        'text': sent,
                        'type': 'opinion' if has_opinion else 'claim',
                        'strength': 'moderate' if has_opinion else 'moderate',
                    })

        return claims

    def _extract_relationships(self, lower: str) -> List[Dict]:
        relationships = []
        for pattern, rel_type in RELATIONSHIP_PATTERNS:
            matches = re.finditer(pattern, lower)
            for m in matches:
                if m.lastindex and m.lastindex >= 2:
                    relationships.append({
                        'subject': m.group(1),
                        'object': m.group(2),
                        'relation': rel_type,
                    })
        return relationships

    def _detect_stance(self, lower: str, context: Optional[Dict]) -> Dict:
        agrees = sum(1 for p in AGREEMENT_MARKERS if re.search(p, lower))
        disagrees = sum(1 for p in DISAGREEMENT_MARKERS if re.search(p, lower))
        contrasts = sum(1 for p in CONTRAST_MARKERS if re.search(p, lower))

        if disagrees > 0 or contrasts > 1:
            position = 'opposing'
        elif agrees > 0 and disagrees == 0:
            position = 'aligned'
        elif contrasts == 1:
            position = 'nuancing'
        else:
            position = 'neutral'

        return {
            'position': position,
            'agreement_signals': agrees,
            'disagreement_signals': disagrees,
            'contrast_signals': contrasts,
        }

    def _assess_complexity(self, text: str, lower: str, concepts: List[str]) -> Dict:
        words = lower.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]

        subordinate_clauses = len(re.findall(r'\b(because|although|while|whereas|since|if|unless|when|after|before)\b', lower))
        unique_ratio = len(set(words)) / max(len(words), 1)

        if len(words) <= 5:
            level = 'minimal'
        elif len(words) <= 15 and subordinate_clauses == 0:
            level = 'simple'
        elif subordinate_clauses >= 2 or len(concepts) >= 4:
            level = 'complex'
        elif len(words) > 30 or len(sentences) >= 3:
            level = 'elaborate'
        else:
            level = 'moderate'

        return {
            'level': level,
            'word_count': len(words),
            'sentence_count': len(sentences),
            'subordinate_clauses': subordinate_clauses,
            'vocabulary_richness': round(unique_ratio, 3),
            'concept_density': round(len(concepts) / max(len(words), 1), 3),
        }

    def _assess_thread_position(self, text: str, lower: str,
                                 concepts: List[str], context: Optional[Dict]) -> Dict:
        if not context or not context.get('recent_exchanges'):
            return {'position': 'opening', 'depth': 0, 'topic_continuity': 0.0}

        recent = context.get('recent_exchanges', [])
        depth = len(recent)
        recent_concepts = context.get('recent_concepts', [])

        if recent_concepts and concepts:
            shared = set(c.lower() for c in concepts) & set(c.lower() for c in recent_concepts)
            continuity = len(shared) / max(len(concepts), 1)
        else:
            continuity = 0.0

        last_ai = context.get('last_ai_response', '')
        references_response = False
        if last_ai:
            ai_words = set(last_ai.lower().split())
            user_words = set(lower.split())
            overlap = ai_words & user_words - {'the', 'a', 'is', 'are', 'was', 'it', 'that', 'this', 'to', 'of', 'and', 'in', 'for'}
            references_response = len(overlap) >= 3

        if depth == 0:
            position = 'opening'
        elif continuity > 0.5 and references_response:
            position = 'deep_engagement'
        elif continuity > 0.3:
            position = 'continuing'
        elif continuity > 0.0:
            position = 'branching'
        else:
            position = 'new_thread'

        return {
            'position': position,
            'depth': depth,
            'topic_continuity': round(continuity, 3),
            'references_previous': references_response,
        }

    def _update_thread(self, user_input: str, intent: Dict,
                       claims: List[Dict], concepts: List[str]):
        self.conversation_thread.append({
            'input': user_input,
            'intent': intent['primary'],
            'concepts': concepts,
        })
        if len(self.conversation_thread) > 20:
            self.conversation_thread = self.conversation_thread[-20:]

        for claim in claims:
            self.active_claims.append(claim)
        if len(self.active_claims) > 10:
            self.active_claims = self.active_claims[-10:]

        if concepts:
            for c in concepts:
                if c not in self.active_topic_stack:
                    self.active_topic_stack.append(c)
            if len(self.active_topic_stack) > 8:
                self.active_topic_stack = self.active_topic_stack[-8:]

    def _generate_directives(self, intent: Dict, claims: List[Dict],
                              relationships: List[Dict], stance: Dict,
                              complexity: Dict, thread_position: Dict,
                              concepts: List[str], context: Optional[Dict]) -> Dict:
        directives = {
            'respond_to_argument': False,
            'answer_question': False,
            'acknowledge_stance': False,
            'match_complexity': complexity['level'],
            'engagement_mode': 'default',
            'response_seeds': [],
            'avoid': [],
        }

        if intent['has_question']:
            directives['answer_question'] = True
            questions = [i for i in intent['all'] if i['type'] == 'question']
            if questions:
                q = questions[0]
                subtype = q.get('subtype', 'open')
                if subtype == 'causal':
                    directives['engagement_mode'] = 'explain_why'
                    directives['response_seeds'].append(f"address_cause_of_{concepts[0] if concepts else 'topic'}")
                elif subtype == 'mechanistic':
                    directives['engagement_mode'] = 'explain_how'
                    directives['response_seeds'].append(f"explain_mechanism_{concepts[0] if concepts else 'topic'}")
                elif subtype == 'definitional':
                    directives['engagement_mode'] = 'define'
                    directives['response_seeds'].append(f"define_{concepts[0] if concepts else 'topic'}")
                elif subtype == 'yes_no':
                    directives['engagement_mode'] = 'take_position'
                elif subtype == 'hypothetical':
                    directives['engagement_mode'] = 'explore_possibility'
                else:
                    directives['engagement_mode'] = 'address_question'

        if intent['has_argument'] or claims:
            directives['respond_to_argument'] = True
            if not directives['answer_question']:
                directives['engagement_mode'] = 'engage_argument'
            for claim in claims[:2]:
                directives['response_seeds'].append(f"engage_{claim['type']}:{claim['text'][:60]}")

        if stance['position'] in ('opposing', 'nuancing'):
            directives['acknowledge_stance'] = True
            directives['avoid'].append('repeat_previous_point')
            if stance['position'] == 'opposing':
                directives['engagement_mode'] = 'counter_or_concede'

        if stance['position'] == 'aligned':
            directives['avoid'].append('redundant_agreement')
            if directives['engagement_mode'] == 'default':
                directives['engagement_mode'] = 'build_on'

        if thread_position['position'] == 'deep_engagement':
            directives['avoid'].append('surface_level_response')
            if directives['engagement_mode'] == 'default':
                directives['engagement_mode'] = 'go_deeper'

        if thread_position['position'] == 'new_thread':
            if directives['engagement_mode'] == 'default':
                directives['engagement_mode'] = 'fresh_take'

        if thread_position['position'] == 'opening':
            if directives['engagement_mode'] == 'default':
                directives['engagement_mode'] = 'establish_ground'

        if complexity['level'] == 'minimal':
            if directives['engagement_mode'] == 'default':
                directives['engagement_mode'] = 'brief_and_direct'

        if complexity['level'] in ('complex', 'elaborate') and directives['engagement_mode'] == 'default':
            directives['engagement_mode'] = 'match_depth'

        if relationships:
            for rel in relationships[:2]:
                directives['response_seeds'].append(
                    f"relationship:{rel['subject']}_{rel['relation']}_{rel['object']}"
                )

        if directives['engagement_mode'] == 'default':
            directives['engagement_mode'] = 'conversational'

        return directives

    def get_status(self) -> Dict:
        return {
            'thread_length': len(self.conversation_thread),
            'active_claims': len(self.active_claims),
            'topic_stack': self.active_topic_stack[-5:],
            'last_intent': self.conversation_thread[-1]['intent'] if self.conversation_thread else None,
        }
