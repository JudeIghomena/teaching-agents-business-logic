# Build 05: Run the Security Audit

**Frameworks applied:** 11 (Security Baseline) + 02 (Project Structure)

---

## What a Security Audit Is

An audit is a structured review of every security control in the platform,
run against a checklist. The goal is not to find new vulnerabilities (though
it sometimes does): the goal is to confirm that every control you implemented
is in place, correctly wired, and producing the expected behaviour.

The audit for this platform has four stages:

1. npm audit: confirm zero high or critical dependency vulnerabilities
2. Grep sweeps: confirm no hardcoded secrets, no unsafe patterns
3. Security test suite: confirm all auth, role guard, and IDOR tests pass
4. Write SECURITY.md: document the complete security posture

Running stages 1, 2, and 3 takes about five minutes. Writing SECURITY.md
takes longer, but it is written once and maintained thereafter. It is also
required: every project under Janna AI Research Labs must have a SECURITY.md
at its root before any deployment.

---

## Stage 1: npm audit

```bash
cd server && npm audit
```

Expected output:

```
found 0 vulnerabilities
```

If you see high or critical vulnerabilities, do not proceed to Stage 2.
Fix them first. The fix for most transitive dependency vulnerabilities is
to add an entry in the `overrides` section of `package.json`:

```json
"overrides": {
  "vulnerable-package": ">=safe-version"
}
```

Then run `npm install` to regenerate the lock file. Run `npm audit` again
to confirm the vulnerability is resolved.

If the vulnerable package is a direct dependency (in `dependencies` or
`devDependencies`), update its version number directly. Do not pin to
a specific patch version if a version range resolves the issue: pinning
creates maintenance debt.

Do not use `npm audit fix --force`. It can introduce breaking changes.
Understand each fix before applying it.

---

## Stage 2: Grep Sweeps

These greps run against the server source directory. All must return zero
results (zero lines of output). Any result is a finding that must be
fixed before committing.

```bash
# No hardcoded Anthropic API keys
grep -rn "sk-ant" server/src/

# No hardcoded JWT secrets
grep -rn "JWT_SECRET\s*=" server/src/

# No synchronous bcrypt (compareSync is banned in request handlers)
grep -rn "compareSync\|hashSync" server/src/

# JWT verify must pin the algorithm
grep -rn "jwt.verify" server/src/
# Manually review each hit and confirm it includes algorithms: ['HS256']

# No raw string concatenation into SQL
grep -rn "WHERE.*\+" server/src/
grep -rn "SELECT.*\$\{" server/src/

# authMiddleware must be on every agent and professor route
grep -rn "router.post\|router.get\|router.patch" server/src/routes/
# Manually review: every line should have authMiddleware in the chain
```

The JWT verify grep requires manual review because it returns positive
results (you want to find the verify calls, then confirm each one is
safe). A `jwt.verify` call without `{ algorithms: ['HS256'] }` must
be updated to include it.

---

## Stage 3: Run the Security Test Suite

```bash
cd server && npm test
```

All tests must pass with zero failures and zero skipped. If any test
fails, fix the underlying code before proceeding to Stage 4.

Record the result:

```
Security tests: [X/Y] passed
Date: [today's date]
```

This baseline goes into SECURITY.md under the Dependency Vulnerability Log.

---

## Stage 4: Write SECURITY.md

Create `SECURITY.md` at the project root (not inside `server/`, at the top
level alongside `requirements.txt`).

SECURITY.md documents the full security posture of the platform. It is a
living document: update it whenever a new route, dependency, or attack
surface is added. A feature is not shipped if it introduces a new attack
surface not documented here.

---

### SECURITY.md Template

