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
# Clean DOM: compress to summary FIRST, then delete raw files
CONTEXT_FILE="$CONV_DIR/browser_context.md"
DOM_COUNT=$(find "$CONV_DIR" \( -name "*dom*" -o -name "*.mhtml" -o -name "*_snapshot*" \) 2>/dev/null | wc -l)
if [ "$DOM_COUNT" -gt 0 ]; then
  # Extract page titles before deleting
  {
    echo "# Browser Context — $(date -Iseconds)"
    for f in $(find "$CONV_DIR" \( -name "*dom*" -o -name "*.mhtml" \) 2>/dev/null | head -10); do
      TITLE=$(grep -oP '(?<=<title>)[^<]+' "$f" 2>/dev/null | head -1)
      [ -n "$TITLE" ] && echo "- $TITLE"
    done
    echo ""
    echo "_AI: append session findings below_"
  } >> "$CONTEXT_FILE" 2>/dev/null
fi
# Then delete raw DOM files
find "$CONV_DIR" -name "*dom*" ! -name "browser_context.md" -delete 2>/dev/null || true
find "$CONV_DIR" -name "*.mhtml" -delete 2>/dev/null || true
find "$CONV_DIR" -name "*_dom.json" -o -name "*_snapshot*" -o -name "*page_source*" -o -name "*_content.html" 2>/dev/null | xargs rm -f 2>/dev/null || true
rm -rf "$CONV_DIR"/.system_generated/dom_snapshots/ 2>/dev/null || true
rm -rf "$CONV_DIR"/.system_generated/page_content/ 2>/dev/null || true
```

### Context Compression
After cleanup, state: `🗜️ Browser context compressed. Key findings: [3-5 bullets]`
Read `browser_context.md` to recover browser state in future sessions.
Do NOT reference deleted artifacts in future responses.

### Dynamic Routing
Read `SKILLS_ROUTER.md` at conversation start.
Read `rules/context-router.md` for full routing protocol.
Re-read every 15 messages.
Skills are loaded from `skills/*/SKILL.md` on-demand via the routing table.

## RULES INHERITANCE
This file extends `AGENTS.md`. All rules in `AGENTS.md` apply here.
