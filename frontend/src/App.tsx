import React, { useState, useMemo } from 'react';
import { Layout, Upload, Button, message, Row, Col, Spin, Typography, Tag, Divider } from 'antd';
import { 
  InboxOutlined, 
  RocketOutlined, 
  FilePdfOutlined, 
  DeleteOutlined, 
  CheckCircleOutlined,
  WarningOutlined,
  RobotOutlined
} from '@ant-design/icons';
import { uploadPDF, startReview } from './api/service';
import RiskPanel from './components/RiskPanel';
import ProcessingStatus from './components/ProcessingStatus'; // 确保创建了这个文件
import { pdfjs, Document as PDFDocument, Page } from 'react-pdf';

// 引入 CSS
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import './App.css'; // 引入上面创建的 CSS

// 配置 PDF Worker (Vite 方式)
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
pdfjs.GlobalWorkerOptions.workerSrc = pdfWorker;

const { Header, Sider, Content } = Layout;
const { Dragger } = Upload;
const { Title, Paragraph, Text } = Typography;

const App: React.FC = () => {
  // --- 状态管理 ---
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [extractedText, setExtractedText] = useState<string>("");
  const [reviewResult, setReviewResult] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [pdfNumPages, setPdfNumPages] = useState<number>(0);
  const [uiState, setUiState] = useState<'initial' | 'processing' | 'result'>('initial');

  // 优化 PDF 配置：使用 jsDelivr 替代 unpkg 以提高国内访问速度
  const pdfOptions = useMemo(() => ({
    cMapUrl: `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjs.version}/cmaps/`,
    cMapPacked: true,
  }), []);

  // --- 事件处理 ---

  // 1. 上传并解析
  const handleUpload = async (file: File) => {
    setLoading(true);
    setPdfFile(file);
    setReviewResult(null);
    setExtractedText("");
    
    try {
      const res = await uploadPDF(file);
      if (res.success) {
        setExtractedText(res.file_content);
        message.success(`文件 "${file.name}" 解析成功`);
      } else {
        message.error('文件解析失败: ' + res.message);
        setPdfFile(null); 
      }
    } catch (err) {
      console.error(err);
      message.error('上传服务连接失败，请检查后端');
      setPdfFile(null);
    } finally {
      setLoading(false);
    }
    return false; // 阻止默认上传
  };

  // 2. 开始 AI 审查
  const handleReview = async () => {
    if (!extractedText) {
      message.warning('请等待文件解析完成');
      return;
    }
    
    setLoading(true);
    setUiState('processing'); // 切换到处理中视图

    try {
      const res = await startReview(extractedText);
      if (res.status === 'success') {
        try {
          let parsedData = res.result;
          if (typeof res.result === 'string') {
             parsedData = JSON.parse(res.result);
          }
          const finalData = parsedData.analysis || parsedData;
          setReviewResult(finalData);
          message.success('智能审查完成！');
          setUiState('result'); // 切换到结果视图
        } catch (e) {
          console.error("JSON Parse Error", e);
          message.warning("结果解析格式异常，展示原始数据");
          setReviewResult({ raw: res.result });
          setUiState('result');
        }
      } else {
        message.error('审查失败: ' + (res.message || '未知错误'));
        setUiState('initial'); // 回退
      }
    } catch (err) {
      console.error(err);
      message.error('审查请求超时或失败');
      setUiState('initial');
    } finally {
      setLoading(false);
    }
  };

  // 3. 重置
  const handleReset = () => {
    setPdfFile(null);
    setExtractedText("");
    setReviewResult(null);
    setUiState('initial');
  };

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setPdfNumPages(numPages);
  }

  // --- 界面渲染 ---

  // 1. 初始上传界面
  const renderInitialView = () => (
    <div className="hero-upload-container">
      <div className="upload-card">
        <Title level={2} style={{ marginBottom: '0.5em', fontWeight: 700 }}>招标文件智能审查系统</Title>
        <Paragraph type="secondary" style={{ marginBottom: '2.5em', fontSize: '16px' }}>
          上传 PDF 合同或招标文件，AI 引擎将自动识别 <Text strong>合规风险</Text> 与 <Text strong>商业陷阱</Text>
        </Paragraph>

        {!pdfFile ? (
          <Dragger 
            accept=".pdf" 
            beforeUpload={handleUpload} 
            showUploadList={false}
            height={240}
            style={{ background: '#fafafa', border: '2px dashed #d9d9d9', borderRadius: '12px' }}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined style={{ color: '#1677ff', fontSize: '64px' }} />
            </p>
            <p className="ant-upload-text" style={{ fontSize: '18px', color: '#595959' }}>
              点击或拖拽文件到此处上传
            </p>
            <p className="ant-upload-hint" style={{ color: '#8c8c8c' }}>
              支持 PDF 格式，建议文件大小不超过 20MB
            </p>
          </Dragger>
        ) : (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ marginBottom: 32 }}>
              <FilePdfOutlined style={{ fontSize: 64, color: '#ff4d4f' }} />
              <div style={{ marginTop: 16, fontSize: 18, fontWeight: 600 }}>{pdfFile.name}</div>
              <div style={{ marginTop: 8 }}>
                {loading ? <Spin size="small" /> : <Tag color="success" icon={<CheckCircleOutlined />}>解析完成</Tag>}
              </div>
            </div>
            
            <Row gutter={24} justify="center">
              <Col>
                <Button size="large" icon={<DeleteOutlined />} onClick={handleReset} style={{ width: 140, height: 48 }}>
                  重新上传
                </Button>
              </Col>
              <Col>
                 <Button 
                   type="primary" 
                   size="large" 
                   icon={<RocketOutlined />} 
                   onClick={handleReview}
                   loading={loading}
                   style={{ width: 180, height: 48, fontSize: '16px', boxShadow: '0 4px 14px rgba(22, 119, 255, 0.3)' }}
                 >
                   开始智能审查
                 </Button>
              </Col>
            </Row>
          </div>
        )}
      </div>
    </div>
  );

  // 2. 结果工作台界面
  const renderResultDashboard = () => (
    <Row gutter={24} style={{ height: '100%' }}>
      {/* 左侧：PDF 阅读器 */}
      <Col span={12} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 8px' }}>
           <Title level={5} style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
             <FilePdfOutlined style={{ marginRight: 8, color: '#ff4d4f' }} /> 原文预览：{pdfFile?.name}
           </Title>
           <Button size="small" onClick={handleReset} icon={<DeleteOutlined />}>关闭</Button>
        </div>
        
        <div className="pdf-container">
          {pdfFile && (
            <PDFDocument
              file={pdfFile}
              onLoadSuccess={onDocumentLoadSuccess}
              options={pdfOptions}
              loading={
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', color: 'rgba(255,255,255,0.8)', marginTop: 100 }}>
                  <Spin size="large" />
                  <div style={{ marginTop: 16 }}>文档渲染中...</div>
                </div>
              }
              error={<div style={{ color: '#ff4d4f', marginTop: 50 }}>PDF 加载失败，请检查网络或文件是否损坏</div>}
            >
              {Array.from(new Array(pdfNumPages), (el, index) => (
                <Page 
                  key={`page_${index + 1}`} 
                  pageNumber={index + 1} 
                  width={600} 
                  renderTextLayer={false}
                  className="pdf-page-shadow"
                  style={{ marginBottom: 24 }}
                />
              ))}
            </PDFDocument>
          )}
        </div>
      </Col>

      {/* 右侧：审查结果 */}
      <Col span={12} style={{ height: '100%', overflowY: 'auto', paddingRight: 4 }}>
        <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center' }}>
          <RobotOutlined style={{ fontSize: '24px', color: '#1677ff', marginRight: 12 }} />
          <div>
            <Title level={4} style={{ margin: 0 }}>智能审查报告</Title>
            <Text type="secondary" style={{ fontSize: 12 }}>由 DeepSeek V3 生成</Text>
          </div>
        </div>
        <RiskPanel analysisData={reviewResult} loading={loading} />
      </Col>
    </Row>
  );

  return (
    <Layout style={{ height: '100vh' }}>
      <Sider width={260} theme="dark" style={{ background: '#001529', boxShadow: '2px 0 8px rgba(0,0,0,0.15)', zIndex: 10 }}>
        <div className="logo-area">
           Contract AI
        </div>
        
        <div style={{ padding: '0 24px', color: 'rgba(255,255,255,0.65)' }}>
          <div style={{ 
            padding: '12px 0', 
            borderBottom: '1px solid rgba(255,255,255,0.1)',
            marginBottom: 20,
            fontSize: '12px',
            textTransform: 'uppercase',
            letterSpacing: '1px'
          }}>
            使用指南
          </div>
          
          <div style={{ marginBottom: 24 }}>
            <div style={{ color: '#fff', marginBottom: 8, display: 'flex', alignItems: 'center' }}>
              <div style={{ width: 24, height: 24, borderRadius: '50%', background: '#1677ff', color: '#fff', textAlign: 'center', lineHeight: '24px', marginRight: 10, fontSize: 12 }}>1</div>
              上传文档
            </div>
            <div style={{ fontSize: 13, paddingLeft: 34 }}>支持 PDF 格式招标文件</div>
          </div>

          <div style={{ marginBottom: 24 }}>
            <div style={{ color: '#fff', marginBottom: 8, display: 'flex', alignItems: 'center' }}>
              <div style={{ width: 24, height: 24, borderRadius: '50%', background: '#1677ff', color: '#fff', textAlign: 'center', lineHeight: '24px', marginRight: 10, fontSize: 12 }}>2</div>
              智能分析
            </div>
            <div style={{ fontSize: 13, paddingLeft: 34 }}>自动识别条款风险</div>
          </div>

          <div style={{ marginBottom: 24 }}>
             <div style={{ color: '#fff', marginBottom: 8, display: 'flex', alignItems: 'center' }}>
              <div style={{ width: 24, height: 24, borderRadius: '50%', background: '#1677ff', color: '#fff', textAlign: 'center', lineHeight: '24px', marginRight: 10, fontSize: 12 }}>3</div>
              获取报告
            </div>
            <div style={{ fontSize: 13, paddingLeft: 34 }}>导出或在线查看建议</div>
          </div>

          <div style={{ marginTop: 100, textAlign: 'center' }}>
            <Tag color="blue" style={{ margin: 0 }}>v1.0.0 Beta</Tag>
          </div>
        </div>
      </Sider>

      <Layout>
        <Header style={{ 
          background: '#fff', 
          padding: '0 32px', 
          height: 64, 
          boxShadow: '0 1px 4px rgba(0,21,41,0.05)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          zIndex: 5
        }}>
          <div style={{ fontSize: 16, fontWeight: 600, color: '#001529' }}>
            项目仪表盘
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
             <Text type="secondary" style={{ fontSize: 13 }}>AI 引擎状态:</Text>
             <Tag color="success" bordered={false}>Online</Tag>
          </div>
        </Header>
        
        <Content style={{ padding: '24px', height: 'calc(100vh - 64px)', overflow: 'hidden', position: 'relative' }}>
          {uiState === 'initial' && renderInitialView()}
          
          {uiState === 'processing' && (
             <div style={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'column', paddingBottom: 100 }}>
               <ProcessingStatus isProcessing={loading} />
             </div>
          )}

          {uiState === 'result' && renderResultDashboard()}
        </Content>
      </Layout>
    </Layout>
  );
};

export default App;