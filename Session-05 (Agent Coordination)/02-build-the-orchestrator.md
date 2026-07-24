# Build 02: Build the Orchestrator

**Frameworks applied:** 01 (Agent Mental Model) + 02 (Project Structure)

---

## What the Orchestrator Is

The orchestrator is not an agent. It does not call a language model. It does
not have a system prompt or a tool registry. It is an Express route that
wraps the three existing agent routes behind a single endpoint.

A student sends a message to `POST /api/chat`. The orchestrator:
1. Reads the student's current stage using `getCurrentStage`
2. Selects the appropriate agent (Matteo, Juli, or Tedd)
3. Loads any cross-agent context needed for that agent
4. Calls the agent's underlying Python process and streams the response
5. After the response completes, checks whether the stage is now complete
6. If complete, records the transition so the next call routes differently

The three individual agent routes (`/api/agent1/chat`, `/api/agent2/chat`,
`/api/agent3/chat`) remain in place. They are still used by the test suite
and by professor tooling. The orchestrator is the student-facing endpoint
only.

This is Framework 01 applied at the system level. The individual agents
still follow the five-layer architecture: they have their own infrastructure,
model config, tool registry, context architecture, and prompt. The
orchestrator sits above them and decides which one runs, not how they run.

---

## What You Are Building

```
server/src/routes/orchestrator.js    POST /api/chat handler
server/src/lib/stageManager.js       getCurrentStage, isStageComplete (from Build 01)
server/src/index.js                  Mount /api/chat route
```

---

## The Route Handler

Create `server/src/routes/orchestrator.js`:

```js
import { Router } from 'express';
import { authMiddleware } from '../middleware/auth.js';
import { agentLimiter } from '../middleware/rateLimiter.js';
import { validateAgentMessage } from '../middleware/validator.js';
import { getCurrentStage, isStageComplete, getMatteoHandoff } from '../lib/stageManager.js';
import { callMatteo, callJuli, callTedd } from '../lib/agentCaller.js';

const router = Router();

router.post(
  '/chat',
  authMiddleware,
  agentLimiter,
  validateAgentMessage,
  async (req, res) => {
    const { message } = req.body;
    const user = req.user;

    const stage = await getCurrentStage(user.id);

    if (stage === 'COMPLETE') {
      return res.json({
        message: 'Your coaching journey is complete. Your professor can now review your work.',
        stage: 'COMPLETE',
      });
    }

    const context = stage === 'JULI' ? getMatteoHandoff(user.id) : null;

    try {
      await callAgent(stage, message, context, user, res);
    } catch (err) {
      if (!res.headersSent) {
        res.status(500).json({ error: 'Agent call failed. Please try again.' });
      }
    }
  }
);

async function callAgent(stage, message, context, user, res) {
  const agentMap = {
    MATTEO: callMatteo,
    JULI: callJuli,
    TEDD: callTedd,
  };

  const agentFn = agentMap[stage];
  if (!agentFn) throw new Error(`Unknown stage: ${stage}`);

  await agentFn(message, context, user, res);
}

export default router;
```

---

## The Agent Caller Module

The orchestrator delegates the actual agent call to a thin wrapper module.
Each function in this module does what the individual agent routes did in
Session 03, but extracted so the orchestrator can call them without
duplicating route handler logic.

Create `server/src/lib/agentCaller.js`:

```js
import { spawn } from 'child_process';
import { getOrCreateSession, appendTurn } from '../db.js';
import { getMatteoHandoff } from './stageManager.js';

export async function callMatteo(message, _context, user, res) {
  const session = getOrCreateSession(user.id, 'matteo', user.cohortId);
  const history = JSON.parse(session.messages || '[]')
    .filter(m => m.role && m.content);

  const progress = getMatteoHandoff(user.id);
  const injectedContext = buildMatteoContext(progress);

  await streamAgent('agent1', message, history, injectedContext, user, session, res);
}

export async function callJuli(message, scqContext, user, res) {
  const session = getOrCreateSession(user.id, 'juli', user.cohortId);
  const messages = JSON.parse(session.messages || '{}');
  const history = (messages.turns || []).filter(m => m.role && m.content);
  const currentStage = messages.current_stage || 'Attention';

  const injectedContext = buildJuliContext(currentStage, scqContext);

  await streamAgent('agent2', message, history, injectedContext, user, session, res);
}

export async function callTedd(message, _context, user, res) {
  const session = getOrCreateSession(user.id, 'tedd', user.cohortId);

  if (session.finalised === 1) {
    res.status(409).json({ error: 'This session has already been evaluated.' });
    return;
  }

  const history = JSON.parse(session.messages || '[]')
    .filter(m => m.role && m.content);

  await streamAgent('agent3', message, history, null, user, session, res);
}

function buildMatteoContext(progress) {
  if (!progress) return '';
  const parts = [];
  if (progress.situation) parts.push(`Situation: ${progress.situation}`);
  if (progress.complication) parts.push(`Complication: ${progress.complication}`);
  if (progress.question) parts.push(`Question: ${progress.question}`);
  if (parts.length === 0) return '';
  return `\n\nCURRENT SESSION CONTEXT\n${parts.join('\n')}`;
}

function buildJuliContext(currentStage, scq) {
  let context = `\n\nCURRENT SESSION CONTEXT\nActive stage: ${currentStage}`;
  if (scq?.situation) {
    context += `\n\nSTUDENT'S CONFIRMED SCQ\nSituation: ${scq.situation}`;
    if (scq.complication) context += `\nComplication: ${scq.complication}`;
    if (scq.question) context += `\nQuestion: ${scq.question}`;
  }
  return context;
}

