# Assignment 09: Add Memory to Your Agent

**What you are building:** A working three-tier memory system: in-context history, a session store for temporary state, and a persistent store for decisions that must survive restarts
**Why it matters:** An agent without memory treats every message as the first. For a coaching agent that must remember what a student discussed two sessions ago, or a procurement agent that must not approve the same request twice, memory is not optional.
**Time estimate:** 35 minutes
**Reads with:** 09-memory-and-state.md

---

## What You Are Going To Do

You are going to implement each tier of the three-tier memory model, decide what your agent stores in each tier, and verify that state persists correctly across turns and across restarts.

---

## The Three Tiers

```
Tier 1: In-Context (conversation history)
  Lives in the message list passed to the API
  Survives: within one session
  Lost when: session ends or history is trimmed

Tier 2: Session Store (temporary state)
  Lives in a Python dict or lightweight cache
  Survives: across turns within the same process run
  Lost when: the process restarts

Tier 3: Persistent Store (database or file)
  Lives in a database or JSON file on disk
  Survives: process restarts, deployments, server crashes
  Lost when: explicitly deleted
```

---

## Step 1: Tier 1 Is Already Working

If you completed Assignment 08, Tier 1 is already in place. Your agent passes
history into each API call and the responses are accumulated in memory.

Verify it by running a two-turn conversation and checking that the agent
references Turn 1 in its Turn 2 response. If it does, Tier 1 is working.

---

## Step 2: Implement Tier 2 (Session Store)

A session store holds state that is too expensive to re-derive every turn but
does not need to survive a process restart. Common uses: caching a lookup
result, tracking a score that updates each turn, storing a flag.

Add a session store to your agent:

```python
# agent/session_store.py

class SessionStore:
    """
    In-memory store for state that must persist across turns
    within a single session but does not need to survive restarts.
    """

    def __init__(self):
        self._store = {}

    def set(self, key: str, value) -> None:
        self._store[key] = value

    def get(self, key: str, default=None):
        return self._store.get(key, default)

    def clear(self) -> None:
        self._store.clear()


# Singleton: one store per agent process
session = SessionStore()
```

Decide what your agent stores in Tier 2 and add it to your CLAUDE.md:

```
Tier 2 (session store): [what gets stored here and why]
Example: vendor lookup results cached for the session duration
         A vendor approved in turn 1 does not need a second API call in turn 3
```

---

## Step 3: Implement Tier 3 (Persistent Store)

A persistent store holds state that must survive a restart. For the starter
agent, use a simple JSON file. Session-02 replaces this with a database.

```python
# agent/persistent_store.py

import json
import os
from pathlib import Path

STORE_PATH = Path("data/agent_store.json")

def load() -> dict:
    """Load all persisted state from disk."""
    if not STORE_PATH.exists():
        return {}
    with open(STORE_PATH) as f:
        return json.load(f)

def save(data: dict) -> None:
    """Write all state to disk."""
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)

def get(key: str, default=None):
    """Read a single value."""
    return load().get(key, default)

def set(key: str, value) -> None:
    """Write a single value, preserving all other keys."""
    data = load()
    data[key] = value
    save(data)
```

Add `data/` to your .gitignore (it may contain user data):

```bash
echo "data/" >> .gitignore
```

Decide what your agent stores in Tier 3:

```
Tier 3 (persistent): [what gets stored here]
Example: completed decisions written to agent_store.json
         Schema: { "decisions": [{ "id", "outcome", "timestamp" }] }
```

---

## Step 4: Connect Memory to Your Tool

Update one of your tool functions from Assignment 06 to use the session store
or persistent store. For example, cache a lookup result in Tier 2:

```python
from agent.session_store import session

def get_order_status(order_id: str) -> dict:
    # Check Tier 2 cache first
    cached = session.get(f"order:{order_id}")
    if cached:
        return cached

    # If not cached, do the real lookup
    result = {
        "order_id": order_id,
        "status": "shipped",
        "estimated_delivery": "2026-07-15"
    }

    # Cache for the rest of this session
    session.set(f"order:{order_id}", result)
    return result
```

---

## Step 5: Test Persistence Across Restarts

Call your persistent store, write something, then restart the process and
confirm the data is still there:

```python
# Terminal 1: write
from agent.persistent_store import set
set("last_test_run", "2026-07-08")

# Stop the process. Start a new Python shell.
# Terminal 2: read
from agent.persistent_store import get
print(get("last_test_run"))  # Should print: 2026-07-08
```

---

## Step 6: Update Your CLAUDE.md

Fill in the Memory Rules section completely:

```
## Memory Rules

Tier 1 (in-context): last [N] turns of conversation history
Tier 2 (session store): [what is cached and why]
Tier 3 (persistent): [what is stored and the file/table name]

What is never stored: [list things that must not be persisted: secrets, PII, raw API responses]
```

---

## You Are Done When

- [ ] Tier 1 works: agent references earlier turns correctly
- [ ] `agent/session_store.py` exists and is used by at least one tool
- [ ] `agent/persistent_store.py` exists and data survives a process restart
- [ ] `data/` is in .gitignore
- [ ] Your CLAUDE.md Memory Rules section has all three tiers documented with specifics
- [ ] You have listed what is never stored

---

## If You Get Stuck

Persistent store file not found: confirm `STORE_PATH.parent.mkdir(parents=True, exist_ok=True)` runs before the write. The `data/` folder must exist before the file can be created.

Session store not sharing state across tool calls: confirm you are importing the singleton `session` object, not instantiating a new `SessionStore()` each time.

Data from Tier 3 growing without bound: add a cleanup function to your persistent store that removes entries older than 30 days. Call it at the start of each session.

---

## Next Assignment

[10-add-observability.md](10-add-observability.md)

---

Copyright Janna AI Research Labs
