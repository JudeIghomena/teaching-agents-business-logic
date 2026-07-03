# Getting Started: Install Claude Code CLI

This guide is for students who prefer working in a terminal. It covers
installing the Claude Code command-line interface, connecting your API key,
and running the starter code from a terminal window.

If you prefer a graphical application with a built-in file panel and
integrated terminal, use the desktop app guide instead:
[00b-getting-started-desktop-app.md](00b-getting-started-desktop-app.md)

---

## What You Need

Before you start, make sure you have:

- Python 3.10 or later (`python3 --version` to check)
- Node.js 18 or later (`node --version` to check)
- An Anthropic account with API access (create one at console.anthropic.com)

---

## Step 1: Install the Claude Code CLI

Claude Code is Anthropic's official command-line tool. It runs Claude
directly in your terminal, reads your project files, and executes code
on your behalf. It is the environment you will use throughout this course
to build, test, and iterate on your agent.

Install it with npm:

```bash
npm install -g @anthropic-ai/claude-code
```

Verify the installation:

```bash
claude --version
```

You should see a version number printed. If you see "command not found",
check that Node.js is installed and that your npm global bin directory
is in your PATH.

On macOS with Homebrew, if the command is not found, run:

```bash
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
```

Then try `claude --version` again. Add that export line to your
`~/.zshrc` or `~/.bashrc` to make it permanent.

---

## Step 2: Get Your Anthropic API Key

1. Go to console.anthropic.com and sign in
2. Click "API Keys" in the left sidebar
3. Click "Create Key" and give it a name (for example: "agent-course")
4. Copy the key immediately. You will not be able to see it again.

Store it somewhere safe. You will add it to a `.env` file in Framework 05.
Never paste it into source code or commit it to git.

---

## Step 3: Verify Claude Code Works

Run a quick test to confirm Claude Code is connected to your API key:

```bash
claude --print "Say hello in one word"
```

If it prints a single word, you are set up correctly.

If it asks you to log in, follow the browser authentication flow it opens.
Your API key will be stored securely in Claude Code's local credential store.

---

## Step 4: Understand What CLAUDE.md Is

CLAUDE.md is a plain text file you place at the root of your project.
Claude Code reads it automatically at the start of every session, before
you type anything. It is how you tell your coding agent:

- what this project is and what role it plays
- which files it is and is not allowed to touch
- which commands it can run and which are forbidden
- what output format you expect
- what security rules it must always follow

You will build this file step by step across the eleven Framework documents
in Session One. By the time you finish Framework 11, you will have a
complete, structured CLAUDE.md that any coding agent can use as a brief.

A starter template is provided in `starter-code/CLAUDE.md`. Copy it into
your project root and fill in the placeholder values as you work through
each Framework doc.

---

## Step 5: Copy the Starter Code

The `starter-code/` folder inside this session contains working Python
you can copy directly into your own project. It is not a blank scaffold.
It is a functioning five-layer agent you customise for your use case.

Copy the whole folder to your project location:

```bash
cp -r "starter-code/" ~/my-agent-project/
cd ~/my-agent-project
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Copy the environment variable template:

```bash
cp .env.example .env
```

Leave `.env` empty for now. Framework 04 covers model selection and
Framework 05 covers environment configuration in detail.

---

## How Claude Code Uses CLAUDE.md

When you run `claude` inside a project folder, it:

1. Looks for `CLAUDE.md` in the current directory and all parent directories
2. Reads every CLAUDE.md it finds, from outermost to innermost
3. Uses the combined content as its operating brief for the session

This means you can have a global CLAUDE.md in your home directory with
rules that apply to every project, and a project-level CLAUDE.md with
rules specific to this agent. The project-level file takes priority where
the two conflict.

---

## How to Import Into Your Coding Agent

Once you have filled in your CLAUDE.md:

**Claude Code (recommended for this course)**
Place `CLAUDE.md` in your project root. Claude Code reads it automatically.
No import step needed.

**Cursor**
Create a file called `.cursorrules` in your project root and paste the
same content. Cursor reads this file at the start of every session.

**OpenAI Codex**
Paste the content into the "System Prompt" field in the workspace settings.
Codex does not read files from disk, so the content must be pasted directly.

---

## You Are Ready

Once `claude --version` and `claude --print "Say hello in one word"` both
work, you are ready to start Framework 01.

Start here: [01-agent-mental-model.md](01-agent-mental-model.md)

---

Copyright Janna AI Research Labs
