import os
import sys
import json
import tempfile
import shutil
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import zipfile

sys.path.append('..')

# 修复模型路径
import group2
group2.YOLO_MODEL_PATH = r"..\models\best.pt"

from group2 import (
    load_yolo_model, 
    classify_images_with_yolo,
    extract_zip_files,
    calculate_image_hash,
    find_similar_photos_with_yolo
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# 全局变量存储处理状态
processing_status = {
    'is_processing': False,
    'current_step': '',
    'progress': 0,
    'total_images': 0,
    'class2_images': 0,
    'groups_found': 0,
    'error': None
}

# 加载YOLO模型（启动时加载一次）
yolo_model = None

def init_model():
    global yolo_model
    yolo_model = load_yolo_model()
    if yolo_model is None:
        processing_status['error'] = "YOLO模型加载失败"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if processing_status['is_processing']:
        return jsonify({'error': '正在处理中，请稍后再试'}), 400
    
    if 'files' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    # 清理旧文件
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))
    
    uploaded_files = []
    for file in files:
        if file and file.filename.endswith('.zip'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            uploaded_files.append(filename)
    
    if not uploaded_files:
        return jsonify({'error': '请上传ZIP文件'}), 400
    
    # 启动后台处理
    thread = threading.Thread(target=process_images)
    thread.start()
    
    return jsonify({
        'message': '文件上传成功，开始处理',
        'files': uploaded_files
    })

def process_images():
    global processing_status
    
    processing_status = {
        'is_processing': True,
        'current_step': '提取图片',
        'progress': 10,
        'total_images': 0,
        'class2_images': 0,
        'groups_found': 0,
        'error': None
    }
    
    try:
        # 清理结果目录
        results_dir = app.config['RESULTS_FOLDER']
        if os.path.exists(results_dir):
            shutil.rmtree(results_dir)
        os.makedirs(results_dir)
        
        # 提取ZIP文件（确保保留source_zip信息）
        processing_status['current_step'] = '提取ZIP文件中的图片'
        image_infos, temp_dirs = extract_zip_files(app.config['UPLOAD_FOLDER'])
        
        # 确保每个image_info包含source_zip信息
        for info in image_infos:
            if 'source_zip' not in info:
                # 从路径推断source_zip
                info['source_zip'] = 'unknown.zip'
        
        processing_status['total_images'] = len(image_infos)
        processing_status['progress'] = 30
        
        if not image_infos:
            raise Exception("未找到图片文件")
        
        # YOLO分类
        processing_status['current_step'] = 'YOLO模型分类中'
        class2_images = classify_images_with_yolo(yolo_model, image_infos)
        processing_status['class2_images'] = len(class2_images)
        processing_status['progress'] = 60
        
        if not class2_images:
            raise Exception("未找到class2图片")
        
        # 计算哈希值和分组
        processing_status['current_step'] = '计算相似度并分组'
        groups = process_similarity(class2_images)
        processing_status['groups_found'] = len(groups)
        processing_status['progress'] = 90
        
        # 保存结果
        save_results(groups)
        
        # 清理临时文件
        for temp_dir in temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        
        processing_status['progress'] = 100
        processing_status['current_step'] = '处理完成'
        
    except Exception as e:
        processing_status['error'] = str(e)
    finally:
        processing_status['is_processing'] = False

def process_similarity(image_infos):
    from collections import defaultdict
    import imagehash
    
    HASH_SIZE = 8
    HASH_THRESHOLD = 5
    
    hashes = {}
    for info in image_infos:
        hash_value = calculate_image_hash(info)
        if hash_value:
            hashes[info['path']] = {'hash': hash_value, 'info': info}
    
    groups = defaultdict(list)
    processed = set()
    
    for path1, data1 in hashes.items():
        if path1 in processed:
            continue
        
        group_id = len(groups) + 1
        groups[group_id].append(data1['info'])
        processed.add(path1)
        
        for path2, data2 in hashes.items():
            if path2 in processed:
                continue
            
            distance = data1['hash'] - data2['hash']
            if distance <= HASH_THRESHOLD:
                groups[group_id].append(data2['info'])
                processed.add(path2)
    
    # 过滤掉单张图片的组
    return {k: v for k, v in groups.items() if len(v) > 1}

def save_results(groups):
    import csv
    import re
    
    results_dir = app.config['RESULTS_FOLDER']
    csv_data = []
    csv_headers = ['组别', '序号', '案件号', '原始文件名', '新文件名', '来源ZIP', 'ZIP内路径', '相似度组大小']
    
    for group_id, images in groups.items():
        group_dir = os.path.join(results_dir, f'group_{group_id}')
        os.makedirs(group_dir, exist_ok=True)
        
        for i, image_info in enumerate(images):
            # 提取案件号（从ZIP文件名或路径中提取）
            source_zip = image_info.get('source_zip', '')
            case_number = extract_case_number(source_zip)
            
            # 生成新文件名：案件号_组号_序号_原文件名
            original_filename = os.path.basename(image_info['path'])
            name, ext = os.path.splitext(original_filename)
            
            if case_number:
                new_filename = f'{case_number}_g{group_id}_{i+1}_{name}{ext}'
            else:
                new_filename = f'unknown_g{group_id}_{i+1}_{name}{ext}'
            
            # 清理文件名中的非法字符
            new_filename = re.sub(r'[<>:"/\\|?*]', '_', new_filename)
            
            dest_path = os.path.join(group_dir, new_filename)
            shutil.copy2(image_info['path'], dest_path)
            
            # 添加到CSV数据
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
    
    # 生成CSV文件
    csv_path = os.path.join(results_dir, '相似图片分组记录.csv')
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(csv_headers)
            writer.writerows(csv_data)
        print(f'CSV记录已生成: {csv_path}')
    except Exception as e:
        print(f'生成CSV文件时出错: {e}')

def extract_case_number(filename):
    """从文件名中提取案件号"""
    import re
    
    # 首先尝试匹配完整的案件号格式
    # 格式如：DQIHWXO80125054932__20250805105326
    full_case_pattern = r'([A-Z]+\d+__\d+)'
    match = re.search(full_case_pattern, filename)
    if match:
        return match.group(1)
    
    # 尝试匹配部分案件号格式（不含日期）
    # 格式如：DQIHWXO80125054932
    partial_case_pattern = r'([A-Z]{3,}[A-Z0-9]*\d{10,})'
    match = re.search(partial_case_pattern, filename)
    if match:
        return match.group(1)
    
    # 其他备用模式
    patterns = [
        r'([A-Z]{2,}\d{8,})',  # 字母+长数字
        r'(\d{10,})',  # 10位或更多数字（可能是案件编号）
        r'案[件]?[_-]?(\d+)',  # "案件123"格式
        r'第(\d+)号',  # "第123号"格式
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
    
    # 如果没有找到，返回文件名的主要部分
    name = os.path.splitext(filename)[0]
    # 清理特殊字符，但保留下划线
    name = re.sub(r'[^\w\-_]', '', name)
    # 如果文件名很长，可能本身就是案件号
    if len(name) > 15:
        return name[:50]  # 保留更长的部分
    return name[:20] if name else 'unknown'

@app.route('/status')
def get_status():
    return jsonify(processing_status)

@app.route('/results')
def get_results():
    results_dir = app.config['RESULTS_FOLDER']
    if not os.path.exists(results_dir):
        return jsonify({'groups': []})
    
    groups = []
    for group_name in sorted(os.listdir(results_dir)):
        group_path = os.path.join(results_dir, group_name)
        if os.path.isdir(group_path):
            images = []
            for img_name in sorted(os.listdir(group_path)):
                if img_name.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    # 返回相对路径用于访问
                    images.append(f'{group_name}/{img_name}')
            groups.append({
                'name': group_name,
                'count': len(images),
                'images': images[:5]  # 只返回前5张预览
            })
    
    return jsonify({'groups': groups})

@app.route('/image/<path:filename>')
def serve_image(filename):
    """提供图片文件访问"""
    return send_file(os.path.join(app.config['RESULTS_FOLDER'], filename))

@app.route('/download_results')
def download_results():
    results_dir = app.config['RESULTS_FOLDER']
    if not os.path.exists(results_dir) or not os.listdir(results_dir):
        return jsonify({'error': '没有结果可下载'}), 404
    
    # 创建ZIP文件
    zip_path = os.path.join(tempfile.gettempdir(), 'results.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(results_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, results_dir)
                zipf.write(file_path, arcname)
    
    return send_file(zip_path, as_attachment=True, download_name='相似图片分组结果.zip')

@app.route('/download_csv')
def download_csv():
    """单独下载CSV文件"""
    csv_path = os.path.join(app.config['RESULTS_FOLDER'], '相似图片分组记录.csv')
    if os.path.exists(csv_path):
        return send_file(csv_path, as_attachment=True, download_name='相似图片分组记录.csv', mimetype='text/csv')
    else:
        return jsonify({'error': 'CSV文件不存在'}), 404

if __name__ == '__main__':
    init_model()
    app.run(debug=True, host='0.0.0.0', port=5000)