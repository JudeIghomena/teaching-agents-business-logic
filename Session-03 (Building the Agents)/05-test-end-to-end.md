# Build 05: Testing End to End

> Framework 08 (The Agent Loop) defines how a single turn works.
> Framework 10 (Observability) gives you the tools to see what happened.
> This document runs the full student journey across all three agents
> and reads the turn trace to verify every layer worked as expected.

**Applies:** Framework 08 (The Agent Loop) + Framework 10 (Observability)
**Builds:** A full end-to-end test of the SCQ platform with turn-level observability and a basic load check

---

## The Full Student Journey

A student using the SCQ platform moves through three agents in sequence.
Each agent handoff depends on the previous agent's output being saved correctly.

```
Student logs in         POST /api/auth/login
                        Response: { token: "eyJ..." }

Turn 1 (Matteo)         POST /api/agent1/chat
                        Body: { message: "My situation is..." }
                        SSE tokens stream back as Matteo coaches

... multiple Matteo turns ...

Situation, Complication, and Question all confirmed.
save_scq_draft called three times. All three saved to agent_sessions.

Turn 1 (Juli)           POST /api/agent2/chat
                        Body: { message: "For my Attention stage..." }
                        System prompt includes STUDENT'S CONFIRMED SCQ block
                        SSE tokens stream back as Juli coaches
                        Response ends with [STAGE: Attention]

... multiple Juli turns across five stages ...

Stage advances to Action. Student completes the full recommendation structure.

Turn 1 (Tedd)           POST /api/agent3/chat
                        Body: { message: "<full recommendation text>" }
                        Tedd calls get_rubric_config, scores all five Cs
                        save_evaluation writes quality_score to DB
                        Response: raw JSON with five scored dimensions

Professor reads          GET /api/professor/sessions
                        Response: all sessions for the cohort with quality scores
```

At every step, the turn is logged to the database and the TurnTrace records
the latency, token count, and any tool calls made during the turn.

---

## Tracing a Single Turn: The Agent Loop in Action

From Framework 08, every agent turn follows the same loop:

```
1. Receive message and history
2. Add system prompt
3. Call Anthropic API
4. If response contains tool_use: execute the tool, append result, loop back to 3
5. If response is end_turn: extract text, return it
```

The TurnTrace from Framework 10 records each iteration of this loop.
After a Matteo turn that called save_scq_draft, the trace looks like:

```
TurnTrace {
  agent: "matteo",
  user_id: "student-001",
  turn_index: 7,
  iterations: 2,
  tool_calls: [
    { name: "save_scq_draft", args: { session_id: 12, element: "situation", content: "..." }, result: { saved: True } }
  ],
  input_tokens: 2847,
  output_tokens: 94,
  latency_ms: 1234,
  timestamp: "2026-07-12T10:30:00Z"
}
```

Two iterations means the loop ran twice: once to produce the tool call,
and once after the tool result to produce the final text response.

---

## Running the Full Journey Test

Write a test script that drives the full student journey without a browser:

```python
# tests/test_end_to_end.py

import requests
import json

BASE = "http://localhost:3001"
STUDENT_EMAIL = "test-student@hult.edu"
STUDENT_PASS  = "TestPass123!"

def test_full_journey():
    # Step 1: Login
    login = requests.post(f"{BASE}/api/auth/login", json={
        "email": STUDENT_EMAIL,
        "password": STUDENT_PASS
    })
    assert login.status_code == 200
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: First Matteo turn
    def stream_agent(agent_num, message):
        resp = requests.post(
            f"{BASE}/api/agent{agent_num}/chat",
            json={"message": message},
            headers=headers,
            stream=True
        )
        full_text = ""
        for line in resp.iter_lines():
            if line.startswith(b"data: "):
                data = json.loads(line[6:])
                if data.get("type") == "token":
                    full_text += data["text"]
                elif data.get("type") == "done":
                    break
        return full_text

    matteo_response = stream_agent(1, "My situation is that the client is a regional bank.")
    assert "?" in matteo_response, "Matteo must end with a question"
    print(f"Matteo response: {matteo_response[:120]}")

    # Step 3: First Tedd turn (full deliverable)
    deliverable = """
    Our client must launch a mobile-only digital account by Q1 next year.
    This is the most important step to stop losing retail customers to fintech competitors.
    Our analysis shows 15% of the customer base left in three years.
    The solution has three pillars: mobile-first UX redesign, zero-fee accounts for under-25s,
    and a referral program. If implemented, the bank retains its existing customers and
    attracts 20,000 new accounts in year one. The CEO must approve the budget this quarter.
    """
    tedd_response = stream_agent(3, deliverable)
    evaluation = json.loads(tedd_response)
    assert "evaluation" in evaluation
    assert all(c in evaluation["evaluation"] for c in ["clear","concise","compelling","credible","consistent"])
    print(f"Tedd scores: { {k: v['score'] for k, v in evaluation['evaluation'].items()} }")

if __name__ == "__main__":
    test_full_journey()
    print("PASS: Full journey completed")
```

Run it:

```bash
node server/src/index.js &
python tests/test_end_to_end.py
```

---

## What to Check After the Test

Run through this checklist after the journey script passes:

**Database checks:**
```sql
-- Confirm SCQ elements saved
SELECT messages FROM agent_sessions
WHERE agent_id = 'matteo' AND user_id = 'student-001';

-- Confirm Juli stage advanced
SELECT messages FROM agent_sessions
WHERE agent_id = 'juli' AND user_id = 'student-001';

-- Confirm Tedd evaluation saved and finalised
SELECT quality_score, finalised FROM agent_sessions
WHERE agent_id = 'tedd' AND user_id = 'student-001';
```

