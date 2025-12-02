import json
import asyncio
import uuid
import logging
import requests
from typing import Dict, List, Any, Optional

# 设置日志格式，方便调试
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
        workflow.add_node("highlight_issues", self.run_highlight_agent)
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
            self.logger.info(f"STEP 1: 规划工作流 - 输入长度: {len(user_request)}")
            
            # 这里可以使用更简单的逻辑，避免每次都调 LLM 规划，节省时间
            # 如果必须调用，请确保有超时控制
            workflow_plan = "标准审查流程: 文档解析 -> 法律/商业分析 -> 整合报告"
            
            return {
                **state,
                "workflow_plan": workflow_plan,
                "error": None
            }
        except Exception as e:
            self.logger.error(f"规划工作流失败: {str(e)}")
            return {**state, "error": str(e)}
    
    def run_document_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """文档处理节点"""
        self.logger.info("STEP 2: 执行文档处理")
        try:
            document_agent = self.agents["document"]
            
            # 增加 try-catch 捕获文档处理内部的错误（如 JSON 解析失败）
            result = document_agent.invoke({
                "text": state["user_input"],
                "context": state.get("context", "")
            })
            
            # 简单的结果验证
            if not result:
                raise ValueError("文档处理 Agent 返回为空")

            self.logger.info(f"文档处理完成，结果摘要: {str(result)[:100]}...")
            
            return {
                **state,
                "context": f"文档结构化信息：{result}", # 将结构化结果传入 Context 供后续使用
                "document_result": result
            }
        except Exception as e:
            self.logger.error(f"文档处理步骤发生严重错误: {str(e)}", exc_info=True)
            # 返回错误状态，但不中断流程，让后续步骤知道出错了
            return {
                **state, 
                "document_result": {"error": str(e)},
                "context": f"文档处理失败: {str(e)}"
            }

    async def _execute_parallel_tasks(self, context_text: str):
        """辅助方法：真正的并发执行"""
        # 使用 ainvoke 确保是异步调用
        # 注意：LegalAgent 和 BusinessAgent 内部必须实现异步逻辑或不阻塞主线程
        legal_future = self.agents["legal"].ainvoke({"text": context_text})
        business_future = self.agents["business"].ainvoke({"text": context_text})
        
        # 使用 asyncio.gather 并发等待所有结果
        return await asyncio.gather(legal_future, business_future, return_exceptions=True)

    async def run_parallel_agents_async(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """异步版本的并行分析节点"""
        self.logger.info("STEP 3: 执行并行分析 (法律 + 商业)")
        context = state.get("context", "")
        
        try:
            # 并发执行
            results = await self._execute_parallel_tasks(context)
            legal_result, business_result = results

            # 处理可能的异常（因为 return_exceptions=True）
            if isinstance(legal_result, Exception):
                self.logger.error(f"法律分析出错: {legal_result}")
                legal_result = f"法律分析失败: {str(legal_result)}"
            
            if isinstance(business_result, Exception):
                self.logger.error(f"商业分析出错: {business_result}")
                business_result = f"商业分析失败: {str(business_result)}"

            self.logger.info("并行分析完成")
            return {
                **state,
                "legal_result": legal_result,
                "business_result": business_result
            }
        except Exception as e:
            self.logger.error(f"并行分析步骤崩溃: {str(e)}")
            return {**state, "error": str(e)}

    def run_parallel_agents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步包装器：为了适配 LangGraph 如果它在同步模式下运行。
        但在生产环境中，建议直接使用异步 Graph。
        这里为了修复原本 asyncio.run 的问题，我们尝试获取当前 Loop。
        """
        try:
            loop = asyncio.get_running_loop()
            # 如果已经在 Loop 中（例如 FastAPI），必须使用 create_task 或直接 await（如果当前函数是 async）
            # 由于 LangGraph 节点定义通常是同步函数签名，这里是一个 tricky 的点。
            # 最佳实践是将 graph 编译为异步，然后节点函数全部定义为 async def。
            # 这里为了兼容性，使用 nest_asyncio 或者假设外部调用是同步的。
            
            # 临时方案：如果已经在 loop 中，说明是异步环境，这里作为同步节点会阻塞。
            # 建议：将此方法改为 async def run_parallel_agents(...)，LangGraph 支持 async 节点。
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(self.run_parallel_agents_async(state))
        except RuntimeError:
            # 如果没有运行的 loop，则创建一个新的
            return asyncio.run(self.run_parallel_agents_async(state))

    def run_highlight_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """重点标注节点"""
        # ... (保持原逻辑，增加 try-except)
        return state

    def run_integration_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """结果整合节点"""
        self.logger.info("STEP 4: 整合结果")
        try:
            integration_agent = self.agents["integration"]
            
            final_result = integration_agent.invoke({
                "results": {
                    "document": state.get("document_result"),
                    "legal": state.get("legal_result"),
                    "business": state.get("business_result"),
                }
            })
            
            return {**state, "final_response": json.dumps(final_result, ensure_ascii=False)}
        except Exception as e:
            self.logger.error(f"整合报告失败: {e}")
            return {**state, "final_response": "生成报告时发生错误，请检查日志。"}

    def process_text_message(self, message: HumanMessage) -> HumanMessage:
        """处理用户请求（入口方法）"""
        user_input = message.content
        thread_id = str(uuid.uuid4())
        self.logger.info(f"收到请求，Thread ID: {thread_id}")
        
        # 运行 LangGraph 工作流
        # 注意：这里直接调用 invoke 是同步阻塞的
        result = self.graph.invoke({
                "user_input": user_input,
                "context": "",
                "final_response": ""
            },
            config={"configurable": {"thread_id": thread_id}}
        )
        
        return HumanMessage(content=result.get("final_response", "No response generated"))

    def parse_pdf_through_api(self, file_path, api_url="http://127.0.0.1:8000/api/pdf/upload"):
        try:
            self.logger.info(f"开始上传 PDF: {file_path}")
            with open(file_path, 'rb') as file:
                files = {'file': (file_path.split('/')[-1], file, 'application/pdf')}
                response = requests.post(api_url, files=files, timeout=120) # 增加超时时间到 120s
                
                if response.status_code == 200:
                    self.logger.info("PDF 解析 API 返回成功")
                    return response.json() # 这里假设 API 直接返回 JSON 结构
                else:
                    self.logger.error(f"PDF 解析失败: {response.status_code} - {response.text}")
                    return {'status': 'error', 'message': f"API Error: {response.status_code}"}
        except Exception as e:
            self.logger.error(f"文件操作异常: {e}")
            return {'status': 'error', 'message': str(e)}

if __name__ == "__main__":
    # 单元测试逻辑
    import os
    coordinator = ContractCoordinator()
    
    pdf_file_path = "/home/star/81/bidgen/交易招标文件.pdf"
    result = coordinator.parse_pdf_through_api(pdf_file_path)
    if result.get("success"):
        test_content = result.get("file_content", "")
    else:
        test_content = "无法解析 PDF 文件内容。"
    print("开始测试工作流...")
    test_request = HumanMessage(content=f"""请审查这份招标文件: {test_content}""")
    response = coordinator.process_text_message(test_request)
    print(f"最终报告：{response.content}")