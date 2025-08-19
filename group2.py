import os
import shutil
import zipfile
import tempfile
import csv
from PIL import Image
import imagehash
from collections import defaultdict
import logging
from ultralytics import YOLO
import glob

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置参数
INPUT_DIR = r"F:\75笔案件\75笔案件\果洛"  # 包含zip文件的目录
OUTPUT_DIR = "similar_photos_class2"  # 输出目录
HASH_SIZE = 8  # 哈希大小（8=64位哈希）
HASH_THRESHOLD = 5  # 汉明距离阈值（≤5视为相似）
SUPPORTED_FORMATS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')  # 支持的图片格式
YOLO_MODEL_PATH = r"..\runs\classify\train26\weights\best.pt"  # YOLO模型路径
CLASS2_CONFIDENCE_THRESHOLD = 0.5  # class2置信度阈值

def load_yolo_model():
    """加载YOLO分类模型"""
    try:
        model = YOLO(YOLO_MODEL_PATH)
        logger.info(f"YOLO模型加载成功: {YOLO_MODEL_PATH}")
        return model
    except Exception as e:
        logger.error(f"加载YOLO模型失败: {str(e)}")
        return None

def classify_images_with_yolo(model, image_paths):
    """使用YOLO模型对图片进行分类，筛选出class2图片"""
    if model is None:
        logger.error("YOLO模型未加载，跳过分类步骤")
        return image_paths
    
    logger.info("开始使用YOLO模型进行图片分类...")
    class2_images = []
    total_images = len(image_paths)
    
    for i, image_info in enumerate(image_paths):
        try:
            # 预测单张图片
            results = model(image_info['path'])
            result = results[0]  # 获取第一个结果
            
            if result.probs is not None:
                # 获取class1和class2的概率
                class1_prob = result.probs.data[0].item()
                class2_prob = result.probs.data[1].item()
                
                # 如果class2概率大于阈值，则保留该图片
                if class2_prob >= CLASS2_CONFIDENCE_THRESHOLD:
                    class2_images.append(image_info)
                    logger.info(f"图片 {i+1}/{total_images}: {os.path.basename(image_info['path'])} - class2概率: {class2_prob:.3f} ✓")
                else:
                    logger.info(f"图片 {i+1}/{total_images}: {os.path.basename(image_info['path'])} - class2概率: {class2_prob:.3f} ✗ (低于阈值)")
            else:
                logger.warning(f"图片 {i+1}/{total_images}: {os.path.basename(image_info['path'])} - 无法获取预测结果")
                
        except Exception as e:
            logger.error(f"预测图片时出错 {image_info['path']}: {str(e)}")
            continue
    
    logger.info(f"YOLO分类完成！从 {total_images} 张图片中筛选出 {len(class2_images)} 张class2图片")
    return class2_images