```markdown
# SECURITY.md - SCQ Business Case Logic Platform

Last updated: [date]
Platform version: 0.4.0 (end of Session 04)

---

## 1. Threat Model

The SCQ platform is a multi-student coaching application. The primary
threat actors are:

Insider misuse: A student who attempts to access another student's sessions
or coaching history. Motive: academic dishonesty or curiosity.

External attacker: Someone not enrolled who attempts to gain access to the
platform. Motive: accessing student data or disrupting the service.

Prompt injection: A student crafting a message designed to manipulate the
agent into stepping outside its defined task. Motive: gaming the coaching
session or producing unintended outputs.

Cost abuse: A student or external party flooding the agent endpoints to
exhaust the Anthropic API budget. Motive: disruption.

---

## 2. Attack Surface Map

| Entry point | Risk | Control |
|---|---|---|
| POST /api/auth/login | Brute force | authLimiter: 10 req/15 min/IP |
| POST /api/agent1/chat | Unauthorised access, flooding | authMiddleware + agentLimiter |
| POST /api/agent2/chat | Unauthorised access, flooding | authMiddleware + agentLimiter |
| POST /api/agent3/chat | Unauthorised access, flooding | authMiddleware + agentLimiter |
| GET /api/professor/sessions | IDOR across cohorts | authMiddleware + requireRole('professor') + cohort_id scope |
| PATCH /api/professor/sessions/:id/finalise | IDOR across cohorts | authMiddleware + requireRole('professor') + cohort_id scope |
| SQLite database file | Direct file access | File stored outside web root, not publicly accessible |
| agent/ Python files | Prompt injection | TOOL_DISPATCH allowlist, output validation |

---

## 3. Active Security Controls

| Control | Layer | Implementation |
|---|---|---|
| JWT authentication | Express middleware | server/src/middleware/auth.js, HS256 algorithm pinned |
| Role-based access | Express middleware | server/src/middleware/roleGuard.js |
| Auth rate limiting | Express middleware | server/src/middleware/rateLimiter.js, 10 req/15 min/IP |
| Agent rate limiting | Express middleware | server/src/middleware/rateLimiter.js, 30 req/min/user |
| Input validation | Express middleware | server/src/middleware/validator.js, max 2000 chars |
| Password hashing | bcrypt | cost factor 12, async only |
| IDOR prevention | Database queries | All queries include user_id or cohort_id scope |
| Tool dispatch allowlist | Python agent | TOOL_DISPATCH dict, unregistered tool names rejected |
| Parameterised queries | Database layer | No string concatenation in SQL |
| Security test suite | vitest | server/tests/security.test.js, runs before every deploy |

---

## 4. OWASP API Top 10 Status

| Risk | Status | Notes |
|---|---|---|
| API1 - Broken Object Level Auth | Mitigated | IDOR prevention: all queries scoped by user_id/cohort_id |
| API2 - Broken Auth | Mitigated | JWT with HS256 pinning, bcrypt cost 12 |
| API3 - Broken Object Property Level Auth | Partial | Professor route returns session IDs but not message content |
| API4 - Unrestricted Resource Consumption | Mitigated | Rate limiting on all endpoints |
| API5 - Broken Function Level Auth | Mitigated | requireRole guards on professor routes |
| API6 - Unrestricted Access to Sensitive Business Flows | Mitigated | Agent routes require auth + rate limit |
| API7 - Server Side Request Forgery | Not applicable | No server-side URL fetching |
| API8 - Security Misconfiguration | Partial | HTTPS not yet configured (Session 06) |
| API9 - Improper Inventory Management | Partial | SECURITY.md maintained but no automated route inventory |
| API10 - Unsafe Consumption of APIs | Partial | Anthropic SDK used, output validation on Tedd only |

---

## 5. Data Classification

| Data type | Sensitivity | Where stored | Who can access |
|---|---|---|---|
| Student email | Medium | users table | Auth system only |
| Password hash | High | users table | Auth middleware, never returned in API responses |
| JWT secret | Critical | Environment variable | Server process only, never logged |
| Anthropic API key | Critical | Environment variable | Agent runner only, never logged |
| Session messages | Medium | agent_sessions.messages | Owning student only |
| Quality scores | Low | agent_sessions.quality_score | Owning student + professor in same cohort |

---

## 6. Known Vulnerabilities and Accepted Risks

HTTPS not yet configured. The platform currently runs on HTTP. In development
this is acceptable. Before any production deployment, HTTPS must be configured
at the hosting layer. See Session 06.

No CSRF protection. The API is stateless (JWT only, no cookies), so CSRF is
not applicable for the agent endpoints. The login endpoint uses JSON body
parameters, not form submissions, so CSRF is not a risk here.

No content security policy headers. Adding Helmet with an explicit CSP is
deferred to Session 06 when the frontend hosting layer is configured.

---

## 7. Dependency Vulnerability Log

| Date | Command | Result |
|---|---|---|
| [date] | npm audit | 0 high, 0 critical |

Update this table after every `npm audit` run and after every dependency
update. Do not mark a dependency update as complete without running
`npm audit` and recording the result.

---

## 8. Incident Response

### API key exposed

1. Rotate immediately at console.anthropic.com
2. Confirm the old key is deactivated (test it: expect 401)
3. Update the environment variable in your hosting environment
4. Audit git log for any commit that may have included the key
5. If the key was committed to a public repo, assume it was captured
   and treat all data accessed under that key as potentially compromised
6. Review Anthropic usage logs for unusual call patterns during the
   exposure window

### JWT secret exposed

1. Generate a new secret (minimum 64 hex characters)
2. Update the environment variable: all existing JWTs are immediately invalidated
3. Students must log in again: this is expected and correct
4. Audit how the secret was exposed and prevent recurrence

### Confirmed IDOR vulnerability

1. Identify which route and which query is missing the scope condition
2. Add `AND user_id = ?` or `AND cohort_id = ?` to the query
3. Determine whether any data was accessed without authorisation
4. If yes: notify affected students, document the incident
5. Add a regression test to the security suite covering the specific case

### Runaway agent (unexpected tool calls or cost spike)

1. Check agent logs for tool call patterns outside normal parameters
2. Kill the Express server to stop all agent calls immediately
3. Review the conversation turns that preceded the unexpected behaviour
4. Identify whether the cause was a prompt issue or a tool dispatch bug
5. Fix, add a test case, redeploy

---

## 9. Pre-Deploy Security Checklist

Before deploying to any environment reachable by users:

- [ ] npm audit: zero high/critical findings
- [ ] grep -rn "sk-ant" server/src/: zero results
- [ ] All jwt.verify calls include algorithms: ['HS256']
- [ ] No bcrypt.compareSync or bcrypt.hashSync in any route handler
- [ ] Security test suite: all tests pass
- [ ] HTTPS configured at hosting layer
- [ ] Environment variables set in hosting environment (not hardcoded)
- [ ] SECURITY.md updated to reflect current state

---

## 10. Future Hardening

Prioritised by impact:

1. HTTPS and Strict-Transport-Security header (Session 06)
2. Helmet CSP, X-Content-Type-Options, X-Frame-Options (Session 06)
3. Automated secret scanning in CI (block commits with secrets)
4. Per-student token budget with hard ceiling (prevent runaway spend)
5. Structured audit log: every tool call logged with user_id, timestamp, outcome
6. Penetration test before any public launch
```

