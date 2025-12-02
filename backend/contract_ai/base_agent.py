import json
import logging
import requests
from typing import Dict, Any, Optional
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek
from config import LLMConfig

class BaseAgent(Runnable):  # 继承 LangChain 的 Runnable 接口
    def __init__(self, agent_name: str, system_prompt: str):
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.llm_config = LLMConfig.LLM_CONFIG
        self.logger = logging.getLogger(agent_name)
        self.setup_logging()
        self.llm = ChatDeepSeek(
            api_key=self.llm_config.api_key,
            model=self.llm_config.model,
            temperature=self.llm_config.temperature
        )
        

    def setup_logging(self):
        """保留原日志配置逻辑"""
        logging.basicConfig(
            level=logging.INFO,
            format=f'%(asctime)s - {self.agent_name} - %(levelname)s - %(message)s'
        )
        
    def invoke(self, input: dict, config=None, **kwargs):
        """实现 LangChain Runnable 接口，接收输入并返回处理结果"""
        user_text = input.get("text", "")
        return self.process_text_message(user_text)
    
    def call_llm(self, user_message: str, conversation_history: Optional[list] = None) -> str:
        """改造为基于 LangChain LLM 的调用方法"""
        try:
            # 构建消息列表（兼容 LangChain 消息格式）
            messages = [SystemMessage(content=self.system_prompt)]
            
            if conversation_history:
                # 若有历史记录，转换为 LangChain 消息格式
                messages.extend([
                    HumanMessage(content=msg["content"]) if msg["role"] == "user" 
                    else SystemMessage(content=msg["content"]) 
                    for msg in conversation_history
                ])
            
            # 添加当前用户消息
            messages.append(HumanMessage(content=user_message))
            
            # 调用 LangChain LLM 的 invoke 方法
            response = self.llm.invoke(messages)
            return response.content  # 直接返回响应内容
            
        except Exception as e:
            self.logger.error(f"LLM 调用异常: {str(e)}")
            return f"LLM 调用失败: {str(e)}"
    
    def process_text_message(self, user_text: str) -> str:
        """简化消息处理流程，直接返回文本结果（供 LangGraph 调用）"""
        try:
            self.logger.info(f"处理消息: {user_text[:100]}...")
            response_text = self.call_llm(user_text)
            return response_text
        except Exception as e:
            self.logger.error(f"消息处理错误: {str(e)}")
            return f"处理消息时发生错误：{str(e)}"
        
    def _get_current_timestamp(self) -> str:
        """辅助方法：获取当前时间戳（新增，便于日志和状态追踪）"""
        from datetime import datetime
        return datetime.now().isoformat()
