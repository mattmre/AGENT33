#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/engine/docker-compose.yml"
ENV_FILE="${REPO_ROOT}/engine/.env"
COMMAND="${1:-start}"

ensure_env() {
  if [ ! -f "${ENV_FILE}" ]; then
    cp "${REPO_ROOT}/engine/.env.example" "${ENV_FILE}"
    echo "Created engine/.env from .env.example. Rotate secrets before shared use."
  fi
}

case "${COMMAND}" in
  start)
    ensure_env
    docker compose -f "${COMPOSE_FILE}" --profile agent-os up -d \
      postgres redis nats searxng api agent-os
    echo "Agent OS is starting. Open a shell with: scripts/agent-os.sh shell"
    ;;
  shell)
    ensure_env
    docker compose -f "${COMPOSE_FILE}" --profile agent-os exec agent-os bash -l
    ;;
  status)
    docker compose -f "${COMPOSE_FILE}" --profile agent-os ps
    ;;
  logs)
    docker compose -f "${COMPOSE_FILE}" --profile agent-os logs --tail=120 agent-os
    ;;
  stop)
    docker compose -f "${COMPOSE_FILE}" --profile agent-os down
    ;;
  *)
    echo "Usage: scripts/agent-os.sh [start|shell|status|logs|stop]" >&2
    exit 2
    ;;
esac
