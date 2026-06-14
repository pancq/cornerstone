Set-Location "c:\Users\Administrator\Desktop\trae\基石\基石\backend"
Write-Host "当前目录: $(Get-Location)"
Write-Host "正在启动后端服务..."
py -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload