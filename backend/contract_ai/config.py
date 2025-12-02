import os
from dataclasses import dataclass
from typing import Dict, Any
from langchain_deepseek import ChatDeepSeek

@dataclass
class LLMConfig:
    """LLM configuration class"""
    api_key: str
    model: str
    base_url: str
    max_tokens: int = 2000
    temperature: float = 0.7
    
class LLMConfig:
    """Main LLM configuration class for the contract review system"""
    
    # LLM configuration (using DeepSeek as example)
    LLM_CONFIG = LLMConfig(
        api_key=os.environ.get('DEEPSEEK_API_KEY', "sk-b39d9a64aadf4d65bbb913ebfa7b02f8"),
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        max_tokens=5000,
        temperature=0.7
    )
