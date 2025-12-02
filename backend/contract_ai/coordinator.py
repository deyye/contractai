import json
import asyncio
import uuid
import requests
from typing import Dict, List, Any, Optional
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import HumanMessage, HumanMessage, SystemMessage
from langgraph.graph import Graph  # 核心：LangGraph 图结构
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
    
    def _build_workflow_graph(self) -> Graph:
        """构建 LangGraph 工作流图"""
        graph = Graph()
        
        # 定义节点：每个节点对应一个工作步骤
        graph.add_node("plan_workflow", self.plan_workflow)  # 规划工作流
        graph.add_node("document_processing", self.run_document_agent)  # 文档处理
        graph.add_node("parallel_analysis", self.run_parallel_agents)  # 并行分析（法律+商业）
        graph.add_node("highlight_issues", self.run_highlight_agent)  # 重点标注
        graph.add_node("integrate_results", self.run_integration_agent)  # 结果整合
        
        # 定义边：工作流执行顺序
        graph.set_entry_point("plan_workflow")  # 入口节点
        graph.add_edge("plan_workflow", "document_processing")
        graph.add_edge("document_processing", "parallel_analysis")
        # graph.add_edge("parallel_analysis", "highlight_issues")
        # graph.add_edge("highlight_issues", "integrate_results")
        graph.add_edge("parallel_analysis", "integrate_results")
        graph.set_finish_point("integrate_results")  # 结束节点
        
        return graph.compile(checkpointer=self.memory)  # 编译图（带状态检查点）
    
    def plan_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """规划工作流（基于用户请求生成步骤）"""
        user_request = state["user_input"]
        self.logger.info(f"规划工作流输入：{user_request[:100]}...")
        
        # 调用 LLM 生成工作流（复用原提示词逻辑）
        planning_prompt = f"""根据请求制定工作流：{user_request}，可用智能体：{list(self.agents.keys())}"""
        workflow_plan = self.call_llm(planning_prompt)
        self.logger.info(f"规划工作流：{workflow_plan}")
        # 解析并返回规划结果（简化：直接返回结构化步骤）
        return {
            **state,
            "workflow_plan": workflow_plan,
            "current_step": "document_processing"
        }
    
    def run_document_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """文档处理节点：调用文档智能体"""
        self.logger.info("执行文档处理步骤")
        document_agent = self.agents["document"]
        
        # 调用文档智能体（直接调用其 invoke 方法）
        result = document_agent.invoke({
            "text": state["user_input"],
            "context": state.get("context", "")
        })
        self.logger.info(f"文档处理结果：{result}")
        return {
            **state,
            "context": f"文档处理结果：{result}",
            "document_result": result
        }

    def run_parallel_agents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """并行分析节点：同时调用法律和商业智能体"""
        self.logger.info("执行并行分析步骤")
        
        # 并行调用两个智能体（使用 asyncio 实现并发）
        async def _parallel_run():
            legal_task = asyncio.create_task(
                self.agents["legal"].ainvoke({"text": state["context"]})
            )
            business_task = asyncio.create_task(
                self.agents["business"].ainvoke({"text": state["context"]})
            )
            return await legal_task, await business_task
        
        legal_result, business_result = asyncio.run(_parallel_run())
        self.logger.info(f"法律分析：{legal_result}\n商业分析：{business_result}")
        return {
            **state,
            "context": f"法律分析：{legal_result}\n商业分析：{business_result}",
            "legal_result": legal_result,
            "business_result": business_result
        }
    
    def run_highlight_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """重点标注节点：调用高亮智能体"""
        self.logger.info("执行重点标注步骤")
        highlight_agent = self.agents["highlight"]
        
        result = highlight_agent.invoke({
            "text": state["user_input"],
            "context": state.get("context", "")
        })
        self.logger.info(f"重点标注处理结果：{result}")
        return {
            **state,
            "context": f"重点标注处理结果：{result}",
            "highlight_result": result
        }
        
    def generate_final_response(self, workflow_results: Dict[str, Any]) -> str:
        """Generate final comprehensive response"""
        summary_prompt = f"""
        基于以下工作流程执行结果，生成一份完整的合同审查报告：
        
        执行结果：
        {json.dumps(workflow_results, ensure_ascii=False, indent=2)}
        
        请生成包含以下部分的综合报告：
        1. 执行摘要
        2. 主要发现
        3. 风险评估
        4. 建议措施
        5. 结论
        
        报告应该专业、清晰、可操作。
        """
        
        final_report = self.call_llm(summary_prompt)
        return final_report
    
    def run_integration_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """结果整合节点：生成最终报告"""
        self.logger.info("整合所有结果生成报告")
        integration_agent = self.agents["integration"]
        
        # 整合所有步骤结果
        final_result = integration_agent.invoke({
            "results": {
                "document": state["document_result"],
                "legal": state["legal_result"],
                "business": state["business_result"],
                # "highlight": state["highlight_result"]
            }
        })
        
        final_result_str = json.dumps(final_result, ensure_ascii=False)
        return {** state, "final_response": final_result_str}

    def process_text_message(self, message: HumanMessage) -> HumanMessage:
        """处理用户请求（入口方法）"""
        user_input = message.content
        thread_id = str(uuid.uuid4())
        
        # 运行 LangGraph 工作流
        result = self.graph.invoke({
                "user_input": user_input,
                "context": "",
                "final_response": ""
            },
            config={"configurable": {"thread_id": thread_id}}
        )
        
        # 返回最终响应
        return HumanMessage(content=result["final_response"])
    
    def parse_pdf_through_api(self, file_path, api_url="http://127.0.0.1:8000/api/pdf/upload"):
        """
        通过API上传PDF文件并获取解析后的文本内容
        
        参数:
            file_path: PDF文件的本地路径
            api_url: API接口的完整URL
        
        返回:
            解析成功返回文本内容，失败返回错误信息
        """
        try:
            with open(file_path, 'rb') as file:
                # 构建multipart/form-data格式的请求体
                files = {
                    'file': (  # 键名必须与API要求的"file"一致
                        file_path.split('/')[-1],  # 文件名
                        file,  # 文件二进制内容
                        'application/pdf'  # MIME类型
                    )
                }
                
                response = requests.post(
                    url=api_url,
                    files=files,
                    timeout=60  # 设置超时时间，避免长期无响应
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        return {
                            'status': 'success',
                            'content': result.get('file_content')
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f"API返回失败: {result.get('message', '未知错误')}"
                        }
                else:
                    return {
                        'status': 'error',
                        'message': f"请求失败，状态码: {response.status_code}"
                    }
                    
        except FileNotFoundError:
            return {'status': 'error', 'message': f"文件未找到: {file_path}"}
        except Exception as e:
            return {'status': 'error', 'message': f"请求发生异常: {str(e)}"}
        
if __name__ == "__main__":
    coordinator = ContractCoordinator()
    pdf_file_path = "/home/star/81/bidgen/交易招标文件.pdf"
    result = coordinator.parse_pdf_through_api(pdf_file_path)
    print(f"PDF解析结果：{result}")
    test_request = HumanMessage(content=f"""请审查这份招标文件:{result["content"]}""")
    response = coordinator.process_text_message(test_request)
    print(f"最终报告：{response.content}")