# Assignment 04: Write the Security Test Suite

**Reads with:** [04-write-security-tests.md](../04-write-security-tests.md)
**Time estimate:** 60-90 minutes
**Frameworks applied:** 11 (Security Baseline) + 10 (Observability)

---

## What You Are Building

A security test file covering authentication, role guards, and IDOR. All
tests run with `npm test`. All must pass before any commit that touches
auth, middleware, or database queries.

---

## Steps

### Step 1: Prepare the app for testing

The test suite needs to inject a test database so it does not touch the
production `scq.db`. To enable this, `server/src/db.js` needs a way to
accept an injected database instance.

Add a `setTestDb` export to `server/src/db.js`:

```js
let _testDb = null;

export function setTestDb(db) {
  _testDb = db;
}

function getDb() {
  if (_testDb) return _testDb;
  // ... rest of existing singleton logic
}
```

Make sure `getDb` is used internally by all exported functions (`appendTurn`,
`getOrCreateSession`, etc.) rather than accessing a module-level `db`
variable directly.

Also export a `buildApp` function from `server/src/app.js` (or `index.js`)
that creates and returns the configured Express app without calling
`app.listen`. This lets the test runner import the app and pass it to
supertest without starting an actual server.

### Step 2: Create the test helpers

Create `server/tests/helpers/testDb.js` with two exports:

- `initTestDb()`: creates an in-memory SQLite database, calls `setTestDb`,
  runs the schema migrations, and seeds three test users: one student
  (`student@test.edu`, password `TestPass123!`, role `student`), a second
  student (`student2@test.edu`, same password), and one professor
  (`professor@test.edu`, password `ProfPass123!`, role `professor`)
- `teardownTestDb()`: closes the database

Seed passwords must be hashed with `bcrypt.hash('TestPass123!', 12)` at
setup time, not hardcoded as hashes in the file (hardcoded hashes break
if the cost factor changes).

### Step 3: Create the security test file

Create `server/tests/security.test.js`.

The file has three `describe` blocks:

**Authentication (5 tests):**
- No Authorization header returns 401
- Malformed token (`Bearer notajwt`) returns 401
- Token signed with wrong secret returns 401
- Login endpoint returns 200 without a token and the response body
  contains a `token` field
- Login with wrong password returns 401

**Role guards (2 tests):**
- Student JWT on GET /api/professor/sessions returns 403
- Professor JWT on GET /api/professor/sessions returns 200

**IDOR prevention (1 test minimum):**
- Student A sends a message to agent1, captures the session ID from the
  response body, then student B attempts to retrieve that session by ID.
  The response must be 404, not 200.

Read the full test file in the build document. Write the tests yourself
rather than copying them. Each test has a comment explaining what it is
testing and why that test is required.

### Step 4: Run the tests

```bash
cd server && npm test
```

All tests must pass with zero failures. If any test fails:

- Auth test failing: check that `authMiddleware` is applied to the route
  and that the JWT secret in the test environment matches `JWT_SECRET`
- Role test failing: check that `requireRole('professor')` is applied in
  the professor route
- IDOR test failing: check that the route returns 404 (not 200 or 403)
  when a user requests a session they do not own

### Step 5: Verify the tests catch real regressions

Temporarily remove `authMiddleware` from one route in `agent1.js`. Run
the tests. The auth tests for that route should fail.

Restore the middleware. Confirm the tests pass again.

This step proves the tests are testing what you think they are testing.
A test that passes regardless of whether the control is in place is not
a security test: it is a false assurance.

---

## Done Checklist

- [ ] `server/src/db.js` exports `setTestDb` function
- [ ] Express app is exported from a `buildApp` function, separated from
  `app.listen`
- [ ] `server/tests/helpers/testDb.js` exists with `initTestDb` and
  `teardownTestDb`
- [ ] Test database seeded with student, student2, and professor users
- [ ] `server/tests/security.test.js` exists with three describe blocks
- [ ] Authentication: 5 tests covering no token, bad token, wrong secret,
  public login endpoint, wrong password
- [ ] Role guards: student gets 403 on professor route, professor gets 200
- [ ] IDOR: student B gets 404 accessing student A's session
- [ ] `npm test` passes with zero failures and zero skipped tests
- [ ] Verified that removing auth middleware causes the relevant test to fail

---

## Troubleshooting

Tests cannot import the app: Confirm `package.json` has `"type": "module"`
or that your vitest config handles ESM. If using CommonJS, change imports
to `require`.

bcrypt async in test helpers: `bcrypt.hash` returns a Promise. The
`initTestDb` function must be `async` and use `await bcrypt.hash(...)`.
If the test runner calls `initTestDb()` without awaiting it, the users
may not be seeded before the tests run. Use `beforeAll(async () => { await
initTestDb(); })`.

IDOR test returning 200: The route is not applying the IDOR fix from
Assignment 03. Go back and confirm the database query includes
`AND user_id = ?`.

IDOR test returning 403 instead of 404: The route is returning forbidden
instead of not-found. Update it to return 404 for any session that is not
found for the authenticated user, regardless of whether it exists for
someone else.

---

**Next assignment:** [05-run-the-security-audit.md](05-run-the-security-audit.md)
