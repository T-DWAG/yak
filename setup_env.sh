#!/bin/bash

echo "牦牛图片相似度分析系统 - 环境安装"
echo "===================================="

# 检查conda是否安装
if ! command -v conda &> /dev/null; then
    echo "错误: 未检测到conda，请先安装Anaconda或Miniconda"
    echo "下载地址: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo ""
echo "选择安装方式:"
echo "1. 完全复制原环境 (推荐在相同操作系统)"
echo "2. 跨平台安装 (推荐在不同操作系统)"
echo ""
read -p "请选择 (1/2): " choice

case $choice in
    1)
        echo ""
        echo "正在创建完全相同的环境..."
        if ! conda env create -f environment.yml; then
            echo "环境创建失败，尝试方式2..."
            choice=2
        else
            echo "✅ 环境创建成功！"
            exit 0
        fi
        ;;
esac

if [ "$choice" = "2" ]; then
    echo ""
    echo "正在创建跨平台环境..."
    if ! conda env create -f environment-cross-platform.yml; then
        echo "环境创建失败"
        exit 1
    fi
fi

echo ""
echo "✅ 环境创建成功！"
echo ""
echo "激活环境:"
echo "  conda activate yolo11"
echo ""
echo "运行系统:"
echo "  命令行版: python group2.py"
echo "  Web版:    cd web_frontend && python app.py"
echo "  Docker版: cd web_docker && ./start.sh"
echo ""