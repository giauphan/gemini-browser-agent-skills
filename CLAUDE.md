# Gemini Browser Agent Skills — Claude Code / Claude CLI

> Auto-loaded by Claude Code and Claude CLI when placed at project root.
> See `AGENTS.md` for universal rules. This file contains Claude-specific overrides.

## CLAUDE-SPECIFIC BEHAVIOR

### Memory Management
- Use `/compact` command when context feels bloated (>80% window used)
- Claude Code supports `CLAUDE.md` at root + nested `CLAUDE.md` in subdirectories
- Subdirectory rules are scoped — only loaded when working in that directory

### Post-Browser Context Protocol
After browser automation tasks:
1. Summarize findings in 3-5 bullets
2. Run cleanup commands from `skills/browser-cleanup/SKILL.md`
3. State: `🗜️ Browser context compressed.`
4. If context window is large → suggest user run `/compact`

### Subagent Usage (Claude Code)
Claude Code supports `context: fork` for isolated skill execution.
For heavy browser analysis → use forked context to prevent main context bloat.

### TodoWrite Integration
Use TodoWrite for multi-step browser tasks:
- Create todo for each milestone (≤ 10 browser steps)
- Mark complete after cleanup
- Track file reading compliance: `Read X/Y files`

### ⚠️ Anti-Loop Protocol (Browser Tasks)
Every browser automation task prompt MUST include:
```
--- ANTI-LOOP PROTOCOL ---
1. Before EVERY click: Verify target is visible and not blocked by popups/overlays
2. After EVERY click: Check if page state changed (URL, title, content)
3. If click had NO EFFECT: Do NOT retry same click — press Escape, scroll, or try different path
4. NEVER click same element more than 2 times in a row
5. If stuck: Return immediately and report the blocker
```
After each browser session, run `scripts/loop_guard.sh` to detect action loops.
If loop detected → change strategy before calling browser again.

### Dynamic Routing
Read `SKILLS_ROUTER.md` at conversation start.
Match tasks against routing table before loading any skill files.

## RULES INHERITANCE
This file extends `AGENTS.md`. All rules in `AGENTS.md` apply here.
