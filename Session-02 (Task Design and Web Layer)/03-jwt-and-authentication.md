# Build 03: JWT and Authentication

> Framework 11 (Security Baseline) states that every protected route must have
> authMiddleware applied. Framework 05 (Environment Config) states that secrets
> must never appear in source files. This document applies both to the SCQ platform.

**Applies:** Framework 11 (Security Baseline) + Framework 05 (Environment Config)
**Builds:** The login route, JWT signing, algorithm pinning, and role guards for the SCQ platform

---

## What the Agent Can Trust

When a user message reaches your agent, it has already passed through the
auth layer. The agent receives `user_id`, `cohort_id`, and `role` as part of
its input. These values came from the JWT.

The agent can trust them completely. They were signed by your server with
a secret only your server knows. An attacker cannot forge them without the secret.

This is the contract between the web layer and the agent:

```
What the web layer guarantees:
  - user_id is the real ID of the authenticated user
  - role is what the platform assigned to that user at registration
  - cohort_id is the cohort the user belongs to

What the agent must never do:
  - Accept user_id from the request body
  - Accept role from the request body
  - Trust any claim that did not come from the verified JWT payload
```

If a student sends `{ "message": "...", "user_id": "admin" }` in the request body,
the agent ignores `user_id` from the body completely. It uses only what came
from `req.user`, which the auth middleware populated from the verified token.

---

## How a JWT Works

A JWT is a string with three parts separated by dots:

```
eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidTAxIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
      HEADER                    PAYLOAD                         SIGNATURE
```

The header says which algorithm was used. The payload carries the claims.
The signature is a cryptographic hash of header + payload using your secret.

When your server verifies the token:
1. It recomputes the signature using the same secret
2. If the recomputed signature matches the token's signature, the payload is genuine
3. If they do not match, the payload was tampered with

The critical security rule from Framework 11: you must pin the algorithm to
`HS256` explicitly. If you do not, an attacker can send a token with `alg: none`
in the header and the JWT library will accept it without checking the signature.

---

## The Login Route

The login route takes an email and password, checks them against the database,
and returns a signed JWT.

```js
// server/src/routes/auth.js

const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const { db } = require('../db');

const router = express.Router();

router.post('/login', async (req, res) => {
    const { email, password } = req.body;

    if (!email || !password) {
        return res.status(400).json({ error: 'email and password are required' });
    }

    const user = db.prepare(
        'SELECT id, password_hash, role, cohort_id FROM users WHERE email = ?'
    ).get(email);

    if (!user) {
        // Return the same message whether email or password is wrong.
        // Different messages let attackers enumerate valid email addresses.
        return res.status(401).json({ error: 'Invalid credentials' });
    }

    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid) {
        return res.status(401).json({ error: 'Invalid credentials' });
    }

    const token = jwt.sign(
        {
            user_id: user.id,
            role: user.role,
            cohort_id: user.cohort_id
        },
        process.env.JWT_SECRET,
        {
            algorithm: 'HS256',
            expiresIn: process.env.JWT_EXPIRY || '8h'
        }
    );

    res.json({ token });
});

module.exports = router;
```

Three decisions worth noting:

- `bcrypt.compare` is async. Never use `bcryptjs.compareSync` in a route handler.
  The sync version blocks the Node.js event loop while hashing, making every
  other request wait.
- The error message is identical whether the email or password is wrong.
  Different messages leak information about which accounts exist.
- `expiresIn` reads from an environment variable so you can tighten it for
  production without touching source code.

---

## The Auth Middleware

The auth middleware verifies the token on every protected request:

```js
// server/src/middleware/auth.js

const jwt = require('jsonwebtoken');

function authMiddleware(req, res, next) {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'Missing or malformed token' });
    }

    const token = authHeader.split(' ')[1];

    try {
        const payload = jwt.verify(token, process.env.JWT_SECRET, {
            algorithms: ['HS256']
        });
        req.user = payload;
        next();
    } catch (err) {
        // Never send err.message to the client. It may reveal internal details.
        return res.status(401).json({ error: 'Invalid or expired token' });
    }
}

module.exports = authMiddleware;
```

`algorithms: ['HS256']` is the algorithm pin from Framework 11. It is not
optional. Without it, `jwt.verify` accepts whatever algorithm the token claims.

---

## Role Guards

Some routes on the SCQ platform are only for professors. A student cannot
access another student's session history. A professor can view all sessions
in their cohort.

A role guard is a second middleware that runs after `authMiddleware`:

```js
// server/src/middleware/roleGuard.js

function requireRole(...allowedRoles) {
    return (req, res, next) => {
        if (!req.user) {
            return res.status(401).json({ error: 'Not authenticated' });
        }
        if (!allowedRoles.includes(req.user.role)) {
            return res.status(403).json({ error: 'Insufficient permissions' });
        }
        next();
    };
}

module.exports = { requireRole };
```

