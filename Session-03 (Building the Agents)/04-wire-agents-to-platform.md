# Build 04: Wiring the Agents to the Platform

> Framework 02 (The Five-Layer Architecture) defines the boundaries.
> Framework 05 (Infrastructure as Foundation) shows what the platform layer
> must provide before the agents can do their work. This document connects
> all three agents to the web layer and adds the professor-facing routes
> that make the platform usable beyond a single student.

**Applies:** Framework 02 (Five-Layer Architecture) + Framework 05 (Infrastructure as Foundation)
**Builds:** Complete Express integration for all three agents, professor dashboard route, and session finalisation

---

## The Five Layers in Motion

After Session 02 and the first three documents of this session, you have
all five layers partially in place. This document assembles them into a
working system.

| Layer | What is in place | What this document adds |
|---|---|---|
| 5 - Infrastructure | get_client(), TurnTrace, logger | Rate limiting on agent routes |
| 4 - Model Config | model_config.py with per-agent models | Nothing (complete) |
| 3 - Tool Registry | save_scq_draft, get_student_progress, get_rubric_config, save_evaluation | Nothing (complete) |
| 2 - Context Architecture | Stage injection, SCQ context block | Session finalisation trigger |
| 1 - The Prompt | matteo_v1.txt, juli_v1.txt, tedd_v1.txt | Nothing (complete) |

The wiring work is at the infrastructure and context layers. The prompts
and tools are already done.

---

## Completing the Agent Routes

Each of the three routes in server/src/routes/ needs to be a complete,
production-ready handler before the platform can run end to end.

A complete agent route does these things in order:

```
1. Authenticate: authMiddleware verifies the JWT and sets req.user
2. Validate input: check that message exists and is a non-empty string
3. Load context: read stage/progress from DB, build system prompt
4. Call the agent: spawn Python agent, stream SSE tokens
5. Validate output: run the format validator on the complete response
6. Persist: call appendTurn to save the turn to the database
7. Advance state: update stage or SCQ progress as needed
8. Done signal: send SSE done event
```

If any step fails, the route must:
- Return a JSON error response (not a stack trace)
- Log the full error server-side with the user_id and timestamp
- Not leave the SSE stream hanging open

---

## Adding Rate Limiting to Agent Routes

From Framework 05: infrastructure provides the platform's defensive layer.
Rate limiting on agent routes prevents a student from burning the API budget
by looping a request.

Install express-rate-limit (already in package.json from Session 02):

```js
// server/src/middleware/rateLimiter.js

const rateLimit = require('express-rate-limit');

const agentLimiter = rateLimit({
    windowMs: 60 * 1000,     // 1 minute window
    max: 30,                  // 30 requests per user per minute
    keyGenerator: (req) => req.user?.id ?? req.ip,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: 'Too many requests. Please wait before sending another message.' }
});

module.exports = { agentLimiter };
```

Apply to all three agent routes:

```js
// In server/src/index.js
const { agentLimiter } = require('./middleware/rateLimiter');

app.use('/api/agent1', agentLimiter, require('./routes/agent1'));
app.use('/api/agent2', agentLimiter, require('./routes/agent2'));
app.use('/api/agent3', agentLimiter, require('./routes/agent3'));
```

The rate limiter uses req.user.id as the key (not IP address) so that students
sharing a network cannot block each other.

---

## Professor Dashboard Route

The professor needs to see how their cohort is progressing. This route
returns all agent sessions for students in the professor's cohort.

```js
// server/src/routes/professor.js

const { authMiddleware } = require('../middleware/auth');
const { requireRole } = require('../middleware/roleGuard');
const db = require('../db');

router.get('/sessions',
    authMiddleware,
    requireRole('professor'),
    (req, res) => {
        const sessions = db.prepare(
            `SELECT s.user_id, s.agent_id, s.quality_score, s.finalised,
                    s.created_at, s.updated_at,
                    u.email
             FROM agent_sessions s
             JOIN users u ON s.user_id = u.id
             WHERE u.cohort_id = ?
             ORDER BY s.updated_at DESC
             LIMIT 200`
        ).all(req.user.cohort_id);

        res.json({ sessions });
    }
);
```

Two security requirements from the baseline framework:
- requireRole('professor') means a student JWT cannot reach this route
- The query scopes to req.user.cohort_id so a professor cannot see
  sessions from a different cohort (IDOR prevention)

