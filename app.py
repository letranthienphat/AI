import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random
import time
from datetime import datetime

# --- 1. CẤU HÌNH HỆ THỐNG & GIAO DIỆN ---
st.set_page_config(page_title="Nexus OS V50.1.2", layout="wide", page_icon="💠")

# Nhúng CSS Dark Mode cao cấp
st.markdown("""
    <style>
    .stApp { background-color: #05070a !important; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #0a0c10 !important; border-right: 1px solid #1e2630; }
    .chat-user { background: #0084ff; color: white; padding: 12px 16px; border-radius: 15px 15px 0 15px; margin: 8px 0 8px auto; max-width: 80%; width: fit-content; box-shadow: 2px 2px 10px rgba(0,0,0,0.3); }
    .chat-ai { background: #1c1f26; color: #e0e0e0; padding: 12px 16px; border-radius: 15px 15px 15px 0; margin: 8px auto 8px 0; max-width: 80%; width: fit-content; border-left: 3px solid #00d2ff; box-shadow: 2px 2px 10px rgba(0,0,0,0.3); }
    .stButton>button { width: 100%; border-radius: 8px; background: #1c1f26; color: white; border: 1px solid #1e2630; transition: 0.3s; }
    .stButton>button:hover { border-color: #00d2ff; background: #252a33; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KẾT NỐI SECRETS ---
try:
    GROQ_POOL = st.secrets["GROQ_KEYS"]
    GEMINI_API = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=GEMINI_API)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("🆘 Secrets chưa được cấu hình đúng! Vui lòng kiểm tra Settings -> Secrets.")
    st.stop()

# --- 3. QUẢN LÝ TRẠNG THÁI ---
if 'messages' not in st.session_state: st.session_state.messages = []
if 'page' not in st.session_state: st.session_state.page = 'auth'
if 'user' not in st.session_state: st.session_state.user = None

# --- 4. LÕI XỬ LÝ AI (FAILOVER ENGINE) ---
def get_response(messages):
    # Trộn Key Groq để tối ưu hạn mức
    keys = list(GROQ_POOL)
    random.shuffle(keys)
    
    # 1. Thử qua các Key Groq
    for k in keys:
        try:
            client = OpenAI(api_key=k, base_url="https://api.groq.com/openai/v1")
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in messages[-6:]],
                stream=True
            )
            return stream, "Groq-Engine"
        except Exception:
            continue # Thử key tiếp theo nếu bị Rate Limit
            
    # 2. Dự phòng Gemini nếu Groq kẹt toàn bộ
    try:
        st.toast("⚡ Đang sử dụng băng tần dự phòng Gemini...", icon="🛡️")
        chat = gemini_model.start_chat(history=[])
        # Chuyển đổi lịch sử cho Gemini
        for m in messages[-5:-1]:
            role = "user" if m["role"] == "user" else "model"
            chat.history.append({"role": role, "parts": [m["content"]]})
        response = chat.send_message(messages[-1]["content"], stream=True)
        return response, "Gemini-Engine"
    except:
        return None, None

# --- 5. SIDEBAR ĐIỀU HƯỚNG ---
with st.sidebar:
    st.title("💠 NEXUS OS")
    st.caption(f"Phiên bản: V50.1.2 | User: {st.session_state.user}")
    st.divider()
    if st.button("🏠 Màn hình chính"): st.session_state.page = 'home'; st.rerun()
    if st.button("🤖 Trợ lý AI"): st.session_state.page = 'chat'; st.rerun()
    if st.button("⚙️ Cài đặt"): st.session_state.page = 'settings'; st.rerun()
    st.divider()
    if st.button("🗑️ Xóa lịch sử chat"): 
        st.session_state.messages = []
        st.toast("Đã dọn dẹp bộ nhớ!"); time.sleep(0.5); st.rerun()

# --- 6. CÁC MÀN HÌNH CHỨC NĂNG ---

# TRANG ĐĂNG NHẬP
if st.session_state.page == 'auth':
    st.title("🔐 Xác thực Nexus")
    name = st.text_input("Nhập tên định danh của bạn:")
    if st.button("Khởi động hệ thống"):
        if name:
            st.session_state.user = name
            st.session_state.page = 'home'; st.rerun()

# TRANG CHỦ
elif st.session_state.page == 'home':
    st.title(f"Chào mừng trở lại, {st.session_state.user}")
    st.info("Hệ thống đang chạy ổn định với 4 lõi AI song song.")
    col1, col2 = st.columns(2)
    with col1:
        st.write("### 🤖 AI Chat")
        st.write("Truy cập Llama 3.3 70B & Gemini Flash.")
        if st.button("Bắt đầu Chat"): st.session_state.page = 'chat'; st.rerun()
    with col2:
        st.write("### ⚙️ Cấu hình")
        st.write("Quản lý API và giao diện người dùng.")
        if st.button("Mở Cài đặt"): st.session_state.page = 'settings'; st.rerun()

# TRANG CHAT CHÍNH
elif st.session_state.page == 'chat':
    st.title("🤖 Nexus AI Terminal")
    
    # Hiển thị tin nhắn cũ
    for m in st.session_state.messages:
        role_class = "chat-user" if m["role"] == "user" else "chat-ai"
        st.markdown(f'<div class="{role_class}">{m["content"]}</div>', unsafe_allow_html=True)

    # Ô nhập liệu
    if prompt := st.chat_input("Nhập lệnh..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.markdown(f'<div class="chat-user">{prompt}</div>', unsafe_allow_html=True)
        
        with st.empty():
            res_box = st.empty()
            full_text = ""
            response, engine = get_response(st.session_state.messages)
            
            if response:
                if engine == "Groq-Engine":
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            full_text += chunk.choices[0].delta.content
                            res_box.markdown(f'<div class="chat-ai">{full_text} ▌</div>', unsafe_allow_html=True)
                else: # Gemini
                    for chunk in response:
                        full_text += chunk.text
                        res_box.markdown(f'<div class="chat-ai">{full_text} ▌</div>', unsafe_allow_html=True)
                
                res_box.markdown(f'<div class="chat-ai">{full_text}</div>', unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": full_text})
                st.caption(f"🛡️ Phản hồi từ: {engine}")
            else:
                st.error("🆘 Tất cả server đều bận. Thử lại sau 30 giây.")

# TRANG CÀI ĐẶT
elif st.session_state.page == 'settings':
    st.title("⚙️ Cài đặt hệ thống")
    st.write(f"**Trạng thái kết nối:** 🟢 Tốt")
    st.write(f"**Số lượng API Key Groq:** {len(GROQ_POOL)}")
    st.write(f"**API Key Gemini:** Đã kích hoạt")
    if st.button("🚪 Đăng xuất"):
        st.session_state.user = None
        st.session_state.page = 'auth'; st.rerun()
