#!/usr/bin/env python3
"""
🏆 Multi-Model Benchmark for Browser Skills Compliance
=======================================================
Tests how well different AI models follow browser management rules.

Compares: Gemma 3, Gemma 4, Gemini 2.0 Flash, Gemini 2.5 Flash, Gemini 3 Flash

Usage:
  export GOOGLE_AI_API_KEY="key1,key2,key3"
  python tests/benchmark_models.py
  python tests/benchmark_models.py --models gemma-3-27b-it gemini-2.5-flash

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
from typing import List, Dict, Any, Optional

# ─── Configuration ───────────────────────────────────────────────────────

SKILLS_DIR = Path(__file__).parent.parent / "skills"
RULES_DIR = Path(__file__).parent.parent / "rules"

SKILL_FILES = ["browser-preflight.md", "browser-cleanup.md", "browser-heavy-cleanup.md"]
RULE_FILES = ["rule-using-browser.md"]

API_KEYS = [k.strip() for k in os.environ.get("GOOGLE_AI_API_KEY", "").split(",") if k.strip()]

# Models to benchmark (ordered by size/capability)
DEFAULT_MODELS = [
    "gemma-3-4b-it",          # Gemma 3 small (4B)
    "gemma-3-12b-it",         # Gemma 3 medium (12B)
    "gemma-3-27b-it",         # Gemma 3 large (27B)
    "gemma-4-31b-it",         # Gemma 4 (31B)
    "gemini-2.0-flash",       # Gemini 2.0 Flash
    "gemini-2.5-flash",       # Gemini 2.5 Flash
    "gemini-3-flash-preview", # Gemini 3 Flash
]

# ─── Test Scenarios ──────────────────────────────────────────────────────

SCENARIOS = [
    {
        "id": "preflight",
        "name": "Pre-flight check before browser",
        "scenario": "User asks you to open a browser to check a website. You have NOT checked system resources yet. What do you do?",
        "criteria": [
            "MUST check RAM before launching browser",
            "MUST check disk space",
            "MUST NOT open browser without checking resources first",
        ],
    },
    {
        "id": "cleanup",
        "name": "Post-session cleanup",
        "scenario": "The browser subagent just finished a task and returned results. What do you do IMMEDIATELY after?",
        "criteria": [
            "MUST summarize what happened in the browser session",
            "MUST compress .webp recordings (gzip)",
            "MUST kill zombie chromium processes (pkill)",
            "MUST clean old .png screenshots",
            "Cleanup order: compress → kill → clean",
        ],
    },
    {
        "id": "milestone",
        "name": "Milestone split for long task",
        "scenario": "User asks you to test 25 different pages in the browser. How do you plan this?",
        "criteria": [
            "MUST split into milestones of max 10 steps each",
            "MUST plan to close browser between milestones",
            "MUST NOT try to do all 25 in one continuous session",
        ],
    },
    {
        "id": "low_ram",
        "name": "Low RAM warning",
        "scenario": "You ran a pre-flight check and found only 1.2GB RAM available. The user wants you to open a browser. What do you do?",
        "criteria": [
            "MUST warn that 1.2GB < 2GB minimum",
            "MUST NOT launch the browser",
            "Should suggest freeing memory or alternative approach",
        ],
    },
    {
        "id": "heavy_cleanup",
        "name": "Heavy cleanup trigger",
        "scenario": "User says 'clean browser'. The artifacts directory is 15GB. What do you do?",
        "criteria": [
            "MUST kill ALL browser processes (pkill -9)",
            "MUST compress .webp recordings",
            "MUST delete old screenshots",
            "MUST clear browser caches (ms-playwright, /tmp)",
            "MUST NOT delete the entire artifacts directory",
        ],
    },
]

# ─── Data Classes ────────────────────────────────────────────────────────

@dataclass
class ModelResult:
    model: str
    scenario_id: str
    response: str = ""
    score: float = 0.0
    compliant: bool = False
    criteria_met: List[str] = field(default_factory=list)
    criteria_missed: List[str] = field(default_factory=list)
    reasoning: str = ""
    latency_ms: int = 0
    error: str = ""


# ─── Core Logic ──────────────────────────────────────────────────────────

def load_all_rules() -> str:
    texts = []
    for f in RULE_FILES:
        p = RULES_DIR / f
        if p.is_file(): texts.append(p.read_text())
    for f in SKILL_FILES:
        p = SKILLS_DIR / f
        if p.is_file(): texts.append(p.read_text())
    return "\n\n".join(texts)


class MultiModelBenchmark:
    def __init__(self, api_keys: List[str], models: List[str]):
        self.api_keys = api_keys
        self.models = models
        self._key_idx = 0
        self.rules_text = load_all_rules()

    def _rotate_key(self):
        self._key_idx = (self._key_idx + 1) % len(self.api_keys)

    def _get_client(self):
        from google import genai
        return genai.Client(api_key=self.api_keys[self._key_idx])

    def _call_model(self, model_name: str, prompt: str, max_retries: int = 6) -> tuple:
        """Call a model and return (response_text, latency_ms, error)."""
        for attempt in range(max_retries):
            try:
                client = self._get_client()
                start = time.time()
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                latency = int((time.time() - start) * 1000)
                return response.text.strip(), latency, ""
            except Exception as e:
                err = str(e).lower()
                if "429" in str(e) or "quota" in err or "resource" in err:
                    self._rotate_key()
                    backoff = min(2 ** (attempt + 1), 30)
                    print(f"      ⏳ Rate limited, waiting {backoff}s (key {self._key_idx+1}/{len(self.api_keys)})...")
                    time.sleep(backoff)
                    continue
                elif "not found" in err or "not supported" in err:
                    return "", 0, f"Model not available: {model_name}"
                else:
                    return "", 0, str(e)[:200]
        return "", 0, "SKIPPED: quota exhausted"

    def generate_response(self, model_name: str, scenario: dict) -> str:
        """Ask the model to respond to a scenario as an AI assistant."""
        prompt = f"""You are an AI coding assistant using Google Gemini IDE (Antigravity). You have been given these rules and skills to follow:

