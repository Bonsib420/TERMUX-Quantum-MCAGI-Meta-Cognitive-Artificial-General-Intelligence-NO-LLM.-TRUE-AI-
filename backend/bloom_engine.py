"""
Bloom's Taxonomy Question Generation Engine
Generates questions at different cognitive levels.
Merged from both Quantum MCAGI projects.
"""
import random
from typing import Dict, List, Optional

BLOOM_LEVELS = {
'remember': {
'templates': [
'What do you actually know about {topic}?',
'Where did you first encounter {topic}?',
'What sticks when you think about {topic}?',
],
'keywords': ['define', 'list', 'name', 'recall', 'identify'],
'complexity': 0.1,
},
'understand': {
'templates': [
'What does {topic} mean to you — not the textbook version?',
'If you had to explain {topic} without jargon, what would you say?',
'What part of {topic} do you actually understand versus repeat?',
],
'keywords': ['explain', 'describe', 'summarize', 'classify', 'discuss'],
'complexity': 0.2,
},
'apply': {
'templates': [
'Where does {topic} show up in your actual experience?',
'When was the last time {topic} mattered to you directly?',
'What changes if you take {topic} seriously?',
],
'keywords': ['apply', 'demonstrate', 'solve', 'use', 'show'],
'complexity': 0.4,
},
'analyze': {
'templates': [
'What breaks if you remove {topic} from the picture?',
'What does {topic} depend on that nobody talks about?',
'Is {topic} the cause or the symptom?',
'What would Penrose say about {topic}?',
],
'keywords': ['analyze', 'compare', 'contrast', 'distinguish', 'examine'],
'complexity': 0.6,
},
'evaluate': {
'templates': [
'Is {topic} fundamental or is it emergent from something deeper?',
'Does {topic} survive the hard problem, or does it dissolve?',
'What would it take to convince you {topic} is wrong?',
'Where does the standard view of {topic} break down?',
],
'keywords': ['evaluate', 'judge', 'critique', 'defend', 'justify'],
'complexity': 0.8,
},
'create': {
'templates': [
'What if {topic} is not what we think it is at all?',
'Imagine {topic} operates at the Planck scale — what follows?',
'What happens to {topic} if consciousness is non-computable?',
'Build a thought experiment where {topic} becomes the ground floor.',
],
'keywords': ['create', 'design', 'invent', 'imagine', 'compose'],
'complexity': 1.0,
},
}

class BloomEngine:
"""Generate questions using Bloom's Taxonomy cognitive levels."""
def __init__(self):
self.levels = BLOOM_LEVELS
self.questions_generated = 0
self.level_order = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
def generate_question(self, level: Optional[str] = None, topic: str = 'consciousness') -> Dict:
if level is None:
level = random.choice(self.level_order)
if level not in self.levels:
level = 'understand'
level_data = self.levels[level]
template = random.choice(level_data['templates'])
keyword = random.choice(level_data['keywords'])
question = template.format(topic=topic)
self.questions_generated += 1
return {
'question': question,

'level': level,
'topic': topic,
'keyword': keyword,
'cognitive_complexity': level_data['complexity'],
}
def generate_questions(
self,
topics: List[str],
growth_stage: int = 0,
count: int = 3,
) -> List[str]:
"""Generate contextually appropriate questions based on growth stage."""
if not topics:
topics = ['consciousness']
level_map = {
0: ['remember', 'understand'],
1: ['understand', 'apply'],
2: ['apply', 'analyze'],
3: ['analyze', 'evaluate'],
4: ['evaluate', 'create'],
5: ['create', 'evaluate'],
6: ['create', 'create'],
}
available_levels = level_map.get(growth_stage, ['understand', 'analyze'])
questions = []
for i in range(count):
topic = topics[i % len(topics)]
level = available_levels[i % len(available_levels)]
q = self.generate_question(level=level, topic=topic)
questions.append(q['question'])
return questions
def get_status(self) -> Dict:
return {
'levels_available': self.level_order,
'questions_generated': self.questions_generated,
'cognitive_levels': 6,
}

