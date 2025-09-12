import logging
import os
from typing import Any, Dict, Union, Tuple

# MinerU 的核心组件
# pip install "mineru[core]"
from mineru.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
from mineru.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
from mineru.backend.pipeline.model_json_to_middle_json import result_to_middle_json
from mineru.utils.enum_class import MakeMode
from mineru.cli.common import _prepare_pdf_bytes
from bs4 import BeautifulSoup
import re
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

# 在首次使用时自动下载MinerU所需的模型
# 如果网络受限，可以设置环境变量 MINERU_MODEL_SOURCE 为 "modelscope"
# os.environ['MINERU_MODEL_SOURCE'] = "modelscope"

class MemoryBasedDataWriter:
    """
    一个虚拟的数据写入器，它实现了 `write` 方法接口，但内部不做任何操作。
    这用于传递给 MinerU 的函数，以防止其将图像等中间文件写入磁盘，
    从而确保整个解析过程在内存中完成。
    """
    def write(self, *args, **kwargs):
        # 接收所有参数，但什么都不做
        pass

    def write_string(self, *args, **kwargs):
        # 同样，为可能存在的 write_string 方法提供一个空实现
        pass

class PDFParser(BaseParser):
    """
    一个基于 MinerU 的PDF解析器，旨在提供高质量的文本和结构化内容提取。
    保持与旧版 PyMuPDF 解析器相同的接口。
    """

    def _html_table_to_markdown(self, html_content: str) -> str:
        """
        [辅助函数] 将单个HTML表格字符串转换为Markdown格式。
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            table = soup.find('table')
            if not table:
                return html_content # 如果不是有效的表格，返回原文

            markdown_lines = []
            
            header_row = table.find('tr')
            if header_row:
                headers = [cell.get_text(strip=True) for cell in header_row.find_all(['td', 'th'])]
                markdown_lines.append("| " + " | ".join(headers) + " |")
                markdown_lines.append("|" + "---|" * len(headers))
            else:
                return html_content # 没有行的表格是无效的

            body_rows = table.find_all('tr')[1:] # 假定第一行总是表头
            for row in body_rows:
                columns = [cell.get_text(strip=True).replace('\n', ' ') for cell in row.find_all(['td', 'th'])]
                # 确保列数与表头一致，避免格式错误
                if len(columns) == len(headers):
                        markdown_lines.append("| " + " | ".join(columns) + " |")
                # 如果不一致（可能是 rowspan/colspan），为简单起见我们可以选择丢弃或填充
                # 这里我们选择只添加列数匹配的行
            
            # 返回转换后的MD表格，并在前后添加换行符以确保它与周围的文本分离
            return "\n" + "\n".join(markdown_lines) + "\n"
        
        except Exception as e:
            logger.warning(f"Failed to convert HTML table to Markdown: {e}. Returning original HTML content.")
            # 返回原文以避免数据丢失
            return html_content

    def _convert_embedded_html_tables(self, text_content: str) -> str:
        """
        [核心转换函数] 在一个大字符串中查找所有HTML表格，并将其替换为Markdown。
        """
        # 定义一个回调函数，re.sub 会将每个匹配项(match object)传递给它
        def replacer_callback(match):
            html_table_str = match.group(1) # 提取匹配到的完整表格字符串
            return self._html_table_to_markdown(html_table_str)

        # 正则表达式：查找所有 <table ...> ... </table> 块
        # re.DOTALL (或 re.S) 是必须的，确保 '.' 可以匹配换行符
        # re.IGNORECASE (或 re.I) 增加健壮性，匹配 <TABLE> 等
        # (.*?) 使用非贪婪匹配，防止第一个 <table> 匹配到最后一个 </table>
        table_pattern = re.compile(r'(<table.*?>.*?</table>)', re.IGNORECASE | re.DOTALL)
        
        # 使用 re.sub 和回调函数执行全局替换
        converted_text = table_pattern.sub(replacer_callback, text_content)
        return converted_text
    def _convert_embedded_latex(self, text_content: str) -> str:
        """
        在一个大字符串中查找所有 LaTeX 公式，并将其定界符转换为 Markdown 数学格式。
        """
        # 1. 处理块级公式 (Display Math)
        # --- MODIFIED ---
        # 在匹配列表中增加了 'array' 环境
        text_content = re.sub(
            r'\\begin\{(equation|align|gather|multline|array)\}(.*?)\\end\{\1\}',
            r'\n$$\2$$\n',
            text_content,
            flags=re.DOTALL
        )
        # 转换 \[ ... \]
        text_content = re.sub(
            r'\\\[(.*?)\\\]',
            r'\n$$\1$$\n',
            text_content,
            flags=re.DOTALL
        )
        
        # 2. 处理行内公式 (Inline Math)
        # 转换 \( ... \)
        text_content = re.sub(
            r'\\\((.*?)\\\)',
            r'$\1$',
            text_content,
            flags=re.DOTALL
        )
        # 将旧的 \bf 替换为标准的 \mathbf 
        text_content = text_content.replace(r'\bf', r'\mathbf')
        # 查找 $$ 后面只有空白字符（空格、换行、制表符等）然后是 $$ 的模式
        text_content = re.sub(r'\$\$\s*\$\$', '', text_content, flags=re.DOTALL)
        
        return text_content
    def parse_into_text(self, content: bytes) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        使用 MinerU 解析 PDF 字节流并返回格式化的文本。

        :param content: PDF 文件的字节内容。
        :return: 解析后的、按页组织的文本字符串。
        """
        logger.info(f"Parsing PDF with MinerU (pipeline backend), size: {len(content)} bytes")

        try:
            # MinerU 的 doc_analyze 函数需要一个 bytes 列表和语言列表
            pdf_bytes_list = [content]
            #预处理
            pdf_bytes_list = _prepare_pdf_bytes(pdf_bytes_list,0, None)
            # 'ch' 代表中文，'en' 代表英文。'auto' 通常也能工作得很好。
            lang_list = ['ch'] 

            # 1. 执行文档分析
            # 这个函数会返回模型推理结果、图像列表、PDF文档对象等
            infer_results, all_image_lists, all_pdf_docs, detected_langs, ocr_enabled_list = pipeline_doc_analyze(
                pdf_bytes_list, 
                lang_list,
                parse_method="auto", # 'auto' 会自动判断是文本型还是扫描型PDF
                formula_enable=True, # 启用公式识别
                table_enable=True    # 启用表格识别
            )

            if not infer_results:
                logger.warning("MinerU doc_analyze did not return any results.")
                return ""

            # 2. 将模型输出转换为中间格式 (middle_json)
            # 这是生成最终内容的前置步骤
            model_list = infer_results[0]
            images_list = all_image_lists[0]
            pdf_doc = all_pdf_docs[0]
            lang = detected_langs[0]
            ocr_enable = ocr_enabled_list[0]

            # 使用内存数据写入器，避免在磁盘上生成不必要的图片文件
            image_writer = MemoryBasedDataWriter()

            middle_json = result_to_middle_json(
                model_list, images_list, pdf_doc, image_writer, lang, ocr_enable, True
            )
            
            pdf_info = middle_json.get("pdf_info")
            if not pdf_info:
                logger.error("Failed to get pdf_info from middle_json.")
                return ""

            # 3. 从中间格式生成最终的内容列表
            content_list = pipeline_union_make(
                pdf_info, 
                MakeMode.MM_MD, 
                "images" # 即使我们不保存图片，这个参数也需要提供
            )
            # 4. 将内容列表格式化为与旧接口兼容的字符串
            final_text_markdown = self._convert_embedded_html_tables(content_list)
            #final_text_markdown = self._convert_embedded_latex(final_text_markdown)

            logger.info(f"PDF parsing with MinerU complete. Extracted {len(final_text_markdown)} text chars.")
            #logger.info(f"Sample text: {final_text_markdown}...")exit
            return final_text_markdown

        except Exception as e:
            logger.error(f"Failed to parse PDF document with MinerU: {e}", exc_info=True)
            return ""