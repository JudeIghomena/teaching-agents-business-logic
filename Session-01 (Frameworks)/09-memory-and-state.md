# Framework 09: Memory and State

> An agent without memory answers every question as if it is the first.
> The design of your memory layer determines whether your agent feels
> intelligent or amnesiac.

---

## The Three Tiers of Agent Memory

Agent memory exists at three distinct tiers. Each has a different lifetime,
a different cost, and a different appropriate use case.

```
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 1: IN-CONTEXT MEMORY                                         │
│  Lifetime: one conversation session                                 │
│  Storage: the context window (tokens)                               │
│  What belongs here: the current conversation, tool results,         │
│                     session-specific injected data                  │
│  Cost: tokens per turn                                              │
└─────────────────────────────────────────────────────────────────────┘
           ↕ (session ends, tier 1 is lost)
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 2: SESSION MEMORY                                            │
│  Lifetime: one server session (minutes to hours)                    │
│  Storage: in-memory dict / Redis / server-side cache                │
│  What belongs here: user preferences set this session, intermediate │
│                     results, workflow state across multiple turns   │
│  Cost: server RAM or cache cost                                     │
└─────────────────────────────────────────────────────────────────────┘
           ↕ (session expires, tier 2 is lost unless promoted)
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 3: PERSISTENT MEMORY                                         │
│  Lifetime: indefinite (until explicitly deleted)                    │
│  Storage: database (PostgreSQL, SQLite, vector DB, etc.)            │
│  What belongs here: user profile, past decisions, learned           │
│                     preferences, completed task history             │
│  Cost: storage + retrieval query per session                        │
└─────────────────────────────────────────────────────────────────────┘
```

The most common architecture mistake is putting Tier 3 data into Tier 1
(context window) for every turn. It works but wastes tokens on data that
has not changed since last session.

---

## Tier 1: In-Context Memory: What Goes Here

```python
# context.py: ConversationContext holds all Tier 1 memory

@dataclass
class ConversationContext:
    # The system message, built once, persists through the session
    system_message: str = ""

    # The conversation history, grows each turn
    messages: list[dict] = field(default_factory=list)

    # Session data injected at start, resolved fresh from DB, not stored here
    # This is Tier 3 data that has been "lifted" into Tier 1 for this session
    session_metadata: dict = field(default_factory=dict)
```

### What to put in Tier 1

- The system message (built from Tier 3 data at session start)
- The current conversation history
- Tool results from this session
- Dynamically retrieved data needed for the current turn

### What NOT to put in Tier 1

- Bulk historical records (use a tool to retrieve specific records)
- Data that will not change during this session (put it in the system message once)
- Secrets or auth tokens (never in context)
- Unvalidated user input in the system role (always in user turn)

---

## Tier 2: Session Memory: Pattern

Session memory lives server-side and survives multiple turns without being
re-injected into context each time.

```python
# agent/session_store.py

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SessionState:
    """
    Server-side session memory. Not injected into the context window
    every turn, retrieved only when needed.
    """
    session_id: str
    user_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)

    # Workflow state, where is the user in a multi-step process?
    workflow_step: str = "initial"
    workflow_data: dict = field(default_factory=dict)

    # Preferences set during this session (not yet persisted to DB)
    pending_preferences: dict = field(default_factory=dict)

    # Actions taken this session, for audit trail
    actions_taken: list[str] = field(default_factory=list)


# Simple in-memory store for single-server deployments
# Replace with Redis for multi-server or persistent-session deployments
_sessions: dict[str, SessionState] = {}


def create_session(session_id: str, user_id: str) -> SessionState:
    session = SessionState(session_id=session_id, user_id=user_id)
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> SessionState | None:
    return _sessions.get(session_id)


def update_session_step(session_id: str, step: str, data: dict = None) -> None:
    session = _sessions.get(session_id)
    if session:
        session.workflow_step = step
        if data:
            session.workflow_data.update(data)


def record_action(session_id: str, action: str) -> None:
    session = _sessions.get(session_id)
    if session:
        session.actions_taken.append(f"{datetime.utcnow().isoformat()} | {action}")
```

---

## Tier 3: Persistent Memory: Pattern

Persistent memory lives in a database and survives across sessions.
It is loaded at session start, selectively injected into Tier 1.

