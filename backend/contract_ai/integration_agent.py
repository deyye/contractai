"""
整合智能体最终版 - 完全匹配前端数据格式
Integration Agent Final - Fully Matching Frontend Data Format
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from base_agent import BaseAgent

class RiskAggregator:
    """风险信息聚合器 - 确保不遗漏任何风险"""
    
    def __init__(self):
        self.all_risks: List[Dict[str, Any]] = []
        self.risk_categories: Dict[str, List[Dict]] = {}
        self.risk_deduplication: Set[str] = set()
        
    def add_risk(self, risk: Dict[str, Any], source: str):
        """添加风险（自动去重）"""
        risk_fingerprint = self._generate_risk_fingerprint(risk)
        
        if risk_fingerprint not in self.risk_deduplication:
            risk['source'] = source
            risk['added_at'] = datetime.now().isoformat()
            self.all_risks.append(risk)
            self.risk_deduplication.add(risk_fingerprint)
            
            # 按类别分组
            category = risk.get('category', '未分类风险')
            if category not in self.risk_categories:
                self.risk_categories[category] = []
            self.risk_categories[category].append(risk)
            
            return True
        return False
    
    def _generate_risk_fingerprint(self, risk: Dict[str, Any]) -> str:
        """生成风险指纹用于去重"""
        key_parts = [
            str(risk.get('category', '')),
            str(risk.get('description', ''))[:50],
            str(risk.get('severity', ''))
        ]
        return '|'.join(key_parts).lower()
    
    def get_all_risks(self) -> List[Dict[str, Any]]:
        """获取所有风险"""
        return self.all_risks
    
    def get_risks_by_severity(self) -> Dict[str, List[Dict]]:
        """按严重程度分组"""
        severity_groups = {
            '高': [],
            '中': [],
            '低': []
        }
        
        for risk in self.all_risks:
            severity = risk.get('severity', '中')
            if severity in severity_groups:
                severity_groups[severity].append(risk)
        
        return severity_groups

class IntegrationAgent(BaseAgent):
    """最终版整合智能体 - 输出完全匹配前端格式"""
    
    def __init__(self):
        system_prompt = """你是专业的合同分析结果整合智能体。
