# Assignment 01: Prepare for Deployment

**Reads with:** [01-prepare-for-deployment.md](../01-prepare-for-deployment.md)
**Time estimate:** 30-40 minutes
**Frameworks applied:** 05 (Environment Config) + 02 (Project Structure)

---

## What You Are Building

A GET /api/health endpoint, a CORS production startup guard, and a verified
pre-deploy checklist. When these are in place, you can hand the platform to
a deployment host and be confident it will behave correctly.

---

## Steps

### Step 1: Add the health check endpoint

Create `server/src/routes/health.js`. The route must:
- Respond to GET /health
- Require no authentication
- Check the database with `SELECT 1`
- Return `{ status: 'ok', db: 'ok', version, node_env }` on success
- Return HTTP 503 with `{ status: 'error', db: 'unavailable' }` on database failure

Mount it in `server/src/index.js` at /api.

### Step 2: Test the health endpoint

Start the server and run:

```bash
curl http://localhost:3001/api/health
```

Expected output:

```json
{"status":"ok","db":"ok","version":"0.6.0","node_env":"development"}
```

If you see `db: 'unavailable'`, the database file does not exist or is locked.
Run `npm run db:init` and try again.

### Step 3: Add the CORS startup guard

In `server/src/index.js`, add a check: if `NODE_ENV` is `'production'` and
`CORS_ORIGIN` is not set, log an error and call `process.exit(1)`.

Set the CORS origin from `CORS_ORIGIN` with a development fallback:

```js
origin: process.env.CORS_ORIGIN || 'http://localhost:5173'
```

Test the guard:

```bash
NODE_ENV=production node server/src/index.js
```

Expected: the process exits immediately with an error message about CORS_ORIGIN.

### Step 4: Generate a strong JWT secret

Run:

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

Copy the output. This is the value you will use for JWT_SECRET in your
deployment environment variables. Store it somewhere safe. Do not commit it.

### Step 5: Run the full pre-deploy checklist

```bash
# Zero high/critical vulnerabilities
npm audit --audit-level=high

# No secrets in source
grep -rE "sk-ant" server/src/

# All tests pass
cd server && npm test

# Health check works
curl http://localhost:3001/api/health
```

All four must pass before you move to the next document.

---

## Done Checklist

- [ ] `server/src/routes/health.js` exists with GET /health (no auth)
- [ ] Health route returns `{ status: 'ok', db: 'ok' }` when db is accessible
- [ ] Health route returns HTTP 503 on database failure
- [ ] Health route is mounted at /api in index.js
- [ ] CORS startup guard exits with non-zero code in production without CORS_ORIGIN
- [ ] JWT_SECRET generated (64-char hex), stored securely, not committed
- [ ] npm audit shows zero high/critical vulnerabilities
- [ ] npm test passes with zero failures
- [ ] CORS_ORIGIN and DB_PATH added to .env.example with production notes

---

## Troubleshooting

Health endpoint returns 404: Confirm the route is mounted with
`app.use('/api', healthRoutes)` and the route file exports the router
as the default export.

CORS startup guard exits in development: The guard checks `NODE_ENV === 'production'`.
Confirm your `.env` file does not set `NODE_ENV=production`. Development
should leave NODE_ENV unset or set to 'development'.

npm audit shows high vulnerabilities: Run `npm audit fix`. If the fix
requires breaking changes, run `npm audit fix --force` and re-run the test
suite to confirm nothing broke. Check the CLAUDE.md overrides section:
some vulnerabilities are suppressed by version overrides already in place.

---

**Next assignment:** [02-deploy-the-platform.md](02-deploy-the-platform.md)