```python
# agent/memory_store.py

from dataclasses import dataclass


@dataclass
class UserMemory:
    """
    Persistent memory for a user, retrieved from DB at session start,
    injected selectively into the system message or conversation.
    """
    user_id: str
    display_name: str
    account_tier: str
    preferred_contact: str
    past_decisions: list[dict]      # Summaries of previous agent interactions
    learned_preferences: dict       # Preferences extracted from past sessions


def load_user_memory(user_id: str) -> UserMemory:
    """
    Load from DB. Replace with your ORM or query layer.
    Use a parameterised query, never string concatenation.
    """
    # cursor.execute("SELECT * FROM user_memory WHERE user_id = %s", (user_id,))
    # row = cursor.fetchone()
    # return UserMemory(**row)

    # Mock for this example:
    return UserMemory(
        user_id=user_id,
        display_name="Amara Osei",
        account_tier="gold",
        preferred_contact="email",
        past_decisions=[
            {"date": "2026-06-01", "action": "applied 15% discount", "reason": "billing error"},
        ],
        learned_preferences={"response_length": "brief", "formality": "professional"},
    )


def inject_memory_into_context(memory: UserMemory) -> str:
    """
    Converts Tier 3 memory into a string suitable for injection into
    the system message or as a user turn prefix.

    Only inject what is relevant. Past decisions are a summary, not the
    full history. Learned preferences shape format, not content.
    """
    decisions_summary = "; ".join(
        f"{d['date']}: {d['action']}" for d in memory.past_decisions[-3:]
    )
    return (
        f"Customer profile: {memory.display_name}, {memory.account_tier} tier. "
        f"Preferred contact: {memory.preferred_contact}. "
        f"Recent history: {decisions_summary}. "
        f"Communication preference: {memory.learned_preferences.get('response_length', 'standard')} responses."
    )
```

---

## The Memory Promotion Pattern

When something important happens in a session, you promote it from Tier 2
to Tier 3 so it survives future sessions.

```python
# At the end of a session, or after a significant decision:

def promote_session_to_persistent(session: SessionState, db_cursor) -> None:
    """
    Promotes relevant session data to persistent memory.
    Called at session end or after high-value actions.

    Not everything is promoted, only what future sessions need to know.
    """
    if not session.actions_taken:
        return

    # Summarise actions into a decision record
    decision_record = {
        "date": session.started_at.date().isoformat(),
        "session_id": session.session_id,
        "actions": session.actions_taken,
        "final_step": session.workflow_step,
    }

    # Write to persistent store with a parameterised query
    db_cursor.execute(
        "INSERT INTO user_decisions (user_id, record) VALUES (%s, %s)",
        (session.user_id, json.dumps(decision_record)),
    )

    # Promote pending preferences that were validated this session
    if session.pending_preferences:
        db_cursor.execute(
            "UPDATE user_preferences SET preferences = %s WHERE user_id = %s",
            (json.dumps(session.pending_preferences), session.user_id),
        )
```

---

## Memory Tier Decision Guide

When you encounter a new piece of information in your agent, ask:

```
Does this need to survive after this conversation ends?
  NO  → Tier 1 (in context) or Tier 2 (session state)
  YES → Tier 3 (database)

Does this change every turn?
  YES → Tier 1 (update in context window)
  NO  → Tier 2 (update in session state, inject into context only when it changes)

Will future sessions need this without being told again?
  YES → Tier 3 + promote at session end
  NO  → Tier 1 or Tier 2 is enough
```

---

## Sample: Memory Layer Checklist

```
MEMORY DESIGN CHECKLIST: [YOUR AGENT NAME]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIER 1: IN-CONTEXT
[ ] What user data is injected into the system message at session start?
    Answer: ________________________________________________
[ ] How is conversation history trimmed when it grows large?
    Answer: ________________________________________________
[ ] What is never allowed in the context window?
    Answer: (secrets, auth tokens, raw PII, unvalidated user input in system role)

TIER 2: SESSION STATE
[ ] What workflow steps need to be tracked across turns?
    Answer: ________________________________________________
[ ] What temporary preferences or selections should survive this session?
    Answer: ________________________________________________
[ ] What is your session store? (in-memory dict / Redis / other)
    Answer: ________________________________________________

TIER 3: PERSISTENT
[ ] What does the next session need to know without being told again?
    Answer: ________________________________________________
[ ] When does promotion from Tier 2 to Tier 3 happen?
    Answer: ________________________________________________
[ ] What is your persistent store? (PostgreSQL / SQLite / other)
    Answer: ________________________________________________

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Apply to Your Coding Agent

**Task:** Add memory rules to your CLAUDE.md that tell your coding agent what
it should carry across sessions, what it must not retain, and how the three
memory tiers map to what it should and should not change in your codebase.

**Why this matters:** Coding agents maintain continuity through CLAUDE.md and
conversation context. Without memory rules, an agent tries to retain everything
(filling context with stale session details) or retains nothing (making you
repeat project decisions every session). Written rules calibrate the right
boundary.

**Step 1: Identify what each tier means for your coding agent**

Tier 1 (in-context, this session only):
- The specific task you gave it this session
- Errors encountered and fixes tried this session
- Test results from this session

Tier 2 (working context, within one long session):
- The file currently being worked on
- The current bug being debugged
- What tests have passed so far this session

Tier 3 (persisted across sessions, what lives in CLAUDE.md):
- Architecture decisions that do not change between sessions
- Security rules that apply to every session permanently
- The tool allowlist and which tools are excluded
- Model routing decisions and why

**Step 2: Copy this template into CLAUDE.md**

```
## Memory Rules

