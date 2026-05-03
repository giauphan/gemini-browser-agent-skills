---
name: browser-preflight
description: Pre-flight resource check before launching Browser Subagent. Use when the agent is about to start a browser session, automate a web page, or run any browser_subagent task. Prevents crashes on low-resource machines by checking RAM, disk space, and zombie processes.
compatibility: "Requires Linux with `free`, `df`, `pgrep`, `pkill` commands. Works on any machine running Gemini CLI, Antigravity, Claude Code, Cursor, or similar AI IDE."
license: MIT
allowed-tools: Bash
metadata:
  triggers:
    - before_browser_session
    - browser_subagent_launch
  token-cost: ~150
  openclaw:
    requires:
      bins:
        - free
        - df
        - pgrep
    homepage: https://github.com/giauphan/gemini-browser-agent-skills
---

# Browser Pre-Flight Check

Run this skill **before every Browser Subagent launch**. If any check fails, warn the user and do NOT launch the browser.

## Step 1: Check Available RAM

```bash
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

## Step 2: Check Disk Space

```bash
echo "=== Disk Check ==="
AVAIL_GB=$(df -BG . | awk 'NR==2 {print $4}' | tr -d 'G')
echo "Available: ${AVAIL_GB}GB"
if [ "$AVAIL_GB" -lt 5 ]; then
  echo "⛔ WARNING: Less than 5GB disk space. Browser artifacts will fill up fast."
  echo "ACTION: Run browser-heavy-cleanup skill first."
else
  echo "✅ Disk OK (>5GB available)"
fi
```

## Step 3: Check Existing Zombie Processes

```bash
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

## Decision

- If ANY check shows ⛔: **DO NOT** launch browser. Warn user.
- If all checks show ✅: Proceed with browser launch.
