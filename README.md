# 🧹 Gemini Browser Agent Skills

> Drop-in skills & rules to prevent **memory leaks**, **disk bloat (12GB+)**, and **IDE crashes** caused by Browser Subagent in Google Gemini AI IDE (Antigravity).

## ⚠️ The Problem

When using AI agents (especially with large-context models like Claude-4.6) for long-running tasks, the Browser Subagent causes serious resource leaks:

| Issue | Root Cause | Impact |
|---|---|---|
| **RAM Leak** | Zombie Chromium processes & unreleased file descriptors after DOM reloads | IDE freezes, system OOM |
| **Context Bloat** | Massive terminal I/O and logs overwhelm IDE's UI renderer | IDE crash mid-task |
| **Disk Bloat (12GB+)** | Auto-recorded `.webp` videos & `.png` screenshots pile up in artifacts dir | Disk full, workspace unusable |

## 💡 The Solution

This repo provides **3 executable skills** and **1 always-on rule** that teach your AI agent to:

1. ✅ **Check resources** before launching browser (RAM, disk, zombie processes)
2. ✅ **Self-limit** to max 10 browser steps per milestone
3. ✅ **Auto-cleanup** after every browser session (compress recordings, kill zombies, clean screenshots)
4. ✅ **Heavy-cleanup** on demand when things get critical

## 📦 Installation

Copy the files into your project's `.agents/` directory:

```bash
# Clone this repo
git clone https://github.com/giauphan/gemini-browser-agent-skills.git

# Copy skills to your project
cp -r gemini-browser-agent-skills/skills/ your-project/.agents/skills/
cp -r gemini-browser-agent-skills/rules/ your-project/.agents/rules/
```

Or just copy the files manually — no dependencies needed.

### Directory Structure

```
your-project/
└── .agents/
    ├── rules/
    │   └── rule-using-browser.md     # Always-on rule: milestone limits + cleanup protocol
    └── skills/
        ├── browser-preflight.md       # Pre-flight: check RAM, disk, zombies
        ├── browser-cleanup.md         # Post-session: compress, kill, clean
        └── browser-heavy-cleanup.md   # Nuclear option: purge everything
```

## 📋 Skills Overview

### 🛫 `browser-preflight` — Before Browser Launch

**Trigger:** `before_browser_session`

Checks before the AI opens a browser:
- Available RAM ≥ 2GB
- Available disk ≥ 5GB
- No zombie Chrome processes lurking

If checks fail → agent warns you and **does NOT** launch browser.

### 🧹 `browser-cleanup` — After Every Session

**Trigger:** `after_browser_session`

Executed immediately when browser returns:
1. Write summary of what happened (replaces video as memory)
2. Compress `.webp` recordings with gzip
3. Kill zombie Chromium processes
4. Delete old `.png` screenshots (>30 min)
5. Report disk usage + remaining processes

### 🔥 `browser-heavy-cleanup` — Nuclear Cleanup

**Trigger:** `manual` (say "clean browser")

For when things are already bad:
1. `pkill -9` ALL Chrome/Chromium processes
2. Compress ALL `.webp` recordings
3. Delete ALL old screenshots
4. Purge Playwright/Chrome caches
5. Full resource report

## 📏 Rule: Milestone-Based Execution

The `rule-using-browser.md` enforces:

- **Max 10 browser steps** per milestone
- **Mandatory pause** between milestones
- **Compress-first** cleanup order (preserve context, then free space)
- **Pre-flight checks** on resource-limited machines

```
Before browser:  ✅ Check RAM > 2GB, Disk > 5GB
During browser:  ✅ Max 10 steps per milestone  
After browser:   ✅ Compress .webp → Kill zombies → Clean .png → Summarize
Long sessions:   ✅ Split into milestones, pause between each
```

## 🤝 Contributing

PRs welcome! If you have tips for:
- Other AI IDEs (Cursor, Windsurf, etc.)
- Windows/macOS specific cleanup paths
- Better compression strategies

## 📄 License

MIT — Use freely, share widely.
