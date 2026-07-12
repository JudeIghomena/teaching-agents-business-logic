# Session 03: Building Matteo, Juli, and Tedd

> Session 01 gave you the frameworks. Session 02 gave you the web layer.
> Session 03 is where the three agents come to life with their full coaching logic,
> real tools, and the SCQ platform running end to end.

---

## Where You Are in the Build

By the end of Session 02 you have:
- An Express server with authenticated `/api/agent1/chat`, `/api/agent2/chat`,
  and `/api/agent3/chat` routes
- A database storing conversation history per student per agent
- JWT authentication with role guards for students and professors
- Task definitions for all three agents written into your CLAUDE.md
- A system prompt for Matteo with few-shot examples and a passing evaluation baseline
- A versioned prompt store with at least one iteration cycle completed

Session 03 implements the full coaching logic of each agent on top of that foundation.

---

## What This Session Covers

This session builds the three agents in full. Each agent gets:
- A complete, tested system prompt
- The tools it needs to interact with the platform
- Stage tracking logic (for Matteo and Juli)
- A passing evaluation suite

| Document | What it builds |
|---|---|
| 00-session-overview.md (this file) | Build recap, session scope, what you will have |
| 01-build-matteo.md | Full Matteo implementation: SCQ coaching, stage tracking, tool wiring |
| 02-build-juli.md | Full Juli implementation: Monroe's Sequence, five-stage progression |
| 03-build-tedd.md | Full Tedd implementation: 5 Cs rubric, JSON output, score persistence |
| 04-wire-agents-to-platform.md | Connect all three agents to the web layer from Session 02 |
| 05-test-end-to-end.md | Full platform test: student completes all three stages |

**What you will have at the end of Session 03:**
All three agents running on the platform. A student can start a conversation
with Matteo, progress to Juli, submit to Tedd, and receive a scored rubric.
Every turn is stored in the database. Every agent follows its defined scope.

**Previous session:** [Session 02 - Web Layer and Prompt Engineering](../Session-02%20(Web%20Layer%20and%20Prompt%20Engineering)/00-platform-overview.md)
**Next session:** Session 04 - Security

---

## The Three Agents: Quick Reference

### Matteo - Issue Analysis Coach
Guides students through the SCQ framework using Socratic questioning.
One turn: student message in, one coaching question out.
Output: plain text, max 120 words, ends with exactly one question.
Stage tracking: the web layer injects which SCQ element is being worked on.

### Juli - Monroe's Motivated Sequence Coach
Guides students through building a persuasive recommendation in five stages.
One turn: student draft in, one stage-specific prompt out.
Output: plain text, max 150 words, ends with [STAGE: StageName].
Stage tracking: the web layer reads the stage tag and updates the session record.

### Tedd - 5 Cs Peer Review Evaluator
Evaluates deliverables against the 5 Cs rubric.
One turn: completed deliverable in, scored rubric out as JSON.
Output: raw JSON with score (1-5) and observation per C.
No stage tracking: Tedd evaluates once per submitted deliverable.

---

## What Each Agent Needs That Was Not in Session 02

Session 02 built Matteo's prompt skeleton and ran one iteration cycle.
Session 03 completes what was deferred:

**Matteo needs:**
- save_scq_draft tool: saves the student's current SCQ elements to the database
- get_student_progress tool: reads which SCQ elements have been confirmed
- Stage-aware prompt injection: the web layer adds the current SCQ state to context

**Juli needs:**
- Full five-section system prompt with Monroe's Sequence stage definitions
- Stage progression logic: the web layer tracks which stage is active
- get_stage_context tool: reads the student's completed Matteo work as starting context

**Tedd needs:**
- Full 5 Cs system prompt with rubric definitions
- get_rubric_config tool: reads the rubric from a config file (not hardcoded in the prompt)
- save_evaluation tool: writes the scored rubric to the database

All three tools per agent follow the pattern from Framework 06: schema in TOOLS,
implementation function, registration in TOOL_DISPATCH.

---

## Before You Start

Confirm these are all true before opening the first document:

- [ ] `node server/src/index.js` starts without errors
- [ ] A curl request with a valid JWT reaches the Matteo route and returns SSE tokens
- [ ] `python evaluation/run_golden.py` passes at 90% or above for Matteo
- [ ] Your CLAUDE.md has Task Definitions for all three agents
- [ ] `data/scq.db` exists and has both the agent_sessions and users tables

If any of these are not true, complete the relevant Session 02 assignment first.

---

## Start Here

[Build 01: Building Matteo](01-build-matteo.md)

---

Copyright Janna AI Research Labs
