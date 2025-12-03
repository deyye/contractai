"""
优化后的协调器
Optimized Coordinator with Improved Parallel Processing and Data Flow
"""
import json
import asyncio
import uuid
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from base_agent import BaseAgent
from config import Config

# 简化的智能体导入（实际使用时需要优化版本）
try:
    from legal_agent import LegalAgent
    from business_agent import ContractReviewAgent  
    from document_agent import DocumentProcessingAgent
    from integration_agent import IntegrationAgent
except ImportError:
    # 如果原始智能体不可用，使用占位符
    LegalAgent = None
    ContractReviewAgent = None
    DocumentProcessingAgent = None
    IntegrationAgent = None

@dataclass
class WorkflowMetrics:
    """工作流性能指标"""
    total_time: float = 0.0
    document_time: float = 0.0
    parallel_time: float = 0.0
    integration_time: float = 0.0
    cache_hits: int = 0
    total_tokens: int = 0

class ContractCoordinator(BaseAgent):
    """优化后的协调器"""
    
    def __init__(self):
        system_prompt = """你是合同审查系统的主协调器。你的职责是：
1. 接收用户的合同审查请求
2. 高效地将任务分配给专业智能体团队
3. 优化并行处理流程，减少等待时间
4. 智能整合各方分析结果
5. 生成高质量的综合报告

你应该：
- 最小化数据传输开销
- 优化任务调度策略
- 确保结果的一致性和完整性
- 提供清晰的进度反馈"""
        
        super().__init__("OptimizedCoordinator", system_prompt)
        
        # 初始化专业智能体
        self.agents = self._initialize_agents()
        
        # 工作流配置
        self.memory = MemorySaver()
        self.graph = self._build_workflow_graph()
        
        # 性能配置
        self.executor = ThreadPoolExecutor(
            max_workers=Config.PERFORMANCE_CONFIG.max_workers
        )
        
        self.logger.info("✅ 优化协调器初始化完成")
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """初始化智能体（延迟加载）"""
        agents = {}
        
        # 使用延迟初始化，避免启动时的性能开销
        agent_classes = {
            "document": DocumentProcessingAgent,
            "legal": LegalAgent,
            "business": ContractReviewAgent,
            "integration": IntegrationAgent
        }
        
        for name, agent_class in agent_classes.items():
            if agent_class is not None:
                try:
                    agents[name] = agent_class()
                    self.logger.info(f"✅ {name} 智能体加载成功")
                except Exception as e:
                    self.logger.warning(f"⚠️ {name} 智能体加载失败: {e}")
                    agents[name] = None
            else:
                agents[name] = None
        
        return agents
    
    def _build_workflow_graph(self):
        """构建优化的工作流图"""
        workflow = StateGraph(dict)
        
        # 定义节点
        workflow.add_node("plan", self.plan_workflow)
        workflow.add_node("document", self.run_document_agent_optimized)
        workflow.add_node("parallel", self.run_parallel_agents_optimized)
        workflow.add_node("integrate", self.run_integration_agent_optimized)
        
        # 定义流程
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "document")
        workflow.add_edge("document", "parallel")
        workflow.add_edge("parallel", "integrate")
        workflow.set_finish_point("integrate")
        
        return workflow.compile(checkpointer=self.memory)
    
    def plan_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """快速规划工作流（无需LLM调用）"""
        start_time = time.time()
        
        user_input = state.get("user_input", "")
        input_length = len(user_input)
        
        self.logger.info(f"🔄 [STEP 1] 规划工作流")
        self.logger.info(f"  输入长度: {input_length:,} 字符")
        
        # 基于输入长度选择处理策略
        if input_length < 1000:
            strategy = "快速处理"
            use_compression = False
        elif input_length < 10000:
            strategy = "标准处理"
            use_compression = False
        else:
            strategy = "分块处理"
            use_compression = True
        
        elapsed = time.time() - start_time
        self.logger.info(f"✅ 规划完成: {strategy} (耗时: {elapsed:.2f}秒)")
        
        return {
            **state,
            "workflow_plan": strategy,
            "use_compression": use_compression,
            "metrics": WorkflowMetrics(),
            "error": None
        }
    
    def run_document_agent_optimized(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """优化的文档处理"""
        start_time = time.time()
        self.logger.info("🔄 [STEP 2] 文档处理")
        
        try:
            document_agent = self.agents.get("document")
            if not document_agent:
                raise ValueError("文档处理智能体不可用")
            
            # 准备输入
            user_input = state["user_input"]
            use_compression = state.get("use_compression", False)
            
            # 如果需要压缩，预处理文本
            if use_compression:
                user_input = self._compress_text(user_input)
                self.logger.info(f"  📦 已压缩输入文本")
            
            # 调用文档处理
            result = document_agent.invoke({
                "text": user_input
                # "context": ""
            })
            
            # 提取关键信息（减少数据传输）
            context_summary = self._extract_key_info(result)
            
            elapsed = time.time() - start_time
            self.logger.info(f"✅ 文档处理完成 (耗时: {elapsed:.2f}秒)")
            
            # 更新性能指标
            metrics = state.get("metrics", WorkflowMetrics())
            metrics.document_time = elapsed
            
            return {
                **state,
                "document_result": result,
                "context_summary": context_summary,
                "metrics": metrics,
                "error": None
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"❌ 文档处理失败 (耗时: {elapsed:.2f}秒): {e}")
            return {
                **state,
                "document_result": {"status": "error", "message": str(e)},
                "context_summary": "",
                "error": str(e)
            }
    
    def _extract_key_info(self, result: Any) -> str:
        """提取关键信息，减少数据传输量"""
        try:
            if isinstance(result, dict):
                # 只提取关键字段
                key_fields = ["key_points", "summary", "risk_areas", "important_clauses"]
                extracted = {}
                
                for field in key_fields:
                    if field in result:
                        extracted[field] = result[field]
                
                if "response_text" in result:
                    # 只保留前1000字符
                    text = result["response_text"]
                    extracted["summary"] = text[:1000] if len(text) > 1000 else text
                
                return json.dumps(extracted, ensure_ascii=False)
            
            elif isinstance(result, str):
                # 截断长文本
                return result[:1000] if len(result) > 1000 else result
            
            return str(result)[:500]
            
        except Exception as e:
            self.logger.warning(f"⚠️ 提取关键信息失败: {e}")
            return ""
    
    def run_parallel_agents_optimized(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """优化的并行分析"""
        start_time = time.time()
        self.logger.info("🔄 [STEP 3] 并行分析 (法律 + 商业)")
        
        # 检查上游错误
        if state.get("error"):
            self.logger.warning("⚠️ 检测到上游错误，跳过分析")
            return {
                **state,
                "legal_result": "因上游错误跳过",
                "business_result": "因上游错误跳过"
            }
        
        try:
            # 准备共享输入（使用压缩后的上下文）
            context_summary = state.get("context_summary", "")
            
            # 并行执行
            legal_agent = self.agents.get("legal")
            business_agent = self.agents.get("business")
            
            if not legal_agent or not business_agent:
                raise ValueError("分析智能体不可用")
            
            # 使用线程池并行执行
            futures = {
                self.executor.submit(
                    self._safe_agent_invoke, 
                    legal_agent, 
                    context_summary,
                    "法律分析"
                ): "legal",
                self.executor.submit(
                    self._safe_agent_invoke,
                    business_agent,
                    context_summary,
                    "商业分析"
                ): "business"
            }
            
            results = {}
            for future in as_completed(futures):
                agent_type = futures[future]
                try:
                    result = future.result(timeout=60)
                    results[agent_type] = result
                    self.logger.info(f"  ✅ {agent_type} 分析完成")
                except Exception as e:
                    self.logger.error(f"  ❌ {agent_type} 分析失败: {e}")
                    results[agent_type] = f"Error: {str(e)}"
            
            elapsed = time.time() - start_time
            self.logger.info(f"✅ 并行分析完成 (耗时: {elapsed:.2f}秒)")
            
            # 更新性能指标
            metrics = state.get("metrics", WorkflowMetrics())
            metrics.parallel_time = elapsed
            
            return {
                **state,
                "legal_result": results.get("legal", "未执行"),
                "business_result": results.get("business", "未执行"),
                "metrics": metrics
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"❌ 并行分析失败 (耗时: {elapsed:.2f}秒): {e}")
            return {
                **state,
                "legal_result": f"Error: {str(e)}",
                "business_result": f"Error: {str(e)}"
            }
    
    def _safe_agent_invoke(self, agent, text: str, agent_name: str) -> Any:
        """安全的智能体调用（带超时和异常处理）"""
        try:
            result = agent.invoke({"text": text})
            return result
        except Exception as e:
            self.logger.error(f"❌ {agent_name} 调用失败: {e}")
            raise
    
    def run_integration_agent_optimized(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """优化的结果整合"""
        start_time = time.time()
        self.logger.info("🔄 [STEP 4] 整合结果")
        
        try:
            integration_agent = self.agents.get("integration")
            if not integration_agent:
                # 如果整合智能体不可用，使用简单整合
                return self._simple_integration(state)
            
            # 收集结果（只传递必要信息）
            results = {
                "document": self._extract_key_info(state.get("document_result")),
                "legal": self._extract_key_info(state.get("legal_result")),
                "business": self._extract_key_info(state.get("business_result"))
            }
            
            # 调用整合智能体
            final_result = integration_agent.invoke({"results": results})
            
            # 格式化输出
            if isinstance(final_result, dict):
                final_response = json.dumps(final_result, ensure_ascii=False, indent=2)
            else:
                final_response = str(final_result)
            
            elapsed = time.time() - start_time
            self.logger.info(f"✅ 整合完成 (耗时: {elapsed:.2f}秒)")
            
            # 更新性能指标
            metrics = state.get("metrics", WorkflowMetrics())
            metrics.integration_time = elapsed
            metrics.total_time = (
                metrics.document_time + 
                metrics.parallel_time + 
                metrics.integration_time
            )
            
            # 记录性能报告
            self._log_performance_report(metrics)
            
            return {
                **state,
                "final_response": final_response,
                "metrics": metrics,
                "error": None
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"❌ 整合失败 (耗时: {elapsed:.2f}秒): {e}")
            return self._simple_integration(state)
    
    def _simple_integration(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """简单的结果整合（后备方案）"""
        self.logger.info("  使用简单整合模式")
        
        report = {
            "status": "success",
            "summary": "审查完成",
            "document_analysis": str(state.get("document_result", ""))[:500],
            "legal_analysis": str(state.get("legal_result", ""))[:500],
            "business_analysis": str(state.get("business_result", ""))[:500],
            "note": "使用简化模式生成报告"
        }
        
        return {
            **state,
            "final_response": json.dumps(report, ensure_ascii=False, indent=2)
        }
    
    def _log_performance_report(self, metrics: WorkflowMetrics):
        """记录性能报告"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 性能报告")
        self.logger.info("="*60)
        self.logger.info(f"  总耗时: {metrics.total_time:.2f} 秒")
        self.logger.info(f"  ├─ 文档处理: {metrics.document_time:.2f} 秒")
        self.logger.info(f"  ├─ 并行分析: {metrics.parallel_time:.2f} 秒")
        self.logger.info(f"  └─ 结果整合: {metrics.integration_time:.2f} 秒")
        
        if self.cache:
            cache_stats = self.cache.stats()
            self.logger.info(f"  缓存命中率: {cache_stats['hit_rate']*100:.1f}%")
        
        self.logger.info("="*60 + "\n")
    
    def process_text_message(self, message: HumanMessage) -> HumanMessage:
        """处理用户请求（入口）"""
        user_input = message.content
        thread_id = str(uuid.uuid4())
        
        self.logger.info("\n" + "="*60)
        self.logger.info("🚀 收到新的审查请求")
        self.logger.info(f"📝 Thread ID: {thread_id}")
        self.logger.info(f"📄 输入长度: {len(user_input):,} 字符")
        self.logger.info("="*60 + "\n")
        
        workflow_start = time.time()
        
        try:
            # 运行工作流
            result = self.graph.invoke(
                {
                    "user_input": user_input,
                    "final_response": "",
                    "error": None
                },
                config={"configurable": {"thread_id": thread_id}}
            )
            
            final_response = result.get("final_response", "未生成报告")
            
            workflow_elapsed = time.time() - workflow_start
            
            if result.get("error"):
                self.logger.warning(f"⚠️ 工作流存在错误: {result['error']}")
            else:
                self.logger.info(f"✅ 工作流执行成功")
            
            self.logger.info(f"\n🏁 审查流程完成 (总耗时: {workflow_elapsed:.2f}秒)\n")
            
            return HumanMessage(content=final_response)
            
        except Exception as e:
            workflow_elapsed = time.time() - workflow_start
            self.logger.error(
                f"❌ 工作流失败 (耗时: {workflow_elapsed:.2f}秒): {e}",
                exc_info=True
            )
            error_message = f"审查流程失败: {str(e)}"
            return HumanMessage(content=error_message)
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("优化版合同审查系统 - 测试模式")
    print("="*60 + "\n")
    
    coordinator = OptimizedCoordinator()
    
    # 测试请求
    test_content = """
    请审查以下合同条款：
    
    甲方：某科技公司
    乙方：某服务商
    
    合同金额：100万元
    付款方式：预付30%，项目验收后支付70%
    履行期限：6个月
    违约责任：逾期违约金为合同总额的0.1%/日
    """
    
    test_request = HumanMessage(content=test_content)
    response = coordinator.process_text_message(test_request)
    
    print("\n" + "="*60)
    print("审查报告")
    print("="*60)
    print(response.content)
    print("="*60 + "\n")