# Gemini Browser Agent Skills

> Universal agent instructions following [agentskills.io](https://agentskills.io) standard.
> Auto-detected by: Claude Code, Gemini CLI, GitHub Copilot, Cursor, Kiro, Codex, and 30+ tools.

## CRITICAL RULES (Always Active)

1. **NEVER** preload all skill/rule files — use dynamic routing via `SKILLS_ROUTER.md`
2. **NEVER** run Browser Subagent > 10 steps without pausing
3. **ALWAYS** summarize browser results BEFORE deleting artifacts
4. **ALWAYS** delete `.webp` recordings + `.png` screenshots + DOM files after browser sessions  
5. **ALWAYS** verify file reading count: state `"Read X/Y files"` before proceeding
6. **NEVER** delete the `~/.gemini/antigravity` directory itself
7. **ALWAYS** compress browser context to text summary after cleanup
8. **NEVER** navigate to a URL without reading project routes first — no guessing
9. **NEVER** attempt the same browser action more than 3 times — switch strategy or stop
10. **ALWAYS** use Observe-Then-Act: browser subagent = hands, outer AI = brain
11. **NEVER** put both "find element" AND "click element" in one browser_subagent call
12. **ALWAYS** include Anti-Loop protocol in ALL browser task prompts
13. **ALWAYS** trust SCREENSHOT over HTML/DOM for element visibility
14. **ALWAYS** use Self-Reflection (`<THINK>`/`<VERIFY>`) for tasks > 10 browser steps
15. **ALWAYS** split tasks > 10 steps into Checkpoints before execution

## ROUTING (On-Demand Skill Loading)

At conversation start, read `SKILLS_ROUTER.md` for the full routing table.
Match each task against trigger conditions. Load skills ONLY when triggered.

| Trigger | Action |
|---|---|
| Browser task detected | Load `skills/browser-route-discovery/SKILL.md` → read routes FIRST |
| Before planning browser steps | Load `skills/browser-preflight/SKILL.md` → then `rules/rule-using-browser.md` |
| Before navigating to URL | Load `skills/browser-tab-manager/SKILL.md` → check & reuse tabs |
| Browser Subagent returns | Load `skills/browser-cleanup/SKILL.md` → execute immediately (incl. DOM cleanup) |
| Disk > 10GB or "clean" requested | Load `skills/browser-heavy-cleanup/SKILL.md` |
| Before writing code | Load `rules/self-check.md` (verify rule compliance) |
| Every 15 messages | Re-read `SKILLS_ROUTER.md` to refresh routing |
| **ANY browser task** (2-agent) | Load `skills/browser-observe-then-act/SKILL.md` → split observe/act calls |
| **ANY browser task** (anti-loop) | Load `skills/browser-anti-loop/SKILL.md` → include anti-loop prompt in task |
| Task > 10 steps OR AI looping | Load `skills/browser-self-reflection/SKILL.md` → add `<THINK>`/`<VERIFY>` |
| Action repeated 2+ times | Load `skills/browser-loop-breaker/SKILL.md` → detect & break loops |
| Multi-step test planning | Load `skills/browser-checkpoint-manager/SKILL.md` → split into checkpoints |

## SELF-CHECK (Before Every Action)

Before writing code or executing tasks:
```
📋 Active Rules: [list top 3 applicable rules]
📂 Files Read: X/Y requested (Missing: [none | list])
```
If files missing → read them NOW before proceeding.

## ERROR RECOVERY

- Terminal shows `[AI_SYSTEM_HINT]` → follow instructions immediately
- Browser fails → load `skills/browser-cleanup/SKILL.md` BEFORE retrying
- Context feels stale (>15 messages) → re-read `SKILLS_ROUTER.md`
- **Action repeated 3 times** → STOP, load Loop Breaker, change strategy
- **Long task failing mid-way** → load Checkpoint Manager, isolate failed section
