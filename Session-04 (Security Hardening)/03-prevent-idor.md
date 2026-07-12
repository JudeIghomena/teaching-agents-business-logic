# Build 03: Prevent IDOR

**Frameworks applied:** 11 (Security Baseline) + 09 (Memory and State)

---

## What IDOR Is

IDOR stands for Insecure Direct Object Reference. It is one of the most
common and most damaging vulnerabilities in web applications, and it is
simple to explain: a user changes the ID in a request to access someone
else's data.

On the SCQ platform, every student has agent sessions stored in the
`agent_sessions` table. Each session has an integer `id`. If a route
looks up a session by `id` alone:

```sql
SELECT * FROM agent_sessions WHERE id = ?
```

Then student A can fetch student B's Matteo session, Juli session, or
Tedd evaluation simply by trying different numbers. The database will
return the row regardless of who owns it.

This is not a hypothetical risk. On any multi-student platform where
sessions are numbered sequentially, an attacker can enumerate all sessions
by incrementing the ID. The fix is one additional condition in every query:

```sql
SELECT * FROM agent_sessions WHERE id = ? AND user_id = ?
```

The second condition means the session is only returned if it belongs to
the user making the request. A different user sending the same `id` gets
no rows back.

---

## Why This Connects to Framework 09 (Memory and State)

Framework 09 covers how agents store and retrieve state. The design
decision in Session 02 was to store all session state in a relational
database (SQLite) with an explicit `user_id` column on every session row.

That design decision was made precisely to enable this fix. The `user_id`
is there. Every row in `agent_sessions` has one. The only question is
whether every query in the application uses it.

The vulnerability is not in the schema: the schema is correct. The
vulnerability is in any query that omits the `user_id` condition. This
document audits every such query and confirms that none are missing.

---

## The Safe Response Pattern: 404 Not 403

When a user requests a resource they do not own, the correct HTTP status is
404 (Not Found), not 403 (Forbidden).

Returning 403 tells an attacker that the resource exists and that they lack
permission to access it. This leaks information: the attacker now knows the
session ID is valid and belongs to someone.

Returning 404 reveals nothing. The resource does not exist as far as this
user is concerned. The attacker cannot distinguish "wrong ID" from "ID you
don't own" and cannot enumerate which IDs are valid.

Apply this consistently: wherever a query returns zero rows because of an
IDOR check, respond with 404.

---

## The Audit: Every Query That Needs Scoping

Go through each server-side file and confirm that every SELECT, UPDATE, and
DELETE on `agent_sessions` includes both `id = ?` and `user_id = ?`.

### db.js

The `getOrCreateSession` function finds or creates the current student's
session for a given agent. It must scope by `user_id`:

```js
export function getOrCreateSession(userId, agentId, cohortId) {
  let session = db
    .prepare(
      `SELECT * FROM agent_sessions
       WHERE user_id = ? AND agent_id = ?
       ORDER BY created_at DESC LIMIT 1`
    )
    .get(userId, agentId);

  if (!session) {
    const result = db
      .prepare(
        `INSERT INTO agent_sessions (user_id, agent_id, cohort_id, messages)
         VALUES (?, ?, ?, '[]')`
      )
      .run(userId, agentId, cohortId);
    session = db
      .prepare('SELECT * FROM agent_sessions WHERE id = ?')
      .get(result.lastInsertRowid);
  }

  return session;
}
```

This is safe. The SELECT looks up by `user_id` and `agent_id`, not by `id`.
The INSERT includes `user_id`. The final SELECT by `id` is safe here because
the `id` was just returned by the INSERT of the current user's row.

The `appendTurn` function updates by `id`:

```js
export function appendTurn(sessionId, role, content) {
  const session = db
    .prepare('SELECT messages FROM agent_sessions WHERE id = ?')
    .get(sessionId);
  ...
  db.prepare('UPDATE agent_sessions SET messages = ? WHERE id = ?')
    .run(JSON.stringify(messages), sessionId);
}
```

This function is called from routes that already have the session record
(obtained via `getOrCreateSession`). The session ID was retrieved using the
authenticated user's ID, so it belongs to that user. The `appendTurn`
function itself does not need user scoping because the caller already
verified ownership.

However, if you ever expose a route that accepts `sessionId` directly from
the request body or query string and passes it to `appendTurn`, you must
scope the initial lookup by user ID before calling `appendTurn`.

### routes/agent1.js, agent2.js, agent3.js

These routes use `getOrCreateSession(req.user.id, 'matteo', req.user.cohortId)`.
The user ID comes from the verified JWT payload, not from the request body.
This is the correct pattern.

If any route has code like this:

```js
const sessionId = req.body.sessionId;
const session = db.prepare('SELECT * FROM agent_sessions WHERE id = ?').get(sessionId);
```

