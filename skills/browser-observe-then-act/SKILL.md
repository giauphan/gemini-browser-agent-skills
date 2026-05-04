---
name: browser-observe-then-act
description: "Split browser work into 2 agents: Browser Subagent = hands (capture DOM/screenshot + execute clicks). Outer AI = brain (analyze DOM, decide what to click). This prevents loops because the 'brain' sits OUTSIDE the browser and controls each action precisely. Based on Stagehand observe()/act() and Browser-Use dual-phase architecture."
compatibility: "Works with Antigravity, Gemini CLI, Claude Code, Cursor."
license: MIT
allowed-tools: BrowserSubagent
metadata:
  triggers:
    - before_browser_action
    - browser_click_failed
    - any_browser_task
  token-cost: ~200
  research-basis:
    - "Stagehand: observe() + act() separated primitives"
    - "Browser-Use: observe → decide → act loop"
    - "Playwright MCP: Accessibility tree first, action second"
  openclaw:
    homepage: https://github.com/giauphan/gemini-browser-agent-skills
---

# Browser Observe-Then-Act (2-Agent Pattern)

> **Root Cause of Loops**: One browser_subagent call does EVERYTHING — reads DOM,
> analyzes it, decides what to click, clicks, fails, retries — all inside one call
> where we can't intervene. The loop happens inside the black box.
>
> **Fix**: Split the work between 2 agents:
> - **Browser Subagent** = hands only (get DOM + execute precise clicks)
> - **Outer AI** = brain (read DOM file, analyze, decide action)
>
> The "brain" sits OUTSIDE the browser. It controls each step. No loop possible.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ CURRENT (broken — loops happen inside the black box):          │
│                                                                 │
│   browser_subagent("Go to page, find button, click it")        │
│       → subagent reads DOM internally                           │
│       → subagent decides to click button                        │
│       → click fails (popup covers it)                           │
│       → subagent retries (WE CAN'T STOP IT) ← LOOP            │
│       → subagent retries again...                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ NEW (fixed — outer AI controls each step):                     │
│                                                                 │
│   Step 1: browser_subagent("Just OBSERVE — describe page")     │
│       → returns: "Page has login form. Popup is covering it."  │
│                          ↓                                      │
│   Step 2: Outer AI reads the report (or DOM file)              │
│       → analyzes: "Popup blocking → dismiss popup first"       │
│       → decides next action precisely                           │
│                          ↓                                      │
│   Step 3: browser_subagent("Click X button on popup to close") │
│       → returns: "Popup closed. Login form now visible."       │
│                          ↓                                      │
│   Step 4: Outer AI: "Good, now click login button"             │
│                          ↓                                      │
│   Step 5: browser_subagent("Click the Login button")           │
│       → returns: "Clicked. Dashboard loaded."                  │
│                                                                 │
│   ✅ No loop possible — outer AI decides between each step      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 1: OBSERVE — Browser Subagent as Data Collector

The browser subagent ONLY captures data, does NOT decide or click.

### Task Prompt for OBSERVE call:

```
OBSERVE ONLY — DO NOT click, type, or interact with anything.

Capture and report the current page state:

1. PAGE: URL, title, is page fully loaded?

2. VISIBLE INTERACTIVE ELEMENTS — List each one:
   Format: [NUMBER] TYPE "label/text" — STATUS
   Example:
   [1] BUTTON "Login" — visible, clickable
   [2] INPUT "Email" — visible, empty
   [3] BUTTON "Submit" — visible but BLOCKED by popup
   [4] LINK "Forgot password" — visible, clickable

3. BLOCKERS — Anything covering page content?
   - Popup/modal? Describe it. What's the close button?
   - Cookie banner? Where is it?
   - Loading spinner? Still loading?
   - Overlay/backdrop?

4. SCREENSHOT SUMMARY: Describe what you see in 2-3 sentences.

RETURN this info and STOP. Do not take any actions.
```

### What the outer AI does with this data:

The outer AI receives the element list and:
1. **Finds the target** element for current task step
2. **Checks if it's blocked** by any reported blockers
3. **Decides the action**:
   - If blocked → next call = dismiss blocker
   - If visible → next call = click target
   - If not found → next call = scroll down, then re-observe
4. **Writes precise instructions** for the ACT call

---

## Step 2: ACT — Browser Subagent as Precise Executor

The browser subagent does EXACTLY ONE action, no more.

### Task Prompt for ACT call:

```
PRECISE ACTION — Perform exactly ONE action, then report result.

ACTION: [Click the "Login" button]

After performing this action, report:
1. Did the page change? YES or NO
2. If YES: What changed? (new page, popup appeared, form submitted, etc.)
3. If NO: What do you see? Is the element still there? Is something blocking it?
4. Current URL and page title

Perform ONLY this one action. Do not do anything else.
```

---

## Step 3: VERIFY — Outer AI Checks Result

After the ACT call returns, the outer AI:

```
IF result says "page changed" → ✅ Step succeeded → move to next step
IF result says "no change"    → ❌ Step failed:
    → Run another OBSERVE call to understand current state
    → Analyze what went wrong
    → Decide alternative action (different element, dismiss blocker, etc.)
    → Do NOT retry the same action blindly

IF 2 consecutive failures on same step → STOP, report to user
```

---

## Complete Workflow Example

Task: "Login to the app with username admin and password 1234"

```
OBSERVE Call #1:
  → "Page shows login form. Cookie banner at bottom. 
     [1] INPUT 'Username' — visible
     [2] INPUT 'Password' — visible
     [3] BUTTON 'Login' — visible
     [4] BANNER 'Accept cookies' — bottom of page"

Outer AI: "Cookie banner might interfere. Dismiss it first."

ACT Call #1: "Click 'Accept' on the cookie banner"
  → "Cookie banner dismissed. Page unchanged otherwise."

ACT Call #2: "Type 'admin' into the Username input field"
  → "Text entered. Username field now shows 'admin'."

ACT Call #3: "Type '1234' into the Password input field"
  → "Text entered. Password field now shows dots."

ACT Call #4: "Click the Login button"
  → "Page changed! Redirected to /dashboard. Title: 'Dashboard'."

✅ Done — 4 precise actions, no loops, outer AI controlled each step.
```

---

## When to Use

| Situation | Pattern |
|---|---|
| Short click (1-2 steps, known page) | Can use single call (simple enough) |
| Unknown page or first visit | **OBSERVE first** — always |
| Previous action failed / looped | **OBSERVE first** — understand why |
| Page with popups/overlays | **OBSERVE first** — detect blockers |
| Multi-step form or checkout | **OBSERVE → ACT for each field** |
| Long-horizon task (10+ steps) | **Always OBSERVE → ACT** for every step |

---

## Integration with Other Skills

| Skill | How it integrates |
|---|---|
| **loop_guard.sh** | Log each ACT call result. Check between steps. |
| **anti-loop** | Include visual verification in ACT prompt |
| **self-reflection** | Outer AI uses `<THINK>` before deciding action |
| **checkpoint-manager** | Each checkpoint uses observe-then-act internally |
| **cleanup** | Run after final step, not between observe/act pairs |

---

## For the Outer AI (GEMINI.md / AGENTS.md rule):

```
OBSERVE-THEN-ACT RULE:

For browser tasks, NEVER write a single browser_subagent call that says:
  ❌ "Go to page, find the login form, fill in username/password, click login"

Instead, break it into separate calls:
  ✅ Call 1: "Observe the page. List all visible elements and blockers."
  ✅ Call 2: "Type 'admin' into the Username field."
  ✅ Call 3: "Type '1234' into the Password field."
  ✅ Call 4: "Click the Login button."

Each call = one action. You (outer AI) analyze between each call.
```
