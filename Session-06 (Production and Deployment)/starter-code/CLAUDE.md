# CLAUDE.md - SCQ Platform (Definitive - End of Session 06)

This file is the authoritative operating brief for the SCQ Business Case Logic
platform. Any coding agent or developer starting work on this platform reads
this file first and has a complete picture of every decision made across the
six-session build.

---

## Role

You are a coding agent working on the SCQ Business Case Logic platform,
an AI coaching application for MBA students at Hult International Business School.

The platform hosts three AI coaching agents: Matteo (Issue Analysis using the
SCQ framework), Juli (Recommendation structure using Monroe's Motivated
Sequence), and Tedd (Peer review using the 5 Cs rubric). Students interact
with a single endpoint that routes them through all three agents in sequence.
The platform is production-deployed on Railway with persistent SQLite storage,
structured monitoring, per-student token budgets, and Anthropic prompt caching.

---

## Layer Ownership

| Layer | Owner | Do not cross this boundary |
|---|---|---|
| HTTP routing, auth, SSE, rate limiting, validation | Express (server/src/) | Agents do not import Express |
| Database reads and writes | Express routes + db.js | Agents do not import better-sqlite3 |
| JWT verification | authMiddleware | Agents receive user_id from req.user, never from req.body |
| Stage routing | stageManager.js | Only the orchestrator calls stageManager |
| Agent invocation and streaming | agentCaller.js | Only orchestrator.js imports agentCaller |
| Error tracking | errorTracker.js | Only agentCaller.js and orchestrator.js call it |
| Agent reasoning and response | Python agents (agent/) | Express does not write prompt logic |
| Prompt versioning | agent/prompts/*.txt | Never hardcode system prompts in .py files |
| Prompt caching | agent/context.py | Cache headers are set here, not in runner.py |
| Rubric configuration | agent/config/rubric.json | Tedd reads this via get_rubric_config tool |
| Security controls | middleware/ | All security middleware lives here, not in routes |

---

## Project Structure

```
scq-platform/
|
|-- server/
|   |-- src/
|   |   |-- index.js              Express entry point: CORS guard, routes, error handler
|   |   |-- app.js                buildApp() export (no app.listen - used by test suite)
|   |   |-- db.js                 better-sqlite3, reads DB_PATH from env, setTestDb export
|   |   |-- db-init.js            Schema creation (npm run db:init)
|   |   |-- routes/
|   |   |   |-- auth.js           POST /api/auth/login
|   |   |   |-- health.js         GET /api/health (no auth, checks db + returns error stats)
|   |   |   |-- orchestrator.js   POST /api/chat (student-facing, budget check then routing)
|   |   |   |-- agent1.js         POST /api/agent1/chat (Matteo, kept for test suite)
|   |   |   |-- agent2.js         POST /api/agent2/chat (Juli, kept for test suite)
|   |   |   |-- agent3.js         POST /api/agent3/chat (Tedd, kept for test suite)
|   |   |   `-- professor.js      GET /sessions, GET /cost, PATCH /sessions/:id/finalise
|   |   |-- lib/
|   |   |   |-- stageManager.js   getCurrentStage, isStageComplete, getMatteoHandoff
|   |   |   |-- agentCaller.js    callMatteo, callJuli, callTedd, streamAgent
|   |   |   `-- errorTracker.js   recordRequest, getErrorStats (5-min sliding window)
|   |   `-- middleware/
|   |       |-- auth.js           JWT verify with algorithms: ['HS256']
|   |       |-- roleGuard.js      requireRole('student'|'professor'|'admin')
|   |       |-- rateLimiter.js    authLimiter (IP) + agentLimiter (user ID)
|   |       `-- validator.js      validateAgentMessage + validateTeddMessage
|   |-- tests/
|   |   |-- security.test.js      Auth, role guard, IDOR tests (Session 04)
|   |   |-- orchestrator.test.js  Stage routing and context tests (Session 05)
|   |   `-- helpers/
|   |       `-- testDb.js         initTestDb, teardownTestDb, getTestDb
|   |-- scripts/
|   |   `-- backup-db.js          Timestamped SQLite backup (npm run db:backup)
|   |-- .env                      Secrets and config (gitignored)
|   |-- .env.example              Annotated template (committed)
|   `-- package.json              Version 0.6.0
|
|-- agent/
|   |-- runner.py                 call_with_retry (529 retry), __USAGE__ token emission
|   |-- context.py                build_system_prompt returns list with cache_control block
|   |-- model_config.py           MODEL, MAX_TOKENS, MAX_HISTORY_TURNS per agent
|   |-- tool_registry.py          TOOL_DISPATCH allowlist, all tool implementations
|   |                             save_evaluation sets needs_review flag
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
|   |-- golden/matteo_golden.json
|   |-- run_golden.py
|   |-- llm_judge.py
|   `-- measure_prompt.py
|
|-- tests/
|   `-- test_end_to_end.py
|
|-- data/
|   `-- scq.db                    SQLite database (gitignored, on Railway Volume at /data/)
|
|-- HANDOFF.md                    Human-readable project handoff document
|-- SECURITY.md                   Platform security posture document
|-- Procfile                      web: node server/src/index.js (used by Railway)
|-- .env                          ANTHROPIC_API_KEY (gitignored)
|-- .env.example
|-- .gitignore
`-- requirements.txt              anthropic>=0.50.0, python-dotenv, requests
```

---

## Model Routing

| Agent | Model | Reason |
|---|---|---|
| Matteo | claude-haiku-4-5-20251001 | Conversational coaching, speed matters for streaming |
| Juli | claude-haiku-4-5-20251001 | Conversational coaching, speed matters for streaming |
| Tedd | claude-haiku-4-5-20251001 | Switch to claude-sonnet-5 if JSON error rate exceeds 5% |

Model names must come from model_config.py. Never hardcode in routes or runner.py.
To change a model: update model_config.py, run the golden dataset, confirm 90%+.

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
    total_tokens  INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

### Schema migrations for existing databases

```sql
-- Session 05
ALTER TABLE agent_sessions ADD COLUMN needs_review INTEGER NOT NULL DEFAULT 0;

-- Session 06
ALTER TABLE users ADD COLUMN total_tokens INTEGER NOT NULL DEFAULT 0;
```

Database path: reads from `DB_PATH` environment variable.
Default: `./data/scq.db` in development, `/data/scq.db` in production.

---

## Context Window Budget

| Agent | Context limit | System prompt | Injected context | History | Buffer |
|---|---|---|---|---|---|
| Matteo | 20,000 tokens | max 3,000 | ~80 (SCQ state) | max 13,920 | 3,000 |
| Juli | 20,000 tokens | max 3,000 | ~350 (stage + full SCQ) | max 13,650 | 3,000 |
| Tedd | 20,000 tokens | max 4,000 | none | min (one shot) | 16,000 |

System prompts are cacheable. On calls 2+ per session, the cached portion
costs approximately 10% of the normal input token rate.

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
  Tools: none (stage from injected context, advance handled by Express route)

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
TEDD -> COMPLETE  when finalised = 1 on Tedd session row
```

Stage is derived from agent_sessions table. No additional schema required.
Module: server/src/lib/stageManager.js

Functions:
  getCurrentStage(userId) -> 'MATTEO' | 'JULI' | 'TEDD' | 'COMPLETE'
  isStageComplete(userId, stage) -> boolean
  getMatteoHandoff(userId) -> { situation, complication, question } | null

Only the orchestrator calls these. Individual agent routes do not.

---

## Orchestrator

File: server/src/routes/orchestrator.js
Route: POST /api/chat
Middleware: authMiddleware -> agentLimiter -> validateAgentMessage -> handler

Handler logic:
  1. Budget check: if total_tokens >= TOKEN_BUDGET_PER_USER, return JSON (not SSE)
  2. getCurrentStage(user.id)
  3. If COMPLETE, return JSON (no agent call)
  4. If JULI, getMatteoHandoff(user.id) as context
  5. Call appropriate agentCaller function
  6. On error, write SSE error event and end response

Individual routes (/api/agent1,2,3/chat) remain for test suite and professor tooling.

---

## Agent Caller

File: server/src/lib/agentCaller.js

streamAgent behaviour:
  - Sets SSE headers, calls res.flushHeaders()
  - Records requestStart = Date.now()
  - Spawns python3 -m agent.runner
  - Tracks firstTokenSent and timeToFirstToken
  - Parses __USAGE__: prefix line for token counts (does not stream to client)
  - Buffers stderr, logs server-side only
  - On non-zero exit: writes SSE error event with generic message, ends response
  - On req close: kills Python process
  - In stdout 'end': appendTurn, update total_tokens, log turn_complete, send done event
  - Calls recordRequest(true/false) on error/success

---

## Failure Handling

| Failure | Response |
|---|---|
| 529 Overloaded | Python retries once after 1 second, then exits non-zero |
| Non-zero Python exit | Express writes SSE error event with generic message, ends stream |
| Client disconnect | req.on('close') kills Python process, no appendTurn |
| Budget exceeded | Orchestrator returns JSON before any agent call |

All failure log events include: event, user_id, stage, error_type, timestamp.
Stack traces go to console.error only. Clients never see internal errors.

---

## HITL Hook

Trigger: Tedd evaluation average score below HITL_SCORE_THRESHOLD (default 3.0)
Action: needs_review = 1 on agent_sessions row
Surface: GET /api/professor/sessions orders by needs_review DESC
No flow block: students complete their journey regardless of score

---

## Production Monitoring

Token tracking: __USAGE__ line from Python agent parsed in agentCaller.js.
Error tracking: errorTracker.js with 5-minute sliding window, 5% alert threshold.

turn_complete log structure:
  { event, agent_id, user_id, input_tokens, output_tokens,
    time_to_first_token_ms, total_latency_ms, timestamp }

Health check: GET /api/health (no auth) checks db + returns last_5min error stats.

---

## Prompt Caching

System prompts returned as list of dicts with cache_control: { type: 'ephemeral' }.
Applies to all three agents. Cached for approximately 5 minutes.
Reduces input token cost by ~30% on calls 2+ within a session.

---

## Registered Tools

| Tool name | Agent | What it does | Returns |
|---|---|---|---|
| save_scq_draft | Matteo | Saves confirmed SCQ element | {"saved": true, "element": string} |
| get_student_progress | Matteo | Reads confirmed SCQ from session | {"situation", "complication", "question"} |
| get_rubric_config | Tedd | Loads rubric.json | rubric dict |
| save_evaluation | Tedd | Writes quality_score, finalised=1, needs_review flag | {"saved", "average_score", "needs_review"} |

TOOL_DISPATCH is the security allowlist. Unregistered names are rejected.

---

## Rate Limiting

Auth (POST /api/auth/login):
  Window: RATE_LIMIT_AUTH_WINDOW_MS (default 900000 ms)
  Max: RATE_LIMIT_AUTH_MAX (default 10)
  Key: IP address

Agent (POST /api/agent1,2,3/chat and POST /api/chat):
  Window: RATE_LIMIT_AGENT_WINDOW_MS (default 60000 ms)
  Max: RATE_LIMIT_AGENT_MAX (default 30)
  Key: req.user.id

---

## Input Validation

validateAgentMessage (agent1, agent2, /api/chat): max MAX_MESSAGE_LENGTH (default 2000)
validateTeddMessage (agent3): max MAX_TEDD_MESSAGE_LENGTH (default 8000)
Both check typeof, trim, empty, then set req.body.message to trimmed value.

---

## IDOR Prevention

Student routes: WHERE id = ? AND user_id = ?
Professor routes: WHERE ... AND cohort_id = ?
On zero rows: respond 404, not 403.

Pre-commit: grep -rn "WHERE id = ?" server/src/
Every match must be followed by AND user_id = ? or AND cohort_id = ?

---

## Security Non-Negotiables

- JWT verify: algorithms: ['HS256'] always
- bcrypt: async only, cost factor 12 minimum, no compareSync
- SQL: parameterised queries only, no string concatenation
- authMiddleware on every protected route
- Role guards on professor/admin routes
- CORS: explicit origin from CORS_ORIGIN env var, startup guard in production
- Error responses: generic message to client, full error to console.error only
- Rate limiting on auth and agent routes
- Input validation on agent routes
- Secrets: never in source files, always in .env

Pre-commit checklist:
  [ ] grep -rE "sk-ant" server/src/ returns zero hits
  [ ] .env is gitignored and not tracked
  [ ] authMiddleware on all protected routes
  [ ] JWT verify includes algorithms: ['HS256']
  [ ] No bcrypt.compareSync in any handler
  [ ] No SQL built by string concatenation
  [ ] All session queries scoped to user_id or cohort_id
  [ ] npm test passes with zero failures (minimum 15 tests)
  [ ] npm audit returns zero high/critical vulnerabilities

---

## Test Suite

Security tests (Session 04): server/tests/security.test.js
  Auth (5), Role guards (2), IDOR (1+) = minimum 8 tests

Orchestrator tests (Session 05): server/tests/orchestrator.test.js
  Routing (5), Context (2) = 7 tests

Total minimum: 15 passing tests.
Run: cd server && npm test

Test helpers: server/tests/helpers/testDb.js
  initTestDb(): in-memory SQLite, seeds users, calls setTestDb
  teardownTestDb(): closes test db
  getTestDb(): returns db instance for seeding test data

---

## Pre-Commit Gate (Prompt Changes)

Before any change to agent/prompts/ or agent/config/rubric.json:
  1. python evaluation/run_golden.py      >= 90% pass rate (all agents)
  2. python evaluation/measure_prompt.py  Matteo/Juli <= 3,000; Tedd <= 4,000 tokens
  3. python evaluation/format_check.py    all 5 test inputs pass
  4. Append entry to agent/PROMPT_ITERATIONS.md

---

## Deployment

Host: Railway
Database: SQLite on Railway Volume mounted at /data
DB_PATH: /data/scq.db in production
Start command: node server/src/index.js (via Procfile: web: node server/src/index.js)
Python: requirements.txt at project root, Railway installs automatically
HTTPS: automatic from Railway, no config needed
Health check URL: GET /api/health (Railway pings this to decide traffic routing)

First deploy steps:
  1. Push to GitHub (Railway deploys from main on every push)
  2. Set all environment variables in Railway dashboard
  3. Add Volume at /data
  4. Run npm run db:init via Railway one-off command
  5. Verify GET /api/health returns { status: 'ok', db: 'ok' }

---

## How to Start (Development)

```bash
# First time
cd server && npm install && npm run db:init

# Python dependencies
pip install -r requirements.txt

# Start the server
node server/src/index.js

# Run tests
cd server && npm test

# Run agent evaluation
python evaluation/run_golden.py

# Backup database
npm run db:backup
```

---

## Student Journey (Complete)

```
POST /api/auth/login              Student logs in, receives JWT

POST /api/chat (n turns)          Orchestrator routes to Matteo
  -- save_scq_draft x3            Three SCQ elements confirmed

POST /api/chat (n turns)          Orchestrator routes to Juli
  -- Stage advances: Attention through Action
  -- SCQ from Matteo injected into each turn

POST /api/chat (1 turn)           Orchestrator routes to Tedd
  -- get_rubric_config            Rubric loaded
  -- save_evaluation              quality_score, finalised=1, needs_review set if low score

POST /api/chat                    Stage = COMPLETE, JSON response, no agent call

GET  /api/professor/sessions      Professor sees cohort scores + flagged sessions
GET  /api/professor/cost          Professor sees cohort token usage
```

---

## Evaluation Baselines

Record after first run. Update on every prompt change.

Matteo golden dataset: [X/20 pass - fill in]
Matteo LLM-judge avg: [fill in]
Date recorded: [fill in]
