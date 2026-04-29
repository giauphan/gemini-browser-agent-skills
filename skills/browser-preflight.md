---
skill: browser-preflight
trigger: before_browser_session
description: Pre-flight resource check before launching Browser Subagent. Prevents crashes on low-resource machines.
---

# 🛫 Skill: Browser Pre-Flight Check

## When to Use
Execute this skill **before every Browser Subagent launch**.
If checks fail, warn the user and do NOT launch the browser.

## Steps

### Step 1: Check Available RAM
```bash
// turbo
echo "=== RAM Check ==="
free -h | grep Mem
AVAIL_MB=$(free -m | awk '/Mem:/ {print $7}')
echo "Available: ${AVAIL_MB}MB"
if [ "$AVAIL_MB" -lt 2048 ]; then
  echo "⛔ WARNING: Less than 2GB RAM available. Browser launch is RISKY."
  echo "ACTION: Clean up processes or warn user before proceeding."
else
  echo "✅ RAM OK (>2GB available)"
fi
```

### Step 2: Check Disk Space
```bash
// turbo
echo "=== Disk Check ==="
AVAIL_GB=$(df -BG . | awk 'NR==2 {print $4}' | tr -d 'G')
echo "Available: ${AVAIL_GB}GB"
if [ "$AVAIL_GB" -lt 5 ]; then
  echo "⛔ WARNING: Less than 5GB disk space. Browser artifacts will fill up fast."
  echo "ACTION: Run browser-cleanup skill first."
else
  echo "✅ Disk OK (>5GB available)"
fi
```

### Step 3: Check Existing Zombie Processes
```bash
// turbo
echo "=== Zombie Chrome Check ==="
CHROME_COUNT=$(pgrep -c -f "chromium|chrome" 2>/dev/null || echo "0")
echo "Existing chrome processes: $CHROME_COUNT"
if [ "$CHROME_COUNT" -gt 3 ]; then
  echo "⚠️ WARNING: $CHROME_COUNT chrome processes already running. Cleaning up first..."
  pkill -f "chromium.*--headless" 2>/dev/null || true
  pkill -f "chrome.*--automation" 2>/dev/null || true
  echo "✅ Cleaned up old chrome processes"
else
  echo "✅ No zombie chrome processes"
fi
```

### Decision
- If ANY check shows ⛔: **DO NOT** launch browser. Warn user.
- If all checks show ✅: Proceed with browser launch.
