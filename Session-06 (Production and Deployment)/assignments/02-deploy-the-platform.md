# Assignment 02: Deploy the Platform

**Reads with:** [02-deploy-the-platform.md](../02-deploy-the-platform.md)
**Time estimate:** 45-60 minutes
**Frameworks applied:** 02 (Project Structure) + 08 (Internal Setup)

---

## What You Are Building

A live, HTTPS-accessible deployment of the SCQ Simulation Portal on Railway
with a persistent SQLite database stored on a Railway Volume. A database
backup script. The Procfile and runtime configuration that Railway needs.

---

## Steps

### Step 1: Update db.js for configurable path

Update `server/src/db.js` to read the database path from `DB_PATH`:

```js
const dbPath = process.env.DB_PATH || path.join(process.cwd(), 'data', 'scq.db');
```

Import `path` from `'node:path'`. Keep the WAL pragma and the `setTestDb`
export unchanged.

After this change, run the test suite to confirm nothing broke:

```bash
cd server && npm test
```

### Step 2: Add the Procfile

Create `Procfile` at the project root (not inside server/):

```
web: node server/src/index.js
```

### Step 3: Create the backup script

Create `server/scripts/backup-db.js` as described in the build document.
Add the npm script:

```json
"db:backup": "node server/scripts/backup-db.js"
```

Test it:

```bash
DB_PATH=./data/scq.db npm run db:backup
```

Expected: a timestamped `.db` file appears in `./data/`.

### Step 4: Deploy to Railway

1. Push all changes to GitHub
2. Go to railway.app and create a new project
3. Connect your GitHub repository
4. Railway auto-detects Node.js and runs `npm install` and `npm start`
5. In the Railway dashboard, add a Volume mounted at `/data`
6. Set these environment variables in the Railway dashboard:
   - `ANTHROPIC_API_KEY` (your key)
   - `JWT_SECRET` (the 64-char hex from Assignment 01)
   - `NODE_ENV` = `production`
   - `CORS_ORIGIN` = (your frontend URL, or `*` temporarily for testing)
   - `DB_PATH` = `/data/scq.db`
7. Wait for the build and deploy to complete

### Step 5: Initialise the database on the Volume

In the Railway dashboard, find the one-off command or SSH option.
Run the schema initialisation:

```bash
npm run db:init
```

Confirm the database file exists at `/data/scq.db`.

### Step 6: Verify the deployment

```bash
curl https://your-app.railway.app/api/health
```

Expected: `{ "status": "ok", "db": "ok" }`.

Then log in via the API:

```bash
curl -X POST https://your-app.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.edu","password":"TestPass123!"}'
```

---

## Done Checklist

- [ ] `db.js` reads database path from `DB_PATH` environment variable
- [ ] Test suite still passes after the db.js change
- [ ] `Procfile` at project root with `web: node server/src/index.js`
- [ ] `server/scripts/backup-db.js` created and tested
- [ ] `db:backup` npm script added to package.json
- [ ] Railway project created and connected to GitHub repo
- [ ] Railway Volume mounted at `/data`
- [ ] All production environment variables set in Railway dashboard
- [ ] Database initialised on the Volume (`npm run db:init`)
- [ ] GET /api/health returns `{ status: 'ok', db: 'ok' }` on the live URL
- [ ] Auth login returns a JWT on the live URL

---

## Troubleshooting

Railway build fails with "missing script: start": Confirm `package.json`
has `"start": "node server/src/index.js"`. The Procfile overrides are
only used if Railway reads it; the package.json start script is the fallback.

Python agent not working in production: Check the Railway build logs for
Python installation errors. Confirm `requirements.txt` is at the project
root. If it is inside `agent/`, Railway will not find it automatically.

SQLite data lost after redeploy: The Volume is not mounted. Check the Railway
dashboard: the Volume should show as mounted at `/data` and `DB_PATH` must
be `/data/scq.db`. Without the Volume, the file is written to the ephemeral
filesystem and wiped on every deploy.

CORS errors from the frontend: Set `CORS_ORIGIN` to exactly the frontend
URL including the protocol and any port. `https://myapp.com` and
`https://myapp.com/` (trailing slash) are treated as different origins.

---

**Next assignment:** [03-add-production-monitoring.md](03-add-production-monitoring.md)
