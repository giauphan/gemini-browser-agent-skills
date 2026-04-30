#!/usr/bin/env python3
"""
🔬 A/B Benchmark: Dynamic Routing vs Full Preload
===================================================
Compares 3 strategies for AI rule compliance:
  [A] Full Preload — All rules/skills loaded in system prompt (old way)
  [B] Dynamic Router — Only SKILLS_ROUTER.md index loaded (new way)
  [C] Baseline — No rules at all (control group)

Measures: compliance score, token usage, latency

Usage:
  export GOOGLE_AI_API_KEY="key1,key2,key3"
  python tests/ab_dynamic_routing.py
  python tests/ab_dynamic_routing.py --model gemini-2.0-flash --verbose
  python tests/ab_dynamic_routing.py --model gemma-4-31b-it
  python tests/ab_dynamic_routing.py --slow          # Free tier (60s between calls)
  python tests/ab_dynamic_routing.py --quick          # Only 3 core scenarios

Requirements:
  pip install google-genai
"""

import json
import os
import re
import sys
import time
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# ─── Config ──────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"
RULES_DIR = PROJECT_ROOT / "rules"
ROUTER_FILE = PROJECT_ROOT / "SKILLS_ROUTER.md"

SKILL_FILES = ["browser-preflight.md", "browser-cleanup.md", "browser-heavy-cleanup.md"]
RULE_FILES = ["rule-using-browser.md", "context-router.md", "self-check.md"]

API_KEYS = [k.strip() for k in os.environ.get("GOOGLE_AI_API_KEY", "").split(",") if k.strip()]

# ─── Scenarios ───────────────────────────────────────────────
# Each scenario has:
#   - A user prompt
#   - Criteria for the judge
#   - Which skill file the dynamic router SHOULD trigger
#   - "Irrelevant" scenarios (no browser) test false-positive routing

SCENARIOS = [
    {
        "id": "preflight",
        "name": "Pre-flight check before browser",
        "type": "browser",  # Should trigger routing
        "expected_skill": "skills/browser-preflight.md",
        "prompt": "User asks: Open a browser to check https://example.com. What do you do first?",
        "criteria": [
            "MUST check RAM (free -h or similar)",
            "MUST check disk space (df -h or similar)",
            "MUST NOT open browser without checking resources",
        ],
    },
    {
        "id": "cleanup",
        "name": "Post-session cleanup",
        "type": "browser",
        "expected_skill": "skills/browser-cleanup.md",
        "prompt": "The browser subagent just finished checking a website and returned. What do you do immediately after?",
        "criteria": [
            "MUST summarize what happened in the session",
            "MUST delete .webp recordings",
            "MUST kill zombie chromium/chrome processes (pkill)",
            "MUST clean old .png screenshots",
        ],
    },
    {
        "id": "milestone",
        "name": "Milestone-based execution",
        "type": "browser",
        "expected_skill": "rules/rule-using-browser.md",
        "prompt": "User asks: Test 25 different web pages in the browser for me. How do you plan this?",
        "criteria": [
            "MUST split into milestones of max 10 steps each",
            "MUST plan to close browser between milestones",
            "MUST NOT try all 25 in one continuous session",
        ],
    },
    {
        "id": "low_ram",
        "name": "Low RAM safety guard",
        "type": "browser",
        "expected_skill": "skills/browser-preflight.md",
        "prompt": "You checked: only 1.2GB RAM available. User still wants to open browser. What do you do?",
        "criteria": [
            "MUST warn that 1.2GB is below 2GB minimum",
            "MUST refuse to launch browser",
            "Should suggest freeing memory or alternative",
        ],
    },
    {
        "id": "heavy_cleanup",
        "name": "Heavy cleanup trigger",
        "type": "browser",
        "expected_skill": "skills/browser-heavy-cleanup.md",
        "prompt": "User says 'clean browser'. The artifacts directory ~/.gemini/antigravity is 15GB. What do you do?",
        "criteria": [
            "MUST kill ALL browser processes (pkill -9)",
            "MUST delete .webp recordings",
            "MUST delete old screenshots",
            "MUST clear browser caches",
            "MUST NOT delete entire artifacts directory",
        ],
    },
    # ─── Non-browser scenarios (should NOT trigger routing) ───
    {
        "id": "login_form",
        "name": "Non-browser: Add login form",
        "type": "non-browser",
        "expected_skill": None,
        "prompt": "Add a login form with email and password fields to the app. Use React.",
        "criteria": [
            "MUST generate code for a login form",
            "MUST include email and password fields",
            "MUST NOT mention browser cleanup or pre-flight checks",
            "MUST NOT mention .webp or pkill",
        ],
    },
    {
        "id": "database_query",
        "name": "Non-browser: Database query",
        "type": "non-browser",
        "expected_skill": None,
        "prompt": "Write a SQL query to find all users who signed up in the last 30 days.",
        "criteria": [
            "MUST generate a valid SQL query",
            "MUST filter by date (last 30 days)",
            "MUST NOT mention browser cleanup or browser subagent",
            "MUST NOT mention .webp, pkill, or pre-flight",
        ],
    },
]


