"""测试案件号提取功能"""

from app import extract_case_number

# 测试用例
test_cases = [
    # 标准格式
    ("DQIHWXO80125054932__20250805105326.zip", "DQIHWXO80125054932__20250805105326"),
    ("DQIHWXO80125054931__20250805105251.zip", "DQIHWXO80125054931__20250805105251"),
    
    # 不含日期的格式
    ("DQIHWXO80125054932.zip", "DQIHWXO80125054932"),
    ("DQIHWXO80125054931.zip", "DQIHWXO80125054931"),
    
    # 其他可能的格式
    ("案件_DQIHWXO80125054932__20250805105326.zip", "DQIHWXO80125054932__20250805105326"),
    ("20250805_DQIHWXO80125054932.zip", "DQIHWXO80125054932"),
    
    # 纯数字案件号
    ("80125054932.zip", "80125054932"),
    ("20250805105326.zip", "20250805105326"),
    
    # 其他格式
    ("案件123.zip", "123"),
    ("第456号.zip", "456"),
    ("GL-001.zip", "GL001"),
    ("test.zip", "test"),
]

print("案件号提取测试")
print("=" * 60)

for filename, expected in test_cases:
    result = extract_case_number(filename)
    status = "[PASS]" if result == expected else "[FAIL]"
    print(f"{status} {filename}")
    print(f"  期望: {expected}")
    print(f"  实际: {result}")
    if result != expected:
        print(f"  >>> 不匹配!")
    print()

print("=" * 60)
print("测试完成")