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

## How to Use

1. **Match** current task against Trigger Condition column
2. **Read** the file using `read_file` / `view_file` / `@filename`
3. **Execute** instructions in that file
4. **No match** → proceed normally (0 extra tokens)

## CRITICAL Rules (Always Active — No File Load)

1. NEVER run Browser Subagent > 10 steps without pausing
2. ALWAYS summarize browser results BEFORE deleting artifacts
3. ALWAYS delete `.webp` and `.png` files after browser sessions
4. NEVER delete the entire `~/.gemini/antigravity` directory
5. ALWAYS verify file reading count: "Read X/Y files" before proceeding
6. ALWAYS compress browser context to text summary after cleanup

## Token Budget

| State | Cost |
|---|---|
| Idle (no browser) | ~100 tokens (this file only) |
| Browser task | ~450 tokens (this + preflight + cleanup) |
| All preloaded (old way) | ~800+ tokens |
