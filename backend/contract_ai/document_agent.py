import re
import json
import requests
from typing import Dict, List, Any, Optional, Callable
from base_agent import BaseAgent
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate


# 招标场景核心提取字段
TENDER_CORE_FIELDS = [
    "tender_title",  # 招标项目名称
    "tender_number",  # 招标编号
    "tender_method",  # 招标方式（公开/邀请/竞争性谈判等）
    "project_budget",  # 项目预算/最高限价
    "bid_submission_deadline",  # 投标截止时间
    "opening_time",  # 开标时间
    "tenderer",  # 招标人
    "tender_agency",  # 招标代理机构
    "bid_security",  # 投标保证金（金额+形式）
    "qualification_requirements",  # 投标人资格要求（列表）
    "evaluation_criteria",  # 评审标准（核心条款）
    "tender_scope",  # 招标范围
    "implementation_period",  # 项目实施周期
    "project_location",  # 项目地点
]

# 招标核心章节关键词
TENDER_SECTION_KEYWORDS = {
    "基本信息": ["项目名称", "招标编号", "招标方式", "招标人", "代理机构"],
    "财务相关": ["预算", "最高限价", "投标保证金", "付款方式", "金额"],
    "时间要求": ["截止时间", "开标时间", "公告期限", "投标有效期", "实施周期"],
    "资格要求": ["投标人资格", "资质条件", "准入标准", "报名条件", "注册资金"],
    "评审标准": ["评审标准", "评标办法", "打分细则", "中标条件", "价格权重"],
    "招标范围": ["招标范围", "采购内容", "服务要求", "技术参数", "项目内容"],
}

