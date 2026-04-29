---
skill: browser-heavy-cleanup
trigger: manual
description: Aggressive cleanup when disk space is critical. Kills all browser processes, compresses all recordings, purges caches.
---

# 🔥 Skill: Browser Heavy Cleanup

## When to Use
- Disk usage > 10GB in artifacts directory
- User reports slow IDE or crash
- Before starting a long browser-heavy task
- Manual trigger: user says "clean browser" or similar

## Steps

### Step 1: Kill ALL Browser Processes
```bash
// turbo
echo "=== Killing ALL browser processes ==="
pkill -9 -f "chromium" 2>/dev/null || true
pkill -9 -f "chrome.*remote-debugging" 2>/dev/null || true
pkill -9 -f "chrome.*--automation" 2>/dev/null || true
pkill -9 -f "chrome.*--headless" 2>/dev/null || true
sleep 1
echo "Remaining chrome processes: $(pgrep -c -f 'chromium|chrome' 2>/dev/null || echo '0')"
```

### Step 2: Compress ALL Recordings
```bash
// turbo
echo "=== Compressing ALL .webp recordings ==="
BEFORE=$(du -sh ~/.gemini/antigravity 2>/dev/null | cut -f1)
find ~/.gemini/antigravity -name "*.webp" -exec gzip -f {} \; 2>/dev/null
echo "Before: $BEFORE"
echo "After:  $(du -sh ~/.gemini/antigravity 2>/dev/null | cut -f1)"
```

### Step 3: Remove Old Screenshots
```bash
// turbo
echo "=== Removing ALL old screenshots ==="
find ~/.gemini/antigravity -name "*.png" -mmin +60 -delete 2>/dev/null
echo "Done. Remaining PNGs: $(find ~/.gemini/antigravity -name '*.png' 2>/dev/null | wc -l)"
```

### Step 4: Clear Browser Caches
```bash
// turbo
echo "=== Clearing browser caches ==="
rm -rf ~/.cache/ms-playwright/chromium-*/Cache 2>/dev/null
rm -rf /tmp/.org.chromium.Chromium.* 2>/dev/null
rm -rf /tmp/puppeteer_dev_chrome_profile-* 2>/dev/null
echo "✅ Browser caches cleared"
```

### Step 5: Final Report
```bash
// turbo
echo ""
echo "========================================="
echo "  🔥 HEAVY CLEANUP COMPLETE"
echo "========================================="
echo "Artifacts dir:  $(du -sh ~/.gemini/antigravity 2>/dev/null | cut -f1 || echo 'N/A')"
echo "Chrome procs:   $(pgrep -c -f 'chromium|chrome' 2>/dev/null || echo '0')"
echo "Available RAM:  $(free -h | awk '/Mem:/ {print $7}')"
echo "Available Disk: $(df -h . | awk 'NR==2 {print $4}')"
echo "========================================="
```
