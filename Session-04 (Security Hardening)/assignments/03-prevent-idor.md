# Assignment 03: Prevent IDOR

**Reads with:** [03-prevent-idor.md](../03-prevent-idor.md)
**Time estimate:** 45-60 minutes
**Frameworks applied:** 11 (Security Baseline) + 09 (Memory and State)

---

## What You Are Building

An audit of every database query in the platform. Every query that reads,
updates, or deletes from `agent_sessions` must include a scope condition
binding the result to the authenticated user or cohort.

---

## Steps

### Step 1: Run the grep check

Before making any changes, run this to find all queries that read from
`agent_sessions` by `id`:

```bash
grep -rn "WHERE id = ?" server/src/
```

Write down every file and line number that appears. These are your targets.

Also run:

```bash
grep -rn "agent_sessions" server/src/
```

Review every query this returns. For each one, ask: does it include a
`user_id = ?` or `cohort_id = ?` condition, or is the row being read from
user input without ownership verification?

### Step 2: Audit db.js

Go through each function in `server/src/db.js`:

For `getOrCreateSession`: confirm it looks up by `user_id` and `agent_id`,
not by `id`. The `id` should only appear in a SELECT immediately after an
INSERT that belongs to the current user.

For `appendTurn`: this accepts a `sessionId` from the calling route. Confirm
that the calling route obtained this `sessionId` from a query that was already
scoped to `req.user.id`. If the `sessionId` ever comes from `req.body` or
`req.params` without prior ownership verification, add that verification.

For `getStudentProgress`: confirm it scopes by `user_id`. It should look like:

```js
export function getStudentProgress(userId) {
  return db
    .prepare(
      `SELECT messages FROM agent_sessions
       WHERE user_id = ? AND agent_id = 'matteo'
       ORDER BY created_at DESC LIMIT 1`
    )
    .get(userId);
}
```

For `getJuliSession`: confirm it scopes by `user_id`. It should look like:

```js
export function getJuliSession(userId) {
  return db
    .prepare(
      `SELECT * FROM agent_sessions
       WHERE user_id = ? AND agent_id = 'juli'
       ORDER BY created_at DESC LIMIT 1`
    )
    .get(userId);
}
```

For any function that updates a session: confirm the UPDATE includes
`AND user_id = ?`. An UPDATE that uses only `WHERE id = ?` can be
exploited if an attacker guesses another user's session ID.

### Step 3: Audit all three agent routes

In each of `agent1.js`, `agent2.js`, `agent3.js`:

- Confirm that `req.user.id` (from the verified JWT) is passed to all
  database functions, not any ID from `req.body` or `req.params`
- Confirm that the result of `getOrCreateSession` is used to get the
  session ID rather than accepting a session ID from the client

### Step 4: Audit professor.js

In `routes/professor.js`:

For the GET sessions route: confirm it selects WHERE `cohort_id = ?`
using `req.user.cohortId`.

For the PATCH finalise route: confirm the UPDATE uses
`WHERE id = ? AND cohort_id = ?` using both `req.params.id` and
`req.user.cohortId`. If `result.changes === 0`, return 404.

### Step 5: Fix any queries that fail the audit

If you find a query that reads `agent_sessions` by `id` alone without a
scope condition, update it to include the scope. Return 404 (not 403)
if the scoped query returns no rows.

Pattern for student routes:

```js
const session = db
  .prepare('SELECT * FROM agent_sessions WHERE id = ? AND user_id = ?')
  .get(sessionId, req.user.id);

if (!session) {
  return res.status(404).json({ error: 'Session not found.' });
}
```

Pattern for professor routes:

```js
const result = db
  .prepare('UPDATE agent_sessions SET finalised = 1 WHERE id = ? AND cohort_id = ?')
  .run(req.params.id, req.user.cohortId);

if (result.changes === 0) {
  return res.status(404).json({ error: 'Session not found.' });
}
```

### Step 6: Run the grep check again

```bash
grep -rn "WHERE id = ?" server/src/
```

Every result must now be followed by an `AND user_id = ?` or
`AND cohort_id = ?` condition, or be a query where the ID was produced by
the server (not received from the client) in the same function call.

---

## Done Checklist

- [ ] Ran `grep -rn "agent_sessions" server/src/` and reviewed every hit
- [ ] `getOrCreateSession` looks up by `user_id` and `agent_id`, not by `id`
  from user input
- [ ] `getStudentProgress` and `getJuliSession` scope by `user_id`
- [ ] Any UPDATE on `agent_sessions` includes `user_id = ?` or
  `cohort_id = ?` in the WHERE clause
- [ ] Professor GET route scopes by `req.user.cohortId`
- [ ] Professor PATCH route scopes UPDATE by both `id` and `cohort_id`,
  returns 404 if `result.changes === 0`
- [ ] No query uses an `id` received from `req.body` or `req.params` without
  a scope condition
- [ ] All 404 responses for not-found scoped queries return `{ error: 'Session not found.' }`
- [ ] Grep check after fixes: every `WHERE id = ?` is followed by a scope condition

---

## Troubleshooting

Update returns 0 changes even for valid session: Confirm the `cohort_id`
in the JWT payload matches the value stored in `agent_sessions.cohort_id`
for that session. If they were created with different cohort IDs, the scope
condition will not match.

Professor seeing sessions from other cohorts: The GET route is likely missing
the `WHERE cohort_id = ?` condition or using the wrong value. Confirm that
`req.user.cohortId` comes from the verified JWT payload.

Session not found for valid student: Confirm that `getOrCreateSession` is
called with `req.user.id` and not with a value from `req.body`. If the
user ID in the JWT does not match the user ID stored on the session, the
scoped query returns nothing.

---

**Next assignment:** [04-write-security-tests.md](04-write-security-tests.md)
