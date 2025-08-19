@echo off
echo 牦牛图片相似度分析系统 - Docker版本
echo =================================

:: 检查Docker是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker未运行，请先启动Docker
    pause
    exit /b 1
)

:: 创建数据目录
echo 创建数据目录...
if not exist "data\uploads" mkdir data\uploads
if not exist "data\results" mkdir data\results

:: 检查模型文件
if not exist "..\runs\classify\train26\weights\best.pt" (
    echo 警告: 模型文件不存在
    echo 系统将在无YOLO分类的模式下运行
)

:: 构建并启动容器
echo 构建Docker镜像...
docker-compose build

echo 启动容器...
docker-compose up -d

:: 等待服务启动
echo 等待服务启动...
timeout /t 10 >nul

:: 检查服务状态
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo ❌ 服务启动失败
    echo 查看日志: docker-compose logs
) else (
    echo.
    echo ✅ 服务启动成功!
    echo 访问地址: http://localhost:5000
    echo.
    echo 管理命令:
    echo   查看日志: docker-compose logs -f
    echo   停止服务: docker-compose down
    echo   重启服务: docker-compose restart
)

pause