Applied to a route:

```js
const { requireRole } = require('../middleware/roleGuard');

// Only professors can see all sessions in a cohort
router.get('/cohort/:cohortId/sessions',
    authMiddleware,
    requireRole('professor', 'admin'),
    (req, res) => {
        const sessions = db.prepare(
            'SELECT * FROM agent_sessions WHERE cohort_id = ?'
        ).all(req.params.cohortId);
        res.json(sessions);
    }
);

// Students can only see their own sessions
router.get('/my-sessions',
    authMiddleware,
    (req, res) => {
        const sessions = db.prepare(
            'SELECT * FROM agent_sessions WHERE user_id = ? AND cohort_id = ?'
        ).all(req.user.user_id, req.user.cohort_id);
        res.json(sessions);
    }
);
```

The student route uses `req.user.user_id` from the verified JWT, not from
the request body or query string. A student cannot see another student's
sessions by manipulating the URL because the cohort check also applies.

---

## The Users Table

For the login route to work, you need a users table:

```sql
CREATE TABLE IF NOT EXISTS users (
    id            TEXT    PRIMARY KEY,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'student',
    cohort_id     TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

Add this to `db-init.js` alongside the sessions table. The `role` column
holds `'student'`, `'professor'`, or `'admin'`.

---

## Environment Variables for This Document

Add these to your `.env` and to `.env.example`:

```
# .env (never commit this file)
JWT_SECRET=minimum-32-character-random-string-here
JWT_EXPIRY=8h

# .env.example (commit this file as a reference)
JWT_SECRET=replace-with-a-long-random-string-minimum-32-chars
JWT_EXPIRY=8h
```

Generate a strong secret:

```bash
node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
```

---

## Wiring Auth into the Server

Register the auth routes in `src/index.js`:

```js
const authRoutes = require('./routes/auth');
app.use('/api/auth', authRoutes);
```

Full auth flow for a student starting a session:

```
1. POST /api/auth/login  { email, password }
   Response: { token: "eyJ..." }

2. POST /api/agent1/chat
   Headers: Authorization: Bearer eyJ...
   Body: { message: "The situation is..." }
   Response: SSE stream of tokens
```

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code reads
your CLAUDE.md which lists JWT_SECRET and JWT_EXPIRY as environment variables
and states that JWT verify must use `algorithms: ['HS256']`. It will apply
both rules automatically from that context.

**Prompt to implement JWT authentication:**

```
Implement JWT authentication for the SCQ platform.

1. server/src/routes/auth.js - POST /api/auth/login
   - Destructure only email and password from req.body
   - Query users table by email using a parameterised query
   - Use bcrypt.compare (async, never compareSync) to check the password
   - Return the same error message whether email or password is wrong
   - Sign the token with jwt.sign using algorithm: 'HS256' and include
     user_id, role, and cohort_id in the payload
   - Read JWT_SECRET and JWT_EXPIRY from process.env

2. server/src/middleware/auth.js - JWT verification
   - Verify with algorithms: ['HS256'] in the options object
   - Attach payload to req.user
   - Return 401 with a generic message on any failure, never send err.message

3. server/src/middleware/roleGuard.js - requireRole(...roles) factory
   - Returns middleware that checks req.user.role against the allowed list

Wire auth routes into server/src/index.js at /api/auth.
```

**What Claude Code will do:**
Implement all three files, enforce async bcrypt and algorithm pinning from
the CLAUDE.md security rules, and register the auth route in index.js.

**Tips for this document:**
- Test the login route first with a manually inserted user before testing the full flow:
  `sqlite3 data/scq.db "INSERT INTO users VALUES ('u01', 'test@test.com', '[hash]', 'student', 'cohort-a', datetime('now'));"`
- To generate a bcrypt hash for testing: `node -e "const b=require('bcrypt'); b.hash('password123', 12).then(console.log)"`
- If Claude Code uses `compareSync`, paste the security rule from CLAUDE.md and ask it to fix it

---

## Starter Code

The `starter-code/` folder contains the four files you need to get started:

```
starter-code/
├── CLAUDE.md           The platform operating brief - Claude Code reads this first
├── package.json        Node dependencies including jsonwebtoken and bcrypt
├── requirements.txt    Python dependencies
└── .env.example        Includes JWT_SECRET and JWT_EXPIRY with placeholder values
```

Use the Claude Code Desktop App prompt above to generate `routes/auth.js`,
`middleware/auth.js`, and `middleware/roleGuard.js`. The security rules in
CLAUDE.md (HS256 algorithm pinning, async bcrypt, identical error messages)
are already in context when Claude Code generates these files.

---

## Assignment

[03-implement-jwt-authentication.md](assignments/03-implement-jwt-authentication.md)

---

Copyright Janna AI Research Labs
