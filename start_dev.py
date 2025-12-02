import os
import sys
import subprocess
import time
import threading
import signal
import platform

# --- 配置路径 ---
# 获取脚本所在目录作为根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

# 全局进程变量
backend_process = None
frontend_process = None

def install_frontend_deps():
    """检查并安装前端依赖"""
    node_modules_path = os.path.join(FRONTEND_DIR, "node_modules")
    if not os.path.exists(node_modules_path):
        print("📦 [系统] 检测到前端依赖缺失，正在执行 'npm install'...")
        try:
            # 兼容 Windows 和 Linux 的 npm 命令
            npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
            subprocess.check_call([npm_cmd, "install"], cwd=FRONTEND_DIR)
            print("✅ [系统] 前端依赖安装完成！")
        except subprocess.CalledProcessError:
            print("❌ [错误] 前端依赖安装失败，请手动检查。")
            sys.exit(1)
    else:
        print("✅ [系统] 前端依赖已就绪。")

def stream_output(process, prefix, color_code):
    """实时读取子进程输出并打印"""
    if process.stdout is None:
        return
        
    try:
        # 逐行读取输出
        for line in iter(process.stdout.readline, ""):
            if line:
                # 给日志加上颜色和前缀
                print(f"\033[{color_code}m[{prefix}]\033[0m {line.strip()}")
            else:
                break
    except ValueError:
        pass

def stop_services(signum=None, frame=None):
    """优雅关闭所有服务"""
    print("\n🛑 [系统] 正在停止服务...")
    
    # 关闭后端
    if backend_process:
        print("   - 正在关闭后端...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()

    # 关闭前端 (npm 往往会启动子进程，需要特殊处理)
    if frontend_process:
        print("   - 正在关闭前端...")
        if platform.system() == "Windows":
            # Windows 下杀死进程树
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(frontend_process.pid)], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Linux/Mac 下，发送信号给进程组
            try:
                os.killpg(os.getpgid(frontend_process.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass

    print("👋 [系统] 服务已全部关闭。")
    sys.exit(0)

def main():
    global backend_process, frontend_process

    # 1. 检查依赖
    install_frontend_deps()

    # 注册 Ctrl+C 信号处理
    signal.signal(signal.SIGINT, stop_services)
    signal.signal(signal.SIGTERM, stop_services)

    print("🚀 [系统] 正在启动服务...")

    # 2. 启动后端 (FastAPI)
    # 使用 python -m app.main 启动，设置 cwd 为 backend 目录以确保 imports 正常
    print("🐍 [后端] 启动中 (Port 8001)...")
    backend_env = os.environ.copy()
    backend_env["PYTHONUNBUFFERED"] = "1" # 确保日志实时输出
    
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "app.main"],
        cwd=BACKEND_DIR,
        env=backend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1  # 行缓冲
    )
    
    # 启动后端日志监听线程 (绿色前缀)
    threading.Thread(
        target=stream_output, 
        args=(backend_process, "Backend", "32"), 
        daemon=True
    ).start()

    # 3. 启动前端 (Vite)
    print("🎨 [前端] 启动中 (Port 5173)...")
    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
    
    # Linux下使用 preexec_fn=os.setsid 创建进程组，方便后续整体杀掉 npm+vite
    preexec = os.setsid if platform.system() != "Windows" else None
    
    frontend_process = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        preexec_fn=preexec
    )

    # 启动前端日志监听线程 (蓝色前缀)
    threading.Thread(
        target=stream_output, 
        args=(frontend_process, "Frontend", "36"), 
        daemon=True
    ).start()

    print("✨ [系统] 所有服务已启动！按 Ctrl+C 停止。")
    print("-" * 50)

    # 4. 主循环监控
    try:
        while True:
            time.sleep(1)
            # 检查进程是否意外退出
            if backend_process.poll() is not None:
                print("❌ [错误] 后端服务意外退出！")
                stop_services()
            if frontend_process.poll() is not None:
                print("❌ [错误] 前端服务意外退出！")
                stop_services()
    except KeyboardInterrupt:
        stop_services()

if __name__ == "__main__":
    main()