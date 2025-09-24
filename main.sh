#!/usr/bin/env bash
set -euo pipefail

# Single-entry orchestrator for JsRpc + headless browser (Playwright)
# - Starts the Go RPC server
# - Waits for it to listen
# - Starts the Playwright-based browser adapter to connect via WS

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_PATH="${CONFIG_PATH:-$APP_DIR/config.yaml}"
GO_BIN="${GO_BIN:-$APP_DIR/jsrpc}"

TLS_ENABLE="${TLS_ENABLE:-false}"
TLS_CERT_PATH="${TLS_CERT_PATH:-$APP_DIR/certs/jsrpc.pem}"
TLS_KEY_PATH="${TLS_KEY_PATH:-$APP_DIR/certs/jsrpc.key}"
TLS_PORT="${TLS_PORT:-12443}"
TLS_HOST="${TLS_HOST:-localhost}"

# Prepare runtime config if TLS is enabled
RUNTIME_CONFIG="$CONFIG_PATH"
if [[ "$TLS_ENABLE" == "true" ]];
then
  mkdir -p "$APP_DIR/certs"
  if [[ ! -f "$TLS_CERT_PATH" || ! -f "$TLS_KEY_PATH" ]]; then
    echo "[entry] generating self-signed TLS certificate"
    # CN defaults to TLS_HOST
    openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
      -keyout "$TLS_KEY_PATH" -out "$TLS_CERT_PATH" \
      -subj "/CN=${TLS_HOST}" >/dev/null 2>&1
  fi
  RUNTIME_CONFIG="$APP_DIR/runtime-config.yaml"
  HTTP_PORT="${PORT:-12080}"
  HTTPS_LISTEN="0.0.0.0:${TLS_PORT}"
  HTTPS_HOST_LINE="${TLS_HOST}:${TLS_PORT}"
  cat > "$RUNTIME_CONFIG" <<EOF
BasicListen: "0.0.0.0:${HTTP_PORT}"
HttpsServices:
  IsEnable: true
  HttpsListen: "${HTTPS_LISTEN}"
  HttpsHost: "${HTTPS_HOST_LINE}"
  PemPath: "${TLS_CERT_PATH}"
  KeyPath: "${TLS_KEY_PATH}"
Mode: release
CloseLog: false
CloseWebLog: false
Cors: false
RouterReplace:
  IsEnable: false
  ReplaceRoute: "/"
EOF
  echo "[entry] TLS enabled; runtime config written to: $RUNTIME_CONFIG"
fi

echo "[entry] starting JsRpc server with config: $RUNTIME_CONFIG"
"$GO_BIN" -c "$RUNTIME_CONFIG" &
GO_PID=$!

cleanup() {
  echo "[entry] received signal, stopping..."
  if kill -0 "$GO_PID" 2>/dev/null; then
    kill "$GO_PID" || true
  fi
  if [[ -n "${NODE_PID:-}" ]] && kill -0 "$NODE_PID" 2>/dev/null; then
    kill "$NODE_PID" || true
  fi
  wait || true
}
trap cleanup INT TERM

# Wait for server to listen on port (default 12080) using bash TCP
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-12080}"
echo "[entry] waiting for server ${HOST}:${PORT}"
for i in {1..60}; do
  if exec 3<>"/dev/tcp/${HOST}/${PORT}"; then
    exec 3>&-
    echo "[entry] http is up"
    break
  fi
  sleep 1
done

if [[ "$TLS_ENABLE" == "true" ]]; then
  echo "[entry] waiting for tls ${HOST}:${TLS_PORT}"
  for i in {1..60}; do
    if exec 3<>"/dev/tcp/${HOST}/${TLS_PORT}"; then
      exec 3>&-
      echo "[entry] https is up"
      break
    fi
    sleep 1
  done
fi

echo "[entry] launching Playwright browser adapter"
export JRPC_TLS="$TLS_ENABLE"
export TLS_PORT="$TLS_PORT"
node "$APP_DIR/features/browser/infrastructure/play_client.js" &
NODE_PID=$!

wait "$GO_PID" "$NODE_PID"