class DocumentProcessingAgent(BaseAgent):
    """Agent specialized in tender document processing and key information extraction"""
    
    def __init__(self):
        system_prompt = """你是专门处理招标文件的智能体。你的职责包括：

1. 招标文件解析和文本提取
2. 识别招标文件结构（章节、条款、附件、技术参数等）
3. 提取关键招标信息（招标人、项目信息、资格要求、评审标准等）
4. 识别招标文件类型（货物采购、服务采购、工程建设等）
5. 清理和标准化文本格式，为后续审查提供结构化数据

你需要：
- 准确识别招标文件的核心组成部分
- 提取招投标关键要素和约束条件
- 识别潜在的格式不规范问题
- 输出结构化数据，便于法律、商务等智能体进一步分析
- 重点关注招标程序、资格要求、评审标准等核心模块

输出格式应该结构化，包含关键信息字典、文档结构分析、文本统计等模块。"""

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # 每块最大字符数（适配LLM上下文）
            chunk_overlap=200,  # 块重叠字符数（避免拆分关键信息）
            separators=["\n\n", "\n", "。", "；", " "],  # 优先按段落拆分
        )
        self.extraction_prompt = self._build_extraction_prompt()
        self.extractor = JSONExtractor()
        
        super().__init__(agent_name="DocumentProcessingAgent", system_prompt=system_prompt)
    
    def parse_pdf_through_api(self, file_path, api_url="http://127.0.0.1:8000/api/pdf/upload"):
        """
        通过API上传PDF文件并获取解析后的文本内容
        
        参数:
            file_path: PDF文件的本地路径
            api_url: API接口的完整URL
        
        返回:
            解析成功返回文本内容，失败返回错误信息
        """
        try:
            with open(file_path, 'rb') as file:
                # 构建multipart/form-data格式的请求体
                files = {
                    'file': (  # 键名必须与API要求的"file"一致
                        file_path.split('/')[-1],  # 文件名
                        file,  # 文件二进制内容
                        'application/pdf'  # MIME类型
                    )
                }
                
                response = requests.post(
                    url=api_url,
                    files=files,
                    timeout=60  # 设置超时时间，避免长期无响应
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        return {
                            'status': 'success',
                            'content': result.get('file_content')
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f"API返回失败: {result.get('message', '未知错误')}"
                        }
                else:
                    return {
                        'status': 'error',
                        'message': f"请求失败，状态码: {response.status_code}"
                    }
                    
        except FileNotFoundError:
            return {'status': 'error', 'message': f"文件未找到: {file_path}"}
        except Exception as e:
            return {'status': 'error', 'message': f"请求发生异常: {str(e)}"}
        
    def _build_extraction_prompt(self) -> PromptTemplate:
        """构建结构化提取Prompt模板"""
        fields_desc = "\n".join([f"- {field}：请提取准确值，未找到填null" for field in TENDER_CORE_FIELDS])
        
        prompt = """
        你是招标文件关键信息提取专家，请从以下文档片段中提取指定字段，严格按照JSON格式返回结果：
        
        提取要求：
        1. 仅提取与字段相关的精准信息，不添加额外描述
        2. 金额、时间、编号等信息需完整提取（如：2025年12月31日、￥100万元、ZB-2025-001）
        3. 资格要求、评审标准、资信标部分、技术部分、商务报价部分等列表类字段，用数组形式返回
        4. 未找到的字段必须填null，不可省略
        5. 优先使用文档原文表述，如需概括需保证准确
        
        需提取的字段：
        {fields_desc}
        
        文档片段：
        {document_chunk}
        
        输出格式（仅JSON，无其他内容）：
        {{
            "tender_title": "",
            "tender_number": "",
            ...（其他字段）
        }}
        """
        return PromptTemplate(
            template=prompt,
            input_variables=["fields_desc", "document_chunk"],
            partial_variables={"fields_desc": fields_desc}
        )

    def _preprocess_document(self, document_text: str) -> str:
        """文档预处理：清理格式、去除冗余"""
        # 去除多余空格、换行
        cleaned_text = re.sub(r'\s+', ' ', document_text)
        # 去除特殊字符（保留中文、英文、数字、常用标点）
        cleaned_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。；：""''（）《》、·！？￥$¥%&*+=-_(){}[]]', '', cleaned_text)
        return cleaned_text

    def _split_document_by_keywords(self, cleaned_text: str) -> Dict[str, List[str]]:
        """按关键词分块：将文档拆分为核心章节对应的区块"""
        keyword_chunks = {section: [] for section in TENDER_SECTION_KEYWORDS.keys()}
        # 先按通用分块器拆分基础块
        base_chunks = self.text_splitter.split_text(cleaned_text)
        
        # 为每个基础块匹配对应的核心章节
        for chunk in base_chunks:
            for section, keywords in TENDER_SECTION_KEYWORDS.items():
                if any(keyword in chunk for keyword in keywords):
                    keyword_chunks[section].append(chunk)
                    break  # 一个块只匹配一个核心章节
        
        # 合并每个章节的区块（避免过于零散）
        merged_chunks = {}
        for section, chunks in keyword_chunks.items():
            if chunks:
                merged_chunks[section] = " ".join(chunks)[:]  # 限制单章节长度
        
        return merged_chunks

    def _extract_from_chunk(self, chunk_text: str) -> Dict[str, Any]:
        """从单个区块提取信息（已修复卡死问题）"""
        try:
            extraction_chain = self.extraction_prompt | self.llm
            # 增加 timeout 防止网络层卡死
            response = extraction_chain.invoke({"document_chunk": chunk_text})
            
            # 使用新的提取器
            extracted_list = self.extractor.extract(response.content)
            
            if extracted_list:
                # 合并提取到的所有字典（有些模型可能会分多个对象返回）
                merged = {field: None for field in TENDER_CORE_FIELDS}
                for item in extracted_list:
                    for k, v in item.items():
                        if k in TENDER_CORE_FIELDS and v is not None:
                            merged[k] = v
                return merged
            else:
                self.logger.warning("LLM返回了内容，但无法解析为JSON")
                return {field: None for field in TENDER_CORE_FIELDS}
                
        except Exception as e:
            self.logger.error(f"区块提取发生异常: {str(e)}")
            return {field: None for field in TENDER_CORE_FIELDS}

    def _merge_extracted_results(self, results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多区块提取结果:取非空值、去重、整合列表"""
        print(f"_merge_extracted_results 接收到 {len(results_list)} 个结果")
        merged_result = {field: None for field in TENDER_CORE_FIELDS}
        
        for idx, result in enumerate(results_list):
            print(f"处理第 {idx+1} 个结果，类型: {type(result)}")
            # 修复:result本身就是字典,不需要通过[0]索引访问
            if not isinstance(result, dict):
                print(f"  警告: 第 {idx+1} 个结果不是字典类型，跳过")
                continue
                
            for field in TENDER_CORE_FIELDS:
                value = result.get(field)
                if value is None or value == "null":
                    continue
                
                # 处理列表类字段（如资格要求、评审标准）
                if field in ["qualification_requirements", "evaluation_criteria"]:
                    current_value = merged_result[field] or []
                    if isinstance(value, list):
                        current_value.extend([item for item in value if item not in current_value])
                    else:
                        if value not in current_value:
                            current_value.append(value)
                    merged_result[field] = current_value if current_value else None
                # 处理普通字段（取第一个非空值，确保唯一性）
                else:
                    if merged_result[field] is None:
                        merged_result[field] = value
        
        return merged_result

    def _validate_and_supplement(self, merged_result: Dict[str, Any], full_text: str) -> Dict[str, Any]:
        """结果校验与补全：针对缺失的关键字段，用全文档快速检索"""
        missing_fields = [field for field in TENDER_CORE_FIELDS if merged_result[field] is None]
        print(f"缺失字段数量: {len(missing_fields)}, 字段: {missing_fields}")
        
        if not missing_fields:
            print("无缺失字段，跳过补全")
            return merged_result
        
        # 如果缺失字段过多（>10个），可能提取失败，跳过补全避免浪费时间
        if len(missing_fields) > 10:
            print(f"缺失字段过多({len(missing_fields)}个)，跳过补全")
            return merged_result
        
        # 限制全文长度，避免token超限（最多使用前8000字符）
        # truncated_text = full_text[:8000] if len(full_text) > 8000 else full_text
        # print(f"使用文本长度: {len(truncated_text)} 字符进行补全")
        
        # 为缺失字段构建针对性检索Prompt
        supplement_prompt = f"""
        以下是招标文件片段：
        {full_text}
        
        请补充提取以下缺失的字段（仅返回字段值，用JSON格式，未找到填null）：
        {json.dumps(missing_fields, ensure_ascii=False)}
        
        输出格式（仅JSON，无其他内容）：
        {{
            "字段名": "值"
        }}
        """
        
        try:
            print("开始调用LLM补全缺失字段...")
            response = self.llm.invoke(supplement_prompt)
            print("LLM补全调用完成")
            print("LLM补全调用完成")
            supplement_data = json.loads(response.content)
            print(f"补全数据解析成功: {list(supplement_data.keys())}")
            # 补充缺失字段
            for field, value in supplement_data.items():
                if field in missing_fields and value is not None and value != "null":
                    merged_result[field] = value
                    print(f"  补全字段 {field}: {str(value)[:50]}...")
        except json.JSONDecodeError as e:
            print(f"补全缺失字段失败（JSON解析错误）：{str(e)}")
        except Exception as e:
            print(f"补全缺失字段失败：{str(e)}")
        
        return merged_result
    
    def extract_key_information(self, document_text: str) -> Dict[str, Any]:
        """主提取流程：预处理→分块→提取→合并→校验"""
        # 1. 文档预处理
        cleaned_text = self._preprocess_document(document_text)
        print(f"预处理后文档长度：{len(cleaned_text)}字符")
        
        # 2. 按关键词分块（聚焦核心章节）
        keyword_chunks = self._split_document_by_keywords(cleaned_text)
        print(f"分块完成，有效章节：{list(keyword_chunks.keys())}")
        
        # 3. 逐区块提取信息
        results_list = []
        for section, chunk in keyword_chunks.items():
            print(f"正在提取【{section}】相关信息...")
            extracted = self._extract_from_chunk(chunk)
            print(f"【{section}】提取结果类型: {type(extracted)}, 内容预览: {str(extracted)[:100]}...")
            results_list.append(extracted)
        
        print(f"所有章节提取完成，results_list长度: {len(results_list)}")
        
        # 4. 合并多区块结果
        print("开始合并结果...")
        merged_result = self._merge_extracted_results(results_list)
        print(f"合并完成，merged_result: {list(merged_result.keys())}")
        
        # 5. 校验并补全缺失字段
        print("开始校验和补全...")
        final_result = self._validate_and_supplement(merged_result, cleaned_text)
        print("校验补全完成")
        
        # 6. 格式化输出（美化JSON）
        final_result = {
            k: (v if v is not None else "未找到") 
            for k, v in final_result.items()
        }
        self.logger.info(f"提取完成，结果：{final_result}")
        return final_result
    
    def process_text_message(self, message, context=None):
        """Process tender document analysis requests"""
        user_text = message
        self.logger.info("Processing tender document analysis request")
        try:
            # Extract task and content
            task_info = self.extract_task_info(user_text)
            document_content = task_info.get("content", user_text)
            
            # Perform tender document processing
            processing_results = self.process_tender_document(document_content)
            
            # Format response
            response_text = self.format_processing_results(processing_results)
            
            return {
                "agent": "DocumentProcessingAgent",
                "status": "success",
                "analysis": processing_results,
                "response_text": response_text,
                "timestamp": self._get_current_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Error in tender document processing: {str(e)}")
            return {
                "agent": "DocumentProcessingAgent",
                "status": "error",
                "message": f"招标文件处理过程中发生错误：{str(e)}",
                "response_text": "招标文件处理过程中发生错误。",
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
                # Everything after "上下文：" is the tender document content
                context_start = text.find("上下文：")
                if context_start != -1:
                    task_info["content"] = text[context_start + 4:].strip()
                break
        
        return task_info
    
    def process_tender_document(self, document_text: str) -> Dict[str, Any]:
        """Main tender document processing function"""
        key_tender_info = self.extract_key_information(document_text)
        
        tender_parties = self.extract_tender_parties(
            text=document_text,
            extracted_info=key_tender_info
        )
        
        # 3. 组装最终结果
        results = {
            "document_structure": self.analyze_tender_document_structure(document_text),
            "key_tender_information": key_tender_info,
            "tender_type": self.identify_tender_type(document_text),
            "tender_parties": tender_parties,  
            "financial_terms": self.extract_tender_financial_terms(document_text),
            "timeline_information": self.extract_tender_timeline(document_text),
            "qualification_requirements": self.extract_qualification_requirements(document_text),
            "evaluation_criteria": self.extract_evaluation_criteria(document_text),
            # "format_issues": self.identify_format_issues(document_text),
            "text_statistics": self.calculate_text_statistics(document_text)
        }
        return results
    
    def analyze_tender_document_structure(self, text: str) -> Dict[str, Any]:
        """Analyze the structure of the tender document"""
        structure = {
            "core_sections": [],  # 核心章节（项目概况、资格要求等）
            "general_clauses": [],  # 通用条款
            "specific_clauses": [],  # 专用条款
            "appendices": [],  # 附件（技术参数、格式要求等）
            "has_contact_information": False,  # 是否包含联系方式
            "has_tender_schedule": False,  # 是否包含招标时间表
            "has_submission_requirements": False  # 是否包含投标文件递交要求
        }
        
        lines = text.split('\n')
        current_section = None
        
        # 招标文件核心章节关键词
        core_section_keywords = [
            '项目概况', '招标范围', '投标人资格', '资格要求', '评审标准', '评标办法',
            '投标文件', '递交要求', '时间安排', '公告期限', '质疑与投诉', '合同主要条款',
            '交易公告', '招标公告', '投标须知', '技术规范', '服务要求', '交易须知',
            '采购需求', '评审办法'
        ]
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 识别核心章节标题
            if any(keyword in line for keyword in core_section_keywords) and len(line) < 50:
                section_info = {
                    "line_number": i + 1,
                    "title": line,
                    "section_type": "core"
                }
                structure["core_sections"].append(section_info)
                current_section = section_info
            
            # 识别条款标记（编号条款）
            elif re.match(r'^(第?[一二三四五六七八九十\d]+[条章节款]|Article\s+\d+|Section\s+\d+)', line, re.IGNORECASE):
                clause_type = "general" if any(g in line for g in ['通用', '一般', '基本']) else "specific"
                clause_info = {
                    "line_number": i + 1,
                    "text": line,
                    "section": current_section["title"] if current_section else None,
                    "clause_type": clause_type
                }
                if clause_type == "general":
                    structure["general_clauses"].append(clause_info)
                else:
                    structure["specific_clauses"].append(clause_info)
            
            # 识别附件
            elif re.match(r'^附件|附录|技术参数|投标格式|Appendix|Exhibit|Annex', line, re.IGNORECASE):
                structure["appendices"].append({
                    "line_number": i + 1,
                    "title": line
                })
            
            # 识别联系方式
            elif re.search(r'联系人|联系电话|联系地址|邮箱|电话', line):
                structure["has_contact_information"] = True
            
            # 识别招标时间表
            elif re.search(r'时间安排|日程表|截止日期|开标时间|公告期限', line):
                structure["has_tender_schedule"] = True
            
            # 识别投标文件递交要求
            elif re.search(r'投标文件.*递交|递交方式|密封要求|份数要求', line):
                structure["has_submission_requirements"] = True
        
        return structure
    
    def extract_key_tender_information(self, text: str) -> Dict[str, Any]:
        """Extract key information from the tender document"""
        key_info = {}
        
        # Use LLM to extract structured tender information
        extraction_prompt = f"""
        请从以下招标文件文本中提取关键信息，以JSON格式返回：
        
        文本：{text}...
        
        请提取以下招标核心信息，未找到的项标记为null：
        1. tender_title - 招标项目名称
        2. tender_number - 招标编号
        3. tender_method - 招标方式（公开招标/邀请招标/竞争性谈判等）
        4. project_budget - 项目预算金额
        5. tender_scope - 招标范围（货物/服务/工程具体内容）
        6. bid_submission_deadline - 投标截止时间
        7. opening_time - 开标时间
        8. tender_agency - 招标代理机构（如有）
        9. winning_criteria - 中标原则（最低价/综合评分等）
        10. bid_security_amount - 投标保证金金额及形式
        11. project_location - 项目实施地点
        12. implementation_period - 项目实施周期
        
        返回严格的JSON格式，不要包含额外说明文字。
        """
        
        llm_response = self.call_llm(extraction_prompt)
        
        try:
            extracted_info = json.loads(llm_response)
            key_info.update(extracted_info)
        except json.JSONDecodeError:
            # Fallback to regex-based extraction for critical fields
            key_info = self.regex_based_tender_extraction(text)
        
        return key_info
    
    def regex_based_tender_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback regex-based tender information extraction"""
        info = {
            "tender_title": None,
            "tender_number": None,
            "tender_method": None,
            "project_budget": None,
            "bid_submission_deadline": None,
            "opening_time": None,
            "tender_agency": None
        }
        
        # 提取招标项目名称（通常在文档开头）
        title_match = re.search(r'项目名称[:：]\s*([^，。；\n]{10,50})', text)
        if not title_match:
            title_match = re.search(r'^(.*?招标项目|.*?采购项目)', text[:500], re.MULTILINE)
        if title_match:
            info["tender_title"] = title_match.group(1).strip()
        
        # 提取招标编号
        number_match = re.search(r'招标编号[:：]\s*([A-Za-z0-9\-_]+)', text)
        if number_match:
            info["tender_number"] = number_match.group(1).strip()
        
        # 提取招标方式
        method_patterns = [r'公开招标', r'邀请招标', r'竞争性谈判', r'询价采购', r'竞争性磋商']
        for method in method_patterns:
            if re.search(method, text):
                info["tender_method"] = method
                break
        
        # 提取项目预算
        budget_match = re.search(r'预算金额[:：]\s*([￥$¥\d,]+(?:\.\d{2})?[元万千万亿]?)', text)
        if not budget_match:
            budget_match = re.search(r'最高限价[:：]\s*([￥$¥\d,]+(?:\.\d{2})?[元万千万亿]?)', text)
        if budget_match:
            info["project_budget"] = budget_match.group(1).strip()
        
        # 提取投标截止时间
        deadline_match = re.search(r'投标截止时间[:：]\s*([\d年月日时分\s\-:/]+)', text)
        if deadline_match:
            info["bid_submission_deadline"] = deadline_match.group(1).strip()
        
        # 提取开标时间
        opening_match = re.search(r'开标时间[:：]\s*([\d年月日时分\s\-:/]+)', text)
        if opening_match:
            info["opening_time"] = opening_match.group(1).strip()
        
        # 提取招标代理机构
        agency_match = re.search(r'招标代理机构[:：]\s*([^，。；\n]+)', text)
        if agency_match:
            info["tender_agency"] = agency_match.group(1).strip()
        
        return info
    
    def identify_tender_type(self, text: str) -> str:
        """Identify the type of tender document"""
        tender_types = {
            '货物采购招标文件': ['货物采购', '设备采购', '物资采购', '产品采购'],
            '服务采购招标文件': ['服务采购', '技术服务', '咨询服务', '运维服务', '物业服务'],
            '工程建设招标文件': ['工程建设', '建筑工程', '施工招标', '建设项目', '基础设施'],
            '软件开发招标文件': ['软件开发', '系统开发', '程序开发', '信息化建设'],
            '框架协议招标文件': ['框架协议', '年度框架', '长期合作', '批量采购'],
            '竞争性谈判文件': ['竞争性谈判', '谈判文件', '磋商文件'],
            '询价采购文件': ['询价采购', '询价文件']
        }
        
        for tender_type, keywords in tender_types.items():
            if any(keyword in text for keyword in keywords):
                return tender_type
        
        return "通用招标文件"
    
    def extract_tender_parties(self, text: str, extracted_info: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Extract tender related parties (tenderer, agency, etc.)
        优先从 extracted_info 提取，缺失则从原文补充
        """
        parties = {}
        extracted_info = extracted_info or {}
        
        # 第一步：优先从已提取的关键信息中获取相关方
        # 映射关系：key_tender_information 中的字段名 → 相关方角色名
        info_mappings = {
            'tenderer': '招标人',
            'tender_agency': '招标代理机构',
            'purchaser': '采购人',
            'project_owner': '项目业主'
        }
        
        for info_key, role in info_mappings.items():
            # 从关键信息中获取值，过滤无效值
            party_value = extracted_info.get(info_key)
            valid_values = ['未找到', '无', 'null', None, '']  # 定义无效值列表
            if party_value not in valid_values:
                parties[role] = str(party_value).strip()  # 确保值为字符串并去重空格
        
        # 第二步：识别需要补充的角色（已获取的角色不再从原文提取）
        all_needed_roles = ['招标人', '采购人', '采购单位', '招标代理机构', '项目业主']
        missing_roles = [role for role in all_needed_roles if role not in parties]
        
        # 若所有角色都已获取，直接返回
        if not missing_roles:
            return parties
        
        # 第三步：从原文提取缺失的相关方
        # 正则模式：(匹配规则, 对应角色)，只提取 missing_roles 中的角色
        party_patterns = [
            (r'招标人[:：]\s*([^，。；\n]+)', '招标人'),
            (r'采购人[:：]\s*([^，。；\n]+)', '采购人'),
            (r'采购单位[:：]\s*([^，。；\n]+)', '采购单位'),
            (r'招标代理机构[:：]\s*([^，。；\n]+)', '招标代理机构'),
            (r'代理机构[:：]\s*([^，。；\n]+)', '招标代理机构'),  # 代理机构默认映射为招标代理机构
            (r'项目业主[:：]\s*([^，。；\n]+)', '项目业主')
        ]
        
        for pattern, role in party_patterns:
            # 只处理缺失的角色，提升效率
            if role not in missing_roles:
                continue
            
            matches = re.findall(pattern, text)
            if matches:
                # 取第一个匹配结果（避免多个匹配导致混乱）
                valid_value = matches[0].strip()
                if valid_value not in valid_values:
                    parties[role] = valid_value
                    missing_roles.remove(role)  # 找到后从缺失列表移除
                    if not missing_roles:  # 所有缺失角色都找到，提前退出循环
                        break
        
        return parties
    
    def extract_tender_financial_terms(self, text: str) -> Dict[str, Any]:
        """Extract financial terms specific to tender documents"""
        financial_terms = {
            "project_budget": [],  # 项目预算
            "bid_security": [],    # 投标保证金
            "payment_terms": [],   # 付款方式
            "price_evaluation": [],# 价格评审相关
            "penalty_clauses": []  # 处罚条款（如弃标处罚）
        }
        
        # 提取项目预算/最高限价
        budget_patterns = [
            r'预算金额[:：]\s*([￥$¥\d,]+(?:\.\d{2})?[元万千万亿]?)',
            r'最高限价[:：]\s*([￥$¥\d,]+(?:\.\d{2})?[元万千万亿]?)',
            r'项目总投资[:：]\s*([￥$¥\d,]+(?:\.\d{2})?[元万千万亿]?)'
        ]
        for pattern in budget_patterns:
            matches = re.findall(pattern, text)
            financial_terms["project_budget"].extend(matches)
        
        # 提取投标保证金
        security_patterns = [
            r'投标保证金[:：]\s*([￥$¥\d,]+(?:\.\d{2})?[元万千万亿]?)',
            r'保证金金额[:：]\s*([￥$¥\d,]+(?:\.\d{2})?[元万千万亿]?)'
        ]
        for pattern in security_patterns:
            matches = re.findall(pattern, text)
            financial_terms["bid_security"].extend(matches)
        
        # 提取付款方式
        payment_keywords = ['付款方式', '支付条款', '结算方式', '预付款', '进度款', '尾款']
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line for keyword in payment_keywords) and len(line.strip()) > 10:
                financial_terms["payment_terms"].append(line.strip())
        
        # 提取价格评审相关
        price_keywords = ['价格得分', '报价评审', '评标基准价', '价格权重']
        for line in lines:
            if any(keyword in line for keyword in price_keywords) and len(line.strip()) > 10:
                financial_terms["price_evaluation"].append(line.strip())
        
        # 提取处罚条款
        penalty_keywords = ['弃标', '违约金', '处罚', '保证金不退']
        for line in lines:
            if any(keyword in line for keyword in penalty_keywords) and len(line.strip()) > 10:
                financial_terms["penalty_clauses"].append(line.strip())
        
        return financial_terms
    
    def extract_tender_timeline(self, text: str) -> Dict[str, List[str]]:
        """Extract tender timeline information (deadlines, schedules)"""
        timeline_info = {
            "key_dates": [],      # 关键日期（公告发布、截止、开标等）
            "time_requirements": [],  # 时间要求（公告期限、质疑期限等）
            "implementation_schedule": []  # 项目实施进度
        }
        
        # 关键日期提取模式
        date_patterns = [
            (r'公告发布日期[:：]\s*([\d年月日\s\-:/]+)', '公告发布日期'),
            (r'投标截止时间[:：]\s*([\d年月日时分\s\-:/]+)', '投标截止时间'),
            (r'开标时间[:：]\s*([\d年月日时分\s\-:/]+)', '开标时间'),
            (r'公示开始日期[:：]\s*([\d年月日\s\-:/]+)', '公示开始日期'),
            (r'质疑截止时间[:：]\s*([\d年月日时分\s\-:/]+)', '质疑截止时间')
        ]
        
        for pattern, date_type in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                timeline_info["key_dates"].append(f"{date_type}：{match.strip()}")
        
        # 时间要求提取（期限类）
        time_requirement_keywords = ['公告期限', '公示期', '质疑期限', '投标有效期', '响应期限']
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line for keyword in time_requirement_keywords) and len(line.strip()) > 10:
                timeline_info["time_requirements"].append(line.strip())
        
        # 项目实施进度
        schedule_keywords = ['实施周期', '工期', '交付期限', '服务期限', '进度安排']
        for line in lines:
            if any(keyword in line for keyword in schedule_keywords) and len(line.strip()) > 10:
                timeline_info["implementation_schedule"].append(line.strip())
        
        return timeline_info
    
    def extract_qualification_requirements(self, text: str) -> List[str]:
        """Extract bidder qualification requirements"""
        qualifications = []
        
        # 资格要求关键词
        qual_keywords = ['投标人资格', '资格要求', '资质条件', '准入标准', '报名条件', '交易须知', '报价要求', 
                         '实质性要求', '资格预审', '资格条件', '评审办法']
        lines = text.split('\n\n')
        capture_mode = False
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # 开始捕获资格要求章节
            if any(keyword in line_stripped for keyword in qual_keywords) and len(line_stripped) < 50:
                capture_mode = True
                qualifications.append(line_stripped)
                continue
            
            # 捕获资格要求内容（直到下一个章节标题）
            if capture_mode:
                # 停止条件：遇到新的章节标题
                if re.match(r'^(第?[一二三四五六七八九十\d]+[条章节]|.*?[:：]$)', line_stripped) and len(line_stripped) < 50:
                    capture_mode = False
                    continue
                qualifications.append(line_stripped)
        
        # 过滤过短的无效内容，保留有意义的资格要求
        qualifications = [q for q in qualifications if len(q) > 8]
        self.logger.info(f"提取到资格要求条目：{qualifications}")
        return qualifications  # 限制返回前15条核心资格要求
    
    def extract_evaluation_criteria(self, text: str) -> List[str]:
        """Extract tender evaluation criteria and methods"""
        evaluation_criteria = []
        
        # 评审标准关键词
        eval_keywords = ['评审标准', '评标办法', '打分细则', '评分标准', '中标条件']
        lines = text.split('\n')
        capture_mode = False
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # 开始捕获评审标准章节
            if any(keyword in line_stripped for keyword in eval_keywords) and len(line_stripped) < 50:
                capture_mode = True
                evaluation_criteria.append(line_stripped)
                continue
            
            # 捕获评审标准内容
            if capture_mode:
                # 停止条件：遇到新的章节标题
                if re.match(r'^(第?[一二三四五六七八九十\d]+[条章节]|.*?[:：]$)', line_stripped) and len(line_stripped) < 50:
                    capture_mode = False
                    continue
                evaluation_criteria.append(line_stripped)
        
        # 过滤无效内容
        evaluation_criteria = [ec for ec in evaluation_criteria if len(ec) > 8]
        return evaluation_criteria[:15]  # 限制返回前15条核心评审标准
    
    def identify_format_issues(self, text: str) -> List[Dict[str, Any]]:
        """Identify potential format issues in tender documents"""
        issues = []
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # 检查过长行（影响可读性）
            if len(line) > 250:
                issues.append({
                    "type": "long_line",
                    "line_number": i + 1,
                    "description": f"第{i+1}行过长（{len(line)} 字符），可能影响条款阅读和理解"
                })
            
            # 检查异常空格（格式不规范）
            if re.search(r'\s{4,}', line):
                issues.append({
                    "type": "inconsistent_spacing",
                    "line_number": i + 1,
                    "description": f"第{i+1}行存在过多连续空格，格式不规范"
                })
            
            # 检查关键条款缺少标点（可能导致歧义）
            if any(keyword in line_stripped for keyword in ['要求', '应当', '不得', '必须', '需要']) and \
               len(line_stripped) > 20 and not line_stripped.endswith(('。', '；', '：', '！', '？', '.', ';', ':', '!', '?')):
                issues.append({
                    "type": "missing_punctuation",
                    "line_number": i + 1,
                    "description": f"第{i+1}行关键要求条款缺少结尾标点，可能存在表述不完整风险"
                })
            
            # 检查编号混乱（条款编号不连续）
            if re.match(r'^\d+\.', line_stripped) and i > 0:
                prev_line = lines[i-1].strip()
                # 简单检查数字编号是否连续（如 1.2 后接 1.4 视为异常）
                try:
                    current_num = float(re.search(r'^\d+\.?\d*', line_stripped).group())
                    prev_num_match = re.search(r'^\d+\.?\d*', prev_line)
                    if prev_num_match:
                        prev_num = float(prev_num_match.group())
                        if current_num - prev_num > 1.1:  # 允许0.1的误差（如1.1后接2.0）
                            issues.append({
                                "type": "disordered_numbering",
                                "line_number": i + 1,
                                "description": f"第{i+1}行条款编号（{current_num}）与前一条（{prev_num}）不连续，可能存在格式混乱"
                            })
                except (ValueError, AttributeError):
                    pass
        
        return issues
    
    def calculate_text_statistics(self, text: str) -> Dict[str, Any]:
        """
        优化后的文本统计模块：增强准确性、增加关键指标、提升鲁棒性
        返回更全面的招标文件文本统计数据，辅助评估文档完整性和规范性
        """
        # 基础文本分割与清洗
        lines = text.split('\n')
        stripped_lines = [line.strip() for line in lines]
        non_empty_lines = [line for line in stripped_lines if line]  # 非空行（已去首尾空格）
        
        # 1. 字符级统计
        total_characters = len(text)
        # 有效字符数（排除纯空白字符）
        valid_characters = len(re.sub(r'\s+', '', text))
        
        # 2. 行级统计
        total_lines = len(lines)
        empty_line_count = total_lines - len(non_empty_lines)
        empty_line_ratio = round(empty_line_count / total_lines * 100, 1) if total_lines > 0 else 0
        
        # 3. 词级统计（优化分词逻辑，适配中文场景）
        # 结合正则分词：支持中英文、数字及常见符号组合
        words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+[^\s]*[\u4e00-\u9fa5a-zA-Z0-9]+|[\u4e00-\u9fa5a-zA-Z0-9]+', text)
        total_words = len(words)
        
        # 4. 行长度统计（更精准的分布分析）
        line_lengths = [len(line) for line in non_empty_lines]
        avg_line_length = round(sum(line_lengths) / len(line_lengths), 1) if line_lengths else 0
        max_line_length = max(line_lengths) if line_lengths else 0
        # 过长行占比（超过200字符视为过长，影响可读性）
        long_line_ratio = round(sum(1 for l in line_lengths if l > 200) / len(line_lengths) * 100, 1) if line_lengths else 0
        
        # 5. 核心章节覆盖率（优化匹配逻辑）
        core_modules = {
            '项目概况': ['项目概况', '项目简介', '项目说明'],
            '投标人资格': ['投标人资格', '资格要求', '资质条件'],
            '评审标准': ['评审标准', '评标办法', '打分细则'],
            '投标文件': ['投标文件', '响应文件', '标书要求'],
            '时间安排': ['时间安排', '日程表', '截止日期'],
            '质疑与投诉': ['质疑与投诉', '异议处理', '举报方式']
        }
        
        # 优化模块匹配：支持多关键词匹配，提升准确性
        covered_modules = 0
        module_coverage_details = {}
        for module, keywords in core_modules.items():
            is_covered = any(re.search(keyword, text) for keyword in keywords)
            module_coverage_details[module] = "已覆盖" if is_covered else "未覆盖"
            if is_covered:
                covered_modules += 1
        
        core_module_coverage_rate = round(covered_modules / len(core_modules) * 100, 1) if core_modules else 0
        
        # 6. 关键信息密度（核心字段相关词汇出现频率）
        key_terms = ['招标编号', '预算', '截止时间', '开标时间', '资格要求', '评审标准']
        key_term_count = sum(len(re.findall(term, text)) for term in key_terms)
        key_term_density = round(key_term_count / total_words * 100, 2) if total_words > 0 else 0
        
        return {
            # 基础统计
            "total_characters": total_characters,
            "valid_characters": valid_characters,  # 新增：有效字符数（排除纯空白）
            "total_lines": total_lines,
            "non_empty_lines": len(non_empty_lines),
            "empty_line_count": empty_line_count,  # 新增：空行数
            "empty_line_ratio": empty_line_ratio,  # 新增：空行占比（%）
            
            # 词汇统计
            "total_words": total_words,
            "key_term_count": key_term_count,  # 新增：核心术语出现次数
            "key_term_density": key_term_density,  # 新增：核心术语密度（%）
            
            # 行长度分析
            "average_line_length": avg_line_length,
            "max_line_length": max_line_length,  # 新增：最长行长度
            "long_line_ratio": long_line_ratio,  # 新增：过长行占比（%）
            
            # 核心模块覆盖
            "core_module_coverage": covered_modules,
            "core_module_coverage_rate": core_module_coverage_rate,
            "module_coverage_details": module_coverage_details,  # 新增：各模块覆盖详情
            
            # 文档质量评估（新增）
            "readability_score": round(100 - long_line_ratio - empty_line_ratio, 1)  # 可读性评分（越高越好）
        }
    
    def format_processing_results(self, results: Dict[str, Any]) -> str:
        """Format tender document processing results for output"""
        output = "=== 招标文件处理结果 ===\n\n"
        # 基本信息
        output += f"招标文件类型：{results.get('tender_type', '未识别')}\n"
        tender_title = results.get('key_tender_information', {}).get('tender_title', '未提取')
        output += f"招标项目名称：{tender_title}\n"
        tender_number = results.get('key_tender_information', {}).get('tender_number', '未提取')
        output += f"招标编号：{tender_number}\n"
        
        # 相关方信息
        parties = results.get('tender_parties', {})
        if parties:
            output += "\n--- 招标相关方 ---\n"
            for role, party in parties.items():
                output += f"{role}：{party}\n"
        
        # 核心关键信息
        key_info = results.get('key_tender_information', {})
        output += "\n--- 核心招标信息 ---\n"
        output += f"招标方式：{key_info.get('tender_method', '未明确')}\n"
        output += f"项目预算：{key_info.get('project_budget', '未明确')}\n"
        output += f"投标截止时间：{key_info.get('bid_submission_deadline', '未明确')}\n"
        output += f"开标时间：{key_info.get('opening_time', '未明确')}\n"
        output += f"投标保证金：{key_info.get('bid_security_amount', '未明确')}\n"
        
        # 文档结构分析
        # structure = results.get('document_structure', {})
        # output += f"\n--- 文档结构分析 ---\n"
        # output += f"核心章节数量：{len(structure.get('core_sections', []))}\n"
        # output += f"通用条款数量：{len(structure.get('general_clauses', []))}\n"
        # output += f"附件数量：{len(structure.get('appendices', []))}\n"
        # output += f"包含联系方式：{'是' if structure.get('has_contact_information') else '否'}\n"
        # output += f"包含招标时间表：{'是' if structure.get('has_tender_schedule') else '否'}\n"
        
        # 资格要求和评审标准预览
        qualifications = results.get('qualification_requirements', [])
        output += f"\n--- 资格要求预览（共{len(qualifications)}条） ---\n"
        for i, qual in enumerate(qualifications[:5], 1):  # 显示前5条
            output += f"{i}. {qual[:80]}...\n" if len(qual) > 80 else f"{i}. {qual}\n"
        
        evaluation_criteria = results.get('evaluation_criteria', [])
        output += f"\n--- 评审标准预览（共{len(evaluation_criteria)}条） ---\n"
        for i, ec in enumerate(evaluation_criteria[:5], 1):  # 显示前5条
            output += f"{i}. {ec[:80]}...\n" if len(ec) > 80 else f"{i}. {ec}\n"
        
        # 文本统计信息
        stats = results.get('text_statistics', {})
        output += f"\n--- 文本统计信息 ---\n"
        output += f"总字符数：{stats.get('total_characters', 0)}\n"
        output += f"有效行数：{stats.get('non_empty_lines', 0)}\n"
        output += f"核心模块覆盖率：{stats.get('core_module_coverage_rate', 0)}%（{stats.get('core_module_coverage', 0)}/6个核心模块）\n"
        
        # 格式问题提示
        # issues = results.get('format_issues', [])
        # if issues:
        #     output += f"\n--- 格式问题提示（共{len(issues)}项） ---\n"
        #     for issue in issues[:3]:  # 显示前3个关键格式问题
        #         output += f"- {issue['description']}\n"
        #     if len(issues) > 3:
        #         output += f"- 另有{len(issues)-3}项格式问题，建议查看详细分析\n"
        
        return output

class JSONExtractor:
    """
    修复版 JSON 提取器：放弃复杂正则，使用非递归查找 + 标准库解析，防止死锁。
    """
    def extract(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取 JSON"""
        results = []
        # 1. 尝试提取 Markdown 代码块中的 JSON
        code_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        
        if not matches:
            # 2. 如果没有代码块，寻找最外层的大括号
            # 这是一个简单的贪婪匹配，通常对 LLM 输出有效
            # 查找所有 { ... } 结构
            matches = self._find_json_candidates(text)
            
        for json_str in matches:
            try:
                # 清理常见的会导致解析失败的字符
                json_str = self._clean_json_str(json_str)
                data = json.loads(json_str)
                if isinstance(data, dict):
                    results.append(data)
                elif isinstance(data, list):
                    results.extend([item for item in data if isinstance(item, dict)])
            except json.JSONDecodeError:
                continue
        return results

    def _find_json_candidates(self, text: str) -> List[str]:
        """简单的堆栈平衡算法寻找最外层 JSON 对象，比正则快且安全"""
        candidates = []
        balance = 0
        start_index = -1
        for i, char in enumerate(text):
            if char == '{':
                if balance == 0:
                    start_index = i
                balance += 1
            elif char == '}':
                balance -= 1
                if balance == 0 and start_index != -1:
                    candidates.append(text[start_index : i+1])
                    start_index = -1
        return candidates

    def _clean_json_str(self, json_str: str) -> str:
        # 移除注释
        json_str = re.sub(r'//.*', '', json_str)
        # 尝试修复末尾逗号
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        return json_str
    
if __name__ == "__main__":
    agent = DocumentProcessingAgent()
    with open('/home/star/81/12.1tender_reviewer/backend/uploads/zhaobiao_sample.txt', 'r', encoding='utf-8') as f:
        contract_text = f.read()
    print(f"已读取合同文件 ({len(contract_text)} 字符)")
    state = {
        'user_input': f'请分析以下招标文件内容，提取关键信息并评估格式规范性。\n上下文：这是招标文件的具体内容{contract_text}'
    }
    result = agent.invoke({
            "text": state["user_input"],
            "context": state.get("context", "")
        })
    agent.logger.info("招标文件处理结果：")
    agent.logger.info(result['response_text'])