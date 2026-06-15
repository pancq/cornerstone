# 基石 Cornerstone 部署指南

本文档涵盖基石平台从开发到生产环境的完整部署方案。

## 目录

- [部署架构](#部署架构)
- [开发环境部署](#开发环境部署)
- [生产环境部署（推荐）](#生产环境部署推荐)
- [Docker Compose 部署](#docker-compose-部署)
- [Nginx 反向代理与 HTTPS](#nginx-反向代理与-https)
- [Systemd 进程管理](#systemd-进程管理)
- [数据库迁移](#数据库迁移)
- [备份与恢复](#备份与恢复)
- [升级流程](#升级流程)
- [安全加固](#安全加固)
- [常见故障排查](#常见故障排查)

---

## 部署架构

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Browser    │────▶│    Nginx     │────▶│  Vue 静态文件 │
└──────────────┘     │  (HTTPS:443) │     └──────────────┘
                     │              │
                     │              │     ┌──────────────┐
                     │   /api/*     │────▶│   FastAPI    │
                     └──────────────┘     │ (uvicorn:8000)│
                                          └───────┬──────┘
                                                  │
                            ┌─────────────────────┼─────────────────────┐
                            ▼                     ▼                     ▼
                    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
                    │ PostgreSQL   │     │    Redis     │     │ 网络设备     │
                    │   (5432)     │     │   (6379)     │     │ SSH/SNMP     │
                    └──────────────┘     └──────────────┘     └──────────────┘
```

## 开发环境部署

### 前置要求

| 软件 | 版本 |
|------|------|
| Node.js | ≥ 18 |
| Python | ≥ 3.11 |
| Git | 任意 |

### 步骤

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/cornerstone.git
cd cornerstone

# 2. 配置后端
cd backend
cp .env.example .env
# 编辑 .env，至少设置：
#   SECRET_KEY=<openssl rand -hex 32>
#   INITIAL_ADMIN_PASSWORD=<your-strong-password>
#   DATABASE_URL=sqlite+aiosqlite:///./cornerstone.db
#   DATABASE_URL_SYNC=sqlite:///./cornerstone.db

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install poetry
poetry install

python init_db.py                  # 初始化数据库
uvicorn src.main:app --reload --port 8000

# 3. 启动前端（新终端）
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173，使用 `admin` 与 `INITIAL_ADMIN_PASSWORD` 登录。

---

## 生产环境部署（推荐）

### 服务器规格建议

| 规模 | CPU | 内存 | 磁盘 | 数据库 |
|------|-----|------|------|--------|
| 小型（< 100 设备） | 2 核 | 4 GB | 50 GB | SQLite / PostgreSQL |
| 中型（100~500 设备） | 4 核 | 8 GB | 100 GB | PostgreSQL |
| 大型（> 500 设备） | 8 核 | 16 GB | 200 GB+ | PostgreSQL + Redis |

### 操作系统

推荐 Ubuntu 22.04 LTS / CentOS Stream 9 / Rocky Linux 9。

### 1. 安装系统依赖

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm \
                    postgresql postgresql-contrib redis-server nginx git

# CentOS / Rocky
sudo dnf install -y python3.11 python3.11-pip nodejs npm \
                    postgresql-server postgresql-contrib redis nginx git
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql redis nginx
```

### 2. 创建专用系统用户

```bash
sudo useradd -r -m -s /bin/bash cornerstone
sudo mkdir -p /opt/cornerstone
sudo chown cornerstone:cornerstone /opt/cornerstone
```

### 3. 部署代码

```bash
sudo -u cornerstone -i
cd /opt/cornerstone
git clone https://github.com/your-org/cornerstone.git app
cd app
```

### 4. 配置 PostgreSQL

```bash
sudo -u postgres psql <<EOF
CREATE USER cornerstone WITH PASSWORD '<strong-password>';
CREATE DATABASE cornerstone OWNER cornerstone;
GRANT ALL PRIVILEGES ON DATABASE cornerstone TO cornerstone;
EOF
```

### 5. 后端部署

```bash
cd /opt/cornerstone/app/backend
cp .env.example .env
```

编辑 `.env`：

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://cornerstone:<password>@localhost:5432/cornerstone
DATABASE_URL_SYNC=postgresql://cornerstone:<password>@localhost:5432/cornerstone

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT（务必随机生成）
SECRET_KEY=<openssl rand -hex 32>
ACCESS_TOKEN_EXPIRE_MINUTES=480

# 初始管理员
INITIAL_ADMIN_PASSWORD=<strong-admin-password>

# 凭证加密（留空首次启动自动生成并写入）
CREDENTIAL_SECRET_KEY=

# 备份目录
BACKUP_DIR=/opt/cornerstone/backups

# CORS（替换为实际域名）
CORS_ORIGINS=https://cornerstone.example.com

# 调试模式
DEBUG=false
```

安装并初始化：

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install poetry
poetry install --without dev

mkdir -p /opt/cornerstone/backups
python init_db.py
```

### 6. 前端构建

```bash
cd /opt/cornerstone/app/frontend
npm install
npm run build
# 产物：dist/
```

将 `dist/` 部署到 Nginx 静态目录（见下方 Nginx 章节）。

---

## Docker Compose 部署

> 项目已自带完整的 Docker 部署文件：
> - [`docker-compose.yml`](../docker-compose.yml)
> - [`backend/Dockerfile`](../backend/Dockerfile) + [`backend/docker-entrypoint.sh`](../backend/docker-entrypoint.sh)
> - [`frontend/Dockerfile`](../frontend/Dockerfile) + [`frontend/nginx.conf`](../frontend/nginx.conf)
> - [`.env.docker.example`](../.env.docker.example)

整体结构：

```
┌──────────┐    80/tcp   ┌──────────────────┐
│  Browser │ ──────────▶ │ frontend (nginx) │ ──┐
└──────────┘             └──────────────────┘   │ /api/*
                                                ▼
                          ┌──────────────────────────┐
                          │  backend (FastAPI×4)     │
                          └─────────┬────────────────┘
                                    │
                       ┌────────────┴────────────┐
                       ▼                         ▼
                ┌─────────────┐          ┌─────────────┐
                │ postgres:16 │          │  redis:7    │
                └─────────────┘          └─────────────┘
```

### Rocky Linux 10 一键部署

#### 1. 安装 Docker Engine & Compose Plugin

```bash
# 卸载旧版本（如有）
sudo dnf remove -y docker docker-client docker-client-latest docker-common \
    docker-latest docker-latest-logrotate docker-logrotate docker-engine podman runc

# 添加官方仓库（Rocky 10 兼容 RHEL 9 仓库）
sudo dnf install -y dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo

# 安装
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 启动
sudo systemctl enable --now docker

# 验证
docker --version
docker compose version
```

> 国内服务器加速：编辑 `/etc/docker/daemon.json` 添加镜像加速地址，然后 `sudo systemctl restart docker`。
> ```json
> {
>   "registry-mirrors": ["https://mirror.ccs.tencentyun.com"],
>   "log-driver": "json-file",
>   "log-opts": {"max-size": "10m", "max-file": "3"}
> }
> ```

#### 2. 检查端口占用并放行防火墙

Docker Compose 默认只对宿主机暴露前端端口 `HTTP_PORT`（默认 80）。后端 8000、PostgreSQL 5432、Redis 6379 只在 Docker 内网访问，不暴露到宿主机。

部署前先检查常用端口是否被占用：

```bash
# 查看 80 / 443 / 8080 是否被占用
sudo ss -ltnp | grep -E ':(80|443|8080)\\b' || echo "80/443/8080 未被占用"

# 或查看全部监听端口
sudo ss -ltnp
```

如果 80 已被 Nginx / Apache / 其他服务占用，有两种处理方式：

**方案 A：改用其他端口（推荐先验证）**

```bash
# 将前端暴露到 8080
sed -i 's|^HTTP_PORT=.*|HTTP_PORT=8080|' .env
```

浏览器访问：`http://<服务器IP>:8080`

**方案 B：保留宿主机 Nginx，反向代理到容器端口**

```bash
# Docker 前端监听 8080，宿主机 Nginx 监听 80/443
sed -i 's|^HTTP_PORT=.*|HTTP_PORT=8080|' .env
```

然后按下方「Nginx 反向代理与 HTTPS」章节配置宿主机 Nginx。

防火墙放行：

```bash
# 如果 HTTP_PORT=80
sudo firewall-cmd --permanent --add-service=http

# 如果 HTTP_PORT=8080
sudo firewall-cmd --permanent --add-port=8080/tcp

# 如果启用 HTTPS
sudo firewall-cmd --permanent --add-service=https

sudo firewall-cmd --reload
```

> SELinux：Rocky 10 默认开启。Docker 默认会处理好挂载卷标签，无需关闭。如确需调整：
> ```bash
> sudo setenforce 0           # 临时
> sudo sed -i 's/^SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config  # 永久
> ```

#### 3. 拉取代码并配置环境变量

```bash
sudo mkdir -p /opt/cornerstone
sudo chown $USER:$USER /opt/cornerstone
cd /opt/cornerstone

git clone https://github.com/your-org/cornerstone.git app
cd app

# 复制环境变量模板
cp .env.docker.example .env

# 生成强随机 SECRET_KEY 与初始密码
SECRET=$(openssl rand -hex 32)
ADMIN_PWD=$(openssl rand -base64 18)
DB_PWD=$(openssl rand -base64 18)
CRED_KEY=$(openssl rand -hex 32)

# 写入 .env（手动编辑或用 sed 批量替换）
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET}|" .env
sed -i "s|^INITIAL_ADMIN_PASSWORD=.*|INITIAL_ADMIN_PASSWORD=${ADMIN_PWD}|" .env
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${DB_PWD}|" .env
sed -i "s|^CREDENTIAL_SECRET_KEY=.*|CREDENTIAL_SECRET_KEY=${CRED_KEY}|" .env

echo "管理员初始密码：${ADMIN_PWD}（请妥善保存）"
```

将服务器实际域名 / IP 写入 `CORS_ORIGINS`：

```bash
sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=https://cornerstone.example.com|" .env
```

#### 4. 构建并启动

启动前按 `.env` 中的 `HTTP_PORT` 再检查一次端口：

```bash
HTTP_PORT=$(grep '^HTTP_PORT=' .env | cut -d= -f2)
HTTP_PORT=${HTTP_PORT:-80}
sudo ss -ltnp | grep -E ":${HTTP_PORT}\\b" && echo "端口 ${HTTP_PORT} 已被占用，请修改 .env 中的 HTTP_PORT" && exit 1 || true
```

确认端口空闲后启动：

```bash
# 后台构建并启动全部服务（首次约 3~5 分钟）
docker compose up -d --build

# 查看状态
docker compose ps

# 跟踪日志（Ctrl+C 退出）
docker compose logs -f backend
```

预期输出：

```
NAME                       STATUS              PORTS
cornerstone-backend        Up (healthy)
cornerstone-frontend       Up (healthy)        0.0.0.0:80->80/tcp
cornerstone-postgres       Up (healthy)
cornerstone-redis          Up (healthy)
```

#### 5. 访问验证

```bash
# 健康检查
curl http://<服务器IP>/healthz       # 返回 ok
curl http://<服务器IP>/docs          # FastAPI Swagger
```

浏览器访问：`http://<服务器IP>` ，使用 `admin` + `INITIAL_ADMIN_PASSWORD` 登录。

#### 6. 常用运维命令

```bash
# 查看实时日志
docker compose logs -f --tail=200

# 重启某个服务
docker compose restart backend

# 进入容器
docker compose exec backend bash
docker compose exec postgres psql -U cornerstone

# 停止 / 启动 / 销毁（保留数据卷）
docker compose stop
docker compose start
docker compose down

# 销毁包含数据卷（⚠️ 数据丢失）
docker compose down -v

# 升级
git pull
docker compose up -d --build
```

#### 7. HTTPS（可选）

如需 HTTPS，推荐在 docker-compose 之外用宿主机 Nginx 做 TLS 终结，然后反向代理到容器 80 端口；或在 docker-compose 里再加一个 Caddy / Traefik 容器自动签证书。

最简方案（宿主机 Nginx + Let's Encrypt）：

```bash
# 修改 docker-compose.yml 中 HTTP_PORT，避免与宿主 Nginx 冲突
sed -i 's|HTTP_PORT=80|HTTP_PORT=8080|' .env
docker compose up -d

sudo dnf install -y nginx certbot python3-certbot-nginx
# /etc/nginx/conf.d/cornerstone.conf 见下方"Nginx 反向代理与 HTTPS"章节
sudo certbot --nginx -d cornerstone.example.com
```

#### 8. 数据持久化目录

| 卷名 | 内容 | 备份建议 |
|------|------|---------|
| `cornerstone_postgres_data` | 全部业务数据 | 每日 `pg_dump` 至宿主机 |
| `cornerstone_backend_backups` | 设备配置备份文件 | 每周 tar 打包至对象存储 |
| `cornerstone_redis_data` | Redis AOF | 不重要 |
| `cornerstone_backend_data` | 应用临时数据 | 不重要 |

宿主机备份示例（cron）：

```bash
# /etc/cron.d/cornerstone-backup
0 2 * * * root docker compose -f /opt/cornerstone/app/docker-compose.yml exec -T postgres \
    pg_dump -U cornerstone -F c cornerstone > /opt/cornerstone/db-backup/$(date +\%Y\%m\%d).dump
0 3 * * * root find /opt/cornerstone/db-backup -mtime +30 -delete
```

---

## Nginx 反向代理与 HTTPS

`/etc/nginx/conf.d/cornerstone.conf`：

```nginx
upstream cornerstone_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name cornerstone.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cornerstone.example.com;

    ssl_certificate     /etc/nginx/ssl/cornerstone.crt;
    ssl_certificate_key /etc/nginx/ssl/cornerstone.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 50M;

    # 前端静态资源
    root /opt/cornerstone/app/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://cornerstone_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # API 文档
    location /docs {
        proxy_pass http://cornerstone_backend;
    }
    location /openapi.json {
        proxy_pass http://cornerstone_backend;
    }
}
```

启用配置：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

使用 Let's Encrypt 申请证书：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d cornerstone.example.com
```

---

## Systemd 进程管理

`/etc/systemd/system/cornerstone-backend.service`：

```ini
[Unit]
Description=Cornerstone Backend (FastAPI)
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=simple
User=cornerstone
Group=cornerstone
WorkingDirectory=/opt/cornerstone/app/backend
EnvironmentFile=/opt/cornerstone/app/backend/.env
ExecStart=/opt/cornerstone/app/backend/venv/bin/uvicorn src.main:app \
          --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cornerstone-backend
sudo systemctl status cornerstone-backend
sudo journalctl -u cornerstone-backend -f
```

---

## 数据库迁移

项目使用 Alembic 管理数据库 schema：

```bash
cd /opt/cornerstone/app/backend
source venv/bin/activate

# 查看当前版本
alembic current

# 升级到最新
alembic upgrade head

# 回滚一个版本
alembic downgrade -1

# 生成新迁移（开发时）
alembic revision --autogenerate -m "add_xxx_table"
```

> 首次部署执行 `python init_db.py` 已自动初始化所有表，无需再跑 `alembic upgrade`。

---

## 备份与恢复

### 数据库备份

```bash
# PostgreSQL 备份
pg_dump -h localhost -U cornerstone -d cornerstone -F c -f /backup/cornerstone-$(date +%Y%m%d).dump

# 恢复
pg_restore -h localhost -U cornerstone -d cornerstone -c /backup/cornerstone-20260101.dump
```

### 配置备份目录

定期备份 `BACKUP_DIR`（默认 `/opt/cornerstone/backups`）和 `.env` 文件。

### 自动备份 Cron

```bash
# /etc/cron.d/cornerstone-backup
0 2 * * * cornerstone /usr/bin/pg_dump -F c -f /opt/cornerstone/db-backup/$(date +\%Y\%m\%d).dump cornerstone
0 3 * * * cornerstone find /opt/cornerstone/db-backup -mtime +30 -delete
```

---

## 升级流程

```bash
sudo -u cornerstone -i
cd /opt/cornerstone/app

# 1. 拉取新代码
git pull origin main

# 2. 后端升级
cd backend
source venv/bin/activate
poetry install --without dev
alembic upgrade head

# 3. 前端构建
cd ../frontend
npm install
npm run build

# 4. 重启服务
exit
sudo systemctl restart cornerstone-backend
sudo systemctl reload nginx
```

---

## 安全加固

| 项目 | 建议 |
|------|------|
| `SECRET_KEY` | 32 字节以上随机字符串，使用 `openssl rand -hex 32` 生成 |
| 默认密码 | 首次登录后立即修改 admin 密码 |
| 数据库 | 仅监听 `127.0.0.1`，使用强密码 |
| 防火墙 | 只开放 80/443，禁止 8000 直接暴露 |
| HTTPS | 全站强制 HTTPS，启用 HSTS |
| CORS | `CORS_ORIGINS` 严格设置为业务域名，不要用 `*` |
| 凭证加密 | `CREDENTIAL_SECRET_KEY` 妥善保管，丢失将无法解密设备凭证 |
| 日志保留 | 在「日志设置」配置审计 / 登录日志保留天数与自动清理 |
| 访问控制 | 创建 `operator` / `viewer` 角色，避免共用 admin |
| SSO | 生产环境推荐启用 OAuth2 / SAML，关闭本地登录 |

---

## 常见故障排查

### 1. 登录返回 500

- 检查后端日志：`sudo journalctl -u cornerstone-backend -n 100`
- 常见原因：`bcrypt` 与 `passlib` 版本不兼容。修复：

```bash
pip install "bcrypt==4.0.1"
```

### 2. 前端访问 502 Bad Gateway

- 检查后端是否运行：`sudo systemctl status cornerstone-backend`
- 检查端口监听：`ss -ltn | grep 8000`

### 3. 数据库连接失败

```
sqlalchemy.exc.OperationalError: connection refused
```

- PostgreSQL 是否运行：`sudo systemctl status postgresql`
- 防火墙 / `pg_hba.conf` 是否允许连接
- `.env` 中的连接字符串密码 / 端口是否正确

### 4. 设备配置备份失败

- 在「设备凭证」中检查凭证是否正确
- 确认服务器到设备网络可达：`telnet <device-ip> 22`
- 查看后端日志中 Netmiko 错误堆栈

### 5. AI 功能无响应

- 检查「系统管理 → AI 设置」中 API Key 与 Base URL
- 后端可访问大模型 API（OpenAI / DeepSeek 等）
- 查看后端日志中 `ai_client` 相关错误

### 6. 国际化菜单显示 key（如 `system.logs`）

- 检查 `frontend/src/locales/*.json` 是否存在键名冲突（同名字符串与对象）
- 重新构建前端：`npm run build`
- 清理浏览器缓存

---

如有其他部署问题，请提交 Issue 或参考项目 [README](../README.md)。
