import re
import json
from typing import Dict, List, Any, Optional, Tuple
from base_agent import BaseAgent

class HighlightAgent(BaseAgent):
    """Agent specialized in highlighting key points and important clauses"""
    
    def __init__(self):
        system_prompt = """你是专门进行重点标注和高亮的智能体。你的职责包括：

1. 识别合同中的关键条款和重要信息
2. 标注潜在风险点和注意事项
3. 突出显示重要的财务条款
4. 高亮法律责任和义务条款
5. 标记时间期限和截止日期
6. 注释专业术语和复杂条款

重点标注类别：
- 🔴 高风险条款：法律风险、财务风险、履行风险
- 🟡 中等关注：重要条款、特殊约定、限制条件
- 🔵 重要信息：当事人信息、金额、日期、期限
- 🟢 有利条款：权益保护、优惠条件、灵活安排
- ⚠️ 注意事项：模糊表述、争议可能、合规要求

你的标注应该：
- 准确识别关键内容
- 使用统一的标注体系
- 提供简明的注释说明
- 便于用户快速理解重点
- 支持后续的决策分析"""

        super().__init__(agent_name="HighlightAgent", system_prompt=system_prompt)
        self.highlight_categories = self.initialize_highlight_categories()
    
    def initialize_highlight_categories(self) -> Dict[str, Dict[str, Any]]:
        """Initialize highlight categories and their criteria"""
        return {
            "高风险条款": {
                "color": "🔴",
                "keywords": ["违约金", "赔偿", "终止", "解除", "免责", "不可撤销", "无条件"],
                "patterns": [
                    r"违约金.*?[\d,]+",
                    r"不承担.*?责任",
                    r"单方.*?解除",
                    r"无条件.*?接受"
                ],
                "priority": 1
            },
            "财务条款": {
                "color": "🔵",
                "keywords": ["金额", "费用", "价格", "支付", "预付", "尾款", "保证金"],
                "patterns": [
                    r"[￥$¥]\s*[\d,]+(?:\.\d{2})?",
                    r"[\d,]+(?:\.\d{2})?\s*[元万千万亿]",
                    r"总价.*?[\d,]+",
                    r"预付.*?[\d,]+"
                ],
                "priority": 2
            },
            "时间条款": {
                "color": "🟡",
                "keywords": ["期限", "截止", "到期", "完成时间", "交付时间", "生效日期"],
                "patterns": [
                    r"\d{4}年\d{1,2}月\d{1,2}日",
                    r"\d{1,2}/\d{1,2}/\d{4}",
                    r"\d+天内",
                    r"\d+个工作日",
                    r"\d+个月内"
                ],
                "priority": 3
            },
            "权利义务": {
                "color": "🟢",
                "keywords": ["权利", "义务", "责任", "保证", "承诺", "声明"],
                "patterns": [
                    r"甲方.*?权利",
                    r"乙方.*?义务",
                    r"有权.*?要求",
                    r"应当.*?履行"
                ],
                "priority": 4
            },
            "争议条款": {
                "color": "⚠️",
                "keywords": ["争议", "纠纷", "仲裁", "诉讼", "管辖", "适用法律"],
                "patterns": [
                    r"争议.*?解决",
                    r"仲裁.*?委员会",
                    r"管辖.*?法院",
                    r"适用.*?法律"
                ],
                "priority": 5
            },
            "特殊条款": {
                "color": "🟡",
                "keywords": ["保密", "不可抗力", "知识产权", "违约责任", "终止条件"],
                "patterns": [
                    r"保密.*?义务",
                    r"不可抗力.*?事件",
                    r"知识产权.*?归属",
                    r"提前.*?终止"
                ],
                "priority": 6
            }
        }
    
    def process_text_message(self, message):
        """Process highlighting requests"""
        user_text = message
        self.logger.info("Processing highlight analysis request")
        
        try:
            # Extract task and content
            task_info = self.extract_task_info(user_text)
            document_content = task_info.get("content", user_text)
            
            # Perform highlighting analysis
            highlight_analysis = self.perform_highlight_analysis(document_content)
            
            # Format response
            response_text = self.format_highlight_results(highlight_analysis)
            
            return {
                "agent": "HighlightAgent",
                "status": "success",
                "analysis": highlight_analysis,
                "response_text": response_text,
                "timestamp": self._get_current_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Error in highlight analysis: {str(e)}")
            return {
                "agent": "BusinessAgent",
                "status": "error",
                "message": f"重点标注过程中发生错误：{str(e)}",
                "response_text": "重点标注过程中发生错误。",
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
    
    def perform_highlight_analysis(self, document_text: str) -> Dict[str, Any]:
        """Perform comprehensive highlighting analysis"""
        analysis = {
            "highlighted_content": self.create_highlighted_content(document_text),
            "key_points": self.extract_key_points(document_text),
            "risk_highlights": self.identify_risk_highlights(document_text),
            "important_clauses": self.identify_important_clauses(document_text),
            "financial_highlights": self.extract_financial_highlights(document_text),
            "time_sensitive_items": self.extract_time_sensitive_items(document_text),
            "annotation_summary": self.create_annotation_summary(document_text),
            "highlight_statistics": {}
        }
        
        # Calculate highlight statistics
        analysis["highlight_statistics"] = self.calculate_highlight_statistics(analysis)
        
        # Get detailed analysis from LLM
        llm_analysis = self.get_llm_highlight_analysis(document_text)
        analysis["detailed_analysis"] = llm_analysis
        
        return analysis
    
    def create_highlighted_content(self, text: str) -> str:
        """Create highlighted version of the document"""
        highlighted_text = text
        highlight_count = 0
        
        # Process each highlight category
        for category_name, category_info in self.highlight_categories.items():
            color = category_info["color"]
            keywords = category_info["keywords"]
            patterns = category_info["patterns"]
            
            # Highlight keywords
            for keyword in keywords:
                # Find keyword occurrences in context
                pattern = rf'([^。；！？]*{keyword}[^。；！？]*[。；！？]?)'
                
                def highlight_match(match):
                    nonlocal highlight_count
                    highlight_count += 1
                    return f"{color} **[{category_name}]** {match.group(1)}"
                
                highlighted_text = re.sub(pattern, highlight_match, highlighted_text)
            
            # Highlight specific patterns
            for pattern in patterns:
                def pattern_highlight(match):
                    nonlocal highlight_count
                    highlight_count += 1
                    return f"{color} **[{category_name}]** {match.group(0)}"
                
                highlighted_text = re.sub(pattern, pattern_highlight, highlighted_text)
        
        return highlighted_text
    
    def extract_key_points(self, text: str) -> List[Dict[str, Any]]:
        """Extract key points from the document"""
        key_points = []
        lines = text.split('\n')
        
        # Define importance indicators
        importance_keywords = {
            "关键信息": ["合同编号", "合同金额", "签署日期", "生效日期", "到期日期"],
            "重要条款": ["违约责任", "争议解决", "知识产权", "保密条款", "终止条件"],
            "财务条款": ["支付方式", "付款期限", "违约金", "保证金", "价格调整"],
            "履行条款": ["交付时间", "质量标准", "验收标准", "服务要求", "维护义务"]
        }
        
        for category, keywords in importance_keywords.items():
            for keyword in keywords:
                for i, line in enumerate(lines):
                    if keyword in line:
                        key_points.append({
                            "category": category,
                            "keyword": keyword,
                            "line_number": i + 1,
                            "content": line.strip(),
                            "importance": self.calculate_importance_score(line, keyword)
                        })
        
        # Sort by importance score
        key_points.sort(key=lambda x: x["importance"], reverse=True)
        
        return key_points[:20]  # Return top 20 key points
    
    def calculate_importance_score(self, text: str, keyword: str) -> int:
        """Calculate importance score for a text segment"""
        score = 5  # Base score
        
        # Increase score for financial amounts
        if re.search(r'[\d,]+[元万千万亿]', text):
            score += 3
        
        # Increase score for legal terms
        legal_terms = ["违约", "责任", "赔偿", "争议", "终止", "解除"]
        for term in legal_terms:
            if term in text:
                score += 2
                break
        
        # Increase score for time-sensitive content
        if re.search(r'\d+天|\d+月|\d+年|\d{4}-\d{2}-\d{2}', text):
            score += 2
        
        # Increase score for specific numbers or percentages
        if re.search(r'\d+%|\d+倍', text):
            score += 1
        
        # Decrease score for very short or very long lines
        if len(text) < 20 or len(text) > 200:
            score -= 1
        
        return max(score, 1)
    
    def identify_risk_highlights(self, text: str) -> List[Dict[str, Any]]:
        """Identify and highlight risk-related content"""
        risk_highlights = []
        
        # Define risk patterns and their severity
        risk_patterns = {
            "高风险": [
                (r"不承担任何责任", "过度免责条款"),
                (r"单方面.*?决定", "单方决定权"),
                (r"无条件.*?同意", "无条件接受"),
                (r"违约金.*?100%", "过高违约金"),
                (r"立即.*?终止", "即时终止风险")
            ],
            "中风险": [
                (r"市场价格.*?调整", "价格波动风险"),
                (r"不可抗力", "不可抗力条款"),
                (r"提前.*?通知", "短期通知要求"),
                (r"第三方.*?责任", "第三方责任"),
                (r"保密.*?期限", "长期保密义务")
            ],
            "低风险": [
                (r"协商.*?解决", "协商解决机制"),
                (r"合理.*?费用", "费用承担"),
                (r"双方.*?同意", "双方同意条款"),
                (r"按照.*?标准", "标准化要求")
            ]
        }
        
        for risk_level, patterns in risk_patterns.items():
            for pattern, description in patterns:
                matches = list(re.finditer(pattern, text))
                for match in matches:
                    # Get surrounding context
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end]
                    
                    risk_highlights.append({
                        "risk_level": risk_level,
                        "description": description,
                        "matched_text": match.group(0),
                        "context": context,
                        "position": match.start(),
                        "severity_score": self.calculate_risk_severity(risk_level, description)
                    })
        
        # Sort by severity score
        risk_highlights.sort(key=lambda x: x["severity_score"], reverse=True)
        
        return risk_highlights
    
    def calculate_risk_severity(self, risk_level: str, description: str) -> int:
        """Calculate risk severity score"""
        base_scores = {"高风险": 9, "中风险": 6, "低风险": 3}
        score = base_scores.get(risk_level, 5)
        
        # Adjust based on description
        if "免责" in description:
            score += 2
        elif "违约金" in description:
            score += 2
        elif "终止" in description:
            score += 1
        
        return min(score, 10)
    
    def identify_important_clauses(self, text: str) -> List[Dict[str, Any]]:
        """Identify important clauses that need attention"""
        important_clauses = []
        lines = text.split('\n')
        
        # Define clause importance indicators
        clause_indicators = {
            "核心条款": [
                "合同标的", "服务内容", "产品规格", "工作范围", "项目要求"
            ],
            "财务条款": [
                "合同价款", "支付方式", "付款期限", "费用承担", "价格调整"
            ],
            "履行条款": [
                "履行期限", "交付条件", "验收标准", "质量要求", "服务水平"
            ],
            "责任条款": [
                "违约责任", "赔偿责任", "免责条件", "责任限制", "连带责任"
            ],
            "终止条款": [
                "合同期限", "终止条件", "解除权", "提前终止", "合同续期"
            ]
        }
        
        for clause_type, indicators in clause_indicators.items():
            for indicator in indicators:
                for i, line in enumerate(lines):
                    if indicator in line and len(line.strip()) > 10:
                        importance_score = self.calculate_clause_importance(line, clause_type)
                        
                        important_clauses.append({
                            "clause_type": clause_type,
                            "indicator": indicator,
                            "line_number": i + 1,
                            "content": line.strip(),
                            "importance_score": importance_score,
                            "requires_attention": importance_score >= 7
                        })
        
        # Remove duplicates and sort
        seen_lines = set()
        unique_clauses = []
        for clause in important_clauses:
            if clause["line_number"] not in seen_lines:
                unique_clauses.append(clause)
                seen_lines.add(clause["line_number"])
        
        unique_clauses.sort(key=lambda x: x["importance_score"], reverse=True)
        
        return unique_clauses[:15]  # Return top 15 important clauses
    
    def calculate_clause_importance(self, text: str, clause_type: str) -> int:
        """Calculate clause importance score"""
        score = 5  # Base score
        
        # Type-specific scoring
        type_scores = {
            "核心条款": 8,
            "财务条款": 9,
            "履行条款": 7,
            "责任条款": 8,
            "终止条款": 6
        }
        
        score = type_scores.get(clause_type, 5)
        
        # Content-based adjustments
        if re.search(r'必须|应当|不得|禁止', text):
            score += 1
        
        if re.search(r'[\d,]+[元万千万亿]', text):
            score += 2
        
        if re.search(r'违约|赔偿|损失', text):
            score += 2
        
        if re.search(r'立即|马上|当日|次日', text):
            score += 1
        
        return min(score, 10)
    
    def extract_financial_highlights(self, text: str) -> List[Dict[str, Any]]:
        """Extract and highlight financial information"""
        financial_highlights = []
        
        # Financial patterns to highlight
        financial_patterns = [
            (r'[￥$¥]\s*[\d,]+(?:\.\d{2})?', "货币金额"),
            (r'[\d,]+(?:\.\d{2})?\s*[元万千万亿]', "中文金额"),
            (r'总价.*?([\d,]+)', "总价条款"),
            (r'单价.*?([\d,]+)', "单价条款"),
            (r'预付.*?([\d,]+)', "预付款"),
            (r'保证金.*?([\d,]+)', "保证金"),
            (r'违约金.*?([\d,]+)', "违约金"),
            (r'(\d+)%.*?折扣', "折扣比例"),
            (r'利率.*?(\d+\.?\d*)%', "利率条款")
        ]
        
        for pattern, description in financial_patterns:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                # Get surrounding context
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end]
                
                financial_highlights.append({
                    "type": description,
                    "amount": match.group(0),
                    "context": context,
                    "position": match.start(),
                    "priority": self.calculate_financial_priority(description, match.group(0))
                })
        
        # Sort by priority
        financial_highlights.sort(key=lambda x: x["priority"], reverse=True)
        
        return financial_highlights
    
    def calculate_financial_priority(self, description: str, amount: str) -> int:
        """Calculate financial highlight priority"""
        priority = 5  # Base priority
        
        # Higher priority for larger amounts
        amount_value = self.extract_numeric_value(amount)
        if amount_value:
            if amount_value >= 1000000:  # 100万以上
                priority += 3
            elif amount_value >= 100000:  # 10万以上
                priority += 2
            elif amount_value >= 10000:   # 1万以上
                priority += 1
        
        # Type-specific priorities
        type_priorities = {
            "总价条款": 9,
            "违约金": 8,
            "保证金": 7,
            "预付款": 7,
            "单价条款": 6,
            "货币金额": 5,
            "中文金额": 5,
            "折扣比例": 4,
            "利率条款": 6
        }
        
        type_priority = type_priorities.get(description, 5)
        priority = max(priority, type_priority)
        
        return min(priority, 10)
    
    def extract_numeric_value(self, amount_str: str) -> Optional[float]:
        """Extract numeric value from amount string"""
        try:
            # Remove currency symbols and spaces
            cleaned = re.sub(r'[￥$¥\s,]', '', amount_str)
            
            # Handle Chinese units
            if '万' in cleaned:
                number = re.search(r'([\d.]+)万', cleaned)
                if number:
                    return float(number.group(1)) * 10000
            elif '千' in cleaned:
                number = re.search(r'([\d.]+)千', cleaned)
                if number:
                    return float(number.group(1)) * 1000
            elif '亿' in cleaned:
                number = re.search(r'([\d.]+)亿', cleaned)
                if number:
                    return float(number.group(1)) * 100000000
            
            # Extract regular numbers
            number = re.search(r'[\d.]+', cleaned)
            if number:
                return float(number.group(0))
            
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def extract_time_sensitive_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract time-sensitive items and deadlines"""
        time_items = []
        
        # Time patterns to highlight
        time_patterns = [
            (r'\d{4}年\d{1,2}月\d{1,2}日', "具体日期"),
            (r'\d{1,2}/\d{1,2}/\d{4}', "日期格式"),
            (r'(\d+)天内', "天数期限"),
            (r'(\d+)个工作日', "工作日期限"),
            (r'(\d+)个月内', "月份期限"),
            (r'(\d+)年内', "年限期限"),
            (r'截止.*?(\d{4}年\d{1,2}月\d{1,2}日)', "截止日期"),
            (r'不超过.*?(\d+天)', "最长期限"),
            (r'自.*?之日起.*?(\d+)', "起算期限")
        ]
        
        for pattern, description in time_patterns:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                # Get surrounding context
                start = max(0, match.start() - 40)
                end = min(len(text), match.end() + 40)
                context = text[start:end]
                
                time_items.append({
                    "type": description,
                    "time_expression": match.group(0),
                    "context": context,
                    "position": match.start(),
                    "urgency": self.calculate_time_urgency(description, match.group(0))
                })
        
        # Sort by urgency
        time_items.sort(key=lambda x: x["urgency"], reverse=True)
        
        return time_items
    
    def calculate_time_urgency(self, description: str, time_expr: str) -> int:
        """Calculate urgency score for time-sensitive items"""
        urgency = 5  # Base urgency
        
        # Extract time value
        time_value = re.search(r'\d+', time_expr)
        if time_value:
            value = int(time_value.group(0))
            
            if "天" in time_expr:
                if value <= 7:
                    urgency += 4
                elif value <= 30:
                    urgency += 2
                elif value <= 90:
                    urgency += 1
            elif "工作日" in time_expr:
                if value <= 5:
                    urgency += 4
                elif value <= 20:
                    urgency += 2
            elif "月" in time_expr:
                if value <= 1:
                    urgency += 3
                elif value <= 6:
                    urgency += 1
        
        # Type-specific urgency
        if "截止" in description:
            urgency += 3
        elif "最长" in description:
            urgency += 2
        
        return min(urgency, 10)
    
    def create_annotation_summary(self, text: str) -> Dict[str, Any]:
        """Create summary of all annotations"""
        summary = {
            "total_highlights": 0,
            "category_counts": {},
            "priority_distribution": {"高": 0, "中": 0, "低": 0},
            "key_attention_areas": [],
            "recommended_actions": []
        }
        
        # Count highlights by category
        for category_name, category_info in self.highlight_categories.items():
            keywords = category_info["keywords"]
            patterns = category_info["patterns"]
            
            count = 0
            for keyword in keywords:
                count += len(re.findall(keyword, text))
            
            for pattern in patterns:
                count += len(re.findall(pattern, text))
            
            if count > 0:
                summary["category_counts"][category_name] = count
                summary["total_highlights"] += count
        
        # Identify key attention areas
        for category, count in summary["category_counts"].items():
            if count >= 3:
                summary["key_attention_areas"].append({
                    "area": category,
                    "mentions": count,
                    "recommendation": self.get_category_recommendation(category)
                })
        
        # Generate recommended actions
        if summary["category_counts"].get("高风险条款", 0) > 0:
            summary["recommended_actions"].append("重点关注高风险条款，建议法务审核")
        
        if summary["category_counts"].get("财务条款", 0) >= 3:
            summary["recommended_actions"].append("财务条款较多，建议财务部门详细审核")
        
        if summary["category_counts"].get("时间条款", 0) >= 2:
            summary["recommended_actions"].append("注意时间期限要求，建议制定履行计划")
        
        return summary
    
    def get_category_recommendation(self, category: str) -> str:
        """Get recommendation for specific category"""
        recommendations = {
            "高风险条款": "建议详细评估风险影响，必要时寻求法律建议",
            "财务条款": "建议财务部门审核金额和支付条件的合理性",
            "时间条款": "建议制定详细的时间计划，确保按期履行",
            "权利义务": "建议确认双方权利义务的平衡性和可执行性",
            "争议条款": "建议评估争议解决机制的适用性和有效性",
            "特殊条款": "建议重点关注特殊约定，确保理解和执行"
        }
        
        return recommendations.get(category, "建议重点关注此类条款")
    
    def calculate_highlight_statistics(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate highlight statistics"""
        stats = {
            "total_key_points": len(analysis.get("key_points", [])),
            "risk_highlights_count": len(analysis.get("risk_highlights", [])),
            "important_clauses_count": len(analysis.get("important_clauses", [])),
            "financial_highlights_count": len(analysis.get("financial_highlights", [])),
            "time_sensitive_count": len(analysis.get("time_sensitive_items", [])),
            "high_priority_items": 0,
            "attention_score": 0
        }
        
        # Count high priority items
        for item in analysis.get("risk_highlights", []):
            if item.get("severity_score", 0) >= 8:
                stats["high_priority_items"] += 1
        
        for item in analysis.get("important_clauses", []):
            if item.get("importance_score", 0) >= 8:
                stats["high_priority_items"] += 1
        
        # Calculate attention score
        base_score = 5
        if stats["risk_highlights_count"] > 5:
            base_score += 2
        if stats["financial_highlights_count"] > 3:
            base_score += 1
        if stats["high_priority_items"] > 3:
            base_score += 2
        
        stats["attention_score"] = min(base_score, 10)
        
        return stats
    
    def get_llm_highlight_analysis(self, text: str) -> str:
        """Get detailed highlight analysis from LLM"""
        analysis_prompt = f"""
        请对以下合同文本进行重点标注分析：
        
        合同文本：{text[:1500]}...
        
        请识别并分析：
        1. 最重要的关键条款和信息点
        2. 需要特别注意的风险点
        3. 重要的财务条款和金额信息
        4. 时间敏感的条款和期限要求
        5. 可能存在争议的模糊表述
        6. 对合同履行至关重要的条款
        
        请提供具体的标注建议和注意事项。
        """
        
        return self.call_llm(analysis_prompt)
    
    def format_highlight_results(self, analysis: Dict[str, Any]) -> str:
        """Format highlight analysis results for output"""
        output = "=== 重点标注分析报告 ===\n\n"
        
        # Statistics overview
        stats = analysis.get("highlight_statistics", {})
        output += f"总体关注度：{stats.get('attention_score', 0)}/10\n"
        output += f"关键点总数：{stats.get('total_key_points', 0)}\n"
        output += f"高优先级项目：{stats.get('high_priority_items', 0)}\n\n"
        
        # Risk highlights
        risk_highlights = analysis.get("risk_highlights", [])
        if risk_highlights:
            output += "--- 🔴 风险标注 ---\n"
            for i, risk in enumerate(risk_highlights[:5], 1):
                output += f"{i}. [{risk['risk_level']}] {risk['description']}\n"
                output += f"   内容：{risk['matched_text']}\n"
                output += f"   风险评分：{risk['severity_score']}/10\n\n"
        
        # Financial highlights
        financial_highlights = analysis.get("financial_highlights", [])
        if financial_highlights:
            output += "--- 💰 财务标注 ---\n"
            for i, financial in enumerate(financial_highlights[:5], 1):
                output += f"{i}. {financial['type']}：{financial['amount']}\n"
                output += f"   优先级：{financial['priority']}/10\n\n"
        
        # Time-sensitive items
        time_items = analysis.get("time_sensitive_items", [])
        if time_items:
            output += "--- ⏰ 时间标注 ---\n"
            for i, time_item in enumerate(time_items[:5], 1):
                output += f"{i}. {time_item['type']}：{time_item['time_expression']}\n"
                output += f"   紧急度：{time_item['urgency']}/10\n\n"
        
        # Important clauses
        important_clauses = analysis.get("important_clauses", [])
        if important_clauses:
            output += "--- 📋 重要条款 ---\n"
            for i, clause in enumerate(important_clauses[:5], 1):
                output += f"{i}. [{clause['clause_type']}] {clause['indicator']}\n"
                output += f"   重要性：{clause['importance_score']}/10\n"
                if clause.get('requires_attention'):
                    output += f"   ⚠️ 需要特别注意\n"
                output += "\n"
        
        # Key points summary
        key_points = analysis.get("key_points", [])
        if key_points:
            output += "--- 🔑 关键信息点 ---\n"
            categories = {}
            for point in key_points[:10]:
                category = point['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(point)
            
            for category, points in categories.items():
                output += f"\n{category}：\n"
                for point in points[:3]:  # Show top 3 per category
                    output += f"  • {point['keyword']} (重要性: {point['importance']}/10)\n"
        
        # Annotation summary
        annotation_summary = analysis.get("annotation_summary", {})
        if annotation_summary:
            output += "\n--- 📊 标注统计 ---\n"
            
            category_counts = annotation_summary.get("category_counts", {})
            for category, count in category_counts.items():
                output += f"{category}：{count}处\n"
            
            key_areas = annotation_summary.get("key_attention_areas", [])
            if key_areas:
                output += "\n重点关注领域：\n"
                for area in key_areas:
                    output += f"  • {area['area']} ({area['mentions']}处) - {area['recommendation']}\n"
            
            actions = annotation_summary.get("recommended_actions", [])
            if actions:
                output += "\n建议行动：\n"
                for i, action in enumerate(actions, 1):
                    output += f"  {i}. {action}\n"
        
        # Detailed analysis
        detailed_analysis = analysis.get("detailed_analysis", "")
        if detailed_analysis:
            output += "\n--- 📝 详细标注分析 ---\n"
            output += detailed_analysis
        
        return output

if __name__ == "__main__":
    agent = HighlightAgent()