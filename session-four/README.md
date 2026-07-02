# Session Four — Multi-Agent Systems

> One agent can reason. A team of agents can coordinate, specialise, check each
> other's work, and handle workflows too large for a single context window.
> Session Four covers how to design and orchestrate agent teams.

**Status: Coming after Session Three**

---

## What This Session Covers

Session Four moves from single-agent to multi-agent architecture. The patterns
here are used in production systems where tasks are too complex, too long, or
too sensitive to trust to a single agent turn.

---

## Planned Documents

```
session-four/
├── 01-multi-agent-mental-model.md
│     How multiple agents communicate, what an orchestrator does,
│     and when multi-agent is the right choice vs single-agent.
│
├── 02-orchestrator-pattern.md
│     The orchestrator receives a task, delegates sub-tasks to specialist
│     agents, collects results, and synthesises a final output.
│     Full implementation with the Anthropic Agent SDK.
│
├── 03-specialist-agents.md
│     Designing agents with narrow, deep capability.
│     Why specialists outperform generalists on scoped tasks.
│     Example: a team of research, analysis, and writing agents.
│
├── 04-human-in-the-loop.md
│     When to pause the agent loop and ask a human for approval.
│     HITL state machine, approval request format, resume pattern.
│     Example: financial approval workflow with HITL gate.
│
├── 05-agent-to-agent-trust.md
│     What one agent should and should not trust from another.
│     Validation between agents, signed outputs, scope containment.
│
├── 06-parallel-agent-execution.md
│     Running multiple agents concurrently for speed.
│     Fan-out and fan-in patterns. Handling partial failures.
│
└── starter-code/
      Orchestrator + two specialist agents, fully wired.
      HITL approval workflow with state machine.
```

---

## Prerequisites

Complete Sessions One through Three.
Multi-agent systems are built from single agents. You must be able to design,
prompt, and evaluate a single agent reliably before coordinating multiple.

---

Copyright Janna AI Research Labs
