# Assignment 05: Final Platform Review

**Reads with:** [05-final-platform-review.md](../05-final-platform-review.md)
**Time estimate:** 45-60 minutes
**Frameworks applied:** All eleven frameworks

---

## What You Are Building

A complete audit of the platform before it goes to real students. A HANDOFF.md
at the project root. A committed, pushed, production-deployed platform that
has passed every check.

---

## Steps

### Step 1: Run the full final audit

Work through every item in the audit list from the build document. Use the
exact commands listed. Do not mark an item as done until the command runs
clean.

Security checks first:

```bash
# JWT algorithm pinning
grep -rn "algorithms" server/src/middleware/auth.js

# No sync bcrypt
grep -rn "compareSync\|hashSync" server/src/

# IDOR prevention: all session queries scoped
grep -rn "WHERE id = ?" server/src/

# Secret scan
grep -rE "sk-ant" server/src/

# Vulnerability scan
npm audit --audit-level=high
```

Then tests:

```bash
cd server && npm test
```

Minimum 15 tests, zero failures.

Then agent quality:

```bash
python evaluation/run_golden.py
# All three agents must pass at 90% or above

python evaluation/measure_prompt.py
# Matteo and Juli <= 3,000 tokens, Tedd <= 4,000 tokens
```

### Step 2: Verify the live deployment

These checks must pass against the production URL, not localhost:

```bash
# Health check
curl https://your-app.railway.app/api/health

# Auth works
curl -X POST https://your-app.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.edu","password":"TestPass123!"}'

# Rate limit active (run 12 times, expect 429 on requests 11-12)
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST https://your-app.railway.app/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"x@x.com","password":"wrong"}'
done
```

### Step 3: Generate HANDOFF.md with Claude Code

Open the project in the Claude Code desktop app. Use the prompt from the
build document to generate HANDOFF.md at the project root.

Read the generated HANDOFF.md carefully. Correct any inaccuracies before
committing. The "Current State" section in particular must reflect what is
actually working in production, not what the code suggests should work.

### Step 4: Final commit and push

Stage and commit all changes from Session 06:

```bash
git add .
git status  # review what you are committing
git commit -m "feat(session-06): complete production deployment

Health check, Railway deploy with Volume, structured monitoring,
per-student token budgets, prompt caching, professor cost endpoint,
final platform review and HANDOFF.md.

Authored by Jude Ighomena, Copyright Janna AI Research Labs"

git push origin main
```

Confirm Railway automatically redeploys from the push. Verify the health
endpoint one more time after the redeploy completes.

---

## Done Checklist

Security audit:
- [ ] JWT verify includes algorithms: ['HS256']
- [ ] No bcrypt.compareSync in any route handler
- [ ] All agent_sessions queries scoped by user_id or cohort_id
- [ ] No hardcoded secrets in source files
- [ ] npm audit returns zero high/critical

Tests:
- [ ] npm test passes with minimum 15 tests, zero failures

Agent quality:
- [ ] All three agents pass golden dataset at 90%+
- [ ] All three system prompt token counts within limits

Production:
- [ ] GET /api/health returns ok on the live URL
- [ ] Auth login works on the live URL
- [ ] Rate limit active on the live URL (429 on request 11)
- [ ] turn_complete logs appearing in Railway logs
- [ ] total_tokens incrementing in the database after student turns

Documentation:
- [ ] HANDOFF.md at project root is accurate and committed
- [ ] starter-code/CLAUDE.md reflects the complete production platform
- [ ] All changes committed and pushed to main

---

## Troubleshooting

Golden dataset below 90%: The evaluation suite tests the current prompt
against expected outputs. If a prompt change during the course degraded
Matteo's performance, review PROMPT_ITERATIONS.md for the last change that
reduced the score and revert it.

Health check returns ok but students cannot connect: The platform is running
but CORS is blocking the frontend. Confirm CORS_ORIGIN matches the exact
frontend URL. Check the browser console for the specific CORS error.

Railway redeploying but DATABASE_URL not found: The Volume may not be
correctly attached. Check the Railway dashboard: the Volume should appear
under the service, not as a separate service. If it shows as a separate
service, re-attach it.

HANDOFF.md is empty or generic: Claude Code generates HANDOFF.md from the
codebase and git history. If the history is thin or the CLAUDE.md is
missing sections, the output will be generic. Add more context to your
CLAUDE.md prompt and regenerate.

---

Session 06 is complete. The SCQ Simulation Portal is built, secured,
coordinated, deployed, monitored, and documented. What you have built across
these six sessions is a production-quality AI coaching platform. Every
architectural decision was deliberate and documented. The platform is ready
for real students.

**This is the final session.**
