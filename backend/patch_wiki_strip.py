"""
Patch script: Replace _clean_response in hidden_thinking.py with aggressive
wiki markup stripping.
Targets every junk pattern observed leaking into responses:
- Citation templates: {{Cite journal|...|...}}
- Pipe-delimited fields: |journal=, |first=, |doi=, |s2cid=, |pmid=, |arxiv=
- Wiki internal links: [[link|text]] -> text, [[link]] -> link
- Reference tags: <ref>...</ref>, <ref name="x"/>, all variants
- Italic/bold markers: '' '' and ''' '''
- Wiki tables: {| ... |}
- Section headers: == X ==, === X ===
- Standalone bibliographic numbers: doi:, pmid:, isbn:, arxiv: numbers
- Standalone dates: 2001-02-02, etc.
- URLs: http://, https://, www.
- Math-check artifacts from junk numbers: "(Math check: 1177/... = ...)"
- Multiple spaces collapsing to one
- Trailing/leading whitespace
"""
import os, re
TARGET = os.path.expanduser(
"~/Quantum_MCAGI_NO_LLM_V⁰²/backend/hidden_thinking.py"
)
OLD = """
def _clean_response(self, text: str) -> str:
text = re.sub(r'https?://\\S+|www\\.\\S+', '', text)
text = re.sub(r'\\{\\{[^}]+\\}\\}', '', text)
text = re.sub(r'\\|[a-z\\-]+=\\s*[^\\s]+\\s*', '', text)
text = re.sub(r'[{}|]', '', text)
text = re.sub(r'retrieved\\s+\\d+\\s+[A-Za-z]+\\s+\\d{4}', '', text, flags=re.IGNORECASE)
text = re.sub(r'doi:[^\\s]+|pmid:[^\\s]+|s2cid:[^\\s]+', '', text)
text = re.sub(r'\\s+', ' ', text).strip()
return text"""
NEW = '''
def _clean_response(self, text: str) -> str:
"""Aggressive wiki markup stripping. Targets every junk pattern observed."""
if not text:
return text
# 1. Strip nested wiki templates {{...}} including multi-line ones
# Run multiple passes to handle nested templates
for _ in range(5):
new_text = re.sub(r'\\{\\{[^{}]*\\}\\}', '', text, flags=re.DOTALL)
if new_text == text:
break
text = new_text
# 2. Strip wiki tables {| ... |}
text = re.sub(r'\\{\\|.*?\\|\\}', '', text, flags=re.DOTALL)
# 3. Strip <ref>...</ref> and <ref name="x"/> variants
text = re.sub(r'<ref[^>]*?/>', '', text)
text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', '', text) # any remaining HTML/XML tags
# 4. Wiki internal links [[link|display]] -> display, [[link]] -> link
text = re.sub(r'\\[\\[(?:[^|\\]]*\\|)?([^\\]]*)\\]\\]', r'\\1', text)
# 5. External link [http://url text] -> text
text = re.sub(r'\\[https?://\\S+\\s+([^\\]]+)\\]', r'\\1', text)
# 6. Bare URLs
text = re.sub(r'https?://\\S+', '', text)
text = re.sub(r'www\\.\\S+', '', text)
# 7. Wiki italic/bold markers
text = re.sub(r"\'{2,5}", '', text)
# 8. Section headers == ... ==, === ... ===
text = re.sub(r'={2,}\\s*[^=]+\\s*={2,}', '', text)
# 9. Pipe-delimited fields anywhere in text |key=value
# Match |word= followed by whatever isn't another pipe or end
text = re.sub(r'\\|[a-zA-Z][\\w\\-]*\\s*=\\s*[^|]*?(?=\\||$)', '', text)
# 10. Stray pipes and braces
text = re.sub(r'[|{}]', ' ', text)
# 11. Bibliographic identifiers
text = re.sub(r'\\b(?:doi|pmid|pmc|isbn|s2cid|arxiv|oclc|issn|lccn|jstor):\\s*\\S+', '', text, flags=re.IGNORECASE)
text = re.sub(r'\\b(?:doi|pmid|pmc|isbn|s2cid|arxiv|oclc|issn|lccn|jstor)\\s*=\\s*\\S+', '', text, flags=re.IGNORECASE)
# 12. "retrieved X" date phrases
text = re.sub(r'\\bretrieved\\s+\\d+\\s+[A-Za-z]+\\s+\\d{4}', '', text, flags=re.IGNORECASE)
# 13. Citation phrases that survived: "cite journal", "cite book", "cite web"
text = re.sub(r'\\bcite\\s+(?:journal|book|web|news|encyclopedia)\\b', '', text, flags=re.IGNORECASE)
# 14. Standalone ISO dates
text = re.sub(r'\\b\\d{4}-\\d{2}-\\d{2}\\b', '', text)
# 15. Junk math results from doi numbers being picked up by tail-math-check

# Pattern: "(Math check: <numeric>/<numeric> = <result>)"
text = re.sub(r'\\(Math check:\\s*[\\d./eE\\-+]+\\s*=\\s*[\\d.eE\\-+]+\\)', '', text)
# 16. Volume/issue/pages fragments that survived
text = re.sub(r'\\bvolume\\s*=?\\s*\\d+\\b', '', text, flags=re.IGNORECASE)
text = re.sub(r'\\bissue\\s*=?\\s*\\d+\\b', '', text, flags=re.IGNORECASE)
text = re.sub(r'\\bpages\\s*=?\\s*[\\d\\-\\u2013\\u2014]+\\b', '', text, flags=re.IGNORECASE)
# 17. Standalone bracket numbers (footnote refs)
text = re.sub(r'\\[\\d+\\]', '', text)
# 18. "See also" and similar leftover phrases
text = re.sub(r'\\bSee also\\b\\s*[:\\-]?', '', text, flags=re.IGNORECASE)
# 19. Stray brackets
text = re.sub(r'[\\[\\]]', '', text)
# 20. Final whitespace normalization
text = re.sub(r'\\s+([.,;:!?])', r'\\1', text)
text = re.sub(r'\\s+', ' ', text).strip()

# space before punctuation

return text'''

def main():
if not os.path.exists(TARGET):
print(f"■ Target not found: {TARGET}")
return False
s = open(TARGET).read()
if OLD not in s:
print("■ ANCHOR NOT FOUND. Current _clean_response:")
idx = s.find("def _clean_response")
if idx > 0:
end = s.find("def ", idx + 10)
print(s[idx:end] if end > 0 else s[idx:idx+800])
return False
if NEW in s:
print("✓ Already patched")
return True
# Backup before write
backup = TARGET + ".bak.wikiclean." + str(int(__import__('time').time()))
open(backup, 'w').write(s)
print(f"✓ Backup: {backup}")
s = s.replace(OLD, NEW)
open(TARGET, 'w').write(s)
print("✓ Patched _clean_response with aggressive wiki markup stripping")
# Verify it compiles
import py_compile
try:
py_compile.compile(TARGET, doraise=True)
print("✓ File compiles cleanly")
except py_compile.PyCompileError as e:
print(f"■ Compile failed — rolling back: {e}")
open(TARGET, 'w').write(open(backup).read())
return False
return True

if __name__ == "__main__":
main()

