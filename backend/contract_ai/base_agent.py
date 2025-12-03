"""
优化后的基础智能体类
Optimized Base Agent with Caching, Performance Monitoring and Retry Logic
"""
import json
import logging
import time
import hashlib
from typing import Dict, Any, Optional, List
from functools import lru_cache, wraps
from datetime import datetime, timedelta
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_deepseek import ChatDeepSeek
from config import Config

# 简单的内存缓存实现
class SimpleCache:
    """简单的内存缓存类"""
    def __init__(self, ttl: int = 3600, max_size: int = 100):
        self.cache: Dict[str, tuple] = {}  # key -> (value, expire_time)
        self.ttl = ttl
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self.cache:
            value, expire_time = self.cache[key]
            if datetime.now() < expire_time:
                self.hits += 1
                return value
            else:
                del self.cache[key]
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        # LRU淘汰
        if len(self.cache) >= self.max_size:
            # 删除最早过期的项
            oldest_key = min(self.cache.items(), key=lambda x: x[1][1])[0]
            del self.cache[oldest_key]
        
        expire_time = datetime.now() + timedelta(seconds=self.ttl)
        self.cache[key] = (value, expire_time)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def stats(self) -> Dict[str, int]:
        """缓存统计"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "size": len(self.cache)
        }

def performance_monitor(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        try:
            result = func(self, *args, **kwargs)
            elapsed = time.time() - start_time
            
            if Config.LOG_CONFIG.enable_performance_log:
                self.logger.info(
                    f"⏱️ {func.__name__} 执行时间: {elapsed:.2f}秒"
                )
            
            # 记录性能指标
            if not hasattr(self, '_performance_metrics'):
                self._performance_metrics = []
            self._performance_metrics.append({
                "function": func.__name__,
                "elapsed": elapsed,
                "timestamp": datetime.now().isoformat()
            })
            
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(
                f"❌ {func.__name__} 执行失败 (耗时: {elapsed:.2f}秒): {str(e)}"
            )
            raise
    return wrapper

def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """错误重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        self.logger.warning(
                            f"⚠️ {func.__name__} 第 {attempt + 1} 次尝试失败: {str(e)}，{delay}秒后重试"
                        )
                        time.sleep(delay * (attempt + 1))  # 指数退避
                    else:
                        self.logger.error(
                            f"❌ {func.__name__} 所有重试均失败: {str(e)}"
                        )
            raise last_exception
        return wrapper
    return decorator

