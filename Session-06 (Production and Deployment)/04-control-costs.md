# Build 04: Control Costs

**Frameworks applied:** 04 (Context Window Budget) + 10 (Observability)

---

## The Cost Problem at Scale

Framework 04 (Context Window Budget) was introduced in Session 01 as a
design constraint: you must know how many tokens each agent uses per turn
so you can fit the platform within the model's context limit.

In production, the same accounting applies to money. Every input and output
token costs a fraction of a cent. The fractions add up.

For a class of 60 students, with three agents, and approximately 20 turns
per agent on average:

```
60 students
  x 3 agents
  x 20 turns per agent
  x 1,500 tokens per turn (average input + output combined)
= 5,400,000 tokens per cohort
```

At claude-haiku-4-5 pricing (approximately $0.80 per million input tokens,
$4.00 per million output tokens), a cohort costs roughly $10-20 per semester.
That is affordable. But if a student runs an unusually long session, or if a
bug causes the history to grow without bound, one session can cost more than
the entire intended cohort budget.

Two controls prevent this:
1. A per-student token budget enforced at the orchestrator
2. Anthropic prompt caching to reduce input token cost on repeated calls

---

## Per-Student Token Budget

Add a `total_tokens` column to the users table:

```sql
ALTER TABLE users ADD COLUMN total_tokens INTEGER NOT NULL DEFAULT 0;
```

Add this column to `server/src/db-init.js` so new installs include it:

```sql
total_tokens INTEGER NOT NULL DEFAULT 0,
```

After each turn completes, update the user's token count in the `done` handler
of `streamAgent`:

```js
python.stdout.on('end', () => {
  // ... existing appendTurn and logging

  if (usageData) {
    const totalUsed = (usageData.input_tokens || 0) + (usageData.output_tokens || 0);
    db.prepare(
      `UPDATE users SET total_tokens = total_tokens + ? WHERE id = ?`
    ).run(totalUsed, user.id);
  }
  // ... existing done event
});
```

Before calling any agent in the orchestrator, check the budget:

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

This returns a clean JSON response (not SSE) before spawning any Python process.
The student sees a plain message. The professor can reset the budget by running:

```sql
UPDATE users SET total_tokens = 0 WHERE id = 'student-user-id';
```

---

## Prompt Caching

The Anthropic API supports prompt caching on claude-haiku models. Caching
marks a portion of the system prompt with a cache breakpoint. On subsequent
calls, the API recognises the cached prefix and charges a lower input token
rate for the cached portion.

The system prompts (matteo_v1.txt, juli_v1.txt, tedd_v1.txt) do not change
between turns. They are perfect candidates for caching.

Update `agent/context.py` to add cache_control to the system prompt:

```python
def build_system_prompt_block(agent_id, version='v1'):
    text = load_prompt(agent_id, version)
    return {
        "type": "text",
        "text": text,
        "cache_control": {"type": "ephemeral"}
    }
```

Update `agent/runner.py` to pass the system prompt as a content block
rather than a plain string:

```python
system_block = build_system_prompt_block(agent_id)

response = call_with_retry(
    client,
    messages=messages,
    system=[system_block],   # list of blocks, not a string
    model=model,
    tools=tools,
)
```

The `ephemeral` cache type is valid for approximately 5 minutes. For a
student in a single session, the system prompt will be cached on calls 2
through N of each agent, reducing input token cost by approximately 30%.

---

## The Professor Cost Endpoint

Professors need to see how much their cohort is using the platform. Add a
cost summary to the professor routes:

In `server/src/routes/professor.js`:

