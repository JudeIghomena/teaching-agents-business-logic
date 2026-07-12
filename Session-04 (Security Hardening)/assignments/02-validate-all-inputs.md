# Assignment 02: Validate All Inputs

**Reads with:** [02-validate-all-inputs.md](../02-validate-all-inputs.md)
**Time estimate:** 30-45 minutes
**Frameworks applied:** 11 (Security Baseline) + 06 (Tool Design)

---

## What You Are Building

Two validation middleware functions: `validateAgentMessage` for Matteo and
Juli, and `validateTeddMessage` for Tedd. Both exported from a single file.

---

## Steps

### Step 1: Create the validator file

Create `server/src/middleware/validator.js`.

Implement `validateAgentMessage`:
- Type check: if `typeof message !== 'string'`, return 400
- Trim the message
- Empty check: if trimmed length is 0, return 400
- Length check: if trimmed length exceeds `MAX_MESSAGE_LENGTH`, return 400
- If all checks pass: set `req.body.message = trimmed` and call `next()`

Implement `validateTeddMessage`:
- Same as above but uses `MAX_TEDD_MESSAGE_LENGTH` (default 8000)
- Different error message: "Deliverable must be..." instead of "Message must be..."

Both read their limits from environment variables with safe fallback defaults.

### Step 2: Add environment variables

In `.env`:

```
MAX_MESSAGE_LENGTH=2000
MAX_TEDD_MESSAGE_LENGTH=8000
```

### Step 3: Wire into agent routes

In `server/src/routes/agent1.js` and `agent2.js`:

```js
import { validateAgentMessage } from '../middleware/validator.js';

router.post('/chat', authMiddleware, validateAgentMessage, async (req, res) => {
  ...
});
```

In `server/src/routes/agent3.js`:

```js
import { validateTeddMessage } from '../middleware/validator.js';

router.post('/chat', authMiddleware, validateTeddMessage, async (req, res) => {
  ...
});
```

### Step 4: Test each validation case

Get a valid JWT first:

```bash
TOKEN=$(curl -s -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.edu","password":"TestPass123!"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
```

Test empty message (expect 400):

```bash
curl -s -X POST http://localhost:3001/api/agent1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "   "}'
```

Test over-length (expect 400):

```bash
python3 -c "print('x' * 2001)" | \
  xargs -I MSG curl -s -X POST http://localhost:3001/api/agent1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "MSG"}'
```

Test non-string (expect 400):

```bash
curl -s -X POST http://localhost:3001/api/agent1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": 12345}'
```

Test valid message (expect 200 or streaming response):

```bash
curl -s -X POST http://localhost:3001/api/agent1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "My situation is that sales have dropped 20% in Q3."}'
```

---

## Done Checklist

- [ ] `server/src/middleware/validator.js` exists with two named exports
- [ ] `validateAgentMessage` checks type, empty after trim, max length
- [ ] `validateTeddMessage` checks type, empty after trim, max Tedd length
- [ ] Both write `req.body.message = trimmed` before calling `next()`
- [ ] Both read limits from environment variables with numeric defaults
- [ ] `validateAgentMessage` wired into agent1 and agent2 routes
- [ ] `validateTeddMessage` wired into agent3 route
- [ ] All four test cases produce the expected HTTP status codes
- [ ] Environment variables added to `.env` and `.env.example`

---

## Troubleshooting

Validator not triggering: check the import path. If your routes are in
`server/src/routes/` and the validator is in `server/src/middleware/`,
the import is `'../middleware/validator.js'`.

Type check not catching numbers: `typeof 12345` is `'number'`, not
`'string'`. The check `typeof message !== 'string'` correctly rejects
this. If it is not working, confirm the raw body is being parsed as JSON
by Express (`express.json()` must be in index.js).

Empty string after trim not caught: confirm the trim is applied before the
empty check, not after. The order must be: trim, then check length.

---

**Next assignment:** [03-prevent-idor.md](03-prevent-idor.md)
