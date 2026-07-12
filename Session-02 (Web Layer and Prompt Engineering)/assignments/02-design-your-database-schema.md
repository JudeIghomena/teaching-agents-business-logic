# Assignment 02: Design Your Database Schema

**What you are building:** The sessions table that stores every conversation turn your agents have with students, and the two helper functions that read and write it
**Why it matters:** Without a database, every agent session is stateless. The moment a user refreshes the page or the server restarts, the conversation is gone. This assignment makes the platform persistent.
**Time estimate:** 45 minutes
**Reads with:** 02-database-schema-design.md

---

## What You Are Going To Do

You are going to create a SQLite database with one table, write two helper functions that the Express routes will use to load history and save turns, and wire those functions into the agent route you built in Assignment 01.

---

## What the Schema Must Do

The agent_sessions table has one job: store every conversation turn so the agent can see what was said before. It needs to do three things correctly:

```
1. Scope by user and agent    Each row belongs to one user AND one agent
2. Store turns as JSON        A single text column holding the full turn array
3. Track timestamps           So sessions can be sorted and the professor sees recent work
```

Never store turns in separate rows. One row per session. Turns are a JSON array inside the messages column. This makes loading history a single database read, not a join.

---

## Step 1: Create the Database Module

Create `server/src/db.js`:

```js
const Database = require('better-sqlite3');
const path = require('path');

const DB_PATH = process.env.DB_PATH || path.join(process.cwd(), 'data', 'scq.db');
const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');

module.exports = db;
```

The `WAL` pragma (Write-Ahead Logging) allows concurrent reads while a write is in progress. Without it, a write from one route can block reads from another.

---

## Step 2: Create the Schema Init Script

Create `server/src/db-init.js`:

```js
const db = require('./db');

db.exec(`
    CREATE TABLE IF NOT EXISTS agent_sessions (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id       TEXT    NOT NULL,
        cohort_id     TEXT    NOT NULL,
        agent_id      TEXT    NOT NULL,
        messages      TEXT    NOT NULL DEFAULT '[]',
        quality_score REAL,
        finalised     INTEGER NOT NULL DEFAULT 0,
        created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
        updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS users (
        id            TEXT    PRIMARY KEY,
        email         TEXT    NOT NULL UNIQUE,
        password_hash TEXT    NOT NULL,
        role          TEXT    NOT NULL DEFAULT 'student',
        cohort_id     TEXT    NOT NULL,
        created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
    );
`);

console.log('Database initialised.');
process.exit(0);
```

Add the init script to package.json:

```json
"scripts": {
    "db:init": "node server/src/db-init.js"
}
```

Run it:

```bash
mkdir -p data
npm run db:init
```

---

## Step 3: Write getOrCreateSession

Add this function to `server/src/db.js`:

```js
function getOrCreateSession(userId, cohortId, agentId) {
    const existing = db.prepare(
        'SELECT * FROM agent_sessions WHERE user_id = ? AND agent_id = ? ORDER BY created_at DESC LIMIT 1'
    ).get(userId, agentId);

    if (existing) return existing;

    const result = db.prepare(
        'INSERT INTO agent_sessions (user_id, cohort_id, agent_id) VALUES (?, ?, ?)'
    ).run(userId, cohortId, agentId);

    return db.prepare('SELECT * FROM agent_sessions WHERE id = ?').get(result.lastInsertRowid);
}

module.exports = { db, getOrCreateSession };
```

The query scopes to both user_id and agent_id. This is intentional: Matteo, Juli, and Tedd each have their own session record per student. A student's Matteo conversation is separate from their Juli conversation.

---

## Step 4: Write appendTurn

Add this function to `server/src/db.js`:

```js
function appendTurn(sessionId, userMessage, agentResponse) {
    const row = db.prepare('SELECT messages FROM agent_sessions WHERE id = ?').get(sessionId);
    const turns = JSON.parse(row.messages);

    turns.push({ role: 'user', content: userMessage });
    turns.push({ role: 'assistant', content: agentResponse });

    db.prepare(
        "UPDATE agent_sessions SET messages = ?, updated_at = datetime('now') WHERE id = ?"
    ).run(JSON.stringify(turns), sessionId);
}

module.exports = { db, getOrCreateSession, appendTurn };
```

Both the user message and the agent response are appended in one operation. The turns array is always a valid Anthropic messages format, so it can be passed directly to the API in the next turn.

---

## Step 5: Wire Into the Agent Route

Update `server/src/routes/agent1.js` to use the database functions:

```js
const { getOrCreateSession, appendTurn } = require('../db');

router.post('/chat', authMiddleware, async (req, res) => {
    const { message } = req.body;
    const { user_id, cohort_id } = req.user;

    // Load history
    const session = getOrCreateSession(user_id, cohort_id, 'matteo');
    const history = JSON.parse(session.messages);

    setupSSE(res);

    const agentInput = JSON.stringify({ user_id, cohort_id, message, history });
    const python = spawn('python', ['agent/runner.py'], { cwd: process.cwd() });

    python.stdin.write(agentInput);
    python.stdin.end();

    let fullResponse = '';

    python.stdout.on('data', (chunk) => {
        const token = chunk.toString();
        fullResponse += token;
        sendToken(res, token);
    });

    python.stdout.on('end', () => {
        appendTurn(session.id, message, fullResponse);
        sendDone(res);
    });

    python.stderr.on('data', (err) => {
        console.error(`[agent1] python error: ${err}`);
    });
});
```

---

## Step 6: Test Persistence

Send two messages to the agent:

```bash
# First message
curl -N -X POST http://localhost:3001/api/agent1/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "The situation is that our client is a bank."}'

# Second message (agent should remember the first)
curl -N -X POST http://localhost:3001/api/agent1/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "The complication is that they are losing customers."}'
```

After the second message, check the database:

```bash
sqlite3 data/scq.db "SELECT messages FROM agent_sessions WHERE agent_id='matteo';"
```

You should see both turns in the messages JSON array.

---

## You Are Done When

- [ ] `npm run db:init` creates the database without errors
- [ ] `data/scq.db` exists and has both the agent_sessions and users tables
- [ ] getOrCreateSession returns the same session on the second call for the same user
- [ ] appendTurn adds two entries to the messages array (user turn + assistant turn)
- [ ] A second message to the agent receives a response that references the first

---

## If You Get Stuck

Database file not found: confirm the `data/` directory exists before running the init script. Run `mkdir -p data` first.

Session returns a new row every time instead of the same one: the query in getOrCreateSession is missing the `LIMIT 1`. Without it, if there are multiple sessions for the same user, the function creates a new one every time instead of returning the most recent.

Agent does not remember the first message: confirm you are passing `history` to the Python agent in the stdin JSON. Print `data["history"]` inside runner.py to verify it is arriving.

---

## Next Assignment

[03-implement-jwt-authentication.md](03-implement-jwt-authentication.md)

---

Copyright Janna AI Research Labs
