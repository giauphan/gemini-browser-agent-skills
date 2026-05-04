---
name: browser-route-discovery
description: Discover project routes/URLs BEFORE planning browser navigation. Prevents 404 errors by reading route definitions from the codebase first. Supports Laravel, Next.js, Nuxt, React Router, Vue Router, Django, Flask, Express, and static sites.
compatibility: "Works with any AI IDE. Requires access to the project's codebase via file reading tools."
license: MIT
allowed-tools: ReadFile, ViewFile, Bash, Grep
metadata:
  triggers:
    - before_browser_plan
    - before_navigate_url
    - browser_404_encountered
  token-cost: ~200
  openclaw:
    homepage: https://github.com/giauphan/gemini-browser-agent-skills
---

# Browser Route Discovery

> **MANDATORY**: Read project routes BEFORE planning ANY browser navigation.
> Skipping this step is the #1 cause of 404 errors in browser automation.

## Problem

AI agents guess URLs based on common conventions (e.g., `/admin`, `/dashboard`, `/api/users`).
But every project has **unique routing** — guessed URLs often return 404, wasting browser steps.

## When to Use

| Situation | Action |
|---|---|
| **BEFORE planning browser steps** | Run **Step 1** to discover routes |
| Browser hit a 404 | Run **Step 1**, then re-plan with correct URLs |
| Unsure about URL structure | Run **Step 1** before proceeding |
| Project uses custom routing | Run **Step 1** — NEVER guess |

---

## Step 1: Detect Framework & Find Route Files

**BEFORE planning any browser navigation**, identify the project's framework and read its route definitions.

### Auto-Detection Script

```bash
echo "=== Route Discovery ==="
PROJECT_DIR="$(pwd)"

# Detect framework by checking key files
if [ -f "$PROJECT_DIR/routes/web.php" ]; then
  echo "📦 Framework: Laravel"
  echo "📄 Route files:"
  ls -la "$PROJECT_DIR/routes/"
  echo "--- web.php routes ---"
  grep -n "Route::" "$PROJECT_DIR/routes/web.php" | head -50
  echo "--- api.php routes ---"
  grep -n "Route::" "$PROJECT_DIR/routes/api.php" 2>/dev/null | head -30

elif [ -d "$PROJECT_DIR/app" ] && [ -f "$PROJECT_DIR/next.config.js" -o -f "$PROJECT_DIR/next.config.mjs" -o -f "$PROJECT_DIR/next.config.ts" ]; then
  echo "📦 Framework: Next.js (App Router)"
  echo "📄 Page routes:"
  find "$PROJECT_DIR/app" -name "page.tsx" -o -name "page.jsx" -o -name "page.js" -o -name "page.ts" 2>/dev/null | sort
  echo "📄 API routes:"
  find "$PROJECT_DIR/app/api" -name "route.ts" -o -name "route.js" 2>/dev/null | sort

elif [ -d "$PROJECT_DIR/pages" ] && [ -f "$PROJECT_DIR/next.config.js" -o -f "$PROJECT_DIR/next.config.mjs" ]; then
  echo "📦 Framework: Next.js (Pages Router)"
  echo "📄 Page routes:"
  find "$PROJECT_DIR/pages" -name "*.tsx" -o -name "*.jsx" -o -name "*.js" -o -name "*.ts" 2>/dev/null | grep -v "_app\|_document\|_error" | sort

elif [ -d "$PROJECT_DIR/pages" ] && [ -f "$PROJECT_DIR/nuxt.config.ts" -o -f "$PROJECT_DIR/nuxt.config.js" ]; then
  echo "📦 Framework: Nuxt.js"
  echo "📄 Page routes:"
  find "$PROJECT_DIR/pages" -name "*.vue" 2>/dev/null | sort

elif [ -f "$PROJECT_DIR/manage.py" ]; then
  echo "📦 Framework: Django"
  echo "📄 URL configs:"
  find "$PROJECT_DIR" -name "urls.py" 2>/dev/null | head -10
  for f in $(find "$PROJECT_DIR" -name "urls.py" | head -5); do
    echo "--- $f ---"
    grep -n "path\|url(" "$f" | head -30
  done

elif [ -f "$PROJECT_DIR/app.py" ] || [ -f "$PROJECT_DIR/wsgi.py" ]; then
  echo "📦 Framework: Flask/Python"
  echo "📄 Route decorators:"
  grep -rn "@app.route\|@blueprint.route" "$PROJECT_DIR" --include="*.py" | head -30

elif [ -f "$PROJECT_DIR/package.json" ] && grep -q "express" "$PROJECT_DIR/package.json" 2>/dev/null; then
  echo "📦 Framework: Express.js"
  echo "📄 Route files:"
  find "$PROJECT_DIR" -path "*/routes/*.js" -o -path "*/routes/*.ts" 2>/dev/null | head -10
  grep -rn "router\.\(get\|post\|put\|delete\|patch\)\|app\.\(get\|post\|put\|delete\)" "$PROJECT_DIR/routes" --include="*.js" --include="*.ts" 2>/dev/null | head -30

elif [ -f "$PROJECT_DIR/src/router/index.ts" ] || [ -f "$PROJECT_DIR/src/router/index.js" ]; then
  echo "📦 Framework: Vue Router"
  echo "📄 Route config:"
  cat "$PROJECT_DIR/src/router/index.ts" 2>/dev/null || cat "$PROJECT_DIR/src/router/index.js" 2>/dev/null | head -60

elif grep -rq "createBrowserRouter\|BrowserRouter\|<Route" "$PROJECT_DIR/src" --include="*.tsx" --include="*.jsx" --include="*.ts" --include="*.js" 2>/dev/null; then
  echo "📦 Framework: React Router"
  echo "📄 Route definitions:"
  grep -rn "createBrowserRouter\|<Route\|path:" "$PROJECT_DIR/src" --include="*.tsx" --include="*.jsx" --include="*.ts" --include="*.js" | head -30

else
  echo "📦 Framework: Unknown / Static"
  echo "📄 Looking for HTML entry points..."
  find "$PROJECT_DIR" -maxdepth 2 -name "index.html" -o -name "*.html" 2>/dev/null | head -10
  echo "📄 Looking for any route patterns..."
  grep -rn "route\|path\|url\|endpoint" "$PROJECT_DIR/src" --include="*.js" --include="*.ts" --include="*.py" --include="*.php" 2>/dev/null | head -20
fi
```

