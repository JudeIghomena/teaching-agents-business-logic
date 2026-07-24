# Assignment 04: Control Costs

**Reads with:** [04-control-costs.md](../04-control-costs.md)
**Time estimate:** 40-50 minutes
**Frameworks applied:** 04 (Context Window Budget) + 10 (Observability)

---

## What You Are Building

A per-student token budget enforced at the orchestrator. A schema column that
tracks cumulative token usage per user. A professor endpoint for cohort cost
visibility. Anthropic prompt caching enabled on all three agent system prompts.

---

## Steps

### Step 1: Add total_tokens to the users table

In `server/src/db-init.js`, add `total_tokens INTEGER NOT NULL DEFAULT 0` to
the users table CREATE statement.

Run the ALTER TABLE migration on your existing development database:

```bash
sqlite3 data/scq.db "ALTER TABLE users ADD COLUMN total_tokens INTEGER NOT NULL DEFAULT 0;"
```

Verify the column exists:

```bash
sqlite3 data/scq.db ".schema users"
```

### Step 2: Update token count after each turn

In `server/src/lib/agentCaller.js`, in the stdout `end` handler (after
`appendTurn`), add the token count update:

```js
if (usageData) {
  const totalUsed = (usageData.input_tokens || 0) + (usageData.output_tokens || 0);
  db.prepare(`UPDATE users SET total_tokens = total_tokens + ? WHERE id = ?`)
    .run(totalUsed, user.id);
}
```

Wrap this in its own try/catch so a tracking failure does not interrupt the
student response.

### Step 3: Add the budget check to the orchestrator

In `server/src/routes/orchestrator.js`, before the stage check, read the
budget and the user's current token count:

```js
const TOKEN_BUDGET = parseInt(process.env.TOKEN_BUDGET_PER_USER || '50000');
const userRow = db.prepare(`SELECT total_tokens FROM users WHERE id = ?`).get(user.id);

if (userRow && userRow.total_tokens >= TOKEN_BUDGET) {
  return res.json({
    message: 'You have reached your session token limit. Your professor can reset it if needed.',
    budget_exceeded: true,
    stage: 'BUDGET_EXCEEDED',
  });
}
```

Test the budget check:

```bash
# Set a very low budget in .env for testing
TOKEN_BUDGET_PER_USER=1
```

Restart the server. Send a message to POST /api/chat. The response should
be the budget exceeded JSON immediately. Restore the real value after testing.

### Step 4: Add the professor cost endpoint

In `server/src/routes/professor.js`, add GET /cost as shown in the build
document. The route must require `authMiddleware` and `requireRole('professor')`.

Test it by logging in as a professor and calling:

```bash
curl -H "Authorization: Bearer <professor-token>" \
  http://localhost:3001/api/professor/cost
```

### Step 5: Enable prompt caching

In `agent/context.py`, update the system prompt function to return a list
containing a dict with the `text` and `cache_control`:

```python
def build_system_prompt(agent_id, version='v1'):
    text = load_prompt(agent_id, version)
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
```

In `agent/runner.py`, update the `client.messages.create` call (inside
`call_with_retry`) to pass the system as the list rather than a string:

```python
system=build_system_prompt(agent_id),
```

Start a student session and send two messages to the same agent. Check the
Railway (or local server) logs. The second call's `input_tokens` should be
lower than the first due to caching. The difference should roughly equal the
system prompt token count.

---

## Done Checklist

- [ ] `total_tokens` column in db-init.js and migrated on existing database
- [ ] Token count updated after each turn in agentCaller.js
- [ ] Token update wrapped in try/catch (tracking failure does not block student)
- [ ] Budget check in orchestrator returns JSON with budget_exceeded: true
- [ ] `TOKEN_BUDGET_PER_USER` in .env.example with default 50000
- [ ] Professor GET /cost endpoint requires auth and professor role
- [ ] Cost endpoint returns total_tokens per student and cohort total
- [ ] System prompts updated with cache_control in context.py
- [ ] runner.py passes system as a list of blocks
- [ ] Caching effect visible in logs: second call's input_tokens lower than first
- [ ] npm test passes with zero failures after all changes

---

## Troubleshooting

Total_tokens is always 0 after turns: Either usageData is null (Python is not
emitting the __USAGE__ line) or the UPDATE query is not running. Add
`console.log('updating tokens:', totalUsed, 'for user:', user.id)` temporarily
to confirm the code path is reached.

Budget check runs but never triggers: Confirm `total_tokens` is being
incremented. Check the users table directly:
`sqlite3 data/scq.db "SELECT id, email, total_tokens FROM users;"`

Prompt caching not reducing token counts: Confirm the anthropic Python SDK
version supports prompt caching. Run `pip show anthropic` and check the
version. Caching requires SDK >= 0.27.0. Also confirm the model supports
caching: claude-haiku-4-5-20251001 does, but check the Anthropic docs if
you have changed the model.

Professor cost endpoint returns 403: Confirm the test user has `role = 'professor'`
in the users table. The test suite seeds a professor user but your manual
test account may have the default role of 'student'.

---

**Next assignment:** [05-final-platform-review.md](05-final-platform-review.md)
