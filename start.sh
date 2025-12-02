#!/bin/bash

# =================配置区域=================
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
# =========================================

# --- 辅助函数: 尝试加载 NVM ---
load_nvm() {
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    if command -v nvm &> /dev/null; then
        # 尝试切换到 Node 20，失败则使用系统默认
        nvm use 20 2>/dev/null || nvm use node 2>/dev/null
    fi
}

# --- 核心函数: 优雅退出 ---
cleanup() {
    echo -e "\n${YELLOW}🛑 正在停止所有服务...${NC}"
    
    # 1. 尝试杀死后端进程及其子进程 (Uvicorn reloader)
    if [ -n "$BACKEND_PID" ]; then
        echo "   - 停止后端 (PID: $BACKEND_PID)..."
        pkill -P "$BACKEND_PID" 2>/dev/null # 杀子进程
        kill "$BACKEND_PID" 2>/dev/null     # 杀父进程
    fi
    
    # 2. 尝试杀死前端进程及其子进程 (Vite)
    if [ -n "$FRONTEND_PID" ]; then
        echo "   - 停止前端 (PID: $FRONTEND_PID)..."
        pkill -P "$FRONTEND_PID" 2>/dev/null # 杀子进程
        kill "$FRONTEND_PID" 2>/dev/null     # 杀父进程
    fi
    
    # 3. 兜底策略: 检查端口是否释放
    sleep 1
    echo "   - 检查端口残留..."
    # 检查 8001 (后端)
    if lsof -i:8001 -t >/dev/null 2>&1; then
        echo "     ! 强制释放端口 8001"
        kill -9 $(lsof -i:8001 -t) 2>/dev/null
    fi
    # 检查 5173 (前端)
    if lsof -i:5173 -t >/dev/null 2>&1; then
        echo "     ! 强制释放端口 5173"
        kill -9 $(lsof -i:5173 -t) 2>/dev/null
    fi

    echo -e "${GREEN}👋 服务已全部关闭${NC}"
    exit 0
}

# 注册信号捕获
trap cleanup SIGINT SIGTERM

# =================主逻辑=================

echo -e "${GREEN}🚀 初始化启动脚本...${NC}"
echo "项目根目录: $ROOT_DIR"

# 0. 加载环境
load_nvm
echo -e "Node 版本: $(node -v)"

# 1. 检测并准备前端环境
echo -e "\n${YELLOW}🔍 [1/3] 检查前端环境...${NC}"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ 错误: 找不到 frontend 目录!${NC}"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${YELLOW}⚠️  未检测到前端依赖，正在自动安装 (npm install)...${NC}"
    cd "$FRONTEND_DIR" || exit
    
    if npm install; then
        echo -e "${GREEN}✅ 前端依赖安装完成${NC}"
    else
        echo -e "${RED}❌ 前端安装失败，请手动检查${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 前端依赖已就绪${NC}"
fi

# 2. 启动后端 (FastAPI)
echo -e "\n${YELLOW}🐍 [2/3] 正在启动后端服务...${NC}"
cd "$BACKEND_DIR" || exit

# 使用 python -m 运行，并放入后台
python3 -m app.main & 
BACKEND_PID=$!

# 稍微等待以检查是否立即崩溃
sleep 2
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✅ 后端已在后台启动 (PID: $BACKEND_PID) | Port: 8001${NC}"
else
    echo -e "${RED}❌ 后端启动失败 (进程已退出)${NC}"
    cleanup
fi

# 3. 启动前端 (Vite)
echo -e "\n${YELLOW}🎨 [3/3] 正在启动前端服务...${NC}"
cd "$FRONTEND_DIR" || exit

npm run dev &
FRONTEND_PID=$!

sleep 2
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✅ 前端已在后台启动 (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}❌ 前端启动失败 (进程已退出)${NC}"
    cleanup
fi

# 4. 等待循环
echo -e "\n${GREEN}✨ 所有服务已启动! 按 Ctrl+C 停止.${NC}"
echo "-----------------------------------------------------"

# 循环等待，直到任一进程退出
while true; do
    sleep 1
    if ! ps -p $BACKEND_PID > /dev/null; then
        echo -e "\n${RED}❌ 后端服务意外退出!${NC}"
        cleanup
    fi
    if ! ps -p $FRONTEND_PID > /dev/null; then
        echo -e "\n${RED}❌ 前端服务意外退出!${NC}"
        cleanup
    fi
done