#!/usr/bin/env bash
set -euo pipefail

deploy_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd
}

load_api_env() {
  local root
  root="$(deploy_root)"
  if [[ -f "$root/apps/api/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$root/apps/api/.env"
    set +a
  fi
}

database_url_to_pg() {
  local url="${1:-}"
  url="${url/postgresql+asyncpg/postgresql}"
  printf '%s' "$url"
}

is_local_docker_db() {
  local url="${1:-}"
  [[ "$url" == *"@127.0.0.1:5432/"* || "$url" == *"@localhost:5432/"* ]]
}

docker_compose_file() {
  printf '%s/docker-compose.yml' "$(deploy_root)"
}

docker_postgres_running() {
  local compose_file
  compose_file="$(docker_compose_file)"
  [[ -f "$compose_file" ]] && docker compose -f "$compose_file" ps -q postgres 2>/dev/null | grep -q .
}

require_pg_tools() {
  if command -v pg_dump >/dev/null; then
    return 0
  fi
  if is_local_docker_db "${DATABASE_URL:-}" && docker_postgres_running; then
    return 0
  fi
  echo "pg_dump not found — install PostgreSQL client tools or run pnpm run dev:docker"
  exit 1
}

pg_dump_to_stdout() {
  local pg_url
  pg_url="$(database_url_to_pg "${1:-}")"
  if command -v pg_dump >/dev/null; then
    pg_dump "$pg_url"
    return
  fi
  if is_local_docker_db "$pg_url" && docker_postgres_running; then
    docker compose -f "$(docker_compose_file)" exec -T postgres \
      pg_dump -U doctordesk doctordesk
    return
  fi
  echo "pg_dump not available"
  exit 1
}

psql_from_stdin() {
  local pg_url
  pg_url="$(database_url_to_pg "${1:-}")"
  if command -v psql >/dev/null; then
    psql "$pg_url" --set ON_ERROR_STOP=1
    return
  fi
  if is_local_docker_db "$pg_url" && docker_postgres_running; then
    docker compose -f "$(docker_compose_file)" exec -T postgres \
      psql -U doctordesk -d doctordesk --set ON_ERROR_STOP=1
    return
  fi
  echo "psql not available"
  exit 1
}

load_deploy_env() {
  local target="${1:-dev}"
  local root
  root="$(deploy_root)"
  if [[ -f "$root/scripts/deploy/.env.${target}" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$root/scripts/deploy/.env.${target}"
    set +a
  elif [[ -f "$root/scripts/deploy/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$root/scripts/deploy/.env"
    set +a
  fi
  load_api_env
}

require_deploy_var() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "deploy: set ${name} in scripts/deploy/.env.${DEPLOY_TARGET:-dev} or scripts/deploy/.env"
    echo "See scripts/deploy/.env.example"
    exit 1
  fi
}
