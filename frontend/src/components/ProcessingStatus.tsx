import React, { useEffect, useState } from 'react';
import { Steps, Card, Typography, Progress } from 'antd';
import { 
  FileSearchOutlined, 
  SafetyCertificateOutlined, 
  AlertOutlined, 
  FileTextOutlined,
  LoadingOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;

interface ProcessingStatusProps {
  isProcessing: boolean;
}

const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ isProcessing }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [percent, setPercent] = useState(0);

  useEffect(() => {
    if (!isProcessing) {
      setPercent(100);
      setCurrentStep(3);
      return;
    }

    // 重置
    setCurrentStep(0);
    setPercent(0);

    // 模拟进度动画 (假设总耗时约 10秒)
    const timer = setInterval(() => {
      setPercent((prev) => {
        // 到达 99% 后等待后端真实响应
        if (prev >= 99) return 99;
        // 前期快，后期慢
        const increment = prev < 30 ? 2 : prev < 70 ? 1 : 0.2;
        return Math.min(prev + increment, 99);
      });
    }, 100);

    return () => clearInterval(timer);
  }, [isProcessing]);

  // 根据进度百分比联动步骤条
  useEffect(() => {
    if (percent < 25) setCurrentStep(0);
    else if (percent < 55) setCurrentStep(1);
    else if (percent < 85) setCurrentStep(2);
    else setCurrentStep(3);
  }, [percent]);

  const items = [
    {
      title: '解析',
      description: '文档结构化解析',
      icon: currentStep === 0 && isProcessing ? <LoadingOutlined /> : <FileSearchOutlined />,
    },
    {
      title: '合规',
      description: '法律条款比对',
      icon: currentStep === 1 && isProcessing ? <LoadingOutlined /> : <SafetyCertificateOutlined />,
    },
    {
      title: '风险',
      description: '商业陷阱识别',
      icon: currentStep === 2 && isProcessing ? <LoadingOutlined /> : <AlertOutlined />,
    },
    {
      title: '报告',
      description: '生成审查报告',
      icon: currentStep === 3 && isProcessing ? <LoadingOutlined /> : <FileTextOutlined />,
    },
  ];

  return (
    <Card className="processing-card" bordered={false}>
      <div style={{ textAlign: 'center', marginBottom: 40, marginTop: 20 }}>
        <Title level={3} style={{ color: '#1890ff' }}>AI 智能审查引擎运行中</Title>
        <Text type="secondary" style={{ fontSize: '16px' }}>
          DeepSeek 大模型正在深度分析合同条款，请稍候...
        </Text>
      </div>
      
      <div style={{ padding: '0 40px 20px 40px' }}>
        <Steps 
          current={currentStep} 
          items={items} 
          labelPlacement="vertical"
        />

        <div style={{ marginTop: 48, maxWidth: '600px', margin: '48px auto 0' }}>
          <Progress 
            percent={Math.floor(percent)} 
            status="active" 
            strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }} 
            strokeWidth={12}
            showInfo={true}
          />
        </div>
      </div>
    </Card>
  );
};

export default ProcessingStatus;