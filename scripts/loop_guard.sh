#!/usr/bin/env bash
# =============================================================================
# 🔄 Loop Guard — Real-time browser action loop detection & breaking
# =============================================================================
#
# This script runs BETWEEN browser_subagent calls to detect loops.
# It tracks what the browser subagent reported back and catches patterns.
#
# Usage:
#   source scripts/loop_guard.sh
#   loop_guard_init                              # Start tracking
#   loop_guard_log "click" "#btn-submit" "fail"  # Log an action
#   loop_guard_check                              # Check for loops
#   loop_guard_report                             # Show action history
#   loop_guard_reset                              # Clear history
#
# Integration with AI IDE:
#   The outer AI (Gemini/Claude/Cursor) should call these functions
#   between browser_subagent invocations. If loop_guard_check returns
#   non-zero, the AI MUST change strategy before calling browser again.
# =============================================================================

# Config
LOOP_GUARD_MAX_RETRIES=${LOOP_GUARD_MAX_RETRIES:-3}    # Max same-action retries
LOOP_GUARD_HISTORY_SIZE=${LOOP_GUARD_HISTORY_SIZE:-20}  # Actions to remember
LOOP_GUARD_DIR="${LOOP_GUARD_DIR:-/tmp/loop_guard_$$}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# =============================================================================
# Initialize tracking
# =============================================================================
loop_guard_init() {
    local conv_dir="${1:-$LOOP_GUARD_DIR}"
    LOOP_GUARD_DIR="$conv_dir"
    mkdir -p "$LOOP_GUARD_DIR"
    
    # Action log: action|target|result|timestamp
    LOOP_GUARD_LOG="$LOOP_GUARD_DIR/action_log.txt"
    # State hashes
    LOOP_GUARD_STATES="$LOOP_GUARD_DIR/state_hashes.txt"
    # Blockers detected
    LOOP_GUARD_BLOCKERS="$LOOP_GUARD_DIR/blockers.txt"
    
    : > "$LOOP_GUARD_LOG"
    : > "$LOOP_GUARD_STATES"
    : > "$LOOP_GUARD_BLOCKERS"
    
    echo -e "${GREEN}✅ Loop Guard initialized: $LOOP_GUARD_DIR${NC}"
    echo -e "   Max retries per action: $LOOP_GUARD_MAX_RETRIES"
}

# =============================================================================
# Log a browser action and its result
# =============================================================================
# Args: action_type target_element result [page_title] [url]
# action_type: click | type | scroll | navigate | press_key
# result:      success | no_change | error | page_loaded | timeout
loop_guard_log() {
    local action="$1"
    local target="$2"
    local result="$3"
    local page_title="${4:-unknown}"
    local url="${5:-unknown}"
    local ts
    ts=$(date +%s)
    
    # Append to log
    echo "${action}|${target}|${result}|${page_title}|${url}|${ts}" >> "$LOOP_GUARD_LOG"
    
    # Keep only last N entries
    if [ "$(wc -l < "$LOOP_GUARD_LOG")" -gt "$LOOP_GUARD_HISTORY_SIZE" ]; then
        tail -"$LOOP_GUARD_HISTORY_SIZE" "$LOOP_GUARD_LOG" > "$LOOP_GUARD_LOG.tmp"
        mv "$LOOP_GUARD_LOG.tmp" "$LOOP_GUARD_LOG"
    fi
    
    # Track state hash (page_title + url as simple state fingerprint)
    echo "${page_title}|${url}" >> "$LOOP_GUARD_STATES"
}

# =============================================================================
# Save a DOM/page state hash for comparison
# =============================================================================
loop_guard_save_state() {
    local state_content="$1"  # Any string representing page state
    local hash
    hash=$(echo "$state_content" | md5sum | cut -d' ' -f1)
    echo "$hash|$(date +%s)" >> "$LOOP_GUARD_STATES"
    echo "$hash"
}

