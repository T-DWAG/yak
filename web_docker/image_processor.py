import os
import shutil
import zipfile
import tempfile
import csv
import re
import logging
from PIL import Image
import imagehash
from collections import defaultdict
from ultralytics import YOLO
import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置参数
HASH_SIZE = 8
HASH_THRESHOLD = 5
SUPPORTED_FORMATS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')
YOLO_MODEL_PATH = "/app/models/best.pt"  # Docker内模型路径
CLASS2_CONFIDENCE_THRESHOLD = 0.5

def load_yolo_model():
    """加载YOLO分类模型"""
    try:
        if os.path.exists(YOLO_MODEL_PATH):
            model = YOLO(YOLO_MODEL_PATH)
            logger.info(f"YOLO模型加载成功: {YOLO_MODEL_PATH}")
            return model
        else:
            logger.warning(f"模型文件不存在: {YOLO_MODEL_PATH}，将跳过YOLO分类")
            return None
    except Exception as e:
        logger.error(f"加载YOLO模型失败: {str(e)}")
        return None

def classify_images_with_yolo(model, image_paths):
    """使用YOLO模型对图片进行分类，筛选出class2图片"""
    if model is None:
        logger.warning("YOLO模型未加载，返回所有图片")
        return image_paths
    
    logger.info("开始使用YOLO模型进行图片分类...")
    class2_images = []
    total_images = len(image_paths)
    
    for i, image_info in enumerate(image_paths):
        try:
            results = model(image_info['path'])
            result = results[0]
            
            if result.probs is not None:
                class1_prob = result.probs.data[0].item()
                class2_prob = result.probs.data[1].item()
                
                if class2_prob >= CLASS2_CONFIDENCE_THRESHOLD:
                    class2_images.append(image_info)
                    logger.info(f"图片 {i+1}/{total_images}: class2概率: {class2_prob:.3f} ✓")
                else:
                    logger.debug(f"图片 {i+1}/{total_images}: class2概率: {class2_prob:.3f} ✗")
                    
        except Exception as e:
            logger.error(f"预测图片时出错 {image_info['path']}: {str(e)}")
            continue
    
    logger.info(f"YOLO分类完成！从 {total_images} 张图片中筛选出 {len(class2_images)} 张class2图片")
    return class2_images

