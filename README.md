# 智能合同审查系统 (Contract AI)

基于 LangGraph 多智能体架构与 React 前端的智能化合同/招标文件审查系统。该系统通过多个专业智能体（法律、商业、文档处理）的分工协作，实现对合同文档的全维度自动化分析、风险评估与合规性检查。

## 📖 项目简介

本项目采用分布式智能体架构，将复杂的审查任务拆解为专业化子任务。系统包含前端可视化交互界面与后端多智能体处理引擎，能够自动解析 PDF 文档，识别潜在的法律风险与商业陷阱，并生成结构化的审查报告。

### 核心功能

  * **智能文档解析**：自动提取招标文件/合同中的关键要素（如项目预算、截止时间、资质要求等）。
  * **多维度风险审查**：
      * **法律合规**：识别条款漏洞、法律风险及合规性问题。
      * **商业风险**：评估付款条款、违约责任及商业合理性。
  * **智能工作流编排**：通过协调器（Coordinator）动态规划任务，支持文档预处理、并行分析与结果整合。
  * **可视化报告**：前端实时展示审查进度、风险等级及详细的修改建议。

## 🏗 系统架构

系统由以下核心智能体组成：

| 智能体 | 职责 |
| :--- | :--- |
| **Coordinator (协调器)** | 负责任务拆解、流程调度及异常处理，优化并行执行效率。 |
| **DocumentAgent (文档)** | 负责 PDF 解析、文本清洗、分块及关键字段的结构化提取。 |
| **LegalAgent (法律)** | 专注法律层面的合规性审查与风险识别。 |
| **BusinessAgent (商业)** | 专注商业条款、价格支付及履约风险的评估。 |
| **IntegrationAgent (整合)** | 汇总各方分析结果，生成最终面向用户的结构化报告。 |

## 🛠 技术栈

### Backend (后端)

  * **语言**: Python 3.11+
  * **框架**: FastAPI (API 服务)
  * **AI 编排**: LangChain, LangGraph (多智能体协作)
  * **模型支持**: DeepSeek (默认)
  * **PDF 处理**: pdfplumber

### Frontend (前端)

  * **框架**: React 19 + TypeScript
  * **构建工具**: Vite
  * **UI 组件库**: Ant Design (v6.0)
  * **PDF 预览**: react-pdf

## 🚀 快速开始

### 1\. 环境准备

确保本地已安装：

  * Python 3.8+
  * Node.js 18+ (推荐使用 nvm)

### 2\. 获取代码

```bash
git clone <repository_url>
cd contractai-main
```

### 3\. 配置环境变量

修改后端配置文件 `backend/contract_ai/config.py` 或创建环境变量，配置 LLM API 密钥：

```python
# backend/contract_ai/config.py 或 .env
DEEPSEEK_API_KEY="your-api-key-here"
```

### 4\. 安装依赖

**后端依赖：**

```bash
cd backend
pip install -r requirements.txt  # (需确保requirements.txt存在)
```

**前端依赖：**
系统启动脚本会自动检查并安装前端依赖，您也可以手动安装：

```bash
cd frontend
npm install
```

### 5\. 一键启动

项目提供了 Python 启动脚本，可同时启动后端 (Port 8001) 和前端 (Port 5173) 服务：

**Windows / Linux / Mac:**

```bash
python start_dev.py
```

或者使用 Shell 脚本 (Linux/Mac)：

```bash
./start.sh
```

启动成功后，访问浏览器：`http://localhost:5173`

## 📂 项目结构

```text
contractai-main/
├── backend/                  # 后端工程
│   ├── app/
│   │   ├── api/              # API 路由定义
│   │   └── services/         # 基础服务 (如 PDF 处理)
│   ├── contract_ai/          # 智能体核心逻辑
│   │   ├── base_agent.py     # 智能体基类 (含缓存/重试机制)
│   │   ├── coordinator.py    # 协调器与工作流图
│   │   ├── *_agent.py        # 各类专业智能体实现
│   │   └── config.py         # 系统配置
│   └── uploads/              # 上传文件临时存储
├── frontend/                 # 前端工程
│   ├── src/
│   │   ├── components/       # UI 组件 (RiskPanel, ProcessingStatus)
│   │   ├── api/              # API 接口封装
│   │   └── App.tsx           # 主应用入口
│   └── vite.config.ts        # Vite 配置
├── start_dev.py              # Python 跨平台启动脚本
└── start.sh                  # Shell 启动脚本
```

## ⚠️ 注意事项

  * **API Key**: 请确保在运行前配置有效的 `DEEPSEEK_API_KEY`，否则智能体无法调用大模型进行分析。
  * **PDF 解析**: 目前主要支持文本型 PDF，对于纯图片扫描件的解析能力取决于底层 OCR 库的支持情况。
  * **日志**: 系统运行日志（包括智能体思考过程和性能监控）默认输出到控制台，可通过修改配置开启文件日志。

## 📄 License

MIT