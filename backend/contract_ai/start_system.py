#!/usr/bin/env python3
"""
合同审查多智能体系统启动脚本 (基于LangGraph+LangChain框架)
Contract Review Multi-Agent System (LangGraph+LangChain Framework)
"""

import os
import sys
import time
import signal
import logging
from typing import List, Dict, Any, Optional, Tuple, Annotated
from langgraph.graph import Graph, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import Tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.pydantic_v1 import BaseModel, Field
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LangGraphContractSystem")

class AgentManager:
    """Agent manager for starting and monitoring all agents"""
    
    def __init__(self):
        self.agents = [
            {"name": "coordinator", "file": "coordinator.py", "port": 7000, "process": None},
            {"name": "legal", "file": "legal_agent.py", "port": 7002, "process": None},
            {"name": "business", "file": "business_agent.py", "port": 7003, "process": None},
            {"name": "format", "file": "format_agent.py", "port": 7004, "process": None},
            {"name": "document", "file": "document_agent.py", "port": 7005, "process": None},
            {"name": "highlight", "file": "highlight_agent.py", "port": 7006, "process": None},
            {"name": "integration", "file": "integration_agent.py", "port": 7007, "process": None}
        ]
        self.running = False
        
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        try:
            import python_a2a
            import requests
            logger.info("✓ All dependencies are available")
            return True
        except ImportError as e:
            logger.error(f"✗ Missing dependency: {e}")
            logger.error("Please install dependencies: pip install -r requirements.txt")
            return False
    
    def check_files(self) -> bool:
        """Check if all agent files exist"""
        missing_files = []
        
        for agent in self.agents:
            if not os.path.exists(agent["file"]):
                missing_files.append(agent["file"])
        
        if missing_files:
            logger.error(f"✗ Missing agent files: {', '.join(missing_files)}")
            return False
        
        logger.info("✓ All agent files are present")
        return True
    
    def start_agent(self, agent: Dict[str, Any]) -> bool:
        """Start a single agent"""
        try:
            logger.info(f"Starting {agent['name']} agent on port {agent['port']}...")
            url = Config.get_agent_url(agent["name"])
            # Start the agent process
            process = subprocess.Popen(
                [sys.executable, agent["file"], "--url", url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            agent["process"] = process
            
            # Give the agent a moment to start
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                logger.info(f"✓ {agent['name']} agent started successfully")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"✗ {agent['name']} agent failed to start")
                logger.error(f"Error: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Failed to start {agent['name']} agent: {str(e)}")
            return False
    
    def stop_agent(self, agent: Dict[str, Any]):
        """Stop a single agent"""
        if agent["process"] and agent["process"].poll() is None:
            logger.info(f"Stopping {agent['name']} agent...")
            agent["process"].terminate()
            
            # Wait for graceful shutdown
            try:
                agent["process"].wait(timeout=5)
                logger.info(f"✓ {agent['name']} agent stopped")
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {agent['name']} agent...")
                agent["process"].kill()
                agent["process"].wait()
            
            agent["process"] = None
    
    def start_all_agents(self) -> bool:
        """Start all agents in the correct order"""
        logger.info("Starting contract review multi-agent system...")
        
        # Start specialized agents first (they don't depend on each other)
        specialized_agents = [a for a in self.agents if a["name"] != "coordinator"]
        
        for agent in specialized_agents:
            if not self.start_agent(agent):
                logger.error("Failed to start specialized agents")
                self.stop_all_agents()
                return False
        
        # Give specialized agents time to fully initialize
        logger.info("Waiting for specialized agents to initialize...")
        time.sleep(3)
        
        # Start coordinator last (it depends on the specialized agents)
        coordinator = next(a for a in self.agents if a["name"] == "coordinator")
        if not self.start_agent(coordinator):
            logger.error("Failed to start coordinator")
            self.stop_all_agents()
            return False
        
        self.running = True
        logger.info("🎉 All agents started successfully!")
        return True
    
    def stop_all_agents(self):
        """Stop all agents"""
        logger.info("Stopping all agents...")
        
        for agent in self.agents:
            self.stop_agent(agent)
        
        self.running = False
        logger.info("All agents stopped")
    
    def monitor_agents(self):
        """Monitor agent health"""
        while self.running:
            time.sleep(10)  # Check every 10 seconds
            
            for agent in self.agents:
                if agent["process"] and agent["process"].poll() is not None:
                    logger.warning(f"Agent {agent['name']} has stopped unexpectedly")
                    # Could implement restart logic here
        
        logger.info("Agent monitoring stopped")
    
    def show_status(self):
        """Show status of all agents"""
        print("\n" + "="*60)
        print("合同审查多智能体系统状态 / Contract Review System Status")
        print("="*60)
        
        for agent in self.agents:
            status = "🟢 运行中" if agent["process"] and agent["process"].poll() is None else "🔴 已停止"
            print(f"{agent['name'].ljust(12)} - 端口 {agent['port']} - {status}")
        
        print("="*60)
        print("系统访问地址 / System Access URLs:")
        print(f"主协调器 Coordinator: http://localhost:7000/a2a")
        print(f"各专业智能体端口 Agent Ports: 7002-7007")
        print("="*60)
    
    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info("Received shutdown signal, stopping all agents...")
        self.stop_all_agents()
        sys.exit(0)

def print_banner():
    """Print system banner"""
    banner = """
╔════════════════════════════════════════════════════════════════╗
║                    合同审查多智能体系统                        ║
║              Contract Review Multi-Agent System                ║
║                                                                ║
║  基于 A2A 协议的专业合同分析和审查系统                       ║
║  Professional contract analysis and review system             ║
║  built on A2A (Agent-to-Agent) protocol                       ║
╚════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def print_usage():
    """Print usage instructions"""
    usage = """
使用方法 / Usage:
  python start_system.py [start|stop|status|help]

命令说明 / Commands:
  start   - 启动所有智能体 / Start all agents
  stop    - 停止所有智能体 / Stop all agents  
  status  - 显示系统状态 / Show system status
  help    - 显示此帮助信息 / Show this help


专业智能体 / Specialized Agents:
  • 文档处理 Document Processing
  • 法律分析 Legal Analysis
  • 商业分析 Business Analysis
  • 格式检查 Format Check
  • 重点标注 Highlighting
  • 结果整合 Integration
"""
    print(usage)

def main():
    """Main function"""
    print_banner()
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        command = "help"
    else:
        command = sys.argv[1].lower()
    
    manager = AgentManager()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    if command == "start":
        # Check dependencies and files
        if not manager.check_dependencies() or not manager.check_files():
            sys.exit(1)
        
        # Start the system
        if manager.start_all_agents():
            manager.show_status()
            print("\n系统已启动 / System started successfully!")
            print("按 Ctrl+C 停止系统 / Press Ctrl+C to stop the system")
            
            # Start monitoring in a separate thread
            monitor_thread = threading.Thread(target=manager.monitor_agents)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            try:
                # Keep main thread alive
                while manager.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                manager.stop_all_agents()
        else:
            logger.error("Failed to start the system")
            sys.exit(1)
    
    elif command == "stop":
        logger.info("Stopping system...")
        manager.stop_all_agents()
    
    elif command == "status":
        manager.show_status()
    
    elif command == "help":
        print_usage()
    
    else:
        print(f"未知命令: {command}")
        print("Unknown command:", command)
        print_usage()
        sys.exit(1)

if __name__ == "__main__":
    main()