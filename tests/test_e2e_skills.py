#!/usr/bin/env python3
"""
E2E Test Suite for Gemini Browser Agent Skills & Rules
=====================================================

Tests 3 dimensions:
1. STRUCTURAL: SKILL.md format compliance (Anthropic spec)
2. ROUTING: Trigger conditions match correct files
3. ACTIVATION: Rules & skills actually fire in real scenarios

Based on community best practices:
- skill-test-skill scoring rubric (youngfreeFJS)
- Anthropic Agent Skills specification
- LLM-as-Judge eval pattern
"""

import os
import re
import sys
import json
import yaml
import subprocess
from pathlib import Path
from datetime import datetime

# ============================================
# CONFIG
# ============================================
PROJECT_ROOT = Path(__file__).parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"
RULES_DIR = PROJECT_ROOT / "rules"
ROUTER_FILE = PROJECT_ROOT / "SKILLS_ROUTER.md"

RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "summary": {"passed": 0, "failed": 0, "warnings": 0, "total": 0, "score": 0}
}

# ============================================
# HELPERS
# ============================================
def log_test(name, passed, details="", category="structural", points=0, max_points=0):
    """Log a test result."""
    status = "PASS" if passed else "FAIL"
    icon = "✅" if passed else "❌"
    RESULTS["tests"].append({
        "name": name,
        "category": category,
        "status": status,
        "details": details,
        "points": points if passed else 0,
        "max_points": max_points,
    })
    if passed:
        RESULTS["summary"]["passed"] += 1
    else:
        RESULTS["summary"]["failed"] += 1
    RESULTS["summary"]["total"] += 1
    print(f"  {icon} {name}: {details}" if details else f"  {icon} {name}")


def log_warning(name, details=""):
    """Log a warning."""
    RESULTS["tests"].append({
        "name": name,
        "category": "warning",
        "status": "WARN",
        "details": details,
        "points": 0,
        "max_points": 0,
    })
    RESULTS["summary"]["warnings"] += 1
    print(f"  ⚠️  {name}: {details}")


def parse_yaml_frontmatter(filepath):
    """Parse YAML frontmatter from a markdown file."""
    content = filepath.read_text()
    if not content.startswith("---"):
        return None, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content
    try:
        fm = yaml.safe_load(parts[1])
        return fm, parts[2].strip()
    except yaml.YAMLError:
        return None, content


# ============================================
# DIMENSION 1: DIRECTORY STRUCTURE (10 pts)
# ============================================
def test_directory_structure():
    """Test skills follow the SKILL.md directory structure."""
    print("\n📁 DIMENSION 1: Directory Structure (10 pts)")

    # Test 1.1: Each skill has its own directory
    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
    log_test(
        "Skills use subdirectory pattern",
        len(skill_dirs) >= 1,
        f"Found {len(skill_dirs)} skill directories: {[d.name for d in skill_dirs]}",
        "structural", 3, 3
    )

    # Test 1.2: Each skill directory contains SKILL.md
    for skill_dir in skill_dirs:
        has_skill_md = (skill_dir / "SKILL.md").exists()
        log_test(
            f"  {skill_dir.name}/SKILL.md exists",
            has_skill_md,
            "" if has_skill_md else f"Missing SKILL.md in {skill_dir}",
            "structural", 2, 2
        )

    # Test 1.3: No flat .md files in skills/ root (old format)
    flat_files = list(SKILLS_DIR.glob("*.md"))
    log_test(
        "No flat .md files in skills/ root",
        len(flat_files) == 0,
        f"Found {len(flat_files)} flat files (should be 0): {[f.name for f in flat_files]}" if flat_files else "Clean",
        "structural", 2, 2
    )

    # Test 1.4: SKILLS_ROUTER.md exists at project root
    log_test(
        "SKILLS_ROUTER.md exists",
        ROUTER_FILE.exists(),
        "",
        "structural", 1, 1
    )

    # Test 1.5: rules/ directory exists
    log_test(
        "rules/ directory exists",
        RULES_DIR.exists() and RULES_DIR.is_dir(),
        "",
        "structural", 2, 2
    )


