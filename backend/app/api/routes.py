from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
import os
import uuid
import sys

# 将 contract_ai 加入路径，确保能 import
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from contract_ai.coordinator import ContractCoordinator
from app.services.pdf_service import PDFService

router = APIRouter()

# 初始化协调器 (单例模式)
# 注意：确保环境变量 DEEPSEEK_API_KEY 已设置
coordinator = ContractCoordinator()

# --- 请求模型 ---
class ReviewRequest(BaseModel):
    contract_text: str
    context: str = ""

# --- 接口实现 ---

@router.post("/pdf/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    对应 coordinator.py 中 parse_pdf_through_api 调用的接口
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名防止冲突
    file_id = str(uuid.uuid4())
    file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
    
    try:
        # 1. 保存文件
        PDFService.save_upload_file(file, file_path)
        
        # 2. 解析内容
        content = PDFService.extract_text_from_pdf(file_path)
        
        return {
            "success": True,
            "message": "Upload and parse successful",
            "file_id": file_id,
            "file_content": content # 返回解析后的文本给 Coordinator
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/review")
async def start_review(request: ReviewRequest):
    """
    触发智能体工作流
    """
    try:
        # 构造 LangChain 的 HumanMessage
        from langchain_core.messages import HumanMessage
        msg = HumanMessage(content=request.contract_text)
        
        # 调用你的 Coordinator
        # process_text_message 是同步的还是异步的？
        # 你的 coordinator.py 中 process_text_message 是同步方法，但内部调用了 graph.invoke
        response = coordinator.process_text_message(msg)
        
        # 你的 process_text_message 返回的是 HumanMessage 对象
        return {
            "status": "success",
            "result": response.content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review process failed: {str(e)}")

@router.get("/health")
def health_check():
    return {"status": "active", "agents": list(coordinator.agents.keys())}