def extract_zip_files(zip_dir):
    """从指定目录提取所有zip文件中的图片"""
    image_paths = []
    temp_dirs = []
    
    # 遍历目录中的所有zip文件
    for root, _, files in os.walk(zip_dir):
        for file in files:
            if file.lower().endswith('.zip'):
                zip_path = os.path.join(root, file)
                logger.info(f"正在处理zip文件: {zip_path}")
                
                try:
                    # 创建临时目录
                    temp_dir = tempfile.mkdtemp(prefix=f"zip_extract_{os.path.splitext(file)[0]}_")
                    temp_dirs.append(temp_dir)
                    
                    # 解压zip文件，处理中文编码
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        # 获取zip文件中的文件列表
                        for zip_info in zip_ref.infolist():
                            try:
                                # 尝试不同的编码方式处理文件名
                                filename = None
                                for encoding in ['utf-8', 'gbk', 'gb2312', 'cp437']:
                                    try:
                                        filename = zip_info.filename.encode('cp437').decode(encoding)
                                        break
                                    except (UnicodeDecodeError, UnicodeEncodeError):
                                        continue
                                
                                if filename is None:
                                    # 如果所有编码都失败，使用原始文件名
                                    filename = zip_info.filename
                                
                                # 解压单个文件
                                zip_ref.extract(zip_info, temp_dir)
                                
                                # 如果文件名包含中文且需要重命名
                                if filename != zip_info.filename:
                                    old_path = os.path.join(temp_dir, zip_info.filename)
                                    new_path = os.path.join(temp_dir, filename)
                                    if os.path.exists(old_path):
                                        # 确保目标目录存在
                                        os.makedirs(os.path.dirname(new_path), exist_ok=True)
                                        os.rename(old_path, new_path)
                                
                            except Exception as e:
                                logger.warning(f"处理zip文件中的文件 {zip_info.filename} 时出错: {str(e)}")
                                continue
                    
                    # 收集解压后的图片文件
                    for extract_root, _, extract_files in os.walk(temp_dir):
                        for extract_file in extract_files:
                            if extract_file.lower().endswith(SUPPORTED_FORMATS):
                                full_path = os.path.join(extract_root, extract_file)
                                # 记录原始zip文件的完整路径
                                original_zip_path = os.path.join(root, file)
                                # 图片在zip文件中的相对路径（处理中文编码）
                                relative_path = os.path.relpath(full_path, temp_dir)
                                # 尝试修复相对路径中的中文乱码
                                try:
                                    path_parts = relative_path.split('\\')
                                    fixed_parts = []
                                    for part in path_parts:
                                        if '╨' in part or '╧' in part or '╥' in part:
                                            # 修复GBK编码问题
                                            fixed_part = part.encode('latin1').decode('gbk', errors='ignore')
                                        else:
                                            fixed_part = part
                                        fixed_parts.append(fixed_part)
                                    relative_path = '\\'.join(fixed_parts)
                                except:
                                    pass  # 如果修复失败，保持原路径
                                image_paths.append({
                                    'path': full_path,
                                    'source_zip': file,
                                    'original_zip_path': original_zip_path,
                                    'relative_path': relative_path
                                })
                                
                except Exception as e:
                    logger.error(f"处理zip文件 {zip_path} 时出错: {str(e)}")
                    continue
    
    logger.info(f"共提取了 {len(image_paths)} 张图片")
    return image_paths, temp_dirs

def calculate_image_hash(image_info):
    """计算单张图片的哈希值"""
    try:
        with Image.open(image_info['path']) as img:
            # 转换为RGB模式（避免RGBA模式问题）
            img = img.convert('RGB')
            # 计算感知哈希
            h = imagehash.phash(img, hash_size=HASH_SIZE)
            return h
    except Exception as e:
        logger.error(f"计算图片哈希值时出错 {image_info['path']}: {str(e)}")
        return None

