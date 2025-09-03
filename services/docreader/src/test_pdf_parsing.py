import os
import logging
from typing import Dict
from PIL.Image import Image as PilImage
from types import SimpleNamespace # A simple way to create mock objects
# 导入您项目中的 PDFParser 类
from parser.pdf_parser import PDFParser
# 1. 设置您想要测试的PDF文件的路径
PDF_FILE_PATH = "/data1/home/lwx/work/Code/Experiment/WeKnora/services/docreader/src/zhidu_travel.pdf"  
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
    print("\n" + "=" * 30)
    print(f"  {title.upper()}")
    print("=" * 30)

def print_image_map_details(image_map: Dict[str, PilImage]):
    """详细打印 image_map 的信息并保存图像"""
    print_section_header("提取的图像信息 (Image Map)")
    if not image_map:
        print(" -> 未在此PDF中提取到任何图像。")
        return
    print(f" -> 总共提取到 {len(image_map)} 张图像。")
    print("-" * 20)
    if not os.path.exists(OUTPUT_DIR):
        print(f"创建输出目录: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR)
    for image_name, pil_image in image_map.items():
        print(f"  图像名称 (内部): '{image_name}'")
        print(f"    - 尺寸 (宽x高): {pil_image.size}")
        print(f"    - 模式 (e.g., RGB): {pil_image.mode}")
        try:
            save_path = os.path.join(OUTPUT_DIR, image_name)
            pil_image.save(save_path)
            print(f"    - [成功] 图像已保存至: '{save_path}'")
        except Exception as e:
            print(f"    - [失败] 保存图像时出错: {e}")
        print("-" * 20)

def run_parser_test():
    """执行PDF解析器的测试"""
    if not os.path.exists(PDF_FILE_PATH):
        print(f"错误: 测试文件未找到，请检查路径 '{PDF_FILE_PATH}'")
        return

    # 1. 模拟真实的 ChunkingConfig 对象
    mock_vlm_config = SimpleNamespace(model_name=None, base_url=None, api_key=None, interface_type=None)
    mock_chunking_config = SimpleNamespace(vlm_config=mock_vlm_config)

    # 2. 实例化解析器时传入模拟配置
    pdf_parser = PDFParser(
        enable_multimodal=True,  # 确保多模态逻辑被激活
        chunking_config=mock_chunking_config
    )
    print(f"成功实例化 PDFParser: {pdf_parser.__class__.__name__}")
    
    print(f"正在读取PDF文件: '{PDF_FILE_PATH}'")
    with open(PDF_FILE_PATH, "rb") as f:
        pdf_content = f.read()
    print("文件读取完成。")

    print("调用 pdf_parser.parse_into_text() ...")
    final_text = pdf_parser.parse_into_text(pdf_content)
    print("解析完成！")

    print_section_header("最终提取的文本 (Final Text)")
    print("注意：以下文本包含了纯文本、Markdown格式的表格和图像的占位符。")
    print("-" * 20 + " [文本开始] " + "-" * 20)
    print(final_text)
    print("-" * 20 + " [文本结束] " + "-" * 20)
    
if __name__ == "__main__": 
    setup_logging()
    run_parser_test()