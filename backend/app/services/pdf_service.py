import pdfplumber
import os

class PDFService:
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        text_content = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            return "\n".join(text_content)
        except Exception as e:
            raise Exception(f"PDF解析失败: {str(e)}")

    @staticmethod
    def save_upload_file(upload_file, destination: str):
        try:
            with open(destination, "wb") as buffer:
                import shutil
                shutil.copyfileobj(upload_file.file, buffer)
        finally:
            upload_file.file.close()