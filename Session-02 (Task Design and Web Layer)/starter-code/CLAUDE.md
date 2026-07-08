# CLAUDE.md - SCQ Platform (End of Session 02)

This file describes the full state of the SCQ Business Case Logic platform
after Session 02 is complete. Any coding agent (Claude Code, Cursor, Codex)
starting work on this project should read this file first.

---

## Role

You are a coding agent working on the SCQ Business Case Logic platform,
an AI coaching application for MBA students at Hult International Business School.

The platform hosts three AI coaching agents: Matteo (Issue Analysis),
Juli (Monroe's Motivated Sequence), and Tedd (5 Cs peer review).
After Session 02, the web layer is complete and the agent prompts are drafted.
Session 03 will implement the full logic of all three agents.

---

## Layer Ownership

| Layer | Owner | Do not cross this boundary |
|---|---|---|
| HTTP routing, auth, SSE streaming | Express (server/src/) | Agents do not import Express |
| Database reads and writes | Express routes + db.js | Agents do not import better-sqlite3 |
| JWT verification | authMiddleware | Agents receive user_id from req.user, never from req.body |
| Agent reasoning and response | Python agents (agent/) | Express does not write prompt logic |
| Prompt versioning | agent/prompts/*.txt | Never hardcode system prompts in .py files |

---

## Project Structure

```
scq-platform/
|
|-- server/
|   |-- src/
|   |   |-- index.js              Express entry point
|   |   |-- db.js                 better-sqlite3 singleton, getOrCreateSession, appendTurn
|   |   |-- db-init.js            Schema creation (run once with npm run db:init)
|   |   |-- routes/
|   |   |   |-- auth.js           POST /api/auth/login (bcrypt + JWT sign)
|   |   |   |-- agent1.js         POST /api/agent1/chat (Matteo)
|   |   |   |-- agent2.js         POST /api/agent2/chat (Juli)
|   |   |   `-- agent3.js         POST /api/agent3/chat (Tedd)
|   |   `-- middleware/
|   |       |-- auth.js           JWT verify with algorithms: ['HS256']
|   |       `-- roleGuard.js      requireRole('student'|'professor'|'admin')
|   |-- .env                      JWT_SECRET, JWT_EXPIRY, PORT (gitignored)
|   |-- .env.example              Template with placeholder values (committed)
|   `-- package.json
|
|-- agent/
|   |-- runner.py                 run_agent_loop(message, history) -> str
|   |-- context.py                build_system_prompt(agent_id, version) -> str
|   |-- model_config.py           MODEL per agent, MAX_TOKENS, TEMPERATURE
|   |-- tool_registry.py          TOOLS list, TOOL_DISPATCH dict
|   |-- infrastructure.py         get_client(), TurnTrace, get_logger()
|   |-- session_store.py          SessionStore singleton (Tier 2 memory)
|   |-- prompts/
|   |   |-- matteo_v1.txt         Matteo system prompt version 1
|   |   |-- juli_v1.txt           Juli system prompt version 1
|   |   |-- tedd_v1.txt           Tedd system prompt version 1
|   |   `-- matteo_current.txt    Active version (copy of latest)
|   `-- PROMPT_ITERATIONS.md      Prompt change log
|
|-- evaluation/
|   |-- golden/
|   |   `-- matteo_golden.json    20 golden records for Matteo
|   |-- run_golden.py             Golden dataset runner
|   |-- llm_judge.py              LLM-as-judge for coaching quality
|   `-- measure_prompt.py         Token counter per prompt version
|
|-- data/
|   `-- scq.db                    SQLite database (gitignored)
|
|-- .env                          ANTHROPIC_API_KEY (gitignored)
|-- .env.example                  Template (committed)
|-- .gitignore                    .env, data/, __pycache__/
`-- requirements.txt              anthropic, python-dotenv
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
-- Sessions table (one row per agent session per student)
CREATE TABLE agent_sessions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       TEXT    NOT NULL,
    cohort_id     TEXT    NOT NULL,
    agent_id      TEXT    NOT NULL,  -- 'matteo', 'juli', or 'tedd'
    messages      TEXT    NOT NULL DEFAULT '[]',  -- JSON array of turns
    quality_score REAL,
    finalised     INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Users table
CREATE TABLE users (
    id            TEXT    PRIMARY KEY,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'student',  -- student | professor | admin
    cohort_id     TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

---

## Context Window Budget

| Agent | Context limit | System prompt | History | Buffer |
|---|---|---|---|---|
| Matteo | 20,000 tokens | max 3,000 | max 14,000 (35 turns x 200 avg) | 3,000 |
| Juli | 20,000 tokens | max 3,000 | max 14,000 | 3,000 |
| Tedd | 20,000 tokens | max 4,000 (rubric included) | max 12,000 | 4,000 |

History trim order (never trim the system message):
1. Tool result messages (oldest first)
2. Assistant messages (oldest first)
3. User messages (oldest first)

---

## Task Definitions

Matteo:
  Job: Guide students through the SCQ framework using Socratic questioning.
  One turn: student message in, one coaching question out.
  Output: plain text, max 120 words, ends with exactly one question mark.
  Out of scope: scoring, model answers, Juli/Tedd topics.

Juli:
  Job: Guide students through Monroe's Motivated Sequence for recommendations.
  One turn: student draft in, one stage-specific prompt out.
  Output: plain text, max 150 words, ends with [STAGE: Name].
  Out of scope: SCQ review, evaluation, skipping stages.

Tedd:
  Job: Evaluate deliverables against the 5 Cs rubric.
  One turn: deliverable in, scored rubric out (JSON).
  Output: raw JSON with evaluation.{clear,concise,compelling,credible,consistent}.{score,observation}.
  Out of scope: revision coaching, process evaluation, finalised submissions.

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

## Secrets and Environment Variables

All secrets are in .env files, never in source code.

server/.env (never commit):
  JWT_SECRET       32+ character random string for signing JWTs
  JWT_EXPIRY       Token lifetime (default: 8h)
  PORT             Express server port (default: 3001)

.env in project root (never commit):
  ANTHROPIC_API_KEY   Your Anthropic API key

.env.example files (commit these as reference):
  All variable names with placeholder values, no real values.

Verify before every commit:
  grep -rn "sk-ant" agent/ server/src/    must return zero hits
  grep -rn "JWT_SECRET\s*=\s*['\"]" server/src/    must return zero hits

---

## Registered Tools

Tools are registered in agent/tool_registry.py.
After Session 02, tools from Session 01 are in place.
Session 03 will add platform-specific tools (save_scq_draft, get_rubric_config).

| Tool name | What it does | When to use it |
|---|---|---|
| [your Session-01 tool] | [what it does] | [when to call it] |

Every tool name in TOOLS must have a matching entry in TOOL_DISPATCH.
TOOL_DISPATCH is the security allowlist. Unknown tool names are rejected.

---

## Security Non-Negotiables

- JWT verify must use algorithms: ['HS256'] - never omit this
- bcrypt.compare is async only - never compareSync in a route handler
- All DB queries use parameterised statements - never string concatenation
- agent receives user_id from req.user (verified JWT) not from req.body
- Every protected route must apply authMiddleware before any other handler
- Role guards (requireRole) applied to all professor/admin-only routes
- Error handlers return generic message to client - full error logged server-side only

Pre-commit checklist:
  [ ] grep -rn "sk-ant" finds zero hits in source files
  [ ] .env is gitignored and confirmed not tracked
  [ ] All routes that need auth have authMiddleware applied
  [ ] JWT verify call includes algorithms: ['HS256']
  [ ] No bcrypt.compareSync in any route handler

---

## Pre-Commit Gate (Prompt Changes)

Before committing any change to agent/prompts/:
  1. python evaluation/run_golden.py      must be >= 90% pass rate
  2. python evaluation/measure_prompt.py  system prompt must be <= 3,000 tokens
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
python agent/runner.py           # Test the agent directly

# Run evaluation
python evaluation/run_golden.py
```

---

## What Is Not Yet Built (Session 03)

- Full Matteo agent logic with SCQ stage tracking
- Full Juli agent logic with Monroe's stage progression
- Full Tedd agent logic with 5 Cs rubric evaluation
- Platform tools: save_scq_draft, get_rubric_config, get_student_history
- Professor dashboard route: GET /api/professor/sessions
- Session finalisation: PATCH /api/sessions/:id/finalise

Do not implement these until Session 03. They are out of scope for this session.
