import json
import re

with open('backend/data/questions/pseudocode.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

print(f'Total questions: {len(questions)}')
errors = []
categories = set()

forbidden_patterns = [
    r"\bSystem\.out\b", r"\bconsole\.log\b", r"\bprint\s*\(", r"\bprintf\s*\(",
    r"\bcout\s*<<", r"\bcin\s*>>", r"\bpublic\s+class\b", r"\bpublic\s+static\b",
    r"\bdef\s+[a-zA-Z_]", r"\b#include\b", r"\bimport\s+[a-zA-Z_]",
    r"\bfrom\s+[a-zA-Z_]+\s+import\b", r"\bstd::", r"\bint\s+main\b",
    r"\bchar\*", r"\bNone\b", r"\bnullptr\b",
    r"\bList<", r"\bArrayList<", r"\bvector<", r"\bHashMap<", r"\bMap<",
    r"\bdict\(", r"\bset\(", r"\blet\s+", r"\bvar\s+",
    r"\bconst\s+", r"\bfn\b", r"\bfunc\b"
]

for i, q in enumerate(questions):
    qid = q.get('id', f'index_{i}')
    categories.add(q.get('category'))
    opts = q.get('options', [])
    if len(opts) != 4:
        errors.append(f'{qid}: options count is {len(opts)}')
    opt_ids = [opt.get('id') for opt in opts]
    if opt_ids != ['A', 'B', 'C', 'D']:
        errors.append(f'{qid}: option ids are {opt_ids}')
    corr = q.get('correctOptionId') or q.get('correct_option_id')
    if corr not in ['A', 'B', 'C', 'D']:
        errors.append(f'{qid}: invalid correctOptionId {corr}')
    if not q.get('pseudocode') and not q.get('code_snippet'):
        errors.append(f'{qid}: missing pseudocode')
    if not q.get('input') and not q.get('input_description'):
        errors.append(f'{qid}: missing input')
    
    # Check language independence
    content = f"{q.get('question','')} {q.get('pseudocode','')} {q.get('code_snippet','')} {q.get('input','')} {q.get('input_description','')}"
    for pat in forbidden_patterns:
        match = re.search(pat, content, re.IGNORECASE)
        if match:
            errors.append(f'{qid}: matched forbidden pattern {pat}: {match.group(0)}')

print(f'Categories found: {categories}')
print(f'Errors found: {len(errors)}')
for e in errors:
    print('  -', e)
