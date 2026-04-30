---
trigger: always_on
priority: critical
weight: minimal
---

# 🧭 SKILLS ROUTER — Dynamic Context Index

> **DO NOT** preload all skill/rule files. Use this index to load ONLY what you need, WHEN you need it.

## Routing Table

| Trigger Condition | Action | File to Read |
|---|---|---|
| **BEFORE** launching Browser Subagent | Run pre-flight checks | `skills/browser-preflight.md` |
| **AFTER** Browser Subagent returns | Run cleanup immediately | `skills/browser-cleanup.md` |
| Disk > 10GB OR user says "clean browser" | Run nuclear cleanup | `skills/browser-heavy-cleanup.md` |
| Any browser-related task | Load browser rules | `rules/rule-using-browser.md` |
| Before writing ANY code | Self-check rules | `rules/self-check.md` |

## How to Use This Router

1. **Match** the current task against the "Trigger Condition" column above
2. **Read** the corresponding file using your file-reading tool (e.g., `read_file`, `view_file`, `@filename`)
3. **Execute** the instructions in that file
4. If NO condition matches → proceed normally without loading extra context

## CRITICAL Rules (Always Active — No File Load Needed)

- **NEVER** run Browser Subagent for more than 10 steps without pausing
- **ALWAYS** summarize browser session results BEFORE deleting artifacts
- **ALWAYS** clean up `.webp` and `.png` files after browser sessions
- **NEVER** delete the entire `~/.gemini/antigravity` directory
