# Assignment 08: Evaluate Your Agent

**What you are building:** A golden dataset with 10 records for Matteo, a runner that checks every record, and a baseline score you will use to detect regressions in Assignment 09
**Why it matters:** Without a baseline, you cannot know whether a prompt change improved the agent or made it worse. This assignment creates the measurement system that makes all future iteration meaningful.
**Time estimate:** 45-60 minutes
**Reads with:** 08-evaluation-methods.md

---

## What You Are Going To Do

You are going to write 10 golden records covering the main SCQ failure modes, build the runner that checks them, run the suite to get a baseline score, and record that score in CLAUDE.md.

---

## What the Evaluation Must Do

```
1. Cover realistic cases        Student messages a real MBA student would write
2. Check automatically          must_contain, must_not_contain, format checks
3. Produce a pass rate          X/10 - a number you can compare across prompt versions
4. Take under 60 seconds        So you can run it before every prompt commit
```

---

## Step 1: Create the Evaluation Directory

```bash
mkdir -p evaluation/golden
```

---

## Step 2: Write the Golden Dataset

Create `evaluation/golden/matteo_golden.json`. Write 10 records covering these failure modes:

- Records 1-3: student messages with a weak or vague Situation
- Records 4-6: student messages with a weak Complication (symptom not root cause)
- Records 7-8: student messages with a vague Question (not decision-focused)
- Records 9-10: student messages where SCQ elements are mixed together

Each record:

```json
{
  "id": "matteo-gold-01",
  "student_message": "Our client is a retail bank that has been losing customers.",
  "must_contain": ["?"],
  "must_not_contain": ["you should", "the answer", "correct", "wrong", "great", "good job"],
  "format_checks": {
    "max_words": 120,
    "ends_with_question_mark": true,
    "question_count": 1
  },
  "quality_note": "Strong response targets the Situation gap: losing customers is a fact, not a context. The question should press for what makes this client's situation distinct."
}
```

The quality_note is for human review. It is not used by the automated runner.

---

## Step 3: Write the Runner

Create `evaluation/run_golden.py`:

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent.runner import run_agent_loop

def run_golden_suite(golden_file: str) -> dict:
    with open(golden_file) as f:
        golden = json.load(f)

    results = []
    for record in golden:
        print(f"  Running {record['id']}...", end=" ")
        response = run_agent_loop(record["student_message"], history=[])

        word_count = len(response.split())
        question_count = response.count("?")

        checks = {
            "id": record["id"],
            "must_contain": all(term in response.lower() for term in record["must_contain"]),
            "must_not_contain": all(term not in response.lower() for term in record["must_not_contain"]),
            "word_count_pass": word_count <= record["format_checks"]["max_words"],
            "ends_with_question": response.strip().endswith("?"),
            "question_count_pass": question_count == record["format_checks"]["question_count"],
        }
        checks["pass"] = all(checks.values())
        results.append(checks)
        print("PASS" if checks["pass"] else "FAIL")

    passed = sum(1 for r in results if r["pass"])
    failures = [r for r in results if not r["pass"]]

    return {
        "total": len(results),
        "passed": passed,
        "pass_rate": f"{passed}/{len(results)} ({100*passed//len(results)}%)",
        "failures": failures
    }

if __name__ == "__main__":
    print("Running Matteo golden dataset...\n")
    result = run_golden_suite("evaluation/golden/matteo_golden.json")
    print(f"\nResult: {result['pass_rate']}")
    if result["failures"]:
        print(f"\nFailures:")
        for f in result["failures"]:
            print(f"  {f['id']}: {f}")
```

---

## Step 4: Run the Suite

```bash
python evaluation/run_golden.py
```

The first run will produce a baseline. Record it.

If the pass rate is below 70% on the first run, something in the FORMAT or RULES section is not being followed. Check which checks are failing most. If it is always `question_count_pass`, the FORMAT constraint needs reinforcing.

---

## Step 5: Record the Baseline in CLAUDE.md

Open CLAUDE.md and add an Evaluation Baselines section:

```
## Evaluation Baselines

Recorded: [today's date]

Matteo golden dataset: [X/10 pass] ([Y]%)
  Failures: [list the record IDs that failed]
  Most common failure type: [format / content / banned phrase]

Pre-commit gate: golden dataset must pass at 90% or above before any prompt commit.
```

If you scored below 90% on the first run, the next assignment will fix it.
Record the actual score, not a target.

---

## Step 6: Run the LLM Judge on 3 Records

Run the judge on three of the golden records to get a quality baseline:

```python
# In a Python shell or add to run_golden.py
from evaluation.llm_judge import judge_matteo_response
import json

golden = json.load(open("evaluation/golden/matteo_golden.json"))

for record in golden[:3]:
    from agent.runner import run_agent_loop
    response = run_agent_loop(record["student_message"], history=[])
    scores = judge_matteo_response(record["student_message"], response)
    print(record["id"], scores)
```

Record the average scores in CLAUDE.md alongside the golden dataset results.

---

## You Are Done When

- [ ] evaluation/golden/matteo_golden.json has 10 records covering 4 failure modes
- [ ] evaluation/run_golden.py runs without errors and prints a pass rate
- [ ] The baseline score is recorded in CLAUDE.md
- [ ] At least 3 LLM judge scores are recorded in CLAUDE.md
- [ ] The pre-commit gate is documented in CLAUDE.md (90% threshold)

---

## If You Get Stuck

run_golden.py cannot find the agent module: confirm the sys.path.insert line is at the top of the file and that the path points to the project root, not the evaluation directory.

All 10 records fail on must_not_contain: check if any of the forbidden terms appear in the system prompt. If Matteo's prompt contains "correct" or "good" as part of an example, the validator will catch those in the generated response if the model copies the example style.

The runner hangs on one record: the agent loop is waiting for input that is not coming. Add a timeout to the API call in runner.py or check if the model is returning an empty response for that specific student message.

---

## Next Assignment

[09-run-your-first-iteration.md](09-run-your-first-iteration.md)

---

Copyright Janna AI Research Labs
