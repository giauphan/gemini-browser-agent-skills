---
trigger: before_code_generation
priority: high
description: Forces AI to self-verify rule compliance before writing any code. Prevents rule amnesia in long conversations.
---

# ✅ Self-Check Protocol — Rule Compliance Verification

## When to Activate

This protocol activates **before the AI writes any code** in these situations:
- User requests a new feature implementation
- User asks for a bug fix
- Any task involving Browser Subagent
- Any task after 10+ messages in a conversation

## MANDATORY Self-Check Steps

### Step 1: Identify Active Rules
Before writing code, list the rules that apply to the current task:

```
📋 Active Rules for This Task:
1. [Rule name] — [1-line summary of what it requires]
2. [Rule name] — [1-line summary]
3. [Rule name] — [1-line summary]
```

### Step 2: Verify Context Freshness
Ask yourself:
- "Have I re-read `SKILLS_ROUTER.md` recently?" (If not → re-read it)
- "Is this a browser task?" (If yes → load browser rules)
- "Am I past message 15 in this conversation?" (If yes → refresh all active rules)

### Step 3: Proceed with Code
Only after completing Steps 1 and 2 may you write code.

## Why This Works

This technique is called **"Chain-of-Thought Anchoring"**. By forcing the AI to:
1. Recall rules explicitly (not just implicitly)
2. Write them down before coding
3. Cross-reference against the routing table

...it activates the relevant knowledge in the AI's attention window, dramatically reducing rule violations.

## Override

User can disable this by saying: "Skip self-check" or "No need to list rules."
