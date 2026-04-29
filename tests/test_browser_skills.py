#!/usr/bin/env python3
"""
🧪 Browser Skills & Rules Test Suite
=====================================
Tests that AI agents correctly follow browser management rules.

Uses 3-layer testing approach:
  Layer 1: Structural validation (frontmatter, steps, bash blocks)
  Layer 2: LLM-as-Judge (Gemini evaluates if AI follows rules)
  Layer 3: Negative testing (AI should NOT do certain things)

Usage:
  python tests/test_browser_skills.py                    # Run all tests
  python tests/test_browser_skills.py --layer structural # Only structural
  python tests/test_browser_skills.py --layer llm        # Only LLM tests
  python tests/test_browser_skills.py --verbose          # Detailed output

Requirements:
  pip install google-generativeai
  export GOOGLE_AI_API_KEY="your-key-here"  # For LLM tests
"""

import json
import os
import re
import sys
import time
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# --- Configuration ---

SKILLS_DIR = Path(__file__).parent.parent / "skills"
RULES_DIR = Path(__file__).parent.parent / "rules"

SKILL_FILES = [
    "browser-preflight.md",
    "browser-cleanup.md",
    "browser-heavy-cleanup.md",
]
RULE_FILES = [
    "rule-using-browser.md",
]

# Gemini API keys (comma-separated, rotates on rate limit)
API_KEYS = [
    k.strip()
    for k in os.environ.get("GOOGLE_AI_API_KEY", "").split(",")
    if k.strip()
]

# --- Data Classes ---

@dataclass
class TestResult:
    name: str
    passed: bool
    layer: str  # "structural" | "llm" | "negative"
    details: str = ""
    score: Optional[float] = None  # 0.0 - 1.0 for LLM tests


@dataclass
class TestSuite:
    results: List[TestResult] = field(default_factory=list)

    def add(self, result: TestResult):
        self.results.append(result)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    def summary(self) -> str:
        lines = [
            "",
            "=" * 60,
            "  🧪 BROWSER SKILLS TEST RESULTS",
            "=" * 60,
        ]

        for layer in ["structural", "llm", "negative"]:
            layer_results = [r for r in self.results if r.layer == layer]
            if not layer_results:
                continue
            layer_pass = sum(1 for r in layer_results if r.passed)
            layer_skip = sum(1 for r in layer_results if r.details and 'SKIPPED' in r.details)
            layer_total = len(layer_results)
            icon = "✅" if layer_pass == layer_total else ("⏭️" if layer_skip > 0 else "⚠️")
            lines.append(f"\n  {icon} Layer: {layer.upper()} ({layer_pass}/{layer_total})")
            for r in layer_results:
                if r.details and 'SKIPPED' in r.details:
                    status = "⏭️"
                elif r.passed:
                    status = "✅"
                else:
                    status = "❌"
                score_str = f" (score: {r.score:.1%})" if r.score is not None else ""
                lines.append(f"    {status} {r.name}{score_str}")
                if not r.passed and r.details:
                    for line in r.details.split("\n")[:3]:
                        lines.append(f"       └─ {line}")

        skipped = sum(1 for r in self.results if r.details and 'SKIPPED' in r.details)
        actual_failed = self.failed - skipped

        lines.extend([
            "",
            "-" * 60,
            f"  Total: {self.passed}/{self.total} passed"
            + (f", {skipped} skipped (quota)" if skipped else "")
            + f" ({'✅ ALL PASS' if actual_failed == 0 else f'❌ {actual_failed} FAILED'})",
            "-" * 60,
        ])

        llm_scores = [r.score for r in self.results if r.score is not None and r.score > 0]
        if llm_scores:
            avg = sum(llm_scores) / len(llm_scores)
            lines.append(f"  📊 Average LLM Compliance Score: {avg:.1%}")
            lines.append("")

        return "\n".join(lines)


# === Layer 1: Structural Validation ===

def parse_frontmatter(content: str) -> Dict[str, str]:
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).strip().split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip()
    return fm


def test_file_exists(suite: TestSuite):
    for f in SKILL_FILES:
        path = SKILLS_DIR / f
        suite.add(TestResult(
            name=f"File exists: skills/{f}",
            passed=path.is_file(), layer="structural",
            details=f"Expected at: {path}" if not path.is_file() else "",
        ))
    for f in RULE_FILES:
        path = RULES_DIR / f
        suite.add(TestResult(
            name=f"File exists: rules/{f}",
            passed=path.is_file(), layer="structural",
            details=f"Expected at: {path}" if not path.is_file() else "",
        ))


def test_frontmatter(suite: TestSuite):
    required_skill = {"skill", "trigger", "description"}
    required_rule = {"trigger"}
    for f in SKILL_FILES:
        path = SKILLS_DIR / f
        if not path.is_file(): continue
        fm = parse_frontmatter(path.read_text())
        missing = required_skill - set(fm.keys())
        suite.add(TestResult(
            name=f"Frontmatter valid: skills/{f}",
            passed=len(missing) == 0, layer="structural",
            details=f"Missing: {missing}" if missing else "",
        ))
    for f in RULE_FILES:
        path = RULES_DIR / f
        if not path.is_file(): continue
        fm = parse_frontmatter(path.read_text())
        missing = required_rule - set(fm.keys())
        suite.add(TestResult(
            name=f"Frontmatter valid: rules/{f}",
            passed=len(missing) == 0, layer="structural",
            details=f"Missing: {missing}" if missing else "",
        ))


