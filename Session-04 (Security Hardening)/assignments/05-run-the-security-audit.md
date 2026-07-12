# Assignment 05: Run the Security Audit

**Reads with:** [05-run-the-security-audit.md](../05-run-the-security-audit.md)
**Time estimate:** 60-90 minutes
**Frameworks applied:** 11 (Security Baseline) + 02 (Project Structure)

---

## What You Are Building

A completed four-stage security audit and a SECURITY.md at the project root
that documents the full security posture of the SCQ platform.

---

## Steps

### Step 1: Run npm audit

```bash
cd server && npm audit
```

Expected result: "found 0 vulnerabilities".

If you see high or critical findings, fix them before continuing. Do not
proceed to Step 2 with open high or critical vulnerabilities. The fix path
is in the build document (overrides in package.json, not npm audit fix
--force).

Record the result and today's date. You will include this in SECURITY.md.

### Step 2: Run the grep sweeps

Run each grep check from the build document in order:

```bash
grep -rn "sk-ant" server/src/
grep -rn "JWT_SECRET\s*=" server/src/
grep -rn "compareSync\|hashSync" server/src/
grep -rn "jwt.verify" server/src/
grep -rn "WHERE.*\+" server/src/
grep -rn "SELECT.*\$\{" server/src/
```

The first five greps must return zero results (no output). The `jwt.verify`
grep will return results: manually read each one and confirm it includes
`{ algorithms: ['HS256'] }` as the third argument.

Write down any finding. If you find a violation, fix it before continuing.

### Step 3: Run the security test suite

```bash
cd server && npm test
```

All tests must pass. Record the result: how many tests passed, today's
date. This goes into SECURITY.md under the dependency vulnerability log
(Section 7).

### Step 4: Write SECURITY.md

Create `SECURITY.md` at the project root (at the same level as
`requirements.txt`, not inside `server/`).

Use the template in the build document as your starting structure. Fill in
every section for your specific platform:

Section 1 (Threat Model): write in your own words who the threat actors
are for a student coaching platform and what their motives are.

Section 2 (Attack Surface Map): complete the table. Add any routes or entry
points that are not in the template. Remove any that do not apply.

Section 3 (Active Security Controls): fill in the table based on what you
actually built in Assignments 01 through 04. If you did not implement
something, mark it as not implemented and note it in Section 6.

Section 4 (OWASP API Top 10): review each of the ten risks and mark the
actual status for your platform. Be honest. "Partial" is the correct status
for anything that is not fully mitigated.

Section 5 (Data Classification): fill in based on what is actually stored
in your database. Review the schema from Session 02.

Section 6 (Known Vulnerabilities and Accepted Risks): list every item from
the template that applies. HTTPS not being configured is an accepted risk
for development. Do not omit it. A SECURITY.md that lists no known risks
is not honest: real platforms always have accepted risks.

Section 7 (Dependency Vulnerability Log): add one row with today's date and
the result of `npm audit` from Step 1.

Section 8 (Incident Response): fill in the playbooks. The key exposure and
JWT rotation playbooks are generic but should reference your platform's
specific environment: where your API key is stored, how to rotate it.

Section 9 (Pre-Deploy Security Checklist): this becomes your literal
checklist before any production deployment. Make sure it reflects all the
controls you actually implemented.

Section 10 (Future Hardening): list HTTPS, Helmet CSP, and any other items
you identified during the audit as not yet implemented. Prioritise them.

### Step 5: Commit everything

```bash
git add SECURITY.md \
  server/src/middleware/ \
  server/src/routes/ \
  server/src/db.js \
  server/tests/ \
  .env.example

git commit -m "feat(session-04): security hardening complete

- Rate limiting on auth (10/15min/IP) and agent endpoints (30/min/user)
- Input validation middleware: type, empty, max length
- IDOR prevention: all queries scoped to user_id or cohort_id
- Security test suite: auth, role guard, IDOR categories, all pass
- SECURITY.md: full platform security posture documented
- npm audit: 0 high, 0 critical"
```

---

## Done Checklist

- [ ] `npm audit` returns zero high or critical findings
- [ ] All five grep sweeps return zero results (or reviewed and clean for
  jwt.verify)
- [ ] `npm test` passes with zero failures
- [ ] `SECURITY.md` exists at the project root
- [ ] SECURITY.md has all 10 sections filled in with platform-specific content
- [ ] Section 6 (Known Vulnerabilities) is honest: lists HTTPS as not yet
  configured if applicable
- [ ] Section 7 (Dependency Vulnerability Log) has one entry with today's
  date and the npm audit result
- [ ] Everything committed with the complete commit message
- [ ] Commit message references the security work done in all four assignments

---

## Troubleshooting

npm audit returns findings after adding overrides: Run `npm install` after
adding the override to regenerate the lock file. The overrides only take
effect after the lock file is updated.

SECURITY.md feels generic: It should be specific to this platform. Every
section should reference actual files, actual routes, actual tools. A
SECURITY.md that could apply to any Express app is not useful. The threat
model should name the actual users (MBA students, professors). The attack
surface should name the actual routes. The incident response should name
where the API key is actually stored.

Not sure what to put in Section 6: list every item from Section 10 of the
template that you deferred to a later session. If you did not implement
Helmet CSP, it belongs in Section 6 as an accepted risk with the note
"deferred to Session 06". This is honest and is the correct approach.

---

Session 04 is complete. The platform is hardened against the four risks
identified in the overview: unauthenticated access, unvalidated inputs,
IDOR, and missing security test coverage.

**Next session:** Session 05 - Agent Coordination