```js
router.get(
  '/cost',
  authMiddleware,
  requireRole('professor'),
  (req, res) => {
    const cohortId = req.user.cohortId;

    const rows = db.prepare(`
      SELECT
        u.id as user_id,
        u.email,
        u.total_tokens,
        COUNT(s.id) as session_count,
        SUM(s.quality_score) / NULLIF(COUNT(s.quality_score), 0) as avg_quality
      FROM users u
      LEFT JOIN agent_sessions s ON s.user_id = u.id AND s.cohort_id = ?
      WHERE u.cohort_id = ?
      GROUP BY u.id
      ORDER BY u.total_tokens DESC
    `).all(cohortId, cohortId);

    const totalTokens = rows.reduce((sum, r) => sum + (r.total_tokens || 0), 0);

    res.json({
      cohort_id: cohortId,
      student_count: rows.length,
      total_tokens: totalTokens,
      students: rows,
    });
  }
);
```

This gives the professor a single endpoint to see which students are consuming
the most tokens and which are not yet started. The professor does not see the
actual cost in dollars: that calculation belongs in whatever reporting tool
the institution uses, not in the platform.

---

## Soft Warning at 80% Budget

A hard cutoff at 100% is abrupt. At 80% of the budget, send a soft warning
in the SSE `done` event so the student knows to be efficient with their
remaining turns:

```js
const budgetUsedFraction = userRow.total_tokens / TOKEN_BUDGET;

res.write(`data: ${JSON.stringify({
  done: true,
  stage: agentId,
  budget_warning: budgetUsedFraction >= 0.8 && budgetUsedFraction < 1.0
    ? 'You are approaching your session token limit. Aim to complete your work in the next few turns.'
    : null,
})}\n\n`);
```

The client can display this warning in the UI when `budget_warning` is
non-null. The student can continue; only when `budget_exceeded` is true
in the JSON response does the session stop.

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code already
knows the db.js singleton, the users table schema, and the orchestrator
route pattern from CLAUDE.md.

**Prompt to add cost controls:**

```
Add per-student token budgeting to the SCQ platform.

1. Add the total_tokens column to the users table in db-init.js:
   total_tokens INTEGER NOT NULL DEFAULT 0,
   Also write the ALTER TABLE migration for existing databases.

2. In server/src/lib/agentCaller.js (streamAgent), after appending turns in
   the stdout 'end' handler, update the user's token count:
   UPDATE users SET total_tokens = total_tokens + ? WHERE id = ?
   Use (usageData.input_tokens + usageData.output_tokens) as the increment.
   Only run the UPDATE if usageData is not null.

3. In server/src/routes/orchestrator.js, before calling any agent:
   - Read TOKEN_BUDGET_PER_USER from the environment (default 50000)
   - Query SELECT total_tokens FROM users WHERE id = ?
   - If total_tokens >= TOKEN_BUDGET_PER_USER, return a JSON response
     with { message: '...', budget_exceeded: true, stage: 'BUDGET_EXCEEDED' }
   - Do not start an SSE stream for over-budget students

4. In server/src/routes/professor.js, add GET /cost (professor role required)
   that returns total_tokens per student in the cohort plus the cohort total.

5. In agent/context.py, update the system prompt function to return a dict
   with cache_control: { type: 'ephemeral' } alongside the text.
   In agent/runner.py, pass the system as a list containing this dict
   rather than a plain string.

6. Add TOKEN_BUDGET_PER_USER=50000 to server/.env.example.
```

**What Claude Code will do:**
Add the total_tokens column to db-init.js, wire the post-turn token update,
add the budget check to the orchestrator, add the professor cost endpoint,
and update the Python agent to use cacheable system prompts.

**Tips for this document:**
- After adding the budget check, test it by setting TOKEN_BUDGET_PER_USER=1
  in your .env. The next message to /api/chat should return the budget exceeded
  JSON immediately. Reset the env var after testing.
- The prompt caching change requires the Anthropic SDK to support the
  betas.prompt_caching feature for this model. Confirm by checking the
  anthropic Python SDK version in requirements.txt is >= 0.27.0.
- Tell Claude Code: "The UPDATE users SET total_tokens query must not be
  inside the main agent call try/catch. Token tracking should not block
  the student response if it fails. Wrap it in its own try/catch and log
  the error without re-throwing."

---

**Next:** [05-final-platform-review.md](05-final-platform-review.md)

---

Copyright Janna AI Research Labs
