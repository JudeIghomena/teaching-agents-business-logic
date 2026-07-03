# Getting Started: Set Up With the Claude Code Desktop App

This guide is for students who want to use the Claude Code desktop application
instead of the command-line interface. The desktop app gives you the same
Claude Code capabilities inside a graphical window, with a built-in file panel,
conversation view, and integrated terminal. No separate terminal window required.

If you prefer working in a terminal, use the CLI guide instead:
[00a-getting-started-cli.md](00a-getting-started-cli.md)

---

## What You Need Before You Start

- macOS 12 or later, or Windows 10 or later
- Python 3.10 or later installed on your machine (`python3 --version` to check)
- An Anthropic account (create one at console.anthropic.com)

---

## Step 1: Download the Claude Code Desktop App

Go to claude.ai and sign in to your Anthropic account. From the navigation,
look for the Claude Code section and download the desktop app for your
operating system.

On macOS you will download a `.dmg` file.
On Windows you will download a `.exe` installer.

---

## Step 2: Install the App

**macOS**

1. Open the downloaded `.dmg` file
2. Drag the Claude Code icon into your Applications folder
3. Open Applications and double-click Claude Code
4. If macOS asks whether you trust the app, click Open

**Windows**

1. Run the downloaded `.exe` installer
2. Follow the installation wizard, accepting the default install location
3. Once installed, open Claude Code from the Start menu or desktop shortcut

---

## Step 3: Sign In

When Claude Code opens for the first time, it will ask you to sign in.

1. Click "Sign in with Anthropic"
2. A browser window opens. Log in with your Anthropic account credentials
3. Once logged in, the browser shows a confirmation. Return to the desktop app
4. The app connects and you land on the home screen

If you already have an Anthropic API key and prefer to use it directly,
look for the "Use API key" option on the sign-in screen and paste your key there.

---

## Step 4: Open the Course Starter Code as a Project

The desktop app works with folders. You will open the `starter-code` folder
from this session as your project.

1. In the Claude Code home screen, click "Open Project" or "Open Folder"
2. Navigate to where you copied the `starter-code` folder
   (see Step 5 in [starter-code/README.md](starter-code/README.md) for how to copy it)
3. Select the folder and click Open
4. Claude Code loads the project. You will see the files listed in the sidebar

Claude Code reads `CLAUDE.md` automatically when it opens the project.
You do not need to paste or import it. Place `CLAUDE.md` in the root of
the folder you open and it is active immediately.

---

## Step 5: Set Up Your Environment Variables

The desktop app has a built-in terminal panel where you can run shell commands.

1. In Claude Code, open the terminal panel (look for a terminal icon or
   press the keyboard shortcut shown in the View menu)
2. In the terminal, copy the environment file template:

```bash
cp .env.example .env
```

3. Open `.env` in the editor panel and fill in your Anthropic API key:

```
ANTHROPIC_API_KEY=your-key-here
```

Save the file. Never commit `.env` to git. It is already listed in `.gitignore`
in the starter code.

---

## Step 6: Install Python Dependencies

In the built-in terminal panel, run:

```bash
pip install -r requirements.txt
```

If `pip` is not found, try:

```bash
pip3 install -r requirements.txt
```

You should see the `anthropic` and `python-dotenv` packages install.

---

## Step 7: Run the Starter Agent

In the terminal panel, run:

```bash
python main.py
```

Or on some systems:

```bash
python3 main.py
```

The agent starts and waits for your input. Type a message to test it.
You should get a response from Claude. If you do, everything is working.

---

## Step 8: Copy and Fill In Your CLAUDE.md

The project already has a CLAUDE.md template in the `starter-code` folder.
If you opened `starter-code` as your project root, Claude Code is already
reading it.

Open `CLAUDE.md` in the editor panel. You will see sections with
placeholder values in `[BRACKETS]`. Fill them in as you read each
Framework document. Framework 01 gives you the first section.
Framework 11 gives you the last. By the time you finish all eleven docs,
your CLAUDE.md is complete.