def extract_zip_files(zip_dir):
    """从指定目录提取所有zip文件中的图片"""
    image_paths = []
    temp_dirs = []
    
    for root, _, files in os.walk(zip_dir):
        for file in files:
            if file.lower().endswith('.zip'):
                zip_path = os.path.join(root, file)
                logger.info(f"正在处理zip文件: {zip_path}")
                
                try:
                    temp_dir = tempfile.mkdtemp(prefix=f"zip_extract_{os.path.splitext(file)[0]}_")
                    temp_dirs.append(temp_dir)
                    
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        for zip_info in zip_ref.infolist():
                            try:
                                filename = None
                                for encoding in ['utf-8', 'gbk', 'gb2312', 'cp437']:
                                    try:
                                        filename = zip_info.filename.encode('cp437').decode(encoding)
                                        break
                                    except (UnicodeDecodeError, UnicodeEncodeError):
                                        continue
                                
                                if filename is None:
                                    filename = zip_info.filename
                                
                                zip_ref.extract(zip_info, temp_dir)
                                
                                if filename != zip_info.filename:
                                    old_path = os.path.join(temp_dir, zip_info.filename)
                                    new_path = os.path.join(temp_dir, filename)
                                    if os.path.exists(old_path):
                                        os.makedirs(os.path.dirname(new_path), exist_ok=True)
                                        os.rename(old_path, new_path)
                                
                            except Exception as e:
                                logger.warning(f"处理zip文件中的文件时出错: {str(e)}")
                                continue
                    
                    for extract_root, _, extract_files in os.walk(temp_dir):
                        for extract_file in extract_files:
                            if extract_file.lower().endswith(SUPPORTED_FORMATS):
                                full_path = os.path.join(extract_root, extract_file)
                                relative_path = os.path.relpath(full_path, temp_dir)
                                image_paths.append({
                                    'path': full_path,
                                    'source_zip': file,
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
            img = img.convert('RGB')
            h = imagehash.phash(img, hash_size=HASH_SIZE)
            return h
    except Exception as e:
        logger.error(f"计算图片哈希值时出错 {image_info['path']}: {str(e)}")
        return None

def extract_case_number(filename):
    """从文件名中提取案件号"""
    # 完整案件号格式：DQIHWXO80125054932__20250805105326
    full_case_pattern = r'([A-Z]+\d+__\d+)'
    match = re.search(full_case_pattern, filename)
    if match:
        return match.group(1)
    
    # 部分案件号格式：DQIHWXO80125054932
    partial_case_pattern = r'([A-Z]{3,}[A-Z0-9]*\d{10,})'
    match = re.search(partial_case_pattern, filename)
    if match:
        return match.group(1)
    
    # 其他备用模式
    patterns = [
        r'([A-Z]{2,}\d{8,})',
        r'(\d{10,})',
        r'案[件]?[_-]?(\d+)',
        r'第(\d+)号',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
    
    name = os.path.splitext(filename)[0]
    name = re.sub(r'[^\w\-_]', '', name)
    if len(name) > 15:
        return name[:50]
    return name[:20] if name else 'unknown'

def process_similarity(image_infos):
    """计算相似度并分组"""
    logger.info("正在计算图片哈希值...")
    hashes = {}
    for image_info in image_infos:
        hash_value = calculate_image_hash(image_info)
        if hash_value is not None:
            hashes[image_info['path']] = {
                'hash': hash_value,
                'info': image_info
            }
    
    logger.info(f"成功计算了 {len(hashes)} 张图片的哈希值")
    
    logger.info("正在按相似度分组...")
    groups = defaultdict(list)
    processed = set()
    
    for path1, hash_data1 in hashes.items():
        if path1 in processed:
            continue
        
        group_id = len(groups) + 1
        groups[group_id].append(hash_data1['info'])
        processed.add(path1)
        
        for path2, hash_data2 in hashes.items():
            if path2 in processed:
                continue
            
            distance = hash_data1['hash'] - hash_data2['hash']
            if distance <= HASH_THRESHOLD:
                groups[group_id].append(hash_data2['info'])
                processed.add(path2)
    
    # 过滤掉单张图片的组
    return {k: v for k, v in groups.items() if len(v) > 1}

def save_results(groups, output_dir):
    """保存分组结果"""
    os.makedirs(output_dir, exist_ok=True)
    csv_data = []
    csv_headers = ['组别', '序号', '案件号', '原始文件名', '新文件名', '来源ZIP', 'ZIP内路径', '相似度组大小']
    
    for group_id, images in groups.items():
        group_dir = os.path.join(output_dir, f'group_{group_id}')
        os.makedirs(group_dir, exist_ok=True)
        
        for i, image_info in enumerate(images):
            source_zip = image_info.get('source_zip', '')
            case_number = extract_case_number(source_zip)
            
            original_filename = os.path.basename(image_info['path'])
            name, ext = os.path.splitext(original_filename)
            
            if case_number:
                new_filename = f'{case_number}_g{group_id}_{i+1}_{name}{ext}'
            else:
                new_filename = f'unknown_g{group_id}_{i+1}_{name}{ext}'
            
            new_filename = re.sub(r'[<>:"/\\|?*]', '_', new_filename)
            
            dest_path = os.path.join(group_dir, new_filename)
            shutil.copy2(image_info['path'], dest_path)
            
            csv_data.append([
                f'group_{group_id}',
                i + 1,
                case_number or 'unknown',
                original_filename,
                new_filename,
                source_zip,
                image_info.get('relative_path', ''),
                len(images)
            ])
    
    csv_path = os.path.join(output_dir, '相似图片分组记录.csv')
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(csv_headers)
            writer.writerows(csv_data)
        logger.info(f'CSV记录已生成: {csv_path}')
    except Exception as e:
        logger.error(f'生成CSV文件时出错: {e}')
    
    return len(groups), sum(len(g) for g in groups.values())

def process_images(input_dir, output_dir, use_yolo=True):
    """主处理函数"""
    logger.info(f"开始处理: {input_dir}")
    
    # 加载模型
    model = load_yolo_model() if use_yolo else None
    
    # 提取图片
    image_infos, temp_dirs = extract_zip_files(input_dir)
    
    if not image_infos:
        logger.warning("没有找到任何图片文件")
        return 0, 0
    
    # YOLO分类
    if model:
        image_infos = classify_images_with_yolo(model, image_infos)
    
    if not image_infos:
        logger.warning("没有找到符合条件的图片")
        return 0, 0
    
    # 相似度分组
    groups = process_similarity(image_infos)
    
    # 保存结果
    group_count, image_count = save_results(groups, output_dir)
    
    # 清理临时文件
    for temp_dir in temp_dirs:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
    
    logger.info(f"处理完成！共找到 {group_count} 组相似照片，总计 {image_count} 张图片")
    return group_count, image_count