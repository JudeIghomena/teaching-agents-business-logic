# Build 05: Handle Agent Failures

**Frameworks applied:** 11 (Security Baseline) + 01 (Agent Mental Model)

---

## What Can Fail

An agent call involves three components: the Express route, the Python
process spawned by child_process, and the Anthropic API called by the
Python agent. Any of these can fail.

| Failure type | Where it occurs | What the student sees without handling |
|---|---|---|
| API timeout | Anthropic SDK in Python | Stream hangs, browser spins forever |
| 529 Overloaded | Anthropic API | Python exits with error, SSE stream ends with no done event |
| Tool call error | Python agent | Partial response, tool result missing from history |
| Python spawn error | Node child_process | 500 or silent failure if headers already sent |
| Stream break mid-response | SSE connection | Partial message with no done event |
| Tedd double-submit | Route logic | 409 returned correctly (already handled in Session 03) |

The failure handling in this document covers the first four cases. The fifth
(stream break) is handled by the client reconnection pattern. The sixth is
already handled.

---

## Retry on 529 Overloaded

The Anthropic API returns 529 when the service is temporarily overloaded.
This is a transient error. One retry with a short delay resolves it in
most cases.

Add a retry wrapper in the Python agent runner:

```python
import time
import anthropic

def call_with_retry(client, messages, system, model, tools, max_retries=1):
    for attempt in range(max_retries + 1):
        try:
            return client.messages.create(
                model=model,
                max_tokens=1024,
                system=system,
                messages=messages,
                tools=tools or [],
                stream=True,
            )
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < max_retries:
                time.sleep(1)
                continue
            raise
```

Replace the direct `client.messages.create` call in `agent/runner.py`
with `call_with_retry`. This is a one-retry budget: one wait, one retry,
then raise the error. More retries add latency that students notice.

Do not retry on 400 (bad request) or 401 (invalid API key). These errors
indicate a code or configuration problem and will not resolve with retrying.

---

## Clean Error Response on Exhausted Retries

When the retry is exhausted, the Python agent exits with a non-zero return
code and writes the error to stderr. The Express orchestrator catches this
in the `python.on('error')` handler and in the stderr stream.

The student must receive a clean message, not a stack trace:

```js
python.stderr.on('data', (data) => {
  const errText = data.toString();
  console.error(`[orchestrator] agent stderr:`, errText);
  stderrBuffer += errText;
});

python.on('close', (code) => {
  if (code !== 0) {
    console.error(`[orchestrator] agent exited with code ${code}`, stderrBuffer);
    if (!res.writableEnded) {
      res.write(
        `data: ${JSON.stringify({
          error: true,
          message: 'The coaching agent is temporarily unavailable. Please try again in a moment.',
        })}\n\n`
      );
      res.end();
    }
  }
});
```

This closes the SSE stream cleanly with a structured error event instead of
leaving the stream hanging. The client can listen for `event.data.error` and
display the message to the student.

The full error including the Python stack trace is logged to the console
server-side. The student never sees it.

---

## Handling a Stream Break Mid-Response

If the student's network drops mid-stream, the SSE connection is severed.
The Python process continues running and produces output that is never
received. When the Python process finishes, `res.end()` is called on a
closed connection, which throws a `write after end` error.

Suppress this error safely:

```js
req.on('close', () => {
  if (!python.killed) {
    python.kill();
    console.log(`[orchestrator] client disconnected, killed agent process`);
  }
});
```

This kills the Python process when the client disconnects. No output is
written to a closed response. The student retries by sending the same
message again: the orchestrator re-enters the same stage and calls the
same agent.

The partial response that was streamed before the disconnect is not saved
to the database because `appendTurn` is called only in the `stdout.on('end')`
handler, which does not fire when the process is killed. This is intentional:
a partial response should not be stored as a complete turn in the conversation
history.

---

## The HITL Hook for Tedd

Human-in-the-loop (HITL) means pausing the automated flow and requesting
a human decision. For the SCQ platform, the HITL case is a Tedd evaluation
that scores below the professor review threshold.

When `save_evaluation` runs and the average quality score is below
`HITL_SCORE_THRESHOLD` (default 3.0 out of 5), the Tedd session should
be flagged for professor review.

Add a `needs_review` column to the `agent_sessions` table:

```sql
ALTER TABLE agent_sessions ADD COLUMN needs_review INTEGER NOT NULL DEFAULT 0;
```

