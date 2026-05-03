# Gemini Browser Agent Skills — OpenAI Codex

> Auto-loaded by OpenAI Codex CLI when placed at project root.
> See `AGENTS.md` for universal rules. This file contains Codex-specific overrides.

## CODEX-SPECIFIC BEHAVIOR

### Sandbox Awareness
- Codex runs in a sandboxed environment with limited network access
- Browser automation may not be available in sandbox mode
- If browser tools are unavailable → skip browser-specific rules, warn user

### File Reading Protocol
Codex tends to be aggressive with file reads. Enforce compliance:
- When user requests reading N files → read ALL N files
- State: `📂 Read X/Y files` after reading
- If X < Y → read remaining files BEFORE any analysis

### Context Management
- Codex sessions are typically shorter — less context drift risk
- Focus on accurate file reading and rule compliance over compression
- Use structured output for verification:
  ```
  📋 Rules: [active rules]
  📂 Files: X/Y read
  ✅ Proceeding with task
  ```

### Dynamic Routing
Read `SKILLS_ROUTER.md` at conversation start.
Match tasks against routing table before loading `skills/*/SKILL.md` files.

## RULES INHERITANCE
This file extends `AGENTS.md`. All rules in `AGENTS.md` apply here.
