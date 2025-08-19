# 牦牛图片相似度分析系统

基于 YOLO 分类和感知哈希的智能图片分组系统。自动识别相似图片并按案件号归类。

## 功能特点

- 🔍 **智能分类**: YOLO模型自动筛选目标图片
- 📊 **相似度分析**: 感知哈希算法识别相似图片
- 📁 **批量处理**: 支持多ZIP文件同时处理
- 🏷️ **案件号提取**: 自动识别并提取案件编号
- 📄 **结果导出**: 生成CSV记录和分组文件
- 🐳 **Docker支持**: 容器化部署，一键启动

## 项目结构

```
code/
├── group2.py              # 核心处理脚本
├── web_frontend/          # Web前端版本
│   ├── app.py            # Flask后端
│   ├── templates/        # HTML模板
│   └── 使用说明.md        # 详细使用文档
├── web_docker/           # Docker版本
│   ├── Dockerfile        # 镜像构建
│   ├── docker-compose.yml
│   ├── start.bat         # Windows启动
│   ├── start.sh          # Linux启动
│   └── README.md         # Docker文档
└── README.md             # 本文件
```

## 快速开始

### 方式一：Docker版本（推荐）

```bash
cd web_docker
# Windows
start.bat
# Linux/Mac
chmod +x start.sh && ./start.sh
```

访问：http://localhost:5000

### 方式二：本地运行

```bash
# 1. 安装依赖
conda create -n yolo11 python=3.9
conda activate yolo11
pip install -r web_frontend/requirements.txt

# 2. 启动服务
cd web_frontend
python app.py
```

### 方式三：命令行版本

```bash
conda activate yolo11
python group2.py
```

## 案件号格式支持

系统自动识别以下案件号格式：
- `DQIHWXO80125054932__20250805105326`（完整格式）
- `DQIHWXO80125054932`（简化格式）
- 其他数字编号格式

## 输出结果

### 文件命名
```
案件号_g组号_序号_原文件名.扩展名
```

### CSV记录字段
- 组别、序号、案件号
- 原始文件名、新文件名
- 来源ZIP、ZIP内路径、组大小

## 系统要求

### 最低配置
- Python 3.9+
- 4GB RAM
- 5GB 存储空间

### 推荐配置
- NVIDIA GPU（CUDA支持）
- 8GB+ RAM
- 10GB+ 存储空间

### 模型文件
需要训练好的YOLO分类模型：
```
runs/classify/train26/weights/best.pt
```

## 技术栈

- **后端**: Python + Flask + YOLO + OpenCV
- **前端**: HTML5 + CSS3 + JavaScript
- **AI模型**: Ultralytics YOLO
- **图像处理**: PIL + ImageHash
- **容器**: Docker + Docker Compose

## 开发指南

### 添加新的案件号格式
编辑 `extract_case_number()` 函数：
```python
patterns = [
    r'([A-Z]+\d+__\d+)',    # 现有格式
    r'(YOUR_PATTERN)',      # 添加新格式
]
```

### 调整相似度阈值
修改 `HASH_THRESHOLD` 参数：
```python
HASH_THRESHOLD = 5  # 降低数值=更严格匹配
```

### 修改YOLO置信度
调整 `CLASS2_CONFIDENCE_THRESHOLD`：
```python
CLASS2_CONFIDENCE_THRESHOLD = 0.5  # 0.0-1.0
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request

## 更新日志

- v1.0.0 - 基础功能完成
- v1.1.0 - 添加Web界面
- v1.2.0 - Docker化部署
- v1.3.0 - 案件号自动提取

---

**"Talk is cheap. Show me the code."** - 系统能工作就是美的。