Update `save_evaluation` in `agent/tool_registry.py` to set this flag:

```python
def save_evaluation(session_id, evaluation, user_id):
    scores = [v['score'] for v in evaluation.values() if 'score' in v]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    threshold = float(os.getenv('HITL_SCORE_THRESHOLD', '3.0'))
    needs_review = 1 if avg_score < threshold else 0

    db.execute(
        """UPDATE agent_sessions
           SET quality_score = ?, finalised = 1, needs_review = ?
           WHERE id = ? AND user_id = ?""",
        (avg_score, needs_review, session_id, user_id)
    )
    return {"saved": True, "average_score": avg_score, "needs_review": bool(needs_review)}
```

The professor GET `/api/professor/sessions` route already returns all
sessions in the cohort. Add `needs_review` to the SELECT so professors
can filter for sessions requiring attention:

```js
const sessions = db
  .prepare(
    `SELECT id, user_id, agent_id, quality_score, finalised, needs_review, created_at
     FROM agent_sessions
     WHERE cohort_id = ?
     ORDER BY needs_review DESC, created_at DESC`
  )
  .all(req.user.cohortId);
```

Ordering by `needs_review DESC` puts flagged sessions at the top of the
professor's list. No new route is needed: the existing endpoint surfaces
the information.

---

## Failure Logging Standard

Every failure in the orchestrator must log the same fields:

```js
console.error(JSON.stringify({
  event: 'agent_failure',
  user_id: user.id,
  stage: stage,
  agent_selected: stage.toLowerCase(),
  error_type: err.code || err.status || 'unknown',
  error_message: err.message,
  retry_count: retryCount,
  timestamp: new Date().toISOString(),
}));
```

Structured JSON logs can be filtered and queried in any logging platform.
Free-form strings cannot. Adopting structured logging now costs nothing and
saves significant debugging time in production.

---

## Environment Variable

Add to `.env` and `.env.example`:

```
HITL_SCORE_THRESHOLD=3.0
```

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code already
knows the agent runner pattern from your CLAUDE.md and the tool_registry.py
structure from Session 03.

**Prompt to add failure handling and HITL:**

```
Add failure handling and the HITL hook to the SCQ platform.

1. In agent/runner.py, wrap the client.messages.create call in a
   call_with_retry function that retries once after 1 second on 529 status
   errors. Do not retry on 400 or 401. Raise the error after one failed retry.

2. In server/src/lib/agentCaller.js (the streamAgent function):
   - Buffer stderr output into a stderrBuffer string
   - Listen for python.on('close', code) and if code !== 0, write a structured
     SSE error event with { error: true, message: '...' } and end the response
   - Listen for req.on('close') and kill the python process if it is still running
   - Call appendTurn only in the stdout 'end' handler, not in the 'close' handler

3. Run the db schema migration to add the needs_review column:
   ALTER TABLE agent_sessions ADD COLUMN needs_review INTEGER NOT NULL DEFAULT 0;
   Add this to server/src/db-init.js so new installs include it.

4. In agent/tool_registry.py, update the save_evaluation function to:
   - Calculate the average score from the evaluation fields
   - Compare it to float(os.getenv('HITL_SCORE_THRESHOLD', '3.0'))
   - Set needs_review = 1 in the UPDATE if below threshold
   - Include needs_review in the returned dict

5. In server/src/routes/professor.js, add needs_review to the SELECT columns
   and ORDER BY needs_review DESC, created_at DESC.

Log all failures with structured JSON including user_id, stage, error_type,
and timestamp. Never write stack traces or full error messages to the client.
```

**What Claude Code will do:**
Update the Python runner with retry logic, update the Node streaming wrapper
with clean error handling and process kill on disconnect, add the schema
migration, update the save_evaluation tool, and update the professor route.

**Tips for this document:**
- Test the retry by temporarily setting the model to a nonexistent model ID
  in `model_config.py`. This produces a 404 (not a 529), so the retry should
  not fire. Confirm you see exactly one attempt in the logs.
- To test the student disconnect handling, start a long agent call and close
  the browser tab. Check the server logs: you should see the "client
  disconnected, killed agent process" message.
- Tell Claude Code: "The needs_review column must be added to db-init.js so
  it is created on fresh installs. Do not rely on the ALTER TABLE migration
  alone."

---

**Next session:** [Session 06 - Production and Deployment](../Session-06%20(Production%20and%20Deployment)/00-session-overview.md)

---

Copyright Janna AI Research Labs
