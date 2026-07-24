# Session Five: Agent Coordination

> The three agents work. They are secure. Now the question is: how do they work
> together? Session 05 builds the layer that coordinates Matteo, Juli, and Tedd
> as a system rather than three independent endpoints.

---

## Framework Mapping

Session 05 applies Framework 01 (Agent Mental Model) at the system level: the
orchestrator reasons about which agent to use so that no individual agent needs
to reason about the others. Each document connects to a second framework that
explains which layer the coordination concern belongs to.

| Session-05 Document | Applies These Frameworks |
|---|---|
| 00-session-overview.md | Read first. Build recap, the coordination problem, what you will have. |
| 01-design-the-handoff.md | Framework 01 (Agent Mental Model) + Framework 09 (Memory and State) |
| 02-build-the-orchestrator.md | Framework 01 (Agent Mental Model) + Framework 02 (Project Structure) |
| 03-manage-cross-agent-context.md | Framework 09 (Memory and State) + Framework 04 (Context Window Budget) |
| 04-test-agent-coordination.md | Framework 10 (Observability) + Framework 08 (Internal Setup) |
| 05-handle-agent-failures.md | Framework 11 (Security Baseline) + Framework 01 (Agent Mental Model) |

---

## Documents in This Session

```
Session-05 (Agent Coordination)/
|
|-- 00-session-overview.md
|       Read this first. The coordination problem, the orchestrator pattern,
|       what Session 04 left in place, and what you will have when done.
|
|-- 01-design-the-handoff.md
|       Framework 01 + 09. What triggers a stage transition. What data must
|       pass between agents. The four-state student journey (MATTEO, JULI,
|       TEDD, COMPLETE). The stageManager module: getCurrentStage and
|       isStageComplete derived from the existing agent_sessions table.
|
|-- 02-build-the-orchestrator.md
|       Framework 01 + 02. The single POST /api/chat endpoint that replaces
|       the three individual agent routes for student-facing requests. How
|       the orchestrator reads stage, selects the right agent, loads context,
|       calls the agent, streams the response, and advances stage on completion.
|
|-- 03-manage-cross-agent-context.md
|       Framework 09 + 04. The cross-agent context schema: what Juli needs
|       from Matteo and how the orchestrator retrieves and injects it. Context
|       budget accounting for the added orchestrator overhead. What each agent
|       can read and what only the orchestrator can write.
|
|-- 04-test-agent-coordination.md
|       Framework 10 + 08. Four routing test scenarios: new student at MATTEO,
|       complete SCQ routes to JULI, complete Monroe routes to TEDD, COMPLETE
|       state returns the right message. Extended TurnTrace with stage_before,
|       agent_selected, and stage_after fields. Vitest orchestrator test suite.
|
|-- 05-handle-agent-failures.md
|       Framework 11 + 01. What can fail and what the student sees. Retry
|       budget for 529 errors. Partial response handling when a stream breaks
|       mid-response. HITL hook: flagging low-scoring Tedd evaluations for
|       professor review. Error logging with stage and retry count.
|
|-- assignments/
|   |-- 01-design-the-handoff.md
|   |-- 02-build-the-orchestrator.md
|   |-- 03-manage-cross-agent-context.md
|   |-- 04-test-agent-coordination.md
|   |-- 05-handle-agent-failures.md
|   `-- README.md
|
`-- starter-code/
    |-- CLAUDE.md          Cumulative operating brief for end of Session 05
    |-- .env.example       Environment variables including HITL threshold
    |-- package.json       Version 0.5.0, no new dependencies
    `-- requirements.txt   Python dependencies unchanged from Session 04
```

---

## What You Will Have at the End

- A single `POST /api/chat` endpoint that routes to Matteo, Juli, or Tedd
  based on the student's current stage, automatically
- Cross-agent context injected by the orchestrator: Juli receives Matteo's
  confirmed SCQ without the student needing to repeat it
- Stage progression managed centrally by the orchestrator, derived from the
  existing agent_sessions table with no schema changes
- An orchestrator test suite covering all four routing states
- Failure handling: retry on 529, clean error on exhaustion, HITL flag for
  Tedd evaluations below the professor review threshold
- Extended TurnTrace logging that records which agent was selected and why

---

## How This Session Relates to Others

| Session | Coordination angle covered |
|---|---|
| Session 01 | Framework 01: the five-layer model that individual agents run on |
| Session 02 | Three separate agent routes: the starting point this session replaces |
| Session 03 | Stage injection per-route: the pattern the orchestrator centralises |
| Session 04 | Security hardening: rate limiting and validation carry forward unchanged |
| Session 05 | Orchestration layer: one endpoint, shared context, failure handling |
| Session 06 | Production: HTTPS, monitoring, cost per student session |

---

Copyright Janna AI Research Labs
