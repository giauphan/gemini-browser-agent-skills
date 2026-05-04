---
name: browser-tab-manager
description: Manage browser tabs during sessions. Check if a URL is already open before navigating to avoid duplicates. Close unused/stale tabs to save RAM and prevent resource leaks. Use BEFORE navigating to a new URL and AFTER each milestone.
compatibility: "Works with any Browser Subagent that supports tab listing and switching. Requires AI IDE with browser_subagent tool (Gemini CLI, Antigravity, Claude Code, Cursor, etc.)."
license: MIT
allowed-tools: BrowserSubagent
metadata:
  triggers:
    - before_navigate_url
    - after_browser_milestone
    - tab_count_high
  token-cost: ~180
  openclaw:
    homepage: https://github.com/giauphan/gemini-browser-agent-skills
---

# Browser Tab Manager

> Prevent duplicate tabs and clean up unused ones. Load this skill BEFORE navigating to a URL and AFTER each browser milestone.

## Problem

Without tab management, browser sessions:
- Open **duplicate tabs** for the same URL, wasting RAM
- Accumulate **stale tabs** from previous milestones
- Eventually **crash** on low-resource machines (Colab, VPS)

## When to Use

| Situation | Action |
|---|---|
| About to navigate to a URL | Run **Step 1** (Check & Reuse) |
| After a browser milestone completes | Run **Step 2** (Clean Stale Tabs) |
| Tab count > 5 | Run **Step 2** immediately |
| Browser feels slow or unresponsive | Run **Step 2** + kill zombies |

---

## Step 1: Check If URL Already Open (Before Navigate)

**BEFORE calling `open_browser_url` or navigating**, the Browser Subagent MUST:

1. **List all open tabs** — check the current tab's URL and any other tabs
2. **Match the target URL** against all open tab URLs:
   - **Exact match**: Switch to that tab instead of opening a new one
   - **Same domain + path match** (ignore query params): Switch to that tab and reload if needed
   - **No match**: Proceed with opening a new tab
3. **Log the decision**:
   ```
   🔍 Tab Check: [TARGET_URL]
   → Found existing tab: [yes/no]
   → Action: [switched to tab N / opened new tab]
   → Total open tabs: [N]
   ```

### Instructions for Browser Subagent Task Prompt

When writing the `Task` for `browser_subagent`, include this instruction block:

```
TAB MANAGEMENT RULES:
- Before navigating to any URL, first check all open browser tabs
- If the target URL (or same domain+path) is already open, switch to that tab instead of opening a new one
- After completing the task, report how many tabs are currently open
- If there are more than 3 tabs open, close any tabs that are not needed for the current task
- Always prefer reusing existing tabs over opening new ones
```

---

## Step 2: Clean Stale Tabs (After Milestone)

**AFTER each browser milestone** (every ≤10 steps), the Browser Subagent MUST:

1. **Count open tabs** — if > 3, proceed to cleanup
2. **Identify the active tab** — the one currently needed
3. **Close all other tabs** except:
   - The active/current tab
   - Tabs explicitly bookmarked by the task (if any)
4. **Report cleanup**:
   ```
   🧹 Tab Cleanup:
   → Tabs before: [N]
   → Closed: [list of closed tab URLs]
   → Tabs after: [M]
   ```

### Instructions for Browser Subagent Task Prompt

When writing the `Task` for `browser_subagent`, include this at the END of the task:

```
BEFORE RETURNING:
- List all currently open browser tabs
- Close any tabs that are NOT needed for the next milestone
- Keep only the most relevant tab open (max 2 tabs)
- Report: "Tabs cleaned: [closed N tabs, kept M]"
```

---

## Step 3: Integration with Existing Skills

### With `browser-preflight` (BEFORE launch)
Add to preflight check: count existing browser tabs from previous sessions.

### With `rule-using-browser` (DURING session)
Every milestone task prompt MUST include tab management instructions from Steps 1 & 2.

### With `browser-cleanup` (AFTER session)
Tab cleanup happens automatically when browser processes are killed. No extra action needed.

---

## Quick Reference: Task Prompt Template

Use this template when building Browser Subagent task prompts:

```
[Your actual task description here]

--- TAB MANAGEMENT ---
1. Before navigating to any URL, check if it's already open in a tab. If yes, switch to it.
2. Do NOT open duplicate tabs for the same URL.
3. If more than 3 tabs are open, close the ones not needed for this task.
4. Before returning, close all tabs except the one most relevant for future work.
5. Report tab status: "Open tabs: [N], Reused: [yes/no], Cleaned: [N closed]"
```
