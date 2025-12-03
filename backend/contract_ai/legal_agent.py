import json
import re
from typing import Dict, List, Any, Optional
from base_agent import BaseAgent

class LegalAgent(BaseAgent):
    """Agent specialized in tender document analysis and compliance checking"""
    
    def __init__(self):
        system_prompt = """你是专门进行招标文件分析的智能体。你的职责包括：

1. 招标文件合规性分析
2. 识别潜在的招标法律风险
3. 检查必要的招标条款是否完整
4. 分析投标方资格要求和评审标准
5. 检查招标流程和时间安排的合法性
6. 识别可能存在的招标漏洞

重点关注领域：
- 招标程序合法性
- 资格审查标准合理性
- 评审标准明确性
- 投标人权利义务平衡性
- 异议与投诉机制
- 适用法律和争议解决条款
- 强制性招标规定的遵守

你的分析应该：
- 准确识别招标风险
- 提供具体的改进建议
- 评估风险等级
- 引用相关法律法规（如果适用）
- 为其他智能体提供招标法律背景信息"""
        
        super().__init__(agent_name="TenderDocumentAgent", system_prompt=system_prompt)
        self.tender_risk_categories = self.initialize_risk_categories()
    
    def initialize_risk_categories(self) -> Dict[str, List[str]]:
        """Initialize tender document risk categories and keywords"""
        return {
            "程序合法性风险": [
                "招标方式", "公开招标", "邀请招标", "竞争性谈判", "程序违法", "流程合规"
            ],
            "资格要求风险": [
                "投标人资格", "资质要求", "门槛", "注册资金", "业绩要求", "准入条件"
            ],
            "评审标准风险": [
                "评分标准", "评审办法", "打分细则", "权重分配", "中标条件", "评审委员会"
            ],
            "时间安排风险": [
                "公告期限", "投标截止", "澄清时间", "质疑期限", "公示期", "开标时间"
            ],
            "合同条款风险": [
                "付款方式", "履行期限", "质量标准", "验收方式", "违约责任", "合同主要条款"
            ],
            "异议投诉风险": [
                "质疑", "投诉", "异议处理", "救济途径", "行政复议", "诉讼"
            ]
        }
    
    def process_text_message(self, message, context=None):
        """Process tender document analysis requests"""
        user_text = message
        self.logger.info("Processing tender document analysis request")
        
        try:
            # Extract task and content
            task_info = self.extract_task_info(user_text)
            document_content = task_info.get("content", user_text)
            
            # Perform tender document analysis
            tender_analysis = self.perform_tender_analysis(document_content)
            
            # Format response
            response_text = self.format_tender_analysis(tender_analysis)
            
            return {
                "agent": "TenderDocumentAgent",
                "status": "success",
                "analysis": tender_analysis,
                "response_text": response_text,
                "timestamp": self._get_current_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"招标文件分析出错: {str(e)}")
            return {
                "agent": "TenderDocumentAgent",
                "status": "error",
                "message": f"招标文件分析过程中发生错误：{str(e)}",
                "response_text": "招标文件分析过程中发生错误。",
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
    
    def perform_tender_analysis(self, document_text: str) -> Dict[str, Any]:
        """Perform comprehensive tender document analysis"""
        analysis = {
            "risk_assessment": self.assess_tender_risks(document_text),
            "compliance_check": self.check_compliance(document_text),
            "clause_analysis": self.analyze_key_clauses(document_text),
            "procedure_check": self.check_tender_procedure(document_text),
            "evaluation_analysis": self.analyze_evaluation_criteria(document_text),
            "qualification_analysis": self.analyze_qualification_requirements(document_text),
            "recommendations": self.generate_tender_recommendations(document_text),
            "detailed_analysis": self.get_llm_tender_analysis(document_text)
        }
        
        return analysis
    
    def assess_tender_risks(self, text: str) -> Dict[str, Any]:
        """Assess legal risks in the tender document"""
        risks = {
            "high_risk": [],
            "medium_risk": [],
            "low_risk": [],
            "risk_score": 0
        }
        
        total_risk_score = 0
        
        for risk_category, keywords in self.tender_risk_categories.items():
            category_risk = self.evaluate_category_risk(text, risk_category, keywords)
            
            if category_risk["score"] >= 8:
                risks["high_risk"].append(category_risk)
                total_risk_score += category_risk["score"]
            elif category_risk["score"] >= 5:
                risks["medium_risk"].append(category_risk)
                total_risk_score += category_risk["score"]
            elif category_risk["score"] > 0:
                risks["low_risk"].append(category_risk)
                total_risk_score += category_risk["score"]
        
        risks["risk_score"] = min(total_risk_score // len(self.tender_risk_categories), 10)
        
        return risks
    
    def evaluate_category_risk(self, text: str, category: str, keywords: List[str]) -> Dict[str, Any]:
        """Evaluate risk for a specific category"""
        risk_info = {
            "category": category,
            "score": 0,
            "issues": [],
            "keywords_found": []
        }
        
        text_lower = text.lower()
        
        # Check for presence of keywords
        for keyword in keywords:
            if keyword in text:
                risk_info["keywords_found"].append(keyword)
        
        # Specific risk evaluation logic for each category
        if category == "程序合法性风险":
            risk_info["score"] = self.evaluate_procedure_risk(text)
            risk_info["issues"] = self.find_procedure_issues(text)
        
        elif category == "资格要求风险":
            risk_info["score"] = self.evaluate_qualification_risk(text)
            risk_info["issues"] = self.find_qualification_issues(text)
        
        elif category == "评审标准风险":
            risk_info["score"] = self.evaluate_evaluation_risk(text)
            risk_info["issues"] = self.find_evaluation_issues(text)
        
        else:
            # General risk scoring based on keyword presence
            risk_info["score"] = min(len(risk_info["keywords_found"]) * 2, 10)
        
        return risk_info
    
    def evaluate_procedure_risk(self, text: str) -> int:
        """Evaluate tender procedure risks"""
        risk_score = 0
        
        # Check for proper tender method
        if not re.search(r'公开招标|邀请招标|竞争性谈判|询价', text):
            risk_score += 4  # Missing tender method
        
        # Check for公告期限
        if not re.search(r'公告.*?(\d+|几)日', text):
            risk_score += 2  # Missing announcement period
        
        # Check for 投标截止时间
        if not re.search(r'投标截止|递交截止', text):
            risk_score += 3  # Missing bid deadline
        
        return min(risk_score, 10)
    
    def find_procedure_issues(self, text: str) -> List[str]:
        """Find specific procedure issues"""
        issues = []
        
        # Check tender method
        if not re.search(r'公开招标|邀请招标', text) and re.search(r'国家投资|政府项目', text):
            issues.append("政府投资项目未明确公开招标或邀请招标方式")
        
        # Check for 澄清机制
        if not re.search(r'澄清|答疑|补遗', text):
            issues.append("缺少招标文件澄清与答疑机制")
        
        # Check for 开标程序
        if not re.search(r'开标|唱标|评标', text):
            issues.append("缺少开评标程序说明")
        
        return issues
    
    def evaluate_qualification_risk(self, text: str) -> int:
        """Evaluate qualification requirement risks"""
        risk_score = 0
        
        # Check for excessive qualification requirements
        if re.search(r'本地.*?注册|指定.*?品牌|特定.*?业绩', text):
            risk_score += 5  # Potential discriminatory clauses
        
        # Check for unclear qualification criteria
        if re.search(r'优秀|良好|适当', text) and not re.search(r'具体标准|量化指标', text):
            risk_score += 3  # Vague criteria
        
        # Check for missing qualification requirements
        if not re.search(r'资格|资质|要求', text):
            risk_score += 4  # No qualification requirements
        
        return min(risk_score, 10)
    
    def find_qualification_issues(self, text: str) -> List[str]:
        """Find specific qualification issues"""
        issues = []
        
        # Check for discriminatory clauses
        if re.search(r'仅限|必须.*?本地', text):
            issues.append("存在潜在的歧视性资格要求")
        
        # Check for clear criteria
        if not re.search(r'资格.*?标准|资质.*?条件', text):
            issues.append("资格审查标准不明确")
        
        # Check for 联合体投标规定
        if not re.search(r'联合体|联合投标', text):
            issues.append("未明确是否接受联合体投标及相关要求")
        
        return issues
    
    def evaluate_evaluation_risk(self, text: str) -> int:
        """Evaluate evaluation criteria risks"""
        risk_score = 0
        
        # Check for clear evaluation criteria
        if not re.search(r'评分标准|打分细则|权重', text):
            risk_score += 5  # No clear evaluation criteria
        
        # Check for subjective criteria
        if re.search(r'专家评审意见|评委酌情', text) and not re.search(r'量化.*?标准', text):
            risk_score += 3  # Overly subjective criteria
        
        return min(risk_score, 10)
    
    def find_evaluation_issues(self, text: str) -> List[str]:
        """Find specific evaluation issues"""
        issues = []
        
        if not re.search(r'评审委员会|评标专家', text):
            issues.append("未明确评审委员会组成和专家要求")
        
        if not re.search(r'废标.*?情形|无效投标', text):
            issues.append("未明确废标情形和无效投标条件")
        
        if not re.search(r'中标.*?公示|结果.*?公告', text):
            issues.append("未明确中标结果公示要求")
        
        return issues
    
    def check_compliance(self, text: str) -> Dict[str, Any]:
        """Check compliance with tender legal requirements"""
        compliance = {
            "required_clauses": self.check_required_clauses(text),
            "prohibited_terms": self.check_prohibited_terms(text),
            "format_compliance": self.check_format_compliance(text),
            "compliance_score": 0
        }
        
        # Calculate compliance score
        total_checks = len(compliance["required_clauses"]) + len(compliance["prohibited_terms"])
        passed_checks = sum(1 for clause in compliance["required_clauses"] if clause["present"]) + \
                       sum(1 for term in compliance["prohibited_terms"] if not term["found"])
        
        compliance["compliance_score"] = int((passed_checks / total_checks * 10)) if total_checks > 0 else 10
        
        return compliance
    
    def check_required_clauses(self, text: str) -> List[Dict[str, Any]]:
        """Check for required tender clauses"""
        required_clauses = [
            {"name": "项目概况", "pattern": r"项目名称|建设内容|采购需求", "present": False},
            {"name": "投标人资格", "pattern": r"资格要求|资质条件|准入标准", "present": False},
            {"name": "招标文件获取", "pattern": r"获取方式|购买流程|下载地址", "present": False},
            {"name": "投标文件要求", "pattern": r"投标文件|编制要求|递交方式", "present": False},
            {"name": "评审标准", "pattern": r"评分标准|评审办法|打分细则", "present": False},
            {"name": "时间安排", "pattern": r"时间表|截止日期|开标时间", "present": False},
            {"name": "合同主要条款", "pattern": r"合同条款|付款方式|履行要求", "present": False},
            {"name": "异议与投诉", "pattern": r"质疑|投诉|异议处理", "present": False}
        ]
        
        for clause in required_clauses:
            if re.search(clause["pattern"], text):
                clause["present"] = True
        
        return required_clauses
    
    def check_prohibited_terms(self, text: str) -> List[Dict[str, Any]]:
        """Check for prohibited or risky terms in tender documents"""
        prohibited_terms = [
            {"name": "歧视性条款", "pattern": r"本地.*?优先|指定.*?品牌|限制.*?潜在投标人", "found": False},
            {"name": "倾向性条款", "pattern": r"唯一.*?供应商|特定.*?技术参数|定制化.*?要求", "found": False},
            {"name": "模糊条款", "pattern": r"视情况而定|另行通知|招标人保留.*?权利", "found": False},
            {"name": "违法条款", "pattern": r"规避.*?招标|违反.*?招标投标法", "found": False}
        ]
        
        for term in prohibited_terms:
            if re.search(term["pattern"], text):
                term["found"] = True
        
        return prohibited_terms
    
    def check_format_compliance(self, text: str) -> Dict[str, bool]:
        """Check format compliance requirements for tender documents"""
        return {
            "has_title": bool(re.search(r'^.{1,50}(招标文件|招标公告|采购文件)', text, re.MULTILINE)),
            "has_project_info": bool(re.search(r'项目概况|采购内容', text)),
            "has_timeline": bool(re.search(r'时间安排|日程表', text)),
            "has_contact_info": bool(re.search(r'联系人|联系电话|邮箱', text))
        }
    
    def analyze_key_clauses(self, text: str) -> Dict[str, Any]:
        """Analyze key tender document clauses"""
        key_clauses = {
            "tender_scope": self.extract_tender_scope(text),
            "bid_submission": self.extract_bid_submission_clauses(text),
            "evaluation_process": self.extract_evaluation_clauses(text),
            "contract_terms": self.extract_contract_terms(text),
            "objection_handling": self.extract_objection_clauses(text)
        }
        
        return key_clauses
    
    def extract_tender_scope(self, text: str) -> List[str]:
        """Extract tender scope clauses"""
        scope_clauses = []
        lines = text.split('\n')
        
        scope_keywords = ['项目概况', '采购内容', '招标范围', '工作内容', '服务要求']
        
        for line in lines:
            if any(keyword in line for keyword in scope_keywords):
                scope_clauses.append(line.strip())
        
        return scope_clauses
    
    def extract_bid_submission_clauses(self, text: str) -> List[str]:
        """Extract bid submission clauses"""
        submission_clauses = []
        lines = text.split('\n')
        
        submission_keywords = ['投标文件', '递交方式', '截止时间', '密封要求', '份数要求']
        
        for line in lines:
            if any(keyword in line for keyword in submission_keywords):
                submission_clauses.append(line.strip())
        
        return submission_clauses
    
    def extract_evaluation_clauses(self, text: str) -> List[str]:
        """Extract evaluation process clauses"""
        evaluation_clauses = []
        lines = text.split('\n')
        
        evaluation_keywords = ['评审标准', '打分细则', '权重', '评标委员会', '中标条件']
        
        for line in lines:
            if any(keyword in line for keyword in evaluation_keywords):
                evaluation_clauses.append(line.strip())
        
        return evaluation_clauses
    
    def extract_contract_terms(self, text: str) -> List[str]:
        """Extract contract terms clauses"""
        contract_clauses = []
        lines = text.split('\n')
        
        contract_keywords = ['合同条款', '付款方式', '履行期限', '质量标准', '验收方式']
        
        for line in lines:
            if any(keyword in line for keyword in contract_keywords):
                contract_clauses.append(line.strip())
        
        return contract_clauses
    
    def extract_objection_clauses(self, text: str) -> List[str]:
        """Extract objection and complaint clauses"""
        objection_clauses = []
        lines = text.split('\n')
        
        objection_keywords = ['质疑', '投诉', '异议', '申诉', '救济途径']
        
        for line in lines:
            if any(keyword in line for keyword in objection_keywords):
                objection_clauses.append(line.strip())
        
        return objection_clauses
    
    def check_tender_procedure(self, text: str) -> Dict[str, Any]:
        """Check overall tender procedure compliance"""
        procedure = {
            "tender_method": self.identify_tender_method(text),
            "timeline_check": self.check_tender_timeline(text),
            "publicity_check": self.check_publicity_requirements(text),
            "procedure_score": 0
        }
        
        # Calculate procedure score
        scores = []
        if procedure["tender_method"] != "未明确":
            scores.append(3)
        
        if procedure["timeline_check"]["complete"]:
            scores.append(3)
        elif procedure["timeline_check"]["partially_complete"]:
            scores.append(1)
            
        if procedure["publicity_check"]["complete"]:
            scores.append(4)
        elif procedure["publicity_check"]["partially_complete"]:
            scores.append(2)
        
        procedure["procedure_score"] = sum(scores) if scores else 0
        
        return procedure
    
    def identify_tender_method(self, text: str) -> str:
        """Identify tender method"""
        if re.search(r'公开招标', text):
            return "公开招标"
        elif re.search(r'邀请招标', text):
            return "邀请招标"
        elif re.search(r'竞争性谈判', text):
            return "竞争性谈判"
        elif re.search(r'询价', text):
            return "询价采购"
        else:
            return "未明确"
    
    def check_tender_timeline(self, text: str) -> Dict[str, Any]:
        """Check if tender timeline is complete"""
        timeline = {
            "has_announcement_date": bool(re.search(r'公告.*?日期', text)),
            "has_bid_deadline": bool(re.search(r'投标截止.*?时间', text)),
            "has_opening_date": bool(re.search(r'开标.*?时间', text)),
            "has_evaluation_period": bool(re.search(r'评标.*?期限', text)),
            "has_publication_period": bool(re.search(r'公示.*?期限', text)),
            "complete": False,
            "partially_complete": False
        }
        
        timeline_count = sum(timeline[k] for k in timeline if k not in ["complete", "partially_complete"])
        
        timeline["complete"] = timeline_count >= 4
        timeline["partially_complete"] = timeline_count >= 2 and timeline_count < 4
        
        return timeline
    
    def check_publicity_requirements(self, text: str) -> Dict[str, Any]:
        """Check if publicity requirements are met"""
        publicity = {
            "publication_media": bool(re.search(r'发布.*?媒介|公告.*?网站', text)),
            "publicity_period": bool(re.search(r'公示.*?(\d+|几)日', text)),
            "result_publication": bool(re.search(r'中标.*?公告', text)),
            "complete": False,
            "partially_complete": False
        }
        
        publicity_count = sum(publicity[k] for k in publicity if k not in ["complete", "partially_complete"])
        
        publicity["complete"] = publicity_count >= 2
        publicity["partially_complete"] = publicity_count == 1
        
        return publicity
    
    def analyze_evaluation_criteria(self, text: str) -> Dict[str, Any]:
        """Analyze evaluation criteria and methods"""
        evaluation = {
            "criteria_clarity": self.assess_criteria_clarity(text),
            "weight_distribution": self.check_weight_distribution(text),
            "objectivity_check": self.check_evaluation_objectivity(text),
            "committee_composition": self.check_committee_composition(text),
            "evaluation_score": 0
        }
        
        # Calculate evaluation score
        scores = [
            evaluation["criteria_clarity"]["score"],
            evaluation["weight_distribution"]["score"],
            evaluation["objectivity_check"]["score"],
            evaluation["committee_composition"]["score"]
        ]
        
        evaluation["evaluation_score"] = sum(scores) // len(scores) if scores else 0
        
        return evaluation
    
    def assess_criteria_clarity(self, text: str) -> Dict[str, Any]:
        """Assess clarity of evaluation criteria"""
        clarity = {
            "is_quantified": bool(re.search(r'\d+%|权重|分值', text)),
            "has_detailed_items": bool(re.search(r'评审项|评分项', text)),
            "score": 0
        }
        
        if clarity["is_quantified"] and clarity["has_detailed_items"]:
            clarity["score"] = 3
        elif clarity["is_quantified"] or clarity["has_detailed_items"]:
            clarity["score"] = 2
        else:
            clarity["score"] = 0
            
        return clarity
    
    def check_weight_distribution(self, text: str) -> Dict[str, Any]:
        """Check weight distribution in evaluation"""
        weight = {
            "has_weight_info": bool(re.search(r'权重分配|分值比例', text)),
            "has_price_weight": bool(re.search(r'价格.*?权重|报价.*?分值', text)),
            "score": 0
        }
        
        if weight["has_weight_info"] and weight["has_price_weight"]:
            weight["score"] = 3
        elif weight["has_weight_info"]:
            weight["score"] = 2
        else:
            weight["score"] = 0
            
        return weight
    
    def check_evaluation_objectivity(self, text: str) -> Dict[str, Any]:
        """Check objectivity of evaluation criteria"""
        objectivity = {
            "has_subjective_terms": bool(re.search(r'酌情|适当|专家判断', text)),
            "has_objective_standards": bool(re.search(r'明确标准|具体指标', text)),
            "score": 0
        }
        
        if objectivity["has_objective_standards"] and not objectivity["has_subjective_terms"]:
            objectivity["score"] = 3
        elif objectivity["has_objective_standards"]:
            objectivity["score"] = 2
        else:
            objectivity["score"] = 0
            
        return objectivity
    
    def check_committee_composition(self, text: str) -> Dict[str, Any]:
        """Check composition of evaluation committee"""
        committee = {
            "has_committee_info": bool(re.search(r'评标委员会|评审专家', text)),
            "has_expert_requirements": bool(re.search(r'专家.*?资质|评委.*?条件', text)),
            "score": 0
        }
        
        if committee["has_committee_info"] and committee["has_expert_requirements"]:
            committee["score"] = 3
        elif committee["has_committee_info"]:
            committee["score"] = 2
        else:
            committee["score"] = 0
            
        return committee
    
    def analyze_qualification_requirements(self, text: str) -> Dict[str, Any]:
        """Analyze qualification requirements for bidders"""
        qualification = {
            "basic_requirements": self.check_basic_requirements(text),
            "specialized_requirements": self.check_specialized_requirements(text),
            "discrimination_check": self.check_for_discrimination(text),
            "clarity_score": 0
        }
        
        # Calculate clarity score
        scores = [
            qualification["basic_requirements"]["score"],
            qualification["specialized_requirements"]["score"],
            3 if not qualification["discrimination_check"]["found"] else 0
        ]
        
        qualification["clarity_score"] = sum(scores) // len(scores) if scores else 0
        
        return qualification
    
    def check_basic_requirements(self, text: str) -> Dict[str, Any]:
        """Check basic qualification requirements"""
        basic = {
            "has_legal_status": bool(re.search(r'法人资格|营业执照|合法经营', text)),
            "has_credit_requirements": bool(re.search(r'信用记录|失信|行政处罚', text)),
            "score": 0
        }
        
        if basic["has_legal_status"] and basic["has_credit_requirements"]:
            basic["score"] = 3
        elif basic["has_legal_status"]:
            basic["score"] = 2
        else:
            basic["score"] = 0
            
        return basic
    
    def check_specialized_requirements(self, text: str) -> Dict[str, Any]:
        """Check specialized qualification requirements"""
        specialized = {
            "has_technical_qualifications": bool(re.search(r'技术资质|专业认证|行业许可', text)),
            "has_experience_requirements": bool(re.search(r'类似项目|业绩|经验', text)),
            "score": 0
        }
        
        if specialized["has_technical_qualifications"] and specialized["has_experience_requirements"]:
            specialized["score"] = 3
        elif specialized["has_technical_qualifications"] or specialized["has_experience_requirements"]:
            specialized["score"] = 2
        else:
            specialized["score"] = 0
            
        return specialized
    
    def check_for_discrimination(self, text: str) -> Dict[str, Any]:
        """Check for discriminatory requirements"""
        discrimination = {
            "found": False,
            "terms": []
        }
        
        discriminatory_patterns = [
            r'本地.*?企业|本地.*?注册',
            r'指定.*?品牌|特定.*?供应商',
            r'仅限.*?投标',
            r'不合理.*?门槛|过高.*?要求'
        ]
        
        for pattern in discriminatory_patterns:
            matches = re.findall(pattern, text)
            if matches:
                discrimination["found"] = True
                discrimination["terms"].extend(matches)
                
        return discrimination
    
    def get_llm_tender_analysis(self, text: str) -> str:
        """Get detailed tender document analysis from LLM"""
        analysis_prompt = f"""
        请对以下招标文件进行专业的法律分析：
        
        招标文件文本：{text[:3000]}...
        
        请从以下角度进行分析：
        1. 招标程序的合法性评估
        2. 主要招标风险识别
        3. 资格要求和评审标准的合理性
        4. 招标文件条款的完整性和明确性
        5. 异议与投诉机制的有效性
        6. 需要补充或修改的条款
        
        请提供具体、专业的法律意见和建议。
        """
        
        return self.call_llm(analysis_prompt)
    
    def generate_tender_recommendations(self, text: str) -> List[Dict[str, str]]:
        """Generate tender document recommendations"""
        recommendations = []
        
        # Check for missing clauses
        if not re.search(r'质疑|投诉|异议', text):
            recommendations.append({
                "type": "补充条款",
                "priority": "高",
                "recommendation": "建议添加异议与投诉处理条款，明确质疑程序、时限和救济途径"
            })
        
        if not re.search(r'评分标准|评审细则', text):
            recommendations.append({
                "type": "补充条款",
                "priority": "高",
                "recommendation": "建议明确评审标准和打分细则，确保评审过程的公平公正"
            })
        
        # Check for risky clauses
        if re.search(r'本地.*?优先|指定.*?品牌', text):
            recommendations.append({
                "type": "修改条款",
                "priority": "高",
                "recommendation": "存在潜在的歧视性条款，可能违反招标投标法，建议修改为开放性要求"
            })
        
        if not re.search(r'公告.*?期限|公示.*?日', text):
            recommendations.append({
                "type": "补充条款",
                "priority": "中",
                "recommendation": "建议明确招标文件公告期限和中标结果公示期限，符合法定要求"
            })
        
        return recommendations
    
    def format_tender_analysis(self, analysis: Dict[str, Any]) -> str:
        """Format tender document analysis results for output"""
        output = "=== 招标文件分析报告 ===\n\n"
        
        # Risk Assessment
        risk_assessment = analysis.get("risk_assessment", {})
        output += f"招标风险评分：{risk_assessment.get('risk_score', 0)}/10\n\n"
        
        # High Risk Issues
        high_risks = risk_assessment.get("high_risk", [])
        if high_risks:
            output += "--- 高风险问题 ---\n"
            for risk in high_risks:
                output += f"• {risk['category']}：风险分数 {risk['score']}/10\n"
                for issue in risk.get("issues", []):
                    output += f"  - {issue}\n"
            output += "\n"
        
        # Compliance Check
        compliance = analysis.get("compliance_check", {})
        output += f"合规性评分：{compliance.get('compliance_score', 0)}/10\n"
        
        required_clauses = compliance.get("required_clauses", [])
        missing_clauses = [clause["name"] for clause in required_clauses if not clause["present"]]
        if missing_clauses:
            output += f"缺失必要条款：{', '.join(missing_clauses)}\n"
        
        # Tender Procedure
        procedure = analysis.get("procedure_check", {})
        output += f"招标程序评分：{procedure.get('procedure_score', 0)}/10\n"
        output += f"招标方式：{procedure.get('tender_method', '未明确')}\n\n"
        
        # Evaluation Criteria
        evaluation = analysis.get("evaluation_analysis", {})
        output += "--- 评审标准分析 ---\n"
        output += f"评审标准清晰度：{evaluation.get('criteria_clarity', {}).get('score', 0)}/3\n"
        output += f"权重分配合理性：{evaluation.get('weight_distribution', {}).get('score', 0)}/3\n"
        output += f"评审客观性：{evaluation.get('objectivity_check', {}).get('score', 0)}/3\n"
        output += f"评审委员会合规性：{evaluation.get('committee_composition', {}).get('score', 0)}/3\n\n"
        
        # Recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            output += "--- 改进建议 ---\n"
            for i, rec in enumerate(recommendations, 1):
                output += f"{i}. [{rec['priority']}] {rec['recommendation']}\n"
            output += "\n"
        
        # Detailed Analysis
        detailed_analysis = analysis.get("detailed_analysis", "")
        if detailed_analysis:
            output += "--- 详细分析 ---\n"
            output += detailed_analysis
        
        return output

if __name__ == "__main__":
    agent = LegalAgent()