---
trigger: on_demand
loaded_by: SKILLS_ROUTER.md
description: Full browser session management. Only loaded when browser task is triggered — NOT always-on.
---

# Browser Subagent — Session Management

## EXECUTION PROTOCOL

### Phase 1: Pre-Flight (BEFORE browser launch)
1. Run `skills/browser-preflight/SKILL.md` checks
2. If ANY check fails → STOP, warn user
3. Plan milestones: split task into chunks of **≤ 10 browser steps**

### Phase 2: Milestone Execution
- Execute ≤ 10 browser steps per milestone
- At milestone end → Browser Subagent MUST return
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
