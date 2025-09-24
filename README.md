```dart

       __       _______..______      .______     ______ 
      |  |     /       ||   _  \     |   _  \   /      |
      |  |    |   (----`|  |_)  |    |  |_)  | |  ,----'
.--.  |  |     \   \    |      /     |   ___/  |  |     
|  `--'  | .----)   |   |  |\  \----.|  |      |  `----.
 \______/  |_______/    | _| `._____|| _|       \______|

```

## 交流平台

为了建立一个更好的 jsrpc 交流平台，我们与猿人学的平哥共同创建了一个微信交流群。  
希望借此机会，帮助广大开发者更深入地了解和使用 jsrpc。

### 加入方式
请使用微信扫描以下二维码并备注“jsrpc”以申请加入我们的交流群。

### 交流群的内容
在这个交流群里，我们将：
- 及时分享 jsrpc 的使用方法和实践案例。
- 发布工具的后续功能更新和版本维护信息。
- 邀请多位长期关注 jsrpc 的技术创作者共同参与内容交流和经验分享。

### 特别资源
群内将提供更多的jsrpc 实操案例 、使用方法 及常见问题 汇总等资料，

欢迎感兴趣的朋友踊跃加入，共同构建一个开放、实用的jsrpc工具交流社区。

<img width="250" alt="王平" src="https://github.com/user-attachments/assets/a9586ac9-a8b7-4322-b3c2-00d2841f6e48" />  

&nbsp; 
&nbsp; 

---
-- js逆向之远程调用(rpc)免去抠代码补环境

