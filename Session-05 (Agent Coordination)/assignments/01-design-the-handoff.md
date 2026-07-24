# Assignment 01: Design the Handoff

**Reads with:** [01-design-the-handoff.md](../01-design-the-handoff.md)
**Time estimate:** 30-40 minutes
**Frameworks applied:** 01 (Agent Mental Model) + 09 (Memory and State)

---

## What You Are Building

A stageManager module that derives the student's current coaching stage from
the existing agent_sessions table. No schema changes required.

---

## Steps

### Step 1: Create the stageManager module

Create `server/src/lib/stageManager.js` with three exported functions:
`getCurrentStage`, `isStageComplete`, and `getMatteoHandoff`.

Read the logic in the build document carefully before writing any code. The
check order in `getCurrentStage` matters: Tedd must be checked before Juli,
Juli before Matteo. If the order is reversed, a student with all three agents
active will always be routed to the earliest stage.

### Step 2: Verify getCurrentStage with a manual test

Start the server and open a SQLite shell:

```bash
sqlite3 data/platform.db
```

Insert a test Matteo session with all three SCQ fields:

```sql
INSERT INTO agent_sessions (user_id, cohort_id, agent_id, messages)
VALUES ('test-user-001', 'cohort-test', 'matteo',
  '{"situation":"Revenue dropped","complication":"Unknown cause","question":"How to diagnose?"}');
```

Then add a quick Node.js test script at the project root:

```js
// test-stage.mjs
import { getCurrentStage } from './server/src/lib/stageManager.js';
console.log(getCurrentStage('test-user-001')); // should print: JULI
console.log(getCurrentStage('unknown-user'));   // should print: MATTEO
```

Run it:

```bash
node test-stage.mjs
```

Delete the test script when done.

### Step 3: Verify getMatteoHandoff

Add two more lines to the test script before deleting it:

```js
console.log(getMatteoHandoff('test-user-001'));  // { situation, complication, question }
console.log(getMatteoHandoff('no-such-user'));   // null
```

Confirm the returned object has the correct field values.

### Step 4: Check SQL parameterisation

Open `stageManager.js` and confirm that every `db.prepare()` call uses `?`
placeholders. There must be no string concatenation inside any SQL statement.
Run this grep to verify:

```bash
grep -n "user_id = " server/src/lib/stageManager.js
```

Every match should show `user_id = ?` not `user_id = '${userId}'`.

---

## Done Checklist

- [ ] `server/src/lib/stageManager.js` exists with three named exports
- [ ] `getCurrentStage` checks Tedd first, Juli second, Matteo third
- [ ] Default return value is 'MATTEO' (no sessions found)
- [ ] All SQL uses `?` placeholders, no string concatenation
- [ ] `getMatteoHandoff` returns null when no Matteo session exists
- [ ] Manual test confirms 'JULI' for a user with complete SCQ
- [ ] Test script deleted after verification

---

## Troubleshooting

getCurrentStage always returns MATTEO even after inserting a session: Confirm
the `user_id` in your INSERT matches the value you pass to `getCurrentStage`
exactly. SQLite comparisons are case-sensitive.

getMatteoHandoff returns null for a user that has a session: Check that
`JSON.parse(session.messages || '{}')` is being called before reading the
fields. The `messages` column stores a JSON string, not a parsed object.

Duplicate session rows causing wrong stage: The queries use
`ORDER BY created_at DESC LIMIT 1`. If `created_at` is null on test data,
ordering is undefined. Add a `created_at` value to your INSERT:
`'created_at': datetime('now')`.

---

**Next assignment:** [02-build-the-orchestrator.md](02-build-the-orchestrator.md)
