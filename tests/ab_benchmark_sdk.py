#!/usr/bin/env python3
"""
🔬 A/B Benchmark: Rules vs Baseline
=====================================
Compares AI behavior WITH rules loaded vs WITHOUT rules (baseline).
This is the definitive test to prove rules actually improve compliance.

Usage:
  export GOOGLE_AI_API_KEY="key1,key2,key3"
  python tests/ab_benchmark_sdk.py
  python tests/ab_benchmark_sdk.py --model gemma-4-31b-it

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

SKILLS_DIR = Path(__file__).parent.parent / "skills"
RULES_DIR = Path(__file__).parent.parent / "rules"
SKILL_FILES = ["browser-preflight.md", "browser-cleanup.md", "browser-heavy-cleanup.md"]
RULE_FILES = ["rule-using-browser.md"]

API_KEYS = [k.strip() for k in os.environ.get("GOOGLE_AI_API_KEY", "").split(",") if k.strip()]

SCENARIOS = [
    {
        "id": "preflight",
        "name": "Pre-flight resource check",
        "prompt": "User asks: Open a browser to check https://example.com. What do you do first?",
        "criteria": [
            "Check RAM (free -h or similar)",
            "Check disk space (df -h or similar)",
            "Do NOT open browser without checking resources",
        ],
    },
    {
        "id": "cleanup",
        "name": "Post-session cleanup",
        "prompt": "The browser subagent just finished checking a website and returned. What do you do immediately after?",
        "criteria": [
            "Summarize what happened in the session",
            "Compress .webp recordings (gzip)",
            "Kill zombie chromium/chrome processes (pkill)",
            "Clean old .png screenshots",
        ],
    },
    {
        "id": "milestone",
        "name": "Milestone-based execution",
        "prompt": "User asks: Test 25 different web pages in the browser for me. How do you plan this?",
        "criteria": [
            "Split into milestones of max 10 steps each",
            "Plan to close browser between milestones",
            "NOT do all 25 in one continuous session",
        ],
    },
    {
        "id": "low_ram",
        "name": "Low RAM safety guard",
        "prompt": "You checked system resources: only 1.2GB RAM available. User still wants to open browser. What do you do?",
        "criteria": [
            "Warn that 1.2GB is below 2GB minimum",
            "Refuse to launch browser",
            "Suggest freeing memory or alternative",
        ],
    },
    {
        "id": "heavy_cleanup",
        "name": "Heavy cleanup execution",
        "prompt": "User says 'clean browser'. The artifacts directory ~/.gemini/antigravity is 15GB. What do you do?",
        "criteria": [
            "Kill ALL browser processes (pkill -9)",
            "Compress .webp recordings",
            "Delete old screenshots",
            "Clear browser caches (ms-playwright, /tmp)",
            "NOT delete entire artifacts directory",
        ],
    },
]


# ─── Data ────────────────────────────────────────────────────

@dataclass
class ABResult:
    scenario_id: str
    scenario_name: str
    score_with_rules: float = 0.0
    score_baseline: float = 0.0
    delta: float = 0.0
    with_rules_met: List[str] = field(default_factory=list)
    with_rules_missed: List[str] = field(default_factory=list)
    baseline_met: List[str] = field(default_factory=list)
    baseline_missed: List[str] = field(default_factory=list)
    error: str = ""


# ─── Core ────────────────────────────────────────────────────

def load_rules() -> str:
    texts = []
    for f in RULE_FILES:
        p = RULES_DIR / f
        if p.is_file(): texts.append(p.read_text())
    for f in SKILL_FILES:
        p = SKILLS_DIR / f
        if p.is_file(): texts.append(p.read_text())
    return "\n\n---\n\n".join(texts)


class ABBenchmark:
    def __init__(self, api_keys: List[str], model: str, judge_model: str):
        self.api_keys = api_keys
        self.model = model
        self.judge_model = judge_model
        self._key_idx = 0
        self.rules = load_rules()

    def _rotate_key(self):
        self._key_idx = (self._key_idx + 1) % len(self.api_keys)

    def _call(self, model: str, system: str, prompt: str, retries: int = 8) -> str:
        from google import genai
        from google.genai import types

        for attempt in range(retries):
            try:
                client = genai.Client(api_key=self.api_keys[self._key_idx])
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system if system else None,
                        temperature=0.3,
                    ),
                )
                return response.text.strip()
            except Exception as e:
                err = str(e).lower()
                if "429" in str(e) or "quota" in err or "resource" in err:
                    self._rotate_key()
                    backoff = min(2 ** (attempt + 1), 30)
                    print(f"      ⏳ Rate limit, waiting {backoff}s...")
                    time.sleep(backoff)
                else:
                    return f"ERROR: {str(e)[:150]}"
        return "ERROR: quota exhausted"

    def _judge(self, response: str, criteria: List[str]) -> Dict:
        criteria_text = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(criteria))
        judge_prompt = f"""Evaluate this AI assistant response against strict criteria.

