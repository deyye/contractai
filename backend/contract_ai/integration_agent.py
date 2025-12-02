import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from base_agent import BaseAgent

class IntegrationAgent(BaseAgent):
    """Agent specialized in integrating results and generating final reports for bidding document review"""
    
    def __init__(self):
        system_prompt = """你是专门进行招标文件审查结果整合和最终报告生成的智能体。你的职责包括：

1. 整合各专业智能体的分析结果
2. 生成综合性的招标文件审查报告
3. 提供统一的风险评级和建议
4. 创建执行摘要和决策支持信息
5. 协调不同角度的分析发现
6. 生成标准化的输出格式

整合分析内容：
- 文档处理结果（结构、格式、统计）
- 法律合规分析结果（合规性、风险、建议）
- 商务分析结果（财务、市场、运营）
- 格式检查结果（规范性、专业性）
- 重点标注结果（关键信息、风险点）

报告输出规格：
- 执行摘要（关键发现和建议）
- 风险评估（综合风险等级和分布）
- 详细分析（各专业角度的发现）
- 改进建议（具体可执行的建议）
- 决策支持（关键指标和参考信息）

你的整合应该：
- 确保信息的一致性和完整性
- 提供清晰的优先级排序
- 消除重复和矛盾的信息
- 突出最重要的发现和建议
- 为决策者提供可操作的洞察"""

        super().__init__(agent_name="IntegrationAgent", system_prompt=system_prompt)
        self.report_template = self.initialize_report_template()
    
    def initialize_report_template(self) -> Dict[str, Dict[str, Any]]:
        """Initialize report template structure"""
        return {
            "executive_summary": {
                "overall_assessment": "",
                "key_findings": [],
                "critical_risks": [],
                "recommendations": [],
                "decision_recommendation": ""
            },
            "risk_assessment": {
                "overall_risk_score": 0,
                "risk_distribution": {},
                "high_risk_items": [],
                "mitigation_strategies": []
            },
            "detailed_analysis": {
                "document_analysis": {},
                "legal_compliance_analysis": {},
                "business_analysis": {},
                "format_analysis": {},
                "highlight_analysis": {}
            },
            "recommendations": {
                "immediate_actions": [],
                "short_term_actions": [],
                "long_term_considerations": [],
                "bid_strategy_points": []
            },
            "appendices": {
                "key_metrics": {},
                "detailed_findings": {},
                "reference_information": {}
            }
        }
    
    def process_text_message(self, message):
        """Process integration requests for bidding documents"""
        user_text = message
        self.logger.info("Processing bidding document integration request")
        
        try:
            # Extract task and results data
            task_info = self.extract_task_info(user_text)
            
            # Parse input data (could be from workflow results)
            integration_data = self.parse_integration_data(task_info.get("content", user_text))
            
            # Perform integration analysis
            integrated_report = self.perform_integration(integration_data)
            
            # Format final response
            response_text = self.format_integrated_report(integrated_report)
            
            return {
                "agent": "IntegrationAgent",
                "status": "success",
                "analysis": integrated_report,
                "response_text": response_text,
                "timestamp": self._get_current_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Error in integration: {str(e)}")
            return {
                    "agent": "IntegrationAgent",
                    "status": "error",
                    "message": f"招标文件整合过程中发生错误：{str(e)}",
                    "response_text": "招标文件整合过程中发生错误。",
                    "timestamp": self._get_current_timestamp()
                }
    
    def extract_task_info(self, text: str) -> Dict[str, Any]:
        """Extract task information from the input text"""
        lines = text.split('\n')
        task_info = {"content": text}
        
        for line in lines:
            if line.startswith("任务："):
                task_info["task"] = line.replace("任务：", "").strip()
            elif line.startswith("上下文："):
                context_start = text.find("上下文：")
                if context_start != -1:
                    task_info["content"] = text[context_start + 4:].strip()
                break
        
        return task_info
    
    def parse_integration_data(self, content: str) -> Dict[str, Any]:
        """Parse integration data from various sources"""
        integration_data = {
            "original_content": content,
            "analysis_results": {},
            "metadata": {
                "processing_time": datetime.now().isoformat(),
                "content_length": len(content),
                "content_type": "bidding_document"
            }
        }
        
        # Try to extract structured data if present
        try:
            # Look for JSON data in the content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group(0))
                integration_data["analysis_results"] = parsed_data
        except json.JSONDecodeError:
            # If no structured data, treat as raw content
            integration_data["analysis_results"]["raw_content"] = content
        
        return integration_data
    
    def perform_integration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive integration of all analysis results"""
        integrated_report = self.report_template.copy()
        
        # Extract analysis results
        analysis_results = data.get("analysis_results", {})
        original_content = data.get("original_content", "")
        
        # Perform integration steps
        integrated_report["executive_summary"] = self.create_executive_summary(analysis_results, original_content)
        integrated_report["risk_assessment"] = self.integrate_risk_assessment(analysis_results, original_content)
        integrated_report["detailed_analysis"] = self.integrate_detailed_analysis(analysis_results, original_content)
        integrated_report["recommendations"] = self.integrate_recommendations(analysis_results, original_content)
        integrated_report["appendices"] = self.create_appendices(analysis_results, original_content)
        
        # Add metadata
        integrated_report["metadata"] = {
            "report_generated": datetime.now().isoformat(),
            "integration_agent_version": "1.0",
            "total_analysis_components": len(analysis_results),
            "content_summary": self.create_content_summary(original_content)
        }
        
        return integrated_report
    
    def create_executive_summary(self, analysis_results: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Create executive summary from all analysis results"""
        summary = {
            "overall_assessment": "",
            "key_findings": [],
            "critical_risks": [],
            "recommendations": [],
            "decision_recommendation": ""
        }
        
        # Analyze content for key information
        content_analysis = self.analyze_content_for_summary(content)
        
        # Overall assessment based on content analysis
        summary["overall_assessment"] = self.generate_overall_assessment(content_analysis)
        
        # Extract key findings
        summary["key_findings"] = self.extract_key_findings(content_analysis, analysis_results)
        
        # Identify critical risks
        summary["critical_risks"] = self.identify_critical_risks(content_analysis)
        
        # Generate top recommendations
        summary["recommendations"] = self.generate_top_recommendations(content_analysis)
        
        # Provide decision recommendation
        summary["decision_recommendation"] = self.generate_decision_recommendation(content_analysis)
        
        return summary
    
    def analyze_content_for_summary(self, content: str) -> Dict[str, Any]:
        """Analyze content to create executive summary"""
        analysis = {
            "document_type": self.identify_document_type(content),
            "parties": self.extract_parties_info(content),
            "financial_terms": self.extract_financial_summary(content),
            "key_requirements": self.extract_key_requirements(content),
            "risk_indicators": self.identify_risk_indicators(content),
            "compliance_issues": self.identify_compliance_issues(content),
            "time_factors": self.extract_time_factors(content)
        }
        
        return analysis
    
    def identify_document_type(self, content: str) -> str:
        """Identify the type of bidding document"""
        document_types = {
            '货物采购招标文件': ['货物', '采购', '设备', '物资'],
            '服务采购招标文件': ['服务', '咨询', '技术服务', '运维'],
            '工程建设招标文件': ['工程', '建设', '施工', '项目'],
            '软件开发招标文件': ['软件', '开发', '系统', '程序'],
            '框架协议招标文件': ['框架', '协议', '长期', '年度'],
            '竞争性谈判文件': ['竞争性', '谈判', '磋商', '询价']
        }
        
        for doc_type, keywords in document_types.items():
            if any(keyword in content for keyword in keywords):
                return doc_type
        
        return "通用招标文件"
    
    def extract_parties_info(self, content: str) -> Dict[str, str]:
        """Extract parties information"""
        parties = {}
        
        party_patterns = [
            r'招标人[:：]\s*([^，。；\n]+)',
            r'采购人[:：]\s*([^，。；\n]+)',
            r'招标代理机构[:：]\s*([^，。；\n]+)',
            r'投标人资格[:：]\s*([^，。；\n]+)'
        ]
        
        for pattern in party_patterns:
            match = re.search(pattern, content)
            if match:
                if '招标人' in pattern:
                    parties['招标人'] = match.group(1).strip()
                elif '采购人' in pattern:
                    parties['采购人'] = match.group(1).strip()
                elif '招标代理机构' in pattern:
                    parties['招标代理机构'] = match.group(1).strip()
                elif '投标人资格' in pattern:
                    parties['投标人资格要求'] = match.group(1).strip()
        
        return parties
    
    def extract_financial_summary(self, content: str) -> Dict[str, Any]:
        """Extract financial summary"""
        financial = {
            "amounts": [],
            "payment_terms": [],
            "budget_amount": "未明确"
        }
        
        # Extract monetary amounts
        amount_patterns = [
            r'[￥$¥]\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*[元万千万亿]'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, content)
            financial["amounts"].extend(matches)
        
        # Extract payment terms
        payment_keywords = ['支付', '付款', '结算', '预付']
        lines = content.split('\n')
        
        for line in lines:
            if any(keyword in line for keyword in payment_keywords):
                financial["payment_terms"].append(line.strip())
        
        # Identify budget amount if possible
        total_patterns = ['预算金额', '最高限价', '项目总投资', '采购预算']
        for pattern in total_patterns:
            match = re.search(rf'{pattern}.*?([\d,]+[元万千万亿])', content)
            if match:
                financial["budget_amount"] = match.group(1)
                break
        
        return financial
    
    def extract_key_requirements(self, content: str) -> List[str]:
        """Extract key requirements"""
        requirements = []
        
        requirement_keywords = ['应当', '必须', '要求', '需', '应', '不得']
        lines = content.split('\n')
        
        for line in lines:
            if any(keyword in line for keyword in requirement_keywords) and len(line.strip()) > 10:
                requirements.append(line.strip())
        
        return requirements[:5]  # Return top 5 requirements
    
    def identify_risk_indicators(self, content: str) -> List[Dict[str, str]]:
        """Identify risk indicators"""
        risks = []
        
        risk_patterns = [
            (r'保证金.*?不退', '财务风险', '保证金不退条款可能导致损失'),
            (r'资格.*?无效', '资质风险', '资格要求不明确可能导致投标无效'),
            (r'单方面.*?变更', '流程风险', '单方面变更条款存在不确定性'),
            (r'短于.*?期限', '时间风险', '过短的投标期限存在响应风险'),
            (r'不接受.*?质疑', '合规风险', '不接受质疑条款不符合招标规范')
        ]
        
        for pattern, risk_type, description in risk_patterns:
            if re.search(pattern, content):
                risks.append({
                    "type": risk_type,
                    "description": description,
                    "severity": "高" if "保证金" in pattern or "无效" in pattern else "中"
                })
        
        return risks
    
    def identify_compliance_issues(self, content: str) -> List[str]:
        """Identify compliance issues"""
        issues = []
        
        # Check for missing essential elements
        essential_elements = {
            '招标项目信息': r'项目名称|项目编号',
            '投标人资格': r'资格要求|资质',
            '投标截止时间': r'截止时间|投标期限',
            '评标标准': r'评标|评审标准',
            '质疑与投诉': r'质疑|投诉|异议'
        }
        
        for element, pattern in essential_elements.items():
            if not re.search(pattern, content):
                issues.append(f"缺少{element}条款")
        
        return issues
    
    def extract_time_factors(self, content: str) -> Dict[str, Any]:
        """Extract time-related factors"""
        time_factors = {
            "bidding_period": "未明确",
            "key_deadlines": [],
            "project_schedule": []
        }
        
        # Extract bidding period
        duration_patterns = [
            r'投标期限.*?(\d+天)',
            r'公示期.*?(\d+日)',
            r'有效期.*?(\d+天)'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, content)
            if match:
                time_factors["bidding_period"] = match.group(1)
                break
        
        # Extract deadlines
        deadline_patterns = [
            r'投标截止.*?(\d{4}年\d{1,2}月\d{1,2}日)',
            r'开标时间.*?(\d{4}年\d{1,2}月\d{1,2}日)',
            r'质疑截止.*?(\d+)个工作日'
        ]
        
        for pattern in deadline_patterns:
            matches = re.findall(pattern, content)
            time_factors["key_deadlines"].extend(matches)
        
        return time_factors
    
    def generate_overall_assessment(self, analysis: Dict[str, Any]) -> str:
        """Generate overall assessment"""
        doc_type = analysis.get("document_type", "通用招标文件")
        parties = analysis.get("parties", {})
        risks = analysis.get("risk_indicators", [])
        compliance_issues = analysis.get("compliance_issues", [])
        
        assessment = f"这是一份{doc_type}，"
        
        if len(parties) >= 2:
            assessment += "招标主体信息相对完整，"
        else:
            assessment += "招标主体信息不够完整，"
        
        if len(risks) == 0:
            assessment += "整体风险较低，"
        elif len(risks) <= 2:
            assessment += "存在一定风险，"
        else:
            assessment += "风险相对较高，"
        
        if len(compliance_issues) == 0:
            assessment += "合规性良好。"
        else:
            assessment += f"存在{len(compliance_issues)}个合规性问题。"
        
        return assessment
    
    def extract_key_findings(self, analysis: Dict[str, Any], results: Dict[str, Any]) -> List[str]:
        """Extract key findings"""
        findings = []
        
        # Document structure findings
        doc_type = analysis.get("document_type", "通用招标文件")
        findings.append(f"文件类型：{doc_type}")
        
        # Financial findings
        financial = analysis.get("financial_terms", {})
        if financial.get("budget_amount") and financial["budget_amount"] != "未明确":
            findings.append(f"项目预算金额：{financial['budget_amount']}")
        
        # Risk findings
        risks = analysis.get("risk_indicators", [])
        high_risks = [r for r in risks if r.get("severity") == "高"]
        if high_risks:
            findings.append(f"发现{len(high_risks)}个高风险项目")
        
        # Compliance findings
        compliance_issues = analysis.get("compliance_issues", [])
        if compliance_issues:
            findings.append(f"识别{len(compliance_issues)}个合规性问题")
        
        # Time findings
        time_factors = analysis.get("time_factors", {})
        if time_factors.get("bidding_period") != "未明确":
            findings.append(f"投标期限：{time_factors['bidding_period']}")
        
        return findings
    
    def identify_critical_risks(self, analysis: Dict[str, Any]) -> List[str]:
        """Identify critical risks"""
        critical_risks = []
        
        risks = analysis.get("risk_indicators", [])
        for risk in risks:
            if risk.get("severity") == "高":
                critical_risks.append(f"{risk['type']}：{risk['description']}")
        
        compliance_issues = analysis.get("compliance_issues", [])
        for issue in compliance_issues:
            critical_risks.append(f"合规风险：{issue}")
        
        return critical_risks
    
    def generate_top_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate top recommendations"""
        recommendations = []
        
        # Risk-based recommendations
        risks = analysis.get("risk_indicators", [])
        high_risk_count = len([r for r in risks if r.get("severity") == "高"])
        
        if high_risk_count > 0:
            recommendations.append("建议重点关注高风险条款，必要时咨询招标专业人士")
        
        # Compliance recommendations
        compliance_issues = analysis.get("compliance_issues", [])
        if compliance_issues:
            recommendations.append("建议完善缺失的必要条款，确保招标文件合规性")
        
        # Financial recommendations
        financial = analysis.get("financial_terms", {})
        if len(financial.get("amounts", [])) > 3:
            recommendations.append("建议财务部门详细审核各项费用和支付条件")
        
        # Time recommendations
        time_factors = analysis.get("time_factors", {})
        if len(time_factors.get("key_deadlines", [])) > 2:
            recommendations.append("建议制定详细的投标计划，确保按期完成各项响应要求")
        
        if not recommendations:
            recommendations.append("建议进行全面的合规性和商务审核，确保招标文件条款合理")
        
        return recommendations
    
    def generate_decision_recommendation(self, analysis: Dict[str, Any]) -> str:
        """Generate decision recommendation"""
        risks = analysis.get("risk_indicators", [])
        compliance_issues = analysis.get("compliance_issues", [])
        
        high_risk_count = len([r for r in risks if r.get("severity") == "高"])
        compliance_issue_count = len(compliance_issues)
        
        if high_risk_count == 0 and compliance_issue_count == 0:
            return "建议：可以考虑参与投标，但建议进行最终审核"
        elif high_risk_count <= 1 and compliance_issue_count <= 2:
            return "建议：针对高风险条款准备应对策略后参与投标"
        else:
            return "建议：需要慎重评估或与招标人澄清后再决定是否参与"
    
    def integrate_risk_assessment(self, analysis_results: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Integrate risk assessment from all sources"""
        risk_assessment = {
            "overall_risk_score": 0,
            "risk_distribution": {},
            "high_risk_items": [],
            "mitigation_strategies": []
        }
        
        # Analyze content for risks
        content_risks = self.analyze_content_risks(content)
        
        # Calculate overall risk score
        risk_assessment["overall_risk_score"] = self.calculate_overall_risk_score(content_risks)
        
        # Create risk distribution
        risk_assessment["risk_distribution"] = self.create_risk_distribution(content_risks)
        
        # Identify high-risk items
        risk_assessment["high_risk_items"] = self.identify_high_risk_items(content_risks)
        
        # Generate mitigation strategies
        risk_assessment["mitigation_strategies"] = self.generate_mitigation_strategies(content_risks)
        
        return risk_assessment
    
    def analyze_content_risks(self, content: str) -> Dict[str, Any]:
        """Analyze content for various risk categories"""
        risks = {
            "legal_compliance_risks": [],
            "financial_risks": [],
            "operational_risks": [],
            "response_risks": []
        }
        
        # Legal and compliance risks
        legal_patterns = [
            (r'不接受.*?质疑', '不接受质疑条款'),
            (r'单方面.*?废标', '单方废标权'),
            (r'与.*?规定不一致', '与法规不一致')
        ]
        
        for pattern, description in legal_patterns:
            if re.search(pattern, content):
                risks["legal_compliance_risks"].append(description)
        
        # Financial risks
        financial_patterns = [
            (r'保证金.*?不退', '保证金风险'),
            (r'预付款.*?限制', '预付款限制'),
            (r'付款.*?延迟', '付款延迟条款')
        ]
        
        for pattern, description in financial_patterns:
            if re.search(pattern, content):
                risks["financial_risks"].append(description)
        
        # Operational risks
        if not re.search(r'技术.*?标准', content):
            risks["operational_risks"].append('缺少技术标准')
        
        if not re.search(r'验收.*?标准', content):
            risks["operational_risks"].append('缺少验收标准')
        
        # Response risks
        if not re.search(r'投标.*?文件.*?要求', content):
            risks["response_risks"].append('缺少投标文件要求')
        
        return risks
    
    def calculate_overall_risk_score(self, risks: Dict[str, Any]) -> int:
        """Calculate overall risk score (1-10 scale)"""
        score = 3  # Base low-risk score
        
        # Add points for each risk category
        for category, risk_list in risks.items():
            risk_count = len(risk_list)
            if category == "legal_compliance_risks":
                score += risk_count * 2
            elif category == "financial_risks":
                score += risk_count * 1.5
            else:
                score += risk_count
        
        return min(int(score), 10)
    
    def create_risk_distribution(self, risks: Dict[str, Any]) -> Dict[str, int]:
        """Create risk distribution by category"""
        distribution = {}
        
        for category, risk_list in risks.items():
            distribution[category] = len(risk_list)
        
        return distribution
    
    def identify_high_risk_items(self, risks: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify high-risk items"""
        high_risk_items = []
        
        # Legal and compliance risks are generally high priority
        for risk in risks.get("legal_compliance_risks", []):
            high_risk_items.append({
                "category": "法律合规风险",
                "description": risk,
                "severity": "高"
            })
        
        # Significant financial risks
        for risk in risks.get("financial_risks", []):
            if "保证金" in risk:
                high_risk_items.append({
                    "category": "财务风险",
                    "description": risk,
                    "severity": "高"
                })
        
        return high_risk_items
    
    def generate_mitigation_strategies(self, risks: Dict[str, Any]) -> List[str]:
        """Generate risk mitigation strategies"""
        strategies = []
        
        if risks.get("legal_compliance_risks"):
            strategies.append("建议法务部门详细审核合规条款，确认是否符合招投标法规要求")
        
        if risks.get("financial_risks"):
            strategies.append("建议财务部门评估财务影响，制定应对保证金和付款条款的策略")
        
        if risks.get("operational_risks"):
            strategies.append("建议技术部门评估技术和验收标准的可行性，提前准备应对方案")
        
        if risks.get("response_risks"):
            strategies.append("建议投标团队仔细准备投标文件，确保满足所有响应要求")
        
        return strategies
    
    def integrate_detailed_analysis(self, analysis_results: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Integrate detailed analysis from all agents"""
        detailed_analysis = {
            "document_analysis": self.summarize_document_analysis(content),
            "legal_compliance_analysis": self.summarize_legal_compliance_analysis(content),
            "business_analysis": self.summarize_business_analysis(content),
            "format_analysis": self.summarize_format_analysis(content),
            "highlight_analysis": self.summarize_highlight_analysis(content)
        }
        
        return detailed_analysis
    
    def summarize_document_analysis(self, content: str) -> Dict[str, Any]:
        """Summarize document processing results"""
        lines = content.split('\n')
        
        return {
            "structure": {
                "total_lines": len(lines),
                "content_lines": len([line for line in lines if line.strip()]),
                "has_title": bool(re.search(r'招标|采购', content[:200])),
                "has_parties": bool(re.search(r'招标人|采购人', content)),
                "has_version_info": bool(re.search(r'版本|编号', content))
            },
            "content_type": self.identify_document_type(content),
            "key_sections": self.identify_key_sections(content)
        }
    
    def identify_key_sections(self, content: str) -> List[str]:
        """Identify key sections in the document"""
        sections = []
        
        section_patterns = [
            (r'第?[一二三四五六七八九十\d]+[条章节]', '条款编号'),
            (r'招标人|采购人', '招标主体信息'),
            (r'项目.*?概况', '项目概况'),
            (r'投标人.*?资格', '投标人资格'),
            (r'评标.*?办法', '评标办法'),
            (r'投标.*?文件.*?要求', '投标文件要求')
        ]
        
        for pattern, description in section_patterns:
            if re.search(pattern, content):
                sections.append(description)
        
        return sections
    
    def summarize_legal_compliance_analysis(self, content: str) -> Dict[str, Any]:
        """Summarize legal and compliance analysis results"""
        return {
            "compliance_status": self.assess_compliance_status(content),
            "legal_risks": self.identify_legal_risks(content),
            "required_clauses": self.check_required_clauses(content),
            "recommendations": self.generate_legal_recommendations(content)
        }
    
    def assess_compliance_status(self, content: str) -> str:
        """Assess compliance status"""
        required_elements = [
            r'招标人|采购人',  # 招标主体
            r'项目.*?概况',  # 项目概况
            r'投标人.*?资格',  # 投标人资格
            r'评标.*?标准',  # 评标标准
            r'投标.*?截止'   # 投标截止
        ]
        
        present_count = sum(1 for pattern in required_elements if re.search(pattern, content))
        compliance_ratio = present_count / len(required_elements)
        
        if compliance_ratio >= 0.8:
            return "良好"
        elif compliance_ratio >= 0.6:
            return "基本合规"
        else:
            return "需要改进"
    
    def identify_legal_risks(self, content: str) -> List[str]:
        """Identify legal risks"""
        risks = []
        
        risk_patterns = [
            (r'限制.*?竞争', '限制竞争条款'),
            (r'歧视性.*?要求', '歧视性条款'),
            (r'模糊.*?标准', '评标标准模糊'),
            (r'无理由.*?废标', '无理由废标风险')
        ]
        
        for pattern, risk_desc in risk_patterns:
            if re.search(pattern, content):
                risks.append(risk_desc)
        
        return risks
    
    def check_required_clauses(self, content: str) -> Dict[str, bool]:
        """Check for required clauses"""
        clauses = {
            "招标主体信息": bool(re.search(r'招标人|采购人', content)),
            "项目概况": bool(re.search(r'项目.*?概况|采购.*?内容', content)),
            "投标人资格": bool(re.search(r'资格.*?要求|资质', content)),
            "评标标准": bool(re.search(r'评标.*?标准|评审.*?办法', content)),
            "投标截止时间": bool(re.search(r'截止.*?时间|投标.*?期限', content)),
            "质疑与投诉": bool(re.search(r'质疑|投诉|异议', content))
        }
        
        return clauses
    
    def generate_legal_recommendations(self, content: str) -> List[str]:
        """Generate legal recommendations"""
        recommendations = []
        
        if not re.search(r'废标.*?情形', content):
            recommendations.append("建议明确废标情形条款")
        
        if not re.search(r'知识产权', content):
            recommendations.append("建议添加知识产权条款")
        
        if re.search(r'单方面.*?变更', content):
            recommendations.append("建议修改单方面变更条款")
        
        return recommendations
    
    def summarize_business_analysis(self, content: str) -> Dict[str, Any]:
        """Summarize business analysis results"""
        return {
            "financial_assessment": self.assess_financial_terms(content),
            "project_value": self.assess_project_value(content),
            "implementation_requirements": self.identify_implementation_requirements(content),
            "market_considerations": self.identify_market_considerations(content)
        }
    
    def assess_financial_terms(self, content: str) -> Dict[str, Any]:
        """Assess financial terms"""
        amounts = re.findall(r'[\d,]+[元万千万亿]', content)
        
        return {
            "amounts_found": len(amounts),
            "payment_terms": bool(re.search(r'支付|付款', content)),
            "pricing_clarity": bool(re.search(r'价格|费用.*?明确', content)),
            "financial_risk_level": "中等" if len(amounts) > 2 else "低"
        }
    
    def assess_project_value(self, content: str) -> str:
        """Assess project value"""
        value_indicators = [
            r'重点项目',
            r'长期合作',
            r'战略意义',
            r'后续项目'
        ]
        
        indicator_count = sum(1 for pattern in value_indicators if re.search(pattern, content))
        
        if indicator_count >= 3:
            return "高价值"
        elif indicator_count >= 1:
            return "中等价值"
        else:
            return "标准价值"
    
    def identify_implementation_requirements(self, content: str) -> List[str]:
        """Identify implementation requirements"""
        requirements = []
        
        if re.search(r'质量.*?标准', content):
            requirements.append("质量标准要求")
        
        if re.search(r'交付.*?时间', content):
            requirements.append("交付时间要求")
        
        if re.search(r'服务.*?水平', content):
            requirements.append("服务水平要求")
        
        if re.search(r'验收.*?流程', content):
            requirements.append("验收流程要求")
        
        return requirements
    
    def identify_market_considerations(self, content: str) -> List[str]:
        """Identify market considerations"""
        considerations = []
        
        if re.search(r'市场.*?行情', content):
            considerations.append("市场行情因素")
        
        if re.search(r'竞争.*?情况', content):
            considerations.append("竞争情况因素")
        
        if re.search(r'独家.*?供应', content):
            considerations.append("独家供应考量")
        
        return considerations
    
    def summarize_format_analysis(self, content: str) -> Dict[str, Any]:
        """Summarize format analysis results"""
        lines = content.split('\n')
        
        return {
            "structure_score": self.calculate_structure_score(content),
            "formatting_issues": self.identify_formatting_issues(content),
            "professional_appearance": self.assess_professional_appearance(content),
            "readability": self.assess_readability(content)
        }
    
    def calculate_structure_score(self, content: str) -> int:
        """Calculate structure score"""
        score = 5  # Base score
        
        if re.search(r'招标|采购', content[:100]):
            score += 2  # Has title
        
        if re.search(r'招标人.*?项目', content):
            score += 2  # Has basic info
        
        if re.search(r'第[一二三四五六七八九十\d]+条', content):
            score += 1  # Has numbered clauses
        
        if re.search(r'附件|附录', content):
            score += 1  # Has attachments
        
        return min(score, 10)
    
    def identify_formatting_issues(self, content: str) -> List[str]:
        """Identify formatting issues"""
        issues = []
        
        lines = content.split('\n')
        
        # Check for very long lines
        long_lines = [i for i, line in enumerate(lines) if len(line) > 100]
        if len(long_lines) > 5:
            issues.append("存在过长行，影响可读性")
        
        # Check for inconsistent spacing
        empty_line_ratio = sum(1 for line in lines if not line.strip()) / len(lines)
        if empty_line_ratio < 0.05:
            issues.append("段落间距过密")
        
        return issues
    
    def assess_professional_appearance(self, content: str) -> str:
        """Assess professional appearance"""
        score = 0
        
        if re.search(r'^.*?(招标|采购)', content[:100]):
            score += 2
        
        if re.search(r'招标人.*?联系方式', content):
            score += 2
        
        if re.search(r'条款.*?清晰', content):
            score += 2
        
        if score >= 5:
            return "专业"
        elif score >= 3:
            return "基本专业"
        else:
            return "需要改进"
    
    def assess_readability(self, content: str) -> str:
        """Assess readability"""
        lines = content.split('\n')
        avg_line_length = sum(len(line) for line in lines if line.strip()) / max(len([line for line in lines if line.strip()]), 1)
        
        if avg_line_length <= 60:
            return "良好"
        elif avg_line_length <= 80:
            return "一般"
        else:
            return "较差"
    
    def summarize_highlight_analysis(self, content: str) -> Dict[str, Any]:
        """Summarize highlight analysis results"""
        return {
            "key_points_count": self.count_key_points(content),
            "risk_highlights": self.count_risk_highlights(content),
            "important_clauses": self.count_important_clauses(content),
            "attention_areas": self.identify_attention_areas(content)
        }
    
    def count_key_points(self, content: str) -> int:
        """Count key points in content"""
        key_indicators = ['重要', '关键', '必须', '应当', '不得', '禁止']
        return sum(content.count(indicator) for indicator in key_indicators)
    
    def count_risk_highlights(self, content: str) -> int:
        """Count risk highlights"""
        risk_indicators = ['违约', '赔偿', '责任', '风险', '损失', '终止']
        return sum(content.count(indicator) for indicator in risk_indicators)
    
    def count_important_clauses(self, content: str) -> int:
        """Count important clauses"""
        return len(re.findall(r'第[一二三四五六七八九十\d]+条', content))
    
    def identify_attention_areas(self, content: str) -> List[str]:
        """Identify areas requiring attention"""
        areas = []
        
        if re.search(r'违约金.*?[\d,]+', content):
            areas.append("违约金条款")
        
        if re.search(r'保密.*?义务', content):
            areas.append("保密义务")
        
        if re.search(r'知识产权', content):
            areas.append("知识产权")
        
        if re.search(r'争议.*?解决', content):
            areas.append("争议解决")
        
        return areas
    
    def integrate_recommendations(self, analysis_results: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Integrate recommendations from all analyses"""
        recommendations = {
            "immediate_actions": [],
            "short_term_actions": [],
            "long_term_considerations": [],
            "negotiation_points": []
        }
        
        # Generate recommendations based on analysis
        content_analysis = self.analyze_content_for_summary(content)
        
        # Immediate actions
        critical_risks = content_analysis.get("risk_indicators", [])
        high_risks = [r for r in critical_risks if r.get("severity") == "高"]
        
        if high_risks:
            recommendations["immediate_actions"].append("立即评估高风险条款的影响")
        
        compliance_issues = content_analysis.get("compliance_issues", [])
        if compliance_issues:
            recommendations["immediate_actions"].append("补充缺失的必要合同条款")
        
        # Short-term actions
        if not re.search(r'不可抗力', content):
            recommendations["short_term_actions"].append("添加不可抗力条款")
        
        if not re.search(r'保密', content):
            recommendations["short_term_actions"].append("完善保密协议条款")
        
        # Long-term considerations
        if re.search(r'长期|多年', content):
            recommendations["long_term_considerations"].append("定期审查合同条款的适用性")
        
        recommendations["long_term_considerations"].append("建立合同履行监控机制")
        
        # Negotiation points
        if re.search(r'违约金.*?[\d,]+', content):
            recommendations["negotiation_points"].append("协商合理的违约金标准")
        
        if re.search(r'单方.*?决定', content):
            recommendations["negotiation_points"].append("协商平衡的决策权分配")
        
        return recommendations
    
    def create_appendices(self, analysis_results: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Create appendices with detailed information"""
        appendices = {
            "key_metrics": self.compile_key_metrics(content),
            "detailed_findings": self.compile_detailed_findings(content),
            "reference_information": self.compile_reference_information(content)
        }
        
        return appendices
    
    def compile_key_metrics(self, content: str) -> Dict[str, Any]:
        """Compile key metrics"""
        return {
            "document_length": len(content),
            "clause_count": len(re.findall(r'第[一二三四五六七八九十\d]+条', content)),
            "financial_items": len(re.findall(r'[\d,]+[元万千万亿]', content)),
            "risk_indicators": len(re.findall(r'违约|赔偿|责任|风险', content)),
            "compliance_score": self.calculate_compliance_score(content)
        }
    
    def calculate_compliance_score(self, content: str) -> int:
        """Calculate compliance score"""
        required_elements = [
            r'甲方|乙方',
            r'标的|内容',
            r'期限|时间',
            r'价款|费用',
            r'违约|责任',
            r'争议.*?解决'
        ]
        
        present_count = sum(1 for pattern in required_elements if re.search(pattern, content))
        return int((present_count / len(required_elements)) * 10)
    
    def compile_detailed_findings(self, content: str) -> Dict[str, Any]:
        """Compile detailed findings"""
        return {
            "contract_structure": self.analyze_contract_structure(content),
            "party_analysis": self.analyze_parties(content),
            "financial_analysis": self.analyze_financial_details(content),
            "risk_analysis": self.analyze_risk_details(content)
        }
    
    def analyze_contract_structure(self, content: str) -> Dict[str, Any]:
        """Analyze contract structure in detail"""
        lines = content.split('\n')
        
        return {
            "total_sections": len(re.findall(r'第[一二三四五六七八九十\d]+[条章节]', content)),
            "has_preamble": bool(re.search(r'鉴于|为了', content[:500])),
            "has_definitions": bool(re.search(r'定义|术语', content)),
            "has_appendices": bool(re.search(r'附件|附录', content)),
            "structure_completeness": "完整" if all([
                re.search(r'合同|协议', content[:100]),
                re.search(r'甲方|乙方', content),
                re.search(r'签字|签名', content)
            ]) else "不完整"
        }
    
    def analyze_parties(self, content: str) -> Dict[str, Any]:
        """Analyze parties in detail"""
        parties = {}
        
        party_patterns = [
            (r'甲方[:：]\s*([^，。；\n]+)', '甲方'),
            (r'乙方[:：]\s*([^，。；\n]+)', '乙方')
        ]
        
        for pattern, label in party_patterns:
            match = re.search(pattern, content)
            if match:
                parties[label] = {
                    "name": match.group(1).strip(),
                    "has_address": bool(re.search(rf'{label}.*?地址', content)),
                    "has_contact": bool(re.search(rf'{label}.*?电话|{label}.*?联系', content)),
                    "has_representative": bool(re.search(rf'{label}.*?法定代表人', content))
                }
        
        return parties
    
    def analyze_financial_details(self, content: str) -> Dict[str, Any]:
        """Analyze financial details"""
        amounts = re.findall(r'[\d,]+[元万千万亿]', content)
        
        return {
            "total_amounts_mentioned": len(amounts),
            "largest_amount": max(amounts, key=len) if amounts else None,
            "payment_methods": list(set(re.findall(r'(银行转账|现金|支票|承兑汇票)', content))),
            "payment_schedule": bool(re.search(r'分期|分批|按月|按季', content)),
            "penalty_clauses": len(re.findall(r'违约金', content))
        }
    
    def analyze_risk_details(self, content: str) -> Dict[str, Any]:
        """Analyze risk details"""
        return {
            "liability_clauses": len(re.findall(r'责任|赔偿', content)),
            "termination_clauses": len(re.findall(r'终止|解除', content)),
            "force_majeure": bool(re.search(r'不可抗力', content)),
            "confidentiality": bool(re.search(r'保密', content)),
            "intellectual_property": bool(re.search(r'知识产权', content)),
            "dispute_resolution": bool(re.search(r'争议.*?解决|仲裁|诉讼', content))
        }
    
    def compile_reference_information(self, content: str) -> Dict[str, Any]:
        """Compile reference information"""
        return {
            "applicable_laws": list(set(re.findall(r'《.*?法》|.*?法律|.*?法规', content))),
            "standards_referenced": list(set(re.findall(r'标准|规范|规程', content))),
            "external_documents": list(set(re.findall(r'附件|附录|补充协议', content))),
            "key_dates": list(set(re.findall(r'\d{4}年\d{1,2}月\d{1,2}日', content))),
            "contact_information": self.extract_contact_information(content)
        }
    
    def extract_contact_information(self, content: str) -> Dict[str, List[str]]:
        """Extract contact information"""
        contacts = {
            "phone_numbers": re.findall(r'1[3-9]\d{9}|\d{3,4}-\d{7,8}', content),
            "email_addresses": re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content),
            "addresses": []
        }
        
        # Extract addresses (simplified pattern)
        address_patterns = [
            r'地址[:：]\s*([^，。；\n]+)',
            r'住所[:：]\s*([^，。；\n]+)'
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, content)
            contacts["addresses"].extend(matches)
        
        return contacts
    
    def create_content_summary(self, content: str) -> Dict[str, Any]:
        """Create content summary for metadata"""
        return {
            "character_count": len(content),
            "word_count": len(content.split()),
            "line_count": len(content.split('\n')),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "contains_tables": bool(re.search(r'\|.*?\|', content)),
            "contains_lists": bool(re.search(r'^\s*[-*]\s', content, re.MULTILINE)),
            "language": "中文" if re.search(r'[\u4e00-\u9fff]', content) else "其他"
        }
    
    def get_llm_integration_analysis(self, integrated_report: Dict[str, Any]) -> str:
        """Get LLM analysis of integrated results"""
        # Summarize the integrated report for LLM analysis
        summary_data = {
            "overall_risk_score": integrated_report.get("risk_assessment", {}).get("overall_risk_score", 0),
            "key_findings": integrated_report.get("executive_summary", {}).get("key_findings", []),
            "critical_risks": integrated_report.get("executive_summary", {}).get("critical_risks", []),
            "compliance_status": integrated_report.get("detailed_analysis", {}).get("legal_analysis", {}).get("compliance_status", "未知")
        }
        
        analysis_prompt = f"""
        基于以下整合分析结果，请提供专业的综合评估：
        
        整合结果摘要：
        - 整体风险评分：{summary_data['overall_risk_score']}/10
        - 关键发现：{summary_data['key_findings']}
        - 重大风险：{summary_data['critical_risks']}
        - 合规状态：{summary_data['compliance_status']}
        
        请从以下角度提供综合分析：
        1. 整体合同质量评估
        2. 主要风险点及其影响
        3. 合同可执行性分析
        4. 商业价值和机会评估
        5. 决策建议和行动方案
        
        请提供专业、客观的综合判断和建议。
        """
        
        return self.call_llm(analysis_prompt)
    
    def format_integrated_report(self, integrated_report: Dict[str, Any]) -> str:
        """Format the integrated report for output"""
        output = "=" * 50 + "\n"
        output += "合同审查综合分析报告\n"
        output += "=" * 50 + "\n\n"
        
        # Report metadata
        metadata = integrated_report.get("metadata", {})
        output += f"报告生成时间：{metadata.get('report_generated', '未知')}\n"
        output += f"分析组件数量：{metadata.get('total_analysis_components', 0)}\n\n"
        
        # Executive Summary
        exec_summary = integrated_report.get("executive_summary", {})
        output += "【执行摘要】\n"
        output += "-" * 30 + "\n"
        output += f"整体评估：{exec_summary.get('overall_assessment', '待评估')}\n\n"
        
        key_findings = exec_summary.get("key_findings", [])
        if key_findings:
            output += "关键发现：\n"
            for i, finding in enumerate(key_findings, 1):
                output += f"  {i}. {finding}\n"
            output += "\n"
        
        critical_risks = exec_summary.get("critical_risks", [])
        if critical_risks:
            output += "🔴 重大风险：\n"
            for i, risk in enumerate(critical_risks, 1):
                output += f"  {i}. {risk}\n"
            output += "\n"
        
        recommendations = exec_summary.get("recommendations", [])
        if recommendations:
            output += "核心建议：\n"
            for i, rec in enumerate(recommendations, 1):
                output += f"  {i}. {rec}\n"
            output += "\n"
        
        decision_rec = exec_summary.get("decision_recommendation", "")
        if decision_rec:
            output += f"决策建议：{decision_rec}\n\n"
        
        # Risk Assessment
        risk_assessment = integrated_report.get("risk_assessment", {})
        output += "【风险评估】\n"
        output += "-" * 30 + "\n"
        output += f"整体风险评分：{risk_assessment.get('overall_risk_score', 0)}/10\n\n"
        
        risk_distribution = risk_assessment.get("risk_distribution", {})
        if risk_distribution:
            output += "风险分布：\n"
            for risk_type, count in risk_distribution.items():
                output += f"  • {risk_type}：{count}项\n"
            output += "\n"
        
        high_risk_items = risk_assessment.get("high_risk_items", [])
        if high_risk_items:
            output += "高风险项目：\n"
            for i, item in enumerate(high_risk_items, 1):
                output += f"  {i}. [{item.get('category', '未分类')}] {item.get('description', '未描述')}\n"
            output += "\n"
        
        mitigation = risk_assessment.get("mitigation_strategies", [])
        if mitigation:
            output += "风险缓解策略：\n"
            for i, strategy in enumerate(mitigation, 1):
                output += f"  {i}. {strategy}\n"
            output += "\n"
        
        # Detailed Analysis Summary
        detailed_analysis = integrated_report.get("detailed_analysis", {})
        output += "【详细分析摘要】\n"
        output += "-" * 30 + "\n"
        
        # Document Analysis
        doc_analysis = detailed_analysis.get("document_analysis", {})
        if doc_analysis:
            structure = doc_analysis.get("structure", {})
            output += f"文档结构：{structure.get('content_lines', 0)}行有效内容，"
            output += f"包含{'标题' if structure.get('has_title') else '无标题'}，"
            output += f"{'有当事人信息' if structure.get('has_parties') else '缺少当事人信息'}，"
            output += f"{'有签署区' if structure.get('has_signature') else '缺少签署区'}\n"
            output += f"合同类型：{doc_analysis.get('content_type', '未识别')}\n\n"
        
        # Legal Analysis
        legal_analysis = detailed_analysis.get("legal_analysis", {})
        if legal_analysis:
            output += f"法律合规性：{legal_analysis.get('compliance_status', '未评估')}\n"
            
            legal_risks = legal_analysis.get("legal_risks", [])
            if legal_risks:
                output += f"法律风险：{len(legal_risks)}项 - {', '.join(legal_risks[:3])}\n"
            
            required_clauses = legal_analysis.get("required_clauses", {})
            missing_clauses = [name for name, present in required_clauses.items() if not present]
            if missing_clauses:
                output += f"缺失条款：{', '.join(missing_clauses)}\n"
            output += "\n"
        
        # Business Analysis
        business_analysis = detailed_analysis.get("business_analysis", {})
        if business_analysis:
            financial = business_analysis.get("financial_assessment", {})
            output += f"财务条款：发现{financial.get('amounts_found', 0)}个金额项目，"
            output += f"风险等级{financial.get('financial_risk_level', '未知')}\n"
            output += f"商业价值：{business_analysis.get('commercial_value', '未评估')}\n\n"
        
        # Format Analysis
        format_analysis = detailed_analysis.get("format_analysis", {})
        if format_analysis:
            output += f"格式规范性：{format_analysis.get('structure_score', 0)}/10分，"
            output += f"专业外观{format_analysis.get('professional_appearance', '未评估')}，"
            output += f"可读性{format_analysis.get('readability', '未评估')}\n\n"
        
        # Highlight Analysis
        highlight_analysis = detailed_analysis.get("highlight_analysis", {})
        if highlight_analysis:
            output += f"重点标注：{highlight_analysis.get('key_points_count', 0)}个关键点，"
            output += f"{highlight_analysis.get('risk_highlights', 0)}个风险标注，"
            output += f"{highlight_analysis.get('important_clauses', 0)}个重要条款\n\n"
        
        # Recommendations
        recommendations_section = integrated_report.get("recommendations", {})
        output += "【行动建议】\n"
        output += "-" * 30 + "\n"
        
        immediate = recommendations_section.get("immediate_actions", [])
        if immediate:
            output += "🔴 立即行动：\n"
            for i, action in enumerate(immediate, 1):
                output += f"  {i}. {action}\n"
            output += "\n"
        
        short_term = recommendations_section.get("short_term_actions", [])
        if short_term:
            output += "🟡 短期行动：\n"
            for i, action in enumerate(short_term, 1):
                output += f"  {i}. {action}\n"
            output += "\n"
        
        long_term = recommendations_section.get("long_term_considerations", [])
        if long_term:
            output += "🟢 长期考虑：\n"
            for i, consideration in enumerate(long_term, 1):
                output += f"  {i}. {consideration}\n"
            output += "\n"
        
        negotiation = recommendations_section.get("negotiation_points", [])
        if negotiation:
            output += "💼 谈判要点：\n"
            for i, point in enumerate(negotiation, 1):
                output += f"  {i}. {point}\n"
            output += "\n"
        
        # Key Metrics
        appendices = integrated_report.get("appendices", {})
        key_metrics = appendices.get("key_metrics", {})
        if key_metrics:
            output += "【关键指标】\n"
            output += "-" * 30 + "\n"
            output += f"文档长度：{key_metrics.get('document_length', 0)} 字符\n"
            output += f"条款数量：{key_metrics.get('clause_count', 0)} 条\n"
            output += f"财务项目：{key_metrics.get('financial_items', 0)} 项\n"
            output += f"风险指标：{key_metrics.get('risk_indicators', 0)} 个\n"
            output += f"合规评分：{key_metrics.get('compliance_score', 0)}/10\n\n"
        
        # Get additional LLM analysis
        llm_analysis = self.get_llm_integration_analysis(integrated_report)
        if llm_analysis:
            output += "【智能分析】\n"
            output += "-" * 30 + "\n"
            output += llm_analysis + "\n\n"
        
        output += "=" * 50 + "\n"
        output += "报告结束\n"
        output += "=" * 50
        
        return output

if __name__ == "__main__":
    agent = IntegrationAgent()