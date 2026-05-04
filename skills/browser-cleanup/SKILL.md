---
name: browser-cleanup
description: Clean up browser artifacts, kill zombie processes, and free disk space after using Browser Subagent. Use immediately after every browser session returns — no exceptions. Targets the CURRENT conversation directory only.
compatibility: "Requires Linux with `find`, `pkill`, `du`, `pgrep` commands. Requires the conversation ID from user metadata (Gemini/Antigravity) or session context."
license: MIT
allowed-tools: Bash
metadata:
  triggers:
    - after_browser_session
    - browser_subagent_returns
  token-cost: ~200
  openclaw:
    requires:
      bins:
        - find
        - pkill
        - du
    homepage: https://github.com/giauphan/gemini-browser-agent-skills
---

# Browser Cleanup

Execute this skill **immediately after every Browser Subagent session returns**. No exceptions. No delays. Clean first, think later.

## Step 1: Summarize What Happened

Before touching any files, write a 2-3 sentence summary of what the browser session accomplished. This summary replaces the video recording as context memory.

## Step 2: Delete Browser Recordings (Current Conversation)

> **IMPORTANT**: Use the **current conversation's** brain directory, NOT the global artifacts dir.
> Path: `~/.gemini/antigravity/brain/<current-conversation-id>/`

```bash
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
echo "=== Deleting recordings in current conversation ==="
find "$CONV_DIR" -name "*.webp" -delete 2>/dev/null
find "$CONV_DIR" -name "*.webp.gz" -delete 2>/dev/null
echo "✅ Recordings deleted"
```

## Step 3: Kill Zombie Chromium Processes

```bash
pkill -f "chromium.*--headless" 2>/dev/null || true
pkill -f "chrome.*--automation" 2>/dev/null || true
pkill -f "chrome.*--remote-debugging" 2>/dev/null || true
```

## Step 4: Clean Screenshots & Temp Media (Current Conversation)

```bash
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
# Clean screenshots older than 10 minutes
find "$CONV_DIR" -name "*.png" -mmin +10 -delete 2>/dev/null || true
# Clean .tempmediaStorage (browser DOM snapshots)
rm -f "$CONV_DIR"/.tempmediaStorage/*.png 2>/dev/null || true
# Clean click_feedback images
rm -f "$CONV_DIR"/.system_generated/click_feedback/*.png 2>/dev/null || true
echo "✅ Screenshots and temp media cleaned"
```

## Step 4.5: Compress DOM → Summary → Then Delete

> **CRITICAL**: Do NOT delete DOM files blindly. First extract useful context, save as text summary, THEN delete raw files. This preserves memory for conversation continuity.

### 4.5a: Extract Context from DOM Files

Before deleting, the AI agent MUST:

1. **Scan DOM files** in the conversation directory
2. **Extract key information** from each DOM file:
   - Page title (`<title>`)
   - Current URL
   - Key visible text content (headings, form labels, error messages, data tables)
   - Page state (logged in? which page? any errors?)
   - Form values, selected options, visible data
3. **Write a compressed summary** to `browser_context.md`

```bash
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
CONTEXT_FILE="$CONV_DIR/browser_context.md"

echo "=== Compressing DOM Context ==="

# Count DOM files before cleanup
DOM_COUNT=$(find "$CONV_DIR" \( -name "*dom*" -o -name "*.mhtml" -o -name "*_snapshot*" -o -name "*page_source*" -o -name "*_content.html" \) 2>/dev/null | wc -l)
echo "DOM files found: $DOM_COUNT"

# Extract titles and URLs from HTML files (lightweight extraction)
echo "--- Extracting page context ---"
{
  echo "# Browser Context Summary"
  echo ""
  echo "Generated: $(date -Iseconds)"
  echo "DOM files compressed: $DOM_COUNT"
  echo ""
  echo "## Pages Visited"
  echo ""
  # Extract <title> from any HTML/MHTML files
  for f in $(find "$CONV_DIR" \( -name "*dom*" -o -name "*.mhtml" -o -name "*_content.html" \) 2>/dev/null | head -10); do
    TITLE=$(grep -oP '(?<=<title>)[^<]+' "$f" 2>/dev/null | head -1)
    URL=$(grep -oP '(?<=url=")[^"]+|(?<=href=")[^"]+' "$f" 2>/dev/null | head -1)
    [ -n "$TITLE" ] && echo "- **$TITLE** — \`$URL\`"
  done
  echo ""
  echo "## Key Context"
  echo ""
  echo "_AI agent: Fill in key findings from browser session below_"
  echo ""
} > "$CONTEXT_FILE" 2>/dev/null

echo "✅ Context saved to browser_context.md"
```

### 4.5b: AI Agent Enriches the Summary

After running the bash extraction, the AI agent MUST:

1. **Read** `browser_context.md`
2. **Append** key findings from the browser session:
   - What was accomplished
   - Current page state
   - Any data collected (table rows, form values, search results)
   - Next steps or pending actions
   - Error messages encountered
3. This file persists across the conversation and serves as **browser memory**

### 4.5c: Delete Raw DOM Files

**Only AFTER** the summary is written:

```bash
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
echo "=== Deleting raw DOM files ==="
# Delete DOM snapshot HTML files
find "$CONV_DIR" -name "*dom*" ! -name "browser_context.md" -delete 2>/dev/null || true
find "$CONV_DIR" -name "*.mhtml" -delete 2>/dev/null || true
# Delete DOM JSON dumps
find "$CONV_DIR" -name "*_dom.json" -delete 2>/dev/null || true
find "$CONV_DIR" -name "*_snapshot*" -delete 2>/dev/null || true
# Delete page source dumps
find "$CONV_DIR" -name "*page_source*" -delete 2>/dev/null || true
find "$CONV_DIR" -name "*_content.html" -delete 2>/dev/null || true
# Delete .system_generated DOM dirs
rm -rf "$CONV_DIR"/.system_generated/dom_snapshots/ 2>/dev/null || true
rm -rf "$CONV_DIR"/.system_generated/page_content/ 2>/dev/null || true
echo "✅ Raw DOM files deleted (summary preserved)"
```

## Step 5: Context Compression

After cleanup, state:
```
🗜️ Browser context compressed. Key findings:
- [finding 1]
- [finding 2]
- [finding 3]
📄 Full context saved to: browser_context.md
```

**For continuing conversations**: Read `browser_context.md` in the conversation directory to recover browser state from previous sessions.

Do NOT reference deleted artifacts (screenshots, recordings, raw DOM) in future responses.
Use `browser_context.md` as the ONLY source of browser memory.

## Step 6: Report

```bash
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
echo "=== Cleanup Report ==="
echo "Remaining files in conversation:"
find "$CONV_DIR" \( -name "*.webp" -o -name "*.png" \) 2>/dev/null | wc -l
echo "Disk usage after cleanup:"
du -sh ~/.gemini/antigravity 2>/dev/null || echo "N/A"
echo "Zombie chrome processes:"
pgrep -c -f "chromium|chrome" 2>/dev/null || echo "0"
```