def find_similar_photos_with_yolo():
    """使用YOLO预筛选后查找相似图片并分组"""
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 加载YOLO模型
    yolo_model = load_yolo_model()
    
    # 提取zip文件中的图片
    image_infos, temp_dirs = extract_zip_files(INPUT_DIR)
    
    if not image_infos:
        logger.warning("没有找到任何图片文件")
        return
    
    # 使用YOLO模型筛选class2图片
    class2_images = classify_images_with_yolo(yolo_model, image_infos)
    
    if not class2_images:
        logger.warning("没有找到任何class2图片")
        return
    
    # 计算所有class2图片的哈希值
    logger.info("正在计算class2图片哈希值...")
    hashes = {}
    for image_info in class2_images:
        hash_value = calculate_image_hash(image_info)
        if hash_value is not None:
            hashes[image_info['path']] = {
                'hash': hash_value,
                'info': image_info
            }
    
    logger.info(f"成功计算了 {len(hashes)} 张class2图片的哈希值")
    
    # 按相似度分组
    logger.info("正在按相似度分组...")
    groups = defaultdict(list)
    processed = set()
    
    for path1, hash_data1 in hashes.items():
        if path1 in processed:
            continue
        
        # 创建新组
        group_id = len(groups) + 1
        groups[group_id].append(hash_data1['info'])
        processed.add(path1)
        
        # 查找相似图片
        for path2, hash_data2 in hashes.items():
            if path2 in processed:
                continue
            
            # 计算汉明距离
            distance = hash_data1['hash'] - hash_data2['hash']
            if distance <= HASH_THRESHOLD:
                groups[group_id].append(hash_data2['info'])
                processed.add(path2)
    
    # 保存结果和生成CSV记录
    logger.info("正在保存分组结果...")
    group_count = 0
    
    # 准备CSV数据
    csv_data = []
    csv_headers = ['组别', '序号', '原始文件名', '新文件名', '原始ZIP路径', '来源ZIP文件', 'ZIP内相对路径', '目标路径', 'YOLO分类结果']
    
    for group_id, image_infos in groups.items():
        if len(image_infos) < 2:  # 跳过单张图片的组
            continue
        
        group_count += 1
        # 创建组目录
        group_dir = os.path.join(OUTPUT_DIR, f"group_{group_id}")
        os.makedirs(group_dir, exist_ok=True)
        
        # 复制图片并重命名（避免覆盖）
        for i, image_info in enumerate(image_infos):
            try:
                # 获取原始文件名
                filename = os.path.basename(image_info['path'])
                name, ext = os.path.splitext(filename)
                
                # 获取zip文件名（不含扩展名）
                zip_name = os.path.splitext(image_info['source_zip'])[0]
                
                # 获取相对路径中的关键信息（处理中文乱码）
                relative_path = image_info['relative_path']
                path_parts = relative_path.split('\\')
                
                # 提取关键路径信息（最多取3层目录）
                key_path_info = []
                for part in path_parts[:-1]:  # 排除文件名
                    if part and len(key_path_info) < 3:
                        # 尝试处理中文编码
                        try:
                            # 如果包含乱码字符，尝试修复
                            if '╨' in part or '╧' in part or '╥' in part:
                                # 这是典型的GBK编码问题，尝试修复
                                fixed_part = part.encode('latin1').decode('gbk', errors='ignore')
                            else:
                                fixed_part = part
                            key_path_info.append(fixed_part)
                        except:
                            key_path_info.append(part)
                
                # 构建新文件名：组ID_序号_来源zip_路径信息_原文件名
                path_suffix = '_'.join(key_path_info) if key_path_info else 'root'
                # 限制文件名长度，避免过长
                if len(path_suffix) > 50:
                    path_suffix = path_suffix[:50] + '...'
                
                new_name = f"{group_id:03d}_{i+1:03d}_{zip_name}_{path_suffix}_{name}{ext}"
                
                # 清理文件名中的非法字符
                new_name = "".join(c for c in new_name if c.isalnum() or c in ('_', '-', '.', '(', ')', '['))
                
                # 复制文件
                dest_path = os.path.join(group_dir, new_name)
                shutil.copy2(image_info['path'], dest_path)
                
                # 添加到CSV数据
                csv_data.append([
                    f"group_{group_id}",  # 组别
                    i + 1,  # 序号
                    filename,  # 原始文件名
                    new_name,  # 新文件名
                    image_info['original_zip_path'],  # 原始ZIP路径
                    image_info['source_zip'],  # 来源ZIP文件
                    image_info['relative_path'],  # ZIP内相对路径
                    dest_path,  # 目标路径
                    "class2"  # YOLO分类结果
                ])
                
            except Exception as e:
                logger.error(f"复制文件时出错 {image_info['path']}: {str(e)}")
    
    # 生成CSV文件
    csv_path = os.path.join(OUTPUT_DIR, "class2图片分组记录.csv")
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(csv_headers)
            writer.writerows(csv_data)
        logger.info(f"CSV记录文件已生成: {csv_path}")
    except Exception as e:
        logger.error(f"生成CSV文件时出错: {str(e)}")
    
    # 清理临时目录
    logger.info("正在清理临时文件...")
    for temp_dir in temp_dirs:
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.error(f"清理临时目录时出错 {temp_dir}: {str(e)}")
    
    logger.info(f"完成！共找到 {group_count} 组相似照片（仅class2）")
    
    # 输出统计信息
    total_images = sum(len(g) for g in groups.values() if len(g) > 1)
    logger.info(f"总共处理了 {total_images} 张相似图片（仅class2）")

if __name__ == "__main__":
    find_similar_photos_with_yolo() 