async function streamAgent(agentId, message, history, injectedContext, user, session, res) {
  // Set SSE headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  const agentInput = JSON.stringify({
    message,
    history,
    user_id: user.id,
    session_id: session.id,
    injected_context: injectedContext,
    agent_id: agentId,
  });

  const python = spawn('python3', ['-m', `agent.runner`], {
    env: { ...process.env },
  });

  python.stdin.write(agentInput);
  python.stdin.end();

  let fullResponse = '';

  python.stdout.on('data', (chunk) => {
    const token = chunk.toString();
    fullResponse += token;
    res.write(`data: ${JSON.stringify({ token })}\n\n`);
  });

  python.stderr.on('data', (data) => {
    console.error(`[${agentId}] stderr:`, data.toString());
  });

  python.stdout.on('end', () => {
    appendTurn(session.id, 'user', message);
    appendTurn(session.id, 'assistant', fullResponse);
    res.write(`data: ${JSON.stringify({ done: true, stage: agentId })}\n\n`);
    res.end();
  });

  python.on('error', (err) => {
    console.error(`[${agentId}] spawn error:`, err);
    if (!res.headersSent) {
      res.status(500).json({ error: 'Agent unavailable.' });
    }
  });
}
```

---

## Mounting the Route

In `server/src/index.js`, import and mount the orchestrator route:

```js
import orchestratorRoutes from './routes/orchestrator.js';

app.use('/api', orchestratorRoutes);
```

This makes `POST /api/chat` available. The existing `/api/agent1/chat`,
`/api/agent2/chat`, and `/api/agent3/chat` routes remain mounted and
unchanged for the test suite and professor tooling.

---

## The Stage After Routing

After the orchestrator streams a response, the client receives a `done`
event. The client can include the current stage in follow-up requests so
the UI can update (for example, showing a progress indicator).

The orchestrator also includes the resolved stage in the `done` event:

```js
res.write(`data: ${JSON.stringify({ done: true, stage: agentId })}\n\n`);
```

The client can use this to display "Matteo session" or "Moving to Juli" as
the student progresses, without the client needing to derive the stage itself.

---

## What the CLAUDE.md Now Records

After completing this document, your CLAUDE.md records:

```
Orchestrator Route:
  POST /api/chat    Student-facing endpoint, auth + agentLimiter + validateAgentMessage
  File: server/src/routes/orchestrator.js
  Logic: reads stage -> selects agent -> loads context -> streams response

Agent Caller:
  File: server/src/lib/agentCaller.js
  callMatteo(message, context, user, res)
  callJuli(message, scqContext, user, res)
  callTedd(message, context, user, res)

Individual routes /api/agent1,2,3/chat remain for test suite and professor tooling.
```

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code already
knows from your CLAUDE.md the agent route pattern, how SSE streaming works,
and how the individual agent routes call the Python agent via spawn.

**Prompt to build the orchestrator:**

```
Build the orchestrator for the SCQ platform.

1. Create server/src/lib/agentCaller.js with three exported async functions:
   callMatteo, callJuli, callTedd. Each takes (message, context, user, res).

   Each function:
   - Gets or creates the session using getOrCreateSession(user.id, agentId, user.cohortId)
   - Builds the agent input JSON with message, history, user_id, session_id,
     injected_context, and agent_id
   - Sets SSE response headers and calls res.flushHeaders()
   - Spawns python3 with the agent runner
   - Pipes the agent output to the SSE stream
   - On stdout end: appends turns to the DB and sends the done event

   callJuli additionally reads scqContext and builds the STUDENT'S CONFIRMED SCQ
   block for injection alongside the active stage context.
   callTedd additionally checks session.finalised === 1 and returns 409 if so.

2. Create server/src/routes/orchestrator.js with a single POST /chat route.
   Apply authMiddleware, agentLimiter, and validateAgentMessage in that order.
   Call getCurrentStage from stageManager.js to get the stage.
   If stage is COMPLETE, return a JSON message (no SSE, no agent call).
   Otherwise call the appropriate function from agentCaller.js.

3. In server/src/index.js, mount the orchestrator at /api.
   Keep the existing /api/agent1, /api/agent2, /api/agent3 routes unchanged.

The orchestrator must apply the same security middleware chain as the
individual routes: authMiddleware then agentLimiter then validateAgentMessage.
Do not bypass any of these.
```

**What Claude Code will do:**
Create both new files and update index.js to mount the new route. It will
read the existing individual route files to match the SSE streaming pattern
and the spawn approach, keeping them consistent.

**Tips for this document:**
- After Claude Code generates the orchestrator, test it with a student account
  that has no sessions. Send a message to `POST /api/chat`. Confirm the
  response comes from Matteo (check the `done` event's `stage` field).
- If the stage is always MATTEO even for a student with a complete SCQ, ask
  Claude Code: "Call getCurrentStage with a test user ID and log the result.
  Is stageManager reading the right user_id?"
- Tell Claude Code: "Do not merge the agent caller logic into the orchestrator
  route file. Keep them in separate files. agentCaller.js is imported by
  orchestrator.js."

---

**Next:** [03-manage-cross-agent-context.md](03-manage-cross-agent-context.md)

---

Copyright Janna AI Research Labs