---

## Completing the Audit

After writing SECURITY.md, run all four stages one final time in sequence:

```bash
cd server && npm audit          # Zero high/critical
cd server && npm test           # All security tests pass
grep -rn "sk-ant" server/src/   # Zero results
```

When all pass, commit everything:

```bash
git add SECURITY.md \
  server/src/middleware/rateLimiter.js \
  server/src/middleware/validator.js \
  server/src/routes/ \
  server/src/db.js \
  server/tests/ \
  starter-code/CLAUDE.md

git commit -m "feat(session-04): security hardening complete

- Rate limiting: auth 10/15min/IP, agents 30/min/user
- Input validation middleware on all agent routes
- IDOR prevention: all queries scoped by user_id/cohort_id
- Security test suite: auth, role guard, IDOR categories
- SECURITY.md: full platform security posture documented
- npm audit: 0 high, 0 critical"
```

Session 04 is complete. The platform is hardened and documented. Session 05
builds the orchestration layer.

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code can run
the audit commands, interpret their output, and generate SECURITY.md from
what it finds. This is one place where Claude Code's ability to read your
whole codebase at once is particularly useful: it can produce a SECURITY.md
that is genuinely specific to your platform rather than generic.

**Prompt to run the audit and write SECURITY.md:**

```
Run the full Session-04 security audit on this platform and produce SECURITY.md.

Step 1: Run npm audit in the server directory. Report the findings.
If there are any high or critical findings, stop and describe each one
with the fix before continuing.

Step 2: Run these grep commands and report results:
  grep -rn "sk-ant" server/src/
  grep -rn "JWT_SECRET\s*=" server/src/
  grep -rn "compareSync\|hashSync" server/src/
  grep -rn "jwt.verify" server/src/
  grep -rn "WHERE.*\+" server/src/
The first four must return zero results. For jwt.verify, list each hit
and confirm it includes { algorithms: ['HS256'] }.

Step 3: Run npm test in the server directory. Report the result: how many
tests passed, whether any failed or were skipped.

Step 4: Create SECURITY.md at the project root (not inside server/).
The file must have exactly these 10 sections:
1. Threat Model - who the threat actors are for a multi-student coaching platform
2. Attack Surface Map - table of every entry point with the control applied
3. Active Security Controls - table of every control built in Session 04
4. OWASP API Top 10 Status - table of all 10 risks with honest status
5. Data Classification - what data is stored and who can access it
6. Known Vulnerabilities and Accepted Risks - list every known gap honestly
7. Dependency Vulnerability Log - one row with today's date and npm audit result
8. Incident Response - playbooks for API key exposure, JWT secret exposure,
   confirmed IDOR, and runaway agent
9. Pre-Deploy Security Checklist - checklist reflecting controls actually built
10. Future Hardening - HTTPS, Helmet CSP, and any other deferred items

Make every section specific to this platform. Name the actual routes, actual
files, actual users (MBA students, professors). Do not write generic content.
```

**What Claude Code will do:**
Run all audit commands and report their output, then generate SECURITY.md
by reading the actual codebase: your real routes, your real middleware, your
real schema. The resulting SECURITY.md will reference actual file paths and
actual controls rather than hypothetical ones.

**Tips for this document:**
- After Claude Code produces SECURITY.md, read Section 6 (Known Vulnerabilities)
  carefully. If it is empty or says "none", ask Claude Code: "What security
  controls are deferred to Session 05 or Session 06? List them in Section 6."
  An honest SECURITY.md always has accepted risks.
- If npm audit shows findings, do not ask Claude Code to run `npm audit fix
  --force`. Tell it: "Show me the vulnerable package name and the recommended
  safe version. I will add it to the overrides section in package.json."
- Tell Claude Code: "SECURITY.md belongs at the project root, alongside
  requirements.txt. Do not put it inside the server/ directory."

---

**Next session:** [Session 05 - Agent Coordination](../Session-05%20(Agent%20Coordination)/00-session-overview.md)

---

Copyright Janna AI Research Labs