class BaseAgent(Runnable):
    """优化后的基础智能体类"""
    
    def __init__(self, agent_name: str, system_prompt: str):
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.llm_config = Config.LLM_CONFIG
        self.cache_config = Config.CACHE_CONFIG
        self.performance_config = Config.PERFORMANCE_CONFIG
        self.processing_config = Config.PROCESSING_CONFIG
        
        # 设置日志
        self.logger = logging.getLogger(agent_name)
        
        # 初始化LLM
        self.llm = ChatDeepSeek(
            api_key=self.llm_config.api_key,
            model=self.llm_config.model,
            temperature=self.llm_config.temperature,
            timeout=self.llm_config.timeout
        )
        
        # 初始化缓存
        if self.cache_config.enabled:
            self.cache = SimpleCache(
                ttl=self.cache_config.ttl,
                max_size=self.cache_config.max_size
            )
        else:
            self.cache = None
        
        # 性能指标
        self._performance_metrics = []
        
        self.logger.info(f"✅ {agent_name} 初始化完成 (缓存: {self.cache_config.enabled})")
    
    def _generate_cache_key(self, text: str, context: Optional[str] = None) -> str:
        """生成缓存键"""
        content = text + (context or "")
        return hashlib.md5(content.encode()).hexdigest()
    
    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        if not self.processing_config.enable_preprocessing:
            return text
        
        # 移除多余空白
        text = ' '.join(text.split())
        
        # 截断过长文本
        if len(text) > self.processing_config.max_text_length:
            self.logger.warning(
                f"⚠️ 文本过长 ({len(text)} 字符)，截断至 {self.processing_config.max_text_length} 字符"
            )
            text = text[:self.processing_config.max_text_length]
        
        return text
    
    def _compress_text(self, text: str) -> str:
        """智能文本压缩 - 保留关键信息"""
        if not self.processing_config.enable_text_compression:
            return text
        
        if len(text) <= self.processing_config.chunk_size:
            return text
        
        # 简单压缩：保留开头和重要部分
        chunks = []
        chunk_size = self.processing_config.chunk_size
        
        # 保留前半部分
        chunks.append(text[:chunk_size])
        
        # 提取中间重要句子（包含关键词的）
        important_keywords = ['风险', '违约', '责任', '义务', '权利', '付款', '价格', '标准', '要求']
        middle_text = text[chunk_size:-chunk_size] if len(text) > chunk_size * 2 else ""
        
        if middle_text:
            sentences = middle_text.split('。')
            important_sentences = [
                s for s in sentences 
                if any(kw in s for kw in important_keywords)
            ][:10]  # 最多10句
            chunks.extend(important_sentences)
        
        # 保留结尾部分
        if len(text) > chunk_size:
            chunks.append(text[-chunk_size:])
        
        compressed = '。'.join(chunks)
        
        if len(compressed) < len(text):
            self.logger.info(
                f"📦 文本压缩: {len(text)} -> {len(compressed)} 字符 "
                f"(压缩率: {(1 - len(compressed)/len(text)) * 100:.1f}%)"
            )
        
        return compressed
    
    def invoke(self, input: dict, config=None, **kwargs):
        """实现LangChain Runnable接口"""
        user_text = input.get("text", "")
        context = input.get("context", "")
        return self.process_text_message(user_text, context)
    
    @performance_monitor
    @retry_on_error(max_retries=3, delay=1.0)
    def call_llm(
        self, 
        user_message: str, 
        conversation_history: Optional[List[Dict]] = None,
        use_cache: bool = True
    ) -> str:
        """调用LLM（带缓存和重试机制）"""
        
        # 检查缓存
        if use_cache and self.cache:
            cache_key = self._generate_cache_key(user_message)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                self.logger.info("✨ 缓存命中")
                return cached_result
        
        # 预处理和压缩
        processed_message = self._preprocess_text(user_message)
        if self.processing_config.enable_text_compression:
            processed_message = self._compress_text(processed_message)
        
        # 构建消息列表
        messages = [SystemMessage(content=self.system_prompt)]
        
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=processed_message))
        
        # 调用LLM
        response = self.llm.invoke(messages)
        result = response.content
        
        # 缓存结果
        if use_cache and self.cache:
            self.cache.set(cache_key, result)
        
        return result
    
    @performance_monitor
    def process_text_message(self, user_text: str, context: str = "") -> str:
        """处理文本消息（优化版本）"""
        try:
            # 验证输入
            if len(user_text) < self.processing_config.min_text_length:
                return "输入文本过短，请提供更多内容以进行分析。"
            
            self.logger.info(
                f"📝 处理消息: {len(user_text)} 字符"
                + (f" (上下文: {len(context)} 字符)" if context else "")
            )
            
            # 组合文本和上下文
            full_text = user_text
            if context:
                full_text = f"上下文信息：\n{context}\n\n待分析内容：\n{user_text}"
            
            # 调用LLM
            response_text = self.call_llm(full_text)
            
            return response_text
            
        except Exception as e:
            self.logger.error(f"❌ 消息处理错误: {str(e)}", exc_info=True)
            return f"处理消息时发生错误：{str(e)}"
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if self.cache:
            return self.cache.stats()
        return {"enabled": False}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        if not self._performance_metrics:
            return {"total_calls": 0}
        
        total_calls = len(self._performance_metrics)
        total_time = sum(m["elapsed"] for m in self._performance_metrics)
        avg_time = total_time / total_calls
        
        return {
            "total_calls": total_calls,
            "total_time": total_time,
            "avg_time": avg_time,
            "recent_calls": self._performance_metrics[-10:]  # 最近10次调用
        }
    
    def clear_cache(self):
        """清空缓存"""
        if self.cache:
            self.cache.clear()
            self.logger.info("🗑️ 缓存已清空")
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().isoformat()