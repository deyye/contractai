import json
import asyncio
import uuid
import logging
import requests
from typing import Dict, List, Any, Optional
import concurrent.futures

# 设置日志格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from base_agent import BaseAgent
from legal_agent import LegalAgent
from business_agent import ContractReviewAgent
from document_agent import DocumentProcessingAgent
from format_agent import FormatAgent
from highlight_agent import HighlightAgent
from integration_agent import IntegrationAgent

class ContractCoordinator(BaseAgent):
    """Main coordinator for contract review tasks"""
    
    def __init__(self):
        system_prompt = """你是合同审查系统的主协调器。你的职责是：
1. 接收用户的合同审查请求
2. 将任务分配给专业的智能体团队
3. 协调各个智能体的工作流程
4. 整合所有分析结果
5. 生成最终的综合报告

专业智能体团队包括：
- 文档处理Agent：处理文档解析和文本提取
- 法律Agent：进行法律条款分析和合规检查
- 商业Agent：分析商业条款和风险评估
- 格式Agent：检查文档格式和结构
- 高亮Agent：标注重要条款和风险点
- 整合Agent：生成最终报告

请根据用户请求制定合适的工作流程。"""
        
        super().__init__("ContractCoordinator", system_prompt)
        self.agents = {
            "document": DocumentProcessingAgent(),
            "legal": LegalAgent(),
            "business": ContractReviewAgent(),
            "format": FormatAgent(),
            "highlight": HighlightAgent(),
            "integration": IntegrationAgent()
        }
        self.memory = MemorySaver()
        self.graph = self._build_workflow_graph()
    
    def _build_workflow_graph(self):
        """构建 LangGraph 工作流图"""
        workflow = StateGraph(dict)
        
        # 定义节点
        workflow.add_node("plan_workflow", self.plan_workflow)
        workflow.add_node("document_processing", self.run_document_agent)
        workflow.add_node("parallel_analysis", self.run_parallel_agents)
        workflow.add_node("integrate_results", self.run_integration_agent)
        
        # 定义边
        workflow.set_entry_point("plan_workflow")
        workflow.add_edge("plan_workflow", "document_processing")
        workflow.add_edge("document_processing", "parallel_analysis")
        workflow.add_edge("parallel_analysis", "integrate_results")
        workflow.set_finish_point("integrate_results")
        
        return workflow.compile(checkpointer=self.memory)
    
    def plan_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """规划工作流"""
        try:
            user_request = state.get("user_input", "")
            self.logger.info(f"🔄 STEP 1: 规划工作流 - 输入长度: {len(user_request)}")
            
            # 使用简单逻辑，避免额外的LLM调用
            workflow_plan = "标准审查流程: 文档解析 -> 法律/商业分析 -> 整合报告"
            
            self.logger.info(f"✅ 工作流规划完成: {workflow_plan}")
            return {
                **state,
                "workflow_plan": workflow_plan,
                "error": None
            }
        except Exception as e:
            self.logger.error(f"❌ 规划工作流失败: {str(e)}")
            return {**state, "error": str(e)}
    
    def run_document_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """文档处理节点"""
        self.logger.info("🔄 STEP 2: 执行文档处理")
        try:
            document_agent = self.agents["document"]
            
            # 调用文档处理agent
            result = document_agent.invoke({
                "text": state["user_input"],
                "context": state.get("context", "")
            })
            
            # 验证结果
            if not result:
                raise ValueError("文档处理 Agent 返回为空")
            
            # 检查是否是错误结果
            if isinstance(result, dict) and result.get("status") == "error":
                error_msg = result.get("message", "未知错误")
                self.logger.error(f"❌ 文档处理返回错误: {error_msg}")
                return {
                    **state,
                    "document_result": result,
                    "context": f"文档处理失败: {error_msg}",
                    "error": error_msg
                }

            self.logger.info(f"✅ 文档处理完成")
            
            # 提取关键信息用于后续分析
            context_summary = self._build_context_summary(result)
            
            return {
                **state,
                "context": context_summary,
                "document_result": result,
                "error": None
            }
        except Exception as e:
            self.logger.error(f"❌ 文档处理步骤发生严重错误: {str(e)}", exc_info=True)
            return {
                **state, 
                "document_result": {"status": "error", "message": str(e)},
                "context": f"文档处理失败: {str(e)}",
                "error": str(e)
            }
    
    def _build_context_summary(self, document_result: Dict[str, Any]) -> str:
        """从文档处理结果中提取摘要信息"""
        try:
            # 如果document_result是字典格式
            if isinstance(document_result, dict):
                # 提取response_text字段
                if "response_text" in document_result:
                    return f"文档处理结果:\n{document_result['response_text']}"
                
                # 或者提取analysis字段
                if "analysis" in document_result:
                    analysis = document_result["analysis"]
                    if isinstance(analysis, dict):
                        # 提取关键信息
                        key_info = analysis.get("key_tender_information", {})
                        summary_parts = []
                        if key_info:
                            summary_parts.append(f"项目名称: {key_info.get('tender_title', '未知')}")
                            summary_parts.append(f"招标编号: {key_info.get('tender_number', '未知')}")
                            summary_parts.append(f"项目预算: {key_info.get('project_budget', '未知')}")
                        return "文档关键信息:\n" + "\n".join(summary_parts) if summary_parts else "文档处理完成"
            
            # 如果是字符串
            if isinstance(document_result, str):
                return f"文档处理结果: {document_result[:500]}..."
            
            return f"文档处理结果: {str(document_result)[:500]}..."
        except Exception as e:
            self.logger.warning(f"构建上下文摘要失败: {e}")
            return "文档处理完成（摘要生成失败）"

    def run_parallel_agents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        并行分析节点（同步版本）
        注意: BaseAgent没有ainvoke方法，这里使用同步调用但模拟并行效果
        """
        self.logger.info("🔄 STEP 3: 执行并行分析 (法律 + 商业)")
        context_text = json.dumps(state.get("document_result", {}), ensure_ascii=False)      
        # 检查是否有错误需要跳过分析
        if state.get("error"):
            self.logger.warning("⚠️ 检测到上游错误，跳过分析步骤")
            return {
                **state,
                "legal_result": "因文档处理失败而跳过法律分析",
                "business_result": "因文档处理失败而跳过商业分析"
            }
        async def _parallel_run():
            # 使用 ainvoke 异步调用
            legal_task = self.agents["legal"].ainvoke({"text": context_text})
            business_task = self.agents["business"].ainvoke({"text": context_text})
            # 并发等待
            return await asyncio.gather(legal_task, business_task, return_exceptions=True)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            # 如果我们在 FastAPI 的事件循环中，不能直接用 asyncio.run
            # 解决方案：使用线程池在另一个线程中运行一个新的 Loop
            self.logger.info("检测到运行中的 Event Loop，切换到线程池执行异步任务")
            with concurrent.futures.ThreadPoolExecutor() as pool:
                results = pool.submit(asyncio.run, _parallel_run()).result()
        else:
            # 如果是脚本直接运行，直接用 asyncio.run
            results = asyncio.run(_parallel_run())
        legal_result, business_result = results
        if isinstance(legal_result, Exception): legal_result = f"Error: {str(legal_result)}"
        if isinstance(business_result, Exception): business_result = f"Error: {str(business_result)}"

        self.logger.info("并行分析完成")
        return {
            **state,
            "legal_result": legal_result,
            "business_result": business_result
        }

    def run_integration_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """结果整合节点"""
        self.logger.info("🔄 STEP 4: 整合所有分析结果")
        try:
            integration_agent = self.agents["integration"]
            
            # 收集所有结果
            results_to_integrate = {
                "document": state.get("document_result"),
                "legal": state.get("legal_result"),
                "business": state.get("business_result"),
            }
            
            self.logger.info(f"  准备整合的结果类型: {[type(v).__name__ for v in results_to_integrate.values()]}")
            
            # 调用整合agent
            final_result = integration_agent.invoke({
                "results": results_to_integrate
            })
            
            # 将结果转换为JSON字符串
            if isinstance(final_result, dict):
                final_response = json.dumps(final_result, ensure_ascii=False, indent=2)
            elif isinstance(final_result, str):
                final_response = final_result
            else:
                final_response = str(final_result)
            
            self.logger.info(f"✅ 报告生成完成 (长度: {len(final_response)} 字符)")
            
            return {
                **state, 
                "final_response": final_response,
                "error": None
            }
        except Exception as e:
            self.logger.error(f"❌ 整合报告失败: {e}", exc_info=True)
            error_response = {
                "status": "error",
                "message": f"生成报告时发生错误: {str(e)}",
                "partial_results": {
                    "document": str(state.get("document_result", "无"))[:200],
                    "legal": str(state.get("legal_result", "无"))[:200],
                    "business": str(state.get("business_result", "无"))[:200]
                }
            }
            return {
                **state, 
                "final_response": json.dumps(error_response, ensure_ascii=False, indent=2),
                "error": str(e)
            }

    def process_text_message(self, message: HumanMessage) -> HumanMessage:
        """处理用户请求（入口方法）"""
        user_input = message.content
        thread_id = str(uuid.uuid4())
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"🚀 收到新的审查请求")
        self.logger.info(f"📝 Thread ID: {thread_id}")
        self.logger.info(f"📄 输入长度: {len(user_input)} 字符")
        self.logger.info(f"{'='*60}\n")
        
        try:
            # 运行 LangGraph 工作流
            result = self.graph.invoke(
                {
                    "user_input": user_input,
                    "context": "",
                    "final_response": "",
                    "error": None
                },
                config={"configurable": {"thread_id": thread_id}}
            )
            
            final_response = result.get("final_response", "未生成报告")
            
            # 检查是否有错误
            if result.get("error"):
                self.logger.warning(f"⚠️ 工作流执行过程中出现错误: {result['error']}")
            else:
                self.logger.info(f"✅ 工作流执行成功")
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"🏁 审查流程完成")
            self.logger.info(f"{'='*60}\n")
            
            return HumanMessage(content=final_response)
            
        except Exception as e:
            self.logger.error(f"❌ 工作流执行失败: {str(e)}", exc_info=True)
            error_message = f"审查流程失败: {str(e)}\n请检查日志获取详细信息"
            return HumanMessage(content=error_message)

    def parse_pdf_through_api(self, file_path, api_url="http://127.0.0.1:8000/api/pdf/upload"):
        """通过API解析PDF文件"""
        try:
            self.logger.info(f"📤 开始上传 PDF: {file_path}")
            
            import os
            if not os.path.exists(file_path):
                self.logger.error(f"❌ 文件不存在: {file_path}")
                return {'status': 'error', 'message': f"文件不存在: {file_path}"}
            
            file_size = os.path.getsize(file_path)
            self.logger.info(f"  文件大小: {file_size / 1024:.2f} KB")
            
            with open(file_path, 'rb') as file:
                files = {'file': (file_path.split('/')[-1], file, 'application/pdf')}
                
                self.logger.info(f"  正在调用PDF解析API: {api_url}")
                response = requests.post(api_url, files=files, timeout=120)
                
                if response.status_code == 200:
                    self.logger.info("✅ PDF 解析成功")
                    return response.json()
                else:
                    self.logger.error(f"❌ PDF 解析失败: HTTP {response.status_code}")
                    self.logger.error(f"  响应内容: {response.text[:500]}")
                    return {
                        'status': 'error', 
                        'message': f"API Error: {response.status_code} - {response.text[:200]}"
                    }
                    
        except FileNotFoundError:
            self.logger.error(f"❌ 文件未找到: {file_path}")
            return {'status': 'error', 'message': f"文件未找到: {file_path}"}
        except requests.exceptions.Timeout:
            self.logger.error(f"❌ PDF解析API超时")
            return {'status': 'error', 'message': "PDF解析超时，请检查文件大小或API状态"}
        except Exception as e:
            self.logger.error(f"❌ 文件操作异常: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

if __name__ == "__main__":
    print("\n" + "="*60)
    print("合同审查系统 - 测试模式")
    print("="*60 + "\n")
    
    # 创建协调器
    coordinator = ContractCoordinator()
    
    # 测试PDF解析
    pdf_file_path = "/home/star/81/bidgen/交易招标文件.pdf"
    
    print(f"📂 PDF文件路径: {pdf_file_path}\n")
    
    result = coordinator.parse_pdf_through_api(pdf_file_path)
    
    if result.get("success"):
        test_content = result.get("file_content", "")
        print(f"✅ PDF解析成功，内容长度: {len(test_content)} 字符\n")
    else:
        print(f"❌ PDF解析失败: {result.get('message', '未知错误')}\n")
        test_content = "无法解析 PDF 文件内容。"
    
    # 开始审查流程
    print("="*60)
    print("开始执行合同审查工作流...")
    print("="*60 + "\n")
    
    test_request = HumanMessage(content=f"""请审查这份招标文件: {test_content[:5000]}""")  # 限制长度避免超长
    
    response = coordinator.process_text_message(test_request)
    
    print("\n" + "="*60)
    print("最终审查报告")
    print("="*60)
    print(response.content)
    print("="*60 + "\n")