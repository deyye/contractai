import React from 'react';
import { Card, Tag, Collapse, Typography, Empty, List, Alert, Divider } from 'antd';
import { WarningOutlined, BugOutlined, SafetyCertificateOutlined } from '@ant-design/icons';

const { Panel } = Collapse;
const { Text, Title, Paragraph } = Typography;

interface RiskPanelProps {
  analysisData: any;
  loading: boolean;
}

const RiskPanel: React.FC<RiskPanelProps> = ({ analysisData, loading }) => {
  // 1. 加载状态
  if (loading) {
    return <Card loading={true} title="AI 正在深度审查合同..." style={{ height: '100%', minHeight: '400px' }} />;
  }

  // 2. 空状态（初始）
  if (!analysisData) {
    return (
      <Card title="审查报告" style={{ height: '100%' }}>
        <Empty 
          image={Empty.PRESENTED_IMAGE_SIMPLE} 
          description="请上传文件并点击“开始智能审查”" 
        />
      </Card>
    );
  }

  // 3. 错误状态处理 (后端 Agent 返回了 error 状态)
  if (analysisData.status === 'error') {
    return (
      <Card title="审查失败" style={{ height: '100%' }}>
        <Alert
          message="智能体执行出错"
          description={analysisData.message || "未知错误，请检查后端日志"}
          type="error"
          showIcon
        />
      </Card>
    );
  }

  // 4. 数据结构校验与降级处理
  // 尝试获取关键字段，如果不存在则给默认空对象
  const executiveSummary = analysisData.executive_summary || {};
  const riskAssessment = analysisData.risk_assessment || {};
  const detailedAnalysis = analysisData.detailed_analysis || {};

  // 检查是否为有效报告（至少应该有总体评估或风险评分）
  const isValidReport = executiveSummary.overall_assessment || riskAssessment.overall_risk_score !== undefined;

  // 如果数据结构完全不对，显示调试视图
  if (!isValidReport) {
    return (
      <Card title={<><BugOutlined /> 数据解析异常</>} style={{ height: '100%', overflow: 'auto' }}>
        <Alert message="后端返回的数据结构不符合预期" type="warning" showIcon style={{ marginBottom: 16 }} />
        <Paragraph>原始数据快照：</Paragraph>
        <div style={{ background: '#f5f5f5', padding: 10, borderRadius: 4, maxHeight: 400, overflow: 'auto' }}>
          <pre style={{ fontSize: 12 }}>{JSON.stringify(analysisData, null, 2)}</pre>
        </div>
      </Card>
    );
  }

  // --- 数据提取 ---
  const criticalRisks = executiveSummary.critical_risks || [];
  const riskScore = riskAssessment.overall_risk_score || 0;
  const highRiskItems = riskAssessment.high_risk_items || [];
  const recommendations = executiveSummary.recommendations || [];

  // 风险等级颜色映射
  const getScoreColor = (score: number) => {
    if (score >= 7) return '#ff4d4f'; // 红 (高风险)
    if (score >= 4) return '#faad14'; // 黄 (中风险)
    return '#52c41a'; // 绿 (低风险)
  };

  const getScoreLabel = (score: number) => {
    if (score >= 7) return '高风险';
    if (score >= 4) return '中风险';
    return '低风险';
  };

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '0 4px' }}>
      {/* 1. 总体评分卡 */}
      <Card style={{ marginBottom: 16, borderTop: `4px solid ${getScoreColor(riskScore)}` }} bodyStyle={{ padding: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ flex: 1, paddingRight: 16 }}>
            <Title level={5} style={{ margin: 0, marginBottom: 8 }}>综合评估</Title>
            <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: '13px' }}>
              {executiveSummary.overall_assessment || "暂无评估内容"}
            </Paragraph>
          </div>
          <div style={{ textAlign: 'center', minWidth: 80 }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: getScoreColor(riskScore), lineHeight: 1 }}>
              {riskScore}/10
            </div>
            <Tag color={getScoreColor(riskScore)} style={{ marginTop: 8, marginRight: 0 }}>
              {getScoreLabel(riskScore)}
            </Tag>
          </div>
        </div>
      </Card>

      {/* 2. 重大风险警告 */}
      {criticalRisks.length > 0 ? (
        <Card 
          title={<span style={{ color: '#ff4d4f' }}><WarningOutlined /> 重大风险预警</span>} 
          style={{ marginBottom: 16, borderColor: '#ffccc7' }} 
          headStyle={{ background: '#fff2f0', borderBottom: '1px solid #ffccc7' }}
          size="small"
        >
          <List
            size="small"
            dataSource={criticalRisks}
            renderItem={(item: string) => (
              <List.Item style={{ padding: '8px 0' }}>
                <Text type="danger">● {item}</Text>
              </List.Item>
            )}
          />
        </Card>
      ) : (
        <Card style={{ marginBottom: 16 }} size="small">
           <div style={{ textAlign: 'center', color: '#52c41a' }}>
             <SafetyCertificateOutlined style={{ fontSize: 24, marginBottom: 8 }} />
             <div>未发现重大致命风险</div>
           </div>
        </Card>
      )}

      {/* 3. 详细分析折叠面板 */}
      <Collapse defaultActiveKey={['1']} ghost>
        <Panel header="🔍 关键发现 (Key Findings)" key="1">
          <List
            size="small"
            dataSource={executiveSummary.key_findings || []}
            renderItem={(item: string) => <List.Item>• {item}</List.Item>}
            locale={{ emptyText: '暂无关键发现' }}
          />
        </Panel>

        <Panel header="⚖️ 法律合规风险详情" key="2">
          <List
            itemLayout="vertical"
            size="small"
            dataSource={highRiskItems}
            locale={{ emptyText: '未检测到高风险合规项' }}
            renderItem={(item: any) => (
              <List.Item style={{ padding: '12px 0' }}>
                <List.Item.Meta
                  title={
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <Tag color="red">{item.category || '风险'}</Tag>
                      <span style={{ fontSize: 13, fontWeight: 600 }}>{item.severity} 风险</span>
                    </div>
                  }
                  description={
                    <div style={{ marginTop: 8 }}>
                      {item.description}
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        </Panel>

        <Panel header="💡 修改建议" key="3">
          <List
            size="small"
            dataSource={recommendations}
            renderItem={(item: string, index: number) => (
              <List.Item>
                <Text strong style={{ color: '#1890ff', marginRight: 8 }}>建议 {index + 1}:</Text>
                {item}
              </List.Item>
            )}
            locale={{ emptyText: '暂无特定修改建议' }}
          />
        </Panel>
      </Collapse>
    </div>
  );
};

export default RiskPanel;