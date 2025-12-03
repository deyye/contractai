import os
import shutil
import logging
import pdfplumber
from fastapi import UploadFile

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFService:
    @staticmethod
    def save_upload_file(upload_file: UploadFile, destination: str):
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            # 保存文件
            with open(destination, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
            logger.info(f"文件已保存: {destination}")
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            raise Exception(f"保存文件失败: {str(e)}")
        finally:
            upload_file.file.close()

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        text_content = []
        try:
            with pdfplumber.open(file_path) as pdf:
                if not pdf.pages:
                    return "警告：PDF文件为空"
                
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                    else:
                        # 处理扫描件或纯图片PDF的情况
                        logger.warning(f"第 {i+1} 页无法提取文本（可能是图片/扫描件）")
            
            full_text = "\n".join(text_content)
            
            if not full_text.strip():
                return "解析结果为空：该PDF可能是纯图片扫描件，当前版本仅支持提取可编辑文本。"
                
            logger.info(f"PDF解析成功，提取字符数: {len(full_text)}")
            return full_text

        except Exception as e:
            logger.error(f"PDF解析异常: {e}")
            raise Exception(f"PDF解析失败: {str(e)}")