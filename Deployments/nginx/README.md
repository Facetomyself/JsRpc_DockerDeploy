# Nginx TLS 终止与一键 compose

本目录提供开箱即用的 Nginx 反向代理（TLS 终止）与 docker-compose 编排，用于将外部 https/wss 流量安全转发到 JsRpc 应用。

## 目录结构
- `nginx.conf` Nginx 主配置
- `conf.d/jrpc.conf` 服务站点配置（80 重定向到 443；443 处理 TLS 与反代）
- `docker-compose.yml` 一键编排：`app`（JsRpc+Playwright）与 `nginx`
- `certs/` 放置生产证书（挂载到 `nginx` 容器的 `/etc/nginx/certs`）

## 准备证书
将您签发的证书拷贝到 `certs/` 目录并命名为：
- `certs/fullchain.pem`
- `certs/privkey.key`

如需使用其他文件名，请修改 `conf.d/jrpc.conf` 中 `ssl_certificate` 与 `ssl_certificate_key` 路径。

## 启动

在本目录运行：

```bash
docker compose up -d --build
```

启动后：
- 外部访问：`https://<你的域名或IP>/`，WebSocket 使用 `wss://<域名或IP>/ws`
- Nginx 将流量转发到 `app:12080`

## 调整参数
- 修改 `app` 服务环境变量（`docker-compose.yml` 中 `environment`）以定制浏览器行为：
  - `BROWSER`：`chromium|firefox|webkit`
  - `HEADLESS`：`true|false`
  - `TARGET_URL`：无头浏览器打开的页面
  - `JRPC_GROUP`：分组名
- 生产环境建议把 `TARGET_URL` 指向需要注入/交互的站点，或者保持 `about:blank` 并在后续流程中动态导航。

## 说明
- TLS 已在 Nginx 处终止；应用容器的内部浏览器适配器与后端通信默认仍为 `ws://127.0.0.1:12080`，无需在应用容器内启用 TLS。
- `jrpc.conf` 已对 `/ws` 与 `/wst` 路径开启了 WebSocket 升级支持。

