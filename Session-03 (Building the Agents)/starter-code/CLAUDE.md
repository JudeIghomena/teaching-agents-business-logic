# CLAUDE.md - SCQ Platform (End of Session 03)

This file describes the full state of the SCQ Business Case Logic platform
after Session 03 is complete. Any coding agent (Claude Code, Cursor, Codex)
starting work on this project should read this file first.

---

## Role

You are a coding agent working on the SCQ Business Case Logic platform,
an AI coaching application for MBA students at Hult International Business School.

The platform hosts three AI coaching agents: Matteo (Issue Analysis),
Juli (Monroe's Motivated Sequence), and Tedd (5 Cs peer review).
After Session 03, all three agents are fully implemented and the platform
runs end to end. Session 04 will add security hardening for deployment.

---

## Layer Ownership

| Layer | Owner | Do not cross this boundary |
|---|---|---|
| HTTP routing, auth, SSE, rate limiting | Express (server/src/) | Agents do not import Express |
| Database reads and writes | Express routes + db.js | Agents do not import better-sqlite3 |
| JWT verification | authMiddleware | Agents receive user_id from req.user, never from req.body |
| Agent reasoning and response | Python agents (agent/) | Express does not write prompt logic |
| Prompt versioning | agent/prompts/*.txt | Never hardcode system prompts in .py files |
| Rubric configuration | agent/config/rubric.json | Tedd reads this file via get_rubric_config tool |

---

## Project Structure

```
scq-platform/
|
|-- server/
|   |-- src/
|   |   |-- index.js              Express entry point with rate limiting and error handler
|   |   |-- db.js                 better-sqlite3 singleton: getOrCreateSession, appendTurn,
|   |   |                         getStudentProgress, getJuliSession
|   |   |-- db-init.js            Schema creation (run once with npm run db:init)
|   |   |-- routes/
|   |   |   |-- auth.js           POST /api/auth/login (bcrypt + JWT sign)
|   |   |   |-- agent1.js         POST /api/agent1/chat (Matteo, with stage injection)
|   |   |   |-- agent2.js         POST /api/agent2/chat (Juli, with stage + SCQ injection)
|   |   |   |-- agent3.js         POST /api/agent3/chat (Tedd, with double-submission guard)
|   |   |   `-- professor.js      GET /api/professor/sessions, PATCH /sessions/:id/finalise
|   |   `-- middleware/
|   |       |-- auth.js           JWT verify with algorithms: ['HS256']
|   |       |-- roleGuard.js      requireRole('student'|'professor'|'admin')
|   |       `-- rateLimiter.js    30 req/min/user on agent routes
|   |-- .env                      JWT_SECRET, JWT_EXPIRY, PORT (gitignored)
|   |-- .env.example              Template with placeholder values (committed)
|   `-- package.json
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
|   `-- test_end_to_end.py        Full student journey test
|
|-- data/
|   `-- scq.db                    SQLite database (gitignored)
|
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

The messages column stores JSON. For Matteo sessions, it holds conversation turns
AND confirmed SCQ elements (situation, complication, question keys). For Juli
sessions, it holds turns AND current_stage. For Tedd sessions, quality_score is
written directly to the row column, not into messages.

---

## Context Window Budget

| Agent | Context limit | System prompt | Injected context | History | Buffer |
|---|---|---|---|---|---|
| Matteo | 20,000 tokens | max 3,000 | ~80 (SCQ state) | max 13,920 | 3,000 |
| Juli | 20,000 tokens | max 3,000 | ~230 (stage + SCQ) | max 13,770 | 3,000 |
| Tedd | 20,000 tokens | max 4,000 | none | min (one shot) | 16,000 |

Tedd is a one-shot evaluator. His history is typically one user turn.
The 16,000 token buffer means even a very long deliverable fits.

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

The web layer (routes/agent1.js) reads the student's confirmed SCQ elements
from the agent_sessions table and injects them as CURRENT SESSION CONTEXT.
Matteo calls save_scq_draft when a student explicitly confirms an element.
The web layer does not force stage advance. Matteo drives it through tool use.

```
Confirmed elements: situation, complication, question
Storage: messages JSON column in agent_sessions (agent_id = 'matteo')
```

### Juli (Monroe's stages)

The web layer reads current_stage from the messages column of the Juli session.
After each response, parseJuliOutput extracts the [STAGE: Name] tag.
If the tag represents the next stage in sequence, the web layer updates current_stage.
Stage order: Attention, Need, Satisfaction, Visualisation, Action.
Stages must advance one step at a time (no jumping).

```
Current stage field: messages.current_stage in agent_sessions (agent_id = 'juli')
```

### Tedd (no stages)

Tedd evaluates once per deliverable. After save_evaluation completes,
finalised = 1 is set on the session row. A second submission returns 409.

---

## Registered Tools

| Tool name | Agent | What it does | Returns |
|---|---|---|---|
| save_scq_draft | Matteo | Saves a confirmed SCQ element (situation/complication/question) to the DB | {"saved": true, "element": string} |
| get_student_progress | Matteo | Reads confirmed SCQ elements from the most recent Matteo session | {"situation": str or null, "complication": str or null, "question": str or null} |
| get_rubric_config | Tedd | Loads agent/config/rubric.json | rubric dict with dimension definitions |
| save_evaluation | Tedd | Writes quality_score and sets finalised = 1 on the Tedd session | {"saved": true, "average_score": float} |

Every tool name in TOOLS must have a matching entry in TOOL_DISPATCH.
TOOL_DISPATCH is the security allowlist. Any call to an unregistered tool name
must be rejected with an error before the function is executed.

---

## Output Formats

Matteo: plain text, max 120 words, exactly one question at the end, no markdown.
  Validated by: validateMatteoOutput() in server/src/routes/agent1.js

Juli: plain text, max 150 words, ends with [STAGE: StageName].
  Parsed by: parseJuliOutput() in server/src/routes/agent2.js

Tedd: raw JSON only, no markdown fences, no preamble.
  Schema: { "evaluation": { "clear": { "score": 1-5, "observation": "sentence" }, ... } }
  Parsed by: parseTeddOutput() in server/src/routes/agent3.js with clean fallback.
  If parseTeddOutput strips markdown fences as a fallback, log the raw text server-side.

---

## Student Journey

The full flow from first login to final evaluation:

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

## Security Non-Negotiables

- JWT verify must use algorithms: ['HS256'] - never omit this
- bcrypt.compare is async only - never compareSync in a route handler
- All DB queries use parameterised statements - never string concatenation
- agent receives user_id from req.user (verified JWT) not from req.body
- Every protected route must apply authMiddleware before any other handler
- Role guards (requireRole) applied to all professor/admin routes
- Professor routes scope ALL queries to req.user.cohort_id (IDOR prevention)
- Error handlers return generic message to client - full error logged server-side only
- Rate limiting: 30 requests per minute per user on all agent routes

Pre-commit checklist:
  [ ] grep -rn "sk-ant" finds zero hits in source files
  [ ] .env is gitignored and confirmed not tracked
  [ ] All agent routes have authMiddleware applied
  [ ] JWT verify includes algorithms: ['HS256']
  [ ] No bcrypt.compareSync in any route handler
  [ ] No SQL query uses string concatenation

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

# Run Matteo evaluation
python evaluation/run_golden.py
```

---

## What Is Not Yet Built (Session 04)

- Security headers (Helmet CSP, X-Content-Type-Options, X-Frame-Options)
- IDOR test suite (automated check that student A cannot read student B's data)
- npm audit clean run (zero high/critical findings)
- HTTPS setup and Strict-Transport-Security header
- Dependency vulnerability log in SECURITY.md
- SECURITY.md at project root (required by all Janna AI projects)

Do not implement these until Session 04. They are out of scope for this session.
