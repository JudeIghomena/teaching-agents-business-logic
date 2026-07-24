# Build 01: Prepare for Deployment

**Frameworks applied:** 05 (Environment Config) + 02 (Project Structure)

---

## Why Preparation Comes Before Deployment

Deploying before preparing creates a broken production environment that you
then have to fix while real students are trying to use it. Preparation is
the work you do once. It takes 30 minutes and saves hours.

There are four things to prepare:
1. A production environment variable list that is complete and annotated
2. A health check endpoint that confirms the platform is alive
3. A pre-deploy checklist that must be clean before any deploy
4. A production start command verified to work outside your local machine

---

## The Production Environment Variable List

Every value in `.env.example` is a candidate for production. Some have safe
defaults. Some must be set explicitly for production, with no fallback.

| Variable | Production requirement | Dev default safe for prod? |
|---|---|---|
| ANTHROPIC_API_KEY | Required, no default | No - must be set |
| JWT_SECRET | Required, must be 64 random hex chars | No - dev values are weak |
| JWT_EXPIRES_IN | Optional, default 8h | Yes |
| PORT | Railway sets this automatically | Set by host |
| NODE_ENV | Must be production | No |
| CORS_ORIGIN | Must be your production domain URL | No - dev allows all |
| RATE_LIMIT_AUTH_MAX | Optional, default 10 | Yes |
| RATE_LIMIT_AGENT_MAX | Optional, default 30 | Yes |
| MAX_MESSAGE_LENGTH | Optional, default 2000 | Yes |
| MAX_TEDD_MESSAGE_LENGTH | Optional, default 8000 | Yes |
| MAX_SCQ_FIELD_LENGTH | Optional, default 500 | Yes |
| HITL_SCORE_THRESHOLD | Optional, default 3.0 | Yes |
| TOKEN_BUDGET_PER_USER | Optional, default 50000 | Yes |
| DB_PATH | Path to SQLite file | Must match Railway Volume mount |

Generating a strong JWT secret:

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

Run this once, copy the output to your production environment variable store.
Never reuse the development secret in production.

---

## The Health Check Endpoint

A health check is a GET endpoint that returns 200 if the platform is
reachable and the database is responding, or 503 if something is broken.
Railway and other hosts call this endpoint to decide whether to route traffic.

Add to `server/src/routes/health.js`:

```js
import { Router } from 'express';
import { getDb } from '../db.js';

const router = Router();

router.get('/health', (req, res) => {
  try {
    const db = getDb();
    db.prepare('SELECT 1').get();
    res.json({
      status: 'ok',
      db: 'ok',
      version: process.env.npm_package_version || '0.6.0',
      node_env: process.env.NODE_ENV || 'development',
    });
  } catch (err) {
    console.error('[health] db check failed:', err.message);
    res.status(503).json({
      status: 'error',
      db: 'unavailable',
    });
  }
});

export default router;
```

Mount in `server/src/index.js`:

```js
import healthRoutes from './routes/health.js';
app.use('/api', healthRoutes);
```

This endpoint does not require authentication. It must be publicly accessible
because the deployment host calls it before routing any traffic.

Do not call the Anthropic API from the health check. An API call costs tokens,
adds latency, and can fail for reasons unrelated to the platform health. The
health check verifies only what it owns: the web server and the database.

---

## CORS for Production

In development, CORS is often set permissively. In production, only your
actual frontend domain should be allowed.

Update `server/src/index.js`:

```js
const corsOrigin = process.env.CORS_ORIGIN;

if (!corsOrigin && process.env.NODE_ENV === 'production') {
  console.error('[startup] CORS_ORIGIN must be set in production. Exiting.');
  process.exit(1);
}

app.use(cors({
  origin: corsOrigin || 'http://localhost:5173',
  credentials: true,
}));
```

This fails fast at startup if `CORS_ORIGIN` is missing in production. A
missing CORS origin in production means the frontend cannot reach the API,
so failing fast is the correct behaviour.

---

## The Pre-Deploy Checklist

Run all of these before every production deploy. A deploy with any item
failing should be aborted:

```bash
# 1. Zero high/critical vulnerabilities
npm audit --audit-level=high

# 2. Secret scan — zero hits
grep -rE "(sk-ant|ANTHROPIC_API_KEY\s*=\s*['\"][^'\"]{10})" server/src/

# 3. All tests pass
cd server && npm test

# 4. No hardcoded domain or localhost in CORS config
grep -rn "localhost\|127\.0\.0\.1" server/src/index.js

# 5. NODE_ENV is set to production in your deployment config
# (verify in Railway dashboard or equivalent)
```

If any check fails, fix it before deploying. A failed deploy is better than
a broken production environment.

---

## The Production Start Command

Your `package.json` `start` script must work from the project root as a
plain process, not through nodemon:

```json
"start": "node server/src/index.js"
```

Verify it locally:

```bash
NODE_ENV=production node server/src/index.js
```

The process should start on the port in `PORT` (or 3001 by default) without
errors. If it crashes on startup, the deployment host will restart it in a
loop. Read the startup logs carefully before deploying.

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code already
knows the Express route pattern from your CLAUDE.md and the middleware chain
from Session 04.

**Prompt to add the health check and production startup guard:**

```
Add production preparation to the SCQ platform.

1. Create server/src/routes/health.js with a GET /health route.
   The route must not require authentication.
   It checks the database with SELECT 1 and returns:
     { status: 'ok', db: 'ok', version: '0.6.0', node_env: process.env.NODE_ENV }
   On database error, return HTTP 503:
     { status: 'error', db: 'unavailable' }
   Do not call the Anthropic API from this route.

2. Mount the health route in server/src/index.js at /api.

3. Add a CORS startup guard in server/src/index.js:
   If NODE_ENV is 'production' and CORS_ORIGIN is not set,
   log an error and call process.exit(1).
   Set the CORS origin to CORS_ORIGIN env var in production,
   falling back to 'http://localhost:5173' in development.

4. Add CORS_ORIGIN and NODE_ENV to server/.env.example with comments
   explaining the production requirement.

5. Add a DB_PATH env variable to .env.example with a comment explaining
   that it must match the Railway Volume mount path in production.
```

**What Claude Code will do:**
Create the health route, update the CORS setup with the startup guard, and
add the new environment variables to .env.example.

**Tips for this document:**
- After adding the health route, curl it locally:
  `curl http://localhost:3001/api/health`
  Confirm you see status: ok and db: ok.
- If the database check fails with "no such table", db-init has not been run.
  The health route's SELECT 1 does not reference any table, so a fresh
  database with no schema still returns ok.
- Tell Claude Code: "The health route must not be wrapped in authMiddleware.
  It must be publicly accessible, no token required."

---

**Next:** [02-deploy-the-platform.md](02-deploy-the-platform.md)

---

Copyright Janna AI Research Labs
