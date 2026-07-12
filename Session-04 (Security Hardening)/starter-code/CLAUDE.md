# CLAUDE.md - SCQ Platform (End of Session 04)

This file describes the full state of the SCQ Business Case Logic platform
after Session 04 is complete. Any coding agent (Claude Code, Cursor, Codex)
starting work on this project should read this file first.

---

## Role

You are a coding agent working on the SCQ Business Case Logic platform,
an AI coaching application for MBA students at Hult International Business School.

The platform hosts three AI coaching agents: Matteo (Issue Analysis),
Juli (Monroe's Motivated Sequence), and Tedd (5 Cs peer review).
After Session 04, all three agents are running and the platform has full
security hardening: rate limiting, input validation, IDOR prevention, and
a passing security test suite. Session 05 will add the orchestration layer.

---

## Layer Ownership

| Layer | Owner | Do not cross this boundary |
|---|---|---|
| HTTP routing, auth, SSE, rate limiting, validation | Express (server/src/) | Agents do not import Express |
| Database reads and writes | Express routes + db.js | Agents do not import better-sqlite3 |
| JWT verification | authMiddleware | Agents receive user_id from req.user, never from req.body |
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
|   |   |   |-- agent1.js         POST /api/agent1/chat (Matteo)
|   |   |   |-- agent2.js         POST /api/agent2/chat (Juli)
|   |   |   |-- agent3.js         POST /api/agent3/chat (Tedd)
|   |   |   `-- professor.js      GET /api/professor/sessions, PATCH /sessions/:id/finalise
|   |   `-- middleware/
|   |       |-- auth.js           JWT verify with algorithms: ['HS256']
|   |       |-- roleGuard.js      requireRole('student'|'professor'|'admin')
|   |       |-- rateLimiter.js    authLimiter (IP) + agentLimiter (user ID)
|   |       `-- validator.js      validateAgentMessage + validateTeddMessage
|   |-- tests/
|   |   |-- security.test.js      Auth, role guard, IDOR test suite
|   |   `-- helpers/
|   |       `-- testDb.js         initTestDb + teardownTestDb for in-memory DB
|   |-- .env                      All secrets and config (gitignored)
|   |-- .env.example              Template with placeholder values (committed)
|   `-- package.json              Version 0.4.0, adds helmet
|
|-- agent/
|   |-- runner.py                 run_agent_loop(message, history, system_prompt) -> str
|   |-- context.py                build_system_prompt(agent_id, version) -> str
|   |-- model_config.py           MODEL per agent, MAX_TOKENS, MAX_HISTORY_TURNS
|   |-- tool_registry.py          TOOLS list, TOOL_DISPATCH dict, all implementations
|   |-- infrastructure.py         get_client(), TurnTrace, get_logger()
|   |-- session_store.py          SessionStore singleton (Tier 2 memory)
|   |-- prompts/
|   |   |-- matteo_v1.txt         Matteo system prompt (with tool-calling rules)
|   |   |-- juli_v1.txt           Juli system prompt (with [STAGE:] tag requirement)
|   |   `-- tedd_v1.txt           Tedd system prompt (JSON-only output)
|   |-- config/
|   |   `-- rubric.json           5 Cs rubric definitions used by get_rubric_config
|   `-- PROMPT_ITERATIONS.md      Prompt change log
|
|-- evaluation/
|   |-- golden/
|   |   `-- matteo_golden.json    20 golden records for Matteo
|   |-- run_golden.py             Golden dataset runner
|   |-- llm_judge.py              LLM-as-judge for coaching quality
|   `-- measure_prompt.py         Token counter per prompt version
|
|-- tests/
|   `-- test_end_to_end.py        Full student journey test (Python, uses requests lib)
|
|-- data/
|   `-- scq.db                    SQLite database (gitignored)
|
|-- SECURITY.md                   Full platform security posture document
|-- .env                          ANTHROPIC_API_KEY (gitignored)
|-- .env.example                  Template (committed)
|-- .gitignore                    .env, data/, __pycache__/
`-- requirements.txt              anthropic, python-dotenv, requests
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

---

## Context Window Budget

| Agent | Context limit | System prompt | Injected context | History | Buffer |
|---|---|---|---|---|---|
| Matteo | 20,000 tokens | max 3,000 | ~80 (SCQ state) | max 13,920 | 3,000 |
| Juli | 20,000 tokens | max 3,000 | ~230 (stage + SCQ) | max 13,770 | 3,000 |
| Tedd | 20,000 tokens | max 4,000 | none | min (one shot) | 16,000 |

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

## Stage Progression

### Matteo (SCQ elements)

The web layer reads the student's confirmed SCQ elements from agent_sessions
and injects them as CURRENT SESSION CONTEXT. Matteo calls save_scq_draft when
a student explicitly confirms an element. The web layer does not force stage
advance. Matteo drives it through tool use.

Confirmed elements: situation, complication, question
Storage: messages JSON column in agent_sessions (agent_id = 'matteo')

### Juli (Monroe's stages)

The web layer reads current_stage from the messages column of the Juli session.
After each response, parseJuliOutput extracts the [STAGE: Name] tag. If the
tag represents the next stage in sequence, the web layer updates current_stage.
Stage order: Attention, Need, Satisfaction, Visualisation, Action.
Stages must advance one step at a time (no jumping).

Current stage field: messages.current_stage in agent_sessions (agent_id = 'juli')

### Tedd (no stages)

Tedd evaluates once per deliverable. After save_evaluation completes,
finalised = 1 is set on the session row. A second submission returns 409.

---

## Registered Tools

| Tool name | Agent | What it does | Returns |
|---|---|---|---|
| save_scq_draft | Matteo | Saves a confirmed SCQ element to the DB | {"saved": true, "element": string} |
| get_student_progress | Matteo | Reads confirmed SCQ elements from the most recent Matteo session | {"situation": str or null, "complication": str or null, "question": str or null} |
| get_rubric_config | Tedd | Loads agent/config/rubric.json | rubric dict with dimension definitions |
| save_evaluation | Tedd | Writes quality_score and sets finalised = 1 on the Tedd session | {"saved": true, "average_score": float} |

Every tool name in TOOLS must have a matching entry in TOOL_DISPATCH.
TOOL_DISPATCH is the security allowlist. Unregistered tool names are rejected.

---

## Output Formats

Matteo: plain text, max 120 words, exactly one question at the end, no markdown.
  Validated by: validateMatteoOutput() in server/src/routes/agent1.js

Juli: plain text, max 150 words, ends with [STAGE: StageName].
  Parsed by: parseJuliOutput() in server/src/routes/agent2.js

Tedd: raw JSON only, no markdown fences, no preamble.
  Schema: { "evaluation": { "clear": { "score": 1-5, "observation": "sentence" }, ... } }
  Parsed by: parseTeddOutput() in server/src/routes/agent3.js with clean fallback.

---

## Student Journey

```
POST /api/auth/login                Student logs in, receives JWT

POST /api/agent1/chat (n turns)     Matteo coaches SCQ
  -- save_scq_draft x3              Three elements confirmed, saved to DB

POST /api/agent2/chat (n turns)     Juli coaches Monroe's Sequence
  -- Stage advances: Attention through Action
  -- current_stage updated in DB after each advance

POST /api/agent3/chat (1 turn)      Tedd evaluates the final deliverable
  -- get_rubric_config              Rubric loaded from agent/config/rubric.json
  -- save_evaluation                quality_score written, finalised = 1

GET /api/professor/sessions         Professor sees cohort quality scores
PATCH /sessions/:id/finalise        Professor can manually finalise sessions
```

---

## Rate Limiting

Auth endpoint (POST /api/auth/login):
  Window: RATE_LIMIT_AUTH_WINDOW_MS (default 900000 ms = 15 min)
  Max requests: RATE_LIMIT_AUTH_MAX (default 10)
  Key: IP address
  On exceed: 429 with Retry-After header

Agent endpoints (POST /api/agent1,2,3/chat):
  Window: RATE_LIMIT_AGENT_WINDOW_MS (default 60000 ms = 1 min)
  Max requests: RATE_LIMIT_AGENT_MAX (default 30)
  Key: req.user.id (falls back to IP if user not authenticated)
  On exceed: 429 with Retry-After header

Implementation: server/src/middleware/rateLimiter.js
Library: express-rate-limit (in dependencies)

---

## Input Validation

All agent routes apply validation middleware before the agent call.

validateAgentMessage (agent1, agent2):
  - typeof message must be 'string'
  - trimmed length must be > 0
  - trimmed length must be <= MAX_MESSAGE_LENGTH (default 2000)
  - req.body.message is set to trimmed value before calling next()

validateTeddMessage (agent3):
  - Same rules but uses MAX_TEDD_MESSAGE_LENGTH (default 8000)

Implementation: server/src/middleware/validator.js

---

## IDOR Prevention Rule

Every database query on agent_sessions must include a scope condition:

Student routes: WHERE id = ? AND user_id = ?
Professor routes: WHERE ... AND cohort_id = ?
Insertion followed by SELECT of own row: acceptable (ID from server, not client)

When a scoped query returns zero rows: respond with 404, not 403.
Returning 403 reveals that the resource exists. 404 reveals nothing.

Pre-commit check:
  grep -rn "WHERE id = ?" server/src/
  Every result must be followed by AND user_id = ? or AND cohort_id = ?

---

## Security Non-Negotiables

- JWT verify must use algorithms: ['HS256'] - never omit this
- bcrypt.compare is async only - never compareSync in a route handler
- All DB queries use parameterised statements - never string concatenation
- agent receives user_id from req.user (verified JWT) not from req.body
- Every protected route must apply authMiddleware before any other handler
- Role guards (requireRole) applied to all professor/admin routes
- Professor routes scope ALL queries to req.user.cohortId (IDOR prevention)
- Student routes scope ALL session queries to req.user.id (IDOR prevention)
- Error handlers return generic message to client - full error logged server-side only
- Rate limiting applied to all auth and agent routes
- Input validation applied to all agent routes

Pre-commit checklist:
  [ ] grep -rn "sk-ant" finds zero hits in source files
  [ ] .env is gitignored and confirmed not tracked
  [ ] All agent routes have authMiddleware applied
  [ ] JWT verify includes algorithms: ['HS256']
  [ ] No bcrypt.compareSync in any route handler
  [ ] No SQL query uses string concatenation
  [ ] All queries on agent_sessions include user_id or cohort_id scope
  [ ] npm test passes with zero failures

---

## Security Test Suite

File: server/tests/security.test.js
Run with: npm test
Must pass before every commit that touches auth, middleware, or DB queries.

Categories:
  Authentication (5 tests): no token, bad token, wrong secret, public login, wrong password
  Role guards (2 tests): student on professor route (403), professor on professor route (200)
  IDOR prevention (1+ tests): student B gets 404 accessing student A's session

Test helpers: server/tests/helpers/testDb.js
  initTestDb(): creates in-memory SQLite, seeds test users, calls setTestDb
  teardownTestDb(): closes the test database

---

## Pre-Commit Gate (Prompt Changes)

Before committing any change to agent/prompts/ or agent/config/rubric.json:
  1. python evaluation/run_golden.py      must be >= 90% pass rate (Matteo)
  2. python evaluation/measure_prompt.py  Matteo/Juli <= 3,000, Tedd <= 4,000 tokens
  3. python evaluation/format_check.py    must pass all 5 test inputs
  4. Append one entry to agent/PROMPT_ITERATIONS.md

---

## Evaluation Baselines

Record your baselines here after running evaluation for the first time.
This section must be updated before any prompt is committed.

Matteo golden dataset: [X/20 pass - fill in after first run]
Matteo LLM-judge avg: [fill in after first run]
Date recorded: [fill in]

---

## How to Start the Platform

```bash
# First time only
cd server && npm install && npm run db:init

# Every time
node server/src/index.js &       # Express on port 3001

# Test the full journey
python tests/test_end_to_end.py

# Run security tests
cd server && npm test

# Run Matteo evaluation
python evaluation/run_golden.py
```

---

## What Is Not Yet Built (Session 05)

- Single orchestrator endpoint that routes students to the correct agent
  automatically (students do not need to know which agent they are talking to)
- Cross-agent context handoff (Matteo's confirmed SCQ passed to Juli automatically)
- Stage progression managed by orchestrator (not by individual routes)
- Failure handling: what happens when an agent call fails mid-session
- Human-in-the-loop approval hook for Tedd evaluations above a threshold

Do not implement these until Session 05. They are out of scope for this session.
