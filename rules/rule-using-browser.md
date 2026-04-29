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

1. **Compress recordings** — Find all `.webp` video files in the artifacts directory and compress/archive them so context is preserved but disk space is freed:
   ```bash
   # Find and compress browser recordings
   find <artifacts_dir> -name "*.webp" -newer /tmp/.last_browser_cleanup 2>/dev/null | \
     xargs -r -I{} sh -c 'gzip -f "{}" && echo "Compressed: {}"'
   touch /tmp/.last_browser_cleanup
   ```

2. **Kill orphan Chromium processes** — Prevent zombie processes:
   ```bash
   pkill -f "chromium.*--headless" 2>/dev/null || true
   pkill -f "chrome.*--automation" 2>/dev/null || true
   ```

3. **Clean screenshot artifacts** — Remove PNG screenshots that are no longer needed:
   ```bash
   find <artifacts_dir> -name "*.png" -mmin +30 -delete 2>/dev/null || true
   ```

> **Order matters**: Compress FIRST (preserve context), then kill processes, then clean screenshots.

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

When heavy cleanup is needed, run these commands:

```bash
# 1. Kill all Chromium/Chrome zombie processes
pkill -9 -f "chromium" 2>/dev/null || true
pkill -9 -f "chrome.*remote-debugging" 2>/dev/null || true

# 2. Compress all .webp recordings in artifacts
find ~/.gemini/antigravity -name "*.webp" -exec gzip -f {} \; 2>/dev/null

# 3. Remove old screenshots (older than 1 hour)
find ~/.gemini/antigravity -name "*.png" -mmin +60 -delete 2>/dev/null

# 4. Clear Playwright/Chrome cache
rm -rf ~/.cache/ms-playwright/chromium-*/Cache 2>/dev/null
rm -rf /tmp/.org.chromium.Chromium.* 2>/dev/null

# 5. Report freed space
echo "Cleanup complete. Current disk usage:"
du -sh ~/.gemini/antigravity 2>/dev/null || echo "N/A"
```

---

## 📋 Summary Checklist (Copy-Paste Mental Model)

```
Before browser:  ✅ Check RAM > 2GB, Disk > 5GB
During browser:  ✅ Max 10 steps per milestone
After browser:   ✅ Compress .webp → Kill zombies → Clean .png → Summarize
Long sessions:   ✅ Split into milestones, pause between each
```
