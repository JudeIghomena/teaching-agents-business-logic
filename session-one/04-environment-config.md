# Framework 05: Environment Configuration

> Your agent is only as secure and reliable as its configuration layer.
> Environment setup is not a one-time task, it is a discipline.

---

## Why Configuration Is Its Own Framework Step

Configuration mistakes are the most expensive class of agent bugs:

- A wrong model ID fails silently and produces unexpected output
- A missing API key crashes the agent at runtime, not at startup
- A leaked secret in a committed `.env` file exposes your entire API account
- A `max_tokens` that is too low truncates agent responses mid-sentence
- A missing rate limit setting causes downstream systems to be overwhelmed

None of these are prompt problems. None are logic problems. They are all
configuration problems that could have been caught before the first API call.

---

## The Three Configuration Environments

Every production agent runs in at least two environments. Most run in three.

```
┌─────────────────────────────────────────────────────────────────┐
│  DEVELOPMENT          STAGING              PRODUCTION           │
│                                                                  │
│  Your local machine   A shared test env    Live traffic         │
│  Real API key         Real API key         Real API key         │
│  Cheap model (Haiku)  Target model         Target model         │
│  Low token limits     Production limits    Production limits    │
│  Verbose logging      Normal logging       Structured logging   │
│  No rate limits       Rate limits on       Rate limits on       │
└─────────────────────────────────────────────────────────────────┘
```

The model you use in development should be Haiku if your production model is
Sonnet or Opus. Development is for logic testing, not capability testing.
Cheaper model = faster iteration = lower bill during development.

---

## Required Environment Variables

Every agent project needs at minimum:

```bash
# ── Core (required: agent will not start without these) ──────────────

ANTHROPIC_API_KEY=sk-ant-...
# The Anthropic API key. Loaded once at client init.
# Never hardcode. Never log. Never commit.

AGENT_MODEL=claude-sonnet-5
# Full pinned model ID. See 03-model-selection.md for valid values.

AGENT_MAX_TOKENS=4096
# Maximum tokens in the model response. Always set this explicitly.
# Leaving it unset defaults to the model maximum: expensive and slow.

AGENT_TEMPERATURE=0.0
# 0.0 for deterministic business logic. Higher for creative tasks.
# See 03-model-selection.md temperature guide.

AGENT_MAX_ITERATIONS=10
# Maximum tool-call iterations per turn. Prevents infinite loops.
# For simple agents: 5. For complex multi-step workflows: 10-15.

# ── Optional (set based on your deployment) ───────────────────────────

LOG_LEVEL=INFO
# DEBUG for development. INFO for staging. WARNING for production.

APP_ENV=development
# development | staging | production
# Your code can branch on this to enable/disable features.

RATE_LIMIT_REQUESTS_PER_MINUTE=60
# Passed to your rate limiter. Match to your Anthropic tier limits.
```

---

## The .env File Pattern

### What .env contains (never committed)

```bash
# .env : local secrets and config: DO NOT COMMIT
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
AGENT_MODEL=claude-haiku-4-5-20251001    # cheap model for local dev
AGENT_MAX_TOKENS=2048
AGENT_TEMPERATURE=0.0
AGENT_MAX_ITERATIONS=5
LOG_LEVEL=DEBUG
APP_ENV=development
```

### What .env.example contains (committed: no values)

```bash
# .env.example : copy this to .env and fill in your values
ANTHROPIC_API_KEY=
AGENT_MODEL=
AGENT_MAX_TOKENS=
AGENT_TEMPERATURE=
AGENT_MAX_ITERATIONS=
LOG_LEVEL=
APP_ENV=
```

### What .gitignore must contain

```
.env
.env.*
!.env.example
```

The `!.env.example` exception allows the template to be committed while
blocking all actual secret files.

---

## Loading Configuration Safely

```python
# agent/infrastructure.py

import os
from dotenv import load_dotenv

load_dotenv()  # Loads .env file into os.environ at startup

def require_env(key: str) -> str:
    """
    Reads a required environment variable.
    Raises immediately at startup if missing, not silently at runtime.

    This is called "fail fast." Better to crash on startup with a clear
    error than to fail 30 seconds into an agent run with a cryptic message.
    """
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Copy .env.example to .env and fill in the value."
        )
    return value


def optional_env(key: str, default: str) -> str:
    """Reads an optional environment variable with a safe default."""
    return os.environ.get(key, default)
```

---

## Pre-Run Configuration Checklist

Run through this before starting the agent for the first time in any environment.

