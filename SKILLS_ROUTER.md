---
trigger: always_on
priority: critical
weight: minimal
---

# SKILLS ROUTER — Dynamic Context Index

> Load ONLY what you need, WHEN you need it. NEVER preload all files.

## Routing Table

| # | Trigger Condition | Load File | Est. Tokens |
|---|---|---|---|
| 1 | BEFORE launching Browser Subagent | `skills/browser-preflight/SKILL.md` | ~150 |
| 2 | AFTER Browser Subagent returns | `skills/browser-cleanup/SKILL.md` | ~200 |
| 3 | Disk > 10GB OR user says "clean" | `skills/browser-heavy-cleanup/SKILL.md` | ~250 |
| 4 | Any browser-related task (plan/execute) | `rules/rule-using-browser.md` | ~200 |
| 5 | Before writing ANY code | `rules/self-check.md` | ~150 |
| 6 | BEFORE navigating to URL OR tab count > 3 | `skills/browser-tab-manager/SKILL.md` | ~180 |
| 7 | BEFORE planning browser steps (route check) | `skills/browser-route-discovery/SKILL.md` | ~200 |
| 8 | **ANY browser task** (2-agent pattern) | `skills/browser-observe-then-act/SKILL.md` | ~200 |
| 9 | **ANY browser task** (anti-loop prompts) | `skills/browser-anti-loop/SKILL.md` | ~300 |
| 10 | Browser task with **> 10 steps** OR AI repeating | `skills/browser-self-reflection/SKILL.md` | ~250 |
| 11 | AI action **repeated 2+ times** OR DOM unchanged | `skills/browser-loop-breaker/SKILL.md` | ~280 |
| 12 | Task has **> 10 steps** total OR multi-step test | `skills/browser-checkpoint-manager/SKILL.md` | ~220 |

## How to Use

1. **Match** current task against Trigger Condition column
2. **Read** the file using `read_file` / `view_file` / `@filename`
3. **Execute** instructions in that file
4. **No match** → proceed normally (0 extra tokens)

## CRITICAL Rules (Always Active — No File Load)

1. NEVER run Browser Subagent > 10 steps without pausing
2. ALWAYS summarize browser results BEFORE deleting artifacts
3. ALWAYS delete `.webp`, `.png`, and DOM snapshot files after browser sessions
4. NEVER delete the entire `~/.gemini/antigravity` directory
5. ALWAYS verify file reading count: "Read X/Y files" before proceeding
6. ALWAYS compress browser context to text summary after cleanup
7. NEVER navigate to a URL without reading project routes first — no guessing
8. ALWAYS clean DOM files after browser session completes
9. **NEVER** attempt the same browser action more than 3 times — switch strategy
10. **ALWAYS** use Observe-Then-Act pattern: browser subagent = hands, outer AI = brain
11. **NEVER** put both "find element" and "click element" in one browser_subagent call
12. **ALWAYS** include Anti-Loop protocol in ALL browser task prompts
13. **ALWAYS** trust SCREENSHOT over HTML/DOM for element visibility
14. **ALWAYS** include Self-Reflection protocol in tasks > 10 steps
15. **ALWAYS** split tasks > 10 steps into Checkpoints before execution

## Token Budget

| State | Cost |
|---|---|
| Idle (no browser) | ~100 tokens (this file only) |
| Short browser task (≤10 steps) | ~1130 tokens (preflight + tabs + cleanup + routes + anti-loop) |
| Long browser task (>10 steps) | ~1880 tokens (+ self-reflection + loop-breaker + checkpoints) |
| All preloaded (old way) | ~2100+ tokens |
