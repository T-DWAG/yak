import os
import sys
import json
import tempfile
import shutil
import threading
import zipfile
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from image_processor import process_images, extract_case_number

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
app.config['UPLOAD_FOLDER'] = '/app/uploads'
app.config['RESULTS_FOLDER'] = '/app/results'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

processing_status = {
    'is_processing': False,
    'current_step': '',
    'progress': 0,
    'total_images': 0,
    'class2_images': 0,
    'groups_found': 0,
    'error': None
}

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
            # 保留原始文件名用于案件号提取
            original_name = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_name)
            file.save(filepath)
            uploaded_files.append(original_name)
    
    if not uploaded_files:
        return jsonify({'error': '请上传ZIP文件'}), 400
    
    # 启动后台处理
    thread = threading.Thread(target=process_in_background)
    thread.start()
    
    return jsonify({
        'message': '文件上传成功，开始处理',
        'files': uploaded_files
    })

def process_in_background():
    global processing_status
    
    processing_status = {
        'is_processing': True,
        'current_step': '开始处理',
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
        
        processing_status['current_step'] = '正在分析图片...'
        processing_status['progress'] = 50
        
        # 处理图片
        group_count, image_count = process_images(
            app.config['UPLOAD_FOLDER'],
            results_dir,
            use_yolo=True
        )
        
        processing_status['groups_found'] = group_count
        processing_status['total_images'] = image_count
        processing_status['progress'] = 100
        processing_status['current_step'] = '处理完成'
        
    except Exception as e:
        processing_status['error'] = str(e)
    finally:
        processing_status['is_processing'] = False

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
                    images.append(f'{group_name}/{img_name}')
            groups.append({
                'name': group_name,
                'count': len(images),
                'images': images[:5]
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

@app.route('/health')
def health():
    """健康检查接口"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)