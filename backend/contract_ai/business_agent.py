import json
import re
from typing import Dict, List, Any, Optional
from base_agent import BaseAgent

class ContractReviewAgent(BaseAgent):
    """Agent specialized in contract review and legal analysis"""
    
    def __init__(self):
        system_prompt = """你是专门进行合同文件审查的智能体。你的职责包括：

1. 合同条款合法性与合规性审查
2. 权利义务对等性与公平性评估
3. 条款明确性与可执行性分析
4. 风险点识别与责任划分审查
5. 争议解决机制有效性评估
6. 合同生效与终止条件合规性审核

重点分析领域：
- 当事人主体资格与签约权限（是否合法、无瑕疵）
- 合同标的与范围（是否清晰、无歧义）
- 权利义务约定（是否对等、无失衡）
- 价格与支付条款（是否明确、可执行）
- 履行期限与方式（是否具体、可操作）
- 质量标准与验收（是否明确、可验证）
- 违约责任（是否合理、可量化）
- 知识产权与保密条款（是否清晰、无漏洞）
- 争议解决方式（是否有效、可执行）
- 不可抗力与情势变更（是否完整、合理）

你的分析应该：
- 从合法性、公平性、可执行性三维度评估
- 识别条款中的模糊性、歧义性、冲突性风险
- 对标相关法律法规（如《民法典》合同编）及行业惯例
- 提示潜在的法律纠纷、履行争议风险
- 提供条款优化建议（兼顾双方权益与交易安全）
- 为合同完善或签署决策提供专业支持"""

        super().__init__(agent_name="ContractReviewAgent", system_prompt=system_prompt)
        self.contract_metrics = self.initialize_contract_metrics()
    
    def initialize_contract_metrics(self) -> Dict[str, List[str]]:
        """Initialize contract document review metrics and keywords"""
        return {
            "合同主体": [
                "甲方", "乙方", "丙方", "当事人", "主体", "资格", "资质", "权限", "授权"
            ],
            "合同标的": [
                "标的", "标的物", "标的额", "产品", "服务", "内容", "范围", "数量", "规格"
            ],
            "权利义务": [
                "权利", "义务", "责任", "权限", "职责", "应尽", "享有", "承担"
            ],
            "价格支付": [
                "价款", "金额", "支付", "付款", "结算", "发票", "税率", "定金", "预付款"
            ],
            "履行期限": [
                "期限", "时间", "日期", "有效期", "起始日", "截止日", "履行期", "工期"
            ],
            "质量标准": [
                "质量", "标准", "规范", "要求", "验收", "检验", "合格", "达标"
            ],
            "违约责任": [
                "违约", "责任", "赔偿", "违约金", "罚金", "处罚", "损失", "补救"
            ],
            "争议解决": [
                "争议", "纠纷", "解决", "诉讼", "仲裁", "管辖", "法院", "调解"
            ],
            "知识产权": [
                "知识产权", "专利", "商标", "著作权", "版权", "许可", "转让", "归属"
            ],
            "保密条款": [
                "保密", "秘密", "不得泄露", "保密义务", "保密期限", "涉密信息"
            ],
            "不可抗力": [
                "不可抗力", "意外事件", "不可预见", "无法避免", "免责", "情势变更"
            ],
            "合同生效": [
                "生效", "成立", "生效条件", "签署", "盖章", "批准", "备案"
            ],
            "合同终止": [
                "终止", "解除", "终止条件", "解除权", "终止后果", "解除程序"
            ]
        }
    
    def process_text_message(self, message, context=None):
        """Process contract review requests"""
        user_text = message
        self.logger.info("Processing contract review request")
        
        try:
            # Extract task and content
            task_info = self.extract_task_info(user_text)
            document_content = task_info.get("content", user_text)
            
            # Perform contract analysis
            contract_analysis = self.perform_contract_analysis(document_content)
            
            # Format response
            response_text = self.format_contract_analysis(contract_analysis)
            
            return {
                "agent": "ContractReviewAgent",
                "status": "success",
                "analysis": contract_analysis,
                "response_text": response_text,
                "timestamp": self._get_current_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Error in contract analysis: {str(e)}")
            return {
                "agent": "ContractReviewAgent",
                "status": "error",
                "message": f"合同分析过程中发生错误：{str(e)}",
                "response_text": "合同分析过程中发生错误。",
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
    
    def perform_contract_analysis(self, document_text: str) -> Dict[str, Any]:
        """Perform comprehensive contract analysis"""
        analysis = {
            "party_analysis": self.analyze_parties(document_text),
            "term_analysis": self.analyze_contract_terms(document_text),
            "obligation_analysis": self.analyze_rights_obligations(document_text),
            "risk_analysis": self.assess_contract_risks(document_text),
            "compliance_analysis": self.analyze_compliance(document_text),
            "enforceability_analysis": self.assess_enforceability(document_text),
            "recommendations": self.generate_contract_recommendations(document_text)
        }
        
        # Get detailed analysis from LLM
        llm_analysis = self.get_llm_contract_analysis(document_text)
        analysis["detailed_analysis"] = llm_analysis
        
        return analysis
    
    def analyze_parties(self, text: str) -> Dict[str, Any]:
        """Analyze contract parties and their qualifications"""
        party_analysis = {
            "parties_identified": self.identify_parties(text),
            "qualification_check": self.check_qualifications(text),
            "authorization_check": self.check_authorization(text),
            "capacity_analysis": self.analyze_contract_capacity(text)
        }
        
        return party_analysis
    
    def identify_parties(self, text: str) -> List[Dict[str, str]]:
        """Identify contract parties"""
        parties = []
        
        # Identify primary parties
        party_patterns = [
            (r'甲方：(.*?)\n', '甲方'),
            (r'乙方：(.*?)\n', '乙方'),
            (r'丙方：(.*?)\n', '丙方'),
            (r'甲方名称：(.*?)\n', '甲方'),
            (r'乙方名称：(.*?)\n', '乙方'),
            (r'甲方全称：(.*?)\n', '甲方'),
            (r'乙方全称：(.*?)\n', '乙方')
        ]
        
        for pattern, party_type in party_patterns:
            match = re.search(pattern, text)
            if match:
                parties.append({
                    "type": party_type,
                    "name": match.group(1).strip()
                })
        
        # If no structured parties found, look for general mentions
        if not parties:
            if re.search(r'甲方|乙方', text):
                parties.append({"type": "甲方", "name": "未明确"})
                parties.append({"type": "乙方", "name": "未明确"})
        
        return parties
    
    def check_qualifications(self, text: str) -> Dict[str, Any]:
        """Check if parties have required qualifications"""
        qualifications = {
            "has_qualification_clause": False,
            "qualifications_specified": [],
            "potential_issues": []
        }
        
        # Check for qualification clauses
        if re.search(r'资质|资格|许可|认证', text):
            qualifications["has_qualification_clause"] = True
            
            # Extract specific qualifications
            qual_keywords = ['营业执照', '经营许可证', '资质证书', '专业认证', '行业许可']
            for qual in qual_keywords:
                if qual in text:
                    qualifications["qualifications_specified"].append(qual)
        
        # Identify potential issues
        if not qualifications["has_qualification_clause"]:
            qualifications["potential_issues"].append("未明确约定当事人应具备的资质要求")
        
        return qualifications
    
    def check_authorization(self, text: str) -> Dict[str, Any]:
        """Check if signatories have proper authorization"""
        authorization = {
            "has_authorization_clause": False,
            "authorization_type": [],
            "potential_issues": []
        }
        
        if re.search(r'授权|委托|代表权|签字权', text):
            authorization["has_authorization_clause"] = True
            
            if re.search(r'法定代表人|法人', text):
                authorization["authorization_type"].append("法定代表人授权")
            if re.search(r'授权委托书|委托书', text):
                authorization["authorization_type"].append("授权委托书")
            if re.search(r'公章|合同章', text):
                authorization["authorization_type"].append("印章授权")
        
        if not authorization["has_authorization_clause"]:
            authorization["potential_issues"].append("未明确签约人的授权范围和权限")
        
        return authorization
    
    def analyze_contract_capacity(self, text: str) -> Dict[str, str]:
        """Analyze parties' contract capacity"""
        capacity = {
            "legal_person_check": "未明确",
            "natural_person_check": "未明确",
            "capacity_issues": []
        }
        
        if re.search(r'公司|企业|法人|组织', text):
            capacity["legal_person_check"] = "提及法人主体"
        
        if re.search(r'个人|自然人', text):
            capacity["natural_person_check"] = "提及自然人主体"
        
        if not capacity["legal_person_check"] and not capacity["natural_person_check"]:
            capacity["capacity_issues"].append("未明确合同当事人类型及民事行为能力")
        
        return capacity
    
    def analyze_contract_terms(self, text: str) -> Dict[str, Any]:
        """Analyze key contract terms"""
        term_analysis = {
            "subject_matter": self.analyze_subject_matter(text),
            "price_terms": self.analyze_price_terms(text),
            "performance_terms": self.analyze_performance_terms(text),
            "time_terms": self.analyze_time_terms(text),
            "quality_terms": self.analyze_quality_terms(text)
        }
        
        return term_analysis
    
    def analyze_subject_matter(self, text: str) -> Dict[str, Any]:
        """Analyze contract subject matter"""
        subject = {
            "description_clarity": "不明确",
            "scope_defined": False,
            "specifications": [],
            "potential_issues": []
        }
        
        # Check clarity of description
        subject_keywords = ['标的', '标的物', '产品', '服务', '内容', '范围']
        subject_mentions = sum(1 for kw in subject_keywords if kw in text)
        
        if subject_mentions >= 3:
            subject["description_clarity"] = "较明确"
        elif subject_mentions > 0:
            subject["description_clarity"] = "基本明确"
        
        # Check if scope is defined
        if re.search(r'范围|包括|包含|除外|不包括', text):
            subject["scope_defined"] = True
        
        # Extract specifications
        spec_patterns = [
            r'规格：(.*?)\n',
            r'型号：(.*?)\n',
            r'数量：(.*?)\n',
            r'标准：(.*?)\n'
        ]
        
        for pattern in spec_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                subject["specifications"].append(match.strip())
        
        # Identify issues
        if subject["description_clarity"] == "不明确":
            subject["potential_issues"].append("合同标的描述不清晰，可能导致履行争议")
        
        return subject
    
    def analyze_price_terms(self, text: str) -> Dict[str, Any]:
        """Analyze price and payment terms"""
        price_terms = {
            "price_determination": "未明确",
            "payment_schedule": self.extract_payment_schedule(text),
            "payment_conditions": [],
            "tax_clauses": self.analyze_tax_clauses(text),
            "potential_issues": []
        }
        
        # Determine price type
        if re.search(r'固定价|包干价|总价', text):
            price_terms["price_determination"] = "固定价格"
        elif re.search(r'单价|单位价格', text):
            price_terms["price_determination"] = "单价形式"
        elif re.search(r'成本加|可调价', text):
            price_terms["price_determination"] = "可调价格"
        
        # Extract payment conditions
        if re.search(r'验收合格后|验收通过后', text):
            price_terms["payment_conditions"].append("验收合格后付款")
        if re.search(r'发货后|交付后', text):
            price_terms["payment_conditions"].append("交付后付款")
        if re.search(r'见票后|收到发票后', text):
            price_terms["payment_conditions"].append("收到发票后付款")
        
        # Identify issues
        if price_terms["price_determination"] == "未明确":
            price_terms["potential_issues"].append("未明确价格确定方式")
        
        if not price_terms["payment_schedule"]:
            price_terms["potential_issues"].append("未约定具体付款时间表")
        
        return price_terms
    
    def extract_payment_schedule(self, text: str) -> List[Dict[str, str]]:
        """Extract payment schedule information"""
        schedule = []
        lines = text.split('\n')
        
        payment_keywords = ['预付', '首付', '进度款', '尾款', '分期', '结算', '到期付款']
        
        for line in lines:
            for keyword in payment_keywords:
                if keyword in line:
                    # Extract percentage if present
                    percentage = None
                    percent_match = re.search(r'(\d+)%', line)
                    if percent_match:
                        percentage = percent_match.group(1) + "%"
                    
                    schedule.append({
                        "type": keyword,
                        "description": line.strip(),
                        "percentage": percentage
                    })
                    break
        
        return schedule
    
    def analyze_tax_clauses(self, text: str) -> Dict[str, Any]:
        """Analyze tax-related clauses"""
        tax_analysis = {
            "has_tax_clause": False,
            "tax_bearing": "未明确",
            "invoice_requirements": []
        }
        
        if re.search(r'税|税率|发票|税额', text):
            tax_analysis["has_tax_clause"] = True
            
            # Determine tax bearing
            if re.search(r'甲方承担|买方承担', text):
                tax_analysis["tax_bearing"] = "甲方承担"
            elif re.search(r'乙方承担|卖方承担', text):
                tax_analysis["tax_bearing"] = "乙方承担"
            
            # Check invoice requirements
            if re.search(r'增值税专用发票', text):
                tax_analysis["invoice_requirements"].append("增值税专用发票")
            elif re.search(r'普通发票', text):
                tax_analysis["invoice_requirements"].append("普通发票")
        
        return tax_analysis
    
    def analyze_performance_terms(self, text: str) -> Dict[str, Any]:
        """Analyze performance terms"""
        performance = {
            "performance_obligations": self.extract_obligations(text),
            "performance_location": "未明确",
            "performance_method": "未明确",
            "potential_issues": []
        }
        
        # Check performance location
        if re.search(r'地点|地址|场所', text):
            location_match = re.search(r'地点：(.*?)\n', text)
            if location_match:
                performance["performance_location"] = location_match.group(1).strip()
            else:
                performance["performance_location"] = "已提及但未明确具体位置"
        
        # Check performance method
        if re.search(r'方式|方法|途径', text):
            performance["performance_method"] = "已约定履行方式"
        
        # Identify issues
        if not performance["performance_obligations"]:
            performance["potential_issues"].append("未明确双方主要履行义务")
        
        return performance
    
    def extract_obligations(self, text: str) -> List[Dict[str, str]]:
        """Extract performance obligations for each party"""
        obligations = []
        lines = text.split('\n')
        
        for line in lines:
            if re.search(r'甲方应|甲方负责', line):
                obligations.append({
                    "party": "甲方",
                    "obligation": line.strip()
                })
            elif re.search(r'乙方应|乙方负责', line):
                obligations.append({
                    "party": "乙方",
                    "obligation": line.strip()
                })
        
        return obligations
    
    def analyze_time_terms(self, text: str) -> Dict[str, Any]:
        """Analyze time-related terms"""
        time_terms = {
            "effective_date": self.extract_effective_date(text),
            "termination_date": self.extract_termination_date(text),
            "performance_period": "未明确",
            "time_limits": self.extract_time_limits(text),
            "potential_issues": []
        }
        
        # Check performance period
        period_match = re.search(r'有效期(.*?)年|期限(.*?)年', text)
        if period_match:
            time_terms["performance_period"] = f"{period_match.group(1) or period_match.group(2)}年"
        
        # Identify issues
        if time_terms["effective_date"] == "未明确":
            time_terms["potential_issues"].append("未明确合同生效日期")
        
        return time_terms
    
    def extract_effective_date(self, text: str) -> str:
        """Extract contract effective date"""
        if re.search(r'生效日期|生效日', text):
            date_match = re.search(r'生效日期：(.*?)\n', text)
            if date_match:
                return date_match.group(1).strip()
            elif re.search(r'自签署之日起生效', text):
                return "签署之日起生效"
            elif re.search(r'自.*?之日起生效', text):
                return "有条件生效"
        
        return "未明确"
    
    def extract_termination_date(self, text: str) -> str:
        """Extract contract termination date"""
        if re.search(r'终止日期|到期日', text):
            date_match = re.search(r'终止日期：(.*?)\n', text)
            if date_match:
                return date_match.group(1).strip()
            elif re.search(r'有效期届满自动终止', text):
                return "有效期届满自动终止"
        
        return "未明确"
    
    def extract_time_limits(self, text: str) -> List[Dict[str, str]]:
        """Extract key time limits"""
        time_limits = []
        
        limit_patterns = [
            (r'(\d+)日内.*?交付', '交付期限'),
            (r'(\d+)日内.*?付款', '付款期限'),
            (r'(\d+)日内.*?回复', '回复期限'),
            (r'(\d+)日内.*?履行', '履行期限')
        ]
        
        for pattern, limit_type in limit_patterns:
            match = re.search(pattern, text)
            if match:
                time_limits.append({
                    "type": limit_type,
                    "duration": f"{match.group(1)}日内"
                })
        
        return time_limits
    
    def analyze_quality_terms(self, text: str) -> Dict[str, Any]:
        """Analyze quality and acceptance terms"""
        quality_terms = {
            "quality_standards": self.extract_quality_standards(text),
            "acceptance_criteria": self.extract_acceptance_criteria(text),
            "inspection_procedures": self.extract_inspection_procedures(text),
            "potential_issues": []
        }
        
        # Identify issues
        if not quality_terms["quality_standards"]:
            quality_terms["potential_issues"].append("未明确质量标准和要求")
        
        if not quality_terms["acceptance_criteria"]:
            quality_terms["potential_issues"].append("未约定验收标准和程序")
        
        return quality_terms
    
    def extract_quality_standards(self, text: str) -> List[str]:
        """Extract quality standards"""
        standards = []
        lines = text.split('\n')
        
        for line in lines:
            if re.search(r'质量标准|质量要求|应符合', line):
                standards.append(line.strip())
        
        return standards
    
    def extract_acceptance_criteria(self, text: str) -> List[str]:
        """Extract acceptance criteria"""
        criteria = []
        lines = text.split('\n')
        
        for line in lines:
            if re.search(r'验收标准|验收条件|视为合格', line):
                criteria.append(line.strip())
        
        return criteria
    
    def extract_inspection_procedures(self, text: str) -> List[str]:
        """Extract inspection procedures"""
        procedures = []
        lines = text.split('\n')
        
        for line in lines:
            if re.search(r'检验|检查|验收程序|验收流程', line):
                procedures.append(line.strip())
        
        return procedures
    
    def analyze_rights_obligations(self, text: str) -> Dict[str, Any]:
        """Analyze rights and obligations balance"""
        rights_obligations = {
            "rights_balance": self.assess_rights_balance(text),
            "obligations_balance": self.assess_obligations_balance(text),
            "intellectual_property": self.analyze_ip_clauses(text),
            "confidentiality": self.analyze_confidentiality(text),
            "potential_imbalances": []
        }
        
        # Identify potential imbalances
        if rights_obligations["rights_balance"] == "可能失衡":
            rights_obligations["potential_imbalances"].append("双方权利可能不对等")
        
        if rights_obligations["obligations_balance"] == "可能失衡":
            rights_obligations["potential_imbalances"].append("双方义务可能不对等")
        
        return rights_obligations
    
    def assess_rights_balance(self, text: str) -> str:
        """Assess balance of rights between parties"""
        party_a_rights = len(re.findall(r'甲方有权|甲方享有', text))
        party_b_rights = len(re.findall(r'乙方有权|乙方享有', text))
        
        if party_a_rights == 0 and party_b_rights == 0:
            return "未明确约定权利"
        elif abs(party_a_rights - party_b_rights) <= 1:
            return "基本平衡"
        else:
            return "可能失衡"
    
    def assess_obligations_balance(self, text: str) -> str:
        """Assess balance of obligations between parties"""
        party_a_obligations = len(re.findall(r'甲方应|甲方负责|甲方承担', text))
        party_b_obligations = len(re.findall(r'乙方应|乙方负责|乙方承担', text))
        
        if party_a_obligations == 0 and party_b_obligations == 0:
            return "未明确约定义务"
        elif abs(party_a_obligations - party_b_obligations) <= 1:
            return "基本平衡"
        else:
            return "可能失衡"
    
    def analyze_ip_clauses(self, text: str) -> Dict[str, Any]:
        """Analyze intellectual property clauses"""
        ip_analysis = {
            "has_ip_clause": False,
            "ip_ownership": "未明确",
            "license_terms": [],
            "infringement_liability": "未明确"
        }
        
        if re.search(r'知识产权|专利|商标|著作权|版权', text):
            ip_analysis["has_ip_clause"] = True
            
            # Check IP ownership
            if re.search(r'归甲方所有|甲方享有', text):
                ip_analysis["ip_ownership"] = "归甲方所有"
            elif re.search(r'归乙方所有|乙方享有', text):
                ip_analysis["ip_ownership"] = "归乙方所有"
            elif re.search(r'共有|双方共有', text):
                ip_analysis["ip_ownership"] = "双方共有"
            
            # Check license terms
            if re.search(r'许可|授权|使用权', text):
                ip_analysis["license_terms"].append("包含知识产权许可条款")
            
            # Check infringement liability
            if re.search(r'侵权|责任|赔偿', text):
                ip_analysis["infringement_liability"] = "已约定侵权责任"
        
        return ip_analysis
    
    def analyze_confidentiality(self, text: str) -> Dict[str, Any]:
        """Analyze confidentiality clauses"""
        confidentiality = {
            "has_confidentiality_clause": False,
            "confidential_info_scope": "未明确",
            "obligation_duration": "未明确",
            "exceptions": []
        }
        
        if re.search(r'保密|秘密|不得泄露', text):
            confidentiality["has_confidentiality_clause"] = True
            
            # Check duration
            duration_match = re.search(r'保密期(.*?)年|保密义务(.*?)年', text)
            if duration_match:
                confidentiality["obligation_duration"] = f"{duration_match.group(1) or duration_match.group(2)}年"
            elif re.search(r'永久保密', text):
                confidentiality["obligation_duration"] = "永久"
            
            # Check exceptions
            if re.search(r'公开信息|已获知|法律要求', text):
                confidentiality["exceptions"].append("存在保密义务例外情形")
        
        return confidentiality
    
    def assess_contract_risks(self, text: str) -> Dict[str, Any]:
        """Assess contract risks"""
        contract_risks = {
            "breach_risks": self.analyze_breach_risks(text),
            "termination_risks": self.analyze_termination_risks(text),
            "force_majeure": self.analyze_force_majeure(text),
            "dispute_risks": self.assess_dispute_risks(text),
            "overall_risk_level": "中等"
        }
        
        # Calculate overall risk level
        total_risks = len(contract_risks["breach_risks"]["potential_issues"]) + \
                     len(contract_risks["termination_risks"]["potential_issues"]) + \
                     len(contract_risks["dispute_risks"]["potential_issues"])
        
        if total_risks >= 6:
            contract_risks["overall_risk_level"] = "高"
        elif total_risks <= 2:
            contract_risks["overall_risk_level"] = "低"
        
        return contract_risks
    
    def analyze_breach_risks(self, text: str) -> Dict[str, Any]:
        """Analyze breach of contract risks"""
        breach_analysis = {
            "breach_definitions": self.extract_breach_definitions(text),
            "remedies": self.extract_remedies(text),
            "liquidated_damages": self.analyze_liquidated_damages(text),
            "potential_issues": []
        }
        
        # Identify issues
        if not breach_analysis["breach_definitions"]:
            breach_analysis["potential_issues"].append("未明确定义违约情形")
        
        if not breach_analysis["remedies"]:
            breach_analysis["potential_issues"].append("未约定违约救济措施")
        
        return breach_analysis
    
    def extract_breach_definitions(self, text: str) -> List[str]:
        """Extract breach of contract definitions"""
        breaches = []
        lines = text.split('\n')
        
        for line in lines:
            if re.search(r'违约|视为违约|构成违约', line):
                breaches.append(line.strip())
        
        return breaches
    
    def extract_remedies(self, text: str) -> List[str]:
        """Extract breach remedies"""
        remedies = []
        
        remedy_keywords = {
            '继续履行': ['继续履行', '强制履行'],
            '采取补救措施': ['补救', '采取措施', '纠正'],
            '赔偿损失': ['赔偿', '赔偿损失', '补偿'],
            '支付违约金': ['违约金', '罚金', '支付罚款'],
            '解除合同': ['解除合同', '终止合同']
        }
        
        for remedy, keywords in remedy_keywords.items():
            if any(keyword in text for keyword in keywords):
                remedies.append(remedy)
        
        return remedies
    
    def analyze_liquidated_damages(self, text: str) -> Dict[str, Any]:
        """Analyze liquidated damages clauses"""
        damages = {
            "has_liquidated_clause": False,
            "amount_or_rate": "未明确",
            "reasonableness": "无法评估"
        }
        
        if re.search(r'违约金|罚金|违约金额', text):
            damages["has_liquidated_clause"] = True
            
            # Extract amount or rate
            amount_match = re.search(r'违约金(.*?)(元|%)', text)
            if amount_match:
                damages["amount_or_rate"] = amount_match.group(0)
        
        return damages
    
    def analyze_termination_risks(self, text: str) -> Dict[str, Any]:
        """Analyze contract termination risks"""
        termination = {
            "termination_rights": self.extract_termination_rights(text),
            "termination_procedures": "未明确",
            "post_termination_obligations": [],
            "potential_issues": []
        }
        
        # Check termination procedures
        if re.search(r'通知|期限|书面形式', text) and re.search(r'终止|解除', text):
            termination["termination_procedures"] = "已约定终止程序"
        
        # Check post-termination obligations
        if re.search(r'终止后|解除后', text):
            post_match = re.search(r'终止后(.*?)\n', text)
            if post_match:
                termination["post_termination_obligations"].append(post_match.group(1).strip())
        
        # Identify issues
        if not termination["termination_rights"]:
            termination["potential_issues"].append("未明确合同终止权及条件")
        
        return termination
    
    def extract_termination_rights(self, text: str) -> List[Dict[str, str]]:
        """Extract termination rights"""
        termination_rights = []
        
        right_patterns = [
            (r'甲方有权.*?解除|甲方有权.*?终止', '甲方'),
            (r'乙方有权.*?解除|乙方有权.*?终止', '乙方'),
            (r'双方均有权.*?解除|双方均有权.*?终止', '双方')
        ]
        
        for pattern, party in right_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                termination_rights.append({
                    "party": party,
                    "right": match.strip()
                })
        
        return termination_rights
    
    def analyze_force_majeure(self, text: str) -> Dict[str, Any]:
        """Analyze force majeure clauses"""
        force_majeure = {
            "has_force_majeure_clause": False,
            "events_defined": [],
            "notice_requirements": "未明确",
            "consequences": "未明确"
        }
        
        if re.search(r'不可抗力', text):
            force_majeure["has_force_majeure_clause"] = True
            
            # Extract defined events
            event_keywords = ['战争', '自然灾害', '地震', '洪水', '疫情', '政府行为', '罢工']
            for event in event_keywords:
                if event in text:
                    force_majeure["events_defined"].append(event)
            
            # Check notice requirements
            if re.search(r'通知|期限|书面', text):
                force_majeure["notice_requirements"] = "已约定通知要求"
            
            # Check consequences
            if re.search(r'延期|中止|解除|免责', text):
                force_majeure["consequences"] = "已约定不可抗力后果"
        
        return force_majeure
    
    def assess_dispute_risks(self, text: str) -> Dict[str, Any]:
        """Assess potential dispute risks"""
        dispute_analysis = {
            "dispute_resolution_method": self.extract_dispute_method(text),
            "jurisdiction": self.extract_jurisdiction(text),
            "alternative_dispute_resolution": "未约定",
            "potential_issues": []
        }
        
        # Check ADR clauses
        if re.search(r'协商|调解|和解', text):
            dispute_analysis["alternative_dispute_resolution"] = "已约定协商/调解"
        
        # Identify issues
        if dispute_analysis["dispute_resolution_method"] == "未明确":
            dispute_analysis["potential_issues"].append("未明确争议解决方式")
        
        if dispute_analysis["jurisdiction"] == "未明确" and "诉讼" in dispute_analysis["dispute_resolution_method"]:
            dispute_analysis["potential_issues"].append("未明确诉讼管辖法院")
        
        return dispute_analysis
    
    def extract_dispute_method(self, text: str) -> str:
        """Extract dispute resolution method"""
        if re.search(r'诉讼', text) and re.search(r'仲裁', text):
            return "同时约定了诉讼和仲裁（可能冲突）"
        elif re.search(r'仲裁', text):
            return "仲裁"
        elif re.search(r'诉讼', text):
            return "诉讼"
        else:
            return "未明确"
    
    def extract_jurisdiction(self, text: str) -> str:
        """Extract jurisdiction information"""
        if re.search(r'法院|管辖', text):
            court_match = re.search(r'(.*?)法院.*?管辖', text)
            if court_match:
                return court_match.group(1) + "法院"
            elif re.search(r'甲方所在地|乙方所在地', text):
                return "约定了一方所在地管辖"
        
        if re.search(r'仲裁委员会', text):
            arbitrator_match = re.search(r'(.*?)仲裁委员会', text)
            if arbitrator_match:
                return arbitrator_match.group(1) + "仲裁委员会"
        
        return "未明确"
    
    def analyze_compliance(self, text: str) -> Dict[str, Any]:
        """Analyze legal compliance"""
        compliance = {
            "applicable_laws": self.extract_applicable_laws(text),
            "regulatory_compliance": self.check_regulatory_compliance(text),
            "public_policy_check": "未发现明显违反公序良俗内容",
            "potential_issues": []
        }
        
        # Identify issues
        if not compliance["applicable_laws"]:
            compliance["potential_issues"].append("未明确适用法律")
        
        return compliance
    
    def extract_applicable_laws(self, text: str) -> List[str]:
        """Extract applicable laws and regulations"""
        laws = []
        
        if re.search(r'适用法律|依据法律', text):
            law_keywords = ['民法典', '合同法', '公司法', '招标投标法', '知识产权法']
            for law in law_keywords:
                if law in text:
                    laws.append(law)
            
            if not laws:
                laws.append("提及适用法律但未明确具体法规")
        
        return laws
    
    def check_regulatory_compliance(self, text: str) -> Dict[str, str]:
        """Check regulatory compliance mentions"""
        compliance = {
            "industry_regulations": "未提及",
            "government_approval": "未提及",
            "reporting_requirements": "未提及"
        }
        
        if re.search(r'行业规定|行业标准|监管要求', text):
            compliance["industry_regulations"] = "提及行业监管要求"
        
        if re.search(r'审批|批准|备案', text):
            compliance["government_approval"] = "提及需要政府审批"
        
        if re.search(r'报告|报送|申报', text):
            compliance["reporting_requirements"] = "提及报告义务"
        
        return compliance
    
    def assess_enforceability(self, text: str) -> Dict[str, Any]:
        """Assess contract enforceability"""
        enforceability = {
            "clarity_assessment": self.assess_clarity(text),
            "completeness_assessment": self.assess_completeness(text),
            "ambiguities_identified": self.identify_ambiguities(text),
            "enforceability_risk": "中等"
        }
        
        # Determine enforceability risk
        if len(enforceability["ambiguities_identified"]) >= 5:
            enforceability["enforceability_risk"] = "高"
        elif enforceability["completeness_assessment"] == "不完整":
            enforceability["enforceability_risk"] = "高"
        elif len(enforceability["ambiguities_identified"]) <= 2 and enforceability["completeness_assessment"] == "较完整":
            enforceability["enforceability_risk"] = "低"
        
        return enforceability
    
    def assess_clarity(self, text: str) -> str:
        """Assess contract language clarity"""
        ambiguity_indicators = ['可能', '或许', '大概', '适当', '合理', '另行协商', '届时确定']
        ambiguity_count = sum(1 for indicator in ambiguity_indicators if indicator in text)
        
        if ambiguity_count >= 5:
            return "存在较多模糊表述"
        elif ambiguity_count > 0:
            return "存在少量模糊表述"
        else:
            return "表述较为清晰"
    
    def assess_completeness(self, text: str) -> str:
        """Assess contract completeness"""
        key_terms = [
            '标的', '价格', '履行', '期限', '质量', '违约责任', 
            '争议解决', '生效', '当事人'
        ]
        
        covered_terms = sum(1 for term in key_terms if term in text)
        
        if covered_terms >= 8:
            return "较完整"
        elif covered_terms >= 5:
            return "基本完整"
        else:
            return "不完整"
    
    def identify_ambiguities(self, text: str) -> List[str]:
        """Identify potential ambiguities"""
        ambiguities = []
        lines = text.split('\n')
        
        ambiguity_patterns = [
            r'视情况而定',
            r'双方另行协商',
            r'届时确定',
            r'合理的.*?',
            r'适当的.*?',
            r'必要时.*?'
        ]
        
        for line in lines:
            for pattern in ambiguity_patterns:
                if re.search(pattern, line):
                    ambiguities.append(line.strip())
                    break
        
        return ambiguities
    
    def generate_contract_recommendations(self, text: str) -> List[Dict[str, str]]:
        """Generate contract improvement recommendations"""
        recommendations = []
        
        # Analyze for key missing elements
        if not re.search(r'违约责任', text):
            recommendations.append({
                "priority": "高",
                "recommendation": "补充明确的违约责任条款，包括违约情形及相应救济措施"
            })
        
        if not re.search(r'争议解决', text):
            recommendations.append({
                "priority": "高",
                "recommendation": "明确约定争议解决方式（诉讼或仲裁）及管辖机构"
            })
        
        if not re.search(r'生效日期', text):
            recommendations.append({
                "priority": "中",
                "recommendation": "明确合同生效条件和日期"
            })
        
        # Check for ambiguities
        if len(self.identify_ambiguities(text)) > 3:
            recommendations.append({
                "priority": "中",
                "recommendation": "修改模糊不清的表述，增强条款确定性"
            })
        
        # Check rights and obligations balance
        ro_analysis = self.analyze_rights_obligations(text)
        if "可能失衡" in [ro_analysis["rights_balance"], ro_analysis["obligations_balance"]]:
            recommendations.append({
                "priority": "中",
                "recommendation": "调整权利义务约定，确保双方权利义务基本对等"
            })
        
        return recommendations
    
    def get_llm_contract_analysis(self, text: str) -> str:
        """Get detailed contract analysis from LLM"""
        # This would be implemented with actual LLM integration
        prompt = f"""请对以下合同文本进行详细审查，重点关注合法性、公平性和可执行性：

{text}

请从以下方面提供分析：
1. 合同条款的完整性和明确性
2. 双方权利义务的平衡性
3. 潜在的法律风险和争议点
4. 与相关法律法规的符合性
5. 条款优化建议"""
        
        # In a real implementation, this would call an LLM API
        # For this example, we return a placeholder
        return "基于提供的合同文本，LLM分析显示该合同整体结构完整，但存在若干需要完善的条款..."
    
    def format_contract_analysis(self, analysis: Dict[str, Any]) -> str:
        """Format contract analysis for human readability"""
        # Implementation would format the analysis into a readable report
        return "合同审查报告：\n\n" + json.dumps(analysis, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    agent = ContractReviewAgent()