```
CONFIGURATION CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] .env file exists in project root
[ ] ANTHROPIC_API_KEY is set and starts with sk-ant-
[ ] AGENT_MODEL is set to a valid pinned model ID
[ ] AGENT_MAX_TOKENS is set (not blank or 0)
[ ] AGENT_TEMPERATURE is set (0.0 for business logic)
[ ] AGENT_MAX_ITERATIONS is set (5-15 depending on complexity)
[ ] .env is listed in .gitignore
[ ] .env.example is committed with blank values
[ ] No secrets appear in any Python source file
[ ] No secrets appear in requirements.txt, Dockerfile, or CI config
[ ] APP_ENV is set to the correct environment (development/staging/production)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run: grep -r "sk-ant-" . --include="*.py" --include="*.yaml" --include="*.json"
Expected output: no results.
If you see results: remove the key immediately, rotate it at console.anthropic.com.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Deployment-Specific Config

When deploying to a hosting platform, environment variables are set through
the platform's UI or CLI, not through `.env` files, which stay on your machine.

```bash
# Railway
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set AGENT_MODEL=claude-sonnet-5

# AWS / ECS: use Parameter Store or Secrets Manager, not hardcoded task definitions

# Docker
docker run -e ANTHROPIC_API_KEY=sk-ant-... your-agent-image

# Kubernetes: use a Secret manifest, not a ConfigMap
```

The pattern is always the same: secrets come from the environment, never from
source code. The source code reads from the environment.

---

## Sample: Complete .env.example to Customise

```bash
# ── Required ──────────────────────────────────────────────────────────
ANTHROPIC_API_KEY=

# Model selection (see session-one/03-model-selection.md)
# Options: claude-haiku-4-5-20251001 | claude-sonnet-5 | claude-opus-4-8 | claude-fable-5
AGENT_MODEL=

# Token and iteration limits
AGENT_MAX_TOKENS=4096
AGENT_TEMPERATURE=0.0
AGENT_MAX_ITERATIONS=10

# ── Optional ──────────────────────────────────────────────────────────
# Log level: DEBUG | INFO | WARNING | ERROR
LOG_LEVEL=INFO

# Environment: development | staging | production
APP_ENV=development

# Rate limiting (requests per minute, per Anthropic tier)
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# ── Project-specific (add yours below) ────────────────────────────────
# DATABASE_URL=
# REDIS_URL=
# WEBHOOK_SECRET=
```

---

## Apply to Your Coding Agent

**Task:** Copy the .env.example template from this session's starter-code into
your project and add a secrets handling rule to your CLAUDE.md that prevents
your coding agent from ever touching, logging, or hardcoding a secret value.

**Why this matters:** Secrets leaks in AI-assisted development rarely happen
because a developer commits a secret intentionally. They happen because a coding
agent suggests "for simplicity, just hardcode the key here for now." A written
rule in CLAUDE.md stops this at the suggestion stage, before any code is written.

**Step 1: Create your .env.example**

Copy the file at `session-one/starter-code/.env.example` into your project root.
Then add any project-specific variables below the base set:

```bash
# .env.example: copy this to .env and fill in values. Never commit .env.

# Core (required: agent will not start without these)
ANTHROPIC_API_KEY=
AGENT_MODEL=
AGENT_MAX_TOKENS=4096
AGENT_TEMPERATURE=0.0
AGENT_MAX_ITERATIONS=10

# Optional
LOG_LEVEL=INFO
APP_ENV=development
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Project-specific (add yours below)
# DATABASE_URL=
# REDIS_URL=
# WEBHOOK_SECRET=
```

**Step 2: Add this secrets rule to your CLAUDE.md**

```
## Secrets and Configuration Rules

### The rule
All secrets and configuration values live in .env only.
No secret ever appears in any Python file, any config file, or any log output.

### What counts as a secret
- ANTHROPIC_API_KEY and any other API keys
- Database connection strings (they contain passwords)
- JWT signing secrets or HMAC keys
- Webhook secrets
- Any value starting with sk-, pk-, tok-, or Bearer

### What you (coding agent) must never do
- Suggest hardcoding any secret in source code, even temporarily or for testing
- Add print() or logging calls that output a variable holding a secret
- Read .env directly: use os.environ.get() or the require_env() helper
- Suggest committing .env (the file must stay local always)

### What to do when a new secret is needed
1. Add the variable name with no value to .env.example
2. Add a require_env("VAR_NAME") call in agent/infrastructure.py
3. Tell me what value to set in my .env
4. Never ask me to put the value in the source code

### Verification: run this before every commit
grep -rE "(sk-ant-|password\s*=\s*['\"]|api_key\s*=\s*['\"])" . --include="*.py"
Expected output: zero matches.
If you see any: stop, fix before committing.
```

**Step 3: Paste into CLAUDE.md**

Open your project CLAUDE.md. Add this block under `## Secrets and Configuration
Rules`. It should come after the project structure section and before context
budget rules.

**Step 4: Apply to your coding tool**

For Claude Code: this rule is now in CLAUDE.md. Claude Code will follow it
without being reminded. If it ever suggests hardcoding a value, ask it to
"check the secrets rule in CLAUDE.md."

For Cursor: paste into `.cursorrules`. Cursor will apply it when generating
code that reads configuration values.

For Codex: add to the workspace system prompt.

**What you now have:** A coding agent that treats secrets correctly from the
first session. The .env.example documents every variable that exists. The
CLAUDE.md rule prevents the most common class of AI-assisted secret leak
before it can happen.

---

Copyright Janna AI Research Labs