**Turn log checks:**
Read the most recent entries in your turn log file. Verify:
- Matteo: latency under 3,000ms, token count under 3,000 for system prompt
- Juli: stage tag appears at the end of every response
- Tedd: exactly two loop iterations (one for tool call, one for JSON output)

**Professor route check:**
```bash
curl -H "Authorization: Bearer <professor_token>" \
     http://localhost:3001/api/professor/sessions
```
The response should include the student's Tedd session with quality_score set.

---

## Basic Load Check

Before considering the platform ready for a cohort, run a light concurrent
load test. This is not a formal performance test. It is a sanity check.

```bash
# Install artillery (or use the ab tool if available)
npm install -g artillery

# Create a simple load test config
cat > load-test.yml << 'EOF'
config:
  target: "http://localhost:3001"
  phases:
    - duration: 30
      arrivalRate: 5
scenarios:
  - flow:
    - post:
        url: "/api/auth/login"
        json:
          email: "test-student@hult.edu"
          password: "TestPass123!"
        capture:
          - json: "$.token"
            as: "token"
    - post:
        url: "/api/agent1/chat"
        headers:
          Authorization: "Bearer {{ token }}"
        json:
          message: "The situation is that our client is a retail bank."
EOF

npx artillery run load-test.yml
```

What to look for:
- Response times for Matteo should stay under 5,000ms at 5 concurrent users
- No 500 errors in the server log
- Rate limiter kicks in if a single user exceeds 30 requests per minute
- The database is not locked (better-sqlite3 handles concurrent reads well;
  watch for SQLITE_BUSY if writes collide)

---

## Observability: Reading the Turn Log

After running the load test, open the server's log output and look for the
structured turn log entries. Each entry should show:

```
[turn] agent=matteo user=student-001 tokens=2847 latency=1234ms tools=1
[turn] agent=juli   user=student-001 tokens=3102 latency=1456ms tools=0
[turn] agent=tedd   user=student-001 tokens=4210 latency=2103ms tools=2
```

Tedd always makes two tool calls (get_rubric_config and save_evaluation),
so its latency is naturally higher than the other two agents. This is expected.

If any agent shows latency above 8,000ms consistently, the system prompt
may be too long or the history window is hitting the trim threshold every turn.
Add a log line that prints the token count before the API call to investigate.

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code can
write the end-to-end test script, run the full journey, and read the database
to verify that every step persisted correctly.

**Prompt to run the end-to-end test:**

```
Run the end-to-end platform test and verify all three agents are working.

Step 1: Write tests/test_end_to_end.py if it does not exist.
  The test must:
  - Log in as a test student (create the user if it does not exist)
  - Send one message to Matteo and verify the response ends with a question
  - Send a full recommendation to Tedd and verify the JSON response has
    all five Cs dimensions with scores 1-5
  - Print the pass/fail result clearly

Step 2: Run the test:
  python tests/test_end_to_end.py

Step 3: If the test fails, show me the error and diagnose the root cause.
  Check these in order:
  - Is the Express server running? Can you reach /api/auth/login?
  - Does the JWT work? Are we getting 401?
  - Is the Python agent reachable from the Express route?
  - Is the Tedd response valid JSON?

Step 4: After the test passes, query the database and show me:
  SELECT agent_id, quality_score, finalised FROM agent_sessions
  ORDER BY created_at DESC LIMIT 5;

Step 5: Show me the last 10 lines of the server log. Are there any errors?
```

**What Claude Code will do:**
Write the test script, run it, diagnose any failures, and confirm that the
database shows the expected state after the journey completes.

**Tips for this document:**
- If the test passes but the database shows no quality_score for Tedd,
  the save_evaluation tool call is not completing. Ask Claude Code:
  "Add a log line in save_evaluation that prints the user_id and session_id
  being written. What does it print during the test run?"
- If Matteo stops responding mid-stream, the SSE connection may be timing
  out. Ask Claude Code: "Does the Express server have a request timeout configured?
  What is the default Node.js socket timeout?"
- Run the test twice with the same student user. The second Tedd request
  should get 409 (finalised). If it does not, the double-submission guard
  from document 03 is not working.

---

## Starter Code

The test script is generated by Claude Code using the prompt above.
The specific student messages in the test should be realistic SCQ inputs,
not placeholder text.

```
starter-code/
|-- CLAUDE.md           How to Start the Platform section is updated with
|                       the test command and the database verification queries
|-- .env.example        TEST_STUDENT_EMAIL and TEST_STUDENT_PASS added
|-- package.json        Node dependencies (artillery optional, not listed here)
`-- requirements.txt    Python dependencies (requests added for the test script)
```

---

## What You Have Built

By completing this document, all three agents are running on the platform.
The student journey works end to end. Every turn is stored. The professor
can see cohort-level quality scores.

This is the SCQ platform at the end of Session 03:
- Three authenticated agent routes with rate limiting
- Stage progression for Matteo (SCQ elements) and Juli (Monroe's stages)
- Persistent evaluation storage for Tedd with duplicate prevention
- A professor dashboard showing cohort performance
- Turn-level observability with latency and token tracking
- An end-to-end test that verifies the full student journey

Session 04 adds the security hardening that makes this platform safe to
deploy beyond a local environment.

---

## Assignment

[05-test-end-to-end.md](assignments/05-test-end-to-end.md)

---

Copyright Janna AI Research Labs
