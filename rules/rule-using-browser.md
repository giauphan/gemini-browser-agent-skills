---
trigger: always_on
---

# 🌐 Browser Subagent — Resource Management & Cleanup Rules

## ⚠️ Problem Statement

Browser Subagent runs an isolated Chromium instance via automation (Playwright-equivalent). During long-running sessions, it causes:

1. **Memory Leaks**: Zombie processes & socket leaks from unreleased file descriptors after DOM reloads
2. **Context Bloat**: Massive terminal I/O and logs overwhelm the IDE's UI renderer → crash
3. **Disk Bloat (12GB+)**: Auto-recorded screenshots & video artifacts (`.webp`) accumulate rapidly in the artifacts directory

---

## 📏 MANDATORY Rules for Browser Usage

### Rule 1: Milestone-Based Execution (Max 10 Steps)

When performing a long task involving Browser Subagent:

- **MUST** plan and split into milestones of **≤ 10 browser steps** each
- **MUST** close/return from Browser Subagent at the end of each milestone
- **MUST** summarize results before starting the next milestone
- **NEVER** run browser continuously for more than 10 steps without pausing

> This forces context window cleanup and prevents Chromium memory accumulation.

### Rule 2: Immediate Cleanup After Every Browser Session

**Right after** the Browser Subagent returns (every single time), you MUST:

> **IMPORTANT**: The `<conversation_dir>` is the **current conversation's** brain directory:
> `~/.gemini/antigravity/brain/<current-conversation-id>/`
> You can find the conversation ID from the `Conversation ID` in the user metadata.

1. **Delete recordings** — Remove all `.webp` video files in the **current conversation** directory. The text summary (Rule 3) replaces the video as context memory:
   ```bash
   # Delete browser recordings in CURRENT conversation
   find <conversation_dir> -name "*.webp" -delete 2>/dev/null
   # Also delete any previously gzipped recordings
   find <conversation_dir> -name "*.webp.gz" -delete 2>/dev/null
   ```

2. **Kill orphan Chromium processes** — Prevent zombie processes:
   ```bash
   pkill -f "chromium.*--headless" 2>/dev/null || true
   pkill -f "chrome.*--automation" 2>/dev/null || true
   ```

3. **Clean screenshot artifacts** — Remove PNGs including temp media and click feedback:
   ```bash
   # Clean main screenshots older than 10 minutes
   find <conversation_dir> -name "*.png" -mmin +10 -delete 2>/dev/null || true
   # Clean .tempmediaStorage (browser DOM snapshots)
   rm -rf <conversation_dir>/.tempmediaStorage/*.png 2>/dev/null || true
   # Clean click_feedback images
   rm -rf <conversation_dir>/.system_generated/click_feedback/*.png 2>/dev/null || true
   ```

> **Order matters**: Summarize FIRST (Rule 3), then delete recordings, kill processes, then clean screenshots.

### Rule 3: Context Preservation via Summary

Before deleting/compressing any browser artifacts:

- **MUST** write a brief text summary of what was observed/done in the browser session
- Store this summary in the conversation response (not in a file)
- This replaces the video recording as the "memory" of what happened

### Rule 4: Pre-Flight Resource Check

Before launching Browser Subagent on a machine with limited resources:

- Check available RAM: `free -h | grep Mem`
- If available RAM < 2GB, **DO NOT** launch browser — warn the user instead
- Check disk space: `df -h .` — if < 5GB free, clean up first

---

## 🧹 Cleanup Script Reference

When heavy cleanup is needed, run these commands.

**Per-conversation cleanup** (replace `CONV_ID` with actual conversation ID):
```bash
CONV_DIR=~/.gemini/antigravity/brain/CONV_ID

# 1. Kill all Chromium/Chrome zombie processes
pkill -9 -f "chromium" 2>/dev/null || true
pkill -9 -f "chrome.*remote-debugging" 2>/dev/null || true

# 2. Delete all .webp recordings and .webp.gz in current conversation
find "$CONV_DIR" -name "*.webp" -delete 2>/dev/null
find "$CONV_DIR" -name "*.webp.gz" -delete 2>/dev/null

# 3. Remove ALL screenshots (PNGs) in current conversation
find "$CONV_DIR" -name "*.png" -delete 2>/dev/null

# 4. Clean temp media and click feedback
rm -rf "$CONV_DIR"/.tempmediaStorage 2>/dev/null
rm -rf "$CONV_DIR"/.system_generated/click_feedback 2>/dev/null

# 5. Clear Playwright/Chrome cache
rm -rf ~/.cache/ms-playwright/chromium-*/Cache 2>/dev/null
rm -rf /tmp/.org.chromium.Chromium.* 2>/dev/null

# 6. Report freed space
echo "Cleanup complete. Current disk usage:"
du -sh ~/.gemini/antigravity 2>/dev/null || echo "N/A"
```

---

## 📋 Summary Checklist (Copy-Paste Mental Model)

```
Before browser:  ✅ Check RAM > 2GB, Disk > 5GB
During browser:  ✅ Max 10 steps per milestone
After browser:   ✅ Summarize → Delete .webp → Kill zombies → Clean .png + temp media
Long sessions:   ✅ Split into milestones, pause between each
Scope:           ✅ Always clean CURRENT conversation dir, not global
```
