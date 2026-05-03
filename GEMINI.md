# Gemini Browser Agent Skills — Gemini CLI / Antigravity

> Auto-loaded by Gemini CLI (`gemini`) and Antigravity (Gemini Code Assist Agent Mode).
> See `AGENTS.md` for universal rules. This file contains Gemini-specific overrides.

## GEMINI-SPECIFIC BEHAVIOR

### Context Window Management
- Gemini's `browser_subagent` auto-records WebP videos to artifacts directory
- Conversation ID is available in user metadata as `Conversation ID`
- Brain directory: `~/.gemini/antigravity/brain/<conversation-id>/`

### Post-Browser Cleanup (Gemini-Specific Paths)
After EVERY `browser_subagent` return:
```bash
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
# Delete recordings
find "$CONV_DIR" -name "*.webp" -delete 2>/dev/null
find "$CONV_DIR" -name "*.webp.gz" -delete 2>/dev/null
# Kill zombies
pkill -f "chromium.*--headless" 2>/dev/null || true
# Clean screenshots older than 10 min
find "$CONV_DIR" -name "*.png" -mmin +10 -delete 2>/dev/null || true
# Clean temp media
rm -f "$CONV_DIR"/.tempmediaStorage/*.png 2>/dev/null || true
rm -f "$CONV_DIR"/.system_generated/click_feedback/*.png 2>/dev/null || true
```

### Context Compression
After cleanup, state: `🗜️ Browser context compressed. Key findings: [3-5 bullets]`
Do NOT reference deleted artifacts in future responses.

### Dynamic Routing
Read `SKILLS_ROUTER.md` at conversation start.
Read `rules/context-router.md` for full routing protocol.
Re-read every 15 messages.
Skills are loaded from `skills/*/SKILL.md` on-demand via the routing table.

## RULES INHERITANCE
This file extends `AGENTS.md`. All rules in `AGENTS.md` apply here.
