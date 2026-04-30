# 🧹 Gemini Browser Agent Skills

> Drop-in skills, rules, and **dynamic context routing** to prevent **memory leaks**, **disk bloat (12GB+)**, **IDE crashes**, and **AI context amnesia** caused by Browser Subagent in AI IDEs.

## ⚠️ The Problem

When using AI agents for long-running tasks, two critical issues emerge:

| Issue | Root Cause | Impact |
|---|---|---|
| **RAM Leak** | Zombie Chromium processes & unreleased file descriptors | IDE freezes, OOM |
| **Disk Bloat (12GB+)** | Auto-recorded `.webp` videos & `.png` screenshots pile up | Disk full |
| **Context Amnesia** 🧠 | AI "forgets" rules as conversation grows longer | Rule violations, broken code |
| **Token Waste** 💸 | Loading ALL rules into every message bloats context window | Slow responses, high cost |

## 💡 The Solution: Dynamic Context Routing

Instead of loading all rules upfront (800+ tokens), this repo uses a **3-layer strategy**:

### Layer 1: Lightweight Router (~150 tokens, always loaded)
The IDE rule file contains only a **routing table** — a tiny index that tells AI which skill file to load and when.

### Layer 2: On-Demand Skills (loaded only when needed)
Individual skill files are loaded via `read_file` only when the matching trigger condition fires.

### Layer 3: Error Hinting (0 tokens!)
AI hints embedded in `try/catch` error output — AI reads them from terminal logs without any context window cost.

```
Token Budget Comparison:
┌──────────────────────────┬─────────────┐
│ Strategy                 │ Token Cost  │
├──────────────────────────┼─────────────┤
│ ❌ Load ALL rules always │ ~800+ tokens│
│ ✅ Dynamic Routing       │ ~150 idle   │
│ ✅ + Error Hinting       │ ~0 extra    │
└──────────────────────────┴─────────────┘
```

## 📦 Installation

### Quick Setup (Any IDE)

```bash
# Clone this repo
git clone https://github.com/giauphan/gemini-browser-agent-skills.git

# Copy everything to your project
cp -r gemini-browser-agent-skills/skills/ your-project/.agents/skills/
cp -r gemini-browser-agent-skills/rules/ your-project/.agents/rules/
cp gemini-browser-agent-skills/SKILLS_ROUTER.md your-project/.agents/SKILLS_ROUTER.md
```

### IDE-Specific Setup

Copy the rule file for your IDE to your project root:

| IDE | Rule File | Auto-Loaded? |
|---|---|---|
| **Cursor** | `.cursorrules` + `.cursor/rules/*.mdc` | ✅ Yes |
| **Windsurf** | `.windsurfrules` | ✅ Yes |
| **Cline / Roo Code** | `.clinerules` | ✅ Yes |
| **Trae** | `.traerules` | ✅ Yes |
| **GitHub Copilot** | `.github/copilot-instructions.md` | ✅ Yes |
| **Gemini (Antigravity)** | `rules/context-router.md` + `SKILLS_ROUTER.md` | ✅ Yes |

```bash
# Example: Cursor IDE
cp gemini-browser-agent-skills/.cursorrules your-project/
cp -r gemini-browser-agent-skills/.cursor/ your-project/.cursor/

# Example: Windsurf
cp gemini-browser-agent-skills/.windsurfrules your-project/

# Example: GitHub Copilot
cp -r gemini-browser-agent-skills/.github/ your-project/.github/
```

### Directory Structure

```
your-project/
├── .cursorrules                    # Cursor IDE (lightweight router)
├── .windsurfrules                  # Windsurf IDE
├── .clinerules                     # Cline / Roo Code
├── .traerules                      # Trae IDE
├── .github/
│   └── copilot-instructions.md     # GitHub Copilot
├── .cursor/
│   └── rules/
│       ├── browser-agent.mdc       # Cursor MDC: browser context rules
│       └── browser-recovery.mdc    # Cursor MDC: cleanup on error
├── SKILLS_ROUTER.md                # 🧭 Routing table (~50 tokens)
├── rules/
│   ├── rule-using-browser.md       # Full browser rules (loaded on-demand)
│   ├── context-router.md           # Meta-rule: how to use dynamic routing
│   └── self-check.md               # Self-verification before coding
├── skills/
│   ├── browser-preflight.md        # Pre-flight: RAM, disk, zombie check
│   ├── browser-cleanup.md          # Post-session: delete, kill, clean
│   └── browser-heavy-cleanup.md    # Nuclear: purge everything
├── examples/
│   └── error_hinting.py            # Zero-token AI hint examples
└── tests/
    ├── test_browser_skills.py      # 3-layer test suite
    ├── benchmark_models.py         # Multi-model compliance benchmark
    └── ab_benchmark_sdk.py         # A/B testing SDK
```

