---
name: browser-anti-loop
description: "Root-cause fix for browser click loops. Combines 4 top community solutions: (1) AXTree over raw HTML, (2) Stagehand hybrid code+AI, (3) Vision+DOM dual verification, (4) Proactive blocker detection. This skill changes HOW the browser subagent sees and interacts with pages."
compatibility: "Works with any AI IDE Browser Subagent that uses Playwright internally."
license: MIT
allowed-tools: BrowserSubagent
metadata:
  triggers:
    - before_browser_action
    - browser_click_failed
    - long_horizon_task
  token-cost: ~300
  research-basis:
    - "Playwright MCP: Uses Accessibility Tree instead of raw HTML"
    - "Stagehand: Hybrid deterministic code + AI for dynamic parts"
    - "Browser-Use: Numbered bounding boxes on screenshots"
    - "GUI-R1: Inner monologue self-reflection before action"
  openclaw:
    homepage: https://github.com/giauphan/gemini-browser-agent-skills
---

# Browser Anti-Loop — Root Cause Fix

> **The Real Problem**: Browser subagent reads raw HTML → sees hidden/blocked elements →
> clicks them → nothing happens → retries same click → INFINITE LOOP.
>
> **The Real Fix**: Change HOW the browser subagent observes and verifies, not just detect loops after they happen.

## WHY Browser Clicks Fail and Loop

```
Root Cause Chain:
1. Page has popup/overlay/loading spinner covering a button
2. Browser subagent reads raw HTML/DOM → finds the button in HTML
3. HTML says button EXISTS → subagent thinks it's clickable
4. Subagent clicks → click absorbed by overlay → no state change  
5. Subagent retries same click (button still "exists" in HTML)
6. → INFINITE LOOP
```

**The button exists in HTML but is NOT visible/clickable on screen.**
HTML does NOT tell you about visibility — only the Accessibility Tree and Screenshots do.

---

## Solution 1: Visual State Verification (MOST EFFECTIVE)

> Community source: Browser-Use repo, Playwright MCP

The browser subagent in Antigravity/Gemini already takes screenshots internally.
The key is to **force it to USE the screenshot for verification**, not just the DOM.

### Include in EVERY browser_subagent Task prompt:

```
VISUAL VERIFICATION PROTOCOL:

After EVERY click/type/action, you MUST visually verify the result:
1. Look at the CURRENT SCREENSHOT (not the DOM/HTML)
2. Answer these questions by looking at the screenshot:
   - Did the page visually change? (new content, different layout, popup appeared/disappeared)
   - Is my target element ACTUALLY VISIBLE on screen? (not covered by anything)
   - Are there any popups, modals, overlays, cookie banners, or loading spinners visible?

3. If you see a BLOCKER (popup/modal/overlay/banner) on the screenshot:
   → STOP what you're doing
   → Dismiss the blocker FIRST (click X, click "Accept", press Escape)
   → THEN retry your original action

4. If the screenshot shows NO CHANGE after your action:
   → The action FAILED even if the HTML says the element exists
   → Do NOT retry the same action
   → Look at the screenshot to understand WHY it failed
   → Try a different approach

CRITICAL: Trust the SCREENSHOT over the DOM/HTML.
If the screenshot shows a button is covered, it IS covered — even if HTML says it's there.
```

---

## Solution 2: Pre-Action Visibility Check

> Community source: Stagehand framework, Playwright best practices

Before clicking, the subagent must verify the element is genuinely interactive.

### Include in Task prompt:

```
PRE-CLICK CHECKLIST (do this mentally BEFORE every click):

1. CAN I SEE the element on the current screenshot?
   - If NO → scroll to it first, or check if it's behind an overlay
   - If YES → proceed to step 2

2. Is the element BLOCKED by anything?
   Look for these on the screenshot:
   - Dark/semi-transparent overlay covering the page (modal backdrop)
   - Cookie consent banner at bottom/top
   - Chat widget or floating button overlapping
   - Loading spinner or skeleton screen
   - Toast notification sitting on top of a button
   
   If ANY blocker found → dismiss it FIRST

3. Is the element DISABLED?
   - Grayed out / faded appearance?
   - If YES → check what prerequisite is needed (fill form field, etc.)

4. ONLY after all checks pass → perform the click
```

---

## Solution 3: State Change Detection

> Community source: RLVR Verifiable Rewards, World Model

After every action, the subagent must prove the action had an effect.

### Include in Task prompt:

```
STATE CHANGE PROOF (required after every action):

After performing an action, you MUST report ONE of:
A) "STATE_CHANGED: [what changed]" — e.g., "new page loaded", "form submitted", "modal opened"
B) "NO_CHANGE: [what I expected vs what happened]" — e.g., "expected form to submit but page stayed the same"

Rules:
- If you report "NO_CHANGE" → you MUST NOT repeat the same action
- If you report "NO_CHANGE" 2 times in a row → STOP and return with error report
- If you report "STATE_CHANGED" → proceed to next step

Evidence of state change (need at least ONE):
- URL changed
- Page title changed  
- New text/content appeared on screen
- An element appeared or disappeared
- A form was submitted (success/error message shown)
- Navigation occurred (new page rendered)

If NONE of the above happened → the action had NO EFFECT → report "NO_CHANGE"
```

---

## Solution 4: Escape-First Recovery

> Community source: All top agent frameworks use this pattern

When stuck, the #1 fix is pressing Escape before anything else.

### Include in Task prompt:

```
STUCK RECOVERY — THE ESCAPE-FIRST RULE:

If your action has no effect (NO_CHANGE), do this IN ORDER:

Step 1: Press Escape key
  → This dismisses: modals, popups, dropdown menus, tooltips, overlays
  → Wait 1 second after pressing Escape
  → Check if the page changed → if YES, retry original action

Step 2: Scroll the page (if Escape didn't help)
  → The element might be below the viewport
  → Scroll down 300px and check if you can now see the target

Step 3: Click empty space on page body
  → This closes: floating menus, autocomplete dropdowns, context menus
  → Then retry original action

Step 4: Refresh the page (last resort)
  → If nothing else works, the page might be in a broken JS state
  → Refresh and retry from the beginning of current checkpoint

Step 5: STOP and report
  → If Steps 1-4 all failed, the element is genuinely broken
  → Return immediately with detailed error: what you tried, what you saw
```

---

## Combined Task Prompt Template

Use this COMPLETE template when writing browser_subagent tasks:

```
[Your actual task description here]

--- ANTI-LOOP PROTOCOL (MANDATORY) ---

VISUAL VERIFICATION: After every action, look at the screenshot to verify:
- Did the page actually change visually?
- Is my target visible and NOT blocked by popups/modals/overlays?
- Trust the screenshot over HTML/DOM

PRE-CLICK CHECK: Before every click:
- Can I see the element on screen? If NO → scroll or dismiss blockers
- Is anything covering it? If YES → dismiss blocker first

STATE CHANGE PROOF: After every action, report:
- "STATE_CHANGED: [what changed]" → proceed
- "NO_CHANGE" → do NOT retry same action

STUCK RECOVERY (if NO_CHANGE):
1. Press Escape → check → retry
2. Scroll page → check → retry
3. Click empty space → retry
4. Refresh page → retry from checkpoint start
5. STOP and report error

HARD LIMITS:
- NEVER click same element more than 2 times consecutively
- NEVER continue after 2 consecutive NO_CHANGE results
- ALWAYS report blockers you see on screen before trying to click through them
```