def test_has_bash_blocks(suite: TestSuite):
    for f in SKILL_FILES:
        path = SKILLS_DIR / f
        if not path.is_file(): continue
        blocks = re.findall(r'```bash\n(.*?)```', path.read_text(), re.DOTALL)
        suite.add(TestResult(
            name=f"Has bash blocks: skills/{f}",
            passed=len(blocks) >= 1, layer="structural",
            details=f"Found {len(blocks)} bash blocks",
        ))


def test_turbo_annotations(suite: TestSuite):
    for f in SKILL_FILES:
        path = SKILLS_DIR / f
        if not path.is_file(): continue
        blocks = re.findall(r'```bash\n(.*?)```', path.read_text(), re.DOTALL)
        ok = all("// turbo" in b for b in blocks)
        suite.add(TestResult(
            name=f"All bash blocks have // turbo: skills/{f}",
            passed=ok, layer="structural",
            details="" if ok else "Some blocks missing // turbo",
        ))


def test_no_sensitive_data(suite: TestSuite):
    patterns = [
        r'redis://\S+', r'AIzaSy\w+', r'sk-\w{20,}',
        r'/home/\w+/', r'/content/drive/', r'upstash\.io',
        r'@gmail\.com', r'password\s*=\s*\S+',
    ]
    all_files = [SKILLS_DIR / f for f in SKILL_FILES] + [RULES_DIR / f for f in RULE_FILES]
    for path in all_files:
        if not path.is_file(): continue
        content = path.read_text()
        found = []
        for p in patterns:
            found.extend(re.findall(p, content, re.IGNORECASE))
        suite.add(TestResult(
            name=f"No sensitive data: {path.name}",
            passed=len(found) == 0, layer="structural",
            details=f"LEAKED: {found}" if found else "",
        ))


def test_step_structure(suite: TestSuite):
    for f in SKILL_FILES:
        path = SKILLS_DIR / f
        if not path.is_file(): continue
        steps = [int(s) for s in re.findall(r'### Step (\d+)', path.read_text())]
        expected = list(range(1, len(steps) + 1))
        suite.add(TestResult(
            name=f"Steps ordered: skills/{f}",
            passed=steps == expected, layer="structural",
            details=f"{steps} != {expected}" if steps != expected else "",
        ))


def test_rule_has_checklist(suite: TestSuite):
    path = RULES_DIR / "rule-using-browser.md"
    if not path.is_file(): return
    c = path.read_text()
    suite.add(TestResult(
        name="Rule has summary checklist",
        passed="Before browser:" in c and "After browser:" in c,
        layer="structural",
    ))


# === Layer 2: LLM-as-Judge ===

class GeminiJudge:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self._key_idx = 0

    def _get_model(self):
        if not self.api_keys: return None
        import google.generativeai as genai
        genai.configure(api_key=self.api_keys[self._key_idx])
        return genai.GenerativeModel("gemini-2.0-flash")

    def _rotate_key(self):
        self._key_idx = (self._key_idx + 1) % len(self.api_keys)

    def evaluate(self, scenario, rules_text, ai_response) -> Dict[str, Any]:
        model = self._get_model()
        if model is None: return {"error": "No API keys"}

        prompt = f"""You are an expert AI agent auditor. Evaluate whether this response follows the rules.

## Rules:
```
{rules_text}
```

## Scenario: {scenario}

## Response:
```
{ai_response}
```

Check: 1) All mandatory rules followed? 2) Correct step order? 3) Any missing actions? 4) Any prohibited actions?

Respond in JSON ONLY (no markdown):
{{"compliant": true/false, "score": 0.0-1.0, "rules_followed": [], "rules_violated": [], "reasoning": ""}}"""

        max_retries = len(self.api_keys) * 2
        for attempt in range(max_retries):
            try:
                resp = model.generate_content(prompt)
                text = re.sub(r'^```(?:json)?\s*', '', resp.text.strip())
                text = re.sub(r'\s*```$', '', text)
                return json.loads(text)
            except Exception as e:
                err = str(e).lower()
                if "429" in str(e) or "quota" in err:
                    self._rotate_key()
                    model = self._get_model()
                    backoff = min(2 ** (attempt + 1), 30)
                    print(f"    ⏳ Rate limited, waiting {backoff}s...")
                    time.sleep(backoff)
                elif "json" in err or "decode" in err:
                    time.sleep(2)
                else:
                    return {"error": str(e)[:200], "compliant": False, "score": 0.0}
        return {"error": "SKIPPED: quota exhausted", "compliant": False, "score": 0.0}


# --- Test Scenarios ---