{self.rules_text}

---

Now respond to this scenario as if you are the AI assistant:

**Scenario:** {scenario['scenario']}

Respond naturally as the AI assistant would. Show what commands you would run, what checks you would do, and explain your reasoning. Be specific and include actual bash commands where needed."""

        text, latency, error = self._call_model(model_name, prompt)
        return text, latency, error

    def judge_response(self, scenario: dict, response: str) -> dict:
        """Use a strong model to judge the response."""
        criteria_text = "\n".join(f"  - {c}" for c in scenario["criteria"])

        judge_prompt = f"""You are an expert AI agent auditor. Evaluate this AI response against strict rules.

## Evaluation Criteria:
{criteria_text}

## AI's Response:
```
{response}
```

Score EACH criterion as MET or MISSED. Be strict — the response must clearly demonstrate following the rule, not just vaguely mention it.

Respond in JSON ONLY (no markdown fences):
{{
  "score": 0.0 to 1.0,
  "compliant": true if score >= 0.7,
  "criteria_met": ["list of criteria clearly met"],
  "criteria_missed": ["list of criteria missed or unclear"],
  "reasoning": "brief explanation"
}}"""

        judge_model = "gemini-2.5-flash"
        text, _, error = self._call_model(judge_model, judge_prompt)
        if error:
            return {"error": error, "score": 0.0, "compliant": False}

        try:
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            return json.loads(text)
        except:
            return {"error": f"JSON parse failed: {text[:100]}", "score": 0.0, "compliant": False}

    def run(self, verbose: bool = False) -> List[ModelResult]:
        """Run all benchmarks across all models."""
        results = []

        for model_name in self.models:
            print(f"\n{'='*60}")
            print(f"  🤖 Model: {model_name}")
            print(f"{'='*60}")

            for scenario in SCENARIOS:
                print(f"  📋 {scenario['name']}...", end=" ", flush=True)

                response, latency, error = self.generate_response(model_name, scenario)
                if error:
                    print(f"⚠️ {error}")
                    results.append(ModelResult(
                        model=model_name, scenario_id=scenario["id"],
                        error=error, latency_ms=latency,
                    ))
                    time.sleep(2)
                    continue

                if verbose:
                    print(f"\n    Response ({latency}ms): {response[:150]}...")

                time.sleep(3)
                judgment = self.judge_response(scenario, response)
                if "error" in judgment and judgment.get("score", 0) == 0:
                    print(f"⚠️ Judge error")
                    results.append(ModelResult(
                        model=model_name, scenario_id=scenario["id"],
                        response=response, latency_ms=latency,
                        error=judgment.get("error", "unknown"),
                    ))
                    time.sleep(2)
                    continue

                score = judgment.get("score", 0.0)
                icon = "✅" if score >= 0.7 else "⚠️" if score >= 0.4 else "❌"
                print(f"{icon} {score:.0%} ({latency}ms)")

                results.append(ModelResult(
                    model=model_name,
                    scenario_id=scenario["id"],
                    response=response,
                    score=score,
                    compliant=judgment.get("compliant", False),
                    criteria_met=judgment.get("criteria_met", []),
                    criteria_missed=judgment.get("criteria_missed", []),
                    reasoning=judgment.get("reasoning", ""),
                    latency_ms=latency,
                ))

                time.sleep(4)

        return results


def print_leaderboard(results: List[ModelResult]):
    """Print a comparison leaderboard."""
    model_scores: Dict[str, List[float]] = {}
    model_latencies: Dict[str, List[int]] = {}
    model_errors: Dict[str, int] = {}

    for r in results:
        if r.model not in model_scores:
            model_scores[r.model] = []
            model_latencies[r.model] = []
            model_errors[r.model] = 0

        if r.error:
            model_errors[r.model] += 1
        else:
            model_scores[r.model].append(r.score)
            model_latencies[r.model].append(r.latency_ms)

    print("\n" + "=" * 70)
    print("  🏆 MODEL BENCHMARK LEADERBOARD — Browser Skills Compliance")
    print("=" * 70)
    print(f"  {'Model':<30} {'Score':>8} {'Latency':>10} {'Pass':>6} {'Skip':>6}")
    print("  " + "-" * 66)

    rankings = []
    for model in model_scores:
        scores = model_scores[model]
        avg_score = sum(scores) / len(scores) if scores else 0
        avg_latency = sum(model_latencies[model]) / len(model_latencies[model]) if model_latencies[model] else 0
        passed = sum(1 for s in scores if s >= 0.7)
        errors = model_errors[model]
        rankings.append((model, avg_score, avg_latency, passed, len(scores), errors))

    rankings.sort(key=lambda x: x[1], reverse=True)

    for rank, (model, avg_score, avg_lat, passed, total, errors) in enumerate(rankings, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        score_bar = "█" * int(avg_score * 10) + "░" * (10 - int(avg_score * 10))
        skip_str = f"{errors}" if errors else "-"
        print(f"  {medal} {model:<28} {avg_score:>6.0%} {score_bar} {avg_lat:>6.0f}ms {passed}/{total:>3} {skip_str:>5}")

    print("  " + "-" * 66)

    print("\n  📊 Per-Scenario Breakdown:")
    print(f"  {'Scenario':<25}", end="")
    for model, _, _, _, _, _ in rankings:
        short = model.replace("models/", "")[:12]
        print(f" {short:>12}", end="")
    print()
    print("  " + "-" * (25 + 13 * len(rankings)))

    for scenario in SCENARIOS:
        print(f"  {scenario['name'][:25]:<25}", end="")
        for model, _, _, _, _, _ in rankings:
            r = next((x for x in results if x.model == model and x.scenario_id == scenario["id"]), None)
            if r is None or r.error:
                print(f" {'SKIP':>12}", end="")
            else:
                icon = "✅" if r.score >= 0.7 else "⚠️" if r.score >= 0.4 else "❌"
                print(f" {icon}{r.score:>5.0%} {r.latency_ms:>4}ms", end="")
        print()

    print()

    failures = [r for r in results if not r.error and r.score < 0.7]
    if failures:
        print("  ⚠️ Notable Failures:")
        for r in failures:
            print(f"    {r.model} × {r.scenario_id}: {r.reasoning[:80]}")
            if r.criteria_missed:
                for c in r.criteria_missed[:2]:
                    print(f"      └─ Missing: {c}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Benchmark models on browser skills")
    parser.add_argument("--models", nargs="+", default=None,
                        help="Models to test (default: all available)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if not API_KEYS:
        print("❌ Set GOOGLE_AI_API_KEY environment variable")
        sys.exit(1)

    models = args.models or DEFAULT_MODELS
    print(f"🏁 Benchmarking {len(models)} models × {len(SCENARIOS)} scenarios = {len(models) * len(SCENARIOS)} tests")
    print(f"🔑 Using {len(API_KEYS)} API keys with rotation")

    benchmark = MultiModelBenchmark(API_KEYS, models)
    results = benchmark.run(verbose=args.verbose)
    print_leaderboard(results)

    out_path = Path(__file__).parent / "benchmark_results.json"
    with open(out_path, "w") as f:
        json.dump([{
            "model": r.model, "scenario": r.scenario_id,
            "score": r.score, "compliant": r.compliant,
            "latency_ms": r.latency_ms, "error": r.error,
            "criteria_met": r.criteria_met, "criteria_missed": r.criteria_missed,
            "reasoning": r.reasoning,
        } for r in results], f, indent=2)
    print(f"📁 Results saved to {out_path}")


if __name__ == "__main__":
    main()
