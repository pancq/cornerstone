#!/bin/bash

# 基石网络管理系统 - 一键启动脚本
# 使用方式:
#   ./start.sh start      - 启动前后端服务
#   ./start.sh restart    - 重启前后端服务
#   ./start.sh stop       - 停止所有服务
#   ./start.sh status     - 查看服务状态

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# 端口配置
BACKEND_PORT=8000
FRONTEND_PORT=5175

# PID文件
BACKEND_PID_FILE="/tmp/cornerstone_backend.pid"
FRONTEND_PID_FILE="/tmp/cornerstone_frontend.pid"

# 日志文件
BACKEND_LOG_FILE="/tmp/cornerstone_backend.log"
FRONTEND_LOG_FILE="/tmp/cornerstone_frontend.log"

echo "=========================================="
echo "  基石网络管理系统 - 服务管理脚本"
echo "=========================================="

stop_services() {
    echo ""
    echo "[停止服务]"
    
    # 停止后端服务
    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE")
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            echo "停止后端服务 (PID: $BACKEND_PID)..."
            kill "$BACKEND_PID" 2>/dev/null
            sleep 2
            if kill -0 "$BACKEND_PID" 2>/dev/null; then
                kill -9 "$BACKEND_PID" 2>/dev/null
            fi
        fi
        rm -f "$BACKEND_PID_FILE"
    fi
    
    # 停止前端服务
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            echo "停止前端服务 (PID: $FRONTEND_PID)..."
            kill "$FRONTEND_PID" 2>/dev/null
            sleep 2
            if kill -0 "$FRONTEND_PID" 2>/dev/null; then
                kill -9 "$FRONTEND_PID" 2>/dev/null
            fi
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi
    
    echo "所有服务已停止"
}

start_backend() {
    echo ""
    echo "[启动后端服务]"
    
    # 检查端口是否被占用
    if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "端口 $BACKEND_PORT 已被占用，尝试停止占用进程..."
        lsof -ti :$BACKEND_PORT | xargs kill -9 2>/dev/null
        sleep 1
    fi
    
    cd "$BACKEND_DIR"
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    echo "启动后端服务 (端口: $BACKEND_PORT)..."
    nohup python -m uvicorn src.main:app --host 0.0.0.0 --port $BACKEND_PORT > "$BACKEND_LOG_FILE" 2>&1 &
    BACKEND_PID=$!
    echo "$BACKEND_PID" > "$BACKEND_PID_FILE"
    
    # 等待启动
    sleep 3
    
    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo "后端服务启动成功 (PID: $BACKEND_PID)"
        echo "日志文件: $BACKEND_LOG_FILE"
    else
        echo "后端服务启动失败!"
        cat "$BACKEND_LOG_FILE"
        exit 1
    fi
}

start_frontend() {
    echo ""
    echo "[启动前端服务]"
    
    # 检查端口是否被占用
    if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "端口 $FRONTEND_PORT 已被占用，尝试停止占用进程..."
        lsof -ti :$FRONTEND_PORT | xargs kill -9 2>/dev/null
        sleep 1
    fi
    
    cd "$FRONTEND_DIR"
    
    echo "启动前端服务 (端口: $FRONTEND_PORT)..."
    nohup npx vite --host 0.0.0.0 --port $FRONTEND_PORT > "$FRONTEND_LOG_FILE" 2>&1 &
    FRONTEND_PID=$!
    echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"
    
    # 等待启动
    sleep 5
    
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo "前端服务启动成功 (PID: $FRONTEND_PID)"
        echo "日志文件: $FRONTEND_LOG_FILE"
    else
        echo "前端服务启动失败!"
        cat "$FRONTEND_LOG_FILE"
        exit 1
    fi
}

show_status() {
    echo ""
    echo "[服务状态]"
    
    # 检查后端服务
    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE")
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            echo "后端服务: 运行中 (PID: $BACKEND_PID, 端口: $BACKEND_PORT)"
        else
            echo "后端服务: 已停止 (PID文件存在但进程不存在)"
            rm -f "$BACKEND_PID_FILE"
        fi
    else
        echo "后端服务: 已停止"
    fi
    
    # 检查前端服务
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            echo "前端服务: 运行中 (PID: $FRONTEND_PID, 端口: $FRONTEND_PORT)"
        else
            echo "前端服务: 已停止 (PID文件存在但进程不存在)"
            rm -f "$FRONTEND_PID_FILE"
        fi
    else
        echo "前端服务: 已停止"
    fi
    
    echo ""
    echo "访问地址:"
    echo "  前端页面: http://localhost:$FRONTEND_PORT"
    echo "  后端API:  http://localhost:$BACKEND_PORT/api/v1"
    echo "  API文档:  http://localhost:$BACKEND_PORT/docs"
}

case "$1" in
    start)
        stop_services
        start_backend
        start_frontend
        show_status
        ;;
    restart)
        stop_services
        start_backend
        start_frontend
        show_status
        ;;
    stop)
        stop_services
        ;;
    status)
        show_status
        ;;
    *)
        echo "使用方式:"
        echo "  ./start.sh start      - 启动前后端服务"
        echo "  ./start.sh restart    - 重启前后端服务"
        echo "  ./start.sh stop       - 停止所有服务"
        echo "  ./start.sh status     - 查看服务状态"
        exit 1
        ;;
esac

echo ""
echo "=========================================="