# Question System & Distribution Engine — AI Interview Coach

## Core Question System Specification
Every interview session strictly consists of **EXACTLY 10 questions**:
- **3 Project Questions**: Personalised based on candidate resume project details or general software engineering architecture trade-off questions.
- **5 Technical Skill Questions**: Intelligent distribution across candidate's selected skills from curated question banks (`data/questions/skills/*.json`).
- **2 Pseudocode / Output Prediction Questions**: Sourced from `data/questions/pseudocode.json` covering arrays, loops, recursion, OOP, pointers, complexity, and syntax.

## Server-Side Question Distribution Validation
Validation logic enforces:
1. `len(questions) == 10`
2. `count(type == 'project') == 3`
3. `count(type == 'technical') == 5`
4. `count(type == 'pseudocode') == 2`
5. `len(set(q.id)) == 10` (no duplicate IDs)
6. Technical questions match candidate skill taxonomy.
