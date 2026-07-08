# Assignment 01: Build Your Agent Route

**What you are building:** The Express route that receives a user message, authenticates the request, calls your agent, and streams the response back token by token
**Why it matters:** The agent you built in Session-01 runs in isolation. This assignment puts it inside a web application. Once this route exists, any authenticated user with a browser can talk to your agent in real time.
**Time estimate:** 60 minutes
**Reads with:** 01-web-integration-layer.md

---

## What You Are Going To Do

You are going to wire up five pieces in sequence: an Express server, an auth middleware that reads a JWT, an SSE response stream, a call to your Python agent, and a save-to-database step. By the end, a browser request reaches the agent and gets a streamed reply.

---

## What the Route Must Do

Every agent route on the Business Case Logic platform follows this sequence:

```
1. Authenticate     Is this a valid JWT? Extract user_id and role.
2. Validate         Does the request body have a message field?
3. Load history     Read past turns from the database for this user.
4. Call agent       Pass system prompt + history + new message. Get a stream.
5. Stream back      Send each token to the browser as a Server-Sent Event.
6. Save response    Write the new turn to the database once the stream ends.
```

Do not skip steps or reorder them. Skipping auth means any unauthenticated request can drive your agent. Saving before streaming means users wait longer before seeing the first token.

---

## Step 1: Set Up the Express Server

Create your project structure:

```bash
mkdir -p scq-platform/server/src/routes
mkdir -p scq-platform/server/src/middleware
cd scq-platform/server
npm init -y
npm install express jsonwebtoken better-sqlite3 dotenv
```

Create `server/src/index.js`:

```js
const express = require('express');
const dotenv = require('dotenv');
dotenv.config();

const app = express();
app.use(express.json());

const agentRoutes = require('./routes/agent1');
app.use('/api/agent1', agentRoutes);

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
```

---

## Step 2: Write the Auth Middleware

The auth middleware reads the Authorization header, verifies the JWT, and attaches the decoded payload to `req.user`. Every route that calls an agent must use this middleware.

Create `server/src/middleware/auth.js`:

```js
const jwt = require('jsonwebtoken');

function authMiddleware(req, res, next) {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'Missing or malformed token' });
    }

    const token = authHeader.split(' ')[1];
    try {
        const payload = jwt.verify(token, process.env.JWT_SECRET, {
            algorithms: ['HS256']
        });
        req.user = payload;
        next();
    } catch (err) {
        return res.status(401).json({ error: 'Invalid or expired token' });
    }
}

module.exports = authMiddleware;
```

Three things to notice in this implementation:

- `algorithms: ['HS256']` is required. Without it, an attacker can send a token signed with `alg: none` and the JWT library will accept it.
- The full error is never sent to the client. The client receives "Invalid or expired token". The real error stays server-side.
- The middleware calls `next()` only on success. On failure it returns immediately.

---

## Step 3: Set Up SSE Headers

Server-Sent Events use a specific Content-Type and three mandatory headers. If any header is missing, the browser will not treat the response as a stream and the user will see nothing until the entire response completes.

Add this helper at the top of your route file:

```js
function setupSSE(res) {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders();
}

function sendToken(res, token) {
    res.write(`data: ${JSON.stringify({ token })}\n\n`);
}

function sendDone(res) {
    res.write(`data: ${JSON.stringify({ done: true })}\n\n`);
    res.end();
}
```

The `\n\n` at the end of each SSE message is not optional. The SSE specification requires two newlines to terminate each event. A single newline will cause the browser to buffer and wait for the second one indefinitely.

---

## Step 4: Write the Agent Route

Create `server/src/routes/agent1.js`:

```js
const express = require('express');
const { spawn } = require('child_process');
const authMiddleware = require('../middleware/auth');

const router = express.Router();

router.post('/chat', authMiddleware, async (req, res) => {
    const { message } = req.body;

    if (!message || typeof message !== 'string' || message.trim().length === 0) {
        return res.status(400).json({ error: 'message is required' });
    }

    const { user_id, cohort_id } = req.user;

    // Step 3: Load history from database
    // Replace with your actual DB call once you complete Assignment 02
    const history = [];

    // Step 4: Set up SSE
    setupSSE(res);

    // Step 5: Call the Python agent and stream back
    // The Python agent reads user_id, message, and history from stdin as JSON
    const agentInput = JSON.stringify({ user_id, cohort_id, message, history });
    const python = spawn('python', ['agent/runner.py'], {
        cwd: process.cwd()
    });

    python.stdin.write(agentInput);
    python.stdin.end();

    let fullResponse = '';

    python.stdout.on('data', (chunk) => {
        const token = chunk.toString();
        fullResponse += token;
        sendToken(res, token);
    });

    python.stdout.on('end', () => {
        sendDone(res);
        // Step 6: Save to database (implement in Assignment 02)
        console.log(`[agent1] turn complete for user ${user_id}`);
    });

    python.stderr.on('data', (err) => {
        console.error(`[agent1] python error: ${err}`);
    });
});

module.exports = router;
```

---

## Step 5: Update the Python Agent to Accept Stdin

Your Session-01 agent read user input interactively. The web layer sends input via stdin as JSON. Update `agent/runner.py` to accept this format:

```python
import sys
import json

if __name__ == "__main__":
    # Read input from the web layer
    raw = sys.stdin.read()
    data = json.loads(raw)

    user_id = data["user_id"]
    message = data["message"]
    history = data.get("history", [])

    # Call your existing agent loop
    response = run_agent_loop(message, history)

    # Write the response to stdout so the Express route can stream it
    sys.stdout.write(response)
    sys.stdout.flush()
```

---

## Step 6: Create Your .env File

Create `server/.env`:

```
JWT_SECRET=replace-with-a-long-random-string-minimum-32-chars
PORT=3001
```

Add `server/.env` to `.gitignore`:

```bash
echo ".env" >> .gitignore
```

---

## Step 7: Test the Route

Start the server:

```bash
cd server && node src/index.js
```

Generate a test token (run once in a Node.js shell):

```js
const jwt = require('jsonwebtoken');
const token = jwt.sign(
    { user_id: 'test-user-01', cohort_id: 'cohort-a', role: 'student' },
    'replace-with-a-long-random-string-minimum-32-chars',
    { expiresIn: '1h', algorithm: 'HS256' }
);
console.log(token);
```

Send a test request with curl:

```bash
curl -N -X POST http://localhost:3001/api/agent1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"message": "My situation is that our client is losing market share."}'
```

You should see tokens streaming to the terminal one by one. The `-N` flag disables buffering so you see each token as it arrives.

---

## You Are Done When

- [ ] `node src/index.js` starts without errors
- [ ] A request without an Authorization header returns 401
- [ ] A request with a valid token reaches the agent
- [ ] Tokens stream to the terminal one by one, not all at once at the end
- [ ] The Python agent reads from stdin and writes to stdout correctly
- [ ] No JWT secret appears in any source file - only in `.env`
- [ ] `.env` is confirmed gitignored

---

## If You Get Stuck

Server returns 401 on every request: confirm the token was signed with the same JWT_SECRET value that is in `.env`. A mismatch in the secret is the most common cause.

Nothing streams and then all tokens arrive at once: remove the `-N` flag check first. If tokens come all at once even with buffering disabled, confirm `res.flushHeaders()` is called before any `res.write()`. Without `flushHeaders()`, Express buffers the response.

Python agent not found: confirm the `cwd` in the `spawn` call points to the directory that contains the `agent/` folder. Use an absolute path if needed.

Tokens appear as garbled characters: the Python agent may be writing bytes instead of strings. Add `.decode('utf-8')` when reading chunks, or confirm the Python file uses `sys.stdout.write()` not `sys.stdout.buffer.write()`.

---

## Next Assignment

[02-design-your-database-schema.md](02-design-your-database-schema.md)

---

Copyright Janna AI Research Labs