# ============================================
# DIMENSION 2: FRONTMATTER COMPLIANCE (30 pts)
# ============================================
def test_frontmatter_compliance():
    """Test SKILL.md frontmatter follows Anthropic spec."""
    print("\n📋 DIMENSION 2: Frontmatter Compliance (30 pts)")

    required_fields = ["name", "description", "license", "allowed-tools"]
    recommended_fields = ["compatibility", "metadata"]

    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]

    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            log_test(f"{skill_dir.name}: frontmatter", False, "SKILL.md missing", "frontmatter", 0, 10)
            continue

        fm, body = parse_yaml_frontmatter(skill_md)

        # Test 2.1: Has valid YAML frontmatter
        log_test(
            f"{skill_dir.name}: has YAML frontmatter",
            fm is not None,
            "Valid YAML frontmatter" if fm else "Missing or invalid frontmatter",
            "frontmatter", 3, 3
        )
        if fm is None:
            continue

        # Test 2.2: Required fields present
        for field in required_fields:
            has_field = field in fm
            log_test(
                f"  {skill_dir.name}: has '{field}'",
                has_field,
                f"value: {str(fm.get(field, ''))[:60]}..." if has_field else f"MISSING required field",
                "frontmatter", 2, 2
            )

        # Test 2.3: Recommended fields
        for field in recommended_fields:
            has_field = field in fm
            if has_field:
                log_test(
                    f"  {skill_dir.name}: has '{field}'",
                    True,
                    f"present",
                    "frontmatter", 1, 1
                )
            else:
                log_warning(f"  {skill_dir.name}: missing optional '{field}'")

        # Test 2.4: Description is descriptive (> 50 chars)
        desc = fm.get("description", "")
        log_test(
            f"  {skill_dir.name}: description quality",
            len(str(desc)) > 50,
            f"Length: {len(str(desc))} chars (min 50)",
            "frontmatter", 2, 2
        )

        # Test 2.5: Name matches directory name
        name = fm.get("name", "")
        log_test(
            f"  {skill_dir.name}: name matches dir",
            name == skill_dir.name,
            f"name='{name}', dir='{skill_dir.name}'",
            "frontmatter", 1, 1
        )


# ============================================
# DIMENSION 3: BODY CONTENT QUALITY (25 pts)
# ============================================
def test_body_content():
    """Test SKILL.md body content quality."""
    print("\n📝 DIMENSION 3: Body Content Quality (25 pts)")

    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]

    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        fm, body = parse_yaml_frontmatter(skill_md)
        lines = body.split("\n")
        total_lines = len(lines)

        # Test 3.1: Under 500 lines (spec recommendation)
        log_test(
            f"{skill_dir.name}: under 500 lines",
            total_lines < 500,
            f"{total_lines} lines",
            "body", 3, 3
        )

        # Test 3.2: Has H1 heading
        has_h1 = any(line.startswith("# ") for line in lines)
        log_test(
            f"{skill_dir.name}: has H1 heading",
            has_h1,
            "",
            "body", 2, 2
        )

        # Test 3.3: Has code blocks (actionable)
        has_code = "```" in body
        log_test(
            f"{skill_dir.name}: has code blocks",
            has_code,
            "Contains executable instructions" if has_code else "No code blocks found",
            "body", 3, 3
        )

        # Test 3.4: Has step-by-step structure
        has_steps = bool(re.search(r'##\s+Step\s+\d', body))
        log_test(
            f"{skill_dir.name}: has step-by-step structure",
            has_steps,
            "Structured with numbered steps" if has_steps else "Missing step numbering",
            "body", 2, 2
        )

        # Test 3.5: No bare ALWAYS/NEVER without explanation (spec: "why over MUST")
        bare_musts = len(re.findall(r'(?:ALWAYS|NEVER|MUST)\b', body))
        has_explanations = len(re.findall(r'(?:because|since|to prevent|to ensure|otherwise)', body, re.I))
        ratio = has_explanations / max(bare_musts, 1)
        log_test(
            f"{skill_dir.name}: why-over-MUST ratio",
            ratio >= 0.3 or bare_musts <= 2,
            f"{bare_musts} directives, {has_explanations} explanations (ratio: {ratio:.1f})",
            "body", 2, 2
        )


