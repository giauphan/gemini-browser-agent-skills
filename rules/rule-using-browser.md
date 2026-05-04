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
6. **If task has > 10 steps total**: Load `skills/browser-checkpoint-manager/SKILL.md` — define checkpoints

### Phase 1.5: Long-Horizon Setup (IF task > 10 steps)
1. Load `skills/browser-self-reflection/SKILL.md` — include Self-Reflection protocol in ALL task prompts
2. Load `skills/browser-loop-breaker/SKILL.md` — initialize action tracker
3. Load `skills/browser-checkpoint-manager/SKILL.md` — define checkpoint plan
4. Initialize tracking: create `action_history.jsonl` and `checkpoint_state.md`

### Phase 2: Milestone Execution (Observe-Then-Act Pattern)

For EACH step within a milestone, use the **2-agent pattern**:

```
Step N of milestone:
  1. OBSERVE call → browser subagent reports page state (no clicking)
  2. OUTER AI analyzes → identifies target, checks for blockers
  3. ACT call → browser subagent performs ONE precise action
  4. OUTER AI verifies → did the action succeed?
     YES → next step
     NO → re-observe, change strategy
```

Rules for each call:
- **OBSERVE call**: Include `skills/browser-observe-then-act/SKILL.md` observe prompt
- **ACT call**: ONE action only. Include anti-loop protocol from `skills/browser-anti-loop/SKILL.md`
- Before navigating → check if URL already open, reuse tab if so
- Execute ≤ 10 steps per milestone (1 observe+act pair = 1 step)
- At milestone end → close stale tabs, then Browser Subagent MUST return
- **After each milestone**: Run loop_guard check, update checkpoint state
- Summarize results → run cleanup → start next milestone

### Phase 2.5: Mid-Execution Verification (AFTER each milestone)
1. Run loop detection script from `skills/browser-loop-breaker/SKILL.md`
2. If loop detected → STOP current approach → apply recovery protocol
3. Update `checkpoint_state.md` with milestone result
4. Write Working Memory Summary (from Self-Reflection skill)
5. If checkpoint FAILED → decide: retry (max 3) or skip or stop

### Phase 3: Post-Session (AFTER browser returns)
Execute `skills/browser-cleanup/SKILL.md` — every time, no exceptions.

Order: Summarize → Delete .webp → Kill zombies → Clean .png

## CONTEXT COMPRESSION (Post-Browser)

After cleanup completes:
1. Write 3-5 bullet summary of browser findings
2. Include Working Memory Summary if long-horizon task
3. Include Checkpoint Results if checkpointed task
4. State: `🗜️ Browser context compressed. Artifacts deleted.`
5. Do NOT reference deleted screenshots/recordings in future responses
6. Treat the text summary as the ONLY memory of what happened

## CONSTRAINTS
- NEVER run > 10 browser steps without returning
- NEVER delete `~/.gemini/antigravity` directory itself
- NEVER retry browser without cleanup first
- ALWAYS summarize BEFORE deleting artifacts
- NEVER navigate to a URL without reading project routes first
- NEVER guess URLs — always validate against Route Map
- If 404 encountered → re-run Route Discovery, do NOT keep guessing
- **NEVER** attempt same action more than 3 times — switch strategy or stop
- **NEVER** put "find element" AND "click element" in one browser_subagent call
- **ALWAYS** use Observe-Then-Act: browser subagent = hands, outer AI = brain
- **ALWAYS** use Self-Reflection protocol for tasks > 10 steps
- **ALWAYS** define checkpoints for tasks > 10 steps total