# ─── Data Classes ────────────────────────────────────────────

@dataclass
class StrategyResult:
    scenario_id: str
    scenario_name: str
    strategy: str  # "full_preload" | "dynamic_router" | "baseline"
    score: float = 0.0
    criteria_met: List[str] = field(default_factory=list)
    criteria_missed: List[str] = field(default_factory=list)
    reasoning: str = ""
    token_estimate: int = 0  # Estimated input tokens
    latency_ms: int = 0
    error: str = ""


@dataclass
class ABReport:
    model: str
    results: List[StrategyResult] = field(default_factory=list)

    def avg_score(self, strategy: str, scenario_type: str = "all") -> float:
        filtered = [
            r for r in self.results
            if r.strategy == strategy and not r.error
        ]
        if scenario_type != "all":
            scenario_ids = [s["id"] for s in SCENARIOS if s["type"] == scenario_type]
            filtered = [r for r in filtered if r.scenario_id in scenario_ids]
        return sum(r.score for r in filtered) / len(filtered) if filtered else 0.0

    def avg_tokens(self, strategy: str) -> float:
        filtered = [r for r in self.results if r.strategy == strategy and not r.error]
        return sum(r.token_estimate for r in filtered) / len(filtered) if filtered else 0.0

    def avg_latency(self, strategy: str) -> float:
        filtered = [r for r in self.results if r.strategy == strategy and not r.error]
        return sum(r.latency_ms for r in filtered) / len(filtered) if filtered else 0.0


# ─── System Prompts ──────────────────────────────────────────

def load_full_preload() -> str:
    """Strategy A: Load ALL rules + skills into system prompt."""
    texts = []
    for f in RULE_FILES:
        p = RULES_DIR / f
        if p.is_file():
            texts.append(p.read_text())
    for f in SKILL_FILES:
        p = SKILLS_DIR / f
        if p.is_file():
            texts.append(p.read_text())
    return "\n\n---\n\n".join(texts)


def load_dynamic_router() -> str:
    """Strategy B: Load ONLY the SKILLS_ROUTER.md index."""
    if ROUTER_FILE.is_file():
        return ROUTER_FILE.read_text()
    return ""


def build_system_prompt(strategy: str) -> str:
    """Build the system prompt for each strategy."""
    base = "You are an AI coding assistant in Google Gemini IDE (Antigravity)."

    if strategy == "full_preload":
        rules = load_full_preload()
        return f"""{base}

You MUST follow ALL of these rules and skills strictly:

{rules}

Follow every rule. Show exact bash commands when applicable."""

    elif strategy == "dynamic_router":
        router = load_dynamic_router()
        return f"""{base}

You have a skills routing system. Here is your routing table:

{router}

IMPORTANT: You carry ONLY this routing table. When a task matches a trigger condition,
state which skill file you would load and follow its instructions.
For non-matching tasks, proceed normally without loading any extra files.
When responding, if a skill matches, prefix with: 📋 Loaded: [filename]"""

    elif strategy == "baseline":
        return f"{base} Help the user with their coding task."

    return base


def estimate_tokens(text: str) -> int:
    """Rough token estimate (1 token ≈ 4 chars for English)."""
    return len(text) // 4


# ─── Benchmark Engine ────────────────────────────────────────

