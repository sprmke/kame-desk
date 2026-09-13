#!/usr/bin/env bash
# Shared prod-deploy guard for Cursor + Claude Code + OpenCode shell hooks.
# Source this file; do not execute directly.

PROD_DEPLOY_UNLOCK_WORD="deskwave"

prod_deploy_is_unlocked() {
  local cmd="$1"
  local lower_cmd
  lower_cmd=$(printf '%s' "$cmd" | tr '[:upper:]' '[:lower:]')
  [[ "$lower_cmd" == *"${PROD_DEPLOY_UNLOCK_WORD}"* ]]
}

prod_deploy_is_blocked() {
  local cmd="$1"

  if prod_deploy_is_unlocked "$cmd"; then
    return 1
  fi

  case "$cmd" in
    *deploy:api:dev*|*deploy:web:dev*|*deploy-api.sh" dev"*|*deploy-web.sh" dev"*)
      return 1
      ;;
    *migrate:dev*|*migrate-remote.sh" dev"*)
      return 1
      ;;
    *backup:db:*|*backup-db.sh*)
      return 1
      ;;
    *rollback:db:dev*|*rollback-db.sh" dev"*)
      return 1
      ;;
    *env:status*|*env-status.sh*)
      return 1
      ;;
  esac

  case "$cmd" in
    *deploy:api:prod*|*deploy:web:prod*|*deploy-api.sh" prod"*|*deploy-web.sh" prod"*)
      return 0
      ;;
    *migrate:prod*|*migrate-remote.sh" prod"*)
      return 0
      ;;
    *rollback:db:prod*|*rollback-db.sh" prod"*)
      return 0
      ;;
    *alembic*upgrade*|*"alembic upgrade"*)
      if [[ "$cmd" == *"neon.tech"* || "$cmd" == *"migrate:prod"* || "$cmd" == *"migrate-remote"* ]]; then
        return 0
      fi
      return 1
      ;;
    *"--db-url"*)
      [[ "$cmd" == *"127.0.0.1"* || "$cmd" == *"localhost"* || "$cmd" == *":5432"* ]] && return 1
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

prod_deploy_block_reason() {
  cat <<EOF
Blocked: this command can change production API, web, or remote Neon database state.

DoctorDesk develops on branches with production untouched until the team explicitly approves deploy.

To authorize for this shell command only, the user must say the unlock word "${PROD_DEPLOY_UNLOCK_WORD}" in chat, then rerun with that word in the command (e.g. DESKWAVE=${PROD_DEPLOY_UNLOCK_WORD} pnpm run deploy:api:prod).

Safe without unlock: local docker compose, db:migrate against local Postgres, dev deploy scripts, backups, dev rollback, env:status.
EOF
}
