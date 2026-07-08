# Build 02: Database Schema Design

> Framework 09 (Memory and State) introduced three tiers of memory.
> Tier 3 in Session One was a JSON file on disk. On the SCQ platform it is
> a database table. The principle is identical. The implementation is production-ready.

**Applies:** Framework 09 (Memory and State)
**Builds:** The sessions table that stores every Matteo, Juli, and Tedd conversation

---

## What Changes and What Stays the Same

In Session One you built a persistent store using a JSON file:

```python
# Session One: Tier 3 memory
def set(key: str, value) -> None:
    data = load()
    data[key] = value
    save(data)
```

That pattern is correct. The principle does not change in Session Two. What changes
is the storage layer underneath it. A JSON file cannot handle multiple users
reading and writing simultaneously. A database can.

The three-tier model from Framework 09 still applies exactly:

```
Tier 1: In-context history       The messages list passed to the API
Tier 2: Session store            A Python dict, cleared on restart
Tier 3: Database                 Rows in agent1_sessions, survive restarts
```

The only thing that changes is how Tier 3 is implemented.

---

## What the SCQ Platform Needs to Store

Before writing a schema, define what the platform must remember and for how long.

| What to store | Who needs it | How long |
|---|---|---|
| Every turn in a student's session with Matteo | Matteo, the web layer | Until the cohort ends |
| Every turn in a student's session with Juli | Juli, the web layer | Until the cohort ends |
| Every turn in a student's session with Tedd | Tedd, the web layer | Until the cohort ends |
| Quality score for each completed session | Professor dashboard | Permanently |
| Whether a session has been finalised | Platform logic | Permanently |

One sessions table serves all three agents. The `agent_id` column identifies
which agent the row belongs to.

---

## The Sessions Table

```sql
CREATE TABLE IF NOT EXISTS agent_sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL,
    cohort_id   TEXT    NOT NULL,
    agent_id    TEXT    NOT NULL,
    messages    TEXT    NOT NULL DEFAULT '[]',
    quality_score REAL,
    finalised   INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_agent
    ON agent_sessions (user_id, agent_id);
```

Column decisions:

- `messages` stores the conversation history as a JSON string. The web layer
  serialises and deserialises it. The agent never touches the database directly.
- `agent_id` is a string: `'matteo'`, `'juli'`, or `'tedd'`. This lets you
  add agents later without changing the schema.
- `finalised` is 0 or 1. A finalised session is locked. No new turns can be
  added. The professor can score it.
- `quality_score` is nullable. It is written when the session is finalised
  and scored by the evaluation layer (Session Two, document 08).

---

## The Two Queries the Web Layer Needs

Every agent route needs exactly two database operations: load history before
calling the agent, and save the new turn after.

**Load history:**

```js
// server/src/db.js

const Database = require('better-sqlite3');
const path = require('path');

const db = new Database(path.join(__dirname, '../../data/scq.db'));

function getOrCreateSession(userId, cohortId, agentId) {
    let session = db.prepare(`
        SELECT id, messages
        FROM agent_sessions
        WHERE user_id = ? AND cohort_id = ? AND agent_id = ? AND finalised = 0
        ORDER BY created_at DESC
        LIMIT 1
    `).get(userId, cohortId, agentId);

    if (!session) {
        const result = db.prepare(`
            INSERT INTO agent_sessions (user_id, cohort_id, agent_id, messages)
            VALUES (?, ?, ?, '[]')
        `).run(userId, cohortId, agentId);

        session = { id: result.lastInsertRowid, messages: '[]' };
    }

    return {
        sessionId: session.id,
        history: JSON.parse(session.messages)
    };
}

module.exports = { db, getOrCreateSession };
```

**Save new turn:**

```js
function appendTurn(sessionId, userMessage, agentResponse) {
    const session = db.prepare(
        'SELECT messages FROM agent_sessions WHERE id = ?'
    ).get(sessionId);

    const history = JSON.parse(session.messages);
    history.push({ role: 'user', content: userMessage });
    history.push({ role: 'assistant', content: agentResponse });

    db.prepare(
        'UPDATE agent_sessions SET messages = ?, updated_at = datetime("now") WHERE id = ?'
    ).run(JSON.stringify(history), sessionId);
}

module.exports = { db, getOrCreateSession, appendTurn };
```

