# Assignment 05: Handle Agent Failures

**Reads with:** [05-handle-agent-failures.md](../05-handle-agent-failures.md)
**Time estimate:** 35-45 minutes
**Frameworks applied:** 11 (Security Baseline) + 01 (Agent Mental Model)

---

## What You Are Building

Retry logic for transient API errors, clean error responses when retries
are exhausted, process cleanup on client disconnect, and the HITL flag that
surfaces low-scoring Tedd evaluations for professor review.

---

## Steps

### Step 1: Add call_with_retry to agent/runner.py

Wrap the `client.messages.create` call in `agent/runner.py` with the retry
function from the build document. Only retry on status code 529. Do not
retry on 400 or 401.

The retry budget is one attempt: if the first call fails with 529, wait
one second and try once more. If that also fails, raise the exception.

Test the retry path by temporarily passing a bad model name to the client.
This produces a 400 (not 529), so the retry should NOT fire. Confirm you
see exactly one attempt in the server logs, not two.

### Step 2: Add stderr buffer and clean error response in agentCaller.js

In the `streamAgent` function in `agentCaller.js`:

1. Add a `let stderrBuffer = ''` variable before the spawn call
2. In `python.stderr.on('data')`, accumulate output: `stderrBuffer += data.toString()`
3. In `python.on('close', code)`, if `code !== 0`, write a structured SSE
   error event and call `res.end()`. Check `!res.writableEnded` first.
4. Log the full stderr content server-side, not to the client

The error message sent to the client must say something like "The coaching
agent is temporarily unavailable. Please try again in a moment." It must
not include the Python stack trace or any internal detail.

### Step 3: Add client disconnect handling

In `streamAgent`, before the spawn call, add:

```js
req.on('close', () => {
  if (!python.killed) {
    python.kill();
    console.log(`[${agentId}] client disconnected, killed agent process`);
  }
});
```

To test: start a long agent response, then close the browser tab or kill
the curl command mid-stream. Check the server log for the "client
disconnected" message.

### Step 4: Add the needs_review column

Run this migration in a SQLite shell:

```bash
sqlite3 data/platform.db
```

```sql
ALTER TABLE agent_sessions ADD COLUMN needs_review INTEGER NOT NULL DEFAULT 0;
```

Also add the column to `server/src/db-init.js` so new installs get it:

```js
needs_review INTEGER NOT NULL DEFAULT 0
```

Add to `.env` and `.env.example`:

```
HITL_SCORE_THRESHOLD=3.0
```

### Step 5: Update save_evaluation in tool_registry.py

Calculate the average score from the evaluation fields. Compare to
`float(os.getenv('HITL_SCORE_THRESHOLD', '3.0'))`. Set `needs_review = 1`
in the UPDATE if the average is below the threshold.

Include `needs_review` in the returned dict.

### Step 6: Update the professor route

In `server/src/routes/professor.js`, add `needs_review` to the SELECT
columns and add `ORDER BY needs_review DESC, created_at DESC` so flagged
sessions appear at the top of the professor's list.

---

## Done Checklist

- [ ] `call_with_retry` wraps the messages.create call in runner.py
- [ ] Retry fires only on status 529, not on 400 or 401
- [ ] stderr output buffered in agentCaller.js, logged server-side only
- [ ] Non-zero exit code writes SSE error event to client and calls res.end()
- [ ] Client disconnect kills the Python process
- [ ] `needs_review INTEGER NOT NULL DEFAULT 0` in db-init.js
- [ ] Schema migration run on existing database
- [ ] `HITL_SCORE_THRESHOLD=3.0` in .env and .env.example
- [ ] `save_evaluation` sets needs_review based on average score
- [ ] Professor route orders by needs_review DESC
- [ ] `npm test` still shows all previous tests passing

---

## Troubleshooting

Retry fires on 400 errors: Confirm the condition is `e.status_code == 529`
(the integer 529, not the string). Also confirm you are catching
`anthropic.APIStatusError`, not a broader exception class.

Client disconnect message not appearing in logs: Confirm the `req.on('close')`
handler is registered before `python.stdin.end()`. If the client disconnects
during the stdin write, the handler must already be attached.

needs_review column error on existing database: SQLite requires ALTER TABLE
to add columns one at a time. If the column was previously added with a
different type, drop and recreate the table (losing existing data) or rename
the database file and run db-init again in development.

Professor sessions not ordered with needs_review first: Confirm the ORDER BY
clause is `needs_review DESC, created_at DESC` (not ASC). A value of 1 sorts
higher than 0 with DESC ordering.

---

**End of Session 05 assignments.**

Next session: [Session 06 - Production and Deployment](../../Session-06%20(Production%20and%20Deployment)/00-session-overview.md)
