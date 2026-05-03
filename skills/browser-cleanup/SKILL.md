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

## Step 5: Context Compression

After cleanup, state:
```
🗜️ Browser context compressed. Key findings:
- [finding 1]
- [finding 2]
- [finding 3]
```
Do NOT reference deleted artifacts in future responses.

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
