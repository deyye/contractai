import React, { useState } from 'react';
import { Layout, Upload, Button, message, Row, Col, Spin, Empty } from 'antd';
import { InboxOutlined, FilePdfOutlined, RocketOutlined } from '@ant-design/icons';
import { uploadPDF, startReview } from './api/service';
import RiskPanel from './components/RiskPanel';
import { pdfjs, Document, Page } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// 设置 PDF worker (必须)
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

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
    try {
      const res = await uploadPDF(file);
      if (res.success) {
        setExtractedText(res.file_content);
        message.success('文件解析成功，准备审查');
      } else {
        message.error('文件解析失败: ' + res.message);
      }
    } catch (err) {
      message.error('上传出错');
    } finally {
      setLoading(false);
    }
    return false; // 阻止默认自动上传
  };

  // 触发 AI 审查
  const handleReview = async () => {
    if (!extractedText) return;
    setLoading(true);
    try {
      const res = await startReview(extractedText);
      if (res.status === 'success') {
        // 后端返回的是双重序列化的 JSON，需要解析两次
        // 第一次：res.result 是一个包含 JSON 字符串的字符串
        // 实际数据结构可能直接就是 JSON 对象，取决于 IntegrationAgent 的封装
        // 这里尝试直接解析 res.result
        try {
          const parsed = JSON.parse(res.result);
          // 如果解析出来还有 analysis 字段，说明就是我们要的
          setReviewResult(parsed.analysis || parsed);
          message.success('审查完成！');
        } catch (e) {
          console.error("JSON Parse Error", e);
          message.warning("结果解析异常，显示原始文本");
          setReviewResult({ raw: res.result });
        }
      }
    } catch (err) {
      message.error('审查请求失败');
    } finally {
      setLoading(false);
    }
  };

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setPdfNumPages(numPages);
  }

  return (
    <Layout style={{ height: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', color: 'white', fontSize: '18px' }}>
        <FilePdfOutlined style={{ marginRight: 10 }} /> 招标文件智能审查系统
      </Header>
      
      <Content style={{ padding: '20px', height: 'calc(100vh - 64px)' }}>
        <Row gutter={24} style={{ height: '100%' }}>
          
          {/* 左侧：PDF 预览与上传区 */}
          <Col span={12} style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            
            {/* 上传区域 */}
            <div style={{ height: !pdfFile ? '100%' : '150px', marginBottom: 20, transition: 'all 0.3s' }}>
              <Dragger 
                accept=".pdf" 
                beforeUpload={handleUpload} 
                showUploadList={false}
                style={{ height: '100%', background: '#fff' }}
              >
                <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                <p className="ant-upload-text">点击或拖拽上传招标文件 (PDF)</p>
                <p className="ant-upload-hint">支持单文件上传，系统将自动解析文本内容</p>
              </Dragger>
            </div>

            {/* PDF 预览区域 */}
            {pdfFile && (
              <div style={{ flex: 1, overflowY: 'auto', background: '#e6e6e6', padding: 20, borderRadius: 8 }}>
                <div style={{ marginBottom: 10, display: 'flex', justifyContent: 'space-between' }}>
                   <strong>{pdfFile.name}</strong>
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
                  loading={<Spin tip="正在加载 PDF..." />}
                >
                  {/* 简单渲染所有页面 */}
                  {Array.from(new Array(pdfNumPages), (el, index) => (
                    <Page 
                      key={`page_${index + 1}`} 
                      pageNumber={index + 1} 
                      width={600} 
                      renderTextLayer={false} 
                      style={{ marginBottom: 10 }}
                    />
                  ))}
                </Document>
              </div>
            )}
          </Col>

          {/* 右侧：AI 审查报告 */}
          <Col span={12} style={{ height: '100%' }}>
            <RiskPanel analysisData={reviewResult} loading={loading && !!extractedText} />
          </Col>

        </Row>
      </Content>
    </Layout>
  );
};

export default App;