# Build 09: Iteration Workflow

> Framework 10 (Observability) gives you the data. Framework 04 (Context Window Budget)
> reminds you that every change to the prompt has a cost. This document gives you
> the process for making changes that improve the agent without breaking what works.

**Applies:** Framework 10 (Observability) + Framework 04 (Context Window Budget)
**Builds:** A repeatable prompt improvement cycle for the SCQ platform with a versioned prompt store and documented iteration log

---

## The Iteration Trap

The most common mistake after first evaluation results come back is making multiple
changes at once and then re-running the evaluation. If the score improves, you
do not know which change caused it. If the score drops, you do not know which
change caused that either.

Effective iteration follows one rule: **change one thing, measure, then decide.**

This applies to:
- Adding or removing an instruction
- Rewording a rule
- Adding or removing an example
- Changing the FORMAT constraints
- Changing the model

One change per iteration cycle. Measure before and after. Document the result.
Then decide whether to keep the change.

---

## Version-Controlled Prompts

Prompts are code. They deserve version control.

Do not store your system prompt as a hardcoded string inside a Python function.
Store it as a text file with a version number. Load it at runtime.

```
agent/
├── prompts/
│   ├── matteo_v1.txt       First version
│   ├── matteo_v2.txt       After first iteration
│   └── matteo_current.txt  Symlink to the active version (or set by env var)
```

Loading by version:

```python
# agent/context.py

import os
from pathlib import Path

PROMPT_VERSION = os.getenv("MATTEO_PROMPT_VERSION", "current")
PROMPT_DIR = Path(__file__).parent / "prompts"

def build_matteo_system_prompt() -> str:
    prompt_file = PROMPT_DIR / f"matteo_{PROMPT_VERSION}.txt"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return prompt_file.read_text()
```

To test a new version without deploying it:

```bash
MATTEO_PROMPT_VERSION=v2 python evaluation/run_golden.py
```

You compare v1 and v2 scores before changing `MATTEO_PROMPT_VERSION=current` in `.env`.

---

## The Iteration Cycle

Follow this cycle for every prompt change:

```
1. Run golden dataset      Establish current baseline score
2. Identify one failure    Pick the most common failure mode from the results
3. Hypothesise             What single change would fix it?
4. Make one change         Edit the prompt file. One change only.
5. Run golden dataset      Measure the new score
6. Compare                 Did the target failure go down? Did any other score drop?
7. Decide: keep or revert  If overall score improved or held, keep it. If it dropped, revert.
8. Document                Write one entry in the iteration log before moving on
```

Do not skip step 8. The iteration log is how a future Claude Code session
understands why the prompt is written the way it is. A prompt rule that looks
arbitrary often has a specific reason that is only visible in the log.

---

## The Iteration Log

Keep a `PROMPT_ITERATIONS.md` file in the `agent/` directory:

```markdown
# Prompt Iteration Log

## Matteo v3 (2026-07-10)

Baseline (v2): golden pass rate 88%, LLM-judge avg 3.6/5

Hypothesis: The FORMAT section says "maximum 120 words" but does not say
what to cut if 120 words is not enough. The model is sometimes trimming
the question rather than the preamble.

Change: Added to FORMAT: "If you must cut words, cut from the opening sentences.
Never shorten or simplify the closing question."

Result: golden pass rate 93%, LLM-judge avg 3.9/5
Word count failures dropped from 3 to 0. No regression in other dimensions.

Decision: Keep. Promoted to current.

---

## Matteo v2 (2026-07-09)

Baseline (v1): golden pass rate 80%, LLM-judge avg 3.2/5

Hypothesis: The RULES section does not explicitly ban evaluation phrases.
The model is occasionally starting with "That's a thoughtful observation."

Change: Added to RULES: "Never open with an evaluation of the student's message.
No 'Good', 'Interesting', 'Correct', 'That makes sense', or any similar phrase."

Result: golden pass rate 88%, LLM-judge avg 3.6/5
Evaluation phrase failures dropped from 4 to 1. Small regression in
SCQ targeting (4.1 to 3.8) - the new rule may be constraining the opening.

Decision: Keep. The banned phrase failure was more damaging than the targeting drop.
Monitor targeting in next iteration.
```

---

## What Counts as a Regression

Not every metric drop is a regression worth reverting for. Use this rule:

