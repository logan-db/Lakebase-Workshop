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

# Derive the Lakebase project ID and app name (same sanitize logic as notebook 00 and _setup.py)
read -r PROJECT_ID APP_NAME < <(python3 -c "
import re
email = '$USER_EMAIL'
name = email.split('@')[0]
name = re.sub(r'[^a-z0-9-]', '-', name.lower())
name = re.sub(r'-+', '-', name).strip('-')
project_id = f'lakebase-lab-{name}'
app_name = f'lakebase-lab-{name}'
if len(app_name) > 30:
    app_name = app_name[:30].rstrip('-')
print(project_id, app_name)
" 2>/dev/null || echo "<your-project-id> <your-app-name>")

# Write the resolved app name into databricks.yml so it always fits the 30-char limit
python3 -c "
import re
path = '$DAB_YAML'
content = open(path).read()
# Only replace the app 'name:' line (indented under the app resource), not source_code_path
content = re.sub(
    r'(^\s+name:)\s*lakebase-lab-\S+',
    r'\1 $APP_NAME',
    content,
    count=1,
    flags=re.MULTILINE
)
open(path, 'w').write(content)
" 2>/dev/null || true
ok "App name: $APP_NAME (${#APP_NAME} chars)"

# Patch app.yaml with the resolved project ID so the app always knows its project
APP_YAML="$SCRIPT_DIR/apps/lakebase-lab-console/app.yaml"
if [[ -f "$APP_YAML" ]]; then
  python3 -c "
import re
content = open('$APP_YAML').read()
# Replace placeholder or any previous project ID on the LAKEBASE_PROJECT_ID line
content = re.sub(
    r'(name:\s*LAKEBASE_PROJECT_ID\s*\n\s*value:\s*\")([^\"]*)(\")',
    r'\g<1>$PROJECT_ID\3',
    content
)
open('$APP_YAML', 'w').write(content)
" 2>/dev/null || true
  ok "app.yaml configured with project: $PROJECT_ID"
fi

# Write config file for reference
cat > "$SCRIPT_DIR/.workshop-config" <<EOF
PROFILE=$PROFILE
WORKSPACE_HOST=$WORKSPACE_HOST
PROJECT_ID=$PROJECT_ID
APP_NAME=$APP_NAME
EOF
ok "Config saved to .workshop-config"

# ─────────────────────────────────────────────────────────────────────────────
# 6. Deploy to workspace
# ─────────────────────────────────────────────────────────────────────────────

DEPLOYED_APP=false

step "Deploy to workspace"
info "What would you like to deploy?"
echo ""
echo -e "    ${BOLD}1)${RESET} Labs only      — notebooks and lab files (no app compute)"
echo -e "    ${BOLD}2)${RESET} Labs + App     — everything, including the Lab Console app"
echo ""
ask "Choice (1/2):"
read -r DEPLOY_CHOICE
DEPLOY_CHOICE="${DEPLOY_CHOICE:-1}"

if [[ "$DEPLOY_CHOICE" == "2" ]]; then
  FRONTEND_DIR="$SCRIPT_DIR/apps/lakebase-lab-console/frontend"
  if [[ -f "$FRONTEND_DIR/package.json" ]]; then
    if command -v npm &>/dev/null; then
      info "Building frontend..."
      (cd "$FRONTEND_DIR" && npm install --silent && npm run build --silent) 2>&1 | tail -3 || true
      if [[ -f "$FRONTEND_DIR/dist/index.html" ]]; then
        ok "Frontend built"
      else
        warn "Frontend build may have failed — the app will run without a UI"
      fi
    else
      warn "npm not found — skipping frontend build"
      info "Install Node.js to build the frontend: https://nodejs.org"
    fi
  fi
fi

reattach_lakebase_resource() {
  # Bundle deploy uses Terraform which clears API-added app resources and
  # revokes the SP's PostgreSQL grants. Re-attach and re-grant if the project exists.
  DB_NAME=$(databricks api get "/api/2.0/postgres/projects/${PROJECT_ID}/branches/production/databases" \
    --profile "$PROFILE" 2>/dev/null \
    | python3 -c "
import sys, json
data = json.load(sys.stdin)
dbs = data.get('databases', data) if isinstance(data, dict) else data
for db in (dbs if isinstance(dbs, list) else [dbs]):
    status = db.get('status', {})
    if status.get('postgres_database') == 'databricks_postgres':
        print(db['name'])
        break
" 2>/dev/null || true)

  if [[ -n "$DB_NAME" ]]; then
    BRANCH_NAME="projects/${PROJECT_ID}/branches/production"
    databricks api patch "/api/2.0/apps/${APP_NAME}" --profile "$PROFILE" --json "{
      \"resources\": [{
        \"name\": \"lakebase-db\",
        \"postgres\": {
          \"branch\": \"${BRANCH_NAME}\",
          \"database\": \"${DB_NAME}\",
          \"permission\": \"CAN_CONNECT_AND_CREATE\"
        }
      }]
    }" &>/dev/null && ok "Lakebase database attached to app" \
                   || info "Database will be attached when you run notebook 00"

    # Re-grant schema access to the app's service principal
    SP_CLIENT_ID=$(databricks apps get "$APP_NAME" --profile "$PROFILE" -o json 2>/dev/null \
      | python3 -c "import sys,json; print(json.load(sys.stdin).get('service_principal_client_id',''))" 2>/dev/null || true)
    PG_SCHEMA="${PROJECT_ID//-/_}"

    if [[ -n "$SP_CLIENT_ID" ]] && command -v psql &>/dev/null; then
      PG_TOKEN=$(databricks postgres generate-database-credential \
        "projects/${PROJECT_ID}/branches/production/endpoints/primary" \
        --profile "$PROFILE" -o json 2>/dev/null \
        | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])" 2>/dev/null || true)
      PG_HOST=$(databricks api get \
        "/api/2.0/postgres/projects/${PROJECT_ID}/branches/production/endpoints/primary" \
        --profile "$PROFILE" 2>/dev/null \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',{}).get('hosts',{}).get('host',''))" 2>/dev/null || true)

      if [[ -n "$PG_TOKEN" && -n "$PG_HOST" ]]; then
        PGPASSWORD="$PG_TOKEN" psql "host=$PG_HOST dbname=databricks_postgres user=$USER_EMAIL sslmode=require" -q -c "
          GRANT USAGE, CREATE ON SCHEMA $PG_SCHEMA TO \"$SP_CLIENT_ID\";
          GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA $PG_SCHEMA TO \"$SP_CLIENT_ID\";
          GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA $PG_SCHEMA TO \"$SP_CLIENT_ID\";
          ALTER DEFAULT PRIVILEGES IN SCHEMA $PG_SCHEMA GRANT ALL ON TABLES TO \"$SP_CLIENT_ID\";
          ALTER DEFAULT PRIVILEGES IN SCHEMA $PG_SCHEMA GRANT ALL ON SEQUENCES TO \"$SP_CLIENT_ID\";
        " &>/dev/null && ok "Schema access granted to app service principal" \
                       || info "Run notebook 00 to grant schema access to the app"
      fi
    fi
  else
    info "No Lakebase project yet — run notebook 00 to create it and attach the database"
  fi
}