## 🧭 How Dynamic Routing Works

### The Router (Always Loaded — ~50 tokens)

```markdown
| Trigger Condition               | Load This File                    |
|----------------------------------|-----------------------------------|
| Before launching Browser         | skills/browser-preflight.md       |
| After Browser returns            | skills/browser-cleanup.md         |
| Disk > 10GB or "clean browser"   | skills/browser-heavy-cleanup.md   |
| Any browser task                 | rules/rule-using-browser.md       |
```

### Flow: Normal Coding (0 extra tokens)
```
User: "Add a login form"
AI: [Checks router] → No browser trigger → Proceeds normally
Total extra cost: 0 tokens ✅
```

### Flow: Browser Task (loads only what's needed)
```
User: "Test the login page in browser"
AI: [Checks router] → Match! → read_file("skills/browser-preflight.md")
AI: [Runs pre-flight] → RAM OK, Disk OK → Launches browser
AI: [Browser returns] → read_file("skills/browser-cleanup.md")
AI: [Runs cleanup] → Done
Total extra cost: ~300 tokens (vs 800+ if all preloaded) ✅
```

### Flow: Error Recovery (0 extra tokens via hinting)
```
Browser crashes → Terminal shows error + [AI_SYSTEM_HINT]
AI: [Reads terminal] → Sees hint → Follows cleanup instructions
Total extra cost: 0 tokens ✅
```

## 🎯 Error Hinting (Zero-Token Technique)

Embed AI instructions directly in your error handlers:

```python
try:
    run_browser_automation()
except Exception as e:
    print(f"Browser Failed: {e}")

    # 🎯 AI reads this from terminal output — costs 0 context tokens!
    print("""
[AI_SYSTEM_HINT]: Browser error detected.
MANDATORY: Run cleanup before retry:
1. find ~/.gemini/antigravity/brain/ -name "*.webp" -delete
2. pkill -f "chromium" 2>/dev/null || true
""", file=sys.stderr)
    raise
```

See `examples/error_hinting.py` for Python, Bash, and Node.js patterns.

## ✅ Self-Check Protocol

The `rules/self-check.md` forces AI to prove it remembers rules before writing code:

```
📋 Active Rules for This Task:
1. Milestone limit — Max 10 browser steps
2. Cleanup after session — Delete .webp, kill zombies
3. Pre-flight check — Verify RAM > 2GB
```

This "Chain-of-Thought Anchoring" technique dramatically reduces rule violations in long conversations.

## 📋 Skills Overview

### 🛫 `browser-preflight` — Before Browser Launch
- Check RAM ≥ 2GB, Disk ≥ 5GB
- Kill zombie Chrome processes
- If checks fail → warn user, don't launch

### 🧹 `browser-cleanup` — After Every Session
- Summarize what happened
- Delete `.webp` recordings
- Kill zombie Chromium
- Clean old `.png` screenshots

### 🔥 `browser-heavy-cleanup` — Nuclear Cleanup
- `pkill -9` ALL Chrome processes
- Delete ALL recordings + screenshots
- Purge Playwright caches
- Full resource report

## 🧪 Testing

```bash
# Structural tests (no API key needed)
python tests/test_browser_skills.py --layer structural

# Full test with LLM-as-Judge
export GOOGLE_AI_API_KEY="your-key"
python tests/test_browser_skills.py

# Multi-model benchmark
python tests/benchmark_models.py
```

## 🤝 Contributing

PRs welcome! Especially for:
- Other AI IDEs (Augment, Aider, etc.)
- Windows/macOS specific cleanup paths
- New skill categories (database, API, deployment)
- Better error hinting patterns

## 📄 License

MIT — Use freely, share widely.
