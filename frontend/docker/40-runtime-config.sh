#!/usr/bin/env sh
set -eu

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

cat > /usr/share/nginx/html/runtime-config.js <<EOF
window.__AGENT33_CONFIG__ = {
  API_BASE_URL: "${API_BASE_URL}"
};
EOF
