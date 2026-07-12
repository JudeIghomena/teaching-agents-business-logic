# Assignment 05: Test the Full Student Journey

**Covers:** Build 05 (05-test-end-to-end.md)
**Time estimate:** 45-60 minutes
**Done when:** The end-to-end test script passes, the database shows all three agents' output persisted, and the professor route shows the student's quality score

---

## What You Are Building

This is not a new feature. It is the verification that everything built in
Session 03 works together. By running the full student journey and reading
the turn trace, you confirm that all three agents are correctly wired, that
data flows between them, and that the platform is ready for Session 04.

---

## Before You Start

Confirm these are true:
- [ ] All four previous assignments are complete
- [ ] node server/src/index.js starts without errors
- [ ] A test student user exists (email and password you can use in curl)
- [ ] A test professor user exists in the same cohort as the test student

---

## Steps

### Step 1: Write the test script

Create tests/test_end_to_end.py using the template from Build 05.
Confirm the script:
- Logs in as the test student and gets a token
- Sends one message to Matteo (agent 1)
- Sends one message to Juli (agent 2)
- Sends a full deliverable to Tedd (agent 3)
- Asserts that Matteo's response ends with a question mark
- Asserts that Tedd's response is valid JSON with all five Cs

Make sure requests is in your requirements:
```bash
pip install requests
```

### Step 2: Run the test

```bash
# Terminal 1: start the server
node server/src/index.js

# Terminal 2: run the test
python tests/test_end_to_end.py
```

Expected output:
```
Matteo response: ...
Tedd scores: {'clear': 3, 'concise': 2, 'compelling': 4, 'credible': 3, 'consistent': 3}
PASS: Full journey completed
```

### Step 3: Verify the database

Run these queries after the test passes:

```bash
# Matteo session: check messages column for saved SCQ elements
sqlite3 data/scq.db "SELECT messages FROM agent_sessions WHERE agent_id='matteo' ORDER BY created_at DESC LIMIT 1;"

# Tedd session: check quality_score is set and finalised = 1
sqlite3 data/scq.db "SELECT quality_score, finalised FROM agent_sessions WHERE agent_id='tedd' ORDER BY created_at DESC LIMIT 1;"
```

### Step 4: Verify the professor route

Get a professor token (log in as the professor user), then:

```bash
curl -H "Authorization: Bearer YOUR_PROFESSOR_TOKEN" \
     http://localhost:3001/api/professor/sessions | python3 -m json.tool
```

The response must include a session with:
- agent_id: "tedd"
- quality_score: a number between 1 and 5
- finalised: 1
- The student's email

### Step 5: Read the server log

Look at the terminal where node server/src/index.js is running.
After the test, you should see turn log entries like:
```
[turn] agent=matteo user=... tokens=... latency=...ms
[turn] agent=tedd   user=... tokens=... latency=...ms
```

If you do not see structured turn logs, ask Claude Code to add a console.log
in runner.py that prints token count and latency after every turn.

### Step 6: Run the second-submission test

Send the same Tedd message again:
```bash
curl -X POST http://localhost:3001/api/agent3/chat \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "The bank must launch a mobile-first account by Q1..."}' \
  --no-buffer
```

Expected: HTTP 409 with { "error": "This deliverable has already been evaluated." }

---

## Done Checklist

- [ ] tests/test_end_to_end.py exists and passes with PASS output
- [ ] Matteo response ends with a question mark
- [ ] Tedd response is valid JSON with all five Cs scored
- [ ] Database shows quality_score set and finalised = 1 for the Tedd session
- [ ] Professor route returns the student session with quality_score visible
- [ ] A second Tedd submission returns 409
- [ ] Server log shows structured turn entries for each agent call

---

## Troubleshooting

**Test script fails at login with 404:**
The test is hitting the wrong URL or the route is not registered.
Confirm POST /api/auth/login exists in server/src/routes/auth.js and is
registered in index.js.

**Matteo response has no question mark:**
The format validator is not blocking the response but Matteo's prompt is not
following the FORMAT rule. Open agent/prompts/matteo_v1.txt. Confirm the
FORMAT section says "End every response with exactly one question ending in a
question mark." If it says something weaker, tighten it.

**Tedd response is not valid JSON:**
The most common cause is markdown fences in the output.
Confirm parseTeddOutput strips them as a fallback.
Also add "Do not wrap in code fences" to Tedd's RULES section.

**Professor route returns an empty sessions array:**
The test student and professor must be in the same cohort.
Query: SELECT id, email, cohort_id FROM users;
If the cohort_ids differ, update the student's cohort_id to match the professor's.

---

## Session 03 Complete

If this assignment passes, the SCQ platform is running end to end with all
three agents, full data persistence, rate limiting, a professor dashboard,
and a verified student journey.

Session 04 will add the security hardening that makes the platform safe to
deploy beyond your local machine: IDOR testing, dependency audit, security
headers, and an HTTPS setup guide.

---

**You have completed Session 03.**

**Next session:** Session 04 - Security

---

Copyright Janna AI Research Labs