# ============================================
# DIMENSION 4: ROUTING & TRIGGER (15 pts)
# ============================================
def test_routing():
    """Test SKILLS_ROUTER.md routing table."""
    print("\n🧭 DIMENSION 4: Routing & Trigger Compliance (15 pts)")

    if not ROUTER_FILE.exists():
        log_test("SKILLS_ROUTER.md exists", False, "File missing!", "routing", 0, 15)
        return

    content = ROUTER_FILE.read_text()

    # Test 4.1: Router has frontmatter with trigger: always_on
    fm, body = parse_yaml_frontmatter(ROUTER_FILE)
    log_test(
        "Router has always_on trigger",
        fm is not None and fm.get("trigger") == "always_on",
        f"trigger={fm.get('trigger')}" if fm else "No frontmatter",
        "routing", 3, 3
    )

    # Test 4.2: Router references all skill files
    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
    for skill_dir in skill_dirs:
        ref = f"skills/{skill_dir.name}/SKILL.md"
        log_test(
            f"Router references {skill_dir.name}",
            ref in content,
            f"Found: {ref}" if ref in content else f"Missing reference to {ref}",
            "routing", 2, 2
        )

    # Test 4.3: Router has token budget table
    has_budget = "Token Budget" in content or "token" in content.lower()
    log_test(
        "Router has token budget info",
        has_budget,
        "",
        "routing", 2, 2
    )

    # Test 4.4: Router has critical rules section
    has_critical = "CRITICAL" in content or "Always Active" in content
    log_test(
        "Router has critical rules (always-on)",
        has_critical,
        "",
        "routing", 2, 2
    )

    # Test 4.5: All trigger conditions are distinct
    table_rows = re.findall(r'\|\s*\d+\s*\|([^|]+)\|', content)
    unique_triggers = set(t.strip() for t in table_rows)
    log_test(
        "All triggers are unique",
        len(unique_triggers) == len(table_rows),
        f"{len(unique_triggers)} unique / {len(table_rows)} total",
        "routing", 2, 2
    )


# ============================================
# DIMENSION 5: CROSS-REFERENCES (10 pts)
# ============================================
def test_cross_references():
    """Test that all IDE rule files reference SKILL.md paths correctly."""
    print("\n🔗 DIMENSION 5: Cross-References Integrity (10 pts)")

    ide_files = {
        ".cursorrules": PROJECT_ROOT / ".cursorrules",
        ".clinerules": PROJECT_ROOT / ".clinerules",
        ".windsurfrules": PROJECT_ROOT / ".windsurfrules",
        ".traerules": PROJECT_ROOT / ".traerules",
        "copilot-instructions.md": PROJECT_ROOT / ".github" / "copilot-instructions.md",
        "AGENTS.md": PROJECT_ROOT / "AGENTS.md",
        "CLAUDE.md": PROJECT_ROOT / "CLAUDE.md",
        "GEMINI.md": PROJECT_ROOT / "GEMINI.md",
        "CODEX.md": PROJECT_ROOT / "CODEX.md",
    }

    # Test 5.1: No stale references (old flat paths)
    old_patterns = ["skills/browser-preflight.md", "skills/browser-cleanup.md", "skills/browser-heavy-cleanup.md"]
    for name, filepath in ide_files.items():
        if not filepath.exists():
            log_warning(f"{name}: file not found", str(filepath))
            continue
        content = filepath.read_text()
        has_old = any(p in content for p in old_patterns)
        log_test(
            f"{name}: no stale references",
            not has_old,
            "Clean" if not has_old else "Still references old flat paths!",
            "crossref", 1, 1
        )

    # Test 5.2: IDE files reference SKILL.md format
    for name, filepath in ide_files.items():
        if not filepath.exists():
            continue
        content = filepath.read_text()
        has_new = "SKILL.md" in content or "skills/" in content
        log_test(
            f"{name}: references skills/",
            has_new,
            "",
            "crossref", 1, 1
        )


