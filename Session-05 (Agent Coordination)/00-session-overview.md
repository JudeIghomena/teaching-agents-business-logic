# Session 05: Multi-Agent Coordination

> The three agents work. They are secure. Now the question is: how do they work
> together? Session 05 builds the layer that coordinates Matteo, Juli, and Tedd
> as a system, not just as three independent endpoints.

---

## Where You Are in the Build

By the end of Session 04 you have:
- All three agents running, hardened, and tested
- Rate limiting on all endpoints
- Input validation before any message reaches an agent
- IDOR prevention on all database queries
- A passing security test suite
- A completed platform security audit

The agents work individually. Session 05 builds the coordination layer that
manages how a student moves from Matteo to Juli to Tedd, what state is shared
between them, and what happens when an agent fails mid-session.

---

## What This Session Covers

Session 05 applies Framework 01 (Agent Mental Model) at the system level.
Individual agents have boundaries. A multi-agent system needs an orchestration
layer that respects those boundaries while managing the transitions between them.

| Document | What it builds |
|---|---|
| 00-session-overview.md (this file) | Build recap, session scope, what you will have |
| 01-design-the-handoff.md | What data passes between agents and when handoff triggers |
| 02-build-the-orchestrator.md | The orchestration route that routes messages to the right agent |
| 03-manage-cross-agent-context.md | Shared state all three agents can read but do not own |
| 04-test-agent-coordination.md | End-to-end test of a student moving through all three stages |
| 05-handle-agent-failures.md | Fallback and retry logic when an agent fails mid-session |

**What you will have at the end of Session 05:**
A single `/api/chat` endpoint that routes automatically to the correct agent
based on the student's current stage. Shared context (completed SCQ, current
Monroe's stage, prior rubric scores) injected into each agent from a central
state store. A student's full journey from Matteo to Tedd managed without
them knowing which agent they are talking to at any point.

**Previous session:** [Session 04 - Security](../Session-04%20(Security)/00-session-overview.md)
**Next session:** Session 06 - Production

---

## The Coordination Problem

Right now, a student must call the correct endpoint themselves: `/api/agent1/chat`
for Matteo, `/api/agent2/chat` for Juli, `/api/agent3/chat` for Tedd.

The platform should manage this. The student sends a message. The platform
decides which agent should respond based on where the student is in their journey.
The student does not need to know about Matteo, Juli, or Tedd at all.

This requires three things the platform does not yet have:

**1. Stage tracking at the platform level**
Which agent is this student currently working with? When is a stage considered
complete? Who decides that Matteo is done and Juli should take over?

**2. Context handoff**
When Juli starts, she needs to know what the student built with Matteo. When
Tedd evaluates, he needs the student's final deliverable. This context lives
in the database but must be formatted correctly for each agent that needs it.

**3. Failure handling**
If Matteo's agent call fails mid-stream (API timeout, model error), what does
the student see? Does the platform retry? Does it fall back to a simpler response?
Does it save the partial response?

Session 05 answers all three.

---

## The Orchestrator Pattern

The orchestrator is not a new agent. It is an Express route that:

1. Reads the student's current stage from the database
2. Selects the appropriate agent (Matteo, Juli, or Tedd)
3. Loads the relevant context for that agent
4. Calls the agent and streams the response
5. After the response, checks whether the stage is now complete
6. If complete, advances the student to the next stage

The agents themselves do not change. They still receive a message, a history,
and a system prompt. They still return a response. The orchestrator wraps them.

This is Framework 01 applied at the system level: the orchestrator reasons
about which agent to use. The agents reason about their specific task.
They do not overlap.

---

## What Changes in the CLAUDE.md

Session 05 adds to your CLAUDE.md:
- Orchestrator route: `POST /api/chat` replaces the three individual agent routes
  for student-facing requests (professor routes remain separate)
- Stage progression rules: what triggers advancement from Matteo to Juli to Tedd
- Cross-agent context schema: what the shared state store holds and who can write to it
- Failure handling rules: retry budget, fallback behaviour, partial response handling

---

## Before You Start

Confirm these are all true before opening the first document:

- [ ] All three agents pass their evaluation suites
- [ ] The security test suite passes with zero failures
- [ ] A manual end-to-end test (student through all three stages) works correctly
- [ ] SECURITY.md exists and reflects the current platform security posture
- [ ] Your CLAUDE.md has up-to-date task definitions for all three agents

---

## Start Here

[Build 01: Design the Handoff](01-design-the-handoff.md)

---

Copyright Janna AI Research Labs
