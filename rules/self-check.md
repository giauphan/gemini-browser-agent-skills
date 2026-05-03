---
trigger: before_action
priority: high
description: Self-verification protocol. Forces AI to prove rule compliance before acting.
---

# Self-Check Protocol

## WHEN: Before ANY of these actions
- Writing or editing code
- Launching Browser Subagent
- Deleting files or running cleanup
- After 10+ messages in conversation

## MANDATORY Steps

### Step 1: Verify File Reading Compliance
If user requested reading N files:
```
📂 File Reading: Read X/Y requested files.
Missing: [none | list missing files]
```
If X < Y → read missing files NOW before proceeding.

### Step 2: List Active Rules
```
📋 Active Rules:
1. [Rule] — [1-line what it requires]
2. [Rule] — [1-line what it requires]  
3. [Rule] — [1-line what it requires]
```

### Step 3: Verify Context Freshness
- Read `SKILLS_ROUTER.md` recently? (If no → re-read)
- Browser task? (If yes → load browser rules)
- Past message 15? (If yes → refresh routing table)

### Step 4: Proceed
Only after Steps 1-3 → execute task.

## Override
User can skip with: "Skip self-check" or "No need to list rules."
