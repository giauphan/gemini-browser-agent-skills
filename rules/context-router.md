---
trigger: always_on
priority: critical
description: Meta-rule that teaches AI to dynamically load skills on-demand instead of preloading everything. Saves tokens and prevents context amnesia.
---

# 🧠 Context Router — Dynamic Skill Loading Protocol

## Problem This Solves

Loading ALL rules and skills into every chat wastes tokens, bloats context, and causes AI to **forget rules** as conversations grow longer (context window overflow).

## Solution: On-Demand Routing

Instead of pre-loading all rules, the AI carries ONLY this lightweight router and the `SKILLS_ROUTER.md` index. When a specific situation arises, the AI **self-loads** the relevant skill file.

## MANDATORY Behavior

### 1. At Conversation Start
- Read `SKILLS_ROUTER.md` (the index) — this costs < 50 tokens
- Do NOT read any skill files yet
- Do NOT preload `rules/rule-using-browser.md` or any skill files

### 2. Before Every Task
- Check `SKILLS_ROUTER.md` routing table
- If task matches a trigger condition → use `read_file` / `view_file` to load that skill
- If no match → proceed normally (zero extra token cost)

### 3. During Long Conversations (> 15 messages)
- Re-read `SKILLS_ROUTER.md` every 15 messages to refresh routing awareness
- When user gives a new task, ALWAYS re-check the routing table
- NEVER assume you still remember rules from earlier in the conversation

### 4. On Error / Failure
- If Browser Subagent fails → IMMEDIATELY read `skills/browser-cleanup.md`
- If disk space warning appears → read `skills/browser-heavy-cleanup.md`
- If any command shows `[AI_SYSTEM_HINT]` in output → follow the hint instructions

## Token Budget

| Component | Estimated Tokens | When Loaded |
|---|---|---|
| `SKILLS_ROUTER.md` | ~50 | Always (conversation start) |
| `context-router.md` (this file) | ~100 | Always (conversation start) |
| Individual skill files | ~100-200 each | On-demand only |
| **Total idle cost** | **~150** | vs ~800+ if all preloaded |

## Self-Verification

Before acting on any browser-related task, state which skill file you loaded and why.
Format: `📋 Loaded: [filename] — Reason: [trigger condition matched]`
