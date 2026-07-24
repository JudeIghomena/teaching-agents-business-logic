# CLAUDE.md - SCQ Platform (End of Session 05)

This file describes the full state of the SCQ Business Case Logic platform
after Session 05 is complete. Any coding agent (Claude Code, Cursor, Codex)
starting work on this project should read this file first.

---

## Role

You are a coding agent working on the SCQ Business Case Logic platform,
an AI coaching application for MBA students at Hult International Business School.

The platform hosts three AI coaching agents: Matteo (Issue Analysis),
Juli (Monroe's Motivated Sequence), and Tedd (5 Cs peer review).
After Session 05, the platform has a full orchestration layer: students send
all messages to a single endpoint (POST /api/chat) and the orchestrator
routes them to the correct agent based on their current stage. Matteo's
confirmed SCQ is injected into Juli's context automatically. The platform
handles agent failures with retry logic, clean error responses, and a HITL
flag for low-scoring Tedd evaluations. Session 06 will add production
deployment.

---

## Layer Ownership

| Layer | Owner | Do not cross this boundary |
|---|---|---|
| HTTP routing, auth, SSE, rate limiting, validation | Express (server/src/) | Agents do not import Express |
| Database reads and writes | Express routes + db.js | Agents do not import better-sqlite3 |
| JWT verification | authMiddleware | Agents receive user_id from req.user, never from req.body |
| Stage routing | stageManager.js | Only the orchestrator calls stageManager |
| Agent invocation | agentCaller.js | Only orchestrator.js imports agentCaller |
| Agent reasoning and response | Python agents (agent/) | Express does not write prompt logic |
| Prompt versioning | agent/prompts/*.txt | Never hardcode system prompts in .py files |
| Rubric configuration | agent/config/rubric.json | Tedd reads this file via get_rubric_config tool |
| Security controls | middleware/ | All security middleware lives here, not in route handlers |

---

## Project Structure

```
scq-platform/
|
|-- server/
|   |-- src/
|   |   |-- index.js              Express entry point: rate limiting, routes, error handler
|   |   |-- app.js                buildApp() export for testing (no app.listen call)
|   |   |-- db.js                 better-sqlite3 singleton + setTestDb for test injection
|   |   |-- db-init.js            Schema creation (run once with npm run db:init)
|   |   |-- routes/
|   |   |   |-- auth.js           POST /api/auth/login (bcrypt + JWT sign)
|   |   |   |-- orchestrator.js   POST /api/chat (student-facing, routes to agent)
|   |   |   |-- agent1.js         POST /api/agent1/chat (Matteo, kept for test suite)
|   |   |   |-- agent2.js         POST /api/agent2/chat (Juli, kept for test suite)
|   |   |   |-- agent3.js         POST /api/agent3/chat (Tedd, kept for test suite)
|   |   |   `-- professor.js      GET /api/professor/sessions (needs_review field added)
|   |   |-- lib/
|   |   |   |-- stageManager.js   getCurrentStage, isStageComplete, getMatteoHandoff
|   |   |   `-- agentCaller.js    callMatteo, callJuli, callTedd, streamAgent
|   |   `-- middleware/
|   |       |-- auth.js           JWT verify with algorithms: ['HS256']
|   |       |-- roleGuard.js      requireRole('student'|'professor'|'admin')
|   |       |-- rateLimiter.js    authLimiter (IP) + agentLimiter (user ID)
|   |       `-- validator.js      validateAgentMessage + validateTeddMessage
|   |-- tests/
|   |   |-- security.test.js      Auth, role guard, IDOR test suite (Session 04)
|   |   |-- orchestrator.test.js  Stage routing and context tests (Session 05)
|   |   `-- helpers/
|   |       `-- testDb.js         initTestDb + teardownTestDb + getTestDb
|   |-- .env                      All secrets and config (gitignored)
|   |-- .env.example              Template with placeholder values (committed)
|   `-- package.json              Version 0.5.0
|
|-- agent/
|   |-- runner.py                 run_agent_loop with call_with_retry (529 retry logic)
|   |-- context.py                build_system_prompt(agent_id, version) -> str
|   |-- model_config.py           MODEL per agent, MAX_TOKENS, MAX_HISTORY_TURNS
|   |-- tool_registry.py          TOOLS list, TOOL_DISPATCH dict, all implementations
|   |                             save_evaluation now sets needs_review flag
|   |-- infrastructure.py         get_client(), TurnTrace, get_logger()
|   |-- session_store.py          SessionStore singleton (Tier 2 memory)
|   |-- prompts/
|   |   |-- matteo_v1.txt
|   |   |-- juli_v1.txt
|   |   `-- tedd_v1.txt
|   |-- config/
|   |   `-- rubric.json
|   `-- PROMPT_ITERATIONS.md
|
|-- evaluation/
|   |-- golden/
|   |   `-- matteo_golden.json
|   |-- run_golden.py
|   |-- llm_judge.py
|   `-- measure_prompt.py
|
|-- tests/
|   `-- test_end_to_end.py
|
|-- data/
|   `-- scq.db                    SQLite database (gitignored)
|
|-- SECURITY.md
|-- .env                          ANTHROPIC_API_KEY (gitignored)
|-- .env.example
|-- .gitignore
`-- requirements.txt
```

---

## Model Routing

| Agent | Model | Reason |
|---|---|---|
| Matteo | claude-haiku-4-5-20251001 | Conversational coaching, speed matters for streaming |
| Juli | claude-haiku-4-5-20251001 | Conversational coaching, speed matters for streaming |
| Tedd | claude-haiku-4-5-20251001 | Switch to claude-sonnet-5 if JSON error rate exceeds 5% |

Never hardcode model names in routes. Read from model_config.py.

---

## Database Schema

```sql
CREATE TABLE agent_sessions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       TEXT    NOT NULL,
    cohort_id     TEXT    NOT NULL,
    agent_id      TEXT    NOT NULL,
    messages      TEXT    NOT NULL DEFAULT '[]',
    quality_score REAL,
    finalised     INTEGER NOT NULL DEFAULT 0,
    needs_review  INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE users (
    id            TEXT    PRIMARY KEY,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'student',
    cohort_id     TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

The `needs_review` column was added in Session 05. Run the migration on
existing databases:

```sql
ALTER TABLE agent_sessions ADD COLUMN needs_review INTEGER NOT NULL DEFAULT 0;
```

---

## Context Window Budget

| Agent | Context limit | System prompt | Injected context | History | Buffer |
|---|---|---|---|---|---|
| Matteo | 20,000 tokens | max 3,000 | ~80 (SCQ state) | max 13,920 | 3,000 |
| Juli | 20,000 tokens | max 3,000 | ~350 (stage + full SCQ) | max 13,650 | 3,000 |
| Tedd | 20,000 tokens | max 4,000 | none | min (one shot) | 16,000 |

Juli's injected context increased from ~230 (Session 03) to ~350 tokens in
Session 05 because the full confirmed SCQ text is injected alongside the
active stage. Fields longer than MAX_SCQ_FIELD_LENGTH (default 500 chars)
are truncated before injection.

---

## Task Definitions

Matteo:
  Job: Guide students through the SCQ framework using Socratic questioning.
  One turn: student message in, one coaching question out.
  Output: plain text, max 120 words, ends with exactly one question mark.
  Out of scope: scoring, model answers, Juli/Tedd topics.
  Tools: save_scq_draft, get_student_progress

Juli:
  Job: Guide students through Monroe's Motivated Sequence for recommendations.
  One turn: student draft in, one stage-specific prompt out.
  Output: plain text, max 150 words, ends with [STAGE: Name].
  Out of scope: SCQ review, evaluation, skipping stages.
  Tools: none (stage read from injected context, advance handled by Express route)

Tedd:
  Job: Evaluate deliverables against the 5 Cs rubric.
  One turn: deliverable in, scored rubric out (JSON).
  Output: raw JSON with evaluation.{clear,concise,compelling,credible,consistent}.{score,observation}.
  Out of scope: revision coaching, process evaluation, re-evaluation of finalised work.
  Tools: get_rubric_config, save_evaluation

---

## Stage State Machine

```
MATTEO -> JULI    when all 3 SCQ elements confirmed (non-null in messages JSON)
JULI -> TEDD      when current_stage = 'Action' AND action_sent = true
TEDD -> COMPLETE  when finalised = 1 on the Tedd session row
```

Stage source: derived from agent_sessions table, no additional schema required.
Module: server/src/lib/stageManager.js

Functions:
  getCurrentStage(userId) -> 'MATTEO' | 'JULI' | 'TEDD' | 'COMPLETE'
  isStageComplete(userId, stage) -> boolean
  getMatteoHandoff(userId) -> { situation, complication, question } | null

Only the orchestrator calls these functions. Individual agent routes do not.

---

## Orchestrator

File: server/src/routes/orchestrator.js
Route: POST /api/chat
Middleware chain: authMiddleware -> agentLimiter -> validateAgentMessage -> handler

Logic:
  1. Call getCurrentStage(user.id)
  2. If COMPLETE, return JSON (no agent call, no SSE)
  3. If JULI, call getMatteoHandoff(user.id) as context
  4. Call the appropriate function from agentCaller.js
  5. On error: write SSE error event and close the stream

Individual routes (/api/agent1,2,3/chat) remain for test suite and professor
tooling. Students never call them directly after Session 05.

---

## Agent Caller

File: server/src/lib/agentCaller.js
Functions: callMatteo, callJuli, callTedd, streamAgent (private)

streamAgent behaviour:
  - Sets SSE headers and calls res.flushHeaders()
  - Spawns python3 -m agent.runner
  - Buffers stderr into stderrBuffer (logged server-side)
  - On non-zero exit code: writes SSE error event with generic message, ends response
  - On req close: kills Python process if still running
  - Calls appendTurn only in stdout 'end' handler (not in 'close' handler)

Cross-agent context:
  callMatteo: passes null context (reads own session via getMatteoHandoff internally)
  callJuli: receives scqContext from orchestrator, builds context block via buildJuliContext
  callTedd: passes null context, checks finalised before spawning

---

## Failure Handling

### Transient API errors (529)

agent/runner.py wraps client.messages.create in call_with_retry:
  - One retry on status 529 after 1 second delay
  - No retry on 400, 401, or other errors
  - On exhausted retry, raises the exception (Python exits non-zero)

### Clean error response

Express catches non-zero exit from Python:
  - Logs full stderr server-side
  - Writes SSE error event: { error: true, message: "agent unavailable" }
  - Ends the response cleanly
  - Client never receives a stack trace

### Client disconnect

req.on('close') kills the Python process.
appendTurn is NOT called on a killed process (partial responses are not saved).

### Structured failure logging

Every failure logs:
  { event, user_id, stage, agent_selected, error_type, error_message, retry_count, timestamp }

---

## HITL Hook

Trigger: Tedd evaluation average score below HITL_SCORE_THRESHOLD (default 3.0)
Action: needs_review = 1 set on agent_sessions row for that Tedd session
Surface: professor GET /api/professor/sessions returns needs_review field,
         ordered needs_review DESC so flagged sessions appear first
No workflow block: students complete their journey regardless of score
Professor resolves by reviewing the flagged session manually

---

## Stage Progression

### Matteo (SCQ elements)

The orchestrator injects confirmed SCQ elements from agent_sessions as
CURRENT SESSION CONTEXT. Matteo calls save_scq_draft when a student confirms
an element. The orchestrator checks isStageComplete after each response and
routes the next message to Juli when all three elements are confirmed.

Confirmed elements: situation, complication, question
Storage: messages JSON column in agent_sessions (agent_id = 'matteo')

### Juli (Monroe's stages)

The orchestrator reads current_stage from the Juli session messages column
and injects it alongside the confirmed SCQ from Matteo's session. After
each response, parseJuliOutput extracts the [STAGE: Name] tag. If the tag
represents the next stage, the route updates current_stage. When Action stage
response has been sent (action_sent = true), the orchestrator routes the
next message to Tedd.

Stage order: Attention, Need, Satisfaction, Visualisation, Action

### Tedd (no stages)

Tedd evaluates once. After save_evaluation completes, finalised = 1. A second
submission from the same user returns 409.

---

## Registered Tools

| Tool name | Agent | What it does | Returns |
|---|---|---|---|
| save_scq_draft | Matteo | Saves a confirmed SCQ element to the DB | {"saved": true, "element": string} |
| get_student_progress | Matteo | Reads confirmed SCQ elements | {"situation": str|null, ...} |
| get_rubric_config | Tedd | Loads agent/config/rubric.json | rubric dict |
| save_evaluation | Tedd | Writes quality_score, finalised = 1, needs_review flag | {"saved": true, "average_score": float, "needs_review": bool} |

TOOL_DISPATCH is the security allowlist. Unregistered names are rejected.

---

## Rate Limiting

Auth endpoint (POST /api/auth/login):
  Window: RATE_LIMIT_AUTH_WINDOW_MS (default 900000 ms = 15 min)
  Max requests: RATE_LIMIT_AUTH_MAX (default 10)
  Key: IP address

Agent endpoints (POST /api/agent1,2,3/chat and POST /api/chat):
  Window: RATE_LIMIT_AGENT_WINDOW_MS (default 60000 ms = 1 min)
  Max requests: RATE_LIMIT_AGENT_MAX (default 30)
  Key: req.user.id

---

## Input Validation

validateAgentMessage (agent1, agent2, /api/chat):
  - typeof message must be 'string'
  - trimmed length must be > 0
  - trimmed length must be <= MAX_MESSAGE_LENGTH (default 2000)

validateTeddMessage (agent3):
  - Same rules with MAX_TEDD_MESSAGE_LENGTH (default 8000)

---

## IDOR Prevention Rule

Student routes: WHERE id = ? AND user_id = ?
Professor routes: WHERE ... AND cohort_id = ?
On zero rows: respond with 404, not 403.

Pre-commit check:
  grep -rn "WHERE id = ?" server/src/
  Every result must be followed by AND user_id = ? or AND cohort_id = ?

---

## Security Non-Negotiables

- JWT verify uses algorithms: ['HS256'] - never omit this
- bcrypt.compare is async only - never compareSync in a route handler
- All DB queries use parameterised statements - never string concatenation
- agent receives user_id from req.user (verified JWT), never from req.body
- Every protected route applies authMiddleware before any other handler
- Role guards applied to all professor/admin routes
- Professor routes scope ALL queries to req.user.cohortId
- Student routes scope ALL session queries to req.user.id
- Error handlers return generic message to client - full error logged server-side
- Rate limiting applied to all auth and agent routes
- Input validation applied to all agent routes
- No stack trace reaches the SSE stream (caught at orchestrator level)

Pre-commit checklist:
  [ ] grep -rn "sk-ant" finds zero hits in source files
  [ ] .env is gitignored and confirmed not tracked
  [ ] All agent routes have authMiddleware applied
  [ ] JWT verify includes algorithms: ['HS256']
  [ ] No bcrypt.compareSync in any route handler
  [ ] No SQL query uses string concatenation
  [ ] All queries on agent_sessions include user_id or cohort_id scope
  [ ] npm test passes with zero failures (at least 15 tests)

---

## Test Suite

Security tests (Session 04): server/tests/security.test.js
  Authentication (5), Role guards (2), IDOR (1+) = 8+ tests

Orchestrator tests (Session 05): server/tests/orchestrator.test.js
  Routing (5), Cross-agent context (2) = 7 tests

Total minimum: 15 passing tests.
Run with: cd server && npm test

Test helpers: server/tests/helpers/testDb.js
  initTestDb(): creates in-memory SQLite, seeds test users, calls setTestDb
  teardownTestDb(): closes the test database
  getTestDb(): returns the test db instance for seeding test data

---

## Pre-Commit Gate (Prompt Changes)

Before committing any change to agent/prompts/ or agent/config/rubric.json:
  1. python evaluation/run_golden.py      >= 90% pass rate (Matteo)
  2. python evaluation/measure_prompt.py  Matteo/Juli <= 3,000, Tedd <= 4,000 tokens
  3. python evaluation/format_check.py    must pass all 5 test inputs
  4. Append one entry to agent/PROMPT_ITERATIONS.md

---

## Evaluation Baselines

Record your baselines here after running evaluation for the first time.

Matteo golden dataset: [X/20 pass - fill in after first run]
Matteo LLM-judge avg: [fill in after first run]
Date recorded: [fill in]

---

## How to Start the Platform

```bash
# First time only
cd server && npm install && npm run db:init

# Run the schema migration for existing databases
sqlite3 data/scq.db "ALTER TABLE agent_sessions ADD COLUMN needs_review INTEGER NOT NULL DEFAULT 0;"

# Every time
node server/src/index.js &       # Express on port 3001

# Test the full journey
python tests/test_end_to_end.py

# Run all tests
cd server && npm test

# Run Matteo evaluation
python evaluation/run_golden.py
```

---

## What Is Not Yet Built (Session 06)

- Production deployment: containerisation, environment variable management,
  health checks, and process supervision
- Database backup and restore strategy
- Logging infrastructure for production (structured logs to a log aggregator)
- HTTPS termination and reverse proxy configuration
- Horizontal scaling considerations for the SQLite database

Do not implement these until Session 06. They are out of scope for this session.
