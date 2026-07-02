# Session Two: Security

> Security for AI agents is not a feature you add at the end.
> It is a discipline you apply from the first line of code.
> This session gives it the dedicated treatment it deserves.

**Status: Coming next**

---

## Why Security Gets Its Own Session

Session One's document 11 covers the security baseline, the minimum controls
every agent needs before it runs. This session goes much further.

Agent systems have an attack surface that does not exist in traditional software:
a reasoning process that operates on natural language and can be manipulated
through it. SQL injection targets your database. Prompt injection targets your
model. Both are real. Both need dedicated countermeasures.

This session is standalone because security is not a topic you visit once.
It is a discipline that applies to every session that follows. Study this
session before you build business logic, multi-agent systems, or production
deployments. The patterns here will show up again in every one of them.

---

## Planned Documents

```
session-two/
│
├── 01-agent-threat-model.md
│     The complete attack surface map for an AI agent.
│     Traditional threats (SQLi, auth bypass, IDOR) plus agent-specific
│     threats (prompt injection, tool abuse, context poisoning, jailbreaking).
│     How to draw a threat model for your specific agent before building it.
│
├── 02-prompt-injection-deep-dive.md
│     The most important agent-specific attack, in full detail.
│     Direct injection (user manipulates the model in their turn).
│     Indirect injection (malicious content in retrieved data poisons context).
│     Real attack examples. Defence at every layer: system message, input
│     validation, output inspection, architecture-level separation.
│
├── 03-tool-security.md
│     Tool abuse, over-privileged tool registries, and insecure implementations.
│     Principle of least privilege for tool registries.
│     Input validation at the dispatcher level.
│     Preventing tool calls from executing shell commands, file reads outside
│     allowed paths, or unbounded DB queries.
│     Read-only vs write tool separation pattern.
│
├── 04-authentication-and-authorisation.md
│     Who is allowed to talk to your agent, and what are they allowed to ask it to do?
│     API key and JWT patterns for agent endpoints.
│     Role-based tool access, not all users get all tools.
│     Session validation: verifying identity before every high-stakes tool call.
│
├── 05-data-handling-and-privacy.md
│     What data flows through an agent and where it goes.
│     PII in context: what to redact, what to tokenise, what never enters context.
│     Tool results containing sensitive fields: partial return patterns.
│     What gets logged, what must not. GDPR and data residency considerations
│     for agent systems.
│
├── 06-output-security.md
│     What the agent returns can be as dangerous as what it receives.
│     Sanitising model output before it reaches the user or downstream systems.
│     Preventing the model from echoing internal system details.
│     Content injection via model output: when agent responses become attack vectors.
│     Safe rendering: why agent output must never be injected into innerHTML raw.
│
├── 07-secrets-and-credential-management.md
│     Where secrets live in an agent system and how they are accessed.
│     The right way: runtime env vars, secrets managers (AWS Secrets Manager,
│     HashiCorp Vault, Railway secrets).
│     The wrong way: hardcoded, committed, logged, or echoed in responses.
│     Secret rotation without downtime. What to do when a key is leaked.
│
├── 08-rate-limiting-and-abuse-prevention.md
│     Protecting your agent endpoint and your API spend from abuse.
│     Per-user, per-session, and per-endpoint rate limits.
│     Cost ceilings: hard stops when spend exceeds threshold.
│     Detecting and blocking prompt injection attempts at the API gateway layer.
│     Bot detection patterns for public-facing agent endpoints.
│
├── 09-security-testing-for-agents.md
│     How to test an agent's security posture before deploying.
│     Adversarial prompt test suites: a library of injection attempts.
│     Tool abuse test cases: inputs designed to trigger unintended tool calls.
│     Auth bypass tests. IDOR probes for multi-user agent systems.
│     Running security tests as part of CI before every deployment.
│
├── 10-incident-response.md
│     What to do when something goes wrong.
│     Key exposure playbook: rotate immediately, audit, notify.
│     Prompt injection confirmed: triage, contain, patch.
│     Runaway agent (unexpected tool calls, cost spike): kill switch design.
│     How to write a post-incident review for an agent security event.
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

Every other session touches security, but from the angle of making a feature
work. This session focuses entirely on making the system resistant to failure
and attack. The two perspectives are complementary.

| Session | Security angle covered |
|---|---|
| Session One | Security baseline (doc 11), the minimum controls |
| Session Two | Deep-dive security, threat model, attack patterns, testing |
| Session Three | Secure business logic, input validation, audit trails |
| Session Four | Multi-agent trust, what agents should and should not trust from each other |
| Session Five | Multi-agent security boundaries, privilege separation across agents |
| Session Six | Production security, monitoring, alerting, incident response at scale |

---

## Prerequisites

Complete Session One before starting Session Two.
Specifically, the starter-code agent should be running with your own tools
and system message. Session Two will attack that running agent, you need
something to attack before you can learn to defend it.

---

Copyright Janna AI Research Labs
