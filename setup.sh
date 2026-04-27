#!/usr/bin/env bash
#
# Lakebase Workshop — Getting Started
#
# Run this after cloning the repo. It handles everything:
#   1. Installs requirements
#   2. Connects you to your Databricks workspace
#   3. Validates your environment
#   4. Shows you how to get started
#

set -euo pipefail

BOLD="\033[1m"
DIM="\033[2m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RED="\033[31m"
RESET="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROFILE="lakebase-workshop"

banner() {
  echo ""
  echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo -e "${BOLD}${CYAN}  Lakebase Autoscaling Workshop${RESET}"
  echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo ""
}

step() { echo -e "\n${BOLD}${CYAN}▸ $1${RESET}"; }
info() { echo -e "  ${DIM}$1${RESET}"; }
ok()   { echo -e "  ${GREEN}✓ $1${RESET}"; }
warn() { echo -e "  ${YELLOW}⚠ $1${RESET}"; }
fail() { echo -e "  ${RED}✗ $1${RESET}"; exit 1; }
ask()  { echo -en "  ${BOLD}$1${RESET} "; }

banner

# ─────────────────────────────────────────────────────────────────────────────
# 1. Check for Python & pip
# ─────────────────────────────────────────────────────────────────────────────

step "Checking your environment"

if ! command -v python3 &>/dev/null; then
  fail "Python 3 is required but not installed. Install it from https://python.org"
fi
ok "Python $(python3 --version 2>&1 | awk '{print $2}')"

PIP_CMD="pip3"
if ! command -v pip3 &>/dev/null; then
  if command -v pip &>/dev/null; then
    PIP_CMD="pip"
  else
    fail "pip is required but not installed."
  fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# 2. Install requirements
# ─────────────────────────────────────────────────────────────────────────────

step "Python dependencies"
info "The workshop requires: databricks-cli, databricks-sdk, psycopg"
echo ""
ask "Install/update Python requirements now? (Y/n):"
read -r INSTALL_DEPS
INSTALL_DEPS="${INSTALL_DEPS:-Y}"

if [[ "$INSTALL_DEPS" =~ ^[Yy] ]]; then
  echo ""
  $PIP_CMD install -q "databricks-sdk>=0.81.0" "psycopg[binary]>=3.0" 2>&1 | tail -3 || true
  ok "Python packages installed"
else
  info "Skipping. Make sure you have the required packages installed."
fi

# Check for Databricks CLI
if ! command -v databricks &>/dev/null; then
  echo ""
  warn "Databricks CLI is not installed."
  info "Install it:"
  info "  macOS:   brew install databricks/tap/databricks"
  info "  pip:     pip install databricks-cli"
  info "  docs:    https://docs.databricks.com/en/dev-tools/cli/install.html"
  echo ""
  ask "Press Enter once you've installed it, or Ctrl+C to exit..."
  read -r

  if ! command -v databricks &>/dev/null; then
    fail "Databricks CLI still not found. Please install it and re-run this script."
  fi
fi
ok "Databricks CLI $(databricks --version 2>&1 | head -1)"

# ─────────────────────────────────────────────────────────────────────────────
# 3. Connect to workspace
# ─────────────────────────────────────────────────────────────────────────────

step "Connect to your Databricks workspace"

EXISTING=$(databricks auth profiles 2>/dev/null | grep "YES" | head -5 || true)

if [[ -z "$EXISTING" ]]; then
  info "No authenticated workspaces found. Let's connect to one."
fi

if [[ -n "$EXISTING" ]]; then
  echo ""
  info "Found existing authenticated workspaces:"
  echo ""
  echo -e "  ${DIM}Name               Host                                             ${RESET}"
  echo -e "  ${DIM}─────────────────  ─────────────────────────────────────────────────${RESET}"
  databricks auth profiles 2>/dev/null | grep "YES" | while read -r line; do
    echo -e "  ${GREEN}$line${RESET}"
  done
  echo ""
  ask "Use one of these? Enter the profile name, or type NEW to add a workspace:"
  read -r PROFILE_CHOICE

  if [[ "$PROFILE_CHOICE" != "NEW" && "$PROFILE_CHOICE" != "new" && -n "$PROFILE_CHOICE" ]]; then
    PROFILE="$PROFILE_CHOICE"
    WORKSPACE_HOST=$(databricks auth profiles 2>/dev/null | grep "$PROFILE" | awk '{print $2}')
  fi
fi

if [[ "$PROFILE" == "lakebase-workshop" ]] || [[ "${PROFILE_CHOICE:-}" == "NEW" ]] || [[ "${PROFILE_CHOICE:-}" == "new" ]]; then
  echo ""
  ask "Enter your Databricks workspace URL:"
  read -r WORKSPACE_URL
  WORKSPACE_URL="${WORKSPACE_URL%/}"

  if [[ -z "$WORKSPACE_URL" ]]; then
    fail "Workspace URL is required."
  fi

  if [[ ! "$WORKSPACE_URL" =~ ^https:// ]]; then
    WORKSPACE_URL="https://$WORKSPACE_URL"
  fi

  WORKSPACE_HOST="$WORKSPACE_URL"

  ask "Profile name (default: lakebase-workshop):"
  read -r CUSTOM_PROFILE
  [[ -n "$CUSTOM_PROFILE" ]] && PROFILE="$CUSTOM_PROFILE"

  echo ""
  info "Opening your browser to authenticate..."
  info "Log in with your Databricks credentials."
  echo ""
  databricks auth login --host "$WORKSPACE_URL" --profile "$PROFILE"
fi

# Validate
VALID=$(databricks auth profiles 2>/dev/null | grep "$PROFILE" | grep -c "YES" || true)
if [[ "$VALID" -eq 0 ]]; then
  echo ""
  fail "Authentication failed for profile '$PROFILE'. Try running: databricks auth login --host <your-url> --profile $PROFILE"
fi

WORKSPACE_HOST=$(databricks auth profiles 2>/dev/null | grep "$PROFILE" | awk '{print $2}')
ok "Connected to $WORKSPACE_HOST"

# ─────────────────────────────────────────────────────────────────────────────
# 4. Validate Lakebase access
# ─────────────────────────────────────────────────────────────────────────────

step "Validating Lakebase access"

if databricks postgres list-projects --profile "$PROFILE" &>/dev/null; then
  ok "Lakebase Autoscaling is available on this workspace"
else
  warn "Could not verify Lakebase access. This may be a permissions issue,"
  warn "or Lakebase may not be enabled on this workspace."
  info "The workshop requires Lakebase Autoscaling. Contact your workspace admin if needed."
fi

# ─────────────────────────────────────────────────────────────────────────────
# 5. Save config & configure DABs
# ─────────────────────────────────────────────────────────────────────────────

step "Saving configuration"

DAB_YAML="$SCRIPT_DIR/databricks.yml"
python3 -c "
content = open('$DAB_YAML').read()
content = content.replace('<your-profile>', '$PROFILE')
open('$DAB_YAML', 'w').write(content)
" 2>/dev/null || true
ok "databricks.yml configured with profile: $PROFILE"

# Resolve the current user's email for workspace paths (used in later steps)
USER_EMAIL=$(databricks current-user me --profile "$PROFILE" 2>/dev/null \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['userName'])" 2>/dev/null || echo "<your-email>")

WORKSPACE_NOTEBOOK_DIR="/Workspace/Users/${USER_EMAIL}/lakebase-workshop"

# Derive the Lakebase project ID (same logic as notebook 00 and _setup.py)
PROJECT_ID=$(python3 -c "
import re
email = '$USER_EMAIL'
name = email.split('@')[0]
name = re.sub(r'[^a-z0-9-]', '-', name.lower())
name = re.sub(r'-+', '-', name).strip('-')
print(f'lakebase-lab-{name}')
" 2>/dev/null || echo "<your-project-id>")

# Write the project ID into app.yaml
APP_YAML="$SCRIPT_DIR/apps/lakebase-lab-console/app.yaml"
python3 -c "
content = open('$APP_YAML').read()
content = content.replace('<your-project-id>', '$PROJECT_ID')
open('$APP_YAML', 'w').write(content)
" 2>/dev/null || true
ok "app.yaml configured with project ID: $PROJECT_ID"

# Write config file for reference
cat > "$SCRIPT_DIR/.workshop-config" <<EOF
PROFILE=$PROFILE
WORKSPACE_HOST=$WORKSPACE_HOST
PROJECT_ID=$PROJECT_ID
EOF
ok "Config saved to .workshop-config"

# ─────────────────────────────────────────────────────────────────────────────
# 6. Optional: Deploy everything to the workspace
# ─────────────────────────────────────────────────────────────────────────────

step "Deploy to workspace"
info "This deploys notebooks, labs, and the Lab Console app to your workspace"
info "using Databricks Asset Bundles."
echo ""
ask "Deploy now? (Y/n):"
read -r DO_DEPLOY
DO_DEPLOY="${DO_DEPLOY:-Y}"

if [[ "$DO_DEPLOY" =~ ^[Yy] ]]; then
  info "Deploying bundle..."
  if databricks bundle deploy --target dev --profile "$PROFILE"; then
    ok "Deployed to workspace"
    echo ""
    info "Find your content at:"
    info "  /Workspace/Users/${USER_EMAIL}/.bundle/lakebase-workshop/dev/files/"
    echo ""
    info "After running notebook 00, add the postgres resource to the app:"
    info "  Compute → Apps → lakebase-lab-console → Edit → Add Resource → Database"
  else
    warn "Bundle deploy failed. You can retry manually:"
    info "  databricks bundle deploy --target dev --profile $PROFILE"
  fi
else
  info "Skipping deployment. You can deploy later with:"
  info "  databricks bundle deploy --target dev --profile $PROFILE"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 7. Done — show next steps
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}${GREEN}  Workshop Flow${RESET}"
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "  ${BOLD}Step 1: Run the foundation${RESET}"
echo -e "  Open ${BOLD}notebooks/00_Setup_Lakebase_Project${RESET} and click Run All."
echo -e "  This creates your Lakebase project and seeds the demo schema."
echo ""
echo -e "  ${BOLD}Step 2: Pick a lab path${RESET}"
echo -e "  Each path is independent — choose based on your interest:"
echo ""
echo -e "    ${CYAN}1. labs/data-operations/${RESET}         CRUD, JSONB, transactions, advanced SQL"
echo -e "    ${CYAN}2. labs/reverse-etl/${RESET}             Sync Delta tables into Lakebase"
echo -e "    ${CYAN}3. labs/development-experience/${RESET}  Branching, autoscaling, scale-to-zero"
echo -e "    ${CYAN}4. labs/observability/${RESET}           pg_stat views, index analysis, monitoring"
echo -e "    ${CYAN}5. labs/authentication/${RESET}          OAuth tokens, roles, permissions"
echo -e "    ${CYAN}6. labs/backup-recovery/${RESET}         PITR, snapshots, instant restore"
echo -e "    ${CYAN}7. labs/agentic-memory/${RESET}          Persistent AI agent memory"
echo -e "    ${CYAN}8. labs/online-feature-store/${RESET}    Real-time ML feature serving"
echo -e "    ${CYAN}9. labs/app-deployment/${RESET}          Full-stack Lab Console app (capstone)"
echo ""
echo -e "  ${DIM}Workspace:   $WORKSPACE_HOST${RESET}"
echo -e "  ${DIM}Profile:     $PROFILE${RESET}"
echo -e "  ${DIM}Project ID:  $PROJECT_ID${RESET}"
echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
