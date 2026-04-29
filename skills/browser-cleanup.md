---
skill: browser-cleanup
trigger: after_browser_session
description: Clean up browser artifacts, kill zombie processes, and free disk space after using Browser Subagent.
---

# 🧹 Skill: Browser Cleanup

## When to Use
Execute this skill **immediately after every Browser Subagent session returns**.
No exceptions. No delays. Clean first, think later.

## Steps

### Step 1: Summarize What Happened
Before touching any files, write a 2-3 sentence summary of what the browser session accomplished.
This summary replaces the video recording as context memory.

### Step 2: Compress Browser Recordings
```bash
// turbo
find ~/.gemini/antigravity -name "*.webp" -newer /tmp/.last_browser_cleanup 2>/dev/null | \
  xargs -r -I{} sh -c 'gzip -f "{}" && echo "Compressed: {}"'
touch /tmp/.last_browser_cleanup
```

### Step 3: Kill Zombie Chromium Processes
```bash
// turbo
pkill -f "chromium.*--headless" 2>/dev/null || true
pkill -f "chrome.*--automation" 2>/dev/null || true
pkill -f "chrome.*--remote-debugging" 2>/dev/null || true
```

### Step 4: Clean Old Screenshots
```bash
// turbo
find ~/.gemini/antigravity -name "*.png" -mmin +30 -delete 2>/dev/null || true
```

### Step 5: Report
```bash
// turbo
echo "=== Cleanup Report ==="
echo "Disk usage after cleanup:"
du -sh ~/.gemini/antigravity 2>/dev/null || echo "N/A"
echo "Zombie chrome processes:"
pgrep -c -f "chromium|chrome" 2>/dev/null || echo "0"
```