# =============================================================================
# Check for loops — THE CORE FUNCTION
# Returns 0 if OK, 1 if loop detected, 2 if state is stuck
# =============================================================================
loop_guard_check() {
    local exit_code=0
    
    if [ ! -f "$LOOP_GUARD_LOG" ] || [ ! -s "$LOOP_GUARD_LOG" ]; then
        echo -e "${GREEN}✅ No actions logged yet${NC}"
        return 0
    fi
    
    echo -e "${CYAN}=== Loop Guard Check ===${NC}"
    
    # ----- Check 1: Same action+target repeated N+ times -----
    local last_n=$LOOP_GUARD_MAX_RETRIES
    local recent_actions
    recent_actions=$(tail -"$last_n" "$LOOP_GUARD_LOG" | cut -d'|' -f1,2 | sort | uniq -c | sort -rn)
    
    while IFS= read -r line; do
        local count action_target
        count=$(echo "$line" | awk '{print $1}')
        action_target=$(echo "$line" | awk '{$1=""; print $0}' | xargs)
        
        if [ "$count" -ge "$last_n" ]; then
            echo ""
            echo -e "${RED}⛔ LOOP DETECTED!${NC}"
            echo -e "   Action '${action_target}' repeated ${count} times in last ${last_n} entries"
            echo ""
            echo -e "${YELLOW}[AI_SYSTEM_HINT]: LOOP DETECTED — MANDATORY STRATEGY CHANGE!${NC}"
            echo "The same action has been attempted $count times without success."
            echo "You MUST NOT retry the same action. Instead, do ONE of:"
            echo "  1. Press Escape to dismiss any popups/modals"
            echo "  2. Scroll the page to reveal hidden elements"
            echo "  3. Check if the element is disabled/hidden"
            echo "  4. Navigate to a different page and come back"
            echo "  5. Use a completely different UI path"
            echo "  6. STOP and report the issue to the user"
            echo ""
            exit_code=1
        fi
    done <<< "$recent_actions"
    
    # ----- Check 2: Consecutive no_change results -----
    local no_change_streak=0
    while IFS='|' read -r action target result _ _ _; do
        if [ "$result" = "no_change" ] || [ "$result" = "error" ] || [ "$result" = "timeout" ]; then
            no_change_streak=$((no_change_streak + 1))
        else
            no_change_streak=0
        fi
    done < <(tail -5 "$LOOP_GUARD_LOG")
    
    if [ "$no_change_streak" -ge 3 ]; then
        echo ""
        echo -e "${RED}⛔ PAGE STUCK! Last $no_change_streak actions had no effect${NC}"
        echo ""
        echo -e "${YELLOW}[AI_SYSTEM_HINT]: PAGE IS UNRESPONSIVE${NC}"
        echo "The page has not changed after $no_change_streak consecutive actions."
        echo "The page is likely stuck, frozen, or has an overlay blocking all interaction."
        echo "MANDATORY: Try refreshing the page or navigating to a known-good URL."
        echo ""
        exit_code=2
    fi
    
    # ----- Check 3: State not changing (same page title+url) -----
    if [ -f "$LOOP_GUARD_STATES" ] && [ "$(wc -l < "$LOOP_GUARD_STATES")" -ge 3 ]; then
        local unique_states
        unique_states=$(tail -5 "$LOOP_GUARD_STATES" | sort -u | wc -l)
        if [ "$unique_states" -le 1 ]; then
            echo -e "${YELLOW}⚠️ Page state hasn't changed in last 5 actions${NC}"
            if [ "$exit_code" -eq 0 ]; then
                exit_code=2
            fi
        fi
    fi
    
    if [ "$exit_code" -eq 0 ]; then
        echo -e "${GREEN}✅ No loop detected — safe to continue${NC}"
    fi
    
    return $exit_code
}

