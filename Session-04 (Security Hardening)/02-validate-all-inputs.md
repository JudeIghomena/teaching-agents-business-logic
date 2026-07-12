# Build 02: Validate All Inputs

**Frameworks applied:** 11 (Security Baseline) + 06 (Tool Design)

---

## Why Input Validation Is the Web Layer's Job

In Session 03 you gave each agent a clearly defined task scope. Matteo
only handles SCQ coaching. Juli only handles Monroe's Sequence. Tedd only
evaluates completed deliverables. The system prompt enforces those
boundaries at the model layer.

But the model layer is not the right place to enforce message structure.
The model reasons about content. The web layer validates shape.

Consider what happens without validation:

A student pastes a 100,000-word document into the chat box and sends it to
Matteo. The Python agent receives it and builds the message history. The
context window fills immediately. The call fails with a token limit error,
or worse, it succeeds and eats the entire session budget on a single turn.

A student sends a message that is not a string: `{"message": null}`. The
JavaScript route tries to use it as a string, throws an uncaught exception,
and crashes the worker process.

A student sends an empty string. The agent receives an empty user turn and
may produce an incoherent response, a refusal, or hallucinate what the
student must have meant.

Input validation catches all three before the agent call is made. The agent
never sees invalid input. The web layer handles the rejection cleanly and
returns a structured error.

---

## What Validation Is Not

Input validation is not prompt injection detection. You cannot reliably
detect prompt injection by inspecting message content at the HTTP layer.
The techniques that help with prompt injection work at the model layer:
strong system prompts, tool dispatch allowlists, and output validation.

Do not try to filter for phrases like "ignore previous instructions" or
"you are now a different agent". This kind of keyword filtering creates a
false sense of security and is trivially bypassed. Your validation
middleware should only check message structure, not message semantics.

---

## What You Are Building

A single validation middleware function applied to all three agent routes.
The same middleware works for all agents because what changes between agents
is their business logic, not the shape of the input they accept.

```
server/src/middleware/validator.js      validateAgentMessage function
server/src/routes/agent1.js            Wire validator before agent call
server/src/routes/agent2.js            Wire validator before agent call
server/src/routes/agent3.js            Wire validator before agent call
```

---

## The Validation Middleware

Create `server/src/middleware/validator.js`:

```js
const MAX_MESSAGE_LENGTH = parseInt(process.env.MAX_MESSAGE_LENGTH || '2000');

export function validateAgentMessage(req, res, next) {
  const { message } = req.body;

  if (typeof message !== 'string') {
    return res.status(400).json({
      error: 'Message must be a string.',
    });
  }

  const trimmed = message.trim();

  if (trimmed.length === 0) {
    return res.status(400).json({
      error: 'Message must not be empty.',
    });
  }

  if (trimmed.length > MAX_MESSAGE_LENGTH) {
    return res.status(400).json({
      error: `Message must be ${MAX_MESSAGE_LENGTH} characters or fewer.`,
    });
  }

  req.body.message = trimmed;
  next();
}
```

Four decisions encoded here:

First, the type check comes before the length check. Calling `.trim()` on
a non-string throws an error, so the type must be confirmed first.

Second, the validated and trimmed message is written back to `req.body.message`
before calling `next()`. The route handler and the agent both receive the
clean version without needing to know validation happened.

Third, `MAX_MESSAGE_LENGTH` comes from an environment variable with a
default of 2000. Two thousand characters is enough for any realistic
coaching message. If a student legitimately needs to send more (for
example, pasting a business case document for Tedd to evaluate), you can
raise the limit in the environment without touching code.

Fourth, each validation path returns a 400 with a plain English error
message. The message tells the student exactly what is wrong without
revealing anything about the implementation.

---

## Wiring Into Agent Routes

In each agent route file, import the validator and add it to the middleware
chain before the handler that calls the agent:

```js
import { validateAgentMessage } from '../middleware/validator.js';

router.post('/chat', authMiddleware, validateAgentMessage, async (req, res) => {
  const { message } = req.body;
  // message is now guaranteed to be a non-empty trimmed string
  // under MAX_MESSAGE_LENGTH characters
  ...
});
```

The chain is: auth check, then validation, then agent call. This order
matters. You want to reject unauthenticated requests before you do any
work, including validation. And you want to validate before you make an
expensive agent call.

If you wired rate limiting in Build 01, the full middleware chain for an
agent route is:

```
authMiddleware -> agentLimiter -> validateAgentMessage -> handler
```

