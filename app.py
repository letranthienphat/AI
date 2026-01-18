import streamlit as st
from openai import OpenAI
import google.generativeai as genai

st.set_page_config(page_title="Hệ Thống AI Đa Nền Tảng", layout="wide")

# Khởi tạo bộ nhớ lưu API Key
if "keys" not in st.session_state:
    st.session_state.keys = {"OpenAI": "", "DeepSeek": "", "Gemini": ""}
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar cấu hình
with st.sidebar:
    st.title("⚙️ Thiết lập")
    provider = st.selectbox("Chọn hãng AI:", ["OpenAI", "DeepSeek", "Gemini"])
    
    # Nhập key và lưu lại
    key_input = st.text_input(f"Dán API Key {provider} vào đây:", type="password")
    if key_input:
        st.session_state.keys[provider] = key_input
        st.success("Đã ghi nhận Key!")

    if st.button("Xóa hội thoại"):
        st.session_state.messages = []
        st.rerun()

st.title(f"🤖 Chat với {provider}")

# Hiển thị lịch sử
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Xử lý chat
if prompt := st.chat_input("Nhập câu hỏi..."):
    current_key = st.session_state.keys[provider]
    if not current_key:
        st.error("Bạn chưa nhập API Key!")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_res = ""
        res_area = st.empty()
        
        try:
            if provider == "OpenAI":
                client = OpenAI(api_key=current_key)
                stream = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.messages, stream=True)
                for chunk in stream:
                    full_res += (chunk.choices[0].delta.content or "")
                    res_area.markdown(full_res + "▌")
            
            elif provider == "DeepSeek":
                client = OpenAI(api_key=current_key, base_url="https://api.deepseek.com")
                stream = client.chat.completions.create(model="deepseek-chat", messages=st.session_state.messages, stream=True)
                for chunk in stream:
                    full_res += (chunk.choices[0].delta.content or "")
                    res_area.markdown(full_res + "▌")

            elif provider == "Gemini":
                genai.configure(api_key=current_key)
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                full_res = response.text
                res_area.markdown(full_res)

            st.session_state.messages.append({"role": "assistant", "content": full_res})
        except Exception as e:
            st.error(f"Lỗi: {e}")
