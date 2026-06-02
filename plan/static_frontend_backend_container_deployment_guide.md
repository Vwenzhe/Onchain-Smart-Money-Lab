# 前端静态托管 + 后端单独容器部署指南

## 1. 文档目的

本文档用于说明当前项目如何采用“前端静态托管 + 后端单独容器”的方式完成部署。

这套方案适用于当前项目的实际特点：

- 前端是展示型页面，适合静态托管
- 后端是只读 FastAPI，适合单独容器运行
- 数据通过离线工作流生成，不需要用户实时触发刷新
- 项目当前目标是作品集展示与研究展示，不是重型高并发生产系统

## 2. 推荐部署结构

当前最推荐的部署结构如下：

- 前端：部署到静态托管平台，例如 `Vercel`
- 后端：部署到一台 Linux 服务器，以 Docker 容器运行 FastAPI
- 域名：
  - 前端使用主域名，例如 `onchainpulse.example.com`
  - 后端使用 API 子域名，例如 `api.onchainpulse.example.com`

推荐访问链路：

```text
Browser
-> https://onchainpulse.example.com
-> /api/...
-> 静态托管平台 rewrite / proxy
-> https://api.onchainpulse.example.com
-> FastAPI backend container
```

## 3. 为什么这套方案适合当前项目

### 3.1 前端适合静态托管

当前前端是 React + Vite 构建产物，本质是静态文件，适合部署到：

- Vercel
- Netlify
- Cloudflare Pages

优势：

- 部署简单
- 自动构建方便
- 适合作品集展示
- 不需要在服务器上运行 Node 常驻服务

### 3.2 后端适合单独容器

当前后端是只读 FastAPI，职责是：

- 读取 `data/processed`
- 读取 `data/features`
- 聚合为页面接口
- 提供 `/health` 和 `/api/v1/tokens/{symbol}/page`

它不负责：

- 在线跑 Dune
- 在线调用 LLM
- 在线生成研究数据

因此，后端非常适合单独容器化部署。

### 3.3 与当前代码结构一致

当前项目已经具备以下部署基础：

- 已有后端容器定义：`Dockerfile.backend`
- 已有 backend 服务编排：`docker-compose.yml`
- 已有前端静态构建能力：`frontend/Dockerfile`
- 已有健康检查接口：`/health`
- 已有前端相对路径 API 请求：`/api/v1/...`

这意味着项目已经可以平滑过渡到该部署模式。

## 4. 部署前准备

部署前建议先准备以下内容。

### 4.1 必备资源

- 一台 Linux 服务器，推荐 Ubuntu 22.04
- 一个可配置 DNS 的域名
- 一个 GitHub 仓库
- 前端静态托管平台账号，例如 Vercel

### 4.2 推荐域名规划

建议从一开始就拆分前后端域名：

- 前端：`onchainpulse.example.com`
- 后端：`api.onchainpulse.example.com`

这样后续更容易：

- 配置 HTTPS
- 管理前后端访问边界
- 配置 GitHub Actions 自动部署
- 独立排查问题

### 4.3 线上环境变量

后端部署前，需要准备线上 `.env` 文件。

至少需要确认以下变量存在：

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

DUNE_API_KEY=your_key
DUNE_BASE_URL=https://api.dune.com/api/v1

COINGECKO_API_KEY=your_key
COINGECKO_API_PLAN=auto
```

如果项目后续新增其他环境变量，也应统一写入同一份线上 `.env`。

## 5. 后端部署步骤

后端建议优先部署，因为前端最终要依赖它的 API 域名。

### 5.1 登录服务器并安装基础依赖

```bash
sudo apt update
sudo apt install -y git curl ca-certificates gnupg nginx
```

### 5.2 安装 Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

安装完成后检查：

```bash
docker --version
docker compose version
```

### 5.3 创建项目目录并拉取仓库

建议统一把项目放在固定目录，例如：

```bash
sudo mkdir -p /opt/onchain-pulse
sudo chown -R $USER:$USER /opt/onchain-pulse
cd /opt/onchain-pulse
git clone <your-repository-url> .
```

### 5.4 创建线上 `.env`

```bash
cd /opt/onchain-pulse
nano .env
```

填入真实环境变量内容，例如：

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_real_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

DUNE_API_KEY=your_real_key
DUNE_BASE_URL=https://api.dune.com/api/v1

COINGECKO_API_KEY=your_real_key
COINGECKO_API_PLAN=auto
```

### 5.5 启动后端容器

当前推荐只启动 backend：

```bash
cd /opt/onchain-pulse
docker compose up --build -d backend
```

查看运行状态：

```bash
docker compose ps
docker compose logs backend --tail=100
```

### 5.6 验证后端健康状态

先在服务器本机检查：

```bash
curl http://127.0.0.1:8000/health
```

预期返回：

```json
{"status":"ok"}
```

再检查核心接口：

```bash
curl http://127.0.0.1:8000/api/v1/tokens/fet/page
```

如果返回结构化 JSON，说明 FastAPI 已正常工作。

## 6. 使用 Nginx 暴露后端 API

后端容器本身只监听服务器本机端口，建议通过 Nginx 暴露到外部域名。

### 6.1 新建 Nginx 配置

```bash
sudo nano /etc/nginx/sites-available/onchainpulse-api
```

写入：

```nginx
server {
    listen 80;
    server_name api.onchainpulse.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6.2 启用配置

```bash
sudo ln -s /etc/nginx/sites-available/onchainpulse-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6.3 配置 HTTPS

