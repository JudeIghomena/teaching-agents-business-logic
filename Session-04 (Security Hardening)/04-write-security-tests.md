# Build 04: Write the Security Test Suite

**Frameworks applied:** 11 (Security Baseline) + 10 (Observability)

---

## Why Security Tests Are Not Optional

The security controls in Builds 01, 02, and 03 are middleware functions
and SQL conditions. Middleware is wired manually in JavaScript files. SQL
conditions are written by hand in route handlers. Neither is enforced by
the type system or the compiler.

A future developer adding a new route can easily forget to apply
`authMiddleware`. A refactor of `db.js` can accidentally drop the
`user_id = ?` condition from a query. A merge conflict can remove a
role guard. These are not hypothetical failures: they happen in real
codebases and produce real security incidents.

Tests catch these regressions before they reach production. A test that
verifies a route returns 401 without a token will fail the moment someone
removes the auth middleware from that route. The test becomes a permanent
alarm.

This connects to Framework 10 (Observability). Observability is not just
logging and metrics: it is the complete set of instruments that give you
confidence in the system's behaviour. Security tests are observability
for your access control layer.

---

## What the Test Suite Covers

Three categories, run in this order because each builds on the previous:

**Category 1: Authentication**

These tests verify that every protected route rejects unauthenticated
requests. The goal is to confirm that `authMiddleware` is wired on every
route it should be.

- Request with no Authorization header returns 401
- Request with a malformed token (`Authorization: Bearer garbage`) returns 401
- Request with a token signed with the wrong secret returns 401
- Request to the auth endpoint itself works without a token (it is public)

**Category 2: Role Guards**

These tests verify that role-restricted routes reject users with the wrong
role. The goal is to confirm that `requireRole` is applied correctly.

- Student JWT hitting a professor-only route returns 403
- Professor JWT hitting an agent route returns 200 (professors can also chat
  if your application permits this, or 403 if not: document the decision)
- Admin JWT hitting all routes returns the appropriate status

**Category 3: IDOR Probes**

These tests verify that a user cannot access another user's data. The goal
is to confirm that every database query is scoped correctly.

- Student A logs in and creates a Matteo session (session_id returned)
- Student B logs in with a different JWT
- Student B sends a request referencing student A's session_id
- The response is 404, not 200

---

## The Test File

Create `server/tests/security.test.js`:

```js
import { describe, it, expect, beforeAll } from 'vitest';
import request from 'supertest';
import { buildApp } from '../src/app.js';
import { initTestDb, teardownTestDb } from './helpers/testDb.js';

let app;

beforeAll(async () => {
  await initTestDb();
  app = buildApp();
});

afterAll(async () => {
  await teardownTestDb();
});

// -------------------------------------------------------
// Helpers
// -------------------------------------------------------

async function loginAs(email, password) {
  const res = await request(app)
    .post('/api/auth/login')
    .send({ email, password });
  return res.body.token;
}

// -------------------------------------------------------
// Category 1: Authentication
// -------------------------------------------------------

describe('Authentication', () => {
  it('returns 401 with no Authorization header', async () => {
    const res = await request(app).post('/api/agent1/chat').send({ message: 'hello' });
    expect(res.status).toBe(401);
  });

  it('returns 401 with a malformed token', async () => {
    const res = await request(app)
      .post('/api/agent1/chat')
      .set('Authorization', 'Bearer not.a.jwt')
      .send({ message: 'hello' });
    expect(res.status).toBe(401);
  });

  it('returns 401 with a token signed by the wrong secret', async () => {
    const fakeToken = 'eyJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOiJmYWtlIn0.wrongsig';
    const res = await request(app)
      .post('/api/agent1/chat')
      .set('Authorization', `Bearer ${fakeToken}`)
      .send({ message: 'hello' });
    expect(res.status).toBe(401);
  });

  it('login endpoint returns 200 without a token', async () => {
    const res = await request(app)
      .post('/api/auth/login')
      .send({ email: 'student@test.edu', password: 'TestPass123!' });
    expect(res.status).toBe(200);
    expect(res.body.token).toBeDefined();
  });

  it('login returns 401 with wrong password', async () => {
    const res = await request(app)
      .post('/api/auth/login')
      .send({ email: 'student@test.edu', password: 'wrongpassword' });
    expect(res.status).toBe(401);
  });
});

// -------------------------------------------------------
// Category 2: Role Guards
// -------------------------------------------------------

describe('Role guards', () => {
  it('student JWT returns 403 on professor route', async () => {
    const token = await loginAs('student@test.edu', 'TestPass123!');
    const res = await request(app)
      .get('/api/professor/sessions')
      .set('Authorization', `Bearer ${token}`);
    expect(res.status).toBe(403);
  });

  it('professor JWT returns 200 on professor sessions route', async () => {
    const token = await loginAs('professor@test.edu', 'ProfPass123!');
    const res = await request(app)
      .get('/api/professor/sessions')
      .set('Authorization', `Bearer ${token}`);
    expect(res.status).toBe(200);
  });
});

// -------------------------------------------------------
// Category 3: IDOR Probes
// -------------------------------------------------------

describe('IDOR prevention', () => {
  it('student B cannot finalise student A session', async () => {
    const tokenA = await loginAs('student@test.edu', 'TestPass123!');
    const tokenB = await loginAs('student2@test.edu', 'TestPass123!');

    // Student A starts a Tedd session
    const chatRes = await request(app)
      .post('/api/agent3/chat')
      .set('Authorization', `Bearer ${tokenA}`)
      .send({ message: 'My deliverable: ...' });

    const sessionId = chatRes.body.sessionId;
    expect(sessionId).toBeDefined();

    // Student B tries to finalise student A's session via professor route
    // (this also tests that student B cannot impersonate a professor)
    const res = await request(app)
      .patch(`/api/professor/sessions/${sessionId}/finalise`)
      .set('Authorization', `Bearer ${tokenB}`);

    // Must be 403 (not a professor) or 404 (session not in their cohort)
    expect([403, 404]).toContain(res.status);
  });

  it('student B cannot read student A Matteo session by ID', async () => {
    const tokenA = await loginAs('student@test.edu', 'TestPass123!');
    const tokenB = await loginAs('student2@test.edu', 'TestPass123!');

    // Student A creates a session
    await request(app)
      .post('/api/agent1/chat')
      .set('Authorization', `Bearer ${tokenA}`)
      .send({ message: 'I am setting up my SCQ.' });

    // Get the session ID (assumes your route returns it)
    const sessionsRes = await request(app)
      .get('/api/agent1/session')
      .set('Authorization', `Bearer ${tokenA}`);
    const sessionId = sessionsRes.body.sessionId;

    // Student B tries to access it
    const res = await request(app)
      .get(`/api/agent1/session/${sessionId}`)
      .set('Authorization', `Bearer ${tokenB}`);

    expect(res.status).toBe(404);
  });
});
```