class DynamicRoutingBenchmark:
    def __init__(self, api_keys: List[str], model: str, judge_model: str, slow: bool = False):
        self.api_keys = api_keys
        self.model = model
        self.judge_model = judge_model
        self._key_idx = 0
        self.call_delay = 60 if slow else 5  # seconds between API calls

    def _rotate_key(self):
        self._key_idx = (self._key_idx + 1) % len(self.api_keys)

    def _call(self, model: str, system: str, prompt: str, retries: int = 10) -> tuple:
        """Returns (response_text, latency_ms, error)."""
        from google import genai
        from google.genai import types

        # Gemma models don't support system_instruction — embed in contents
        is_gemma = "gemma" in model.lower()

        for attempt in range(retries):
            try:
                client = genai.Client(api_key=self.api_keys[self._key_idx])
                start = time.time()

                if is_gemma and system:
                    # Embed system prompt into user content for Gemma
                    combined = f"[SYSTEM INSTRUCTIONS]\n{system}\n\n[USER REQUEST]\n{prompt}"
                    config = types.GenerateContentConfig(temperature=0.3)
                    response = client.models.generate_content(
                        model=model, contents=combined, config=config,
                    )
                else:
                    config = types.GenerateContentConfig(
                        system_instruction=system if system else None,
                        temperature=0.3,
                    )
                    response = client.models.generate_content(
                        model=model, contents=prompt, config=config,
                    )

                latency = int((time.time() - start) * 1000)
                return response.text.strip(), latency, ""
            except Exception as e:
                err = str(e).lower()
                if "429" in str(e) or "quota" in err or "resource" in err:
                    self._rotate_key()
                    # Parse retryDelay from API response if available
                    retry_match = re.search(r'retry.*?(\d+\.?\d*)s', str(e), re.IGNORECASE)
                    if retry_match:
                        backoff = int(float(retry_match.group(1))) + 5
                    else:
                        backoff = min(2 ** (attempt + 2), 65)
                    print(f"      ⏳ Rate limited, waiting {backoff}s (attempt {attempt+1}/{retries})...")
                    time.sleep(backoff)
                elif "503" in str(e) or "unavailable" in err:
                    backoff = min(2 ** (attempt + 1), 30)
                    print(f"      ⏳ Service unavailable, waiting {backoff}s...")
                    time.sleep(backoff)
                elif "400" in str(e) or "invalid_argument" in err:
                    return "", 0, f"400 INVALID_ARGUMENT (model may not support this config)"
                elif "not found" in err or "not supported" in err:
                    return "", 0, f"Model not available: {model}"
                else:
                    return "", 0, str(e)[:200]
        return "", 0, "SKIPPED: quota exhausted"

    def _judge(self, response: str, criteria: List[str]) -> Dict:
        """Use judge model to evaluate response against criteria."""
        criteria_text = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(criteria))
        judge_prompt = f"""Evaluate this AI assistant response against strict criteria.

## Criteria (each scores equally):
{criteria_text}

## Response to evaluate:
```
{response[:3000]}
```

For EACH criterion, determine if the response CLEARLY demonstrates it.
Score = (criteria met) / (total criteria) × 100

Reply with JSON ONLY, no markdown fences:
{{"score": 0-100, "criteria_met": ["..."], "criteria_missed": ["..."], "reasoning": "brief"}}"""

        text, _, error = self._call(self.judge_model, "You are a strict AI auditor. Reply JSON only.", judge_prompt)
        if error:
            return {"error": error, "score": 0, "criteria_met": [], "criteria_missed": []}
        try:
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            return json.loads(text)
        except Exception:
            return {"error": "JSON parse failed", "score": 0, "criteria_met": [], "criteria_missed": []}

    def run_scenario(self, scenario: Dict, strategy: str) -> StrategyResult:
        """Run one scenario with one strategy."""
        system = build_system_prompt(strategy)
        token_est = estimate_tokens(system + scenario["prompt"])

        response, latency, error = self._call(self.model, system, scenario["prompt"])

        if error:
            return StrategyResult(
                scenario_id=scenario["id"], scenario_name=scenario["name"],
                strategy=strategy, error=error, token_estimate=token_est,
            )

        time.sleep(self.call_delay)
        judgment = self._judge(response, scenario["criteria"])

        if judgment.get("error") and judgment.get("score", 0) == 0:
            return StrategyResult(
                scenario_id=scenario["id"], scenario_name=scenario["name"],
                strategy=strategy, error=judgment["error"], token_estimate=token_est,
            )

        return StrategyResult(
            scenario_id=scenario["id"],
            scenario_name=scenario["name"],
            strategy=strategy,
            score=judgment.get("score", 0),
            criteria_met=judgment.get("criteria_met", []),
            criteria_missed=judgment.get("criteria_missed", []),
            reasoning=judgment.get("reasoning", ""),
            token_estimate=token_est,
            latency_ms=latency,
        )

    def run_all(self, verbose: bool = False) -> ABReport:
        """Run all scenarios across all 3 strategies."""
        report = ABReport(model=self.model)
        strategies = ["full_preload", "dynamic_router", "baseline"]
        strategy_labels = {
            "full_preload": "🅰️  Full Preload",
            "dynamic_router": "🅱️  Dynamic Router",
            "baseline": "🅾️  Baseline (no rules)",
        }

        total = len(SCENARIOS) * len(strategies)
        current = 0

        for scenario in SCENARIOS:
            print(f"\n  ━━━ {scenario['name']} ({scenario['type']}) ━━━")

            for strategy in strategies:
                current += 1
                label = strategy_labels[strategy]
                print(f"    [{current}/{total}] {label}...", end=" ", flush=True)

                result = self.run_scenario(scenario, strategy)
                report.results.append(result)

                if result.error:
                    if "SKIPPED" in result.error:
                        print(f"⏭️  SKIPPED")
                    else:
                        print(f"⚠️  {result.error[:60]}")
                else:
                    icon = "✅" if result.score >= 70 else "⚠️" if result.score >= 40 else "❌"
                    print(f"{icon} {result.score:.0f}/100 ({result.latency_ms}ms, ~{result.token_estimate} tokens)")

                    if verbose and result.criteria_missed:
                        for m in result.criteria_missed[:2]:
                            print(f"       └─ missed: {m}")

                time.sleep(self.call_delay)

        return report


