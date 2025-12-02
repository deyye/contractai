import React, { useState } from 'react';
import { Layout, Upload, Button, message, Row, Col, Spin, Empty } from 'antd';
import { InboxOutlined, FilePdfOutlined, RocketOutlined } from '@ant-design/icons';
import { uploadPDF, startReview } from './api/service';
import RiskPanel from './components/RiskPanel';
import { pdfjs } from 'react-pdf';

// 修正后的 CSS 引入路径 (去除 /esm/)
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// 设置 PDF worker
// pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
pdfjs.GlobalWorkerOptions.workerSrc = pdfWorker;

const { Header, Content } = Layout;
const { Dragger } = Upload;

const App: React.FC = () => {
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [extractedText, setExtractedText] = useState<string>("");
  const [reviewResult, setReviewResult] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [pdfNumPages, setPdfNumPages] = useState<number>(0);

  // 文件上传处理
  const handleUpload = async (file: File) => {
    setLoading(true);
    setPdfFile(file);
    setReviewResult(null);
    setExtractedText(""); // 清空旧文本
    try {
      const res = await uploadPDF(file);
      if (res.success) {
        setExtractedText(res.file_content);
        message.success('文件解析成功，点击“开始智能审查”即可分析');
      } else {
        message.error('文件解析失败: ' + res.message);
      }
    } catch (err) {
      console.error(err);
      message.error('上传请求失败，请检查后端服务');
    } finally {
      setLoading(false);
    }
    return false; // 阻止默认自动上传
  };

  // 触发 AI 审查
  const handleReview = async () => {
    if (!extractedText) {
      message.warning('请先上传 PDF 文件');
      return;
    }
    setLoading(true);
    setReviewResult(null);
    
    try {
      const res = await startReview(extractedText);
      if (res.status === 'success') {
        // 后端返回的双重序列化 JSON 处理
        try {
          // 尝试解析 result 字符串
          let parsedData = res.result;
          if (typeof res.result === 'string') {
             parsedData = JSON.parse(res.result);
          }
          
          console.log("AI Review Result:", parsedData);
          
          // 优先取 analysis 字段，如果没有则整体作为数据
          const finalData = parsedData.analysis || parsedData;
          setReviewResult(finalData);
          message.success('智能审查完成！');
        } catch (e) {
          console.error("JSON Parse Error", e);
          message.warning("结果解析异常，显示原始文本");
          setReviewResult({ raw: res.result }); // 降级显示
        }
      } else {
        message.error('审查失败: ' + (res.message || '未知错误'));
      }
    } catch (err) {
      console.error(err);
      message.error('审查请求超时或失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setPdfNumPages(numPages);
  }

  return (
    <Layout style={{ height: '100vh', overflow: 'hidden' }}>
      <Header style={{ display: 'flex', alignItems: 'center', color: 'white', fontSize: '18px', padding: '0 24px' }}>
        <FilePdfOutlined style={{ marginRight: 10 }} /> 招标文件智能审查系统
      </Header>
      
      <Content style={{ padding: '24px', height: 'calc(100vh - 64px)', overflow: 'hidden' }}>
        <Row gutter={24} style={{ height: '100%' }}>
          
          {/* 左侧：PDF 预览与上传区 */}
          <Col span={12} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            
            {/* 上传区域 */}
            <div style={{ height: !pdfFile ? '100%' : '140px', marginBottom: 16, transition: 'all 0.3s' }}>
              <Dragger 
                accept=".pdf" 
                beforeUpload={handleUpload} 
                showUploadList={false}
                style={{ height: '100%', background: '#fff', borderRadius: '8px' }}
              >
                <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                <p className="ant-upload-text">点击或拖拽上传招标文件 (PDF)</p>
                <p className="ant-upload-hint">支持单文件上传，系统将自动解析文本内容</p>
              </Dragger>
            </div>

            {/* PDF 预览区域 */}
            {pdfFile && (
              <div style={{ 
                flex: 1, 
                overflowY: 'auto', 
                background: '#525659', 
                padding: '24px', 
                borderRadius: '8px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center'
              }}>
                <div style={{ 
                  width: '100%', 
                  marginBottom: 16, 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  background: 'rgba(255,255,255,0.9)',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  position: 'sticky',
                  top: -10,
                  zIndex: 10
                }}>
                   <span style={{ fontWeight: 500 }}>{pdfFile.name}</span>
                   <Button 
                     type="primary" 
                     icon={<RocketOutlined />} 
                     onClick={handleReview} 
                     loading={loading}
                     disabled={!extractedText}
                   >
                     开始智能审查
                   </Button>
                </div>
                
                <Document
                  file={pdfFile}
                  onLoadSuccess={onDocumentLoadSuccess}
                  loading={<div style={{ color: 'white', marginTop: 20 }}><Spin size="large" /> <div style={{marginTop: 10}}>正在加载 PDF...</div></div>}
                  error={<div style={{ color: 'white' }}>PDF 加载失败，请检查文件是否损坏</div>}
                >
                  {/* 渲染所有页面 */}
                  {Array.from(new Array(pdfNumPages), (el, index) => (
                    <Page 
                      key={`page_${index + 1}`} 
                      pageNumber={index + 1} 
                      width={550} 
                      renderTextLayer={false} 
                      className="pdf-page-shadow"
                      style={{ marginBottom: 16 }}
                    />
                  ))}
                </Document>
              </div>
            )}
          </Col>

          {/* 右侧：AI 审查报告 */}
          <Col span={12} style={{ height: '100%' }}>
            <RiskPanel analysisData={reviewResult} loading={loading} />
          </Col>

        </Row>
      </Content>
    </Layout>
  );
};

export default App;