#
# Multi-stage image for JsRpc with a Playwright browser environment.
# Stage 1: build Go server
FROM golang:1.22-bullseye AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/jsrpc .

# Stage 2: runtime with browsers (Playwright maintained image)
FROM mcr.microsoft.com/playwright:v1.55.1-jammy
WORKDIR /app

# Install Playwright for Node.js
RUN npm install playwright

# Copy server binary and app files
COPY --from=builder /out/jsrpc /app/jsrpc
COPY config.yaml /app/config.yaml
COPY main.sh /app/main.sh
COPY resouces /app/resouces
COPY features/browser/infrastructure/play_client.js /app/features/browser/infrastructure/play_client.js

RUN chmod +x /app/main.sh

# Defaults: chromium headless, listen on 0.0.0.0:12080
ENV BROWSER=chromium \
    HEADLESS=true \
    TARGET_URL=about:blank \
    HOST=127.0.0.1 \
    PORT=12080 \
    JRPC_GROUP=default \
    TLS_ENABLE=false \
    TLS_PORT=12443 \
    TLS_HOST=localhost \
    JRPC_CLIENT_PROTO=ws

# Ports: http and optional https
EXPOSE 12080 12443

ENTRYPOINT ["/app/main.sh"]
