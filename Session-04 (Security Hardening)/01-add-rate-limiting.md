# Build 01: Add Rate Limiting

**Frameworks applied:** 11 (Security Baseline) + 05 (Environment Config)

---

## Why Rate Limiting Belongs Here

After Session 03 you have three agent endpoints and one auth endpoint, all
publicly reachable. Without rate limiting, two things can happen:

First, the login endpoint is open to brute-force attacks. An attacker can
try thousands of password combinations per minute until one works. There is
nothing in the Express setup so far that stops this.

Second, your agent endpoints cost money per request. A single user sending
10,000 messages in a minute will exhaust your Anthropic API budget and make
the platform unresponsive for every other student. Rate limiting is not just
a security control: it is a cost control.

Two different limits apply because the threat is different at each layer:

- Auth endpoint: limit by IP address, with a long window (15 minutes). The
  goal is to slow down password guessing from any one source. An IP-based
  limit is appropriate here because the attacker may not even have a valid
  account yet.

- Agent endpoints: limit by authenticated user ID, with a short window (1
  minute). The goal is to prevent any single logged-in student from flooding
  the agents. User-based limits are appropriate because the request has
  already passed authentication and we know who is sending it.

---

## What You Are Building

A middleware file with two configured limiters. Both are wired into the
Express application at the route level, not globally, so each endpoint gets
the right limit for its threat profile.

```
server/src/middleware/rateLimiter.js    Two limiter exports
server/src/index.js                     Wire limiters to routes
```

Both limiters read their configuration from environment variables so that
limits can be tuned for different deployment environments without touching
code.

---

## The Rate Limiter Middleware

express-rate-limit is already in your package.json dependencies from
Session 03. No new package is required.

Create `server/src/middleware/rateLimiter.js`:

```js
import rateLimit from 'express-rate-limit';

export const authLimiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_AUTH_WINDOW_MS || '900000'),
  max: parseInt(process.env.RATE_LIMIT_AUTH_MAX || '10'),
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many login attempts. Try again in 15 minutes.' },
  keyGenerator: (req) => req.ip,
});

export const agentLimiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_AGENT_WINDOW_MS || '60000'),
  max: parseInt(process.env.RATE_LIMIT_AGENT_MAX || '30'),
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests. Slow down and try again.' },
  keyGenerator: (req) => req.user?.id || req.ip,
});
```

Four things to note:

First, both limiters default to the correct values in code so that the
platform works out of the box even if the environment variables are not set.

Second, `standardHeaders: true` makes the limiter add `RateLimit-Limit`,
`RateLimit-Remaining`, and `RateLimit-Reset` headers to every response.
Clients can read these to display a countdown or throttle themselves.

Third, `legacyHeaders: false` disables the older `X-RateLimit-*` header
format. The standard headers are the correct ones to use now.

Fourth, the agentLimiter uses `req.user?.id` as the key. The `?.` is
important: if somehow the limiter fires before authentication (it should
not, but defensive code does not assume request order), it falls back to
the IP address rather than crashing with a null reference error.

---

## Wiring Into the Application

In `server/src/index.js`, import the limiters and apply them at the route
level:

```js
import { authLimiter, agentLimiter } from './middleware/rateLimiter.js';

// Auth routes: IP-based, long window
app.use('/api/auth', authLimiter);
app.use('/api/auth', authRoutes);

// Agent routes: user-based, short window
// Apply after authMiddleware so req.user is populated
app.use('/api/agent1', authMiddleware, agentLimiter, agent1Routes);
app.use('/api/agent2', authMiddleware, agentLimiter, agent2Routes);
app.use('/api/agent3', authMiddleware, agentLimiter, agent3Routes);
```

The ordering matters. For agent routes, authMiddleware runs first to verify
the JWT and populate `req.user`. Then agentLimiter runs and uses `req.user.id`
as the key. If authMiddleware rejects the request with a 401, the limiter
never fires. This is the correct order: authenticate first, then rate-limit
by the authenticated identity.

---

## Environment Variables

Add these to your `.env` file (and to `.env.example` with placeholder values):

