import os
import shutil
import glob
from pathlib import Path

def move_images_from_groups():
    """
    从每个group_数字文件夹中移动一张图片到code/data目录下并重新命名
    """
    # 源目录和目标目录
    source_dir = r"F:\develop\group\similar_photos"
    target_dir = r"F:\develop\青海牦牛案\ultralytics-main\ultralytics-main\code\data"
    
    # 创建目标目录
    os.makedirs(target_dir, exist_ok=True)
    
    # 支持的图片格式
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.tiff', '*.webp']
    
    # 计数器
    moved_count = 0
    
    # 遍历源目录中的所有文件夹
    for folder_name in os.listdir(source_dir):
        folder_path = os.path.join(source_dir, folder_name)
        
        # 检查是否是目录且名称符合group_数字格式
        if os.path.isdir(folder_path) and folder_name.startswith('group_'):
            print(f"处理文件夹: {folder_name}")
            
            # 查找该文件夹中的图片文件
            image_files = []
            for ext in image_extensions:
                image_files.extend(glob.glob(os.path.join(folder_path, ext)))
                image_files.extend(glob.glob(os.path.join(folder_path, ext.upper())))
            
            if image_files:
                # 选择第一张图片
                source_image = image_files[0]
                
                # 获取文件扩展名
                file_ext = os.path.splitext(source_image)[1]
                
                # 新的文件名：group_数字 + 扩展名
                new_filename = f"{folder_name}{file_ext}"
                target_path = os.path.join(target_dir, new_filename)
                
                try:
                    # 移动文件
                    shutil.copy2(source_image, target_path)
                    print(f"  已复制: {os.path.basename(source_image)} -> {new_filename}")
                    moved_count += 1
                except Exception as e:
                    print(f"  错误: 无法复制 {source_image}: {e}")
            else:
                print(f"  警告: {folder_name} 中没有找到图片文件")
    
    print(f"\n完成！共处理了 {moved_count} 个文件夹的图片")
    print(f"图片已保存到: {target_dir}")

if __name__ == "__main__":
    move_images_from_groups()
