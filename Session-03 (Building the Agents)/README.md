# Session 03: Building Matteo, Juli, and Tedd

> Session 01 gave you the frameworks. Session 02 gave you the web layer.
> Session 03 is where the three agents come to life with their full coaching logic,
> real tools, and the SCQ platform running end to end.

**Session goal:** By the end of this session, a student can open a browser,
send a message to Matteo, receive Socratic coaching, progress to Juli for
recommendation structuring, submit their deliverable to Tedd, and receive
a scored 5 Cs rubric. Every turn is stored. Every agent follows its defined scope.

---

## How This Session Connects to Session 01

Every document in this session applies at least one of the eleven Session 01
frameworks to the live platform. The frameworks are not repeated here for study.
They are applied here for the first time under real conditions.

| Document | Framework applied | How it applies |
|---|---|---|
| 01-build-matteo.md | Framework 06 (Tool Design and Schema) + Framework 07 (System Prompt Skeleton) | Adds SCQ-specific tools to Matteo and completes the five-section system prompt |
| 02-build-juli.md | Framework 07 (System Prompt Skeleton) + Framework 04 (Context Window Budget) | Builds Juli's full prompt with stage definitions and manages context across a five-stage coaching session |
| 03-build-tedd.md | Framework 07 (System Prompt Skeleton) + Framework 09 (Memory Architecture and Tiers) | Builds Tedd's rubric prompt and writes evaluation results to the Tier 3 database |
| 04-wire-agents-to-platform.md | Framework 02 (Five-Layer Architecture) + Framework 05 (Infrastructure as Foundation) | Connects all three agents to the Express layer and adds professor-facing routes |
| 05-test-end-to-end.md | Framework 08 (The Agent Loop) + Framework 10 (Observability) | Traces a full student journey across all three agents and reads the turn-by-turn log |

---

## Document Tree

```
Session-03 (Business Case Logic)/
|
|-- README.md                         This file
|-- 00-session-overview.md            Build recap, full session scope, agent quick reference
|
|-- 01-build-matteo.md                SCQ tools, stage injection, complete system prompt
|-- 02-build-juli.md                  Monroe's Sequence prompt, five-stage progression logic
|-- 03-build-tedd.md                  5 Cs rubric prompt, evaluation tool, DB persistence
|-- 04-wire-agents-to-platform.md     Full web layer integration for all three agents
|-- 05-test-end-to-end.md             Student journey test, observability trace, load check
|
|-- assignments/
|   |-- README.md                     Assignment index
|   |-- 01-build-matteo.md            Add SCQ tools and complete Matteo's system prompt
|   |-- 02-build-juli.md              Build Juli's five-stage coaching system
|   |-- 03-build-tedd.md              Build Tedd's rubric evaluator
|   |-- 04-wire-agents-to-platform.md Connect all three agents and add professor routes
|   `-- 05-test-end-to-end.md         Run the full student journey and read the trace
|
`-- starter-code/
    |-- CLAUDE.md                     Cumulative operating brief (end of Session 03)
    |-- .env.example                  Environment variable reference
    |-- package.json                  Node dependencies
    `-- requirements.txt              Python dependencies
```

---

## The CLAUDE.md at the End of This Session

After Session 03, your CLAUDE.md gains three new sections:

**Registered Tools** is now fully populated. Each agent has its own tools listed
with name, purpose, and which agent owns it. TOOL_DISPATCH is the security allowlist.

**Stage Progression** describes how the web layer tracks where a student is in
each coaching sequence. Matteo tracks which SCQ element is active. Juli tracks
which Monroe's stage is active. Tedd has no stages.

**Student Journey** maps the full flow from first Matteo message to final Tedd
evaluation. This section exists to orient any future coding agent session to the
product it is working on.

The starter-code/CLAUDE.md in this folder is the complete version you should
have at the end of Session 03. Use it as the reference for what your own file
should contain.

---

## Reading Order

Work through the documents in number order. Each document builds on the previous
one. Complete the matching assignment before moving to the next document.

Start here: [00-session-overview.md](00-session-overview.md)

---

Copyright Janna AI Research Labs