That is an IDOR vulnerability. Replace it with:

```js
const sessionId = req.body.sessionId;
const session = db
  .prepare('SELECT * FROM agent_sessions WHERE id = ? AND user_id = ?')
  .get(sessionId, req.user.id);

if (!session) {
  return res.status(404).json({ error: 'Session not found.' });
}
```

### routes/professor.js

Professor routes must scope by `cohort_id`, not `user_id`. A professor
should see all sessions in their cohort, not just their own. But they must
not see sessions in other cohorts.

```js
router.get('/sessions', authMiddleware, requireRole('professor'), (req, res) => {
  const sessions = db
    .prepare(
      `SELECT s.id, s.user_id, s.agent_id, s.quality_score, s.finalised, s.created_at
       FROM agent_sessions s
       WHERE s.cohort_id = ?
       ORDER BY s.created_at DESC`
    )
    .all(req.user.cohortId);

  res.json({ sessions });
});
```

The `cohort_id` comes from `req.user.cohortId`, which is in the verified
JWT. A professor cannot change this by modifying the request: the JWT is
signed and its contents are verified server-side.

The PATCH route that finalises a session must scope to the cohort:

```js
router.patch('/sessions/:id/finalise', authMiddleware, requireRole('professor'), (req, res) => {
  const result = db
    .prepare(
      `UPDATE agent_sessions SET finalised = 1
       WHERE id = ? AND cohort_id = ?`
    )
    .run(req.params.id, req.user.cohortId);

  if (result.changes === 0) {
    return res.status(404).json({ error: 'Session not found.' });
  }

  res.json({ finalised: true });
});
```

If `result.changes === 0`, either the session ID does not exist, or it
exists but belongs to a different cohort. Either way, return 404.

---

## The Grep Check

Before committing, grep the server source to find any query that reads
`agent_sessions` by `id` without a scope column:

```bash
grep -rn "WHERE id = ?" server/src/
```

Every hit should be followed by `AND user_id = ?` or `AND cohort_id = ?`.
Any hit that is followed only by `id = ?` is a potential IDOR vulnerability
and must be reviewed before committing.

---

## Summary: The IDOR Rule

Write it into your CLAUDE.md and never deviate:

Every query on `agent_sessions` must include a scope condition:
- Student routes: `WHERE id = ? AND user_id = ?`
- Professor routes: `WHERE ... AND cohort_id = ?`
- Unscopeable queries (after INSERT, reading your own new row): acceptable
  only when the ID was produced in the same function, not from user input.

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code already
knows from your CLAUDE.md that every query on `agent_sessions` must include a
scope condition. Use Claude Code to perform the audit and apply the fixes.

**Prompt to audit and fix IDOR vulnerabilities:**

```
Audit the SCQ platform for IDOR vulnerabilities in database queries.

1. Search all files under server/src/ for queries that read, update, or delete
   from agent_sessions.

2. For each query found:
   - If it is a SELECT or UPDATE/DELETE that uses a session ID from
     req.body or req.params, confirm it includes AND user_id = ? (for student
     routes) or AND cohort_id = ? (for professor routes).
   - If the user_id or cohort_id scope condition is missing, add it.
   - If a scoped query returns zero rows, the route must return 404 with
     { error: 'Session not found.' } - not 403.

3. In routes/professor.js, confirm the PATCH /sessions/:id/finalise route
   updates with WHERE id = ? AND cohort_id = ? and checks result.changes === 0
   to return 404.

4. Run this grep after making changes and report the results:
   grep -rn "WHERE id = ?" server/src/
   Every result must be followed by AND user_id = ? or AND cohort_id = ?

Do not change any query that obtains its session ID from the server's own
INSERT (lastInsertRowid), only queries that receive an ID from the client.
```

**What Claude Code will do:**
Read every file under `server/src/`, find all queries touching `agent_sessions`,
add missing scope conditions, update route handlers to return 404 on empty
results, and run the grep check to confirm no unscoped queries remain.

**Tips for this document:**
- Ask Claude Code: "Show me every place where agent_sessions is queried in
  db.js and in the route files." Review the list before asking it to make
  changes so you understand what is about to be touched.
- If Claude Code returns 403 instead of 404 for an unowned resource, tell it:
  "The correct response is 404, not 403. 403 reveals that the resource exists.
  Change all IDOR guards to return 404."
- Tell Claude Code: "Do not add user_id scoping to the INSERT in
  getOrCreateSession or to the SELECT that reads the newly inserted row by
  lastInsertRowid. Those do not need it. Only add scoping to queries where
  the ID comes from the client request."

---

**Next:** [04-write-security-tests.md](04-write-security-tests.md)

---

Copyright Janna AI Research Labs
