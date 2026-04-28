import re, sys
from pathlib import Path
# Read hidden_thinking.py
ht = Path('hidden_thinking.py').read_text()
# Add a method to do web search (synchronous, using duckduckgo_search)
search_method = '''
def _web_search(self, query: str) -> str:
"""Perform a DuckDuckGo search and return a concise answer."""
try:
from duckduckgo_search import DDGS
with DDGS() as ddgs:
results = list(ddgs.text(query, max_results=3))
if results:
snippets = [r['body'] for r in results if r.get('body')]
if snippets:
return "\n".join(snippets[:2]) # first two snippets
return None
except Exception as e:
print(f"Web search error: {e}")
return None
'''
# Insert the method into the class (after __init__ or before process_with_thinking)
ht = ht.replace('class HiddenThinkingMode:', f'class HiddenThinkingMode:\n{search_method}')
# Now modify process_with_thinking to intercept factual questions
# Find the line where math interception ends and normal processing begins
import re
pattern = r'(# ----- NORMAL PROCESSING -----)'
replacement = '''
# ----- FACTUAL QUESTION INTERCEPT (web search) ----factual_patterns = [
(r'\\bwhere\\s+is\\s+(.+)', 'location'),
(r'\\bwhat\\s+is\\s+(.+)', 'definition'),
(r'\\bwho\\s+is\\s+(.+)', 'person'),
(r'\\bwhen\\s+did\\s+(.+)', 'date'),
(r'\\bhow\\s+many\\s+(.+)', 'number'),
]
is_factual = False
fact_query = None
user_lower = user_input.lower()
for pat, typ in factual_patterns:
m = re.match(pat, user_lower)
if m:
fact_query = m.group(1).strip()
is_factual = True
break
if is_factual and fact_query:
search_result = self._web_search(fact_query)
if search_result:
return {
"response": f"■ According to web search:\\n{search_result}",
"thinking_log": ["Used web search to answer factual question."],
"internal_questions": [],
"research_done": 1,
"confidence": 95,
"show_thinking": self.show_thinking,
"concepts": [],
"explanation": None
}
# ----- END FACTUAL INTERCEPT ----\n\g<0>'''
ht = re.sub(pattern, replacement, ht, flags=re.MULTILINE)
# Write back
Path('hidden_thinking.py').write_text(ht)
print("Patch applied. Restart chat.py")

