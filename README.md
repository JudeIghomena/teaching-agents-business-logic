# Business Case Logic with AI Coding Agents

A practical course on building AI agents that do real work — not demos,
not chatbots, not toys. Agents that make decisions, enforce business rules,
coordinate workflows, and run in production.

Maintained by Jude Ighomena / Janna AI Research Labs.

---

## What This Course Is

Most AI agent tutorials teach you how to call an API and print a response.
This course teaches you how to build an agent you would trust with your business.

There is a wide gap between a working demo and a production agent. The demo
runs on your laptop with one happy-path input. The production agent handles
thousands of users, enforces role-based permissions, validates every tool call,
logs every decision, resists manipulation through natural language, and recovers
gracefully when things go wrong.

This course covers that gap — from the first line of setup code to a deployed,
monitored, and secured multi-agent system.

---

## Who It Is For

Developers who know how to code and want to build AI agents that are actually
fit for production. You do not need prior experience with AI or the Anthropic SDK.
You do need to be comfortable reading and writing Python.

It is also designed for teams building agent-powered products on top of platforms
like Janna AI Research Labs — where agents handle business logic, approvals,
data workflows, and customer-facing decisions at scale.

---

## What You Will Be Able to Do

By the end of this course you will be able to:

- Design the full internal setup of an agent before writing a single prompt
- Choose the right model for the task and budget your context window deliberately
- Build tool registries that are secure, typed, and dispatcher-controlled
- Write system prompts with clear role, scope, rules, format, and escalation
- Understand and defend against every agent-specific attack surface
- Implement real business logic: approvals, pricing, routing, data validation
- Design and orchestrate multi-agent systems with human-in-the-loop controls
- Deploy, monitor, and manage costs for a production agent system

---

## How the Course Is Structured

Six sessions, each building on the last. Read them in order.

Every session contains explanation documents and starter code you can run
and customise immediately. The documents explain the why. The starter code
is the how — working Python you copy into your own project.

**Session One — Frameworks**
The internal foundation every agent is built on. Covers the 5-layer agent
model, project structure, model selection, environment setup, context budgeting,
tool design, system prompt anatomy, memory tiers, observability, and the
minimum security baseline.

**Session Two — Security**
A dedicated session on agent security — the one topic most courses treat as
an afterthought. Covers the full agent threat model, prompt injection attacks
and defences, tool permission scoping, authentication, data privacy, output
sanitisation, secrets management, abuse prevention, adversarial testing,
and incident response.

**Session Three — Task Design, Prompt Engineering, and Evaluation**
How to define what the agent should do, write prompts that do it consistently,
and build evaluation methods that tell you whether it is working.

**Session Four — Business Case Logic**
Concrete implementations of the most common agent-driven business patterns:
approval workflows, pricing engines, routing and triage, document extraction,
and decision audit trails. Every document includes runnable code.

**Session Five — Multi-Agent Systems**
Orchestrators, specialist agents, human-in-the-loop gates, agent-to-agent trust,
and parallel execution. How to coordinate a team of agents on tasks too complex
for a single agent turn.

**Session Six — Production**
Deployment patterns, cost management, rate limiting, production error handling,
prompt versioning, and monitoring. Everything that only matters once real users
and real money are involved.

---

## The Underlying Principle

An agent is only as good as the infrastructure it runs on.
Most developers write the prompt first. This course teaches you to build everything
else first — and write the prompt last.

---

Copyright Janna AI Research Labs
