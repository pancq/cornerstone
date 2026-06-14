import subprocess
import os

# 启动后端服务
backend_proc = subprocess.Popen(
    ['py', '-m', 'uvicorn', 'src.main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'],
    cwd=r'c:\Users\Administrator\Desktop\trae\基石\基石\backend',
    creationflags=subprocess.CREATE_NEW_CONSOLE
)

# 启动前端服务
frontend_proc = subprocess.Popen(
    ['npm', 'run', 'dev'],
    cwd=r'c:\Users\Administrator\Desktop\trae\基石\基石\frontend',
    creationflags=subprocess.CREATE_NEW_CONSOLE
)

print("后端服务 PID:", backend_proc.pid)
print("前端服务 PID:", frontend_proc.pid)
print("服务已启动，按 Ctrl+C 停止")

try:
    backend_proc.wait()
    frontend_proc.wait()
except KeyboardInterrupt:
    backend_proc.terminate()
    frontend_proc.terminate()
    print("服务已停止")
