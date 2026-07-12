# Assignment 03: Implement JWT Authentication

**What you are building:** A login route that issues JWT tokens and a role guard that blocks students from professor-only routes
**Why it matters:** Without authentication, any person who discovers your API URL can send messages to your agents. Without role guards, a student can access cohort data that belongs to a professor. This assignment closes both gaps.
**Time estimate:** 45 minutes
**Reads with:** 03-jwt-and-authentication.md

---

## What You Are Going To Do

You are going to create a login route, a user creation script for testing, a role guard middleware, and apply both to your Express app. By the end, only users with a valid token can reach the agent routes.

---

## What Authentication Must Do

A correct JWT implementation has three properties:

```
1. Algorithm is pinned      algorithms: ['HS256'] on every verify call - never omit
2. Secret is in .env        Never hardcoded in source, never committed to git
3. Role is in the payload   So role guards can read it without a database call
```

If any of these is missing, the authentication is broken in a way that may not cause an immediate error but creates a security vulnerability.

---

## Step 1: Install bcrypt

```bash
cd server && npm install bcrypt
```

---

## Step 2: Write the Login Route

Create `server/src/routes/auth.js`:

```js
const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const db = require('../db').db;

const router = express.Router();

router.post('/login', async (req, res) => {
    const { email, password } = req.body;

    if (!email || !password) {
        return res.status(400).json({ error: 'Email and password are required.' });
    }

    const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email);

    if (!user) {
        return res.status(401).json({ error: 'Invalid credentials.' });
    }

    const valid = await bcrypt.compare(password, user.password_hash);

    if (!valid) {
        return res.status(401).json({ error: 'Invalid credentials.' });
    }

    const token = jwt.sign(
        { id: user.id, email: user.email, role: user.role, cohort_id: user.cohort_id },
        process.env.JWT_SECRET,
        { expiresIn: process.env.JWT_EXPIRY || '8h', algorithm: 'HS256' }
    );

    res.json({ token });
});

module.exports = router;
```

Two things to notice:
- Both a wrong email and a wrong password return the same error message. An attacker cannot tell which one failed.
- `bcrypt.compare` is async. Never use `bcrypt.compareSync` in a route handler. It blocks the Node.js event loop during the comparison.

---

## Step 3: Write the Role Guard

Create `server/src/middleware/roleGuard.js`:

```js
function requireRole(...roles) {
    return (req, res, next) => {
        if (!req.user) {
            return res.status(401).json({ error: 'Authentication required.' });
        }
        if (!roles.includes(req.user.role)) {
            return res.status(403).json({ error: 'Insufficient permissions.' });
        }
        next();
    };
}

module.exports = { requireRole };
```

Usage: `requireRole('professor')` or `requireRole('professor', 'admin')`.
The guard comes after `authMiddleware` in any route that needs role checking.

---

## Step 4: Register Routes in index.js

Update `server/src/index.js`:

```js
const authRoutes = require('./routes/auth');
app.use('/api/auth', authRoutes);
```

---

## Step 5: Create a Test User

Create `server/scripts/create-user.js`:

```js
const bcrypt = require('bcrypt');
const { v4: uuidv4 } = require('uuid');
const db = require('../src/db').db;

async function createUser(email, password, role, cohortId) {
    const hash = await bcrypt.hash(password, 12);
    const id = uuidv4();
    db.prepare(
        'INSERT INTO users (id, email, password_hash, role, cohort_id) VALUES (?, ?, ?, ?, ?)'
    ).run(id, email, hash, role, cohortId);
    console.log(`Created: ${email} (${role}) cohort=${cohortId}`);
}

createUser('student@hult.edu', 'TestPass123!', 'student', 'cohort-a');
createUser('professor@hult.edu', 'TestPass123!', 'professor', 'cohort-a');
```

Install uuid first: `npm install uuid`

Run it: `node server/scripts/create-user.js`

---

## Step 6: Test Login and Role Guard

Get a token:

```bash
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@hult.edu","password":"TestPass123!"}'
```

Copy the token value and test the agent route:

```bash
curl -N -X POST http://localhost:3001/api/agent1/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "My situation is..."}'
```

Test that no token returns 401:

```bash
curl -X POST http://localhost:3001/api/agent1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

Expected response: `{"error":"Missing or malformed token"}`

---

## You Are Done When

- [ ] POST /api/auth/login returns a token for valid credentials
- [ ] A request with a bad password gets 401 with a generic error message
- [ ] A request with no Authorization header gets 401
- [ ] A request with a valid student token reaches the agent
- [ ] cost factor 12 is used in bcrypt.hash (not 10, not 8)
- [ ] bcrypt.compare (async) is used, not bcrypt.compareSync
- [ ] algorithms: ['HS256'] appears in the jwt.verify call in auth middleware

---

## If You Get Stuck

Login returns 401 even with the correct password: the password was hashed with a different secret or a different cost factor. Delete the user from the database and recreate it with the create-user script.

Token is rejected by the agent route: the JWT_SECRET in .env may not match what was used to sign the token. Confirm the server restarted after you edited .env.

Role guard is not applied to the right routes: the middleware order matters. authMiddleware must run before requireRole. If requireRole runs first, req.user is undefined.

---

## Next Assignment

[04-decompose-your-task.md](04-decompose-your-task.md)

---

Copyright Janna AI Research Labs
