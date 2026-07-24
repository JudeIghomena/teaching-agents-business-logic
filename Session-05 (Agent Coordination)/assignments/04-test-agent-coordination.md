# Assignment 04: Test Agent Coordination

**Reads with:** [04-test-agent-coordination.md](../04-test-agent-coordination.md)
**Time estimate:** 40-50 minutes
**Frameworks applied:** 10 (Observability) + 08 (Internal Setup)

---

## What You Are Building

An orchestrator test suite that confirms the routing logic routes each student
to the right agent, and that the Matteo handoff delivers the confirmed SCQ to
the functions that need it.

---

## Steps

### Step 1: Add getTestDb to the testDb helper

Open `server/tests/helpers/testDb.js`. Add a `getTestDb` export:

```js
let testDb;

export function initTestDb() { ... } // existing
export function teardownTestDb() { ... } // existing

export function getTestDb() {
  return testDb;
}
```

The `testDb` variable must be assigned inside `initTestDb` so it is
available when `getTestDb` is called in the test file.

### Step 2: Create orchestrator.test.js

Create `server/tests/orchestrator.test.js` using the code in the build
document as your reference.

Write the test from the document, not copy-paste it. Reading and re-typing
forces you to understand each assertion before writing it.

### Step 3: Run the full test suite

```bash
cd server && npm test
```

The output should include:
- Session 04 security tests (8): all pass
- Session 05 orchestrator tests (7): all pass

Total: at least 15 passing.

### Step 4: Fix the common failure mode

If the routing tests pass but the context tests fail, the most common cause
is that `getMatteoHandoff` is reading `messages` as a raw string instead of
a parsed object. Confirm the function calls `JSON.parse(session.messages)`.

If the HTTP test (test 5 in routing block) fails with a 401, the test user
seeded by `initTestDb` has a different `user_id` than the one you inserted
the COMPLETE session for. Align the IDs.

### Step 5: Verify the extended TurnTrace fields

Add a `console.log` to the orchestrator route logging:

```js
console.log('[orchestrator] turn_start', JSON.stringify({
  user_id: user.id,
  stage_before: stage,
  agent_selected: stage.toLowerCase(),
  timestamp: new Date().toISOString(),
}));
```

Send a message to POST /api/chat. Confirm the log line appears with correct
`stage_before` and `agent_selected` values.

---

## Done Checklist

- [ ] `getTestDb()` added to testDb.js helper
- [ ] `server/tests/orchestrator.test.js` created
- [ ] getCurrentStage returns MATTEO for user with no sessions
- [ ] getCurrentStage returns JULI for user with complete Matteo session
- [ ] getCurrentStage returns TEDD for user with Action-stage Juli session
- [ ] getCurrentStage returns COMPLETE for user with finalised Tedd session
- [ ] getMatteoHandoff returns correct SCQ fields for user with Matteo session
- [ ] getMatteoHandoff returns null for user with no Matteo session
- [ ] `npm test` runs all tests with zero failures
- [ ] TurnTrace log lines appear for each orchestrator request

---

## Troubleshooting

Test file cannot import stageManager.js: Confirm the import path uses the
correct relative path from `server/tests/` to `server/src/lib/`. The path
should be `'../src/lib/stageManager.js'`.

Seeded data not visible in getCurrentStage: The test database is separate
from your development database. Call `getTestDb()` and confirm it is the
same db instance used by `stageManager.js`. If stageManager imports the db
singleton from `db.js`, but testDb creates a separate in-memory db, the
functions will read from the dev database, not the test data.

The fix: in `db.js`, export a `setTestDb(db)` function (as introduced in
Session 04) and call it in `initTestDb`. Verify the `setTestDb` call
happens before any test runs.

All 15 tests pass but one: Read the assertion failure message carefully.
Vitest's output shows the received value and expected value side by side.
A mismatched string (COMPLETE vs complete) or a null when an object was
expected tells you exactly what to fix.

---

**Next assignment:** [05-handle-agent-failures.md](05-handle-agent-failures.md)
