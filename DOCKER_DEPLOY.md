# JsRpc Docker Compose 部署指南

本指南介绍如何使用 Docker Compose 快速部署 JsRpc 服务。

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd JsRpc
```

### 2. 启动服务
```bash
# 构建并启动服务
docker-compose up -d --build

# 查看启动状态
docker-compose ps

# 查看启动日志
docker-compose logs -f jsrpc
```

### 3. 验证服务
```bash
# 运行功能测试
python test_jsrpc.py
```

## 📋 服务配置

### 默认配置
- **HTTP端口**: `30003` (映射到容器内 `12080`)
- **HTTPS端口**: `12443` (当TLS启用时)
- **浏览器**: Chromium (无头模式)
- **目标页面**: https://example.com
- **WebSocket组**: default

### 自定义配置

编辑 `docker-compose.yml` 中的环境变量：

```yaml
environment:
  # 浏览器设置
  - BROWSER=chromium    # chromium/firefox/webkit
  - HEADLESS=true       # true/false
  - TARGET_URL=https://your-target-site.com

  # WebSocket设置
  - JRPC_GROUP=your-group
  - HOST=127.0.0.1
  - PORT=12080
```

## 🔧 高级配置

### 启用 TLS/HTTPS

1. 修改环境变量：
```yaml
environment:
  - TLS_ENABLE=true
  - TLS_HOST=your.domain.com
  - JRPC_CLIENT_PROTO=wss
```

2. 准备证书文件：
```bash
mkdir certs
# 将证书文件放到 certs/ 目录
# - fullchain.pem (完整证书链)
# - privkey.key (私钥)
```

3. 取消 volumes 注释：
```yaml
volumes:
  - ./certs:/app/certs:ro
```

4. 重启服务：
```bash
docker-compose up -d
```

## 🧪 测试功能

运行提供的测试脚本验证所有功能：

```bash
python test_jsrpc.py
```

测试包括：
- ✅ HTTP接口访问
- ✅ WebSocket连接
- ✅ 远程JavaScript执行
- ✅ 页面信息获取
- ✅ 方法调用

## 📚 API 使用

### 基本接口

```bash
# 查看连接的客户端
curl http://localhost:30003/list

# 远程执行JavaScript
curl -X POST http://localhost:30003/execjs \
  -d "group=default&code=console.log('Hello'); return 'success';"

# 获取页面HTML
curl "http://localhost:30003/page/html?group=default"

# 获取页面Cookie
curl "http://localhost:30003/page/cookie?group=default"

# 调用已注册方法
curl "http://localhost:30003/go?group=default&action=your_method&param=data"
```

### WebSocket 连接

```javascript
// 浏览器控制台执行
const client = new Hlclient("ws://localhost:30003/ws?group=default");

// 注册方法
client.regAction("hello", function(resolve, param) {
    resolve("Hello " + param);
});
```

## 🛠️ 管理命令

```bash
# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 更新服务
docker-compose up -d --build

# 清理未使用的镜像
docker image prune -f
```

## 🔍 故障排除

### 服务无法启动
```bash
# 检查容器状态
docker-compose ps

# 查看详细日志
docker-compose logs jsrpc

# 检查端口占用
netstat -tulpn | grep 30003
```

### WebSocket 连接失败
- 确保浏览器已导航到目标页面
- 检查 `TARGET_URL` 是否可访问
- 验证 `JRPC_GROUP` 参数一致

### 功能测试失败
- 确保服务完全启动（等待40秒）
- 检查防火墙设置
- 验证网络连接

## 📁 项目结构

```
JsRpc/
├── Dockerfile              # Docker镜像构建文件
├── docker-compose.yml      # Docker Compose编排文件
├── .dockerignore          # Docker忽略文件
├── test_jsrpc.py          # 功能测试脚本
├── main.go                # Go服务主程序
├── config.yaml            # 配置文件
├── main.sh                # 启动脚本
├── resouces/              # 资源文件
│   ├── JsEnv_Dev.js       # 浏览器端注入脚本
│   └── WeChat_Dev.js      # 微信开发相关
└── features/              # 功能模块
    └── browser/
        └── infrastructure/
            └── play_client.js  # Playwright客户端
```

## 🔐 安全建议

1. **生产环境**:
   - 启用 TLS (`TLS_ENABLE=true`)
   - 使用强密码的证书
   - 定期更新浏览器版本

2. **网络安全**:
   - 限制对外端口访问
   - 使用防火墙规则
   - 定期更新依赖

3. **监控**:
   - 设置日志轮转
   - 监控资源使用
   - 定期备份配置

## 📞 支持

如遇到问题，请：
1. 查看日志：`docker-compose logs jsrpc`
2. 运行测试：`python test_jsrpc.py`
3. 检查网络连接和端口占用
4. 参考 [主README](../README.md) 了解更多细节
