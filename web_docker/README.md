# 牦牛图片相似度分析系统 - Docker版本

基于Docker的容器化部署版本，一键启动，无需配置环境。

## 目录结构

```
web_docker/
├── Dockerfile              # Docker镜像构建文件
├── docker-compose.yml      # Docker编排文件
├── app.py                  # Flask应用主文件
├── image_processor.py      # 图片处理核心逻辑
├── requirements.txt        # Python依赖
├── start.sh               # Linux/Mac启动脚本
├── start.bat              # Windows启动脚本
├── templates/
│   └── index.html         # 前端页面
└── data/                  # 数据目录（自动创建）
    ├── uploads/           # 上传文件
    └── results/           # 处理结果
```

## 快速启动

### Windows
```cmd
双击 start.bat
```

### Linux/Mac
```bash
chmod +x start.sh
./start.sh
```

### 手动启动
```bash
# 创建数据目录
mkdir -p data/uploads data/results

# 构建并启动
docker-compose up -d

# 查看状态
docker-compose ps
```

## 系统要求

- Docker 20.0+
- Docker Compose 2.0+
- 可用内存: 2GB+
- 可用存储: 5GB+

## 功能特点

### Docker化优势
- **零环境配置**: 无需安装Python、CUDA等
- **一键部署**: 双击启动脚本即可
- **隔离运行**: 容器化环境，不影响主机
- **资源控制**: 内存限制4GB，可调整

### 数据持久化
- 上传文件保存在 `data/uploads/`
- 处理结果保存在 `data/results/`
- 重启容器数据不丢失

### 模型挂载
- 自动挂载 `../runs/classify/train26/weights/best.pt`
- 如无模型文件，自动切换为非YOLO模式

## 使用说明

### 1. 启动服务
运行启动脚本后，访问：http://localhost:5000

### 2. 上传处理
- 拖拽或选择ZIP文件
- 支持累加多个案件
- 自动提取案件号（格式：DQIHWXO80125054932__20250805105326）

### 3. 查看结果
- 实时进度显示
- 图片预览展示
- 分组统计信息

### 4. 下载结果
- CSV记录（UTF-8编码）
- 完整ZIP包

## 管理命令

```bash
# 查看运行状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 重新构建
docker-compose build --no-cache
```

## 配置选项

### 端口修改
编辑 `docker-compose.yml`：
```yaml
ports:
  - "8080:5000"  # 改为8080端口
```

### 内存限制
编辑 `docker-compose.yml`：
```yaml
deploy:
  resources:
    limits:
      memory: 8G  # 增加到8GB
```

### 模型路径
编辑 `docker-compose.yml`：
```yaml
volumes:
  - "/path/to/your/model:/app/models:ro"
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| PYTHONUNBUFFERED | 1 | Python输出不缓冲 |
| FLASK_ENV | production | Flask运行模式 |

## 数据目录

### uploads/
上传的ZIP文件临时存储目录

### results/
处理结果存储目录：
```
results/
├── group_1/           # 第1组相似图片
├── group_2/           # 第2组相似图片
├── ...
└── 相似图片分组记录.csv
```

## 故障排除

### 容器启动失败
```bash
# 查看详细日志
docker-compose logs

# 检查端口占用
netstat -tulpn | grep :5000

# 重建镜像
docker-compose build --no-cache
```

### 模型加载失败
```bash
# 检查模型文件
ls -la ../runs/classify/train26/weights/best.pt

# 容器内检查
docker-compose exec yak-image-analyzer ls -la /app/models/
```

### 内存不足
```bash
# 检查内存使用
docker stats

# 增加内存限制
# 编辑 docker-compose.yml 中的 memory 配置
```

### 权限问题
```bash
# Linux/Mac 文件权限
chmod -R 755 data/

# Windows Docker Desktop
# 确保在设置中启用文件共享
```

## 性能优化

### GPU支持
如需GPU加速，修改 `docker-compose.yml`：
```yaml
services:
  yak-image-analyzer:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
```

### 网络配置
如需外网访问，修改端口映射：
```yaml
ports:
  - "0.0.0.0:5000:5000"
```

## 更新升级

```bash
# 停止服务
docker-compose down

# 更新代码
git pull

# 重新构建
docker-compose build --no-cache

# 启动服务
docker-compose up -d
```

## API接口

- `GET /` - 主页面
- `POST /upload` - 上传文件
- `GET /status` - 处理状态
- `GET /results` - 分组结果
- `GET /image/<path>` - 图片访问
- `GET /download_results` - 下载ZIP
- `GET /download_csv` - 下载CSV
- `GET /health` - 健康检查

## 技术栈

- **容器**: Docker + Docker Compose
- **后端**: Python 3.9 + Flask
- **AI模型**: YOLO + OpenCV
- **前端**: HTML5 + JavaScript
- **存储**: 文件系统 + CSV

---

**Docker版本优势：一次构建，到处运行。**