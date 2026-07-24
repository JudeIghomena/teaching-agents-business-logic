# Build 05: Final Platform Review

**Frameworks applied:** All eleven frameworks reviewed at production scale

---

## What Was Built

Six sessions. Six layers. One platform.

This document is the final review of the SCQ Simulation Portal. It exists
for two reasons: to help you understand what you built and why it works, and
to confirm that every architectural rule from every session is still in place
before the platform goes to real students.

---

## The Six-Session Arc

| Session | Layer added | Core decision |
|---|---|---|
| 01 | Agent foundations | Five-layer architecture. Eleven frameworks as a mental model. |
| 02 | Web layer | Express + JWT + SQLite. Matteo prompt engineered and evaluated. |
| 03 | Three agents | Matteo, Juli, Tedd. Tool registry. SSE streaming from Python. |
| 04 | Security | Rate limiting. Input validation. IDOR prevention. Security tests. |
| 05 | Coordination | Orchestrator. Stage state machine. Cross-agent context. HITL. |
| 06 | Production | Health check. Railway deploy. Token monitoring. Cost controls. |

Nothing from Session 01 was thrown away. The five-layer architecture that
Matteo runs on is the same architecture the orchestrator uses to manage
all three agents. The TurnTrace from Session 01 now carries twelve fields
in production. The security baseline from Session 01 became the full security
hardening of Session 04.

---

## The Eleven Frameworks in the Final Platform

| Framework | Where it lives in the final platform |
|---|---|
| 01 Agent Mental Model | stageManager.js, orchestrator.js: the orchestrator reasons about which agent to use |
| 02 Project Structure | Folder layout: server/src/ owns HTTP, agent/ owns reasoning, evaluation/ owns quality |
| 03 Model Selection | model_config.py: model per agent, never hardcoded in routes |
| 04 Context Window Budget | Context budget table in CLAUDE.md, MAX_SCQ_FIELD_LENGTH, TOKEN_BUDGET_PER_USER |
| 05 Environment Config | .env.example with every variable annotated, CORS startup guard in production |
| 06 Tool Design | TOOL_DISPATCH allowlist: save_scq_draft, get_student_progress, get_rubric_config, save_evaluation |
| 07 System Prompt Skeleton | matteo_v1.txt, juli_v1.txt, tedd_v1.txt with task/scope/output/rules/tools sections |
| 08 Internal Setup | buildApp() / app.listen separation, initTestDb / teardownTestDb, Railway Volume |
| 09 Memory and State | agent_sessions table: messages JSON, quality_score, finalised, needs_review |
| 10 Observability | TurnTrace with 12 fields, errorTracker, /api/health with last_5min stats |
| 11 Security Baseline | JWT HS256, bcrypt async cost 12, parameterised queries, authMiddleware, role guards |

---

## The Final Audit

Before deploying to students, verify every item in this list:

### Security
- [ ] JWT verify calls include `{ algorithms: ['HS256'] }` on every call
- [ ] No bcrypt.compareSync in any route handler
- [ ] All agent_sessions queries include `AND user_id = ?` or `AND cohort_id = ?`
- [ ] authMiddleware applied to all agent, professor, and cost routes
- [ ] Rate limiting on auth endpoint (authLimiter) and agent endpoint (agentLimiter)
- [ ] Input validation on all agent routes (validateAgentMessage / validateTeddMessage)
- [ ] CORS_ORIGIN set to the production frontend URL, not localhost
- [ ] JWT_SECRET is a 64-character random hex string, not a development default
- [ ] No API key or secret in source code (grep -rE "sk-ant" finds zero hits)
- [ ] npm audit returns zero high or critical vulnerabilities

### Tests
- [ ] cd server && npm test passes with zero failures (minimum 15 tests)
- [ ] Security test suite: auth (5), role guards (2), IDOR (1+)
- [ ] Orchestrator tests: routing (5), context (2)

### Agents
- [ ] All three agent evaluation suites pass at 90% or above
- [ ] Matteo system prompt token count <= 3,000 (measure_prompt.py)
- [ ] Juli system prompt token count <= 3,000 (measure_prompt.py)
- [ ] Tedd system prompt token count <= 4,000 (measure_prompt.py)
- [ ] PROMPT_ITERATIONS.md has an entry for every prompt commit

