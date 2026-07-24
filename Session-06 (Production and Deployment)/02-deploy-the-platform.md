# Build 02: Deploy the Platform

**Frameworks applied:** 02 (Project Structure) + 08 (Internal Setup)

---

## Why Railway

Railway is the correct deployment target for this platform at this stage.
It runs a Node.js process directly from your GitHub repository, manages
HTTPS automatically, provides a persistent volume for SQLite, and deploys
on every push to main. No Docker knowledge required. No cloud provider
account complexity.

The tradeoffs: Railway is not free at scale and SQLite on a single server
does not scale horizontally. Both of these are acceptable for a cohort of
60 students. The architecture can be upgraded to PostgreSQL and multiple
instances later if needed.

---

## What Railway Does for You

| Concern | How Railway handles it |
|---|---|
| HTTPS | Automatic, included with every deployment |
| Process restart on crash | Automatic with exponential backoff |
| Environment variables | Set in dashboard, injected at runtime |
| Custom domain | Add your domain in the Settings panel |
| Persistent storage | Railway Volume mounted at a path you choose |
| Build and deploy | Runs `npm install` then `npm start` on push |
| Health checks | Calls your GET /api/health and restarts if it fails |

---

## SQLite in Production: The Volume Requirement

SQLite stores data in a file. On Railway (and most cloud platforms), the
file system is ephemeral: it is wiped on every deploy. A fresh deploy would
destroy the student session database.

The fix is a Railway Volume: a persistent disk that survives deploys.

Steps to set up the Volume:

1. In the Railway dashboard, open your project
2. Click your service
3. Go to Volumes
4. Create a new volume, mount path `/data`
5. In your environment variables, set `DB_PATH=/data/scq.db`

Update `server/src/db.js` to read the path from the environment:

```js
import Database from 'better-sqlite3';
import path from 'path';

const dbPath = process.env.DB_PATH || path.join(process.cwd(), 'data', 'scq.db');

let db = new Database(dbPath);
db.pragma('journal_mode = WAL');

export function getDb() { return db; }
export function setTestDb(testDb) { db = testDb; }
```

Also update `server/src/db-init.js` to use the same path:

```js
import { getDb } from './db.js';
// replace the hardcoded path with getDb() call
```

After adding the volume, run the schema initialisation once via Railway's
one-off command feature or SSH:

```bash
NODE_ENV=production npm run db:init
```

Confirm the database file exists at `/data/scq.db` before sending your
first student to the platform.

---

## The Python Agent in Production

Railway runs Node.js natively. The Python agent is spawned as a child
process. Railway supports Python, but your repository must tell it which
language to install.

Add a `Procfile` at the project root:

```
web: node server/src/index.js
```

And a `runtime.txt` if you need a specific Python version:

```
python-3.11
```

Railway reads `requirements.txt` from the project root and installs Python
dependencies automatically. Confirm your `requirements.txt` is at the root
(not inside a subdirectory).

Verify the Python agent works in production by starting a student session
and checking the Railway logs for any Python subprocess errors.

---

## Deploy Steps

```bash
# 1. Push your code to GitHub (Railway deploys from the repo)
git push origin main

# 2. In the Railway dashboard, create a new project
#    Connect your GitHub repository
#    Railway auto-detects Node.js

# 3. Set all environment variables in the Railway dashboard:
#    ANTHROPIC_API_KEY
#    JWT_SECRET        (use: node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")
#    NODE_ENV          production
#    CORS_ORIGIN       https://your-frontend-domain.com
#    DB_PATH           /data/scq.db
#    (all other variables from .env.example)

# 4. Add a Railway Volume mounted at /data

# 5. Railway deploys automatically on every push to main
#    Watch the build logs in the Railway dashboard

# 6. Once deployed, verify the health check:
curl https://your-app.railway.app/api/health
# Expected: { "status": "ok", "db": "ok", ... }

# 7. Initialise the database (first deploy only):
#    Use Railway's CLI or dashboard to run the one-off command:
npm run db:init
```

---

## Database Backup Strategy

SQLite databases should be backed up before every deploy that changes the
schema, and on a regular schedule in production.

Add a backup script at `server/scripts/backup-db.js`:

```js
import { execSync } from 'child_process';
import path from 'path';

const dbPath = process.env.DB_PATH || './data/scq.db';
const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
const backupPath = path.join('./data', `scq-backup-${timestamp}.db`);

try {
  execSync(`cp "${dbPath}" "${backupPath}"`);
  console.log(`Backup created: ${backupPath}`);
} catch (err) {
  console.error('Backup failed:', err.message);
  process.exit(1);
}
```

Add to `package.json`:

```json
"db:backup": "node server/scripts/backup-db.js"
```

Run before schema migrations:

```bash
npm run db:backup && sqlite3 data/scq.db "ALTER TABLE ..."
```

For automated backups, Railway's cron jobs (or a simple scheduled task) can
run `npm run db:backup` daily. Store backups outside the Volume if the
Volume is at risk of corruption.

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code already
knows the db.js singleton pattern and the start script from CLAUDE.md.

**Prompt to update db.js for production paths:**

```
Update the SCQ platform for production database configuration.

1. In server/src/db.js, replace the hardcoded database path with:
   const dbPath = process.env.DB_PATH || path.join(process.cwd(), 'data', 'scq.db');
   Import path from 'node:path'. Keep the WAL pragma and the setTestDb export.

2. In server/src/db-init.js, ensure it uses the same getDb() singleton
   rather than opening a separate database connection with a hardcoded path.

3. Create a Procfile at the project root containing:
   web: node server/src/index.js

4. Create server/scripts/backup-db.js with a backup script that:
   - Reads DB_PATH from the environment
   - Creates a timestamped copy of the database file
   - Logs the backup path on success
   - Exits with code 1 on failure

5. Add "db:backup": "node server/scripts/backup-db.js" to package.json scripts.

Do not change any agent code, route logic, or middleware.
```

**What Claude Code will do:**
Update db.js to read the path from the environment, fix db-init.js to use the
singleton, create the Procfile, and create the backup script.

**Tips for this document:**
- After updating db.js, run the test suite to confirm the setTestDb path still
  works: `cd server && npm test`. If tests fail after this change, check that
  the testDb.js helper still calls setTestDb before any route is called.
- Confirm the Procfile is at the project root, not inside server/.
  Railway looks for it at the top level of the repository.
- Tell Claude Code: "The DB_PATH change must be backward-compatible with the
  development setup. If DB_PATH is not set, default to ./data/scq.db."

---

**Next:** [03-add-production-monitoring.md](03-add-production-monitoring.md)

---

Copyright Janna AI Research Labs
