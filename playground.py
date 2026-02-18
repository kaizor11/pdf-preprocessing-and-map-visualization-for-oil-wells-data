# 从 processor.py 文件中导入 plumber_processor 类
from extract_with_pdfplumber import plumber_processor

# 1. 实例化处理类
# 确保你的当前目录下有一个叫 data 的文件夹，里面放着 W1.pdf, W2.pdf 等
processor = plumber_processor(folder="./data")

# 2. 调用方法进行测试
print("--- 开始测试 ---")
files = processor.GetPdfNames(prefix="W")

# 3. 验证结果
print(f"\n--- 测试结束 ---")
print(f"共找到 {len(files)} 个文件。")

if len(files) > 0:
    print(f"第一个文件是: {files[0].name}")
    print(f"最后一个文件是: {files[-1].name}")
else:
    print("警告: 没有找到文件，请检查 ./data 文件夹是否存在以及里面是否有 PDF。")