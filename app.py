import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import time
import random

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Nexus OS V50.0.1", layout="wide", page_icon="💠")

st.markdown("""
    <style>
    .stApp { background-color: #05070a !important; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #0a0c10 !important; border-right: 1px solid #1e2630; }
    .chat-user { background: #0084ff; color: white; padding: 12px 16px; border-radius: 15px 15px 0 15px; margin: 8px 0 8px auto; max-width: 80%; width: fit-content; }
    .chat-ai { background: #1c1f26; color: #e0e0e0; padding: 12px 16px; border-radius: 15px 15px 15px 0; margin: 8px auto 8px 0; max-width: 80%; width: fit-content; border-left: 3px solid #00d2ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KẾT NỐI SECRETS (FIX LỖI KEYERROR) ---
# Kiểm tra xem bạn đã dán đúng tên trong Secrets chưa
if "GROQ_KEYS" not in st.secrets or "GEMINI_KEY" not in st.secrets:
    st.error("❌ LỖI ĐỒNG BỘ: Hệ thống không tìm thấy 'GROQ_KEYS' trong Secrets.")
    st.info("Vui lòng kiểm tra lại mục Settings -> Secrets. Bạn phải dán đúng tên GROQ_KEYS (có chữ S).")
    st.stop()

# Gán giá trị từ Secrets
ALL_GROQ_KEYS = st.secrets["GROQ_KEYS"]
MY_GEMINI_KEY = st.secrets["GEMINI_KEY"]

# Khởi tạo Gemini
genai.configure(api_key=MY_GEMINI_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. QUẢN LÝ TRẠNG THÁI ---
if 'os_state' not in st.session_state:
    st.session_state.update({
        'page': 'auth', 'user': None, 'messages': []
    })

# --- 4. HÀM XỬ LÝ AI (SỬ DỤNG XOAY VÒNG KEY) ---
def call_nexus_ai(user_messages):
    # Tạo bản sao danh sách Key và trộn ngẫu nhiên
    available_keys = list(ALL_GROQ_KEYS)
    random.shuffle(available_keys)
    
    # Chỉ lấy 6 câu gần nhất để tránh tốn token
    history_context = user_messages[-7:]
    
    # THỬ GROQ TRƯỚC
    for key in available_keys:
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in history_context],
                stream=True
            )
            return response, "Groq-Engine"
        except Exception as e:
            if "rate_limit" in str(e).lower():
                continue # Nếu hết hạn mức, thử Key tiếp theo
            break
            
    # NẾU TẤT CẢ GROQ LỖI -> DÙNG GEMINI
    try:
        st.toast("⚠️ Các cổng Groq đang bận, chuyển sang Gemini...", icon="🔄")
        chat = gemini_model.start_chat(history=[])
        # Chuyển đổi lịch sử cho Gemini
        for m in history_context[:-1]:
            role = "user" if m["role"] == "user" else "model"
            chat.history.append({"role": role, "parts": [m["content"]]})
        
        response = chat.send_message(user_messages[-1]["content"], stream=True)
        return response, "Gemini-Engine"
    except:
        return None, "All-Engines-Offline"

# --- 5. ĐIỀU HƯỚNG ---
with st.sidebar:
    st.title("💠 NEXUS OS")
    st.caption("Phiên bản: V50.0.1")
    if st.button("🏠 Trang chủ"): st.session_state.page = 'home'; st.rerun()
    if st.button("🤖 Trợ lý AI"): st.session_state.page = 'chat'; st.rerun()
    st.divider()
    if st.button("🗑️ Xóa Chat"): st.session_state.messages = []; st.rerun()

# MÀN HÌNH CHAT (TRỌNG TÂM)
if st.session_state.page == 'auth':
    st.title("🔐 Khởi động hệ thống")
    name = st.text_input("Định danh người dùng:")
    if st.button("Truy cập"):
        if name: st.session_state.user = name; st.session_state.page = 'home'; st.rerun()

elif st.session_state.page == 'home':
    st.title(f"Xin chào, {st.session_state.user}")
    st.info("Hệ thống đã sẵn sàng với 3 lõi Groq và 1 lõi Gemini dự phòng.")
    if st.button("Bắt đầu trò chuyện"): st.session_state.page = 'chat'; st.rerun()

elif st.session_state.page == 'chat':
    st.title("🤖 Nexus Terminal")
    
    for m in st.session_state.messages:
        role_class = "chat-user" if m["role"] == "user" else "chat-ai"
        st.markdown(f'<div class="{role_class}">{m["content"]}</div>', unsafe_allow_html=True)

    if prompt := st.chat_input("Nhập câu hỏi..."):
        st.markdown(f'<div class="chat-user">{prompt}</div>', unsafe_allow_html=True)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.empty():
            res_box = st.empty()
            full_text = ""
            response, engine = call_nexus_ai(st.session_state.messages)
            
            if response:
                if engine == "Groq-Engine":
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            full_text += chunk.choices[0].delta.content
                            res_box.markdown(f'<div class="chat-ai">{full_text} ▌</div>', unsafe_allow_html=True)
                else:
                    for chunk in response:
                        full_text += chunk.text
                        res_box.markdown(f'<div class="chat-ai">{full_text} ▌</div>', unsafe_allow_html=True)
                
                res_box.markdown(f'<div class="chat-ai">{full_text}</div>', unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": full_text})
            else:
                st.error("🆘 Hiện tại tất cả các cổng AI đều đang quá tải.")