# ─── Report Printing ─────────────────────────────────────────

def print_report(report: ABReport):
    """Print comprehensive A/B comparison report."""
    print("\n" + "═" * 72)
    print("  🔬 A/B BENCHMARK: DYNAMIC ROUTING vs FULL PRELOAD vs BASELINE")
    print(f"  Model: {report.model}")
    print("═" * 72)

    # ─── Strategy comparison table ───
    strategies = ["full_preload", "dynamic_router", "baseline"]
    labels = {"full_preload": "Full Preload", "dynamic_router": "Dynamic Router", "baseline": "No Rules"}

    print(f"\n  {'Scenario':<30}", end="")
    for s in strategies:
        print(f" {labels[s]:>14}", end="")
    print()
    print("  " + "─" * 72)

    for scenario in SCENARIOS:
        name = scenario["name"][:30]
        type_icon = "🌐" if scenario["type"] == "browser" else "📝"
        print(f"  {type_icon} {name:<28}", end="")
        for strategy in strategies:
            r = next((x for x in report.results
                       if x.scenario_id == scenario["id"] and x.strategy == strategy), None)
            if r is None or r.error:
                print(f" {'SKIP':>14}", end="")
            else:
                icon = "✅" if r.score >= 70 else "⚠️" if r.score >= 40 else "❌"
                print(f" {icon}{r.score:>5.0f}/100   ", end="")
        print()

    # ─── Averages ───
    print("  " + "─" * 72)

    # Browser-only averages
    print(f"  {'🌐 Browser AVG':<30}", end="")
    for s in strategies:
        avg = report.avg_score(s, "browser")
        icon = "✅" if avg >= 70 else "⚠️" if avg >= 40 else "❌"
        print(f" {icon}{avg:>5.0f}/100   ", end="")
    print()

    # Non-browser averages
    print(f"  {'📝 Non-browser AVG':<30}", end="")
    for s in strategies:
        avg = report.avg_score(s, "non-browser")
        icon = "✅" if avg >= 70 else "⚠️" if avg >= 40 else "❌"
        print(f" {icon}{avg:>5.0f}/100   ", end="")
    print()

    # Overall averages
    print(f"  {'📊 OVERALL AVG':<30}", end="")
    for s in strategies:
        avg = report.avg_score(s, "all")
        icon = "✅" if avg >= 70 else "⚠️" if avg >= 40 else "❌"
        print(f" {icon}{avg:>5.0f}/100   ", end="")
    print()

    # ─── Token & Latency comparison ───
    print("\n  " + "─" * 72)
    print(f"  {'📏 AVG TOKENS (input)':<30}", end="")
    for s in strategies:
        avg = report.avg_tokens(s)
        print(f" {avg:>10.0f}    ", end="")
    print()

    print(f"  {'⏱️  AVG LATENCY':<30}", end="")
    for s in strategies:
        avg = report.avg_latency(s)
        print(f" {avg:>8.0f}ms    ", end="")
    print()

    # ─── Token savings calculation ───
    full_tokens = report.avg_tokens("full_preload")
    router_tokens = report.avg_tokens("dynamic_router")
    if full_tokens > 0:
        savings_pct = ((full_tokens - router_tokens) / full_tokens) * 100
        print(f"\n  💰 Token savings: {savings_pct:.0f}% ({full_tokens:.0f} → {router_tokens:.0f} tokens)")

    # ─── Compliance delta ───
    full_browser = report.avg_score("full_preload", "browser")
    router_browser = report.avg_score("dynamic_router", "browser")
    baseline_browser = report.avg_score("baseline", "browser")

    print("\n  " + "═" * 72)
    print("  📋 KEY FINDINGS")
    print("  " + "═" * 72)

    # Finding 1: Router vs Full Preload on browser tasks
    delta_ab = router_browser - full_browser
    if abs(delta_ab) < 5:
        print(f"  ✅ Dynamic Router ≈ Full Preload on browser tasks (Δ = {delta_ab:+.0f})")
        print(f"     → Same compliance, much fewer tokens!")
    elif delta_ab > 0:
        print(f"  🏆 Dynamic Router BEATS Full Preload on browser tasks (+{delta_ab:.0f}%)")
    else:
        print(f"  ⚠️  Dynamic Router slightly behind Full Preload ({delta_ab:.0f}%)")

    # Finding 2: Token savings
    if full_tokens > 0:
        print(f"  💰 Token reduction: {savings_pct:.0f}% ({full_tokens:.0f} → {router_tokens:.0f})")

    # Finding 3: Non-browser noise (false positives)
    full_nonbrowser = report.avg_score("full_preload", "non-browser")
    router_nonbrowser = report.avg_score("dynamic_router", "non-browser")
    if router_nonbrowser > full_nonbrowser:
        delta_noise = router_nonbrowser - full_nonbrowser
        print(f"  🎯 Dynamic Router avoids false positives better (+{delta_noise:.0f}% on non-browser)")
    elif router_nonbrowser == full_nonbrowser:
        print(f"  ➡️  Both strategies handle non-browser tasks equally")

    # Finding 4: vs Baseline
    delta_bc = router_browser - baseline_browser
    if delta_bc > 10:
        print(f"  📈 Rules improve browser compliance by +{delta_bc:.0f}% vs no rules")

    print("  " + "═" * 72)

    # ─── Verdict ───
    print()
    if abs(delta_ab) < 5 and savings_pct > 30:
        print("  ╔═══════════════════════════════════════════════════════════╗")
        print("  ║  🏆 VERDICT: Dynamic Router WINS                        ║")
        print(f"  ║  Same compliance, {savings_pct:.0f}% fewer tokens, less context bloat ║")
        print("  ╚═══════════════════════════════════════════════════════════╝")
    elif delta_ab > 5:
        print("  ╔═══════════════════════════════════════════════════════════╗")
        print("  ║  🏆 VERDICT: Dynamic Router is SUPERIOR                 ║")
        print(f"  ║  Better compliance AND {savings_pct:.0f}% fewer tokens              ║")
        print("  ╚═══════════════════════════════════════════════════════════╝")
    elif delta_ab < -10:
        print("  ╔═══════════════════════════════════════════════════════════╗")
        print("  ║  ⚠️  VERDICT: Full Preload still needed for this model   ║")
        print("  ║  Dynamic routing loses too much compliance               ║")
        print("  ╚═══════════════════════════════════════════════════════════╝")
    else:
        print("  ╔═══════════════════════════════════════════════════════════╗")
        print("  ║  ✅ VERDICT: Dynamic Router is viable                   ║")
        print(f"  ║  Small compliance trade-off ({delta_ab:+.0f}%), big token savings   ║")
        print("  ╚═══════════════════════════════════════════════════════════╝")
    print()


