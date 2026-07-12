# Assignment 01: Add Rate Limiting

**Reads with:** [01-add-rate-limiting.md](../01-add-rate-limiting.md)
**Time estimate:** 30-45 minutes
**Frameworks applied:** 11 (Security Baseline) + 05 (Environment Config)

---

## What You Are Building

Two Express rate limiters applied at the route level. One for the auth
endpoint, scoped by IP address. One for all three agent endpoints, scoped
by authenticated user ID.

---

## Steps

### Step 1: Create the middleware file

Create `server/src/middleware/rateLimiter.js` with two exports:
`authLimiter` and `agentLimiter`.

- `authLimiter`: window from `RATE_LIMIT_AUTH_WINDOW_MS` (default 900000),
  max from `RATE_LIMIT_AUTH_MAX` (default 10), key by `req.ip`
- `agentLimiter`: window from `RATE_LIMIT_AGENT_WINDOW_MS` (default 60000),
  max from `RATE_LIMIT_AGENT_MAX` (default 30), key by `req.user?.id || req.ip`

Both use `standardHeaders: true` and `legacyHeaders: false`. Both return a
JSON error body.

Use the code in the build document as your reference. Write it yourself
rather than copying it directly. The build document explains every decision:
read those explanations before writing the code.

### Step 2: Add environment variables

In `.env`:

```
RATE_LIMIT_AUTH_WINDOW_MS=900000
RATE_LIMIT_AUTH_MAX=10
RATE_LIMIT_AGENT_WINDOW_MS=60000
RATE_LIMIT_AGENT_MAX=30
```

### Step 3: Wire the limiters into index.js

Import both limiters in `server/src/index.js`.

Apply `authLimiter` to the auth route group before the route handler.
Apply `agentLimiter` to each agent route after `authMiddleware`.

The middleware order for agent routes must be:
`authMiddleware` then `agentLimiter` then the route handler.

### Step 4: Test the auth limiter

Start the server. Run this loop:

```bash
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:3001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"x@x.com","password":"wrong"}'
done
```

Expected: first 10 lines print 401, lines 11 and 12 print 429.

If you see 401 on line 11, the limiter is not wired. Recheck the import
and the `app.use` order.

### Step 5: Test the agent limiter

Log in and get a valid JWT. Run 31 rapid requests to the agent1 endpoint.
Request 31 should return 429.

---

## Done Checklist

- [ ] `server/src/middleware/rateLimiter.js` exists with two named exports
- [ ] Auth limiter uses IP-based key, agent limiter uses user ID key
- [ ] Both limiters read from environment variables with safe defaults
- [ ] `standardHeaders: true`, `legacyHeaders: false` on both
- [ ] `authLimiter` applied to `/api/auth` routes in index.js
- [ ] `agentLimiter` applied after `authMiddleware` on all three agent route groups
- [ ] Auth limiter verified with shell loop: 429 on request 11
- [ ] Environment variables added to `.env` and `.env.example`

---

## Troubleshooting

Rate limit not triggering: Confirm the limiter is applied before the route
handler, not after. `app.use('/api/auth', authLimiter)` must come before
`app.use('/api/auth', authRoutes)`.

All requests returning 429 immediately: Check `RATE_LIMIT_AUTH_MAX` in your
`.env`. If it is set to 0 or an empty string, `parseInt` returns NaN and
the limiter may default to 0. Use `parseInt(value || '10')` to guarantee
a numeric fallback.

Agent limiter not using user ID: The `req.user` object is only populated
after `authMiddleware` runs. Confirm that `authMiddleware` is before
`agentLimiter` in the middleware chain.

---

**Next assignment:** [02-validate-all-inputs.md](02-validate-all-inputs.md)
