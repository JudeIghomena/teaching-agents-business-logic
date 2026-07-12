# Assignment 02: Create Your Project Structure

**What you are building:** The folder layout for your agent project with the correct file placement rules
**Why it matters:** A consistent structure means any developer, and your coding agent, can find any file without searching. It also prevents common mistakes like putting secrets in source files or business logic in the wrong layer.
**Time estimate:** 15 minutes
**Reads with:** 02-project-structure.md

---

## What You Are Going To Do

You are going to confirm your project folder matches the five-layer layout, add a placement rule comment to your CLAUDE.md, and verify that the files the starter code expects are all present.

---

## Step 1: Check Your Folder Layout

From inside your project folder, run:

```bash
find . -not -path './.git/*' -not -name '__pycache__' | sort
```

You should see:

```
./CLAUDE.md
./.env
./.env.example
./.gitignore
./main.py
./requirements.txt
./agent/
./agent/__init__.py
./agent/context.py
./agent/infrastructure.py
./agent/model_config.py
./agent/runner.py
./agent/tool_registry.py
```

If any file is missing, copy it from Session-01 starter-code:

```bash
cp "Session-01 (Frameworks)/starter-code/agent/<filename>.py" ./agent/
```

---

## Step 2: Confirm .env Is Gitignored

Check your .gitignore file:

```bash
cat .gitignore
```

You must see `.env` listed. If it is not there, add it:

```bash
echo ".env" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
```

Never commit .env. If you commit it by mistake, rotate your API key immediately.

---

## Step 3: Add Placement Rules to Your CLAUDE.md

Open your CLAUDE.md and find the "Project Structure" section. Below the folder tree, add or confirm these placement rules are present:

```
Placement rules:
- All business logic goes in agent/
- New tools are added to tool_registry.py only
- Secrets go in .env only, never in source files
- The entry point is main.py, do not create other entry points
- No file outside agent/ should import from another file outside agent/
```

Customise the rules for your project. If you have additional folders (for example a data/ folder for documents), add a rule describing what goes there.

---

## Step 4: Update the Project Structure Map in CLAUDE.md

Replace the placeholder structure in CLAUDE.md with your actual folder tree. Run this to get a clean output to paste:

```bash
find . -not -path './.git/*' -not -name '*.pyc' -not -name '__pycache__' | sort
```

Paste the result into the Project Structure section of your CLAUDE.md, formatted as a code block.

---

## You Are Done When

- [ ] `find . | sort` shows all five agent/ files plus main.py and .env.example
- [ ] `.env` is listed in `.gitignore`
- [ ] Your CLAUDE.md Project Structure section shows your actual folder tree
- [ ] Your CLAUDE.md has placement rules that cover where business logic, secrets, and tools go
- [ ] Running `git status` does not show .env as an untracked or modified file

---

## If You Get Stuck

`.env` appears in `git status`: add it to .gitignore immediately with `echo ".env" >> .gitignore` then run `git rm --cached .env` to untrack it without deleting the file.

Missing `__init__.py` in agent/: create it with `touch agent/__init__.py`. Python needs it to treat the folder as a package.

---

## Next Assignment

[03-choose-your-model.md](03-choose-your-model.md)

---

Copyright Janna AI Research Labs
