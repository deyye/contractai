import React from 'react';
import { Card, Tag, Collapse, Typography, Empty, List } from 'antd';
import { WarningOutlined, CheckCircleOutlined, InfoCircleOutlined } from '@ant-design/icons';

const { Panel } = Collapse;
const { Text, Title, Paragraph } = Typography;

interface RiskPanelProps {
  analysisData: any; // 接收解析后的 JSON 数据
  loading: boolean;
}

const RiskPanel: React.FC<RiskPanelProps> = ({ analysisData, loading }) => {
  if (loading) {
    return <Card loading={true} title="正在进行 AI 深度审查..." style={{ height: '100%' }} />;
  }

  if (!analysisData) {
    return (
      <Card title="审查报告" style={{ height: '100%', overflow: 'auto' }}>
        <Empty description="暂无审查结果，请上传文件并开始审查" />
      </Card>
    );
  }

  // 从整合数据中提取关键部分
  const { executive_summary, risk_assessment, detailed_analysis } = analysisData;
  const criticalRisks = executive_summary?.critical_risks || [];
  const riskScore = risk_assessment?.overall_risk_score || 0;

  // 风险等级颜色映射
  const getScoreColor = (score: number) => {
    if (score >= 7) return '#ff4d4f'; // 红
    if (score >= 4) return '#faad14'; // 黄
    return '#52c41a'; // 绿
  };

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '0 10px' }}>
      {/* 1. 总体评分卡 */}
      <Card style={{ marginBottom: 16, borderTop: `4px solid ${getScoreColor(riskScore)}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>综合风险评分</Title>
            <Text type="secondary">{executive_summary?.overall_assessment}</Text>
          </div>
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ color: getScoreColor(riskScore), margin: 0 }}>
              {riskScore}/10
            </Title>
            <Tag color={riskScore >= 7 ? 'error' : riskScore >= 4 ? 'warning' : 'success'}>
              {riskScore >= 7 ? '高风险' : riskScore >= 4 ? '中风险' : '低风险'}
            </Tag>
          </div>
        </div>
      </Card>

      {/* 2. 重大风险警告 */}
      {criticalRisks.length > 0 && (
        <Card title={<><WarningOutlined style={{ color: '#ff4d4f' }} /> 重大风险预警</>} style={{ marginBottom: 16 }} bodyStyle={{ padding: '12px 24px' }}>
          <List
            dataSource={criticalRisks}
            renderItem={(item: string) => (
              <List.Item>
                <Text type="danger">● {item}</Text>
              </List.Item>
            )}
          />
        </Card>
      )}

      {/* 3. 详细分析折叠面板 */}
      <Collapse defaultActiveKey={['1', '2']}>
        <Panel header="关键发现 (Key Findings)" key="1">
          <ul>
            {executive_summary?.key_findings?.map((item: string, idx: number) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </Panel>

        <Panel header="法律合规风险" key="2">
          <List
            itemLayout="vertical"
            dataSource={risk_assessment?.high_risk_items || []}
            renderItem={(item: any) => (
              <List.Item>
                <List.Item.Meta
                  title={<Tag color="red">{item.category}</Tag>}
                  description={<Text strong>{item.description}</Text>}
                />
              </List.Item>
            )}
          />
        </Panel>

        <Panel header="修改建议" key="3">
          <List
            dataSource={executive_summary?.recommendations || []}
            renderItem={(item: string, index: number) => (
              <List.Item>
                <Tag color="blue">建议 {index + 1}</Tag> {item}
              </List.Item>
            )}
          />
        </Panel>
      </Collapse>
    </div>
  );
};

export default RiskPanel;