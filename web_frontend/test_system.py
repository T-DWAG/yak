import os
import sys
import zipfile
import tempfile
from pathlib import Path

sys.path.append('..')

def test_model_loading():
    """测试YOLO模型加载"""
    print("=" * 50)
    print("测试1: YOLO模型加载")
    print("-" * 50)
    
    try:
        from group2 import load_yolo_model
        model = load_yolo_model()
        if model:
            print("[PASS] 模型加载成功")
            return True
        else:
            print("[FAIL] 模型加载失败")
            return False
    except Exception as e:
        print(f"[ERROR] 错误: {e}")
        return False

def test_image_processing():
    """测试图片处理功能"""
    print("\n" + "=" * 50)
    print("测试2: 图片处理功能")
    print("-" * 50)
    
    try:
        from group2 import calculate_image_hash
        from PIL import Image
        import imagehash
        
        # 创建测试图片
        test_img = Image.new('RGB', (100, 100), color='red')
        temp_path = 'test_image.jpg'
        test_img.save(temp_path)
        
        # 测试哈希计算
        image_info = {'path': temp_path}
        hash_value = calculate_image_hash(image_info)
        
        if hash_value:
            print(f"[PASS] 哈希计算成功: {hash_value}")
            os.remove(temp_path)
            return True
        else:
            print("[FAIL] 哈希计算失败")
            os.remove(temp_path)
            return False
            
    except Exception as e:
        print(f"[ERROR] 错误: {e}")
        return False

def test_flask_app():
    """测试Flask应用"""
    print("\n" + "=" * 50)
    print("测试3: Flask应用")
    print("-" * 50)
    
    try:
        from app import app
        
        # 测试主页路由
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("[PASS] 主页访问成功")
            else:
                print(f"[FAIL] 主页访问失败: {response.status_code}")
                
            # 测试状态接口
            response = client.get('/status')
            if response.status_code == 200:
                data = response.get_json()
                print(f"[PASS] 状态接口正常: {data}")
            else:
                print(f"[FAIL] 状态接口失败: {response.status_code}")
                
        return True
        
    except Exception as e:
        print(f"[ERROR] 错误: {e}")
        return False

def test_zip_handling():
    """测试ZIP文件处理"""
    print("\n" + "=" * 50)
    print("测试4: ZIP文件处理")
    print("-" * 50)
    
    try:
        # 创建测试ZIP文件
        test_zip = 'test.zip'
        with zipfile.ZipFile(test_zip, 'w') as zf:
            # 创建测试图片并添加到ZIP
            from PIL import Image
            for i in range(3):
                img = Image.new('RGB', (100, 100), color=(i*50, i*50, i*50))
                img_path = f'test_{i}.jpg'
                img.save(img_path)
                zf.write(img_path)
                os.remove(img_path)
        
        print(f"[PASS] 测试ZIP文件创建成功: {test_zip}")
        
        # 测试解压功能
        from group2 import extract_zip_files
        temp_dir = tempfile.mkdtemp()
        os.rename(test_zip, os.path.join(temp_dir, test_zip))
        
        images, temp_dirs = extract_zip_files(temp_dir)
        print(f"[PASS] 解压成功，找到 {len(images)} 张图片")
        
        # 清理
        import shutil
        for td in temp_dirs:
            shutil.rmtree(td, ignore_errors=True)
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 错误: {e}")
        return False

def main():
    print("\n牦牛图片相似度分析系统 - 功能测试\n")
    
    results = []
    
    # 运行测试
    results.append(("模型加载", test_model_loading()))
    results.append(("图片处理", test_image_processing()))
    results.append(("Flask应用", test_flask_app()))
    results.append(("ZIP处理", test_zip_handling()))
    
    # 输出总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n所有测试通过！系统可以正常使用。")
    else:
        print(f"\n[WARNING] 有 {total - passed} 个测试失败，请检查相关配置。")

if __name__ == "__main__":
    main()