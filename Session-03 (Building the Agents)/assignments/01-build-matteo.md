# Assignment 01: Build Matteo's Full Coaching System

**Covers:** Build 01 (01-build-matteo.md)
**Time estimate:** 45-60 minutes
**Done when:** Matteo responds to a student message with a Socratic question AND the database shows the SCQ draft saved

---

## What You Are Building

Matteo currently returns coaching questions but has no memory of what the student
has confirmed and no ability to save progress. This assignment adds two platform
tools and a stage injection that make Matteo aware of where the student is in
their SCQ work.

By the end of this assignment, Matteo can:
- Read a student's prior SCQ progress at the start of a session
- Save a confirmed Situation, Complication, or Question to the database
- Receive the current SCQ state injected into his context every turn

---

## Before You Start

Confirm these are true:
- [ ] node server/src/index.js starts without errors on port 3001
- [ ] A curl POST to /api/agent1/chat with a valid JWT returns SSE tokens
- [ ] agent/tool_registry.py exists with at least one tool from Session 01

---

## Steps

### Step 1: Add the save_scq_draft tool

Open agent/tool_registry.py. Add the tool schema and implementation from
Build 01 (the SAVE_SCQ_DRAFT schema block and save_scq_draft function).

Register it in TOOL_DISPATCH:
```python
TOOL_DISPATCH = {
    ...existing tools...,
    "save_scq_draft": lambda args: save_scq_draft(**args),
}
```

Use the Claude Code prompt from Build 01 to generate this if you prefer.

### Step 2: Add the get_student_progress tool

Add GET_STUDENT_PROGRESS schema and get_student_progress function to tool_registry.py.
Register it in TOOL_DISPATCH:
```python
TOOL_DISPATCH = {
    ...existing tools...,
    "save_scq_draft": lambda args: save_scq_draft(**args),
    "get_student_progress": lambda args: get_student_progress(**args),
}
```

### Step 3: Add stage injection to routes/agent1.js

After loading the system prompt but before calling the agent, add:
```js
const progress = await db.getStudentProgress(req.user.id);
const scqContext = `\nCURRENT SESSION CONTEXT\nSituation: ${progress.situation ?? 'Not yet confirmed'}\nComplication: ${progress.complication ?? 'Not yet confirmed'}\nQuestion: ${progress.question ?? 'Not yet confirmed'}\nFocus on the first element that is not yet confirmed.`;
const systemPrompt = baseSystemPrompt + scqContext;
```

Add a db.getStudentProgress function in server/src/db.js that reads the
most recent Matteo session for a given user_id.

### Step 4: Update matteo_v1.txt

Open agent/prompts/matteo_v1.txt. Add two lines to the RULES section:
- Call get_student_progress at the start of the first turn of every session.
- Call save_scq_draft only when the student explicitly confirms an element is finalised.

### Step 5: Test it

Send this sequence of curl commands (replace YOUR_TOKEN with a valid student JWT):

```bash
# Turn 1: No SCQ confirmed yet
curl -X POST http://localhost:3001/api/agent1/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi, I am starting my case about a regional bank."}' \
  --no-buffer

# Confirm the SCQ state is empty in the DB
sqlite3 data/scq.db "SELECT messages FROM agent_sessions WHERE agent_id='matteo' ORDER BY created_at DESC LIMIT 1;"
```

---

## Done Checklist

- [ ] save_scq_draft and get_student_progress are both in TOOL_DISPATCH
- [ ] routes/agent1.js injects the CURRENT SESSION CONTEXT block into the system prompt
- [ ] A curl request to /api/agent1/chat returns SSE tokens without errors
- [ ] The system prompt token count is under 3,000 (run: python evaluation/measure_prompt.py)
- [ ] No hardcoded SQL strings (all queries use parameterised placeholders)

---

## Troubleshooting

**Tool not found error from the agent:**
The tool name in TOOLS list must match exactly what is in TOOL_DISPATCH.
Check: are you using "save_scq_draft" (underscore) consistently?

**Stage injection causes a 500:**
db.getStudentProgress is probably undefined. Confirm you exported it from db.js
and imported it in routes/agent1.js.

**Token count above 3,000:**
The tool descriptions are adding too many tokens. Shorten the description strings
in the SAVE_SCQ_DRAFT and GET_STUDENT_PROGRESS schemas to one sentence each.

---

**Next:** [02-build-juli.md](02-build-juli.md)

---

Copyright Janna AI Research Labs
