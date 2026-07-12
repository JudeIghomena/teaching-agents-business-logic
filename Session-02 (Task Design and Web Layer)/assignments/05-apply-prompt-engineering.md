# Assignment 05: Apply Prompt Engineering Principles

**What you are building:** Matteo's production-ready system prompt, saved as agent/prompts/matteo_v1.txt, using the five principles from the document
**Why it matters:** A placeholder prompt produces inconsistent results. A prompt engineered with explicit instructions, constraints, and format rules produces the same quality of coaching question regardless of what the student writes. This assignment is the difference between a demo and a deployable agent.
**Time estimate:** 45 minutes
**Reads with:** 05-prompt-engineering-principles.md

---

## What You Are Going To Do

You are going to rewrite Matteo's system prompt from scratch using the Task Definition you wrote in Assignment 04 and the five principles from the document. By the end, the prompt will be saved as a versioned file, under 3,000 tokens, and ready for evaluation in Assignment 08.

---

## What the Prompt Must Do

A prompt built on the five principles has these properties:

```
1. Instructions not descriptions    Tells the model what TO DO, not what it IS
2. Constraints not explanations     Short active rules instead of paragraphs
3. Specific format rules            Measurable constraints, not "be concise"
4. Chain-of-thought in the rules    Three reasoning steps before the response
5. Under the token budget           Total prompt <= 3,000 tokens for haiku
```

---

## Step 1: Create the Prompts Directory

```bash
mkdir -p agent/prompts
```

---

## Step 2: Draft the Five Sections

Open a text editor and write each section using the principles as a checklist.

**ROLE section** - Use the job statement from your Task Definition. Add the institution, the method, and two explicit constraints:

```
ROLE
You are Matteo, an Issue Analysis Coach for MBA students at [your institution].
Your students are working on consulting cases requiring a Situation-Complication-Question (SCQ) framework.

You use the Socratic method: you ask questions that build the student's own understanding.
You never state the answer. You never write any part of the SCQ framework for the student.
```

**SCOPE section** - List what you cover and what you do not. Use the Boundary field from your Task Definition:

```
SCOPE
You coach on: defining the Situation, isolating the Complication, formulating the Question.

You do not handle: recommendation structuring, Monroe's Sequence, 5 Cs evaluation, or anything outside Issue Analysis.

If the student asks about something outside your scope, acknowledge it briefly and redirect.
```

**RULES section** - Write constraints, not explanations. Start each rule with a verb:

```
RULES
- Before writing your response, identify: which SCQ element the student is on,
  what is missing or unclear, and what one question would expose that gap.
- Your visible response contains only that question. No preamble.
- Never evaluate the student's answer.
- Never write any part of the SCQ for the student.
- Never give more than one question per response.
- If the student asks for an example, ask what they have tried first.
- If the student shows distress, acknowledge it briefly and ask if they need support.
```

**FORMAT section** - Measurable constraints only:

```
FORMAT
- Maximum 120 words per response
- End every response with exactly one question ending in a question mark
- No bullet points, lists, or headers
- No phrases like "Great question" or "That is interesting"
```

**ESCALATION section**:

```
ESCALATION
Escalate if: the student describes a personal crisis, reports a platform
technical failure, or sends content that violates academic integrity.
When escalating: tell the student you are connecting them with support and end your reply.
```

---

## Step 3: Save as matteo_v1.txt

Save the complete prompt to `agent/prompts/matteo_v1.txt`.

---

## Step 4: Count the Tokens

Run the token counter from the document:

```bash
python -c "
import anthropic
c = anthropic.Anthropic()
r = c.messages.count_tokens(
    model='claude-haiku-4-5-20251001',
    system=open('agent/prompts/matteo_v1.txt').read(),
    messages=[{'role': 'user', 'content': 'test'}]
)
print(r.input_tokens, 'tokens')
"
```

If the count is above 3,000: cut description sentences from ROLE and SCOPE. Keep all constraints in RULES and FORMAT.

---

## Step 5: Update context.py to Load from File

Update `agent/context.py` to load the system prompt from the versioned file:

```python
import os
from pathlib import Path

PROMPT_VERSION = os.getenv("MATTEO_PROMPT_VERSION", "v1")
PROMPT_DIR = Path(__file__).parent / "prompts"

def build_matteo_system_prompt() -> str:
    prompt_file = PROMPT_DIR / f"matteo_{PROMPT_VERSION}.txt"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return prompt_file.read_text()
```

---

## Step 6: Read the Prompt Out Loud

Print the prompt file and read it. Ask yourself:

1. Does every sentence tell the model what to DO, or does it describe what it IS?
2. Can you count the constraints in RULES? There should be at least five.
3. Can the FORMAT constraints be checked programmatically? Word count, question count, presence of bullet points - these can all be measured.

If you read a sentence that starts with "You are helpful" or "You care about students", it is a description. Delete it and replace it with an instruction.

---

## You Are Done When

- [ ] agent/prompts/matteo_v1.txt exists with all five sections
- [ ] The prompt is under 3,000 tokens (confirmed by the counter)
- [ ] RULES contains at least one three-step reasoning block
- [ ] FORMAT specifies maximum word count and exact question count
- [ ] context.py loads the prompt from the file using MATTEO_PROMPT_VERSION
- [ ] No description sentences in the ROLE section ("You are helpful", "You care about...")

---

## If You Get Stuck

Token count is above 3,000: the ROLE or SCOPE section has too many description sentences. Cut every sentence that starts with "You are the kind of coach who..." or similar. Keep institution, method, and two constraints in ROLE. Keep two lines in SCOPE.

The agent is not using the new prompt: confirm context.py is called in runner.py and the result is passed to the messages API as the `system` parameter.

The agent ignores the FORMAT rules: constraints in RULES are more reliable than FORMAT alone. Add the word count and single-question requirement as a RULE as well as a FORMAT item.

---

## Next Assignment

[06-write-few-shot-examples.md](06-write-few-shot-examples.md)

---

Copyright Janna AI Research Labs
