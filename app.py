import streamlit as st
import pdfplumber
from openai import OpenAI
import os

# --- 页面配置 ---
st.set_page_config(
    page_title="工业机器人轨迹插补 - 综述生成器",
    page_icon="🤖",
    layout="wide"
)

# --- 侧边栏：设置 ---
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("请输入 API Key (OpenAI/DeepSeek等)", type="password")
    base_url = st.text_input("Base URL (可选)", value="https://api.openai.com/v1", help="如果你使用的是DeepSeek或中转API，请修改此处")
    model_name = st.text_input("模型名称", value="gpt-4-turbo", help="建议使用支持长文本的模型，如 gpt-4-turbo 或 deepseek-chat")
    
    st.markdown("---")
    st.markdown("### 关于本工具")
    st.info("本工具专门用于生成《工业机器人轨迹插补技术研究》综述。只需拖入PDF，即可按指定学术标准生成报告。")

# --- 核心函数：提取PDF文本 ---
def extract_text_from_pdfs(uploaded_files):
    combined_text = ""
    file_info = []
    
    progress_bar = st.progress(0)
    for i, file in enumerate(uploaded_files):
        try:
            with pdfplumber.open(file) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                # 截取每篇论文的前5000字（通常包含摘要、引言、结论和核心方法），防止Token溢出
                # 如果模型支持极大上下文（如Kimi/Claude-200k），可以去掉切片
                combined_text += f"\n--- Start of Paper: {file.name} ---\n{text[:8000]}\n--- End of Paper ---\n"
                file_info.append(file.name)
        except Exception as e:
            st.error(f"读取文件 {file.name} 失败: {e}")
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    return combined_text, file_info

# --- 核心函数：调用LLM生成综述 ---
def generate_review(text_content, api_key, base_url, model):
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    # 这里的Prompt严格遵循了你的所有要求
    system_prompt = """
    你是一位机器人领域的资深学术专家。请根据用户提供的多篇论文内容，撰写一篇有关“工业机器人轨迹插补技术研究”的文献综述。
    
    必须严格遵守以下【结构要求】：
    1. 研究背景: 阐述该领域的起源和发展动机。
    2. 研究脉络: 按时间线梳理关键突破(1980s-2024)。
    3. 方法分类: 对涉及的方法进行分类，并对比每类方法的优缺点。
    4. 研究空白: 指出当前未解决的3-5个关键问题。
    5. 未来方向: 基于已有研究进行合理推测。

    必须严格遵守以下【写作要求】：
    - 引用格式：每个论点必须引用具体论文，格式为 (First Author, Year)。
    - 语言风格：使用学术化语言，客观中立，避免主观评价。
    - 争议处理：对有争议的观点呈现多方立场。
    - 输出格式：Markdown。
    - 关键术语首次出现时请加粗（例如：**NURBS插补**）。
    """

    user_prompt = f"""
    以下是上传的论文内容摘要集：
    {text_content}
    
    请开始撰写综述。
    """

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=True 
        )
        return response
    except Exception as e:
        st.error(f"API 调用失败: {e}")
        return None

# --- 主界面 UI ---
st.title("📄 工业机器人轨迹插补 - 智能综述生成器")
st.markdown("请直接**拖拽**相关的 PDF 论文文件到下方区域。")

uploaded_files = st.file_uploader("上传论文 PDF (支持多选)", type="pdf", accept_multiple_files=True)

if uploaded_files and api_key:
    if st.button("🚀 开始生成综述", type="primary"):
        with st.spinner('正在解析 PDF 内容并提取关键信息...'):
            # 1. 提取文本
            raw_text, files_list = extract_text_from_pdfs(uploaded_files)
            st.success(f"成功解析 {len(files_list)} 篇论文！正在请求 AI 撰写综述...")
            
            # 2. 生成综述（流式输出）
            output_placeholder = st.empty()
            full_response = ""
            
            response_stream = generate_review(raw_text, api_key, base_url, model_name)
            
            if response_stream:
                for chunk in response_stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        output_placeholder.markdown(full_response + "▌") # 模拟打字机效果
                
                output_placeholder.markdown(full_response) # 显示最终结果
                
                # 3. 下载按钮
                st.download_button(
                    label="📥 下载综述 (Markdown)",
                    data=full_response,
                    file_name="Literature_Review_Interpolation.md",
                    mime="text/markdown"
                )
elif uploaded_files and not api_key:
    st.warning("请在左侧侧边栏输入 API Key 后开始。")
