import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import time
import random
from datetime import datetime

# --- 1. THIẾT LẬP HỆ THỐNG (DARK MODE) ---
st.set_page_config(page_title="Nexus OS V50.0.0.2", layout="wide", page_icon="💠")
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
st.markdown("""
    <style>
    .stApp { background-color: #05070a !important; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #0a0c10 !important; border-right: 1px solid #1e2630; }
    h1, h2, h3, p, span, label { color: #ffffff !important; }
    
    /* Bong bóng chat tinh chỉnh */
    .chat-user {
        background: #0084ff; color: white; padding: 12px 16px;
        border-radius: 15px 15px 0 15px; margin: 8px 0 8px auto;
        max-width: 80%; width: fit-content; text-align: right;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .chat-ai {
        background: #1c1f26; color: #e0e0e0; padding: 12px 16px;
        border-radius: 15px 15px 15px 0; margin: 8px auto 8px 0;
        max-width: 80%; width: fit-content; border-left: 3px solid #00d2ff;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    
    /* App Cards cho Home */
    .app-card {
        background: #11141a; border: 1px solid #1e2630;
        padding: 25px; border-radius: 15px; text-align: center;
        transition: 0.3s;
    }
    .app-card:hover { border-color: #00d2ff; background: #161b22; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KIỂM TRA & KÍCH HOẠT SECRETS ---
if "GROQ_KEYS" not in st.secrets or "GEMINI_KEY" not in st.secrets:
    st.error("🆘 CHƯA CẤU HÌNH API KEYS!")
    st.info("Hãy dán danh sách Key vào mục **Settings -> Secrets** trên Streamlit Cloud.")
    st.stop()

GROQ_KEYS = st.secrets["GROQ_KEYS"]
GEMINI_KEY = st.secrets["GEMINI_KEY"]

# Khởi tạo Gemini Core
genai.configure(api_key=GEMINI_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
if 'os_state' not in st.session_state:
    st.session_state.update({
        'page': 'auth', 
        'user': None, 
        'messages': [],
        'feedbacks': []
    })

# --- 4. LÕI XỬ LÝ AI THÔNG MINH (MULTI-FAILOVER) ---
def get_ai_response(messages):
    # Trộn ngẫu nhiên 3 Key Groq
    current_groq_keys = list(GROQ_KEYS)
    random.shuffle(current_groq_keys)
    
    # Chỉ lấy context 6 câu gần nhất
    context = messages[-7:]
    
    # THỬ NGHIỆM LỚP 1: GROQ (3 KEYS)
    for i, key in enumerate(current_groq_keys):
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in context],
                stream=True,
                max_tokens=1024
            )
            return response, f"Groq-Secure-Channel-{i+1}"
        except Exception as e:
            if "rate_limit" in str(e).lower():
                continue # Nhảy sang Key tiếp theo
            break 

    # THỬ NGHIỆM LỚP 2: GEMINI (BACKUP CUỐI CÙNG)
    try:
        st.toast("⚡ Đang sử dụng băng tần dự phòng Gemini...", icon="🛡️")
        chat = gemini_model.start_chat(history=[])
        for m in context[:-1]:
            role = "user" if m["role"] == "user" else "model"
            chat.history.append({"role": role, "parts": [m["content"]]})
        
        response = chat.send_message(messages[-1]["content"], stream=True)
        return response, "Gemini-Ultra-Stability"
    except Exception as e:
        return None, f"Lỗi nghiêm trọng: {str(e)}"

# --- 5. ĐIỀU HƯỚNG SIDEBAR ---
with st.sidebar:
    st.title("💠 NEXUS OS")
    st.caption("Phiên bản: V50.0.0.2")
    st.divider()
    if st.button("🏠 Màn hình chính", use_container_width=True): 
        st.session_state.page = 'home'; st.rerun()
    if st.button("🤖 Trợ lý AI", use_container_width=True): 
        st.session_state.page = 'chat'; st.rerun()
    if st.button("⚙️ Cài đặt hệ thống", use_container_width=True): 
        st.session_state.page = 'settings'; st.rerun()
    st.divider()
    if st.button("🗑️ Xóa lịch sử Chat"):
        st.session_state.messages = []
        st.toast("Đã dọn dẹp bộ nhớ!"); st.rerun()

# --- 6. CHI TIẾT CÁC TRANG ---

# TRANG ĐĂNG NHẬP
if st.session_state.page == 'auth':
    st.title("🔐 Hệ thống xác thực")
    u_name = st.text_input("Nhập tên định danh của bạn:")
    if st.button("Khởi động Nexus"):
        if u_name:
            st.session_state.user = u_name
            st.session_state.page = 'home'; st.rerun()

# TRANG CHỦ (HOME DASHBOARD)
elif st.session_state.page == 'home':
    st.title(f"Chào mừng trở lại, {st.session_state.user}")
    st.write("Hệ thống đang hoạt động với 4 lớp bảo mật API.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="app-card"><h3>🤖</h3><h4>AI CHATBOT</h4><p>Truy cập lõi xử lý ngôn ngữ</p></div>', unsafe_allow_html=True)
        if st.button("Mở Chat", use_container_width=True): st.session_state.page = 'chat'; st.rerun()
    with col2:
        st.markdown('<div class="app-card"><h3>⚙️</h3><h4>CÀI ĐẶT</h4><p>Quản lý cấu hình hệ thống</p></div>', unsafe_allow_html=True)
        if st.button("Vào Cài đặt", use_container_width=True): st.session_state.page = 'settings'; st.rerun()

# TRANG CHAT AI
elif st.session_state.page == 'chat':
    st.title("🤖 Nexus Intelligence Terminal")
    
    # Hiển thị lịch sử
    for m in st.session_state.messages:
        role_class = "chat-user" if m["role"] == "user" else "chat-ai"
        st.markdown(f'<div class="{role_class}">{m["content"]}</div>', unsafe_allow_html=True)

    if prompt := st.chat_input("Nhập lệnh..."):
        st.markdown(f'<div class="chat-user">{prompt}</div>', unsafe_allow_html=True)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.empty():
            res_box = st.empty()
            full_text = ""
            response, engine = get_ai_response(st.session_state.messages)
            
            if response:
                if "Groq" in engine:
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
                st.caption(f"🛡️ Phản hồi qua: {engine}")
            else:
                st.error("🆘 Toàn bộ 4 API Keys đều đang bận. Vui lòng nghỉ 30 giây!")

# TRANG CÀI ĐẶT
elif st.session_state.page == 'settings':
    st.title("⚙️ System Control")
    st.write(f"**Phiên bản:** V50.0.0.2 (Build 2026)")
    st.write(f"**Trạng thái API:** 3 Groq Slots + 1 Gemini Slot (Active)")
    if st.button("Quay lại Home"): st.session_state.page = 'home'; st.rerun()
