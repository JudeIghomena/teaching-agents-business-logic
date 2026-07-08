# Build 08: Evaluation Methods

> Framework 10 (Observability) introduced structured logging and turn traces.
> Observability tells you what happened. Evaluation tells you whether it was good.
> You cannot improve what you have not measured.

**Applies:** Framework 10 (Observability)
**Builds:** Three evaluation methods for the SCQ platform: golden dataset, LLM-as-judge, and a scoring function for Matteo's coaching quality

---

## The Evaluation Problem

After Session One, you can observe your agent. You know how many tokens it used,
how long it took, and whether it called a tool. What you do not yet know is
whether the coaching question it asked was a good one.

Observability from Framework 10 answers: did the agent run correctly?
Evaluation answers: did the agent produce the right output?

Both are required. An agent that runs perfectly and consistently gives bad advice
is worse than one that occasionally crashes, because you can detect a crash but
you cannot detect bad advice without measurement.

---

## Three Evaluation Methods

You do not need all three at once. Build them in this order:

1. **Golden dataset** - the fastest to build and the most immediately useful
2. **Format validation** - catches structural failures automatically (built in document 07)
3. **LLM-as-judge** - the most powerful, used when human evaluation does not scale

---

## Method 1: Golden Dataset

A golden dataset is a collection of inputs with known-correct outputs.
For Matteo, it is a set of student messages where you have pre-decided what a
good coaching question looks like.

You need a minimum of 10 golden examples to catch regressions. 20 is better.

**What a golden record looks like:**

```json
{
  "id": "matteo-gold-01",
  "student_message": "The situation is that our client is a legacy bank that has lost 15% of retail customers to digital-only competitors over three years.",
  "must_contain": ["question"],
  "must_not_contain": ["you should", "the answer", "correct", "wrong"],
  "format_checks": {
    "max_words": 120,
    "ends_with_question_mark": true,
    "question_count": 1
  },
  "quality_note": "A strong response identifies that the Complication is not yet isolated: why is this loss a strategic problem for THIS client specifically?"
}
```

The `must_contain` and `must_not_contain` checks are automated. The `quality_note`
is for human review during the iteration process.

**Running the golden dataset:**

```python
# evaluation/run_golden.py

import json
from agent.runner import run_agent_loop

def run_golden_suite(golden_file: str) -> dict:
    with open(golden_file) as f:
        golden = json.load(f)

    results = []
    for record in golden:
        response = run_agent_loop(record["student_message"], history=[])

        checks = {
            "id": record["id"],
            "response": response,
            "must_contain": all(term in response.lower() for term in record["must_contain"]),
            "must_not_contain": all(term not in response.lower() for term in record["must_not_contain"]),
            "word_count": len(response.split()),
            "word_count_pass": len(response.split()) <= record["format_checks"]["max_words"],
            "ends_with_question": response.strip().endswith("?"),
            "question_count": response.count("?")
        }
        checks["pass"] = all([
            checks["must_contain"],
            checks["must_not_contain"],
            checks["word_count_pass"],
            checks["ends_with_question"],
            checks["question_count"] == record["format_checks"]["question_count"]
        ])
        results.append(checks)

    passed = sum(1 for r in results if r["pass"])
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "pass_rate": passed / len(results),
        "failures": [r for r in results if not r["pass"]]
    }
```

Run this before every prompt change:

```bash
python evaluation/run_golden.py
```

A pass rate below 90% means the prompt has a problem. Fix it before committing.

---

## Method 2: Format Validation (Automated)

Format validation from document 07 is the simplest form of automated evaluation.
Wire it into the route so every response is checked in development:

```js
// In routes/agent1.js (development only)

python.stdout.on('end', () => {
    const check = validateMatteoOutput(fullResponse);
    if (!check.pass) {
        console.warn('[eval] Format failure:', check);
    }
    appendTurn(sessionId, message, fullResponse);
    sendDone(res);
});
```

Log format failures to a file during development. If the same format rule fails
repeatedly, that rule is not being followed by the prompt and needs to be reworded.

---

## Method 3: LLM-as-Judge

LLM-as-judge uses a separate model call to evaluate the quality of your agent's
output. It does not replace human judgment but it scales where human review does not.

For Matteo, the judge evaluates whether the coaching question targets the right
SCQ element and follows the Socratic method:

