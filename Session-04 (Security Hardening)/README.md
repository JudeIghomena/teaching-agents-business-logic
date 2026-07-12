# Session Four: Security Hardening

> You now have three working agents on a real platform. Session Four attacks
> that platform systematically and teaches you to defend it. Security studied
> against something you built yourself lands completely differently from
> security studied on an abstract example.

---

## Framework Mapping

Every document in this session applies Framework 11 (Security Baseline) from
Session One at full depth. Each document also connects to a second framework
that explains why the defence belongs in that layer.

| Session-04 Document | Applies These Frameworks |
|---|---|
| 00-session-overview.md | Read first. Build recap, session scope, prerequisites. |
| 01-add-rate-limiting.md | Framework 11 (Security Baseline) + Framework 05 (Environment Config) |
| 02-validate-all-inputs.md | Framework 11 (Security Baseline) + Framework 06 (Tool Design) |
| 03-prevent-idor.md | Framework 11 (Security Baseline) + Framework 09 (Memory and State) |
| 04-write-security-tests.md | Framework 11 (Security Baseline) + Framework 10 (Observability) |
| 05-run-the-security-audit.md | Framework 11 (Security Baseline) + Framework 02 (Project Structure) |

---

## Documents in This Session

```
Session-04 (Security Hardening)/
|
|-- 00-session-overview.md
|       Read this first. What the platform looks like after Session 03,
|       the four security risks this session targets, and what you will
|       have when Session 04 is complete.
|
|-- 01-add-rate-limiting.md
|       Framework 11 + 05. Two rate limiters: one for the auth endpoint
|       (10 requests per 15 min per IP) and one for all three agent
|       endpoints (30 requests per min per user). Configuration driven
|       by environment variables. 429 response with Retry-After header.
|
|-- 02-validate-all-inputs.md
|       Framework 11 + 06. Input validation middleware applied before any
|       message reaches an agent. Max length enforcement, type checking,
|       and whitespace normalisation. What validation is not: prompt
|       injection detection belongs at the model layer, not here.
|
|-- 03-prevent-idor.md
|       Framework 11 + 09. Insecure Direct Object Reference: a student
|       changing a session ID to read another student's data. Every
|       database query in the platform must include both the resource ID
|       and the authenticated user's ID. Pattern, audit checklist, and
|       why the safe response is 404, not 403.
|
|-- 04-write-security-tests.md
|       Framework 11 + 10. The security test suite: auth tests (no token,
|       bad token, expired token), role guard tests (student hitting
|       professor route), and one IDOR probe per resource type. Using
|       vitest and supertest. Tests that must pass before every deploy.
|
|-- 05-run-the-security-audit.md
|       Framework 11 + 02. Running the full audit: npm audit, grep sweeps,
|       security test suite, and writing SECURITY.md. The SECURITY.md
|       format covers threat model, attack surface, active controls,
|       OWASP status, data classification, and the incident response plan.
|
|-- assignments/
|   |-- 01-add-rate-limiting.md
|   |-- 02-validate-all-inputs.md
|   |-- 03-prevent-idor.md
|   |-- 04-write-security-tests.md
|   |-- 05-run-the-security-audit.md
|   `-- README.md
|
`-- starter-code/
    |-- CLAUDE.md          Cumulative operating brief for end of Session 04
    |-- .env.example       Environment variables including rate limit config
    |-- package.json       Version 0.4.0, adds helmet
    `-- requirements.txt   Python dependencies unchanged from Session 03
```

---

## What You Will Have at the End

- Rate limiting on all auth and agent endpoints, driven by environment variables
- Input validation middleware rejecting malformed messages before agents see them
- Every database query scoped to both resource ID and authenticated user ID
- A passing security test suite covering auth, role guards, and IDOR
- A completed SECURITY.md documenting the full platform security posture
- Zero high or critical findings from npm audit

---

## How This Session Relates to Others

| Session | Security angle covered |
|---|---|
| Session 01 | Framework 11: minimum security baseline before first run |
| Session 02 | JWT authentication, bcrypt password hashing, secure routes |
| Session 03 | Tool dispatch allowlist, parameterised queries, role guards |
| Session 04 | Rate limiting, input validation, IDOR prevention, security tests, audit |
| Session 05 | Multi-agent trust: privilege separation between agents |
| Session 06 | Production security: HTTPS, monitoring, incident response at scale |

---

Copyright Janna AI Research Labs
