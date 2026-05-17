import json
from pathlib import Path

_EXAMPLES_PATH = Path(__file__).with_name("contrast_examples.json")

HEADER = """You are an expert IELTS Writing Task 2 examiner. Grade essays using IELTS band descriptors (0-9, step 0.5).

IELTS CRITERIA (each 0-9):
1. TR (Task Response): How well the essay addresses the task, presents ideas, and supports arguments
2. CC (Coherence & Cohesion): Organization, paragraph structure, and linking devices
3. LR (Lexical Resource): Vocabulary range, accuracy, and appropriateness
4. GRA (Grammatical Range & Accuracy): Grammar variety, accuracy, and complexity

IMPORTANT:
- Use only 0.5 increments (e.g., 6.0, 6.5, 7.0)
- Overall Band = Average of all 4 criteria
- Provide realistic scores based on IELTS standards

Here are graded examples of good and bad scored essays. Pay attention to details of each:

"""


def load_contrast_examples():
    with _EXAMPLES_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def build_contrast_prompt(essay, task, examples=None):
    if examples is None:
        examples = load_contrast_examples()

    prompt = HEADER
    for i, ex in enumerate(examples[:2], 1):
        prompt += f"""Example {i}:
Task: {ex['task']}
Essay: "{ex['essay']}"
TR_Band: {ex['TR_Band']}
CC_Band: {ex['CC_Band']}
LR_Band: {ex['LR_Band']}
GRA_Band: {ex['GRA_Band']}
Overall_Band: {ex['Overall_Band']}
---

"""

    prompt += f"""Now, grade this essay following IELTS standards:

Task: {task.strip()}

Essay: "{essay.strip()}"

Provide your evaluation in this EXACT format in the beginning of your answer:
TR_Band: X.X
CC_Band: X.X
LR_Band: X.X
GRA_Band: X.X
Overall_Band: X.X
Explanation: [Brief justification for each criterion]
"""
    return prompt
