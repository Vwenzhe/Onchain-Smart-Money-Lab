# Docker 容器方案说明

## 1. 目标

当前项目的 Docker 化目标不是一步到位做复杂编排，而是先把前后端拆开，并补出几个直观、方便使用的容器：

- `frontend`：前端展示容器
- `backend`：后端只读 API 容器
- `price-refresher`：价格刷新任务容器
- `research-pipeline`：研究数据全链路任务容器

这样可以先满足：

- 本地一键启动展示站
- 前后端职责清晰拆分
- 后续接 GitHub Actions / 定时任务更自然
- 未来继续演进到云部署或 Docker Compose 编排更容易

## 2. 容器职责

### 2.1 frontend

职责：

- 提供静态前端页面
- 通过 Nginx 对 `/api` 请求反向代理到 `backend`

特点：

- 用户直接访问这个容器即可看到页面
- 不需要关心后端的内部地址
- 适合作为对外暴露入口

默认端口：

- 宿主机 `4173`
- 容器内部 `80`

### 2.2 backend

职责：

- 运行 FastAPI
- 只读消费 `data/processed` 与 `data/features`
- 提供 `/health` 与 `/api/v1/tokens/{symbol}/page`

特点：

- 不直接做页面渲染
- 不直接执行前端构建
- 不直接承担定时刷新职责

默认端口：

- 宿主机 `8000`
- 容器内部 `8000`

### 2.3 price-refresher

职责：

- 手动执行价格刷新脚本
- 更新 `data/features/token_prices`

默认命令：

```bash
python scripts/fetch_token_prices.py
```

特点：

- 这是按需执行的任务容器
- 跑完即退出
- 更适合作为手动任务或调度任务使用

### 2.4 research-pipeline

职责：

- 执行完整研究数据链路
- 生成 `raw / processed / features / rendered`

默认命令：

```bash
python scripts/run_pipeline.py
```

特点：

- 同样是一次性任务容器
- 跑完即退出
- 适合手动触发或后续挂到调度系统

## 3. 启动方式

### 3.1 启动展示站

确保根目录已有 `.env` 后，执行：

```bash
docker compose up --build -d backend frontend
```

访问：

- 前端页面：`http://127.0.0.1:4173`
- 后端健康检查：`http://127.0.0.1:8000/health`

### 3.2 执行价格刷新

```bash
docker compose --profile jobs run --rm price-refresher
```

### 3.3 执行完整研究链路

```bash
docker compose --profile jobs run --rm research-pipeline
```

## 4. 当前设计要点

### 4.1 为什么前端用 Nginx

因为当前前端请求仍然使用相对路径 `/api/...`，所以在容器部署时最简单的方式就是：

- 前端静态文件由 Nginx 提供
- `/api` 直接反代给 `backend`

这样前端无需知道后端公网地址，也不需要在第一版就引入复杂的运行时环境注入。

### 4.2 为什么任务容器单独拆分

因为当前项目有两类运行模式：

- 持续在线服务
- 一次性数据任务

如果把任务也塞进 `backend` 容器，会让职责混乱。单独拆成 job 容器后：

- 语义更清晰
- 后续接 scheduler 更自然
- 失败隔离更容易

## 5. 当前限制

当前 Docker 方案是“适合展示版和本地部署”的版本，还没有覆盖：

- 生产级反向代理
- HTTPS
- 自动重部署
- 定时任务常驻调度
- 日志与告警收口

因此，当前更适合：

- 本地演示
- 作品集部署准备
- 前后端分离和职责收口

## 6. 一句话总结

当前 Docker 方案已经把项目拆成了：

- 一个对外展示容器
- 一个后端 API 容器
- 两个按需执行的数据任务容器

它不是最终生产架构，但已经是一个清晰、直观、方便继续演进的容器化基线。
