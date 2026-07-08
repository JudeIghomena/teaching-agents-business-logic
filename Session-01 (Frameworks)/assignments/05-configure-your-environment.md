# Assignment 05: Configure Your Environment

**What you are building:** A complete, secure environment configuration for your agent with all required variables documented and no secrets in source code
**Why it matters:** A misconfigured environment is the most common reason an agent fails on first run. Getting this right once means every future developer, and every future deployment, starts from a known-good state.
**Time estimate:** 20 minutes
**Reads with:** 05-environment-config.md

---

## What You Are Going To Do

You are going to identify every secret and configuration value your agent needs, document them in .env.example, set real values in .env, and add a secrets rule to your CLAUDE.md.

---

## Step 1: List Every Value Your Agent Needs

Go through your agent code and list every value that must come from outside the code. These fall into two categories:

Secrets (never commit these):
- API keys (ANTHROPIC_API_KEY, any third-party API keys)
- Database connection strings
- JWT secrets
- Webhook tokens

Configuration (safe to document but not commit real values):
- Model name (you set this in Assignment 03, but some teams prefer it in .env)
- Port numbers
- Feature flags
- External service URLs

---

## Step 2: Update .env.example

Open `.env.example` in the starter code. Replace the placeholders with the variables your agent actually needs:

```bash
# .env.example
# Copy this file to .env and fill in your values.
# Never commit .env to git.

# Required
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Add your project-specific variables below
# DATABASE_URL=postgresql://user:password@host:5432/dbname
# JWT_SECRET=your-256-bit-secret
# EXTERNAL_API_KEY=your-key-here
```

Every variable your agent reads must have an entry in .env.example with a
description comment and a placeholder value. This is the documentation for
anyone setting up the project for the first time.

---

## Step 3: Set Your Real Values in .env

Copy .env.example to .env and fill in your real values:

```bash
cp .env.example .env
```

Open .env and replace every placeholder with a real value. Do not leave
placeholders in .env. If a variable is optional, comment it out.

Verify the API key works:

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('ANTHROPIC_API_KEY', '')
print('Key loaded:', bool(key))
print('Key prefix:', key[:8] if key else 'MISSING')
"
```

You should see `Key loaded: True` and a prefix starting with `sk-ant`.

---

## Step 4: Verify .env Is Not Being Committed

```bash
git status
```

.env must not appear in the output. If it does:

```bash
echo ".env" >> .gitignore
git rm --cached .env
git status  # .env should no longer appear
```

---

## Step 5: Add Secrets Rules to CLAUDE.md

Open your CLAUDE.md and fill in the Secrets section:

```
## Secrets and Configuration

API keys and secrets are stored in .env only.
Never hardcode a secret in any source file.
Never log a secret, even partially.
Never include a secret in an error message returned to the user.

If a secret is accidentally committed: rotate it immediately before doing
anything else.

Required environment variables for this project:
- ANTHROPIC_API_KEY: Anthropic API key for all model calls
- [YOUR_VARIABLE]: [what it is and what it is used for]
```

List every variable from your .env.example. For each one, write one sentence
describing what it is and which part of the system uses it.

---

## Step 6: Verify the Full Agent Run

Run your agent end to end to confirm all environment variables load correctly:

```bash
python main.py
```

Send a test message. If the agent responds, your environment is configured.

---

## You Are Done When

- [ ] `.env.example` lists every variable your agent needs with placeholder values and comments
- [ ] `.env` has all real values filled in
- [ ] `git status` does not show `.env`
- [ ] `python main.py` runs without any missing environment variable errors
- [ ] Your CLAUDE.md Secrets section lists every environment variable with a one-sentence description

---

## If You Get Stuck

`python-dotenv` not installed: run `pip install python-dotenv` or check requirements.txt.

Variable loads as None despite being in .env: confirm `load_dotenv()` is called before `os.getenv()`. Check that there are no spaces around the `=` sign in .env.

.env keeps appearing in git status after adding to .gitignore: run `git rm --cached .env` to stop git tracking the file. The file stays on disk.

---

## Next Assignment

[06-design-your-first-tool.md](06-design-your-first-tool.md)

---

Copyright Janna AI Research Labs