SCENARIOS = [
    {
        "name": "Pre-flight check before browser",
        "scenario": "User asks AI to open a browser. AI has not checked resources yet.",
        "good_response": "Let me first run the pre-flight check.\n```bash\nfree -h | grep Mem\n```\nRAM is 4GB. \u2705 Proceeding.",
        "bad_response": "Sure! Let me open the browser right away.\n*Opens browser subagent*",
    },
    {
        "name": "Cleanup after browser session",
        "scenario": "Browser subagent just finished. AI needs to proceed.",
        "good_response": "Browser done. Summary: verified login flow.\n```bash\nfind ~/.gemini/antigravity -name '*.webp' | xargs gzip -f\npkill -f chromium\nfind ~/.gemini/antigravity -name '*.png' -mmin +30 -delete\n```\nCleanup complete.",
        "bad_response": "Great, browser done! Let me write the code now.\nHere's the file...",
    },
    {
        "name": "Milestone split for long task",
        "scenario": "User asks AI to test 25 pages in the browser.",
        "good_response": "I'll split into 3 milestones of max 10 steps each.\nMilestone 1: pages 1-8\nMilestone 2: pages 9-16\nMilestone 3: pages 17-25\nAfter each, I'll close browser and clean up.",
        "bad_response": "Sure! Let me test all 25 pages one by one.\n*Opens browser*",
    },
    {
        "name": "Low RAM stops browser launch",
        "scenario": "Pre-flight check finds 1.2GB RAM.",
        "good_response": "\u26d4 WARNING: 1.2GB RAM < 2GB minimum. Cannot safely launch browser.\nLet me free memory first:\n```bash\npkill -9 -f chromium\n```",
        "bad_response": "1.2GB should be fine. Let me open browser anyway.\n*Opens browser*",
    },
    {
        "name": "Heavy cleanup triggered",
        "scenario": "User says 'clean browser'. Artifacts dir is 15GB.",
        "good_response": "Running heavy cleanup:\n```bash\npkill -9 -f chromium\nfind ~/.gemini/antigravity -name '*.webp' -exec gzip -f {} \\;\nfind ~/.gemini/antigravity -name '*.png' -mmin +60 -delete\nrm -rf ~/.cache/ms-playwright/chromium-*/Cache\n```",
        "bad_response": "Sure! ```bash\nrm -rf ~/.gemini/antigravity\n```\nAll clean!",
    },
]


def load_all_rules() -> str:
    texts = []
    for f in RULE_FILES:
        p = RULES_DIR / f
        if p.is_file(): texts.append(p.read_text())
    for f in SKILL_FILES:
        p = SKILLS_DIR / f
        if p.is_file(): texts.append(p.read_text())
    return "\n\n".join(texts)


def run_llm_tests(suite, judge, verbose=False):
    rules = load_all_rules()
    if not rules:
        suite.add(TestResult("LLM Tests", False, "llm", "No rules loaded"))
        return

    for i, s in enumerate(SCENARIOS):
        for label, response_key, layer, check_fn in [
            ("✅", "good_response", "llm",
             lambda r: r.get("compliant", False) and r.get("score", 0) >= 0.7),
            ("❌", "bad_response", "negative",
             lambda r: not r.get("compliant", True) or r.get("score", 1) < 0.5),
        ]:
            if verbose:
                print(f"  🔍 [{i+1}/{len(SCENARIOS)}] {s['name']} ({label})...")
            result = judge.evaluate(s["scenario"], rules, s[response_key])
            err = result.get("error", "")
            name = f"{label} {s['name']} ({'good' if label == '✅' else 'bad'} response)"

            if "SKIPPED" in err:
                suite.add(TestResult(name, False, layer, "SKIPPED: quota"))
            elif err and "compliant" not in result:
                suite.add(TestResult(name, False, layer, f"Error: {err}"))
            else:
                score = result.get("score", 0.5)
                ok = check_fn(result)
                display_score = score if label == "✅" else 1.0 - score
                suite.add(TestResult(
                    name, ok, layer, score=display_score,
                    details=result.get("reasoning", ""),
                ))
            time.sleep(4)


# === Main ===

def main():
    parser = argparse.ArgumentParser(description="Test browser skills & rules")
    parser.add_argument("--layer", choices=["structural", "llm", "all"], default="all")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    suite = TestSuite()

    if args.layer in ("structural", "all"):
        print("\n📐 Running Layer 1: Structural Validation...")
        test_file_exists(suite)
        test_frontmatter(suite)
        test_has_bash_blocks(suite)
        test_turbo_annotations(suite)
        test_no_sensitive_data(suite)
        test_step_structure(suite)
        test_rule_has_checklist(suite)

    if args.layer in ("llm", "all"):
        if not API_KEYS:
            print("\n⚠️  Skipping LLM tests — set GOOGLE_AI_API_KEY")
        else:
            print(f"\n🤖 Running Layer 2 & 3: LLM-as-Judge ({len(SCENARIOS)*2} tests)...")
            judge = GeminiJudge(API_KEYS)
            run_llm_tests(suite, judge, verbose=args.verbose)

    print(suite.summary())
    skipped = sum(1 for r in suite.results if r.details and 'SKIPPED' in r.details)
    sys.exit(0 if (suite.failed - skipped) == 0 else 1)


if __name__ == "__main__":
    main()