### Production
- [ ] GET /api/health returns { status: 'ok', db: 'ok' }
- [ ] Railway Volume mounted at /data and DB_PATH=/data/scq.db is set
- [ ] Database initialised on the volume: npm run db:init
- [ ] Python requirements.txt at project root installs correctly
- [ ] Turn_complete logs appearing in Railway logs after a student message
- [ ] Token budget check active: TOKEN_BUDGET_PER_USER set in production
- [ ] Prompt caching active: system prompt blocks have cache_control set

---

## What the CLAUDE.md Captures

The starter-code/CLAUDE.md in this session is the definitive operating brief
for the SCQ Simulation Portal. Any developer or coding agent starting a new
session on this platform reads it and has a complete picture of:

- Why each architectural decision was made
- Every rule that must not be broken
- The exact schema, routes, tools, and prompt structure
- The security non-negotiables and pre-commit checklist
- How to start, test, deploy, and monitor the platform

The CLAUDE.md is living documentation. Every significant change to the
platform must be reflected in it before the session ends. The rule is the
same as it has been since Session 01: the CLAUDE.md must describe the
platform as it is, not as it was when the session started.

---

## What Comes After Session 06

The platform is production-ready for a single cohort. The decisions made in
these six sessions were deliberate:

SQLite was chosen because it is sufficient for 60 students and zero devops
overhead. When cohorts grow beyond a single server, swap to PostgreSQL: the
schema does not change, only the driver and connection string.

Express was chosen because it is familiar to most developers. When the
platform needs horizontal scaling, add a load balancer in front and move
session state out of the database (it already is).

Python agents were chosen because the Anthropic Python SDK is the most
complete and the tool_use implementation is well-documented. The protocol
between Express and Python (JSON over stdin, SSE over stdout) is stable and
well-tested. Adding a fourth agent means adding a fourth Python file, a
fourth route, and a fourth entry in the orchestrator's stage machine.

What you built is a foundation. The coaching content can be swapped for any
domain. The three-agent pattern can be extended to any number of agents.
The security layer, the evaluation infrastructure, and the orchestration
logic are production-quality and do not need to change.

---

## Using Claude Code Desktop App

The final use of Claude Code in this course is to generate the project
documentation that a real development team would maintain.

**Prompt to generate HANDOFF.md:**

```
Read the CLAUDE.md in starter-code/ and the full git log for this project.
Generate a HANDOFF.md at the project root covering:

1. Project Purpose - what the SCQ Simulation Portal is, who it is for, why it exists
2. Architecture - the complete stack with a data flow description
3. Implementation Timeline - the six sessions as chronological milestones
4. Current State - what works, what the known limitations are, what is deferred
5. Next Steps - three to five concrete engineering priorities if the platform continues
6. Environment Variables - every variable from .env.example with a one-line description
   (no actual values, just descriptions)
7. Key Files Reference - a table of the 20 most important files with one-line purposes

Write in plain prose. No markdown bold. No em dashes. One sentence per point
in the next steps list. This document will be read by a developer who has
never seen this codebase.
```

**What Claude Code will do:**
Read the CLAUDE.md and git history, then generate a HANDOFF.md that covers
the full six-session platform. Review it for accuracy before committing it.

**Tips for this document:**
- Read the generated HANDOFF.md before committing it. Claude Code will
  write what it can infer from the codebase; you must verify that the
  "Current State" section accurately reflects what is working in production,
  not just what is in the code.
- The HANDOFF.md should not duplicate CLAUDE.md. CLAUDE.md is for coding
  agents. HANDOFF.md is for human developers. CLAUDE.md has rules;
  HANDOFF.md has context.
- The final CLAUDE.md lives in starter-code/CLAUDE.md. The HANDOFF.md
  lives at the project root. Commit both.

---

**Next session:** This is the final session. The SCQ Simulation Portal is complete.

---

Copyright Janna AI Research Labs