Applied in index.js and within the route handler, this means every request
to an agent endpoint is authenticated, rate-limited, and validated before
the Python agent is invoked.

---

## Why Tedd Needs a Different Length Limit

The default 2000-character limit works well for Matteo and Juli, where
messages are conversational. But Tedd evaluates a complete deliverable.
A well-written Monroe's Motivated Sequence recommendation might easily be
3,000 to 5,000 characters.

One approach is a separate `validateTeddMessage` function with a higher
limit, reading from a `MAX_TEDD_MESSAGE_LENGTH` environment variable:

```js
const MAX_TEDD_MESSAGE_LENGTH = parseInt(
  process.env.MAX_TEDD_MESSAGE_LENGTH || '8000'
);

export function validateTeddMessage(req, res, next) {
  const { message } = req.body;

  if (typeof message !== 'string') {
    return res.status(400).json({ error: 'Message must be a string.' });
  }

  const trimmed = message.trim();

  if (trimmed.length === 0) {
    return res.status(400).json({ error: 'Message must not be empty.' });
  }

  if (trimmed.length > MAX_TEDD_MESSAGE_LENGTH) {
    return res.status(400).json({
      error: `Deliverable must be ${MAX_TEDD_MESSAGE_LENGTH} characters or fewer.`,
    });
  }

  req.body.message = trimmed;
  next();
}
```

Wire `validateTeddMessage` into agent3.js instead of `validateAgentMessage`.
This keeps the validation logic in one file with two named exports, each
with its own limit.

---

## Testing the Validator

Three test cases cover the happy path and both failure modes:

```bash
# Valid message - expect 200
curl -s -X POST http://localhost:3001/api/agent1/chat \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"message": "My situation is that our sales team has missed target for three quarters."}'

# Empty message - expect 400
curl -s -X POST http://localhost:3001/api/agent1/chat \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"message": ""}'

# Over-length message - expect 400
python3 -c "print('x' * 2001)" | \
  xargs -I{} curl -s -X POST http://localhost:3001/api/agent1/chat \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"{}\"}"
```

---

## Environment Variable

Add to `.env` and `.env.example`:

```
MAX_MESSAGE_LENGTH=2000
MAX_TEDD_MESSAGE_LENGTH=8000
```

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code already
knows from your CLAUDE.md that input validation middleware lives in
`server/src/middleware/` and must be applied before agent calls in route handlers.

**Prompt to add input validation:**

```
Add input validation middleware to the SCQ platform.

1. Create server/src/middleware/validator.js with two named exports:

   validateAgentMessage:
   - If typeof req.body.message !== 'string', return 400 with
     { error: 'Message must be a string.' }
   - Trim the message
   - If trimmed.length === 0, return 400 with
     { error: 'Message must not be empty.' }
   - If trimmed.length > parseInt(process.env.MAX_MESSAGE_LENGTH || '2000'),
     return 400 with { error: 'Message must be 2000 characters or fewer.' }
   - Set req.body.message = trimmed and call next()

   validateTeddMessage:
   - Same logic but uses MAX_TEDD_MESSAGE_LENGTH (default 8000)
   - Error says 'Deliverable must be...' instead of 'Message must be...'

2. In server/src/routes/agent1.js and agent2.js, import validateAgentMessage
   and add it to the POST /chat middleware chain after authMiddleware.

3. In server/src/routes/agent3.js, import validateTeddMessage and add it
   to the POST /chat middleware chain after authMiddleware.

The middleware chain order must be: authMiddleware, then validator, then handler.
Do not add the validator before authMiddleware.
```

**What Claude Code will do:**
Create `validator.js` with both exports, import the correct validator in each
route file, and add it to the middleware chain. It will read the existing route
files and insert the middleware without changing the handler logic.

**Tips for this document:**
- After Claude Code generates the file, ask: "Walk me through the order of
  checks in validateAgentMessage." Confirm: type check, then trim, then empty,
  then length. If trim comes after the empty check, it will not catch a message
  of only whitespace characters.
- If a valid message is being rejected, ask Claude Code: "What does
  req.body.message look like before the type check? Is express.json() applied
  in index.js?" The validator cannot read the body if the JSON body parser is
  missing.
- Tell Claude Code: "Do not add any keyword filtering or content checking.
  The validator only checks message structure: type, emptiness, and length."

---

**Next:** [03-prevent-idor.md](03-prevent-idor.md)

---

Copyright Janna AI Research Labs
