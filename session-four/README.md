# Session Four: Security

> You now have a working agent that handles real business logic, real tools,
> and real data. Session Four attacks it systematically and teaches you to
> defend it. Security studied on something real lands completely differently
> from security studied on an abstract example.

**Status: Coming after Session Three**

---

## Why Security Gets Its Own Session Here

Session One's document 11 covers the security baseline: the minimum controls
every agent needs before it runs. That is enough to get started safely.

Session Four goes much further, and placing it here is deliberate. After three
sessions of building, you have a concrete agent to model threats against. You
know what data flows through it. You know which tools have write access. You
know what a user can send and what the model might do with it. Every attack
pattern in Session Four will map directly to something you have already built.

Agent systems have an attack surface that does not exist in traditional software:
a reasoning process that operates on natural language and can be manipulated
through it. SQL injection targets your database. Prompt injection targets your
model. Both are real. Both need dedicated countermeasures.

---

## Planned Documents

```
session-four/
│
├── 01-agent-threat-model.md
│     The complete attack surface map for an AI agent.
│     Traditional threats (SQLi, auth bypass, IDOR) plus agent-specific
│     threats (prompt injection, tool abuse, context poisoning, jailbreaking).
│     How to draw a threat model for your specific agent.
│
├── 02-prompt-injection-deep-dive.md
│     The most important agent-specific attack, in full detail.
│     Direct injection (user manipulates the model in their turn).
│     Indirect injection (malicious content in retrieved data poisons context).
│     Real attack examples. Defence at every layer.
│
├── 03-tool-security.md
│     Tool abuse, over-privileged tool registries, and insecure implementations.
│     Principle of least privilege for tool registries.
│     Input validation at the dispatcher level.
│     Read-only vs write tool separation pattern.
│
├── 04-authentication-and-authorisation.md
│     Who is allowed to talk to your agent and what are they allowed to ask?
│     API key and JWT patterns for agent endpoints.
│     Role-based tool access: not all users get all tools.
│
├── 05-data-handling-and-privacy.md
│     What data flows through an agent and where it goes.
│     PII in context: what to redact, what to tokenise, what never enters context.
│     What gets logged, what must not.
│
├── 06-output-security.md
│     What the agent returns can be as dangerous as what it receives.
│     Sanitising model output before it reaches the user or downstream systems.
│     Safe rendering: why agent output must never be injected into innerHTML raw.
│
├── 07-secrets-and-credential-management.md
│     Where secrets live in an agent system and how they are accessed.
│     Secret rotation without downtime. What to do when a key is leaked.
│
├── 08-rate-limiting-and-abuse-prevention.md
│     Protecting your agent endpoint and your API spend from abuse.
│     Per-user, per-session, and per-endpoint rate limits.
│     Cost ceilings: hard stops when spend exceeds threshold.
│
├── 09-security-testing-for-agents.md
│     How to test an agent's security posture before deploying.
│     Adversarial prompt test suites: a library of injection attempts.
│     Tool abuse test cases: inputs designed to trigger unintended tool calls.
│     Running security tests as part of CI before every deployment.
│
├── 10-incident-response.md
│     What to do when something goes wrong.
│     Key exposure playbook: rotate immediately, audit, notify.
│     Prompt injection confirmed: triage, contain, patch.
│     Runaway agent: kill switch design.
│
└── starter-code/
      adversarial-prompt-suite.py   100 injection test cases, runnable
      sanitiser.py                  Production output sanitiser with tests
      rate_limiter.py               Per-user rate limiter, drop-in module
      auth_middleware.py            JWT validation for agent API endpoints
      secrets_loader.py             Safe secret loading with rotation support
```

---

## How This Session Relates to Others

| Session | Security angle covered |
|---|---|
| Session One | Security baseline (doc 11): minimum controls before first run |
| Session Two | Secure prompt design: output format control, evaluation for edge cases |
| Session Three | Secure business logic: input validation, decision audit trails |
| Session Four | Full security deep-dive: threat model, attack patterns, hardening, testing |
| Session Five | Multi-agent trust: privilege separation across agents |
| Session Six | Production security: monitoring, alerting, incident response at scale |

---

## Prerequisites

Complete Sessions One through Three before starting Session Four. Specifically,
have a working business-logic agent from Session Three. Session Four will build
the threat model for that agent directly. The more concrete your agent, the more
the attack patterns here will make immediate sense.

---

Copyright Janna AI Research Labs
