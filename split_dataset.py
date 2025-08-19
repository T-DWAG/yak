import os
import shutil
import random
from pathlib import Path

def split_dataset():
    """
    将data和data2目录中的图片按照8:2的比例划分到train和val目录中
    data -> class1, data2 -> class2
    """
    # 源目录
    data_dir = r"F:\develop\青海牦牛案\ultralytics-main\ultralytics-main\code\data"
    data2_dir = r"F:\develop\青海牦牛案\ultralytics-main\ultralytics-main\code\data2"
    
    # 目标目录
    base_target_dir = r"F:\develop\青海牦牛案\ultralytics-main\ultralytics-main\code\dataset"
    train_dir = os.path.join(base_target_dir, "train")
    val_dir = os.path.join(base_target_dir, "val")
    
    # 创建目录结构
    train_class1_dir = os.path.join(train_dir, "class1")
    train_class2_dir = os.path.join(train_dir, "class2")
    val_class1_dir = os.path.join(val_dir, "class1")
    val_class2_dir = os.path.join(val_dir, "class2")
    
    for dir_path in [train_class1_dir, train_class2_dir, val_class1_dir, val_class2_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    # 支持的图片格式
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
    
    def get_image_files(directory):
        """获取目录中的所有图片文件"""
        image_files = []
        if os.path.exists(directory):
            for file in os.listdir(directory):
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    image_files.append(os.path.join(directory, file))
        return image_files
    
    def split_and_copy_files(source_files, train_dir, val_dir, split_ratio=0.8):
        """将文件按照比例划分并复制到训练集和验证集目录"""
        if not source_files:
            return 0, 0
        
        # 随机打乱文件列表
        random.shuffle(source_files)
        
        # 计算分割点
        split_index = int(len(source_files) * split_ratio)
        
        train_files = source_files[:split_index]
        val_files = source_files[split_index:]
        
        # 复制训练集文件
        for i, file_path in enumerate(train_files):
            filename = os.path.basename(file_path)
            target_path = os.path.join(train_dir, filename)
            shutil.copy2(file_path, target_path)
        
        # 复制验证集文件
        for i, file_path in enumerate(val_files):
            filename = os.path.basename(file_path)
            target_path = os.path.join(val_dir, filename)
            shutil.copy2(file_path, target_path)
        
        return len(train_files), len(val_files)
    
    # 设置随机种子以确保结果可重现
    random.seed(42)
    
    # 处理class1 (data目录)
    print("处理 class1 (data目录)...")
    class1_files = get_image_files(data_dir)
    print(f"找到 {len(class1_files)} 张图片")
    
    train_count1, val_count1 = split_and_copy_files(
        class1_files, train_class1_dir, val_class1_dir
    )
    print(f"class1 - 训练集: {train_count1} 张, 验证集: {val_count1} 张")
    
    # 处理class2 (data2目录)
    print("\n处理 class2 (data2目录)...")
    class2_files = get_image_files(data2_dir)
    print(f"找到 {len(class2_files)} 张图片")
    
    train_count2, val_count2 = split_and_copy_files(
        class2_files, train_class2_dir, val_class2_dir
    )
    print(f"class2 - 训练集: {train_count2} 张, 验证集: {val_count2} 张")
    
    # 统计总结
    total_train = train_count1 + train_count2
    total_val = val_count1 + val_count2
    total_images = total_train + total_val
    
    print(f"\n=== 数据集划分完成 ===")
    print(f"总图片数: {total_images}")
    print(f"训练集: {total_train} 张 ({total_train/total_images*100:.1f}%)")
    print(f"验证集: {total_val} 张 ({total_val/total_images*100:.1f}%)")
    print(f"\n目录结构:")
    print(f"  {base_target_dir}/")
    print(f"  ├── train/")
    print(f"  │   ├── class1/ ({train_count1} 张)")
    print(f"  │   └── class2/ ({train_count2} 张)")
    print(f"  └── val/")
    print(f"      ├── class1/ ({val_count1} 张)")
    print(f"      └── class2/ ({val_count2} 张)")

if __name__ == "__main__":
    split_dataset() 