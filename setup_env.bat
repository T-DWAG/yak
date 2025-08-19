@echo off
echo 牦牛图片相似度分析系统 - 环境安装
echo ====================================

echo 检查conda是否安装...
conda --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未检测到conda，请先安装Anaconda或Miniconda
    echo 下载地址: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

echo.
echo 选择安装方式:
echo 1. 完全复制原环境 (推荐在相同操作系统)
echo 2. 跨平台安装 (推荐在不同操作系统)
echo.
set /p choice="请选择 (1/2): "

if "%choice%"=="1" (
    echo.
    echo 正在创建完全相同的环境...
    conda env create -f environment.yml
    if errorlevel 1 (
        echo 环境创建失败，尝试方式2...
        goto cross_platform
    )
    goto success
)

:cross_platform
echo.
echo 正在创建跨平台环境...
conda env create -f environment-cross-platform.yml
if errorlevel 1 (
    echo 环境创建失败
    pause
    exit /b 1
)

:success
echo.
echo ✅ 环境创建成功！
echo.
echo 激活环境:
echo   conda activate yolo11
echo.
echo 运行系统:
echo   命令行版: python group2.py
echo   Web版:    cd web_frontend && python app.py
echo   Docker版: cd web_docker && start.bat
echo.
pause