---

## The Test Helpers

The test file imports two helper functions: `initTestDb` and
`teardownTestDb`. These set up an in-memory (or temp-file) SQLite
database for the test run and tear it down afterwards.

Create `server/tests/helpers/testDb.js`:

```js
import Database from 'better-sqlite3';
import { setTestDb } from '../../src/db.js';

let db;

export function initTestDb() {
  db = new Database(':memory:');
  setTestDb(db);

  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'student',
      cohort_id TEXT NOT NULL,
      created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS agent_sessions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      cohort_id TEXT NOT NULL,
      agent_id TEXT NOT NULL,
      messages TEXT NOT NULL DEFAULT '[]',
      quality_score REAL,
      finalised INTEGER NOT NULL DEFAULT 0,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );
  `);

  // Seed test users
  const bcrypt = await import('bcrypt');
  const hash = await bcrypt.hash('TestPass123!', 12);
  const profHash = await bcrypt.hash('ProfPass123!', 12);

  db.prepare(`INSERT INTO users VALUES (?,?,?,?,?,datetime('now'))`)
    .run('student-1', 'student@test.edu', hash, 'student', 'cohort-A');

  db.prepare(`INSERT INTO users VALUES (?,?,?,?,?,datetime('now'))`)
    .run('student-2', 'student2@test.edu', hash, 'student', 'cohort-A');

  db.prepare(`INSERT INTO users VALUES (?,?,?,?,?,datetime('now'))`)
    .run('prof-1', 'professor@test.edu', profHash, 'professor', 'cohort-A');
}

export function teardownTestDb() {
  if (db) {
    db.close();
  }
}
```

This requires a `setTestDb` export from `server/src/db.js` that lets the
test suite inject a test database. Add this to `db.js`:

```js
let _db = null;

export function setTestDb(testDb) {
  _db = testDb;
}

function getDb() {
  if (_db) return _db;
  if (!_instance) {
    _instance = new Database(process.env.DB_PATH || 'data/scq.db');
    _instance.pragma('journal_mode = WAL');
  }
  return _instance;
}
```

---

## Running the Tests

```bash
cd server && npm test
```

The test output shows each category clearly. All tests must pass with zero
failures before any commit that touches auth, middleware, or database queries.

If a test fails:
- Auth test failing: check that `authMiddleware` is applied to the route
- Role test failing: check that `requireRole` is applied with the correct role
- IDOR test failing: check that the query includes both `id = ?` and `user_id = ?`

---

**Next:** [05-run-the-security-audit.md](05-run-the-security-audit.md)

---

Copyright Janna AI Research Labs
