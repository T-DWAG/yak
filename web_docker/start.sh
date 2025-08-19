#!/bin/bash

echo "牦牛图片相似度分析系统 - Docker版本"
echo "================================="

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker未运行，请先启动Docker"
    exit 1
fi

# 创建数据目录
echo "创建数据目录..."
mkdir -p data/uploads data/results

# 检查模型文件
MODEL_PATH="../runs/classify/train26/weights/best.pt"
if [ ! -f "$MODEL_PATH" ]; then
    echo "警告: 模型文件不存在 ($MODEL_PATH)"
    echo "系统将在无YOLO分类的模式下运行"
fi

# 构建并启动容器
echo "构建Docker镜像..."
docker-compose build

echo "启动容器..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ 服务启动成功!"
    echo "访问地址: http://localhost:5000"
    echo ""
    echo "管理命令:"
    echo "  查看日志: docker-compose logs -f"
    echo "  停止服务: docker-compose down"
    echo "  重启服务: docker-compose restart"
else
    echo "❌ 服务启动失败"
    echo "查看日志: docker-compose logs"
fi