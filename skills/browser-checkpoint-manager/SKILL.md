---
name: browser-checkpoint-manager
description: "Hierarchical Planning & Working Memory skill. Splits long-horizon tasks (30+ steps) into checkpoint-based sub-tasks with Manager-Worker architecture. Prevents catastrophic cascade failures by isolating each sub-task. Inspired by World Model's state prediction and RLVR checkpointing."
compatibility: "Works with any AI IDE Browser Subagent. No external deps."
license: MIT
allowed-tools: Bash, BrowserSubagent
metadata:
  triggers:
    - long_horizon_task
    - multi_step_test
    - task_over_10_steps
  token-cost: ~220
  openclaw:
    homepage: https://github.com/giauphan/gemini-browser-agent-skills
---

# Browser Checkpoint Manager (Hierarchical Planning)

> **Core Insight**: Never give AI 30+ steps at once. Use Manager-Worker architecture:
> Manager holds the full plan, Worker only executes 5-10 steps at a time.
> If Worker fails → Manager retries ONLY that sub-task, not the entire test.

## Problem: Cascade Failure

```
Step 1-25: All pass ✅
Step 26: Click fails (popup blocks button)
Step 27-50: ALL wrong ❌ (because step 26 corrupted the state)
```

**Result**: 100% test failure caused by ONE step. All work after step 26 is wasted.

## When to Use

| Situation | Action |
|---|---|
| Task has **> 10 browser steps** | MANDATORY: split into checkpoints |
| Testing a **complete user flow** | Split: Login → Navigate → Action → Verify |
| Previous test **failed mid-way** | Identify failed checkpoint, retry only that one |
| **Feature update test** | Rerun only affected checkpoints |

---

## Step 1: Define Checkpoints (Manager Role — AI Does This BEFORE Browser)

Before launching ANY browser session for a multi-step task, the AI MUST:

```
CHECKPOINT PLAN:
Task: [Full task description]
Total estimated steps: [N]

Checkpoints:
  CP-1: [Login & Auth] — Steps 1-5
    Entry state: Landing page loaded
    Exit state: Dashboard visible, user logged in
    Verification: Page title contains "Dashboard"
    
  CP-2: [Navigate to Feature] — Steps 6-10
    Entry state: Dashboard visible
    Exit state: Target feature page loaded
    Verification: URL contains "/feature-name"
    
  CP-3: [Execute Core Action] — Steps 11-18
    Entry state: Feature page loaded
    Exit state: Action completed, success message shown
    Verification: Success toast/message visible
    
  CP-4: [Verify Results] — Steps 19-22
    Entry state: Action completed
    Exit state: Results page shows expected data
    Verification: Data matches expected values
```

### Rules for Checkpoint Design:
1. Each checkpoint has **≤ 10 browser steps**
2. Each checkpoint has a clear **entry state** and **exit state**
3. Each checkpoint has a **verification condition** (verifiable reward)
4. Checkpoints are **independent** — if CP-3 fails, CP-1 and CP-2 are still valid

---

## Step 2: Execute Each Checkpoint (Worker Role)

For each checkpoint, launch a SEPARATE Browser Subagent session:

```
Browser Subagent Task for CP-N:
"You are executing Checkpoint N of a multi-step test.

CONTEXT (from previous checkpoints):
[Working memory summary from CP-1 through CP-(N-1)]

YOUR TASK (this checkpoint only):
[Checkpoint description — max 10 steps]

ENTRY STATE (what you should see):
[Expected page state when you start]

EXIT STATE (your goal):
[What the page should look like when you finish]

VERIFICATION:
[How to confirm this checkpoint passed]

Include Self-Reflection protocol for every action.
Include Loop Breaker (max 3 retries per action).

RETURN FORMAT:
1. Checkpoint result: PASS / FAIL
2. Exit state description (for next checkpoint)
3. Working memory summary
4. Any errors or warnings
"
```

---

## Step 3: Checkpoint State File

Track checkpoint progress in a file:

```bash
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
CP_FILE="$CONV_DIR/checkpoint_state.md"

cat > "$CP_FILE" << 'EOF'
# Checkpoint State

| CP | Name | Status | Attempts | Notes |
|----|------|--------|----------|-------|
| 1  | Login & Auth | ⏳ pending | 0 | - |
| 2  | Navigate to Feature | ⏳ pending | 0 | - |
| 3  | Execute Core Action | ⏳ pending | 0 | - |
| 4  | Verify Results | ⏳ pending | 0 | - |

## Working Memory
(Updated after each checkpoint)
EOF

echo "✅ Checkpoint state initialized: $CP_FILE"
```

### Update After Each Checkpoint:

```bash
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
CP_FILE="$CONV_DIR/checkpoint_state.md"

# AI updates this with actual results
# Example: Mark CP-1 as passed
sed -i 's/| 1  .*/| 1  | Login \& Auth | ✅ pass | 1 | Logged in as admin |/' "$CP_FILE"
echo "✅ Checkpoint 1 marked as PASS"
```

---

## Step 4: Failure Recovery (Manager Decision)

When a checkpoint FAILS, the Manager (outer AI) decides:

```
CHECKPOINT FAILURE PROTOCOL:

CP-N failed. Decision tree:
├── Attempt count < 3?
│   ├── YES → Retry CP-N (fresh browser session)
│   │   └── Include failure context: "Previous attempt failed because: [reason]"
│   └── NO → 3 attempts exhausted
│       ├── Is this checkpoint CRITICAL (blocks all later CPs)?
│       │   ├── YES → STOP entire test. Report failure.
│       │   └── NO → SKIP this CP, continue to CP-(N+1)
│       └── Report: "CP-N failed after 3 attempts: [reason]"
```

---

## Step 5: Final Report

After all checkpoints complete:

```bash
CONV_DIR=~/.gemini/antigravity/brain/<CONVERSATION_ID>
CP_FILE="$CONV_DIR/checkpoint_state.md"

echo "=== Test Execution Report ==="
echo ""
cat "$CP_FILE"
echo ""
echo "Checkpoints Passed: $(grep -c '✅' "$CP_FILE" 2>/dev/null || echo 0)"
echo "Checkpoints Failed: $(grep -c '❌' "$CP_FILE" 2>/dev/null || echo 0)"
echo "Checkpoints Skipped: $(grep -c '⏭️' "$CP_FILE" 2>/dev/null || echo 0)"
```

---

## Integration with Other Skills

| Skill | Integration |
|---|---|
| **Self-Reflection** | Include in EVERY checkpoint's task prompt |
| **Loop Breaker** | Active within each checkpoint (max 3 retries per action) |
| **Tab Manager** | Clean tabs between checkpoints |
| **Browser Cleanup** | Run after final checkpoint (not between CPs) |
| **Preflight** | Run once before first checkpoint |
