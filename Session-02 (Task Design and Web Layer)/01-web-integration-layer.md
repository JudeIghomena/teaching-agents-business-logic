# Build 01: The Web Integration Layer

> Your agent does not live in a Python file. It lives inside a web application.
> Before you design a single task or write a single prompt, you need to understand
> the container your agent runs in and exactly what it receives and returns.

---

## The Journey of One User Message

When a student types a message to Matteo and presses send, here is what happens:

```
Browser (React)
    │
    │  POST /api/agent1/chat
    │  Headers: Authorization: Bearer <jwt>
    │  Body: { message: "The situation is..." }
    │
    ▼
Express Server
    │
    ├── authMiddleware          Is this a valid, logged-in user?
    │                          Extract user_id, role, cohort_id from JWT
    │
    ├── Load session history    SELECT messages FROM agent1_sessions
    │                          WHERE user_id = $1 AND cohort_id = $2
    │
    ├── Call the agent         Pass: system prompt + history + new message
    │                          Receive: token stream from Claude API
    │
    ├── Stream tokens back     SSE: text/event-stream
    │   to browser             data: { token: "The " }
    │                          data: { token: "situation " }
    │                          data: { token: "..." }
    │                          data: { done: true }
    │
    └── Save response          INSERT new message pair into agent1_sessions
        to database
    │
    ▼
Browser renders
the reply token by token
```

Each box in that chain is a responsibility. The agent is responsible for
one box: receiving the prepared input and returning a token stream. Every
other box is the web layer's job.

This separation matters. Your agent code does not know about HTTP, JWTs,
or databases. It receives a message and a history and returns a response.
The web layer handles everything else.

---

## The Express Route

An Express route is a function that receives an HTTP request and sends back
a response. For an agent endpoint it does five things in order:

1. Authenticate the caller
2. Load context from the database
3. Call the agent
4. Stream the response
5. Save the result

Here is the minimal pattern, annotated:

```javascript
// server/routes/agent1.js

import express from 'express';
import { authMiddleware } from '../middleware/auth.js';
import { db } from '../db.js';
import { streamWithAgent } from '../lib/agentRunner.js';

const router = express.Router();

router.post('/chat', authMiddleware, async (req, res) => {

  // Step 1: Extract what we know about the caller from the JWT.
  // authMiddleware already verified the token. We trust these values.
  const { userId, cohortId } = req.user;
  const { message } = req.body;

  // Step 2: Validate the incoming message.
  // Never pass raw user input directly to the agent without checking it.
  if (!message || typeof message !== 'string' || message.trim().length === 0) {
    return res.status(400).json({ error: 'Message is required' });
  }

  // Step 3: Load the student's conversation history from the database.
  // This is what gives the agent memory across browser refreshes.
  const session = await db.query(
    `SELECT messages FROM agent1_sessions
     WHERE user_id = $1 AND cohort_id = $2`,
    [userId, cohortId]
  );
  const history = session.rows[0]?.messages ?? [];

  // Step 4: Set up Server-Sent Events so tokens stream to the browser.
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  // Step 5: Call the agent and stream tokens back as they arrive.
  let fullResponse = '';

  await streamWithAgent({
    history,
    newMessage: message,
    onToken: (token) => {
      fullResponse += token;
      res.write(`data: ${JSON.stringify({ token })}\n\n`);
    },
    onDone: () => {
      res.write(`data: ${JSON.stringify({ done: true })}\n\n`);
      res.end();
    }
  });

  // Step 6: Save the new message pair to the database.
  // The agent never writes to the database. The route does.
  const updatedHistory = [
    ...history,
    { role: 'user', content: message },
    { role: 'assistant', content: fullResponse }
  ];

  await db.query(
    `UPDATE agent1_sessions
     SET messages = $1, updated_at = NOW()
     WHERE user_id = $2 AND cohort_id = $3`,
    [JSON.stringify(updatedHistory), userId, cohortId]
  );

});

export default router;
```

This is the complete pattern. Every agent endpoint in the Business Case Logic
platform follows it. Matteo, Juli, and Tedd each have their own route file but
the five steps are identical. What changes per agent is the system prompt,
the session table, and any agent-specific validation logic.

---

## Server-Sent Events

Standard HTTP follows a request/response pattern: the browser sends a request,
the server sends one response, the connection closes. That does not work for AI
agents because a single response can take 10-30 seconds to generate.

Server-Sent Events (SSE) keep the connection open and let the server push data
to the browser in chunks as it becomes available. The browser renders each chunk
as it arrives, which is why you see Claude responses appear word by word.

The browser side opens the connection like this:

```javascript
// client/src/hooks/useAgentStream.js

const response = await fetch('/api/agent1/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ message })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      if (data.token) {
        // Append each token to the displayed response
        setCurrentResponse(prev => prev + data.token);
      }
      if (data.done) {
        // Response complete
        setIsStreaming(false);
      }
    }
  }
}
```