### What to remember across sessions (permanent, lives in CLAUDE.md)
- Project structure and file placement rules (see Project Structure section)
- Tool allowlist and addition policy (see Registered Tools section)
- Security rules (see Security Rules section)
- Model routing decision and reason (see Model Routing Rules section)
- Context budget targets (see Context Management Rules section)

### What to remember within this session only
- The specific task requested in this conversation
- Errors encountered and their resolutions this session
- Test results from this session
Discard all of these at session end. Do not write them back to CLAUDE.md.

### What to never retain or store
- Contents of .env or any secret value seen during the session
- Customer names, IDs, or account data (this is agent runtime data)
- API responses from test runs (these are ephemeral)
- Step-by-step reasoning traces (remember the outcome, not the path)

### When to update CLAUDE.md during a session
If we make a decision that should apply to all future sessions
(e.g. "we decided to move to Redis for session store"), propose adding it
to the relevant section of CLAUDE.md and wait for my approval before writing.
Do not write directly to CLAUDE.md without telling me first.
```

**Step 3: Paste into CLAUDE.md**

Open your project CLAUDE.md. Add this block under `## Memory Rules`. It should
come after the tool allowlist and before the output format rules.

**Step 4: Apply to your coding tool**

For Claude Code: this is native to CLAUDE.md. The most important line is the
one about not writing session-specific details back to CLAUDE.md. Claude Code
will keep CLAUDE.md clean and authoritative, not polluted with per-session notes.

For Cursor: paste into `.cursorrules`. Cursor will apply the tier rules when
deciding what context to carry forward.

For Codex: add to the workspace system prompt.

**What you now have:** A coding agent that knows the difference between what
belongs in CLAUDE.md (permanent architectural decisions) and what belongs only
in this session's context (current task, current errors). CLAUDE.md stays
clean. Session context stays relevant. You do not repeat yourself every session.

---

## Using Claude Code Desktop App

Open your project folder in the Claude Code desktop app. Claude Code already
knows the three-tier memory model from your CLAUDE.md Memory Rules section.
Use it to implement the Tier 2 session store and Tier 3 persistent store.

**Prompt to implement three-tier memory:**

```
Add Tier 2 and Tier 3 memory to my agent.

Tier 2 - agent/session_store.py:
  - SessionStore class with set(key, value), get(key, default), clear()
  - Module-level singleton: session = SessionStore()
  - Use it to cache: [what your agent should cache across turns]

Tier 3 - agent/persistent_store.py:
  - STORE_PATH = Path("data/agent_store.json")
  - load() -> dict, save(data: dict), get(key, default), set(key, value)
  - STORE_PATH.parent.mkdir(parents=True, exist_ok=True) before writing
  - Use it to persist: [what your agent must remember across restarts]

Add data/ to .gitignore if it is not already there.

Connect Tier 2 to at least one tool in agent/tool_registry.py:
  - Check session.get(cache_key) before doing the real lookup
  - Cache the result with session.set(cache_key, result) after

Verify Tier 3 works across restarts:
  python -c "from agent.persistent_store import set; set('test_key', 'test_value'); print('Written')"
  python -c "from agent.persistent_store import get; print(get('test_key'))"
  (stop and restart Python between the two commands)

Update the Memory Rules section of CLAUDE.md with what is stored in each tier.
```

**What Claude Code will do:**
Implement both store files, wire the session store into one of your tools,
run the persistence test, and update your CLAUDE.md Memory Rules section
with the specific values each tier holds.

**Tips for this framework:**
- Tell Claude Code specifically what to cache in Tier 2 and what to persist in
  Tier 3 before asking it to implement. Generic stores produce generic code.
- Ask Claude Code: "What should never be stored in any tier?" The answer (secrets,
  PII, raw API responses) should go into the Memory Rules section of CLAUDE.md.

---

Copyright Janna AI Research Labs
