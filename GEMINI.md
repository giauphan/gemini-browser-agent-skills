# Gemini Browser Agent Skills — Gemini CLI / Antigravity

> Auto-loaded by Gemini CLI (`gemini`) and Antigravity (Gemini Code Assist Agent Mode).
> See `AGENTS.md` for universal rules. This file contains Gemini-specific overrides.

## GEMINI-SPECIFIC BEHAVIOR

### Context Window Management
- Gemini's `browser_subagent` auto-records WebP videos to artifacts directory
- Conversation ID is available in user metadata as `Conversation ID`
- Brain directory: `~/.gemini/antigravity/brain/<conversation-id>/`

### ⚠️ LOOP PREVENTION (CRITICAL — Read Before Every Browser Task)

**Problem**: Browser subagent clicks wrong → loops forever → entire test fails.
**Solution**: Run `loop_guard` check BETWEEN every browser_subagent call.

#### BEFORE launching browser_subagent (for tasks > 5 steps):
```bash
# Initialize loop tracking
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
SCRIPT_DIR="$(find / -path '*/gemini-browser-agent-skills/scripts/loop_guard.sh' 2>/dev/null | head -1)"
if [ -n "$SCRIPT_DIR" ]; then
  source "$SCRIPT_DIR"
  loop_guard_init "$CONV_DIR/loop_guard"
fi
```

#### AFTER every browser_subagent returns:
The outer AI MUST do these 3 things:
1. **Summarize** what the browser subagent did (action + target + result)
2. **Log** it to loop_guard
3. **Check** for loops BEFORE launching browser again

```bash
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
SCRIPT_DIR="$(find / -path '*/gemini-browser-agent-skills/scripts/loop_guard.sh' 2>/dev/null | head -1)"
if [ -n "$SCRIPT_DIR" ]; then
  source "$SCRIPT_DIR"
  LOOP_GUARD_DIR="$CONV_DIR/loop_guard"

  # AI fills these based on browser subagent's report
  # ACTION: click | type | scroll | navigate | press_key
  # TARGET: the element or URL that was interacted with
  # RESULT: success | no_change | error | timeout
  loop_guard_log "<ACTION>" "<TARGET>" "<RESULT>" "<PAGE_TITLE>" "<URL>"

  # Check for loops — if this returns non-zero, DO NOT launch browser again
  loop_guard_check
  LOOP_STATUS=$?

  if [ "$LOOP_STATUS" -ne 0 ]; then
    echo "🚫 LOOP DETECTED — changing strategy before next browser call"
    loop_guard_hint
  fi
fi
```

#### MANDATORY RULE:
If `loop_guard_check` returns **non-zero**, the AI MUST:
- **NOT** call browser_subagent with the same action
- **Change strategy**: try Escape, scroll, different selector, or different page
- **If stuck 3+ times total**: STOP and ask the user for help

### Browser Subagent Task Prompt — MANDATORY ADDITIONS

Every `browser_subagent` Task prompt MUST include this block at the end:

```
--- ANTI-LOOP PROTOCOL ---
1. Before EVERY click: Check if the target element is actually visible and not covered by popups/modals/overlays
2. After EVERY click: Verify the page state changed (URL, title, visible content)
3. If a click had NO EFFECT: Do NOT retry the same click. Instead:
   a. Press Escape key (dismiss potential overlay)
   b. Scroll the page
   c. Look for alternative path
4. NEVER click the same element more than 2 times in a row
5. If stuck: Return immediately and report what's blocking you

When reporting results, ALWAYS state:
- What action you took
- What element you targeted
- Whether the page state changed (YES/NO)
- Current page title and URL
```

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