To see that Claude Code is reading your CLAUDE.md, start a new conversation
inside the app and ask: "What is this project and what rules are you following?"
It should answer based on what you have filled in so far.

---

## Step 9: How the Desktop App Reads CLAUDE.md

Claude Code reads `CLAUDE.md` files in two places:

1. A global file at `~/.claude/CLAUDE.md` (your home directory), if it exists.
   Rules here apply to every project you open.
2. A project file at the root of the folder you opened.
   Rules here apply to this project only.

The project file takes priority where the two overlap. You will build the
project-level file throughout Session One. If you ever want rules that apply
everywhere (for example, a writing style rule or a secret-management rule),
add them to the global file.

---

## Importing the Starter Files Into Other Coding Agents

If you are using Cursor or OpenAI Codex alongside or instead of the Claude
Code desktop app, follow the steps below to load the starter code and your
CLAUDE.md into those agents.

---

### Cursor

Cursor reads a file called `.cursorrules` from the root of your workspace.
The content is your CLAUDE.md.

1. Open Cursor and go to File, Open Folder, then select your project folder
2. Open the built-in terminal in Cursor (View, Terminal)
3. Create the `.cursorrules` file from the CLAUDE.md template:

```bash
cp CLAUDE.md .cursorrules
```

4. Cursor picks up `.cursorrules` immediately. No restart needed.

To confirm it is working, open a Cursor chat and ask: "What rules are you
following for this project?" It should describe the contents of your file.

As you fill in more sections of your CLAUDE.md throughout the Framework docs,
copy the updated content into `.cursorrules` to keep Cursor in sync:

```bash
cp CLAUDE.md .cursorrules
```

---

### OpenAI Codex

Codex reads its instructions from a system prompt you paste into workspace
settings, not from a file on disk.

1. Open your Codex workspace or create a new one for this course
2. Go to workspace Settings and find the "System Prompt" or "Instructions" field
3. Open `CLAUDE.md` in any text editor, select all, and copy the contents
4. Paste into the System Prompt field and save

Upload the Python starter files so Codex can read and edit them:
1. In the Codex file panel, click Upload or use the import option
2. Upload each file from the `agent/` folder:
   `infrastructure.py`, `model_config.py`, `tool_registry.py`, `context.py`, `runner.py`
3. Upload `main.py` and `requirements.txt`

Each time you fill in more of your CLAUDE.md as you read the Framework docs,
return to workspace Settings and paste the updated content into the system
prompt again to keep Codex in sync.

---

## How This Differs From the CLI

| Capability | CLI | Desktop App |
|---|---|---|
| Open a project | `cd` into the folder and run `claude` | Click "Open Project" in the app |
| Run terminal commands | Your system terminal | Built-in terminal panel in the app |
| View project files | Your file browser or IDE | Built-in file sidebar |
| CLAUDE.md loading | Automatic on `claude` launch | Automatic on project open |
| Authentication | Browser flow or API key in `.env` | Browser flow on first launch |

Both paths lead to the same result. Choose the one that matches how you prefer
to work. You can switch between them at any time.

---

## Troubleshooting

**The app opens but cannot connect to Claude**
Check that you are signed in (look for your account name in the top right).
If signed out, click Sign In and complete the browser flow again.

**Python command not found in the built-in terminal**
The built-in terminal uses your system PATH. If Python is installed but not
found, run `which python3` in your system terminal to find the path, then
set it explicitly: `/full/path/to/python3 main.py`.

**CLAUDE.md does not seem to be taking effect**
Make sure the file is at the root of the folder you opened, not inside a
subfolder. Close the project and re-open it to force a fresh read.

**The app asks for permissions to read files**
This is normal on macOS. Click "Allow" when prompted. Claude Code needs
read and write access to the project folder to function.

---

## You Are Ready

Once `python main.py` runs and you get a response, you are fully set up.

Start here: [01-agent-mental-model.md](01-agent-mental-model.md)

Fill in your CLAUDE.md one section at a time as you read each Framework doc.

---

Copyright Janna AI Research Labs
