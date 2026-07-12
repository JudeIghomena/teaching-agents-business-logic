# Assignment 04: Wire the Agents to the Platform

**Covers:** Build 04 (04-wire-agents-to-platform.md)
**Time estimate:** 30-45 minutes
**Done when:** All three agent routes are production-ready, rate limiting blocks excess requests, and the professor route returns cohort data

---

## What You Are Building

After the first three assignments, each agent works in isolation. This assignment
completes the platform by adding rate limiting, a global error handler, and the
professor dashboard route that makes cohort data visible.

By the end of this assignment:
- No single student can exceed 30 requests per minute
- Stack traces never reach the client
- A professor JWT can read all sessions for their cohort
- A professor JWT can manually finalise a session

---

## Before You Start

Confirm these are true:
- [ ] All three agent routes work (Assignments 01-03 complete)
- [ ] The users table has at least one professor user (role = 'professor')
- [ ] server/src/middleware/auth.js and roleGuard.js exist from Session 02

---

## Steps

### Step 1: Add the rate limiter middleware

Create server/src/middleware/rateLimiter.js:

```js
const rateLimit = require('express-rate-limit');

const agentLimiter = rateLimit({
    windowMs: 60 * 1000,
    max: 30,
    keyGenerator: (req) => req.user?.id ?? req.ip,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: 'Too many requests. Please wait before sending another message.' }
});

module.exports = { agentLimiter };
```

express-rate-limit should already be in package.json from Session 02. If not:
```bash
cd server && npm install express-rate-limit
```

### Step 2: Apply rate limiting in index.js

In server/src/index.js, update the agent route registration:

```js
const { agentLimiter } = require('./middleware/rateLimiter');

app.use('/api/agent1', agentLimiter, require('./routes/agent1'));
app.use('/api/agent2', agentLimiter, require('./routes/agent2'));
app.use('/api/agent3', agentLimiter, require('./routes/agent3'));
```

### Step 3: Audit input validation on all three routes

Open each agent route and confirm:
- req.body.message exists and is a non-empty string before the agent is called
- If not: return res.status(400).json({ error: 'Message is required.' })

For agent1.js this looks like:
```js
const { message } = req.body;
if (!message || typeof message !== 'string' || message.trim() === '') {
    return res.status(400).json({ error: 'Message is required.' });
}
```

### Step 4: Add the professor routes

Create server/src/routes/professor.js with the two routes from Build 04:
- GET /sessions: returns all sessions for the professor's cohort
- PATCH /sessions/:sessionId/finalise: marks a session as finalised

Both must scope queries to req.user.cohort_id (IDOR guard).
Both must use authMiddleware and requireRole('professor').

Register in index.js:
```js
app.use('/api/professor', require('./routes/professor'));
```

### Step 5: Add the global error handler

At the very end of index.js, after all route registrations:

```js
app.use((err, req, res, next) => {
    console.error('[error]', {
        message: err.message,
        stack: err.stack,
        userId: req.user?.id,
        path: req.path,
        timestamp: new Date().toISOString()
    });
    res.status(err.status ?? 500).json({
        error: 'Something went wrong. Please try again.'
    });
});
```

### Step 6: Test each addition

Rate limiter test (requires a loop in your shell):
```bash
for i in {1..35}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:3001/api/agent1/chat \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "test"}';
done
```
Requests 31-35 should return 429.

Role guard test:
```bash
# Professor route with a student token
curl -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
     http://localhost:3001/api/professor/sessions
# Expected: 403
```

Professor dashboard test:
```bash
curl -H "Authorization: Bearer YOUR_PROFESSOR_TOKEN" \
     http://localhost:3001/api/professor/sessions
# Expected: { "sessions": [...] }
```

---

## Done Checklist

- [ ] agentLimiter applied to /api/agent1, /api/agent2, /api/agent3
- [ ] Sending 35 requests in one minute returns 429 on request 31+
- [ ] All three agent routes validate req.body.message before calling the agent
- [ ] GET /api/professor/sessions returns 200 for a professor, 403 for a student
- [ ] PATCH /api/professor/sessions/:id/finalise works for a professor
- [ ] Global error handler is the last middleware in index.js
- [ ] A thrown error in a route returns a generic message to the client, not a stack trace

---

## Troubleshooting

**Rate limiter always returns 200 (never 429):**
The keyGenerator may be returning undefined. Add a console.log in keyGenerator:
console.log('rate key:', req.user?.id ?? req.ip)
If it logs undefined every time, authMiddleware is not setting req.user for that route.
Check that agentLimiter is applied AFTER authMiddleware in the route chain.

**Professor route returns 404:**
Confirm the route is registered in index.js before the error handler.
Also confirm the HTTP method matches: GET for /sessions, PATCH for /sessions/:id/finalise.

**Error handler not running:**
The error handler must have exactly four arguments (err, req, res, next).
Express identifies it as an error handler by the arity of the function.
A three-argument version is a normal middleware and will not catch errors.

---

**Next:** [05-test-end-to-end.md](05-test-end-to-end.md)

---

Copyright Janna AI Research Labs