```python
# evaluation/llm_judge.py

import anthropic

client = anthropic.Anthropic()

JUDGE_PROMPT = """
You are evaluating the quality of a Socratic coaching question for a business case analysis exercise.

The student sent this message:
{student_message}

The coach (Matteo) responded with:
{coach_response}

Evaluate on these three criteria. Score each 1-5:

1. SCQ Targeting: Does the question target a specific weakness in the student's SCQ thinking?
   1 = Generic question unrelated to SCQ
   5 = Precisely targets the weakest element of the student's SCQ

2. Socratic Method: Does the question develop the student's thinking rather than providing an answer?
   1 = Provides an answer or hints at the answer
   5 = Pure question that requires the student to think

3. Specificity: Is the question specific to this student's case, or could it be asked of any student?
   1 = Could be asked of anyone
   5 = Can only be asked of a student who wrote this specific message

Return only this JSON, no preamble:
{"scq_targeting": 1-5, "socratic_method": 1-5, "specificity": 1-5, "overall": 1-5}
"""

def judge_matteo_response(student_message: str, coach_response: str) -> dict:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": JUDGE_PROMPT.format(
                student_message=student_message,
                coach_response=coach_response
            )
        }]
    )
    import json
    return json.loads(response.content[0].text)
```

Use the judge on your golden dataset to get a quality baseline, then run it
again after each prompt change to measure whether quality improved or regressed.

---

## What to Measure for Each Agent

| Agent | Automated checks | LLM-judge dimensions |
|---|---|---|
| Matteo | Word count, question count, banned phrases | SCQ targeting, Socratic method, specificity |
| Juli | Word count, stage tag present and valid | Stage appropriateness, progression, clarity |
| Tedd | JSON valid, all 5 fields present, scores 1-5 | Observation specificity, score calibration |

Build the automated checks first. They run in milliseconds and catch most failures.
Add LLM-judge when you are iterating on coaching quality and need more than a
pass/fail signal.

---

## Recording Evaluation Baselines in CLAUDE.md

After your first evaluation run, record the baseline so future sessions can
detect regression:

```
## Evaluation Baselines

Recorded: [date]

Matteo golden dataset: 18/20 pass (90%)
  Failures: gold-07 (question count 2), gold-14 (word count 134)
  Action: Tighten FORMAT section to address both

Matteo LLM-judge baseline (20 turns):
  SCQ targeting avg: 3.8/5
  Socratic method avg: 4.2/5
  Specificity avg: 3.5/5
  Overall avg: 3.8/5

Pre-commit gate: golden dataset must pass at 90% or above before any prompt commit.
```

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code can both
build the evaluation tooling and help you write the golden dataset. The golden
records are the most important output of this document.

**Prompt to build the evaluation suite:**

```
Build the evaluation suite for Matteo in the evaluation/ folder.

1. evaluation/golden/matteo_golden.json - 10 golden records.
   Each record: { "id", "student_message", "must_contain", "must_not_contain",
   "format_checks": { "max_words", "ends_with_question_mark", "question_count" }, "quality_note" }
   
   The 10 student messages should cover:
   - 3 messages with a weak Situation (missing specificity)
   - 3 messages with a weak Complication (describing a symptom, not an implication)
   - 2 messages with a vague Question (not decision-focused)
   - 2 messages where the student has mixed SCQ elements together
   
   must_not_contain for all records: ["you should", "the answer is", "correct", "wrong", "great"]

2. evaluation/run_golden.py - runs all 10 records through run_agent_loop(),
   checks must_contain, must_not_contain, and format_checks, prints pass rate.

3. evaluation/llm_judge.py - judge_matteo_response(student_message, coach_response)
   calls claude-haiku-4-5 to score on scq_targeting, socratic_method, specificity (1-5 each).
   Returns JSON scores only.

Run the golden suite after building it: python evaluation/run_golden.py
```

**What Claude Code will do:**
Create the golden dataset with realistic SCQ student messages, build the runner
and LLM judge, then run the initial evaluation to give you a baseline score.

**Tips for this document:**
- The golden records are the most valuable thing in this document. Spend time
  reviewing them. Ask Claude Code: "For golden record 3, what is the specific
  SCQ weakness? Would a real student write this?" Adjust until they feel real.
- After the first run, ask Claude Code: "Which format rules are failing most?
  What change to the system prompt would fix the most common failure?"
- The LLM judge costs API tokens. Run it on 5 records, not all 10, to start.

---

## Starter Code

The evaluation suite is generated by Claude Code from the prompt above.
The golden records in particular must be specific to your SCQ case context
and cannot be pre-written.

```
starter-code/
├── CLAUDE.md           Claude Code reads the Task Definitions section to write
│                       realistic student messages for the golden records
├── package.json        Node dependencies
├── requirements.txt    Python dependencies (anthropic - needed for llm_judge.py)
└── .env.example        ANTHROPIC_API_KEY required to run the judge and golden suite
```

After Claude Code generates the golden records, review each student message.
Ask: would a real MBA student write this? If the messages feel artificial,
ask Claude Code to revise them with more realistic case detail.

---

## Assignment

[08-evaluate-your-agent.md](assignments/08-evaluate-your-agent.md)

---

Copyright Janna AI Research Labs