# =============================================================================
# Generate a system hint for the AI based on failure patterns
# =============================================================================
loop_guard_hint() {
    if [ ! -f "$LOOP_GUARD_LOG" ] || [ ! -s "$LOOP_GUARD_LOG" ]; then
        return 0
    fi
    
    local last_entry
    last_entry=$(tail -1 "$LOOP_GUARD_LOG")
    local result
    result=$(echo "$last_entry" | cut -d'|' -f3)
    local target
    target=$(echo "$last_entry" | cut -d'|' -f2)
    
    case "$result" in
        no_change)
            echo ""
            echo "[AI_SYSTEM_HINT]: Last action on '$target' had NO EFFECT."
            echo "Before retrying, check: is the element visible? Is there a popup/overlay?"
            echo "Try pressing Escape first, or scroll to the element."
            ;;
        error)
            echo ""
            echo "[AI_SYSTEM_HINT]: Last action on '$target' caused an ERROR."
            echo "The element may not exist, be detached, or the page may have navigated away."
            echo "Take a fresh screenshot and re-evaluate the page state."
            ;;
        timeout)
            echo ""
            echo "[AI_SYSTEM_HINT]: Last action on '$target' TIMED OUT."
            echo "The page may be loading or the network is slow."
            echo "Wait 3 seconds, then check if the page has finished loading."
            ;;
    esac
}

# =============================================================================
# Show action history (for debugging)
# =============================================================================
loop_guard_report() {
    echo -e "${CYAN}=== Action History ===${NC}"
    
    if [ ! -f "$LOOP_GUARD_LOG" ] || [ ! -s "$LOOP_GUARD_LOG" ]; then
        echo "  (empty)"
        return
    fi
    
    local step=0
    while IFS='|' read -r action target result title url ts; do
        step=$((step + 1))
        local icon="✅"
        [ "$result" = "no_change" ] && icon="⚠️"
        [ "$result" = "error" ] && icon="❌"
        [ "$result" = "timeout" ] && icon="⏳"
        
        echo "  $icon Step $step: $action '$target' → $result"
    done < "$LOOP_GUARD_LOG"
    
    echo ""
    echo "  Total actions: $(wc -l < "$LOOP_GUARD_LOG")"
    echo "  Failures: $(grep -c 'no_change\|error\|timeout' "$LOOP_GUARD_LOG" 2>/dev/null || echo 0)"
}

# =============================================================================
# Reset (clear all tracking)
# =============================================================================
loop_guard_reset() {
    : > "$LOOP_GUARD_LOG" 2>/dev/null
    : > "$LOOP_GUARD_STATES" 2>/dev/null
    : > "$LOOP_GUARD_BLOCKERS" 2>/dev/null
    echo -e "${GREEN}✅ Loop Guard reset${NC}"
}

# =============================================================================
# Cleanup (remove tracking files entirely)
# =============================================================================
loop_guard_cleanup() {
    rm -rf "$LOOP_GUARD_DIR" 2>/dev/null
    echo -e "${GREEN}✅ Loop Guard cleaned up${NC}"
}

# Auto-init if run directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "🔄 Loop Guard — Browser Action Loop Detection"
    echo ""
    echo "Usage: source this file, then call loop_guard_* functions"
    echo ""
    echo "  source scripts/loop_guard.sh"
    echo "  loop_guard_init [tracking_dir]"
    echo "  loop_guard_log click '#btn' success"
    echo "  loop_guard_check  # Returns 0=OK, 1=loop, 2=stuck"
    echo "  loop_guard_report"
    echo "  loop_guard_reset"
    echo ""
    echo "Demo:"
    loop_guard_init "/tmp/loop_guard_demo"
    loop_guard_log "click" "#btn-login" "success" "Login Page" "/login"
    loop_guard_log "click" "#btn-submit" "no_change" "Form Page" "/form"
    loop_guard_log "click" "#btn-submit" "no_change" "Form Page" "/form"
    loop_guard_log "click" "#btn-submit" "no_change" "Form Page" "/form"
    echo ""
    loop_guard_check
    echo ""
    loop_guard_hint
    echo ""
    loop_guard_report
    loop_guard_cleanup
fi
