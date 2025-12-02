import axios from 'axios';

const api = axios.create({
  baseURL: '/api', // 通过 Vite 代理转发
  timeout: 600000, // AI 分析较慢，设置 10 分钟超时
});

export interface ReviewResponse {
  status: string;
  result: string; // 后端返回的是 JSON 字符串
}

export const uploadPDF = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/pdf/upload', formData);
  return res.data;
};

export const startReview = async (contractText: string) => {
  const res = await api.post<ReviewResponse>('/review', { contract_text: contractText });
  return res.data;
};