import logging
import os
import io
from typing import Any, List, Tuple, Dict, Union

import fitz 
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class PDFParser(BaseParser):
    """
    一个基于 PyMuPDF 的、高度鲁棒的PDF解析器。
    它采用双策略、去重的方式来最大化表格查找的准确性和召回率。
    """
    
    def _calculate_iou(self, rect1: fitz.Rect, rect2: fitz.Rect) -> float:
        """计算两个 fitz.Rect 对象的 Intersection over Union (IoU)"""
        intersection = rect1 & rect2
        union = rect1 | rect2

        if intersection.is_empty or union.get_area() == 0:
            return 0.0

        iou = intersection.get_area() / union.get_area()
        return iou

    def _find_tables_robustly(self, page: fitz.Page, iou_threshold: float = 0.5) -> List['fitz.Table']:
        """
        使用双策略、合并去重的方式在页面上查找表格

        :param page: fitz.Page 对象。
        :param iou_threshold: 用于判断表格是否重复的IoU阈值。
        :return: 页面上所有不重复的 fitz.Table 对象列表。
        """
        
        # 策略一: "lines_strict"
        lines_strict_settings = {
            "strategy": "lines_strict",
   
        }
        lines_tables = page.find_tables(**lines_strict_settings)
        
        # 策略二: "text" 三线表
        text_settings = {
            "vertical_strategy": "text",
            "horizontal_strategy": "lines",
            "snap_tolerance": 5,   #对齐容差
            "min_words_vertical": 3,#最少3个词对齐才算一列
           
        }
        text_tables = page.find_tables(**text_settings)
        
        # 合并与去重逻辑
        unique_tables = list(lines_tables.tables)
        
        for text_table in text_tables:
            is_duplicate = False
            for line_table in unique_tables:
                rect1 = fitz.Rect(text_table.bbox)
                rect2 = fitz.Rect(line_table.bbox)
                if self._calculate_iou(rect1, rect2) > iou_threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_tables.append(text_table)
        
        return unique_tables

    def _convert_table_to_markdown(self, table_data: list) -> str:
        """
        一个更健壮的表格到 Markdown 的转换器，能够处理不规则的行（如合并单元格）。
        """
        if not table_data or not table_data[0]: return ""

        def clean_cell(cell):
            if cell is None: return ""
            return str(cell).replace("\n", " <br> ")

        try:
            # --- 关键改动 2: 全新的、更健壮的 Markdown 生成逻辑 ---
            header = [clean_cell(cell) for cell in table_data[0]]
            header_cols = len(header)
            
            markdown = "| " + " | ".join(header) + " |\n"
            markdown += "| " + " | ".join(["---"] * header_cols) + " |\n"
            
            for row in table_data[1:]:
                if not row: continue
                
                body_row_cleaned = [clean_cell(cell) for cell in row]
                
                # 规范化行，确保列数与表头一致
                current_cols = len(body_row_cleaned)
                if current_cols < header_cols:
                    # 如果行太短（常见于合并单元格），用空字符串填充
                    body_row_cleaned.extend([""] * (header_cols - current_cols))
                elif current_cols > header_cols:
                    # 如果行太长（罕见，可能由解析错误导致），则截断
                    body_row_cleaned = body_row_cleaned[:header_cols]
                
                markdown += "| " + " | ".join(body_row_cleaned) + " |\n"
                
            return markdown
        except Exception as e:
            logger.error(f"Error converting table to markdown: {e}")
            return ""

    def parse_into_text(self, content: bytes) -> Union[str, Tuple[str, Dict[str, Any]]]:
        logger.info(f"Parsing PDF with PyMuPDF (Robust Dual-Strategy), size: {len(content)} bytes")
        all_page_content = []

        try:
            pdf = fitz.open(stream=content, filetype="pdf")
            logger.info(f"PDF has {len(pdf)} pages")

            for page_num, page in enumerate(pdf):
                page_content_parts = []
                
                # --- 1. 使用高度鲁棒的方法查找表格 ---
                unique_tables = self._find_tables_robustly(page)

                # --- 2. 处理去重后的表格 ---
                if unique_tables:
                    logger.info(f"Found {len(unique_tables)} unique tables on page {page_num + 1}")
                    for table in unique_tables:
                        markdown_table = self._convert_table_to_markdown(table.extract())
                        page_content_parts.append(f"\n\n{markdown_table}\n\n")

                # --- 3. 提取非表格区域的文本 ---
                table_bboxes = [fitz.Rect(table.bbox) for table in unique_tables]
                
                text_blocks = page.get_text("blocks", sort=True)
                
                non_table_text_parts = []
                for block in text_blocks:
                    block_rect = fitz.Rect(block[0:4])
                    if not any(bbox.intersects(block_rect) for bbox in table_bboxes):
                        non_table_text_parts.append(block[4])
                
                page_content_parts.insert(0, "".join(non_table_text_parts))
                all_page_content.append("".join(page_content_parts))

            final_text = "\n\n--- Page Break ---\n\n".join(all_page_content)
            logger.info(f"PDF parsing complete. Extracted {len(final_text)} text chars.")
            return final_text
            
        except Exception as e:
            logger.error(f"Failed to parse PDF document with PyMuPDF: {e}", exc_info=True)
            return ""