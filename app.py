import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Nexus OS V50.0.1.1", layout="wide", page_icon="💠")

# --- 2. KẾT NỐI SECRETS (KHỚP HOÀN TOÀN VỚI ẢNH CỦA BẠN) ---
try:
    # Lấy danh sách 3 keys từ GROQ_KEYS trong Secrets
    ALL_GROQ_KEYS = st.secrets["GROQ_KEYS"]
    # Lấy key từ GEMINI_KEY trong Secrets
    MY_GEMINI_KEY = st.secrets["GEMINI_KEY"]
    
    # Khởi tạo Gemini
    genai.configure(api_key=MY_GEMINI_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("❌ LỖI SECRETS: Vui lòng kiểm tra lại tên biến trong mục Settings -> Secrets.")
    st.stop()

# --- 3. QUẢN LÝ TRẠNG THÁI ---
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'user' not in st.session_state:
    st.session_state.user = None

# --- 4. HÀM GỌI AI XOAY VÒNG ---
def call_nexus_ai(messages):
    keys = list(ALL_GROQ_KEYS)
    random.shuffle(keys)
    context = messages[-7:]

    # Thử Groq trước
    for key in keys:
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in context],
                stream=True
            )
            return response, "Groq"
        except:
            continue
            
    # Dự phòng Gemini
    try:
        chat = gemini_model.start_chat(history=[])
        response = chat.send_message(messages[-1]["content"], stream=True)
        return response, "Gemini"
    except:
        return None, None

# --- 5. GIAO DIỆN ---
if not st.session_state.user:
    st.title("🔐 Đăng nhập Nexus")
    name = st.text_input("Tên bạn:")
    if st.button("Truy cập"):
        st.session_state.user = name
        st.rerun()
else:
    st.title(f"🤖 Nexus Terminal (V50.0.1.1)")
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Hỏi bất cứ điều gì..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            res_box = st.empty()
            full_text = ""
            response, engine = call_nexus_ai(st.session_state.messages)
            
            if response:
                if engine == "Groq":
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            full_text += chunk.choices[0].delta.content
                            res_box.markdown(full_text + "▌")
                else:
                    for chunk in response:
                        full_text += chunk.text
                        res_box.markdown(full_text + "▌")
                res_box.markdown(full_text)
                st.session_state.messages.append({"role": "assistant", "content": full_text})
            else:
                st.error("🆘 Toàn bộ server đang bận.")