## Criteria (each scores equally):
{criteria_text}

## Response to evaluate:
```
{response[:3000]}
```

For EACH criterion, determine if the response CLEARLY demonstrates it (not just vaguely mentions it).
Score = (criteria met) / (total criteria) × 100

Reply with JSON ONLY, no markdown:
{{"score": 0-100, "criteria_met": ["..."], "criteria_missed": ["..."]}}"""

        result = self._call(self.judge_model, "You are a strict AI auditor. Reply JSON only.", judge_prompt)
        try:
            result = re.sub(r'^```(?:json)?\s*', '', result)
            result = re.sub(r'\s*```$', '', result)
            return json.loads(result)
        except:
            return {"score": 0, "criteria_met": [], "criteria_missed": ["JSON parse error"]}

    def run_scenario(self, scenario: Dict) -> ABResult:
        result = ABResult(scenario_id=scenario["id"], scenario_name=scenario["name"])

        # ─── Group A: WITH RULES ───
        system_a = f"You are an AI coding assistant in Google Gemini IDE (Antigravity). You MUST follow these rules:\n\n{self.rules}\n\nFollow ALL rules strictly. Show exact bash commands."
        response_a = self._call(self.model, system_a, scenario["prompt"])

        if response_a.startswith("ERROR:"):
            result.error = response_a
            return result

        time.sleep(3)
        judge_a = self._judge(response_a, scenario["criteria"])
        result.score_with_rules = judge_a.get("score", 0)
        result.with_rules_met = judge_a.get("criteria_met", [])
        result.with_rules_missed = judge_a.get("criteria_missed", [])

        time.sleep(3)

        # ─── Group B: BASELINE (no rules) ───
        system_b = "You are an AI coding assistant."
        response_b = self._call(self.model, system_b, scenario["prompt"])

        if response_b.startswith("ERROR:"):
            result.error = response_b
            return result

        time.sleep(3)
        judge_b = self._judge(response_b, scenario["criteria"])
        result.score_baseline = judge_b.get("score", 0)
        result.baseline_met = judge_b.get("criteria_met", [])
        result.baseline_missed = judge_b.get("criteria_missed", [])

        result.delta = result.score_with_rules - result.score_baseline
        return result

    def run_all(self) -> List[ABResult]:
        results = []
        for i, s in enumerate(SCENARIOS):
            print(f"\n  📋 [{i+1}/{len(SCENARIOS)}] {s['name']}")
            r = self.run_scenario(s)

            if r.error:
                print(f"    ⚠️ Error: {r.error[:80]}")
            else:
                a_icon = "✅" if r.score_with_rules >= 70 else "⚠️" if r.score_with_rules >= 40 else "❌"
                b_icon = "✅" if r.score_baseline >= 70 else "⚠️" if r.score_baseline >= 40 else "❌"
                d_icon = "📈" if r.delta > 0 else "📉" if r.delta < 0 else "➡️"
                d_sign = f"+{r.delta:.0f}" if r.delta > 0 else f"{r.delta:.0f}"
                print(f"    [A] Rules:    {a_icon} {r.score_with_rules:.0f}/100")
                print(f"    [B] Baseline: {b_icon} {r.score_baseline:.0f}/100")
                print(f"    {d_icon} Delta: {d_sign}")

            results.append(r)
            time.sleep(4)
        return results


def print_ab_report(results: List[ABResult], model: str):
    valid = [r for r in results if not r.error]
    if not valid:
        print("\n❌ No valid results to report")
        return

    avg_a = sum(r.score_with_rules for r in valid) / len(valid)
    avg_b = sum(r.score_baseline for r in valid) / len(valid)
    avg_delta = avg_a - avg_b

    print("\n" + "=" * 62)
    print("  🔬 A/B BENCHMARK REPORT")
    print(f"  Model: {model}")
    print("=" * 62)
    print(f"\n  {'Scenario':<28} {'Rules':>7} {'Base':>7} {'Delta':>7}")
    print("  " + "─" * 55)

    for r in results:
        if r.error:
            print(f"  {r.scenario_name[:28]:<28} {'ERR':>7} {'ERR':>7} {'ERR':>7}")
        else:
            d = r.delta
            d_str = f"+{d:.0f}" if d > 0 else f"{d:.0f}"
            d_color = "✅" if d > 0 else "❌" if d < 0 else "➡️"
            print(f"  {r.scenario_name[:28]:<28} {r.score_with_rules:>5.0f}   {r.score_baseline:>5.0f}   {d_color}{d_str:>4}")

    print("  " + "─" * 55)
    d_sign = f"+{avg_delta:.0f}" if avg_delta > 0 else f"{avg_delta:.0f}"
    verdict = "📈" if avg_delta > 0 else "📉" if avg_delta < 0 else "➡️"
    print(f"  {'AVERAGE':<28} {avg_a:>5.0f}   {avg_b:>5.0f}   {verdict}{d_sign:>4}")

    print(f"\n  ╔{'═'*58}╗")
    if avg_delta > 10:
        print(f"  ║  🏆 Rules improved compliance by +{avg_delta:.0f}% on average!       ║")
    elif avg_delta > 0:
        print(f"  ║  ✅ Rules provided marginal improvement (+{avg_delta:.0f}%)           ║")
    elif avg_delta == 0:
        print(f"  ║  ➡️  No measurable difference between rules and baseline  ║")
    else:
        print(f"  ║  ⚠️ Rules decreased score by {avg_delta:.0f}% — investigate!       ║")
    print(f"  ╚{'═'*58}╝\n")

    improvements = [(r.scenario_name, r.baseline_missed) for r in valid if r.delta > 0 and r.baseline_missed]
    if improvements:
        print("  🎯 Key improvements from rules:")
        for name, missed in improvements:
            for m in missed[:2]:
                print(f"    • {name}: baseline missed '{m}'")
        print()


def main():
    parser = argparse.ArgumentParser(description="A/B benchmark: rules vs baseline")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Model to test")
    parser.add_argument("--judge", default="gemini-2.5-flash", help="Judge model")
    args = parser.parse_args()

    if not API_KEYS:
        print("❌ Set GOOGLE_AI_API_KEY"); sys.exit(1)

    print(f"\n🔬 A/B Benchmark: {args.model}")
    print(f"   Judge: {args.judge}")
    print(f"   Scenarios: {len(SCENARIOS)}")
    print(f"   Keys: {len(API_KEYS)}")

    bench = ABBenchmark(API_KEYS, args.model, args.judge)
    results = bench.run_all()
    print_ab_report(results, args.model)

    out = Path(__file__).parent / "ab_results.json"
    with open(out, "w") as f:
        json.dump([{
            "scenario": r.scenario_id, "name": r.scenario_name,
            "score_rules": r.score_with_rules, "score_baseline": r.score_baseline,
            "delta": r.delta, "error": r.error,
            "rules_met": r.with_rules_met, "rules_missed": r.with_rules_missed,
            "baseline_met": r.baseline_met, "baseline_missed": r.baseline_missed,
        } for r in results], f, indent=2)
    print(f"📁 Saved to {out}")


if __name__ == "__main__":
    main()
