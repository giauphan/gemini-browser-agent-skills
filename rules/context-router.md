---
trigger: always_on
priority: critical
description: Lightweight meta-rule for on-demand skill loading. Cost ~100 tokens.
---

# Context Router — Dynamic Skill Loading

## MANDATORY: On-Demand Loading

DO NOT preload all skill/rule files. Load ONLY what you need, WHEN you need it.

### At Conversation Start
1. Read `SKILLS_ROUTER.md` (~50 tokens) — this is your routing index
2. Do NOT read any other skill or rule files yet

### Before Every Task
1. Match task against `SKILLS_ROUTER.md` routing table
2. If match found → `read_file` / `view_file` to load that skill
3. If no match → proceed normally (zero extra cost)

### Every 15 Messages
- Re-read `SKILLS_ROUTER.md` to refresh routing awareness
- NEVER assume you still remember rules from earlier

### On Error
- If `[AI_SYSTEM_HINT]` appears in terminal output → follow hint instructions
- If Browser Subagent fails → load `skills/browser-cleanup/SKILL.md` IMMEDIATELY
