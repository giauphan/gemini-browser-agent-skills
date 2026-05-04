---
name: browser-loop-breaker
description: "RLVR-inspired Loop Detection & Breaking. Tracks action history, compares DOM states, forces AI strategy changes. Based on RLVR — if action doesn't produce verifiable state change, it's a failure."
compatibility: "Requires Bash. Works with any Browser Subagent."
license: MIT
allowed-tools: Bash, BrowserSubagent
metadata:
  triggers:
    - browser_action_repeated
    - dom_state_unchanged
    - long_horizon_task
  token-cost: ~280
  openclaw:
    homepage: https://github.com/giauphan/gemini-browser-agent-skills
---

# Browser Loop Breaker (RLVR Protocol)

> **RLVR Principle**: Don't trust AI's "feeling" that an action worked.
> Use **verifiable signals** — if DOM/page state didn't change, action FAILED. Binary only.

## Problem: The Deadly Loop

```
Step 28: Click "Submit" → nothing happens
Step 29: Click "Submit" → nothing happens
Step 30: Click "Submit" → nothing happens → LOOP FOREVER
```

**Root Cause**: AI has no mechanism to verify state change after action.

## When to Use

| Situation | Action |
|---|---|
| AI repeated same action **2+ times** | Activate immediately |
| Long-horizon task **(> 15 steps)** | Include from start |
| Previous test **failed at specific step** | Include + Self-Reflection |
| Testing **dynamic/JS-heavy pages** | Always include |

---

## Part 1: State Tracking (Code-Level)

### Initialize Tracker

```bash
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
TRACKER_FILE="$CONV_DIR/action_history.jsonl"
mkdir -p "$CONV_DIR"
echo '{"initialized": true, "ts": "'$(date -Iseconds)'"}' > "$TRACKER_FILE"
echo "✅ Loop Breaker initialized"
```

### Log Each Action (after each Browser Subagent return)

```bash
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
TRACKER_FILE="$CONV_DIR/action_history.jsonl"

# AI fills these based on session results
ACTION_TYPE="click"           # click | type | scroll | navigate
TARGET_ELEMENT="#btn-submit"  # selector or description
STEP_NUMBER="28"
ACTION_RESULT="no_change"     # state_changed | no_change | error

echo "{\"step\":$STEP_NUMBER,\"action\":\"$ACTION_TYPE\",\"target\":\"$TARGET_ELEMENT\",\"result\":\"$ACTION_RESULT\",\"ts\":\"$(date -Iseconds)\"}" >> "$TRACKER_FILE"
```

### Detect Loops

```bash
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
TRACKER_FILE="$CONV_DIR/action_history.jsonl"

echo "=== Loop Detection ==="
LAST_3=$(tail -3 "$TRACKER_FILE" 2>/dev/null)
REPEATED=$(echo "$LAST_3" | grep -oP '"action": "\K[^"]+' | sort | uniq -d)
REPEATED_TARGET=$(echo "$LAST_3" | grep -oP '"target": "\K[^"]+' | sort | uniq -d)

if [ -n "$REPEATED" ] && [ -n "$REPEATED_TARGET" ]; then
  echo "⛔ LOOP DETECTED! '$REPEATED' on '$REPEATED_TARGET' repeated 3+ times"
  echo "[AI_SYSTEM_HINT]: LOOP DETECTED — STOP IMMEDIATELY!"
  echo "MANDATORY: Do NOT retry this action. Instead:"
  echo "  1. Check if popup/modal/overlay is blocking target"
  echo "  2. Press Escape to dismiss overlays"
  echo "  3. Scroll to reveal element"
  echo "  4. Try different UI path to achieve same goal"
  echo "  5. If none work: STOP and report failure"
else
  echo "✅ No loop detected"
fi

NO_CHANGE_COUNT=$(echo "$LAST_3" | grep -c '"result": "no_change"' 2>/dev/null || echo "0")
if [ "$NO_CHANGE_COUNT" -ge 2 ]; then
  echo "⚠️ WARNING: $NO_CHANGE_COUNT/3 actions produced no state change"
  echo "[AI_SYSTEM_HINT]: Page may be stuck. Try alternative approach."
fi
```

---

## Part 2: State Verification (World Model)

> **World Model**: Before acting, predict what page SHOULD look like after.
> After acting, compare actual vs predicted. Mismatch → action failed.

### Include in Browser Subagent Task Prompt:

```
LOOP BREAKER — STATE VERIFICATION:

After EVERY action, verify page state changed:
1. BEFORE action: Note key elements (title, buttons, URL, form values)
2. AFTER action: Check if ANY changed (title, URL, new elements, messages)
3. Verdict:
   - Something changed → SUCCEEDED → next step
   - Nothing changed → FAILED → do NOT retry same action
4. On FAILURE:
   - Attempt #1: Press Escape, then retry
   - Attempt #2: Scroll page, then retry  
   - Attempt #3: STOP. Report "BLOCKED at step N"
5. NEVER attempt same action more than 3 times. After 3 → STOP entirely.
```

---

## Part 3: Blocker Detection

### Include in Task Prompt:

```
BLOCKER DETECTION (check BEFORE every click):

Scan for:
□ Modal dialogs / popups covering page
□ Cookie consent banners
□ Loading spinners / skeleton screens
□ Toast notifications overlapping buttons
□ Unclosed dropdown menus
□ Sticky headers/footers covering targets

If blocker detected → Dismiss FIRST → THEN proceed with action

Dismiss patterns: Escape key, click X, click "Accept", wait 2-3s, scroll
```

---

## Part 4: Combined Flow with Self-Reflection

```
1. <THINK>  — Plan action (Self-Reflection)
2. [Blocker check] — Dismiss if found
3. [Execute action]
4. <VERIFY> — Compare expected vs actual
5. [Log action] — Record in action_history.jsonl
6. [Loop check] — Detect repeated failures
7. <RECOVER> — If failed, diagnose and adapt
8. <WORKING_MEMORY> — Every 5 steps, summarize
```

## Part 5: Cleanup

```bash
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
# action_history.jsonl preserved for debugging (~1KB)
# cleaned by browser-heavy-cleanup
echo "✅ Loop Breaker tracking active"
```
