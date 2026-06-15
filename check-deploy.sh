#!/bin/bash

# 基石 Cornerstone - 部署前检查脚本
# 使用方式: ./check-deploy.sh [端口号]
# 示例: ./check-deploy.sh 8080

set -e

echo "=========================================="
echo "  基石 Cornerstone - 部署前检查"
echo "=========================================="

# 默认端口
DEFAULT_PORT=${1:-80}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ $1 未安装，请先安装"
        return 1
    fi
    echo "✅ $1 已安装"
    return 0
}

# 检查端口是否被占用
check_port() {
    local port=$1
    local service_name=$2
    
    if ss -ltnp | grep -E ":${port}\b" &> /dev/null; then
        local pid=$(ss -ltnp | grep -E ":${port}\b" | awk '{print $7}' | cut -d',' -f1 | cut -d'=' -f2)
        local prog=$(ss -ltnp | grep -E ":${port}\b" | awk '{print $7}' | cut -d',' -f2 | cut -d'=' -f2)
        echo "❌ 端口 $port ($service_name) 已被占用"
        if [ -n "$pid" ]; then
            echo "   占用进程: $prog (PID: $pid)"
            echo "   建议: 停止占用服务或修改 .env 中的 HTTP_PORT"
        fi
        return 1
    fi
    echo "✅ 端口 $port ($service_name) 可用"
    return 0
}

echo ""
echo "[系统依赖检查]"
echo "------------"
check_command "docker"
check_command "docker-compose" || check_command "docker compose"
check_command "openssl"

echo ""
echo "[端口占用检查]"
echo "------------"

# 检查前端端口
if ! check_port "$DEFAULT_PORT" "前端服务"; then
    echo ""
    echo "📌 解决方案："
    echo "   1. 修改 .env 文件中的 HTTP_PORT 为其他端口（如 8080）"
    echo "      sed -i 's|^HTTP_PORT=.*|HTTP_PORT=8080|' .env"
    echo "   2. 或停止占用 80 端口的服务（如 Nginx/Apache）"
    echo "      sudo systemctl stop nginx"
    exit 1
fi

# 检查常用端口
check_port "8080" "备用前端端口"
check_port "443" "HTTPS"

echo ""
echo "[环境变量检查]"
echo "------------"

if [ -f ".env" ]; then
    echo "✅ .env 文件存在"
    
    # 检查必要的环境变量
    REQUIRED_VARS=("SECRET_KEY" "POSTGRES_PASSWORD" "INITIAL_ADMIN_PASSWORD")
    MISSING_VARS=()
    
    for var in "${REQUIRED_VARS[@]}"; do
        if ! grep -q "^${var}=" .env; then
            MISSING_VARS+=("$var")
        fi
    done
    
    if [ ${#MISSING_VARS[@]} -eq 0 ]; then
        echo "✅ 所有必要环境变量已配置"
    else
        echo "❌ 缺少必要环境变量: ${MISSING_VARS[*]}"
        echo "   建议运行: cp .env.docker.example .env 并修改配置"
        exit 1
    fi
    
    # 显示当前配置
    echo ""
    echo "📋 当前配置摘要:"
    echo "   HTTP_PORT: $(grep '^HTTP_PORT=' .env | cut -d'=' -f2 || echo "$DEFAULT_PORT")"
    echo "   POSTGRES_DB: $(grep '^POSTGRES_DB=' .env | cut -d'=' -f2 || echo "cornerstone")"
    echo "   CORS_ORIGINS: $(grep '^CORS_ORIGINS=' .env | cut -d'=' -f2 || echo "未设置")"
else
    echo "⚠️  .env 文件不存在"
    echo "   建议运行: cp .env.docker.example .env"
fi

echo ""
echo "[Docker 网络检查]"
echo "------------"
if docker network ls | grep -q "cornerstone-net"; then
    echo "✅ Docker 网络 cornerstone-net 已存在"
else
    echo "✅ Docker 网络 cornerstone-net 将在部署时创建"
fi

echo ""
echo "=========================================="
echo "  ✅ 所有检查通过，可以开始部署!"
echo "=========================================="
echo ""
echo "下一步命令:"
echo "  docker compose up -d --build"
echo ""
echo "访问地址:"
echo "  http://localhost:${DEFAULT_PORT}"
