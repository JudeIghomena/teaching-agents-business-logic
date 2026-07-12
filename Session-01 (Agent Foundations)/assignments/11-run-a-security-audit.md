# Assignment 11: Run a Security Audit

**What you are building:** A repeatable pre-commit security check for your agent, plus a completed Security Non-Negotiables section in your CLAUDE.md
**Why it matters:** Security issues in agent code are expensive to fix in production and easy to prevent in development. This assignment gives you a repeatable process you will run before every commit on every project you build in this course.
**Time estimate:** 30 minutes
**Reads with:** 11-security-baseline.md

---

## What You Are Going To Do

You are going to run five targeted checks against your agent code, fix anything you find, and document the results in your CLAUDE.md so the next Claude Code session inherits your security posture.

---

## The Five Checks

Run these in order. Each one takes under two minutes. Do not skip any.

---

## Check 1: Secret Scan

No API key, token, password, or connection string may appear in any source file.

```bash
grep -rn "sk-ant" agent/ main.py .env.example
grep -rn "ANTHROPIC_API_KEY\s*=\s*['\"]" agent/ main.py
grep -rn "password\s*=\s*['\"]" agent/ main.py
```

Pass: zero hits in source files. The only place your API key appears is in `.env` (which is gitignored).
Fail: if any hit appears in a .py file, move the value to `.env` immediately and reload from `os.getenv()`.

---

## Check 2: .gitignore Verification

Confirm that `.env` and the data folder cannot be committed accidentally.

```bash
git check-ignore -v .env
git check-ignore -v data/
```

Pass: both lines return a path confirming they are ignored.
Fail: if either returns nothing, add the missing line to `.gitignore`:

```
.env
data/
__pycache__/
*.pyc
```

Then run: `git rm --cached .env` if `.env` was ever tracked.

---

## Check 3: Tool Dispatch Allowlist

Every tool function must go through `TOOL_DISPATCH`. If a tool name is not in that dict, the agent cannot call it even if it tries.

Open `agent/tool_registry.py` and verify:

```python
# Every name in TOOLS must appear in TOOL_DISPATCH
tools_in_schema = [t["name"] for t in TOOLS]
tools_in_dispatch = list(TOOL_DISPATCH.keys())

missing = set(tools_in_schema) - set(tools_in_dispatch)
extra = set(tools_in_dispatch) - set(tools_in_schema)
print("Missing from dispatch:", missing)
print("Extra in dispatch:", extra)
```

Run this in a Python shell from your project root. Pass: both sets are empty. Fail: add missing entries to TOOL_DISPATCH, remove orphaned entries.

---

## Check 4: Environment Variable Completeness

Your `.env.example` must list every variable your code reads via `os.getenv()`. A missing variable in `.env.example` means the next developer (or the next Claude session) will not know it is required.

```bash
grep -rn "os.getenv\|os.environ" agent/ main.py
```

Compare the output to your `.env.example`. Every variable name that appears in the grep output must have a line in `.env.example`.

Add any missing variables to `.env.example` with a placeholder value:

```
ANTHROPIC_API_KEY=your-api-key-here
YOUR_OTHER_VAR=describe-what-goes-here
```

---

## Check 5: Error Handler Check

No error that reaches the user should include a Python traceback or internal details. Users should see a short, clean message. Tracebacks go to logs only.

Search for bare `raise` or unguarded exceptions in your agent loop:

```bash
grep -n "traceback\|print.*Error\|raise Exception" agent/runner.py agent/tool_registry.py
```

Confirm your agent loop has a top-level try/except that catches unexpected errors and returns a clean message:

```python
try:
    return run_agent_loop(user_message, history)
except Exception as e:
    # Log the full error internally
    logger.error("agent_loop_error", extra={"error": str(e)})
    # Return a clean message to the caller
    return "Something went wrong. Please try again."
```

---

## Step 6: Update Your CLAUDE.md

Fill in the Security Non-Negotiables section with your actual findings:

```
## Security Non-Negotiables

Pre-commit checklist (run before every commit):
- [ ] grep -rn "sk-ant" agent/ main.py returns zero hits
- [ ] .env is in .gitignore and git check-ignore confirms it
- [ ] Every tool in TOOLS has a matching entry in TOOL_DISPATCH
- [ ] .env.example lists every os.getenv() variable used in the code
- [ ] Agent loop has a top-level try/except that returns clean errors

Audit results from [today's date]:
- Check 1 (secret scan): [PASS/FAIL - what was found and fixed]
- Check 2 (.gitignore): [PASS/FAIL - what was found and fixed]
- Check 3 (tool allowlist): [PASS/FAIL - what was found and fixed]
- Check 4 (.env.example completeness): [PASS/FAIL - what was found and fixed]
- Check 5 (error handlers): [PASS/FAIL - what was found and fixed]
```

---

## You Are Done When

- [ ] All five checks have been run
- [ ] Zero secrets appear in any .py file
- [ ] `.env` and `data/` are confirmed gitignored
- [ ] TOOL_DISPATCH matches TOOLS exactly
- [ ] `.env.example` lists every environment variable the code uses
- [ ] The agent loop returns clean error messages, not tracebacks
- [ ] Your CLAUDE.md Security Non-Negotiables section has audit results with today's date

---

## If You Get Stuck

`git check-ignore` returns nothing for `.env`: your `.gitignore` may not have a `.env` line, or it may have a comment blocking the match. Open `.gitignore` and add `.env` on its own line, no trailing spaces.

Tool dispatch has orphaned entries: a function was added to TOOL_DISPATCH without a matching schema entry in TOOLS, or vice versa. The Python shell check above will list exactly which names are mismatched.

Agent loop returns a traceback to the user: find the innermost exception handler and confirm it does not call `print(traceback.format_exc())` at a level that returns to the caller. Tracebacks should go to the logger, not to `return`.

---

## You Have Completed Session-01

You have built, wired, documented, observed, and audited a working AI agent from scratch. The five-layer architecture, the tool dispatcher, the system prompt, the three-tier memory, and the security baseline are the same patterns you will carry into every project in this course.

Next: [Session-02, Assignment 01 - Build Your Agent Route](../../Session-02%20(Task%20Design%20and%20Web%20Layer)/assignments/01-build-your-agent-route.md)

---

Copyright Janna AI Research Labs