# ============================================
# DIMENSION 6: RULES COMPLIANCE (10 pts)
# ============================================
def test_rules_compliance():
    """Test that rules/ files follow best practices."""
    print("\n📏 DIMENSION 6: Rules Compliance (10 pts)")

    rule_files = list(RULES_DIR.glob("*.md"))

    # Test 6.1: All rules have frontmatter
    for rule_file in rule_files:
        fm, body = parse_yaml_frontmatter(rule_file)
        log_test(
            f"{rule_file.name}: has frontmatter",
            fm is not None,
            f"trigger={fm.get('trigger')}" if fm else "Missing",
            "rules", 1, 1
        )

    # Test 6.2: self-check.md has file reading verification
    self_check = RULES_DIR / "self-check.md"
    if self_check.exists():
        content = self_check.read_text()
        has_read_check = "Read" in content and "/Y" in content
        log_test(
            "self-check: has file reading verification",
            has_read_check,
            "'Read X/Y files' pattern found" if has_read_check else "Missing",
            "rules", 3, 3
        )
    
    # Test 6.3: context-router has on-demand loading rule
    ctx_router = RULES_DIR / "context-router.md"
    if ctx_router.exists():
        content = ctx_router.read_text()
        has_ondemand = "on-demand" in content.lower() or "do not preload" in content.lower()
        log_test(
            "context-router: enforces on-demand loading",
            has_ondemand,
            "",
            "rules", 3, 3
        )

    # Test 6.4: rule-using-browser references both preflight and cleanup
    browser_rule = RULES_DIR / "rule-using-browser.md"
    if browser_rule.exists():
        content = browser_rule.read_text()
        has_preflight = "preflight" in content.lower()
        has_cleanup = "cleanup" in content.lower()
        log_test(
            "rule-using-browser: references full lifecycle",
            has_preflight and has_cleanup,
            f"preflight={'✅' if has_preflight else '❌'}, cleanup={'✅' if has_cleanup else '❌'}",
            "rules", 3, 3
        )


# ============================================
# MAIN
# ============================================
def main():
    print("=" * 60)
    print("  🧪 E2E Test Suite — Gemini Browser Agent Skills")
    print(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  📂 Project: {PROJECT_ROOT}")
    print("=" * 60)

    # Run all test dimensions
    test_directory_structure()
    test_frontmatter_compliance()
    test_body_content()
    test_routing()
    test_cross_references()
    test_rules_compliance()

    # Calculate score
    total_points = sum(t["points"] for t in RESULTS["tests"])
    max_points = sum(t["max_points"] for t in RESULTS["tests"])
    score = round((total_points / max_points) * 100) if max_points > 0 else 0
    RESULTS["summary"]["score"] = score
    RESULTS["summary"]["total_points"] = total_points
    RESULTS["summary"]["max_points"] = max_points

    # Grade
    if score >= 90:
        grade = "🏆 Excellent — production-ready"
    elif score >= 75:
        grade = "✅ Good — minor improvements recommended"
    elif score >= 60:
        grade = "⚠️ Acceptable — needs improvement"
    elif score >= 40:
        grade = "❌ Poor — significant rework required"
    else:
        grade = "🚫 Critical — major rewrite needed"

    # Print summary
    print("\n" + "=" * 60)
    print(f"  📊 FINAL SCORE: {total_points}/{max_points} ({score}%)")
    print(f"  📈 Grade: {grade}")
    print(f"  ✅ Passed: {RESULTS['summary']['passed']}")
    print(f"  ❌ Failed: {RESULTS['summary']['failed']}")
    print(f"  ⚠️  Warnings: {RESULTS['summary']['warnings']}")
    print("=" * 60)

    # Save results
    results_file = PROJECT_ROOT / "tests" / "e2e_results.json"
    results_file.parent.mkdir(exist_ok=True)
    with open(results_file, "w") as f:
        json.dump(RESULTS, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Results saved to: {results_file}")

    # Exit code
    sys.exit(0 if score >= 75 else 1)


if __name__ == "__main__":
    main()