info "Deploying bundle..."
if databricks bundle deploy --target dev --profile "$PROFILE"; then
  ok "Deployed to workspace"
  echo ""
  info "Find your content at:"
  info "  /Workspace/Users/${USER_EMAIL}/.bundle/lakebase-workshop/dev/files/"

  # Re-attach Lakebase resource (bundle deploy clears it via Terraform)
  reattach_lakebase_resource

  if [[ "$DEPLOY_CHOICE" == "2" ]]; then
    echo ""
    info "Starting app and deploying source code..."
    if databricks bundle run lakebase_lab_console --target dev --profile "$PROFILE"; then
      ok "App deployed and running"
      DEPLOYED_APP=true
    else
      warn "App deploy failed — you can deploy later with:"
      info "  databricks bundle run lakebase_lab_console --target dev --profile $PROFILE"
    fi
  fi
else
  warn "Bundle deploy failed. You can retry manually:"
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
echo -e "  This creates your Lakebase project and seeds your user schema."
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
if [[ "$DEPLOYED_APP" == "true" ]]; then
  echo -e "  ${DIM}App:         $APP_NAME (running)${RESET}"
else
  echo -e "  ${DIM}App:         not deployed — deploy later with:${RESET}"
  echo -e "  ${DIM}             databricks bundle run lakebase_lab_console --target dev --profile $PROFILE${RESET}"
fi
echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
