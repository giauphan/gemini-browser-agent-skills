# 🧹 Gemini Browser Agent Skills

> Drop-in skills, rules, and **dynamic context routing** to prevent **memory leaks**, **disk bloat (12GB+)**, **IDE crashes**, and **AI context amnesia** caused by Browser Subagent in AI IDEs.

## ⚠️ The Problem

When using AI agents for long-running tasks, these critical issues emerge:

| Issue | Root Cause | Impact |
|---|---|---|
| **RAM Leak** | Zombie Chromium processes & unreleased file descriptors | IDE freezes, OOM |
| **Disk Bloat (12GB+)** | Auto-recorded `.webp` videos & `.png` screenshots pile up | Disk full |
| **Context Amnesia** 🧠 | AI "forgets" rules as conversation grows longer | Rule violations, broken code |
| **Token Waste** 💸 | Loading ALL rules into every message bloats context window | Slow responses, high cost |
| **File Reading Skips** 📂 | AI reads 1-4 files when asked to read 10 | Incomplete analysis |

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

### One-Command Install (Agent Skills Standard)

```bash
npx skills add giauphan/gemini-browser-agent-skills
```

### Claude Code Plugin Marketplace

```bash
/plugin marketplace add giauphan/gemini-browser-agent-skills
/plugin install browser-preflight@gemini-browser-agent-skills
/plugin install browser-cleanup@gemini-browser-agent-skills
```

### Manual Setup (Any IDE)

```bash
# Clone this repo
git clone https://github.com/giauphan/gemini-browser-agent-skills.git

# Copy skills & rules to your project
cp -r gemini-browser-agent-skills/skills/ your-project/skills/
cp -r gemini-browser-agent-skills/rules/ your-project/rules/
cp gemini-browser-agent-skills/SKILLS_ROUTER.md your-project/SKILLS_ROUTER.md
```

### IDE-Specific Setup

Copy the rule file for your IDE to your project root:

| IDE / Tool | Rule File | Auto-Loaded? |
|---|---|---|
| **Cursor** | `.cursorrules` + `.cursor/rules/*.mdc` | ✅ Yes |
| **Windsurf** | `.windsurfrules` | ✅ Yes |
| **Cline / Roo Code** | `.clinerules` | ✅ Yes |
| **Trae** | `.traerules` | ✅ Yes |
| **GitHub Copilot** | `.github/copilot-instructions.md` | ✅ Yes |
| **Claude Code / CLI** | `CLAUDE.md` | ✅ Yes |
| **Gemini CLI** | `GEMINI.md` | ✅ Yes |
| **Gemini (Antigravity)** | `GEMINI.md` + `rules/context-router.md` | ✅ Yes |
| **OpenAI Codex** | `CODEX.md` | ✅ Yes |
| **Any AGENTS.md tool** | `AGENTS.md` (universal) | ✅ Yes |

```bash
# Example: Cursor IDE
cp gemini-browser-agent-skills/.cursorrules your-project/
cp -r gemini-browser-agent-skills/.cursor/ your-project/.cursor/

# Example: Claude Code / CLI
cp gemini-browser-agent-skills/CLAUDE.md your-project/

# Example: Gemini CLI / Antigravity
cp gemini-browser-agent-skills/GEMINI.md your-project/

# Example: OpenAI Codex
cp gemini-browser-agent-skills/CODEX.md your-project/

# Example: GitHub Copilot
cp -r gemini-browser-agent-skills/.github/ your-project/.github/
```

### Directory Structure

