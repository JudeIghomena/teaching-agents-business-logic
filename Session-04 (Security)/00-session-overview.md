# Session 04: Security

> A platform with three working agents and no security hardening is a prototype.
> Session 04 turns the prototype into something you can confidently put in front
> of real students without losing sleep about what could go wrong.

---

## Where You Are in the Build

By the end of Session 03 you have:
- All three agents running on the platform (Matteo, Juli, Tedd)
- A student can complete all three stages end to end
- Every turn stored in the database with conversation history
- Agent tools wired: save_scq_draft, get_stage_context, get_rubric_config, save_evaluation
- JWT authentication on all routes, role guards for professor access
- A passing evaluation suite for all three agents

The platform works. Session 04 makes it resistant to the failures that
would expose student data, allow unauthorised access, or let one student
interfere with another's work.

---

## What This Session Covers

Session 04 applies Framework 11 (Security Baseline) at full depth across
the complete platform. Session 02 implemented the baseline. Session 04
hardens every layer against the attacks and failures most likely to affect
a real multi-student coaching platform.

| Document | What it builds |
|---|---|
| 00-session-overview.md (this file) | Build recap, session scope, what you will have |
| 01-add-rate-limiting.md | Rate limits on auth and all three agent endpoints |
| 02-validate-all-inputs.md | Input validation before any message reaches an agent |
| 03-prevent-idor.md | Row-level security: every query scoped to the authenticated user |
| 04-write-security-tests.md | Auth tests, role guard tests, IDOR probe per resource |
| 05-run-the-security-audit.md | Full platform audit against the Session-01 checklist |

**What you will have at the end of Session 04:**
A hardened platform with rate limiting on all sensitive endpoints, validated
inputs, no IDOR vulnerabilities, a passing security test suite, and a completed
platform-wide security audit documented in SECURITY.md.

**Previous session:** [Session 03 - Business Case Logic](../Session-03%20(Business%20Case%20Logic)/00-session-overview.md)
**Next session:** Session 05 - Multi-Agent Coordination

---

## The Four Security Risks This Session Targets

### 1. Unauthenticated or over-privileged access
A student should only be able to access their own sessions. A professor should
only be able to access sessions in their own cohort. No endpoint should be
reachable without a valid JWT. Rate limiting prevents brute-force attacks on
the login endpoint.

### 2. Unvalidated inputs reaching the agents
The agent receives whatever the web layer passes to it. If a student sends
a 50,000-word message, it will consume the entire context window. If a student
sends HTML or script tags, they should be stripped before the agent sees them.
Input validation is the web layer's job, not the agent's.

### 3. IDOR: one student reading another's data
IDOR (Insecure Direct Object Reference) means a student can change an ID in
a request to access someone else's data. Every database query in the platform
must be scoped: `WHERE id = ? AND user_id = ?`. A query that only checks the
resource ID without checking ownership is an IDOR vulnerability.

### 4. Missing test coverage for auth and access control
Auth middleware and role guards are only as reliable as the tests that verify
them. A route that works in manual testing but has no automated test can regress
silently when other code changes. Session 04 writes the test suite that prevents this.

---

## What Changes in the CLAUDE.md

Session 04 adds to your CLAUDE.md:
- Rate limit configuration: requests per minute per endpoint per user
- Input validation rules: max message length, allowed characters, sanitisation steps
- IDOR prevention rule: every query must include both resource ID and user_id
- Security test mandate: auth, role guard, and one IDOR probe per resource type

---

## Before You Start

Confirm these are all true before opening the first document:

- [ ] All three agents respond correctly to authenticated requests
- [ ] A student completing all three stages produces records in agent_sessions
- [ ] Professor routes correctly return 403 when called with a student JWT
- [ ] `python evaluation/run_golden.py` still passes at 90% or above

If any of these are not true, complete the relevant Session 03 work first.

---

## Start Here

[Build 01: Add Rate Limiting](01-add-rate-limiting.md)

---

Copyright Janna AI Research Labs