# ─── Main ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="A/B benchmark: Dynamic Routing vs Full Preload vs Baseline"
    )
    parser.add_argument("--model", default="gemini-2.0-flash", help="Model to test")
    parser.add_argument("--judge", default="gemini-2.0-flash", help="Judge model")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--slow", action="store_true",
                        help="Free tier mode: 60s delay between API calls")
    parser.add_argument("--quick", action="store_true",
                        help="Run only 3 core scenarios (preflight, cleanup, login_form)")
    args = parser.parse_args()

    if not API_KEYS:
        print("❌ Set GOOGLE_AI_API_KEY environment variable")
        print("   export GOOGLE_AI_API_KEY=\"key1,key2\"")
        sys.exit(1)

    # Filter scenarios if --quick mode
    global SCENARIOS
    if args.quick:
        SCENARIOS = [s for s in SCENARIOS if s["id"] in ("preflight", "cleanup", "login_form")]

    mode_label = "🐢 SLOW (free tier)" if args.slow else "🚀 NORMAL"
    print(f"\n🔬 A/B Benchmark: Dynamic Routing")
    print(f"   Model: {args.model}")
    print(f"   Judge: {args.judge}")
    print(f"   Mode: {mode_label}")
    print(f"   Scenarios: {len(SCENARIOS)} ({sum(1 for s in SCENARIOS if s['type'] == 'browser')} browser, {sum(1 for s in SCENARIOS if s['type'] == 'non-browser')} non-browser)")
    print(f"   Strategies: 3 (Full Preload, Dynamic Router, Baseline)")
    print(f"   Total API calls: {len(SCENARIOS) * 3 * 2} (generation + judging)")
    print(f"   API Keys: {len(API_KEYS)}")
    if args.slow:
        est_mins = (len(SCENARIOS) * 3 * 2 * 60) // 60
        print(f"   ⏱️  Estimated time: ~{est_mins} minutes (free tier pacing)")

    # Show token estimates before running
    full_sys = build_system_prompt("full_preload")
    router_sys = build_system_prompt("dynamic_router")
    baseline_sys = build_system_prompt("baseline")
    print(f"\n   📏 System prompt sizes:")
    print(f"      Full Preload:   ~{estimate_tokens(full_sys)} tokens")
    print(f"      Dynamic Router: ~{estimate_tokens(router_sys)} tokens")
    print(f"      Baseline:       ~{estimate_tokens(baseline_sys)} tokens")
    savings = ((estimate_tokens(full_sys) - estimate_tokens(router_sys)) / estimate_tokens(full_sys)) * 100
    print(f"      Expected savings: ~{savings:.0f}%")

    bench = DynamicRoutingBenchmark(API_KEYS, args.model, args.judge, slow=args.slow)
    report = bench.run_all(verbose=args.verbose)
    print_report(report)

    # Save results
    out = Path(__file__).parent / "ab_dynamic_routing_results.json"
    with open(out, "w") as f:
        json.dump({
            "model": report.model,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "results": [{
                "scenario": r.scenario_id, "name": r.scenario_name,
                "strategy": r.strategy, "score": r.score,
                "token_estimate": r.token_estimate, "latency_ms": r.latency_ms,
                "criteria_met": r.criteria_met, "criteria_missed": r.criteria_missed,
                "reasoning": r.reasoning, "error": r.error,
            } for r in report.results],
            "summary": {
                "full_preload_avg": report.avg_score("full_preload"),
                "dynamic_router_avg": report.avg_score("dynamic_router"),
                "baseline_avg": report.avg_score("baseline"),
                "full_preload_tokens": report.avg_tokens("full_preload"),
                "dynamic_router_tokens": report.avg_tokens("dynamic_router"),
                "token_savings_pct": savings,
            },
        }, f, indent=2)
    print(f"📁 Results saved to {out}")


if __name__ == "__main__":
    main()
