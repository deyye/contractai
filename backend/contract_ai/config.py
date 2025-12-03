"""
优化的配置文件 - 包含日志配置
Optimized Configuration with Logging Setup
"""

import os
import sys
import logging
from dataclasses import dataclass
from typing import Dict, Any
from logging.handlers import RotatingFileHandler
from langchain_deepseek import ChatDeepSeek


# ==================== 日志配置 ====================

@dataclass
class LoggingConfig:
    """日志配置类"""
    # 基础配置
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format: str = '%Y-%m-%d %H:%M:%S'
    
    # 输出配置
    log_to_console: bool = True   # 输出到控制台
    log_to_file: bool = False     # 🔧 关键：设为False避免触发文件监控
    log_file: str = "logs/contract_review.log"
    
    # 文件轮转配置
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    # 第三方库日志级别（降低噪音）
    third_party_log_levels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.third_party_log_levels is None:
            self.third_party_log_levels = {
                'watchfiles': 'WARNING',      # 🔧 关键：禁用watchfiles的INFO日志
                'watchfiles.main': 'WARNING',
                'uvicorn.access': 'WARNING',  # 可选：降低uvicorn访问日志
                'httpx': 'WARNING',           # 可选：降低httpx日志
                'httpcore': 'WARNING',        # 可选：降低httpcore日志
            }
    
def setup_logging(config: LoggingConfig = None) -> logging.Logger:
    """
    配置日志系统
    
    参数:
        config: LoggingConfig 实例，如果为None则使用默认配置
        
    返回:
        配置好的根日志记录器
    """
    if config is None:
        config = LoggingConfig()
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper()))
    
    # 清除现有处理器（避免重复）
    root_logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        config.format,
        datefmt=config.date_format
    )
    
    # 1. 控制台处理器（推荐在开发环境使用）
    if config.log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # 2. 文件处理器（可选，生产环境使用）
    if config.log_to_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(config.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 使用轮转文件处理器
        file_handler = RotatingFileHandler(
            config.log_file,
            maxBytes=config.max_bytes,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, config.level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # 3. 配置第三方库的日志级别（🔧 关键部分）
    for logger_name, level in config.third_party_log_levels.items():
        third_party_logger = logging.getLogger(logger_name)
        third_party_logger.setLevel(getattr(logging, level.upper()))
    
    # 记录配置信息
    root_logger.info("="*60)
    root_logger.info("日志系统配置完成")
    root_logger.info(f"  日志级别: {config.level}")
    root_logger.info(f"  控制台输出: {config.log_to_console}")
    root_logger.info(f"  文件输出: {config.log_to_file}")
    if config.log_to_file:
        root_logger.info(f"  日志文件: {config.log_file}")
    root_logger.info("="*60)
    
    return root_logger


# ==================== LLM 配置 ====================

@dataclass
class LLMConfigData:
    """LLM配置数据类"""
    api_key: str
    model: str
    base_url: str
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 60
    max_retries: int = 3

@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    ttl: int = 3600  # 缓存有效期（秒）
    max_size: int = 100  # 最大缓存条目数

@dataclass
class PerformanceConfig:
    """性能优化配置"""
    enable_parallel: bool = True  # 启用并行处理
    max_workers: int = 4  # 最大并行worker数
    chunk_size: int = 2000  # 🔧 修复：添加此字段
    enable_streaming: bool = True  # 启用流式处理
    batch_processing: bool = True  # 启用批处理
    
@dataclass
class ProcessingConfig:
    """处理配置"""
    max_text_length: int = 50000  # 最大文本长度
    min_text_length: int = 50  # 最小文本长度
    enable_preprocessing: bool = True  # 启用预处理
    enable_text_compression: bool = True  # 启用文本压缩
    chunk_size: int = 2000  # 🔧 修复：添加此字段
    
class Config:
    """主配置类 - 合同审查系统"""
    
    # ==================== 日志配置 ====================
    LOGGING_CONFIG = LoggingConfig(
        level="INFO",
        log_to_console=True,      # ✅ 输出到控制台
        log_to_file=False,        # ✅ 不写文件，避免触发watchfiles
        # 如果需要写文件，设置为True并配置忽略规则
    )
    
    # ==================== LLM 配置 ====================
    LLM_CONFIG = LLMConfigData(
        api_key=os.environ.get('DEEPSEEK_API_KEY', "sk-b39d9a64aadf4d65bbb913ebfa7b02f8"),
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        max_tokens=5000,
        temperature=0.7,
        timeout=60,
        max_retries=3
    )
    
    # 缓存配置
    CACHE_CONFIG = CacheConfig(
        enabled=True,
        ttl=3600,
        max_size=100
    )
    
    # 性能配置
    PERFORMANCE_CONFIG = PerformanceConfig(
        enable_parallel=True,
        max_workers=4,
        chunk_size=2000,
        enable_streaming=True,
        batch_processing=True
    )
    
    # 处理配置
    PROCESSING_CONFIG = ProcessingConfig(
        max_text_length=50000,
        min_text_length=50,
        enable_preprocessing=True,
        enable_text_compression=True,
        chunk_size=2000
    )
    
    # ==================== Agent 端口配置 ====================
    AGENT_PORTS = {
        "coordinator": 7000,
        "legal": 7002,
        "business": 7003,
        "format": 7004,
        "document": 7005,
        "highlight": 7006,
        "integration": 7007
    }
    
    @classmethod
    def get_agent_url(cls, agent_name: str) -> str:
        """获取Agent URL"""
        port = cls.AGENT_PORTS.get(agent_name, 7000)
        return f"http://localhost:{port}"
    
    @classmethod
    def initialize(cls):
        """初始化配置（包括日志系统）"""
        # 配置日志系统
        logger = setup_logging(cls.LOGGING_CONFIG)
        return logger


# ==================== 自动初始化 ====================
# 当导入config时自动初始化日志系统
logger = Config.initialize()


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 测试配置
    print("\n" + "="*60)
    print("配置测试")
    print("="*60)
    
    # 测试日志
    logger.info("✅ 这是一条INFO日志")
    logger.warning("⚠️ 这是一条WARNING日志")
    logger.error("❌ 这是一条ERROR日志")
    
    # 测试LLM配置
    print(f"\nLLM配置:")
    print(f"  模型: {Config.LLM_CONFIG.model}")
    print(f"  最大tokens: {Config.LLM_CONFIG.max_tokens}")
    print(f"  温度: {Config.LLM_CONFIG.temperature}")
    
    # 测试Agent URL
    print(f"\nAgent URLs:")
    for agent_name in Config.AGENT_PORTS.keys():
        print(f"  {agent_name}: {Config.get_agent_url(agent_name)}")
    
    print("\n" + "="*60)