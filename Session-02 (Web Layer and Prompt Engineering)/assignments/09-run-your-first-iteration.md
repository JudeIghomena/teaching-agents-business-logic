# Assignment 09: Run Your First Iteration Cycle

**What you are building:** One complete prompt iteration cycle: identify the most common failure, make one change, measure the result, and document it in PROMPT_ITERATIONS.md
**Why it matters:** Running one cycle before Session 03 proves that your evaluation system works and that you can improve the agent in a controlled way. It also creates the habit of measuring before and after every change.
**Time estimate:** 45 minutes
**Reads with:** 09-iteration-workflow.md

---

## What You Are Going To Do

You are going to read the golden dataset failures from Assignment 08, identify the single most common failure type, make one targeted change to matteo_v2.txt (or v1 if you did not add examples), save it as v3, run the golden suite again, and document the result.

---

## What the Iteration Must Do

```
1. One change only        Do not change two things at once
2. Measure before         The baseline score from Assignment 08 is your starting point
3. Measure after          Run the same suite on the new version
4. Document the result    Write one entry in PROMPT_ITERATIONS.md before moving on
```

If you change more than one thing and the score improves, you do not know which change caused it. If the score drops, you do not know which change to revert.

---

## Step 1: Identify the Most Common Failure

Look at the failure list from Assignment 08. Group the failures by which check failed:

- Format failures: word_count_pass, ends_with_question, question_count_pass
- Content failures: must_not_contain (evaluation phrases, banned words)

Which type appeared most often? That is the failure you are targeting this cycle.

Common patterns:
- If question_count_pass fails repeatedly: the FORMAT section does not make the single-question requirement specific enough
- If must_not_contain fails repeatedly: the RULES section needs an explicit banned phrase list
- If word_count_pass fails: the FORMAT maximum word count needs a sentence explaining what to trim if over the limit

---

## Step 2: State Your Hypothesis

Before changing anything, write your hypothesis in plain text:

```
Failure type: [which check is failing most]
Hypothesis: The FORMAT section says [current wording]. This is not specific enough
because [reason]. If I change it to [new wording], the model will [expected behaviour].
```

Write this in a text file or in a comment at the top of the iteration log. Do not skip this step. If you cannot state a hypothesis, you are guessing.

---

## Step 3: Make One Change

Copy your current active prompt to a new version:

```bash
cp agent/prompts/matteo_v2.txt agent/prompts/matteo_v3.txt
```

Open matteo_v3.txt and make exactly one change. Examples:

If question_count is failing:
```
BEFORE: End every response with exactly one question.
AFTER:  End every response with exactly one question. If you find yourself writing
        a second question, remove it before sending.
```

If must_not_contain is failing (evaluation phrases):
```
BEFORE: No phrases like "Great question".
AFTER:  Never open with an evaluation of the student's message. Banned opening words:
        Good, Great, Interesting, Exactly, Correct, Right, Well done, That's.
```

One change. Save the file.

---

## Step 4: Run the Suite on v3

```bash
MATTEO_PROMPT_VERSION=v3 python evaluation/run_golden.py
```

Compare the result to your baseline from Assignment 08.

Three possible outcomes:
- Pass rate improved: keep the change. This is your new baseline.
- Pass rate is the same: the change did not address the root cause. Revert and try a different approach.
- Pass rate dropped: revert immediately. Something in the change made things worse.

---

## Step 5: Document in PROMPT_ITERATIONS.md

Create `agent/PROMPT_ITERATIONS.md` if it does not exist. Add one entry:

```
# Prompt Iteration Log

## Matteo v3 ([today's date])

Baseline (v2): golden pass rate [X/10], LLM-judge avg [Y/5]

Failure type: [which check was failing most]
Hypothesis: [your hypothesis from Step 2]

Change: [describe exactly what you changed - one sentence]

Result: golden pass rate [X/10]
  [name of failure type] failures: [before] to [after]
  Any regression in other checks: [yes/no and detail]

Decision: [Keep / Revert] - [one sentence explaining why]
```

If you kept the change, update CLAUDE.md to record the new baseline score.

---

## Step 6: Set the Active Version

If you kept the change, copy v3 to current:

```bash
cp agent/prompts/matteo_v3.txt agent/prompts/matteo_current.txt
```

Update your .env to point to current:

```
MATTEO_PROMPT_VERSION=current
```

---

## You Are Done When

- [ ] agent/prompts/matteo_v3.txt exists with exactly one change from v2
- [ ] The golden suite ran on v3 and you have a new score
- [ ] PROMPT_ITERATIONS.md has one complete entry with baseline, hypothesis, change, result, and decision
- [ ] If you kept the change: CLAUDE.md Evaluation Baselines section shows the updated score
- [ ] If you reverted: PROMPT_ITERATIONS.md explains why and matteo_current.txt still points to v2

---

## If You Get Stuck

The pass rate did not change at all: the change may not have reached the model. Confirm MATTEO_PROMPT_VERSION=v3 is being read in context.py and that the right file is being loaded. Print the first 50 characters of the loaded prompt to verify.

Both v2 and v3 fail on the same records: the golden records for that failure mode may be too easy to fail regardless of the prompt. Open one of the failing records and look at what the agent actually returned. Is the failure in the response or in the must_contain/must_not_contain check?

The hypothesis turned out to be wrong: that is fine. Document it honestly in PROMPT_ITERATIONS.md. A documented wrong hypothesis is more valuable than an undocumented one: it tells the next session not to try the same approach.

---

## Session 02 Complete

If this assignment is done, you have:

- A running authenticated web API with three agent routes
- A SQLite database storing every conversation turn
- JWT authentication with role guards
- Precise task definitions for all three agents in CLAUDE.md
- A production-ready system prompt for Matteo
- Two few-shot examples that demonstrate good coaching questions
- Format validators for all three agents
- A golden dataset with a documented baseline score
- One complete iteration cycle logged in PROMPT_ITERATIONS.md

Session 03 will implement the full coaching logic for Juli and Tedd and run the full student journey end to end.

---

**You have completed Session 02.**

**Next session:** Session 03 - Building Matteo, Juli, and Tedd in Full

---

Copyright Janna AI Research Labs