---

## Connecting the Database to the Route

Update the agent route from document 01 to use these queries:

```js
// In routes/agent1.js

const { getOrCreateSession, appendTurn } = require('../db');

router.post('/chat', authMiddleware, async (req, res) => {
    const { message } = req.body;
    if (!message) return res.status(400).json({ error: 'message is required' });

    const { user_id, cohort_id } = req.user;

    // Load history from Tier 3
    const { sessionId, history } = getOrCreateSession(user_id, cohort_id, 'matteo');

    setupSSE(res);

    const agentInput = JSON.stringify({ user_id, cohort_id, message, history });
    const python = spawn('python', ['agent/runner.py']);

    python.stdin.write(agentInput);
    python.stdin.end();

    let fullResponse = '';

    python.stdout.on('data', (chunk) => {
        const token = chunk.toString();
        fullResponse += token;
        sendToken(res, token);
    });

    python.stdout.on('end', () => {
        // Save to Tier 3
        appendTurn(sessionId, message, fullResponse);
        sendDone(res);
    });
});
```

---

## Initialising the Database

Create a setup script that runs once:

```js
// server/src/db-init.js

const { db } = require('./db');

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

    CREATE INDEX IF NOT EXISTS idx_sessions_user_agent
        ON agent_sessions (user_id, agent_id);
`);

console.log('Database initialised.');
```

Add a script to `package.json`:

```json
"scripts": {
    "start": "node src/index.js",
    "db:init": "node src/db-init.js"
}
```

Run once before starting the server:

```bash
npm run db:init
```

---

## What the Agent Must Never Do

The agent does not interact with the database. Ever.

The agent receives history as a Python list. It returns a response string.
It does not know whether that history came from a database, a file, or a dict.
It does not save anything. That is the web layer's job.

This boundary is Framework 01 (Agent Mental Model) enforced: the agent's job
is reasoning. The web layer's job is persistence.

```
Correct:    web layer reads DB → passes history to agent → agent responds → web layer writes DB
Incorrect:  agent reads DB → agent responds → agent writes DB
```

If you find yourself importing a database driver inside a Python agent file,
stop. Move that code to the Express route.

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code reads
your CLAUDE.md automatically and already knows your layer ownership rules:
the database belongs to the web layer, not the agent.

**Prompt to implement the database schema:**

```
Implement the database layer for the SCQ platform using better-sqlite3.
Create two files:

1. server/src/db.js - singleton db instance, getOrCreateSession(userId, cohortId, agentId)
   and appendTurn(sessionId, userMessage, agentResponse)
2. server/src/db-init.js - creates the agent_sessions and users tables,
   run with: npm run db:init

The agent_sessions table needs: id, user_id, cohort_id, agent_id, messages (JSON string),
quality_score (nullable), finalised (0 or 1), created_at, updated_at.
Add an index on (user_id, agent_id).

Then update routes/agent1.js to call getOrCreateSession before the agent
and appendTurn after the stream ends. The agent receives history as a parsed
list, not a raw database object.
```

**What Claude Code will do:**
Create both files, wire the DB functions into the existing agent route, and
keep the boundary clean: the agent receives a plain Python list, not a
database connection or query result.

**Tips for this document:**
- If Claude Code adds a DB import to the Python agent files, ask it to remove it.
  The layer ownership section of your CLAUDE.md makes this explicit.
- Run `npm run db:init` before testing. If the table already exists the script
  is safe to re-run because the schema uses `CREATE TABLE IF NOT EXISTS`.
- To inspect the database: `sqlite3 data/scq.db ".tables"` and
  `sqlite3 data/scq.db "SELECT * FROM agent_sessions LIMIT 5;"`

---

## Starter Code

Working implementation in `starter-code/02-database-schema/`:

```
02-database-schema/
├── db.js           getOrCreateSession, appendTurn, db singleton
├── db-init.js      Schema creation script
└── schema.sql      Raw SQL for reference and migration tooling
```

---

## Assignment

[02-design-your-database-schema.md](assignments/02-design-your-database-schema.md)

---

Copyright Janna AI Research Labs