```
RATE_LIMIT_AUTH_WINDOW_MS=900000
RATE_LIMIT_AUTH_MAX=10
RATE_LIMIT_AGENT_WINDOW_MS=60000
RATE_LIMIT_AGENT_MAX=30
```

The values shown above match the defaults in the middleware code. In
production you may want to tighten these: lower the max values, or widen
the windows for the agent limiter if students legitimately need more turns.
Because they are environment variables, you can change them without a deploy
in many hosting environments.

---

## What a 429 Response Looks Like

When the limit is exceeded, express-rate-limit responds automatically. With
`standardHeaders: true`, the response includes:

```
HTTP/1.1 429 Too Many Requests
RateLimit-Limit: 10
RateLimit-Remaining: 0
RateLimit-Reset: 1720000000
Content-Type: application/json

{ "error": "Too many login attempts. Try again in 15 minutes." }
```

Your client-side code does not need to handle 429 specially to make the
platform secure. The limit is enforced server-side regardless of what the
client does.

---

## Testing the Limiter

You can verify the auth limiter with a shell loop before writing automated
tests:

```bash
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:3001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}'
done
```

The first 10 requests return 401 (wrong password, auth works). Requests 11
and 12 return 429 (rate limit exceeded). If you see 401 on request 11, the
limiter is not wired in correctly.

For the agent limiter, verify that 31 rapid requests from the same logged-in
user produce a 429 on the 31st.

---

## What the CLAUDE.md Now Records

After completing this document, your CLAUDE.md for Session 04 records:

```
Rate Limit Configuration:
  Auth endpoint:  10 requests per 900,000 ms (15 min) per IP
  Agent endpoints: 30 requests per 60,000 ms (1 min) per user ID
  Config source: RATE_LIMIT_* environment variables
  Library: express-rate-limit (already in dependencies)
```

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code reads
your CLAUDE.md automatically and already knows the middleware layer lives in
`server/src/middleware/` and must not be bypassed by route handlers.

**Prompt to add rate limiting:**

```
Add rate limiting to the SCQ platform Express server.

1. Create server/src/middleware/rateLimiter.js with two named exports:

   authLimiter: rateLimit with
   - windowMs from parseInt(process.env.RATE_LIMIT_AUTH_WINDOW_MS || '900000')
   - max from parseInt(process.env.RATE_LIMIT_AUTH_MAX || '10')
   - standardHeaders: true, legacyHeaders: false
   - message: { error: 'Too many login attempts. Try again in 15 minutes.' }
   - keyGenerator: (req) => req.ip

   agentLimiter: rateLimit with
   - windowMs from parseInt(process.env.RATE_LIMIT_AGENT_WINDOW_MS || '60000')
   - max from parseInt(process.env.RATE_LIMIT_AGENT_MAX || '30')
   - standardHeaders: true, legacyHeaders: false
   - message: { error: 'Too many requests. Slow down and try again.' }
   - keyGenerator: (req) => req.user?.id || req.ip

2. In server/src/index.js, import both limiters.
   Apply authLimiter to /api/auth routes BEFORE the route handler.
   Apply agentLimiter to /api/agent1, /api/agent2, /api/agent3 routes
   AFTER authMiddleware and BEFORE each route handler.

Do not apply agentLimiter globally. It must be per-route-group.
Do not move authMiddleware - keep it before agentLimiter on agent routes.
```

**What Claude Code will do:**
Create `rateLimiter.js` with both exports, import them in `index.js`, and
wire them at the route level in the correct order. It will read the existing
`index.js` structure from your project and add the limiters without
restructuring the file.

**Tips for this document:**
- If the shell loop test shows 429 on request 1 instead of request 11, the
  `RATE_LIMIT_AUTH_MAX` environment variable is likely 0 or empty. Ask Claude
  Code to add a `console.log` that prints the parsed max value on startup.
- If the agent limiter is not firing, ask Claude Code: "Show me the middleware
  order for the agent1 route in index.js." Confirm agentLimiter appears after
  authMiddleware.
- Tell Claude Code: "Do not add a global rate limiter with `app.use`. Each
  endpoint group needs its own limiter with its own key generator."

---

**Next:** [02-validate-all-inputs.md](02-validate-all-inputs.md)

---

Copyright Janna AI Research Labs
