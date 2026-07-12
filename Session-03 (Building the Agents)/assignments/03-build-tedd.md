# Assignment 03: Build Tedd's Rubric Evaluator

**Covers:** Build 03 (03-build-tedd.md)
**Time estimate:** 45-60 minutes
**Done when:** Tedd returns valid JSON with all five Cs scored AND the database shows quality_score set and finalised = 1

---

## What You Are Building

Tedd is the most format-sensitive agent on the platform. His output must be
parseable JSON every time. This assignment gives him a complete system prompt
with rubric-reading and evaluation-saving tools, and adds a double-submission
guard to the Express route.

By the end of this assignment, Tedd can:
- Load the 5 Cs rubric definitions from a config file
- Score a student deliverable across all five dimensions
- Save the evaluation and block a second submission of the same deliverable

---

## Before You Start

Confirm these are true:
- [ ] Assignment 02 is complete (Juli working with stage tags)
- [ ] parseTeddOutput from Session 02 is in routes/agent3.js
- [ ] The agent_sessions table has a quality_score column and a finalised column

---

## Steps

### Step 1: Create the rubric config file

Create agent/config/rubric.json using the template from Build 03.
The file must have all five dimensions: clear, concise, compelling, credible, consistent.
Each dimension needs: description, score_1 anchor, score_5 anchor.

Create the directory if it does not exist:
```bash
mkdir -p agent/config
```

### Step 2: Add get_rubric_config and save_evaluation tools

In agent/tool_registry.py, add both tool schemas and implementations from Build 03.
Register both in TOOL_DISPATCH:
```python
TOOL_DISPATCH = {
    ...existing tools...,
    "get_rubric_config": lambda args: get_rubric_config(**args),
    "save_evaluation": lambda args: save_evaluation(**args),
}
```

For save_evaluation, the average score calculation:
```python
score = sum(
    evaluation["evaluation"][c]["score"]
    for c in ["clear", "concise", "compelling", "credible", "consistent"]
) / 5.0
```

### Step 3: Write tedd_v1.txt

Save Tedd's system prompt as agent/prompts/tedd_v1.txt. Use the template from Build 03.

Key things to confirm:
- RULES says call get_rubric_config at the start of every turn
- RULES says call save_evaluation after producing the JSON
- FORMAT says raw JSON only, no markdown fences, no preamble
- The JSON schema example is included in FORMAT

Count tokens:
```bash
python -c "import anthropic; c=anthropic.Anthropic(); r=c.messages.count_tokens(model='claude-haiku-4-5-20251001', system=open('agent/prompts/tedd_v1.txt').read(), messages=[{'role':'user','content':'test'}]); print(r.input_tokens, 'tokens')"
```
Tedd's prompt may be slightly longer due to the schema example. Under 4,000 is acceptable.

### Step 4: Add the double-submission guard

In routes/agent3.js, before calling the agent:

```js
const existing = db.prepare(
    "SELECT finalised FROM agent_sessions WHERE user_id = ? AND agent_id = 'tedd' ORDER BY created_at DESC LIMIT 1"
).get(req.user.id);

if (existing?.finalised === 1) {
    return res.status(409).json({ error: "This deliverable has already been evaluated." });
}
```

### Step 5: Test it

Send a test deliverable:
```bash
curl -X POST http://localhost:3001/api/agent3/chat \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "The bank must launch a mobile-first account by Q1. Customer loss is 15% over three years. Three pillars: UX redesign, zero-fee accounts, referral program. The CEO must approve budget this quarter."}' \
  --no-buffer
```

Check the database after:
```bash
sqlite3 data/scq.db "SELECT quality_score, finalised FROM agent_sessions WHERE agent_id='tedd' ORDER BY created_at DESC LIMIT 1;"
```

quality_score should be set (a number between 1.0 and 5.0) and finalised should be 1.

Send the same request again. You should get 409.

---

## Done Checklist

- [ ] agent/config/rubric.json exists with all five dimensions
- [ ] get_rubric_config and save_evaluation are in TOOL_DISPATCH
- [ ] agent/prompts/tedd_v1.txt exists and is under 4,000 tokens
- [ ] A test deliverable returns valid JSON with all five Cs scored
- [ ] The database shows quality_score set and finalised = 1 after the test
- [ ] A second submission returns 409

---

## Troubleshooting

**Tedd returns JSON wrapped in markdown fences (```json...):**
This is the most common Tedd failure. Add this to the RULES section of tedd_v1.txt:
"Return raw JSON only. Do not wrap in code fences. Do not include triple backticks."
Then update your parseTeddOutput to strip fences as a fallback:
```js
const cleaned = text.trim().replace(/^```json\n?/,'').replace(/\n?```$/,'');
```

**save_evaluation fails with a SQL error:**
Confirm that the agent_sessions table has quality_score and finalised columns.
Run: sqlite3 data/scq.db ".schema agent_sessions"
If the columns are missing, add them:
ALTER TABLE agent_sessions ADD COLUMN quality_score REAL;
ALTER TABLE agent_sessions ADD COLUMN finalised INTEGER NOT NULL DEFAULT 0;

**Tedd makes three loop iterations instead of two:**
get_rubric_config and save_evaluation should each be called once.
If there are three iterations, Tedd may be calling get_rubric_config twice.
Add a log line in get_rubric_config to count calls.

---

**Next:** [04-wire-agents-to-platform.md](04-wire-agents-to-platform.md)

---

Copyright Janna AI Research Labs
