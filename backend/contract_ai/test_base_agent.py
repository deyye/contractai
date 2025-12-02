import unittest
from unittest.mock import patch, MagicMock
from base_agent import BaseAgent
from langchain_core.messages import HumanMessage, SystemMessage

class TestBaseAgent(unittest.TestCase):
    """BaseAgent类的单元测试用例"""
    
    def setUp(self):
        """测试前的初始化工作"""
        self.agent_name = "test_agent"
        self.system_prompt = "Test system prompt"
        self.agent = BaseAgent(self.agent_name, self.system_prompt)
        
        # 替换实际LLM为mock对象
        self.mock_llm = MagicMock()
        self.agent.llm = self.mock_llm

    def test_initialization(self):
        """测试代理初始化是否正确"""
        self.assertEqual(self.agent.agent_name, self.agent_name)
        self.assertEqual(self.agent.system_prompt, self.system_prompt)
        self.assertIsNotNone(self.agent.logger)
        self.assertIsNotNone(self.agent.llm)

    @patch('base_agent.logging')
    def test_setup_logging(self, mock_logging):
        """测试日志配置是否正确设置"""
        self.agent.setup_logging()
        mock_logging.basicConfig.assert_called_once()
        # 检查日志格式是否包含代理名称
        log_format = mock_logging.basicConfig.call_args[1]['format']
        self.assertIn(self.agent_name, log_format)

    def test_invoke_method(self):
        """测试invoke方法是否正确处理输入"""
        test_input = {"text": "Hello, world!"}
        
        # 模拟process_text_message返回值
        expected_response = "Test response"
        with patch.object(self.agent, 'process_text_message', return_value=expected_response):
            result = self.agent.invoke(test_input)
            self.assertEqual(result, expected_response)
            self.agent.process_text_message.assert_called_once_with(test_input["text"])

    def test_call_llm_without_history(self):
        """测试无对话历史时的LLM调用"""
        user_message = "Test message"
        mock_response = MagicMock()
        mock_response.content = "Mock response"
        self.mock_llm.invoke.return_value = mock_response
        
        result = self.agent.call_llm(user_message)
        
        # 验证LLM调用参数
        self.mock_llm.invoke.assert_called_once()
        messages = self.mock_llm.invoke.call_args[0][0]
        
        # 检查系统消息
        self.assertEqual(len(messages), 2)
        self.assertIsInstance(messages[0], SystemMessage)
        self.assertEqual(messages[0].content, self.system_prompt)
        
        # 检查用户消息
        self.assertIsInstance(messages[1], HumanMessage)
        self.assertEqual(messages[1].content, user_message)
        
        self.assertEqual(result, mock_response.content)

    def test_call_llm_with_history(self):
        """测试有对话历史时的LLM调用"""
        user_message = "New message"
        conversation_history = [
            {"role": "user", "content": "Previous user message"},
            {"role": "assistant", "content": "Previous assistant response"}
        ]
        
        mock_response = MagicMock()
        mock_response.content = "Mock response with history"
        self.mock_llm.invoke.return_value = mock_response
        
        result = self.agent.call_llm(user_message, conversation_history)
        
        # 验证消息数量：系统提示 + 2条历史 + 1条新消息
        self.assertEqual(len(self.mock_llm.invoke.call_args[0][0]), 4)
        self.assertEqual(result, mock_response.content)

    def test_call_llm_exception_handling(self):
        """测试LLM调用异常处理"""
        error_message = "API Connection failed"
        self.mock_llm.invoke.side_effect = Exception(error_message)
        
        with patch.object(self.agent.logger, 'error') as mock_logger:
            result = self.agent.call_llm("Test message")
            
            # 验证错误日志被调用
            mock_logger.assert_called_once()
            # 验证返回错误信息
            self.assertIn(error_message, result)

    def test_process_text_message(self):
        """测试消息处理流程"""
        test_text = "Test input text"
        expected_response = "Processed response"
        
        with patch.object(self.agent, 'call_llm', return_value=expected_response):
            with patch.object(self.agent.logger, 'info') as mock_info:
                result = self.agent.process_text_message(test_text)
                
                self.assertEqual(result, expected_response)
                self.agent.call_llm.assert_called_once_with(test_text)
                mock_info.assert_called_once()

    def test_process_text_message_exception(self):
        """测试消息处理异常情况"""
        error_msg = "Processing failed"
        
        with patch.object(self.agent, 'call_llm', side_effect=Exception(error_msg)):
            with patch.object(self.agent.logger, 'error') as mock_error:
                result = self.agent.process_text_message("Test text")
                
                mock_error.assert_called_once()
                self.assertIn(error_msg, result)

if __name__ == '__main__':
    unittest.main()