职责：完整保留所有风险信息，生成符合前端UI的结构化报告。"""
        
        super().__init__("IntegrationAgentFinal", system_prompt)
        self.risk_aggregator = RiskAggregator()
        
    def invoke(self, input: dict, config=None, **kwargs):
        """重写invoke方法"""
        results = input.get("results", {})
        return self.integrate_results(results)
    
    def integrate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """整合所有分析结果 - 完全匹配前端格式"""
        self.logger.info("="*60)
        self.logger.info("开始整合分析结果（前端格式）")
        self.logger.info("="*60)
        
        # 重置风险聚合器
        self.risk_aggregator = RiskAggregator()
        
        # 步骤1: 提取所有风险
        self._extract_all_risks(results)
        
        # 步骤2: 构建前端格式报告
        frontend_format_report = self._build_frontend_format_report(results)
        
        # 步骤3: 验证完整性
        self._verify_completeness(results, frontend_format_report)
        
        self.logger.info("="*60)
        self.logger.info(f"✅ 整合完成，共识别 {len(self.risk_aggregator.all_risks)} 个风险")
        self.logger.info("="*60)
        
        return frontend_format_report
    
    def _extract_all_risks(self, results: Dict[str, Any]):
        """从所有来源提取风险"""
        self.logger.info("🔍 第1步: 提取所有风险信息")
        
        # 从文档分析提取
        if results.get('document'):
            self._extract_risks_from_document(results['document'])
        
        # 从法律分析提取
        if results.get('legal'):
            self._extract_risks_from_legal(results['legal'])
        
        # 从商业分析提取
        if results.get('business'):
            self._extract_risks_from_business(results['business'])
        
        # 记录统计
        risks_by_severity = self.risk_aggregator.get_risks_by_severity()
        self.logger.info(f"  📊 总计: {len(self.risk_aggregator.all_risks)} 个风险")
        self.logger.info(f"     - 高风险: {len(risks_by_severity['高'])} 个")
        self.logger.info(f"     - 中风险: {len(risks_by_severity['中'])} 个")
        self.logger.info(f"     - 低风险: {len(risks_by_severity['低'])} 个")
    
    def _extract_risks_from_document(self, document_result: Any):
        """从文档分析中提取风险"""
        try:
            if isinstance(document_result, str):
                try:
                    data = json.loads(document_result)
                    self._process_document_data(data)
                except json.JSONDecodeError:
                    self._extract_risks_from_text(document_result, 'document')
            elif isinstance(document_result, dict):
                self._process_document_data(document_result)
        except Exception as e:
            self.logger.warning(f"⚠️ 文档风险提取异常: {e}")
    
    def _process_document_data(self, data: Dict[str, Any]):
        """处理文档数据"""
        analysis = data.get('analysis', {})
        
        if 'risk_assessment' in analysis:
            self._extract_structured_risks(
                analysis['risk_assessment'], 
                'document', 
                '文档分析'
            )
    
    def _extract_risks_from_legal(self, legal_result: Any):
        """从法律分析中提取风险 - 完整提取"""
        try:
            if isinstance(legal_result, str):
                try:
                    data = json.loads(legal_result)
                    self._process_legal_data(data)
                except json.JSONDecodeError:
                    self._extract_risks_from_text(legal_result, 'legal')
            elif isinstance(legal_result, dict):
                self._process_legal_data(legal_result)
        except Exception as e:
            self.logger.warning(f"⚠️ 法律风险提取异常: {e}")
    
    def _process_legal_data(self, data: Dict[str, Any]):
        """处理法律数据 - 多层次提取"""
        analysis = data.get('analysis', {})
        
        # 1. 风险评估
        if 'risk_assessment' in analysis:
            risk_assessment = analysis['risk_assessment']
            
            for high_risk in risk_assessment.get('high_risk', []):
                self.risk_aggregator.add_risk({
                    'category': high_risk.get('category', '法律高风险'),
                    'description': self._extract_risk_description(high_risk),
                    'severity': '高',
                    'details': high_risk.get('issues', []),
                    'score': high_risk.get('score', 0)
                }, 'legal')
            
            for medium_risk in risk_assessment.get('medium_risk', []):
                self.risk_aggregator.add_risk({
                    'category': medium_risk.get('category', '法律中风险'),
                    'description': self._extract_risk_description(medium_risk),
                    'severity': '中',
                    'details': medium_risk.get('issues', []),
                    'score': medium_risk.get('score', 0)
                }, 'legal')
            
            for low_risk in risk_assessment.get('low_risk', []):
                self.risk_aggregator.add_risk({
                    'category': low_risk.get('category', '法律低风险'),
                    'description': self._extract_risk_description(low_risk),
                    'severity': '低',
                    'details': low_risk.get('issues', []),
                    'score': low_risk.get('score', 0)
                }, 'legal')
        
        # 2. 合规检查
        if 'compliance_check' in analysis:
            compliance = analysis['compliance_check']
            for clause in compliance.get('required_clauses', []):
                if not clause.get('present', True):
                    self.risk_aggregator.add_risk({
                        'category': '合规风险',
                        'description': f"缺失必要条款: {clause.get('name', '未知')}",
                        'severity': '高' if clause.get('mandatory', False) else '中',
                        'recommendation': f"建议补充: {clause.get('description', '')}"
                    }, 'legal')
        
        # 3. 建议
        if 'recommendations' in analysis:
            for rec in analysis['recommendations']:
                if rec.get('priority') == '高':
                    self.risk_aggregator.add_risk({
                        'category': '需改进项',
                        'description': rec.get('recommendation', ''),
                        'severity': '高',
                        'type': rec.get('type', '')
                    }, 'legal')
    
    def _extract_risks_from_business(self, business_result: Any):
        """从商业分析中提取风险"""
        try:
            if isinstance(business_result, str):
                try:
                    data = json.loads(business_result)
                    self._process_business_data(data)
                except json.JSONDecodeError:
                    self._extract_risks_from_text(business_result, 'business')
            elif isinstance(business_result, dict):
                self._process_business_data(business_result)
        except Exception as e:
            self.logger.warning(f"⚠️ 商业风险提取异常: {e}")
    
    def _process_business_data(self, data: Dict[str, Any]):
        """处理商业数据"""
        analysis = data.get('analysis', {})
        
        if 'risk_assessment' in analysis:
            self._extract_structured_risks(
                analysis['risk_assessment'],
                'business',
                '商业分析'
            )
    
    def _extract_structured_risks(
        self,
        risk_data: Dict[str, Any],
        source: str,
        category_prefix: str
    ):
        """提取结构化风险"""
        for risk in risk_data.get('high_risk', []):
            self.risk_aggregator.add_risk({
                'category': f"{category_prefix}-{risk.get('category', '高')}",
                'description': self._extract_risk_description(risk),
                'severity': '高',
                'details': risk.get('issues', [])
            }, source)
        
        for risk in risk_data.get('medium_risk', []):
            self.risk_aggregator.add_risk({
                'category': f"{category_prefix}-{risk.get('category', '中')}",
                'description': self._extract_risk_description(risk),
                'severity': '中',
                'details': risk.get('issues', [])
            }, source)
        
        for risk in risk_data.get('low_risk', []):
            self.risk_aggregator.add_risk({
                'category': f"{category_prefix}-{risk.get('category', '低')}",
                'description': self._extract_risk_description(risk),
                'severity': '低',
                'details': risk.get('issues', [])
            }, source)
    
    def _extract_risks_from_text(self, text: str, source: str):
        """从文本中提取风险"""
        risk_keywords = [
            '风险', '问题', '缺失', '不符合', '违反',
            '未明确', '不完整', '不合理', '缺少', '遗漏'
        ]
        
        sentences = re.split(r'[。！？\n]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue
            
            if any(keyword in sentence for keyword in risk_keywords):
                severity = '中'
                if '严重' in sentence or '重大' in sentence:
                    severity = '高'
                elif '轻微' in sentence or '较小' in sentence:
                    severity = '低'
                
                self.risk_aggregator.add_risk({
                    'category': f'{source}识别风险',
                    'description': sentence,
                    'severity': severity
                }, source)
    
    def _extract_risk_description(self, risk: Dict[str, Any]) -> str:
        """提取风险描述"""
        for field in ['description', 'issue', 'category', 'message']:
            if field in risk and risk[field]:
                desc = str(risk[field])
                if 'issues' in risk and risk['issues']:
                    issues_text = '; '.join(str(i) for i in risk['issues'][:3])
                    desc = f"{desc}: {issues_text}"
                return desc
        return str(risk)
    
    def _build_frontend_format_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """构建完全匹配前端格式的报告"""
        self.logger.info("🔍 第2步: 构建前端格式报告")
        
        all_risks = self.risk_aggregator.get_all_risks()
        risks_by_severity = self.risk_aggregator.get_risks_by_severity()
        
        # 计算风险评分
        overall_risk_score = self._calculate_risk_score(risks_by_severity)
        
        # 提取关键发现
        key_findings = self._extract_key_findings(all_risks)
        
        # 提取重大风险
        critical_risks = self._extract_critical_risks(risks_by_severity['高'])
        
        # 生成建议
        recommendations = self._generate_recommendations(all_risks)
        
        # 格式化高风险项
        high_risk_items = self._format_high_risk_items(risks_by_severity['高'])
        
        # 前端格式报告
        report = {
            # 执行摘要 - 前端主要显示区域
            "executive_summary": {
                "overall_assessment": self._generate_overall_assessment(
                    overall_risk_score,
                    len(all_risks)
                ),
                "key_findings": key_findings[:10],  # 最多10条
                "critical_risks": critical_risks[:5],  # 最多5条重大风险
                "recommendations": recommendations[:8],  # 最多8条建议
                "decision_recommendation": self._generate_decision(overall_risk_score)
            },
            
            # 风险评估 - 前端用于显示评分和高风险项
            "risk_assessment": {
                "overall_risk_score": overall_risk_score,
                "risk_distribution": {
                    "high": len(risks_by_severity['高']),
                    "medium": len(risks_by_severity['中']),
                    "low": len(risks_by_severity['低'])
                },
                "high_risk_items": high_risk_items[:15],  # 最多15条高风险
                "mitigation_strategies": self._generate_mitigation_strategies(
                    risks_by_severity['高']
                )
            },
            
            # 详细分析 - 前端用于展开查看
            "detailed_analysis": {
                "document_analysis": self._summarize_analysis_component(
                    results.get('document')
                ),
                "legal_compliance_analysis": self._summarize_analysis_component(
                    results.get('legal')
                ),
                "business_analysis": self._summarize_analysis_component(
                    results.get('business')
                )
            },
            
            # 元数据 - 用于调试和追踪
            "metadata": {
                "report_time": datetime.now().isoformat(),
                "total_risks": len(all_risks),
                "sources_analyzed": list(results.keys()),
                "agent_version": "1.0.0"
            }
        }
        
        self.logger.info(f"  ✅ 报告生成完成")
        self.logger.info(f"     - 总体风险评分: {overall_risk_score}/10")
        self.logger.info(f"     - 关键发现: {len(key_findings)} 条")
        self.logger.info(f"     - 重大风险: {len(critical_risks)} 条")
        self.logger.info(f"     - 改进建议: {len(recommendations)} 条")
        
        return report
    
    def _calculate_risk_score(self, risks_by_severity: Dict[str, List]) -> int:
        """计算总体风险评分 (0-10)"""
        high_count = len(risks_by_severity['高'])
        medium_count = len(risks_by_severity['中'])
        low_count = len(risks_by_severity['低'])
        
        # 加权计算
        score = (high_count * 3) + (medium_count * 1.5) + (low_count * 0.5)
        
        # 归一化到0-10
        normalized_score = min(int(score / 2), 10)
        
        return normalized_score
    
    def _extract_key_findings(self, all_risks: List[Dict]) -> List[str]:
        """提取关键发现"""
        findings = []
        
        # 按严重程度排序
        sorted_risks = sorted(
            all_risks,
            key=lambda x: {'高': 3, '中': 2, '低': 1}.get(x.get('severity', '中'), 2),
            reverse=True
        )
        
        for risk in sorted_risks[:15]:
            finding = f"{risk.get('category', '风险')}: {risk.get('description', '')}"
            if len(finding) > 100:
                finding = finding[:97] + "..."
            findings.append(finding)
        
        return findings
    
    def _extract_critical_risks(self, high_risks: List[Dict]) -> List[str]:
        """提取重大风险（简短描述）"""
        critical = []
        
        for risk in high_risks[:10]:
            desc = risk.get('description', '')
            # 截取前50字符作为简要描述
            if len(desc) > 50:
                desc = desc[:47] + "..."
            critical.append(f"[{risk.get('category', '高风险')}] {desc}")
        
        return critical
    
    def _generate_recommendations(self, all_risks: List[Dict]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 按严重程度分组
        high_risks = [r for r in all_risks if r.get('severity') == '高']
        medium_risks = [r for r in all_risks if r.get('severity') == '中']
        
        # 高风险建议
        for risk in high_risks[:5]:
            if 'recommendation' in risk:
                recommendations.append(risk['recommendation'])
            else:
                recommendations.append(
                    f"针对{risk.get('category', '')}问题，建议: {risk.get('description', '')[:50]}"
                )
        
        # 中风险建议
        for risk in medium_risks[:3]:
            if 'recommendation' in risk:
                recommendations.append(risk['recommendation'])
            else:
                recommendations.append(
                    f"建议关注{risk.get('category', '')}相关事项"
                )
        
        return recommendations
    
    def _generate_overall_assessment(self, risk_score: int, total_risks: int) -> str:
        """生成总体评估描述"""
        if risk_score >= 8:
            return f"合同存在严重风险隐患（共发现{total_risks}个风险点），不建议在未修改的情况下签署。建议立即修订高风险条款后再进行审核。"
        elif risk_score >= 6:
            return f"合同存在较多风险点（共发现{total_risks}个风险点），建议在充分评估并修改关键条款后谨慎签署。"
        elif risk_score >= 4:
            return f"合同整体可接受但存在一些需要关注的风险点（共发现{total_risks}个），建议在澄清相关条款后签署。"
        else:
            return f"合同风险整体可控（共发现{total_risks}个低风险点），可以在常规审核流程后签署。"
    
    def _generate_decision(self, risk_score: int) -> str:
        """生成决策建议"""
        if risk_score >= 8:
            return "🔴 不建议签署 - 需要重大修改"
        elif risk_score >= 6:
            return "🟡 谨慎签署 - 需要修改关键条款"
        elif risk_score >= 4:
            return "🟡 可以签署 - 建议澄清部分条款"
        else:
            return "🟢 可以签署 - 风险可控"
    
    def _format_high_risk_items(self, high_risks: List[Dict]) -> List[Dict]:
        """格式化高风险项为前端需要的格式"""
        formatted = []
        
        for risk in high_risks:
            formatted.append({
                "category": risk.get('category', '未分类'),
                "severity": risk.get('severity', '高'),
                "description": risk.get('description', ''),
                "source": risk.get('source', 'unknown')
            })
        
        return formatted
    
    def _generate_mitigation_strategies(self, high_risks: List[Dict]) -> List[str]:
        """生成缓解策略"""
        strategies = []
        
        for risk in high_risks[:5]:
            category = risk.get('category', '')
            if '合规' in category:
                strategies.append("补充缺失的合规性条款，确保符合相关法律法规要求")
            elif '财务' in category or '支付' in category:
                strategies.append("重新协商支付条款，确保现金流安全和付款节奏合理")
            elif '违约' in category:
                strategies.append("平衡双方违约责任，避免责任不对等情况")
            else:
                strategies.append(f"针对{category}风险制定专项应对措施")
        
        return strategies
    
    def _summarize_analysis_component(self, component_result: Any) -> Dict[str, Any]:
        """汇总分析组件结果"""
        if not component_result:
            return {"status": "not_available"}
        
        summary = {"status": "completed"}
        
        if isinstance(component_result, dict):
            if 'analysis' in component_result:
                summary['has_analysis'] = True
                if 'risk_assessment' in component_result.get('analysis', {}):
                    risk_data = component_result['analysis']['risk_assessment']
                    summary['risk_count'] = {
                        'high': len(risk_data.get('high_risk', [])),
                        'medium': len(risk_data.get('medium_risk', [])),
                        'low': len(risk_data.get('low_risk', []))
                    }
        elif isinstance(component_result, str):
            summary['content_length'] = len(component_result)
            summary['preview'] = component_result[:200]
        
        return summary
    
    def _verify_completeness(
        self,
        original_results: Dict[str, Any],
        integrated_report: Dict[str, Any]
    ):
        """验证完整性"""
        self.logger.info("🔍 第3步: 验证数据完整性")
        
        # 验证关键字段
        required_fields = [
            'executive_summary',
            'risk_assessment',
            'detailed_analysis'
        ]
        
        for field in required_fields:
            if field not in integrated_report:
                self.logger.error(f"❌ 缺少必要字段: {field}")
            else:
                self.logger.info(f"  ✅ {field}: 已生成")
        
        # 验证数据
        total_risks = integrated_report['metadata']['total_risks']
        if total_risks == 0:
            self.logger.warning("⚠️ 未识别到任何风险")
        else:
            self.logger.info(f"  ✅ 共识别 {total_risks} 个风险")

if __name__ == "__main__":
    print("IntegrationAgentFinal - 测试模式")
    
    agent = IntegrationAgentFinal()
    
    # 模拟输入
    test_results = {
        'legal': {
            'analysis': {
                'risk_assessment': {
                    'high_risk': [
                        {
                            'category': '合规风险',
                            'issues': ['缺少质疑条款', '评审标准不明确'],
                            'score': 9
                        }
                    ]
                }
            }
        }
    }
    
    result = agent.integrate_results(test_results)
    
    print("\n" + "="*60)
    print("前端格式报告:")
    print(json.dumps(result, ensure_ascii=False, indent=2))