> 作者-黑脸怪
- [目录结构](#目录结构)
- [基本介绍](#基本介绍)
- [实现](#实现)
- [食用方法](#食用方法)
  - [打开编译好的文件，开启服务(releases下载)](#打开编译好的文件开启服务releases下载)
  - [注入JS，构建通信环境（/resouces/JsEnv\_De.js）](#注入js构建通信环境resoucesjsenv_dejs)
  - [连接通信](#连接通信)
    - [I 远程调用0：](#i-远程调用0)
      - [接口传js代码让浏览器执行](#接口传js代码让浏览器执行)
    - [Ⅱ 远程调用1： 浏览器预先注册js方法 传递函数名调用](#ⅱ-远程调用1-浏览器预先注册js方法-传递函数名调用)
      - [远程调用1：无参获取值](#远程调用1无参获取值)
      - [远程调用2：带参获取值](#远程调用2带参获取值)
      - [远程调用3：带多个参获 并且使用post方式 取值](#远程调用3带多个参获-并且使用post方式-取值)
      - [远程调用4：获取页面基础信息](#远程调用4获取页面基础信息)



## 目录结构


>  [main.go](https://github.com/jxhczhl/JsRpc/blob/main/main.go) (服务器的主代码)  
>  [resouces/JsEnv_De.js](https://github.com/jxhczhl/JsRpc/blob/main/resouces/JsEnv_Dev.js) (客户端注入js环境)  
>  [config.yaml](https://github.com/jxhczhl/JsRpc/blob/main/config.yaml) (可选配置文件)  


## 基本介绍

运行服务器程序和js脚本 即可让它们通信，实现调用接口执行js获取想要的值(加解密)

## Docker 一体化运行（含浏览器环境）

为便于在无浏览器的环境中直接运行，本仓库新增了 Playwright 浏览器环境适配与镜像构建：

- 基于 Playwright 官方运行时镜像，内置 Chromium/Firefox/WebKit
- 通过 `features/browser/infrastructure/play_client.js` 启动无头浏览器，自动注入 `resouces/JsEnv_Dev.js` 并连接回本服务 `/ws`
- 单一入口 `main.sh` 负责编排：先启动 Go 服务，再启动无头浏览器适配器

构建镜像：

```bash
docker build -t jsrpc:play .
```

运行镜像：

```bash
docker run --rm -p 12080:12080 \
  -e BROWSER=chromium \
  -e HEADLESS=true \
  -e TARGET_URL=https://example.com \
  -e JRPC_GROUP=default \
  --name jsrpc jsrpc:play
```

关键环境变量：

- `BROWSER`：`chromium|firefox|webkit`，默认 `chromium`
- `HEADLESS`：`true|false`，默认 `true`
- `TARGET_URL`：要打开的页面，默认 `about:blank`
- `JRPC_GROUP`：连接 `/ws` 使用的分组名，默认 `default`
- `JRPC_WS_URL`：可直接指定完整的 ws/wss 地址（若设置则覆盖以上 Host/Port/Group）
- `HOST`/`PORT`：当未显式指定 `JRPC_WS_URL` 时，组合 `ws://HOST:PORT/ws?group=...`（默认 `127.0.0.1:12080`）

容器启动后：

- Go 服务监听 `0.0.0.0:12080`
- 无头浏览器在 `TARGET_URL` 打开页面并注入 `Hlclient`，自动连接 `ws://127.0.0.1:12080/ws?group=...`
- 这时可直接调用 `/execjs`、`/go`、`/page/html` 等接口进行远程执行

### 一键启用 wss://（容器内自动 TLS 生成）

如果希望开启 TLS 并通过 wss 访问，可启用内置的自签名证书生成：

```bash
docker run --rm -p 12080:12080 -p 12443:12443 \
  -e TLS_ENABLE=true \
  -e TLS_HOST=localhost \
  -e TLS_PORT=12443 \
  -e TARGET_URL=https://example.com \
  --name jsrpc-wss jsrpc:play
```

- 容器启动时将自动生成证书至 `/app/certs/jsrpc.pem`、`/app/certs/jsrpc.key`
- 运行时配置写入 `/app/runtime-config.yaml` 并开启 `HttpsServices`
- HTTP 服务仍在 `:12080` 监听，HTTPS 在 `:12443`

浏览器侧若要让容器内 Playwright 适配器使用 `wss://` 与服务端通讯（而不是默认的 `ws://`）：

```bash
docker run --rm -p 12080:12080 -p 12443:12443 \
  -e TLS_ENABLE=true \
  -e TLS_HOST=localhost \
  -e TLS_PORT=12443 \
  -e JRPC_CLIENT_PROTO=wss \
  --name jsrpc-wss jsrpc:play
```

注意：容器内自动生成的是自签名证书，真实浏览器直连 `wss://` 时可能因证书不受信导致失败。生产可将已签发证书挂载进容器并指定：

```bash
docker run --rm -p 12080:12080 -p 12443:12443 \
  -e TLS_ENABLE=true \
  -e TLS_HOST=your.domain.com \
  -e TLS_PORT=12443 \
  -e TLS_CERT_PATH=/app/certs/fullchain.pem \
  -e TLS_KEY_PATH=/app/certs/privkey.key \
  -v /path/to/your/fullchain.pem:/app/certs/fullchain.pem:ro \
  -v /path/to/your/privkey.key:/app/certs/privkey.key:ro \
  --name jsrpc-wss jsrpc:play
```

## 生产化 Nginx 反代（TLS 终止）与一键 compose

已在 `Deployments/nginx/` 提供生产可用的 Nginx 配置与一键编排：

1) 准备证书
- 将已签发证书存放到 `Deployments/nginx/certs/`，命名为：
  - `fullchain.pem`
  - `privkey.key`

2) 启动

```bash
cd Deployments/nginx
docker compose up -d --build
```

- 外部访问 `https://<域名或IP>/`；WebSocket 使用 `wss://<域名或IP>/ws`
- Nginx 将流量转发到 `app:12080`，并处理 `/ws` 的 WebSocket 升级

3) 可调参数
- 编辑 `Deployments/nginx/docker-compose.yml` 中 `app.environment`：
  - `BROWSER`、`HEADLESS`、`TARGET_URL`、`JRPC_GROUP`
- 如需调整 Nginx 端口、证书文件名或更多站点配置，修改 `nginx.conf` 与 `conf.d/jrpc.conf`

## 实现

原理：在网站的控制台新建一个WebScoket客户端链接到服务器通信，调用服务器的接口 服务器会发送信息给客户端 客户端接收到要执行的方法执行完js代码后把获得想要的内容发回给服务器 服务器接收到后再显示出来

> 说明：本方法可以https证书且支持wss


## 食用方法

### 打开编译好的文件，开启服务(releases下载)

如图所示

<img width="570" alt="image" src="https://github.com/jxhczhl/JsRpc/assets/41224971/2530274f-33b9-4ccd-8749-6431abea27b2">

[如需更改部分配置，请查看 "其他说明"](#其他说明)  

**api 简介**

- `/list` :查看当前连接的ws服务  (get)
- `/ws`  :浏览器注入ws连接的接口 (ws | wss)
- `/wst`  :ws测试使用-发啥回啥 (ws | wss)
- `/go` :获取数据的接口  (get | post)
- `/execjs` :传递jscode给浏览器执行 (get | post)
- `/page/cookie` :直接获取当前页面的cookie (get)
- `/page/html` :获取当前页面的html (get)

说明：接口用?group分组 如 "ws://127.0.0.1:12080/ws?group={}"
以及可选参数 clientId
clientId说明：以group分组后，如果有注册相同group的 可以传入这个id来区分客户端，如果不传 服务程序会自动生成一个。当访问调用接口时，服务程序随机发送请求到相同group的客户端里。

//注入例子 group可以随便起名(必填)
http://127.0.0.1:12080/go?group={}&action={}&param={} //这是调用的接口
group填写上面注入时候的，action是注册的方法名,param是可选的参数 param可以传string类型或者object类型(会尝试用JSON.parse)

### 注入JS，构建通信环境（[/resouces/JsEnv_De.js](https://github.com/jxhczhl/JsRpc/blob/main/resouces/JsEnv_Dev.js)）

打开JsEnv 复制粘贴到网站控制台(注意：可以在浏览器开启的时候就先注入环境，不要在调试断点时候注入)

![image](https://github.com/jxhczhl/JsRpc/assets/41224971/799fd2ce-28f6-4719-9ff8-e60da57068d7")



### 连接通信

```js
// 注入环境后连接通信
var demo = new Hlclient("ws://127.0.0.1:12080/ws?group=zzz");
// 可选  
//var demo = new Hlclient("ws://127.0.0.1:12080/ws?group=zzz&clientId=hliang/"+new Date().getTime())
```

#### I 远程调用0：

##### 接口传js代码让浏览器执行

浏览器已经连接上通信后 调用execjs接口就行

```python
import requests

js_code = """
(function(){
    console.log("test")
    return "执行成功"
})()
"""

url = "http://localhost:12080/execjs"
data = {
    "group": "zzz",
    "code": js_code
}
res = requests.post(url, data=data)
print(res.text)
```

![image](https://user-images.githubusercontent.com/41224971/165704850-0a22dd7e-68ea-44fe-bda9-608c10795558.png)

#### Ⅱ 远程调用1： 浏览器预先注册js方法 传递函数名调用

##### 远程调用1：无参获取值

```js

// 注册一个方法 第一个参数hello为方法名，
// 第二个参数为函数，resolve里面的值是想要的值(发送到服务器的)
demo.regAction("hello", function (resolve) {
    //这样每次调用就会返回“好困啊+随机整数”
    var Js_sjz = "好困啊"+parseInt(Math.random()*1000);
    resolve(Js_sjz);
})


```

访问接口，获得js端的返回值  
http://127.0.0.1:12080/go?group=zzz&action=hello

![image](https://github.com/jxhczhl/JsRpc/assets/41224971/5f0da051-18f3-49ac-98f8-96f408440475)


##### 远程调用2：带参获取值

```js
//写一个传入字符串，返回base64值的接口(调用内置函数btoa)
demo.regAction("hello2", function (resolve,param) {
    //这样添加了一个param参数，http接口带上它，这里就能获得
    var base666 = btoa(param)
    resolve(base666);
})
```

访问接口，获得js端的返回值
http://127.0.0.1:12080/go?group=zzz&action=hello2&param=123456  

![image](https://github.com/jxhczhl/JsRpc/assets/41224971/91b993ae-7831-4b65-8553-f90e19cc7ebe)


##### 远程调用3：带多个参获 并且使用post方式 取值

```js
//假设有一个函数 需要传递两个参数
function hlg(User,Status){
    return User+"说："+Status;
}

demo.regAction("hello3", function (resolve,param) {
    //这里还是param参数 param里面的key 是先这里写，但到时候传接口就必须对应的上
    res=hlg(param["user"],param["status"])
    resolve(res);
})
```

访问接口，获得js端的返回值

```python
url = "http://127.0.0.1:12080/go"
data = {
    "group": "zzz",
    "action": "hello3",
    "param": json.dumps({"user":"黑脸怪","status":"好困啊"})
}
print(data["param"]) #dumps后就是长这样的字符串{"user": "\u9ed1\u8138\u602a", "status": "\u597d\u56f0\u554a"}
res=requests.post(url, data=data) #这里换get也是可以的
print(res.text)
```

![image](https://github.com/jxhczhl/JsRpc/assets/41224971/5af9bf90-cdfd-4d89-a3c0-a11a54ca7969)


##### 远程调用4：获取页面基础信息

```python
resp = requests.get("http://127.0.0.1:12080/page/html?group=zzz")     # 直接获取当前页面的html
resp = requests.get("http://127.0.0.1:12080/page/cookie?group=zzz")   # 直接获取当前页面的cookie
```


list接口可查看当前注入的客户端信息  
<img width="321" alt="image" src="https://github.com/jxhczhl/JsRpc/assets/41224971/5b2ac7af-f6f0-4569-ac64-553ea41be387">

---
##### 作者是个人开发者，开发和写文档工作量繁重。

##### 如果本项目对您有所帮助，不妨打赏一下 :)


<img width="250" alt="image" src="https://github.com/user-attachments/assets/04420785-ca81-474b-aa19-fc83ca7363a8">