---

## Step 2: Build a Route Map

After reading route files, create a mental map of available URLs:

```
🗺️ Route Map:
- GET  /               → Home page
- GET  /login          → Login page
- GET  /dashboard      → Dashboard (auth required)
- GET  /admin/users    → User management
- POST /api/v1/auth    → Auth API
- ...
```

### Rules for Building the Map

1. **Read the actual route file** — do NOT guess from folder names alone
2. **Note middleware/guards** — some routes require auth, admin role, etc.
3. **Note route parameters** — e.g., `/users/{id}` needs a real ID
4. **Note route prefixes** — e.g., all API routes under `/api/v1/`
5. **Note the base URL** — is it `localhost:3000`, `localhost:8000`, `127.0.0.1:8080`?

---

## Step 3: Validate URLs Before Navigation

**BEFORE putting any URL in a browser task prompt**, check it against the route map:

```
✅ URL Validation:
- Target: /admin/dashboard
- Exists in route map: YES ✅ → proceed
- Auth required: YES → ensure logged in first
```

```
❌ URL Validation:
- Target: /admin/settings
- Exists in route map: NO ❌
- Closest match: /admin/config
- Action: Use /admin/config instead
```

### NEVER Navigate Without Validation

| ❌ BAD (Guessing) | ✅ GOOD (Route-Aware) |
|---|---|
| "Navigate to `/admin`" | Read routes → found `/admin/dashboard` → navigate there |
| "Go to `/api/users`" | Read routes → found `/api/v1/users` → use correct path |
| "Open `/settings`" | Read routes → no `/settings` → found `/account/settings` |
| "Try `localhost:3000`" | Check package.json → dev server on port `5173` → use that |

---

## Step 4: Dev Server Port Discovery

Many 404s happen because the agent uses the **wrong port**. Check the actual dev server config:

```bash
echo "=== Dev Server Port Discovery ==="

# Check running dev servers
echo "Running dev servers:"
ss -tlnp 2>/dev/null | grep -E ":(3000|3001|4000|5000|5173|8000|8080|8888)" || echo "No common dev ports found"

# Check package.json scripts
if [ -f "package.json" ]; then
  echo "--- npm scripts ---"
  grep -A1 '"dev"\|"start"\|"serve"' package.json
fi

# Check .env for APP_URL or similar
for envfile in .env .env.local .env.development; do
  if [ -f "$envfile" ]; then
    echo "--- $envfile ---"
    grep -i "URL\|PORT\|HOST\|APP_URL\|VITE_\|NEXT_PUBLIC_" "$envfile" 2>/dev/null
  fi
done

# Check vite.config
if [ -f "vite.config.ts" ] || [ -f "vite.config.js" ]; then
  echo "--- Vite config ---"
  grep -n "port\|host" vite.config.* 2>/dev/null
fi
```

---

## Quick Reference: Pre-Navigation Checklist

Before EVERY browser navigation, the agent MUST confirm:

```
🔍 Pre-Navigation Check:
1. Route map built: [yes/no]
2. Target URL exists in routes: [yes/no/closest match]
3. Auth required: [yes/no]
4. Dev server running on port: [port number]
5. Base URL: [http://localhost:PORT]
→ Final URL: [full validated URL]
```

**If route map is not built → STOP → Run Step 1 first.**
**If URL not in route map → do NOT navigate → find closest match or ask user.**
