import streamlit as st
import google.generativeai as genai
from openai import OpenAI

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="AI Super Hub - Secure Edition", layout="wide", page_icon="🛡️")

# Lấy Groq API Key từ Secrets của Streamlit
# Cách này giúp mã nguồn không chứa Key thật, tránh bị lộ trên GitHub
if "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
else:
    st.error("❌ Lỗi: Chưa tìm thấy GROQ_API_KEY trong mục Secrets của Streamlit!")
    st.info("Hướng dẫn: Vào Settings -> Secrets trên Dashboard Streamlit và dán Key vào.")
    st.stop()

# Khởi tạo bộ nhớ Session
if "messages" not in st.session_state:
    st.session_state.messages = []
if "custom_keys" not in st.session_state:
    st.session_state.custom_keys = {"Gemini": "", "OpenAI": "", "DeepSeek": ""}

# --- 2. THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.title("🛡️ Quản lý Bảo mật")
    
    # Chế độ mặc định dùng Groq đã được cài trong Secrets
    mode = st.radio("Chế độ:", ["Dùng Groq (Đã cấu hình Secrets)", "Dùng API cá nhân khác"])
    
    if mode == "Dùng API cá nhân khác":
        st.divider()
        provider = st.selectbox("Hãng AI:", ["Gemini", "OpenAI", "DeepSeek"])
        current_k = st.session_state.custom_keys[provider]
        new_k = st.text_input(f"Nhập Key {provider}:", value=current_k, type="password")
        if st.button("Lưu & Áp dụng"):
            st.session_state.custom_keys[provider] = new_k
            st.success("Đã ghi nhận!")
    else:
        provider = "Groq"
        st.success("✅ Hệ thống đang dùng Groq Key từ Secrets.")

    st.divider()
    if st.button("🗑️ Xóa lịch sử chat"):
        st.session_state.messages = []
        st.rerun()

# --- 3. GIAO DIỆN CHAT ---
st.title(f"🤖 Trợ lý AI ({provider})")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Nhập câu hỏi tại đây..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        
        try:
            # SỬ DỤNG GROQ VỚI KEY TỪ SECRETS
            if provider == "Groq":
                client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
                stream = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(full_res + "▌")

            # CÁC HÃNG KHÁC (DÙNG KEY NHẬP TAY)
            else:
                user_key = st.session_state.custom_keys[provider]
                if not user_key:
                    st.warning(f"Vui lòng nhập Key cho {provider} ở sidebar.")
                    st.stop()
                
                if provider == "Gemini":
                    genai.configure(api_key=user_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(prompt)
                    full_res = response.text
                else:
                    b_url = "https://api.openai.com/v1" if provider == "OpenAI" else "https://api.deepseek.com"
                    m_name = "gpt-3.5-turbo" if provider == "OpenAI" else "deepseek-chat"
                    client = OpenAI(api_key=user_key, base_url=b_url)
                    # Logic chat tương tự...
                    
            res_area.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})

        except Exception as e:
            st.error(f"⚠️ Lỗi: {str(e)}")