```
your-project/
├── AGENTS.md                       # Universal (30+ tools auto-detect)
├── CLAUDE.md                       # Claude Code / CLI specific
├── GEMINI.md                       # Gemini CLI / Antigravity specific
├── CODEX.md                        # OpenAI Codex specific
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
│   ├── rule-using-browser.md       # Browser session rules (on-demand)
│   ├── context-router.md           # Meta-rule: dynamic routing protocol
│   └── self-check.md               # Self-verification before coding
├── .claude-plugin/
│   └── marketplace.json            # Claude Code plugin manifest (npx skills add)
├── skills/
│   ├── browser-preflight/
│   │   └── SKILL.md                # Pre-flight: RAM, disk, zombie check
│   ├── browser-cleanup/
│   │   └── SKILL.md                # Post-session: delete, kill, clean
│   └── browser-heavy-cleanup/
│       └── SKILL.md                # Nuclear: purge everything
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
| Before launching Browser         | skills/browser-preflight/SKILL.md       |
| After Browser returns            | skills/browser-cleanup/SKILL.md         |
| Disk > 10GB or "clean browser"   | skills/browser-heavy-cleanup/SKILL.md   |
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
AI: [Checks router] → Match! → read_file("skills/browser-preflight/SKILL.md")
AI: [Runs pre-flight] → RAM OK, Disk OK → Launches browser
AI: [Browser returns] → read_file("skills/browser-cleanup/SKILL.md")
AI: [Runs cleanup] → Summarize → Delete .webp → Kill zombies
AI: States "🗜️ Browser context compressed. Key findings: [bullets]"
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

The `rules/self-check.md` forces AI to prove it remembers rules and reads all files:

```
📋 Active Rules for This Task:
1. Milestone limit — Max 10 browser steps
2. Cleanup after session — Delete .webp, kill zombies
3. Pre-flight check — Verify RAM > 2GB

📂 File Reading: Read 10/10 requested files. Missing: none
```

This "Chain-of-Thought Anchoring" technique dramatically reduces rule violations and file-skipping in long conversations.

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
- Compress context: `🗜️ Browser context compressed`

### 🔥 `browser-heavy-cleanup` — Nuclear Cleanup
- `pkill -9` ALL Chrome processes
- Delete ALL recordings + screenshots
- Purge Playwright caches
- Full resource report

## 🔗 Related Projects & Resources

### Rule Collections (Multi-IDE)
| Repo | Description |
|---|---|
| [Lay4U/awesome-ai-rules](https://github.com/Lay4U/awesome-ai-rules) | Rules for Cursor, Claude, Copilot, Windsurf, Codex CLI & Gemini CLI |
| [PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) | 500+ community-curated `.cursorrules` files |
| [sanjeed5/awesome-cursor-rules-mdc](https://github.com/sanjeed5/awesome-cursor-rules-mdc) | Curated `.mdc` format rules for Cursor |
| [philipbankier/awesome-agent-skills](https://github.com/philipbankier/awesome-agent-skills) | Directory of skills, tools, plugins across ALL platforms |

### Memory & Context Management
| Repo | Description |
|---|---|
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | Standalone memory layer (vector + graph + key-value) |
| [letta-ai/letta](https://github.com/letta-ai/letta) | MemGPT — OS-like context management (RAM/disk paging) |
| [getzep/zep](https://github.com/getzep/zep) | Temporal knowledge graphs for long-running agents |
| [ScaleLabs-Dev/CCFlow](https://github.com/ScaleLabs-Dev/CCFlow) | Memory bank + TDD workflow for Claude Code |

### Skills & Standards
| Repo | Description |
|---|---|
| [anthropics/skills](https://github.com/anthropics/skills) | Official Agent Skills spec (SKILL.md) |
| [agentskills.io](https://agentskills.io) | Cross-platform compatibility spec |
| [sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) | 900+ installable skills for Antigravity |
| [tiandee/awesome-skills-hub](https://github.com/tiandee/awesome-skills-hub) | Package manager for AI IDE skills & rules |

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
- Other AI IDEs (Augment, Aider, Kiro, etc.)
- Windows/macOS specific cleanup paths
- New skill categories (database, API, deployment)
- Better error hinting patterns
- Memory bank integrations

## 📄 License

MIT — Use freely, share widely.
