---
name: browser-self-reflection
description: "GUI-R1 inspired Self-Reflection protocol. Forces AI to reason (THINK) before every browser action and verify (VERIFY) after each action. Prevents blind repetition and loop failures in long-horizon tasks (30+ steps). Based on GUI-R1's inner monologue architecture and RLVR verification principles."
compatibility: "Works with any AI IDE that supports Browser Subagent. No external dependencies — pure prompt engineering. Compatible with Gemini CLI, Antigravity, Claude Code, Cursor, Codex."
license: MIT
allowed-tools: BrowserSubagent
metadata:
  triggers:
    - before_browser_action
    - during_browser_session
    - long_horizon_task
  token-cost: ~250
  research-basis:
    - "GUI-R1: Generalist R1-Style Vision-Language Action Model (2025)"
    - "RLVR: Reinforcement Learning with Verifiable Rewards"
    - "InfiGUI-R1: Hierarchical reasoning for GUI Agents"
  openclaw:
    homepage: https://github.com/giauphan/gemini-browser-agent-skills
---

# Browser Self-Reflection (GUI-R1 Protocol)

> **Core Insight from GUI-R1**: AI agents fail at long tasks because they act *reactively* 
> (Observe → Act → Observe → Act). The fix is to add a *reasoning layer* between observation 
> and action: **Observe → THINK → Act → VERIFY → (next step or RECOVER)**.

## Problem: Why Long-Horizon Tasks Fail

When a browser test has 30+ steps, the AI fails because:
1. **No self-check**: AI clicks a button, doesn't verify if it worked, moves to next step
2. **Stale context**: By step 30, the AI has "forgotten" what step 1-20 accomplished
3. **Blind repetition**: When an action fails, AI retries the SAME action instead of adapting
4. **No error awareness**: A popup covers a button → AI doesn't "see" the popup, keeps clicking

## When to Use

| Situation | Action |
|---|---|
| Browser task with **> 10 steps** | Include Self-Reflection in EVERY task prompt |
| Previous browser session **failed mid-way** | Include Self-Reflection + Loop Breaker |
| Testing a **new/updated feature** | Include Self-Reflection for every action |
| AI is **repeating the same action** | STOP → load this skill → apply RECOVER protocol |

---

## The Self-Reflection Protocol

### Include in EVERY Browser Subagent Task Prompt:

```
SELF-REFLECTION PROTOCOL (MANDATORY for every action):

Before EVERY action, you MUST complete a <THINK> block:
<THINK>
- Current page state: [What do I see right now?]
- Goal of next action: [What am I trying to achieve?]
- Expected result: [What should the page look like AFTER my action?]
- Potential blockers: [Popups? Loading? Disabled buttons? Overlays?]
- Chosen action: [Exact action I will take]
</THINK>

After EVERY action, you MUST complete a <VERIFY> block:
<VERIFY>
- Action taken: [What I just did]
- Expected result: [What I expected to see]
- Actual result: [What actually happened]
- Success: [YES / NO / PARTIAL]
- If NO: What went wrong? [Analysis of failure]
</VERIFY>

CRITICAL RULES:
1. NEVER skip the <THINK> block — even for "obvious" actions
2. If <VERIFY> shows "Success: NO" — do NOT retry the same action
3. If <VERIFY> shows "Success: NO" — analyze WHY and try a DIFFERENT approach
4. After 2 consecutive "Success: NO" — STOP and report the issue, do NOT continue
```

---

## Recovery Protocol (When Action Fails)

When `<VERIFY>` shows `Success: NO`, the AI MUST follow this decision tree:

```
<RECOVER>
Failed action: [what failed]
Failure reason: [why it failed — be specific]

Diagnosis checklist:
□ Is there a popup/modal/overlay blocking the target element?
□ Is the target element disabled or grayed out?
□ Is the target element below the viewport (needs scrolling)?
□ Has the page finished loading? (check for spinners/loading indicators)
□ Am I on the correct page? (verify URL matches expectation)
□ Has the page layout changed unexpectedly?

Recovery action: [ONE of the following]
  A. Close popup/overlay first, then retry
  B. Scroll to reveal the target element, then retry
  C. Wait for page load to complete, then retry
  D. Navigate back and try alternative path
  E. STOP — escalate to user (element genuinely missing)
</RECOVER>
```

---

## Working Memory Summary (Every 5 Steps)

Every 5 browser actions, the AI MUST produce a **Working Memory Summary**:

```
<WORKING_MEMORY step="N">
Completed milestones:
- [x] Step 1-5: Logged in successfully, landed on dashboard
- [x] Step 6-10: Navigated to product page, added item to cart
- [ ] Step 11-15: (current) Attempting checkout flow

Current state:
- Page: [current page title and URL]
- Key UI state: [e.g., "cart has 2 items", "form is half-filled"]
- Errors encountered: [none / list]
- Actions that failed: [none / list with reasons]

Next objective:
- [What the next 5 steps should accomplish]
</WORKING_MEMORY>
```

> **Why this works**: GUI-R1 research shows that summarizing progress every N steps 
> prevents "context rot" — the phenomenon where AI loses track of what it has already 
> accomplished and starts making contradictory decisions.

---

## Integration with Other Skills

### With `browser-preflight` (Phase 1)
Add Self-Reflection requirement to the pre-flight checklist.

### With `rule-using-browser` (Phase 2)
Every milestone task prompt MUST include the Self-Reflection protocol block.

### With `browser-cleanup` (Phase 3)
Include Working Memory Summary in the post-session context compression.

---

## Quick Reference: Task Prompt Template with Self-Reflection

```
[Your actual task description here]

--- SELF-REFLECTION PROTOCOL ---
For EVERY browser action, you MUST:
1. BEFORE acting: Write a <THINK> block analyzing the current state, your goal, 
   expected result, and potential blockers
2. AFTER acting: Write a <VERIFY> block comparing expected vs actual results
3. If VERIFY shows failure: Write a <RECOVER> block with diagnosis and alternative approach
4. Every 5 steps: Write a <WORKING_MEMORY> summary of progress
5. After 2 consecutive failures on the same element: STOP and report — do NOT loop

--- TAB MANAGEMENT ---
[Include tab management rules from browser-tab-manager/SKILL.md]
```
