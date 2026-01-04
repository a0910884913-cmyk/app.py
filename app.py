import streamlit as st
import pdfplumber
import google.generativeai as genai
import os

# --- 页面配置 ---
st.set_page_config(page_title="Gemini 综述生成器", page_icon="🤖", layout="wide")

# --- 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("请输入 Google API Key", type="password")
    model_name = st.selectbox("选择模型", ["gemini-1.5-flash", "gemini-1.5-pro"])
    st.info("💡 提示：Flash速度快，Pro逻辑强。")

# --- 提取文本 ---
def extract_text(uploaded_files):
    combined_text = ""
    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                combined_text += page.extract_text() or ""
    return combined_text

# --- Gemini 生成函数 ---
def generate_review(text, key, model):
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(model)
        
        prompt = f"""
        你是一位机器人领域的专家。基于以下论文内容撰写“工业机器人轨迹插补技术”综述。
        
        【论文内容】
        {text[:30000]} 
        
        【结构要求】
        1. 研究背景
        2. 研究脉络(1980s-2024)
        3. 方法分类(对比优缺点)
        4. 研究空白
        5. 未来方向

        【要求】
        - Markdown格式
        - 必须引用(Author, Year)
        - 学术语言
        """
        
        response = model.generate_content(prompt, stream=True)
        return response
    except Exception as e:
        return str(e)

# --- 主界面 ---
st.title("🤖 工业机器人综述生成器 (Gemini版)")
files = st.file_uploader("拖入PDF", type="pdf", accept_multiple_files=True)

if st.button("开始生成") and files and api_key:
    text = extract_text(files)
    st.success(f"已读取 {len(files)} 份文件，正在思考...")
    
    placeholder = st.empty()
    full_text = ""
    
    #流式输出
    response = generate_review(text, api_key, model_name)
    
    # 错误处理
    if isinstance(response, str): 
        st.error(f"出错啦: {response}")
    else:
        for chunk in response:
            if chunk.text:
                full_text += chunk.text
                placeholder.markdown(full_text + "▌")
        placeholder.markdown(full_text)
        
        st.download_button("下载综述", full_text, "review.md")