- If the overall golden pass rate drops more than 5 percentage points: revert
- If the LLM-judge overall score drops more than 0.3 points: revert
- If a format dimension fails that was passing before: investigate before keeping

A small drop in one dimension while another improves is usually acceptable.
Revert only when the change clearly made things worse overall.

---

## Budget Awareness During Iteration

Every prompt change has a context cost. Track it alongside quality:

```python
def measure_prompt(prompt_version: str) -> dict:
    prompt = load_prompt("matteo", prompt_version)
    response = client.messages.count_tokens(
        model="claude-haiku-4-5-20251001",
        system=prompt,
        messages=[{"role": "user", "content": "test"}]
    )
    return {
        "version": prompt_version,
        "tokens": response.input_tokens,
        "budget_impact": f"{response.input_tokens / 20000 * 100:.1f}% of 20k context"
    }
```

If two prompt versions produce the same quality score, choose the shorter one.
Every token saved in the system prompt is a token available for conversation history.

Record token counts in the iteration log alongside quality scores.

---

## Pre-Commit Gate

Before committing any prompt change, all three checks must pass:

```bash
# 1. Golden dataset
python evaluation/run_golden.py
# Must pass at 90% or above

# 2. Token count
python evaluation/measure_prompt.py matteo current
# Must not exceed 3,000 tokens

# 3. Format validation on 5 test inputs
python evaluation/format_check.py matteo current
# Must pass all 5
```

Add these to your CLAUDE.md:

```
## Pre-Commit Gate (Prompt Changes)

Before committing any change to agent/prompts/:
1. python evaluation/run_golden.py     must be >= 90% pass rate
2. python evaluation/measure_prompt.py must be <= 3,000 tokens
3. python evaluation/format_check.py   must pass all 5 test inputs
4. Append one entry to agent/PROMPT_ITERATIONS.md
```

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code can run
your golden suite, interpret the failure patterns, and suggest a targeted prompt
change. This is the document where you use Claude Code most interactively.

**Prompt to run your first iteration cycle:**

```
Run the evaluation golden suite and help me do one iteration cycle.

Step 1: Run the golden suite
  python evaluation/run_golden.py

Step 2: Show me which records failed and what the failure pattern is.
  Group failures by type: format failures vs content failures.

Step 3: Identify the single most common failure type and hypothesise
  one change to agent/prompts/matteo_current.txt that would fix it.
  Show me exactly what you would change and why.

Step 4: Make that one change and save as agent/prompts/matteo_v2.txt.
  Do not make any other changes.

Step 5: Run the golden suite again pointing at v2:
  MATTEO_PROMPT_VERSION=v2 python evaluation/run_golden.py

Step 6: Compare the scores. Did the target failure go down?
  Did any other check regress?

Step 7: Write one entry in agent/PROMPT_ITERATIONS.md documenting:
  - The baseline score
  - The hypothesis
  - The change made
  - The new score
  - The decision (keep or revert) and why
```

**What Claude Code will do:**
Run the full iteration cycle, interpret results, make one targeted change,
re-measure, and write the iteration log entry. You review the change before
it updates the prompt file.

**Tips for this document:**
- Do not let Claude Code make more than one change at a time, even if it spots
  multiple issues. Tell it: "One change only this cycle. We will do the rest next."
- After the cycle completes, check the token count: the change should not have
  added more than 100 tokens. Ask Claude Code to confirm.
- If the score is exactly the same after the change, ask Claude Code: "What does
  this tell us about the failure? Is it a prompt issue or a model behaviour issue?"
  Sometimes the answer is to add a few-shot example, not another rule.

---

## Starter Code

Full iteration tooling in `starter-code/09-iteration/`:

```
09-iteration/
├── agent/
│   ├── prompts/
│   │   ├── matteo_v1.txt          First version of Matteo's prompt
│   │   └── matteo_current.txt     Copy of v1 (update as you iterate)
│   └── PROMPT_ITERATIONS.md       Blank log ready to fill in
├── evaluation/
│   ├── run_golden.py              Golden dataset runner from document 08
│   ├── measure_prompt.py          Token counter for a given version
│   └── format_check.py            Format validator runner
└── context.py                     Version-aware prompt loader
```

---

## Assignment

[09-run-your-first-iteration.md](assignments/09-run-your-first-iteration.md)

---

Copyright Janna AI Research Labs
