# Assignment 02: Build the Orchestrator

**Reads with:** [02-build-the-orchestrator.md](../02-build-the-orchestrator.md)
**Time estimate:** 40-50 minutes
**Frameworks applied:** 01 (Agent Mental Model) + 02 (Project Structure)

---

## What You Are Building

An Express route at `POST /api/chat` that reads the student's current stage
and delegates to the correct agent. A supporting module, `agentCaller.js`,
that handles the actual agent invocation and SSE streaming.

---

## Steps

### Step 1: Create agentCaller.js

Create `server/src/lib/agentCaller.js` with three exported async functions:
`callMatteo`, `callJuli`, and `callTedd`.

Each function must:
- Get or create the session with `getOrCreateSession`
- Build the injected context string
- Set SSE response headers and call `res.flushHeaders()`
- Spawn the Python agent with `child_process.spawn`
- Stream stdout tokens to the client
- Call `appendTurn` when stdout ends
- Send the `done` event with the stage name

`callTedd` additionally checks `session.finalised === 1` and returns 409
if Tedd is already finalised. This prevents double evaluation.

### Step 2: Create orchestrator.js

Create `server/src/routes/orchestrator.js` with a single `POST /chat` route.

Apply the middleware chain in this exact order:
1. `authMiddleware`
2. `agentLimiter`
3. `validateAgentMessage`
4. The route handler

If stage is `COMPLETE`, return a plain JSON response. Do not start an SSE
stream. Do not call any agent.

### Step 3: Mount the route

In `server/src/index.js`, import `orchestratorRoutes` and mount it:

```js
import orchestratorRoutes from './routes/orchestrator.js';
app.use('/api', orchestratorRoutes);
```

Do not remove the existing `/api/agent1`, `/api/agent2`, `/api/agent3` routes.

### Step 4: Manual end-to-end test

1. Create a student account (POST /api/auth/signup)
2. Log in and copy the JWT
3. Send a message to POST /api/chat with the JWT
4. Confirm the response streams from Matteo (check the `done` event's
   `stage` field equals "agent1")
5. Look at the server logs for the `[orchestrator]` log lines

### Step 5: Verify middleware is present

```bash
grep -n "authMiddleware\|agentLimiter\|validateAgentMessage" server/src/routes/orchestrator.js
```

All three must appear. The orchestrator must not bypass security middleware.

---

## Done Checklist

- [ ] `server/src/lib/agentCaller.js` exists with three exported functions
- [ ] Each caller sets SSE headers before spawning Python
- [ ] `appendTurn` is called only in the `stdout.on('end')` handler
- [ ] `callTedd` returns 409 if the session is already finalised
- [ ] `server/src/routes/orchestrator.js` exists with POST /chat handler
- [ ] Middleware chain: authMiddleware -> agentLimiter -> validateAgentMessage -> handler
- [ ] COMPLETE stage returns JSON, not SSE
- [ ] Route mounted in index.js at /api
- [ ] Individual agent routes still present and unchanged
- [ ] Manual test confirms Matteo responds for a new student

---

## Troubleshooting

POST /api/chat returns 404: Confirm the route is mounted with
`app.use('/api', orchestratorRoutes)` (not `app.use('/api/chat', ...)`).
The route file registers `/chat` and the mount point adds `/api`.

SSE stream never ends: The Python process is still running. Check the
`python.stdout.on('end')` handler is calling `res.end()`. If it is
missing, the client hangs forever waiting for the stream to close.

Route always routes to MATTEO: Add a console.log in the orchestrator
to print `getCurrentStage(user.id)` on every request. Confirm the userId
in the log matches the user whose sessions you seeded. If the ID is different,
the authMiddleware is returning a different user than you expect.

---

**Next assignment:** [03-manage-cross-agent-context.md](03-manage-cross-agent-context.md)
