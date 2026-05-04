---
trigger: on_demand
loaded_by: SKILLS_ROUTER.md
description: Full browser session management. Only loaded when browser task is triggered — NOT always-on.
---

# Browser Subagent — Session Management

## EXECUTION PROTOCOL

### Phase 0: Route Discovery (BEFORE planning)
1. Run `skills/browser-route-discovery/SKILL.md` — read project route files
2. Build a Route Map of all valid URLs
3. Discover dev server port (check running processes + config)
4. **NEVER plan browser steps with guessed/assumed URLs**

### Phase 1: Pre-Flight (BEFORE browser launch)
1. Run `skills/browser-preflight/SKILL.md` checks
2. If ANY check fails → STOP, warn user
3. Load `skills/browser-tab-manager/SKILL.md` — include tab management rules in task prompt
4. Validate ALL planned URLs against Route Map from Phase 0
5. Plan milestones: split task into chunks of **≤ 10 browser steps**

### Phase 2: Milestone Execution
- Include **Tab Management Rules** in EVERY Browser Subagent task prompt (see `skills/browser-tab-manager/SKILL.md`)
- Before navigating → check if URL already open, reuse tab if so
- Execute ≤ 10 browser steps per milestone
- At milestone end → close stale tabs, then Browser Subagent MUST return
- Summarize results → run cleanup → start next milestone

### Phase 3: Post-Session (AFTER browser returns)
Execute `skills/browser-cleanup/SKILL.md` — every time, no exceptions.

Order: Summarize → Delete .webp → Kill zombies → Clean .png

## CONTEXT COMPRESSION (Post-Browser)

After cleanup completes:
1. Write 3-5 bullet summary of browser findings
2. State: `🗜️ Browser context compressed. Artifacts deleted.`
3. Do NOT reference deleted screenshots/recordings in future responses
4. Treat the text summary as the ONLY memory of what happened

## CONSTRAINTS
- NEVER run > 10 browser steps without returning
- NEVER delete `~/.gemini/antigravity` directory itself
- NEVER retry browser without cleanup first
- ALWAYS summarize BEFORE deleting artifacts
- NEVER navigate to a URL without reading project routes first
- NEVER guess URLs — always validate against Route Map
- If 404 encountered → re-run Route Discovery, do NOT keep guessing
