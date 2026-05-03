# Gemini Browser Agent Skills

> Universal agent instructions following [agentskills.io](https://agentskills.io) standard.
> Auto-detected by: Claude Code, Gemini CLI, GitHub Copilot, Cursor, Kiro, Codex, and 30+ tools.

## CRITICAL RULES (Always Active)

1. **NEVER** preload all skill/rule files — use dynamic routing via `SKILLS_ROUTER.md`
2. **NEVER** run Browser Subagent > 10 steps without pausing
3. **ALWAYS** summarize browser results BEFORE deleting artifacts
4. **ALWAYS** delete `.webp` recordings + `.png` screenshots after browser sessions  
5. **ALWAYS** verify file reading count: state `"Read X/Y files"` before proceeding
6. **NEVER** delete the `~/.gemini/antigravity` directory itself
7. **ALWAYS** compress browser context to text summary after cleanup

## ROUTING (On-Demand Skill Loading)

At conversation start, read `SKILLS_ROUTER.md` for the full routing table.
Match each task against trigger conditions. Load skills ONLY when triggered.

| Trigger | Action |
|---|---|
| Browser task detected | Load `skills/browser-preflight/SKILL.md` → then `rules/rule-using-browser.md` |
| Browser Subagent returns | Load `skills/browser-cleanup/SKILL.md` → execute immediately |
| Disk > 10GB or "clean" requested | Load `skills/browser-heavy-cleanup/SKILL.md` |
| Before writing code | Load `rules/self-check.md` (verify rule compliance) |
| Every 15 messages | Re-read `SKILLS_ROUTER.md` to refresh routing |

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