Three rules for SSE in agent applications:

1. Set the correct headers before writing anything. Once you call res.write(),
   headers are locked. Set Content-Type, Cache-Control, and Connection first.

2. Format every chunk as `data: <json>\n\n`. The double newline tells the
   browser the chunk is complete. Missing it causes the browser to buffer
   chunks silently.

3. Always send a done signal. The browser needs to know when the stream ends.
   A connection that hangs open forever wastes resources and confuses users.

---

## What the Agent Receives

The route prepares a clean, structured input for the agent. The agent never
touches the raw HTTP request. It receives:

```python
# agent/matteo.py

def run(history: list, new_message: str, system_prompt: str) -> Iterator[str]:
    """
    history:       list of {"role": "user"/"assistant", "content": "..."} dicts
    new_message:   the student's latest message, already validated
    system_prompt: Matteo's assembled system prompt for this cohort
    """

    messages = history + [{"role": "user", "content": new_message}]

    with anthropic.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=messages
    ) as stream:
        for text in stream.text_stream:
            yield text
```

The agent's job is narrow: take a message list and yield tokens. It does not
know who the student is. It does not know what cohort they are in. It does not
save anything. The route handles all of that. This narrowness is intentional.

It makes the agent testable in isolation: you can call `run()` directly with
any history and message, without spinning up an Express server or a database.

---

## What Gets Saved

Every message pair is saved to the database after the stream completes. This
gives the agent its memory: next time the student sends a message, the full
conversation history is loaded and passed to the agent again.

The session table for Matteo holds:

```
agent1_sessions
  id            UUID primary key
  user_id       FK to users
  cohort_id     FK to cohorts
  messages      JSONB  (the full conversation history)
  quality_score INTEGER  (updated after quality scoring runs)
  finalised     BOOLEAN  (locked once the student finalises)
  created_at    TIMESTAMP
  updated_at    TIMESTAMP
```

This is covered in detail in the next document (02-database-schema-design.md).
What matters here is that the route owns the read and write. The agent owns
nothing outside its own execution.

---

## How This Maps to the SCQ Platform

In the SCQ platform, `server/src/routes/agent1.js` implements exactly this
pattern for Matteo. The route:

- Calls `authMiddleware` on every request
- Resolves the cohort from the `X-Cohort-Id` header via `cohortMiddleware`
- Loads conversation history from `agent1_sessions`
- Calls `streamWithFallback()` in `modelRouter.js` which tries Anthropic
  first, then falls back to Gemini, then OpenAI
- Streams tokens back via SSE
- Saves the response and triggers quality scoring after a minimum message count

The fallback model router is a production detail you add in Session-06. For
now, the single-model pattern above is the right starting point.

---

## The Boundary Principle

The most important thing this document establishes is where the agent's
responsibility ends and the web layer's responsibility begins.

```
Web layer owns:           Agent owns:
  Authentication            Reasoning about the message
  Input validation          Generating a response
  Loading history           Calling tools if needed
  Streaming the response    Knowing its own rules and role
  Saving the result
  Error handling
  Rate limiting
```

Anything in the left column that ends up in agent code is a mistake. It makes
the agent harder to test, harder to replace, and harder to reason about.

---

## Apply to Your Coding Agent

**Task for this document**

Add a web integration block to your CLAUDE.md that defines how the web layer
and the agent layer divide responsibility in your project.

**Copy this template into your CLAUDE.md**

```
## Web Integration Layer

Route pattern: POST /api/[agent-name]/chat
Auth: authMiddleware validates JWT before the route handler runs
What the route passes to the agent:
  - history: list of prior message pairs from the database
  - new_message: the validated user message
  - system_prompt: the assembled prompt for this cohort/context
What the agent returns: a token stream (yielded strings)
What the route owns: streaming the tokens to the browser (SSE),
  saving the message pair to the database, error handling
What the agent never does: read from or write to the database,
  handle HTTP directly, know the caller's identity

Session table: [your-agent-name]_sessions
  messages column: JSONB array of {role, content} pairs
  loaded before each call, saved after the stream completes
```

**What to fill in**

Replace `[agent-name]` with the name of your agent (matteo, juli, tedd).
Replace `[your-agent-name]_sessions` with your actual session table name.
Add any agent-specific fields your session table will need beyond messages
(for example: quality_score, finalised, peer_review_complete).

**How to apply to Claude Code**

Place your updated CLAUDE.md in your project root. Claude Code reads it
automatically. The web integration block tells your coding agent exactly
where the Express route ends and the Python agent begins, so it never
puts database calls inside agent logic.

**How to apply to Cursor**

Copy the same content into `.cursorrules` at your project root:

```bash
cp CLAUDE.md .cursorrules
```

**How to apply to Codex**

Paste the web integration section into your workspace system prompt in
Codex settings. Update it each time you add a new agent route.

---

Copyright Janna AI Research Labs
