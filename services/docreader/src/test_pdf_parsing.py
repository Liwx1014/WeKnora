import os
import logging
from typing import Dict
from PIL.Image import Image as PilImage
from types import SimpleNamespace # A simple way to create mock objects

# 导入您项目中的 PDFParser 和 ParseResult 类
# [修改] 导入 ParseResult 以便进行类型提示
from parser.pdf_parser import PDFParser
from parser.base_parser import ParseResult

# 1. 设置您想要测试的PDF文件的路径
PDF_FILE_PATH = "/data1/home/lwx/work/Code/Experiment/WeKnora/services/docreader/src/WBF.pdf"  
# 2. 设置一个目录来保存提取出的图像
OUTPUT_DIR = "extracted_images"
# ---
def setup_logging():
    """配置日志记录，以便能看到来自解析器内部的日志信息"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def print_section_header(title: str):
    """打印一个格式化的节标题"""
    print("\n" + "=" * 40)
    print(f"  {title.upper()}")
    print("=" * 40)

def print_image_map_details(image_map: Dict[str, PilImage]):
    """详细打印 image_map 的信息并保存图像"""
    # 这个函数在新的测试流程中不会被直接调用，但保留以备后用
    pass

# [新增] 用于打印分块结果的函数
def print_chunk_details(result: ParseResult):
    """详细打印分块的结果，验证表格是否完整"""
    print_section_header("分块验证 (Chunk Verification)")
    if not result.chunks:
        print(" -> 未生成任何 Chunk。")
        return

    print(f" -> 总共生成了 {len(result.chunks)} 个 Chunk。")
    print("-" * 20)
    
    for i, chunk in enumerate(result.chunks):
        # 打印每个 Chunk 的头部信息
        print(f"--- Chunk #{i+1} (序号: {chunk.seq}) ---")
        print(f"    - 字符范围: 从 {chunk.start} 到 {chunk.end} (长度: {len(chunk.content)})")
        
        # 打印 Chunk 的内容
        print("-" * 10 + " [Chunk 内容开始] " + "-" * 10)
        print(chunk.content)
        print("-" * 10 + " [Chunk 内容结束] " + "-" * 10)
        print("\n") # 在每个 Chunk 之后加一个空行，方便阅读

def run_parser_test():
    """执行PDF解析器的测试"""
    if not os.path.exists(PDF_FILE_PATH):
        print(f"错误: 测试文件未找到，请检查路径 '{PDF_FILE_PATH}'")
        return

    # 1. 模拟真实的 ChunkingConfig 对象
    mock_vlm_config = SimpleNamespace(model_name=None, base_url=None, api_key=None, interface_type=None)
    mock_chunking_config = SimpleNamespace(vlm_config=mock_vlm_config)

    # 2. 实例化解析器时传入模拟配置
    # [修改] 可以调整 chunk_size 来观察分块效果
    pdf_parser = PDFParser(
        file_name=PDF_FILE_PATH,
        enable_multimodal=False,  # 在这个测试中可以禁用多模态以加快速度
        chunking_config=mock_chunking_config,
        chunk_size=1000, # 您可以调整这个值来测试不同的分块边界
        chunk_overlap=200
    )
    print(f"成功实例化 PDFParser: {pdf_parser.__class__.__name__}")
    
    print(f"正在读取PDF文件: '{PDF_FILE_PATH}'")
    with open(PDF_FILE_PATH, "rb") as f:
        pdf_content = f.read()
    print("文件读取完成。")

    # [修改] 调用 .parse() 方法而不是 .parse_into_text()
    print("调用 pdf_parser.parse() 来执行完整的解析和分块流程...")
    parse_result = pdf_parser.parse(pdf_content)
    print("解析和分块完成！")

    # [修改] 打印完整的解析文本，用于对比
    print_section_header("完整提取的文本 (Full Extracted Text)")
    print("这是未经分块的原始解析结果，用于参考。")
    print("-" * 20 + " [文本开始] " + "-" * 20)
    print(parse_result.text)
    print("-" * 20 + " [文本结束] " + "-" * 20)
    
    # [新增] 调用新的函数来打印和验证分块结果
    print_chunk_details(parse_result)

if __name__ == "__main__": 
    setup_logging()
    run_parser_test()