建议用 Certbot：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.onchainpulse.example.com
```

完成后检查：

```bash
curl https://api.onchainpulse.example.com/health
```

## 7. 前端静态托管步骤

前端建议部署到 Vercel。当前前端是静态构建项目，不需要单独常驻 Node 进程。

### 7.1 当前前端 API 访问特点

当前前端请求接口的方式是相对路径：

```text
/api/v1/tokens/{token_symbol}/page
```

这意味着：

- 本地开发时通过 Vite proxy 访问本地 FastAPI
- 线上静态部署时，必须配置平台 rewrite，把 `/api/*` 转发到你的后端域名

### 7.2 在 Vercel 导入项目

在 Vercel 中：

1. 选择 `Add New Project`
2. 连接 GitHub 仓库
3. 导入当前项目

构建参数建议：

- Framework Preset：`Vite`
- Root Directory：`frontend`
- Build Command：`npm run build`
- Output Directory：`dist`
- Node Version：`20`

### 7.3 绑定前端域名

建议绑定：

- `onchainpulse.example.com`

也可以根据实际情况使用：

- `www.onchainpulse.example.com`

### 7.4 配置 Rewrite / Proxy

因为前端当前请求的是 `/api/...`，所以必须在静态托管平台上做 rewrite。

逻辑如下：

```text
/api/(.*) -> https://api.onchainpulse.example.com/api/$1
```

如果使用 `vercel.json`，可参考：

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://api.onchainpulse.example.com/api/:path*"
    }
  ]
}
```

这样浏览器访问前端时：

- 页面本身由 Vercel 返回
- `/api/...` 请求由 Vercel 转发到你的后端 API

### 7.5 触发上线

完成上述设置后，Vercel 会自动执行构建并部署。

部署成功后，访问：

- `https://onchainpulse.example.com`

## 8. 上线后联调检查

部署完成后，必须执行完整联调，不要只看“构建成功”。

### 8.1 后端检查

检查：

- `https://api.onchainpulse.example.com/health`
- `https://api.onchainpulse.example.com/api/v1/tokens/fet/page`

确认：

- 服务可访问
- 返回结构正常
- 没有 500 报错

### 8.2 前端检查

打开：

- 首页
- FET 页面
- ETH 页面
- PEPE 页面
- 详细仓位页

检查内容：

- 页面样式是否正常
- 首页三币入口是否可点击
- 二层页面是否成功加载
- 三层页面是否成功加载
- 价格与时间是否展示正常
- 北京时间是否正确
- AI 总结和研究结论是否显示
- Dune 外链是否正常

### 8.3 浏览器网络检查

打开浏览器开发者工具，检查 `/api/...` 请求：

- `200`：正常
- `404`：通常是 rewrite 规则错误
- `502 / 504`：通常是后端未正常运行或 Nginx 反代异常
- `403 / SSL 错误`：通常是域名或 HTTPS 配置问题

## 9. 日常更新操作

### 9.1 后端代码更新

如果后端代码有更新，在服务器上执行：

```bash
cd /opt/onchain-pulse
git pull origin main
docker compose up --build -d backend
docker compose logs backend --tail=100
```

### 9.2 前端代码更新

如果前端代码有更新：

- 推送到 GitHub
- Vercel 自动触发重新构建

### 9.3 数据更新

如果只是数据更新，而后端代码未变化：

- 更新服务器项目目录中的 `data/`
- backend 因为使用挂载目录，通常无需重建镜像

如需稳妥刷新一次：

```bash
docker compose restart backend
```

## 10. 推荐的 GitHub Actions 分工

在这套部署模式下，推荐这样分工：

- `test.yml`
  - 负责测试与基础构建检查
- `refresh-prices.yml`
  - 负责每小时价格刷新
- `refresh-research-data.yml`
  - 负责每日研究数据刷新
- `deploy-backend.yml`
  - 负责后端自动部署到服务器

前端如果使用 Vercel，则通常不需要额外写 GitHub Actions 来部署前端，因为 Vercel 已自带 GitHub 自动部署能力。

## 11. 当前最需要注意的事项

### 11.1 CORS 仍需收口

当前后端如果仍使用全开放 CORS，只适合本地开发。

正式上线时建议：

- 只允许你的前端域名访问
- 或通过前端托管平台 rewrite 减少跨域暴露面

### 11.2 当前前端依赖 `/api` 转发

这意味着前端上线后不能直接裸部署，而必须确保：

- 静态托管平台支持 rewrite
- rewrite 指向正确的 API 域名

### 11.3 数据刷新与页面服务必须分离

页面服务只应该读取已生成的数据，不应该在用户访问页面时触发：

- Dune 查询
- LLM 生成
- 价格抓取

这也是当前项目“所有用户看到同一份发布结果”的核心原则。

## 12. 推荐执行顺序

建议按以下顺序部署：

1. 准备服务器
2. 安装 Docker、Nginx
3. 拉取仓库
4. 写入线上 `.env`
5. 启动 backend 容器
6. 配置 Nginx 和 HTTPS
7. 验证 API 域名
8. 在 Vercel 导入前端
9. 配置前端域名
10. 配置 `/api` rewrite
11. 打开前端页面联调验证
12. 最后再接 GitHub Actions 自动部署

## 13. 一句话总结

当前项目采用“前端静态托管 + 后端单独容器”的方式部署是完全可行的。对这个项目来说，关键不在于引入更复杂的平台，而在于先把：

- 后端 API 独立稳定运行
- 前端静态站正确转发 `/api`
- 数据刷新链与页面服务链彻底分离

这三件事做好。完成后，你的项目就已经具备了稳定的展示型部署基础。