---

## Session Finalisation Route

When a student submits their deliverable to Tedd, the Tedd route calls
save_evaluation which sets finalised = 1. The platform also needs a
route a professor can call to manually finalise a session.

```js
// In server/src/routes/professor.js

router.patch('/sessions/:sessionId/finalise',
    authMiddleware,
    requireRole('professor'),
    (req, res) => {
        const { sessionId } = req.params;

        // Verify this session belongs to the professor's cohort
        const session = db.prepare(
            `SELECT s.id FROM agent_sessions s
             JOIN users u ON s.user_id = u.id
             WHERE s.id = ? AND u.cohort_id = ?`
        ).get(sessionId, req.user.cohort_id);

        if (!session) {
            return res.status(404).json({ error: 'Session not found.' });
        }

        db.prepare(
            'UPDATE agent_sessions SET finalised = 1 WHERE id = ?'
        ).run(sessionId);

        res.json({ finalised: true });
    }
);
```

The cohort check in the query is the IDOR guard. A professor cannot finalise
sessions from another cohort even if they know the session ID.

---

## Wiring the Professor Route to Express

```js
// server/src/index.js

app.use('/api/professor', require('./routes/professor'));
```

No rate limiter is applied to the professor routes. A professor reviewing
cohort data generates far fewer requests than a student in a coaching session.

---

## Error Handler

Every Express application needs a final error handler that converts
unhandled errors into clean JSON responses. Without it, stack traces
reach the client.

```js
// At the end of server/src/index.js, after all routes

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

The error object is logged server-side in full. The client gets only a
generic message. This pattern is required by the security baseline from
Framework 11.

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code can
read all three route files and the current index.js to understand what
is already in place, then add the missing pieces.

**Prompt to complete the platform wiring:**

```
Complete the Express platform wiring for all three agents.

1. Add a rate limiter middleware at server/src/middleware/rateLimiter.js:
   - 30 requests per minute per user (keyed on req.user.id, fallback to IP)
   - Apply to /api/agent1, /api/agent2, and /api/agent3 in index.js
   - Error message must not expose internal details

2. Audit each of the three agent routes (routes/agent1.js, agent2.js, agent3.js):
   - Confirm the route follows the 8-step order: authenticate, validate input,
     load context, call agent, validate output, persist turn, advance state, done signal
   - If any step is missing, add it
   - Input validation: check that req.body.message is a non-empty string before
     passing to the agent. Return 400 if not.

3. Add server/src/routes/professor.js with two routes:
   - GET /api/professor/sessions: all sessions for the professor's cohort
   - PATCH /api/professor/sessions/:sessionId/finalise: mark a session finalised

   Both routes must use authMiddleware and requireRole('professor').
   Both queries must scope to req.user.cohort_id (IDOR guard).

4. Add the professor router to index.js.

5. Add a four-argument error handler at the end of index.js that:
   - Logs the full error server-side (message, stack, userId, path, timestamp)
   - Returns { error: "Something went wrong. Please try again." } to the client

Reference the Security Non-Negotiables section of CLAUDE.md before writing
any route handler. All queries must be parameterised.
```

**What Claude Code will do:**
Audit and complete all three agent routes, add the rate limiter, add professor
routes with IDOR protection, and add the global error handler.

**Tips for this document:**
- After implementing, send a request without a JWT and confirm you get 401,
  not a stack trace.
- Send a professor request using a student JWT and confirm you get 403.
- Send 35 requests in one minute from the Matteo route and confirm the 30th
  returns the rate limit error.
- Ask Claude Code: "Walk me through what happens when the Python agent crashes
  mid-stream. Does the SSE connection close cleanly? Does the Express route log
  the error? Does the client get a message?"

---

## Starter Code

The wiring changes are additions to existing files. Claude Code generates
them by reading what is already there and adding what is missing.

```
starter-code/
|-- CLAUDE.md           Student Journey section added. Shows the full request
|                       path from browser to agent and back, all layers visible.
|-- .env.example        Environment variable reference
|-- package.json        Includes express-rate-limit (already in Session 02 list)
`-- requirements.txt    Python dependencies
```

---

## Assignment

[04-wire-agents-to-platform.md](assignments/04-wire-agents-to-platform.md)

---

Copyright Janna AI Research Labs
