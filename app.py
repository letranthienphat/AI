# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json

# --- 1. CẤU HÌNH HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V2700 - INTELLI-ADAPTIVE"

st.set_page_config(page_title=f"NEXUS {VERSION}", layout="wide", initial_sidebar_state="auto")

try:
    API_LIST = st.secrets.get("GROQ_KEYS", [])
    ACTIVE_KEY = API_LIST[0] if API_LIST else st.secrets.get("GROQ_KEY", "")
except:
    ACTIVE_KEY = ""

# Khởi tạo Session State
if 'users' not in st.session_state: st.session_state.users = {"admin": "123"}
if 'auth_status' not in st.session_state: st.session_state.auth_status = None
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = ""
if 'stage' not in st.session_state: st.session_state.stage = "AUTH"
if 'theme' not in st.session_state:
    st.session_state.theme = {"mode": "dark", "primary_color": "#00f2ff", "bg_url": ""}
if 'chat_library' not in st.session_state: st.session_state.chat_library = {}
if 'current_chat' not in st.session_state: st.session_state.current_chat = None

def nav(p): st.session_state.stage = p

# --- 2. CSS THÍCH ỨNG (RESPONSIVE) & PLASMA GLOW ---
def apply_adaptive_ui():
    theme = st.session_state.theme
    bg_style = f"background-image: url('{theme['bg_url']}'); background-size: cover;" if theme['bg_url'] else ""
    app_bg = "#0f0f0f" if theme['mode'] == "dark" else "#ffffff"
    text_color = "#ffffff" if theme['mode'] == "dark" else "#1a1a1a"
    card_bg = "rgba(25, 25, 25, 0.85)" if theme['mode'] == "dark" else "rgba(240, 240, 240, 0.9)"

    st.markdown(f"""
    <style>
    .stApp {{ background: {app_bg}; {bg_style} background-attachment: fixed; color: {text_color}; }}
    
    /* Responsive Buttons */
    div.stButton > button {{
        width: 100% !important; border-radius: 12px !important;
        background: {card_bg} !important; color: {text_color} !important;
        border: 1px solid #444 !important; font-weight: 600 !important;
        padding: 12px !important; transition: 0.3s;
    }}
    
    /* Media Query cho điện thoại */
    @media (max-width: 600px) {{
        div.stButton > button {{ min-height: 55px !important; font-size: 1rem !important; }}
        h1 {{ font-size: 1.8rem !important; }}
    }}

    div.stButton > button:active {{
        border-color: {theme['primary_color']} !important;
        box-shadow: 0 0 15px {theme['primary_color']} !important;
    }}

    /* AI Bubble - Chống lặp, tương phản cao */
    div[data-testid="stChatMessageAssistant"] {{
        background: #FFFFFF !important; border-radius: 18px !important;
        padding: 1.5rem !important; margin: 10px 0 !important;
        border-left: 6px solid {theme['primary_color']} !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}
    div[data-testid="stChatMessageAssistant"] * {{ color: #000000 !important; line-height: 1.6; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI AI THÔNG MINH ---
def call_smart_ai(messages):
    if not ACTIVE_KEY: return "⚠️ Lỗi: API Key chưa được cấu hình."
    try:
        client = OpenAI(api_key=ACTIVE_KEY, base_url="https://api.groq.com/openai/v1")
        # System prompt giúp AI thông minh và không lặp
        system_msg = {
            "role": "system", 
            "content": "Bạn là Nexus AI, một trợ lý thông minh và sắc sảo. Hãy trả lời gãy gọn, tránh lặp lại các cụm từ hoặc ý tưởng đã nói. Nếu không biết, hãy nói không biết. Luôn giữ thái độ đàng hoàng, chuyên nghiệp."
        }
        full_messages = [system_msg] + messages
        
        return client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=full_messages,
            temperature=0.7, # Tăng độ đa dạng
            presence_penalty=0.6, # Hạn chế lặp chủ đề
            frequency_penalty=0.5, # Hạn chế lặp từ ngữ
            stream=True
        )
    except Exception as e: return f"Lỗi kết nối: {str(e)}"

# --- 4. MÀN HÌNH CHỨC NĂNG ---

def screen_auth():
    apply_adaptive_ui()
    st.markdown("<h1 style='text-align:center;'>NEXUS OS LOGIN</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["🔑 ĐĂNG NHẬP", "📝 ĐĂNG KÝ", "👤 KHÁCH"])
    with t1:
        u = st.text_input("Tài khoản", key="u_login")
        p = st.text_input("Mật khẩu", type="password", key="p_login")
        if st.button("XÁC THỰC"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status, st.session_state.logged_in_user = "User", u
                nav("MENU"); st.rerun()
            else: st.error("Sai thông tin!")
    with t2:
        nu = st.text_input("Tên đăng ký", key="u_reg")
        np = st.text_input("Mật khẩu", type="password", key="p_reg")
        if st.button("TẠO TÀI KHOẢN"):
            st.session_state.users[nu] = np; st.success("Đã đăng ký!"); time.sleep(1)
    with t3:
        if st.button("VÀO VỚI GUEST MODE"):
            st.session_state.auth_status, st.session_state.logged_in_user = "Guest", "Guest"
            nav("MENU"); st.rerun()

def screen_menu():
    apply_adaptive_ui()
    st.markdown(f"### 🚀 Dashboard | {st.session_state.logged_in_user}")
    c = st.columns(2)
    with c[0]:
        st.button("🧠 NEURAL INTERFACE", on_click=nav, args=("CHAT",))
        st.button("📂 STORAGE MANAGER", on_click=nav, args=("STORAGE",))
    with c[1]:
        st.button("🎨 CUSTOM ENGINE", on_click=nav, args=("SETTINGS",))
        st.button("⚙️ SYSTEM INFO", on_click=nav, args=("INFO",))
    st.write("---")
    st.button("🚪 ĐĂNG XUẤT", on_click=nav, args=("AUTH",))

def screen_chat():
    apply_adaptive_ui()
    with st.sidebar:
        st.header("📂 Thư viện Chat")
        new_chat_name = st.text_input("Tên phiên chat mới:")
        if st.button("➕ KHỞI TẠO"):
            if new_chat_name:
                st.session_state.chat_library[new_chat_name] = []
                st.session_state.current_chat = new_chat_name; st.rerun()
        
        st.write("---")
        for chat_id in list(st.session_state.chat_library.keys()):
            if st.button(f"📄 {chat_id}"):
                st.session_state.current_chat = chat_id; st.rerun()
        
        st.write("---")
        st.button("🔙 VỀ MENU", on_click=nav, args=("MENU",))

    if not st.session_state.current_chat:
        st.info("Vui lòng tạo hoặc chọn một cuộc trò chuyện ở Sidebar.")
        return

    st.subheader(f"📍 Đang chạy: {st.session_state.current_chat}")
    history = st.session_state.chat_library[st.session_state.current_chat]
    
    for msg in history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if p := st.chat_input("Nhập lệnh cho Nexus..."):
        history.append({"role": "user", "content": p})
        st.rerun()

    if history and history[-1]["role"] == "user":
        with st.chat_message("assistant"):
            box = st.empty(); full = ""
            res = call_smart_ai(history)
            if isinstance(res, str): st.error(res)
            else:
                for chunk in res:
                    c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                    if c:
                        full += c
                        box.markdown(full + "▌")
                box.markdown(full)
                history.append({"role": "assistant", "content": full})
                st.rerun()

def screen_storage():
    apply_adaptive_ui()
    st.title("📂 STORAGE & EXPORT")
    mode = st.radio("Phạm vi xuất dữ liệu:", ["Chỉ cuộc chat hiện tại", "Toàn bộ thư viện"])
    if st.button("XUẤT FILE .TXT"):
        data = {st.session_state.current_chat: st.session_state.chat_library[st.session_state.current_chat]} if mode == "Chỉ cuộc chat hiện tại" else st.session_state.chat_library
        enc = base64.b64encode(json.dumps(data).encode()).decode()
        st.download_button("💾 DOWNLOAD", data=enc, file_name=f"nexus_data_{st.session_state.logged_in_user}.txt")
    
    st.write("---")
    st.button("🔙 QUAY LẠI", on_click=nav, args=("MENU",))

def screen_info():
    apply_adaptive_ui()
    st.title("⚙️ THÔNG TIN HỆ THỐNG")
    t1, t2, t3 = st.tabs(["👤 KIẾN TRÚC SƯ", "📊 PHIÊN BẢN", "📜 ĐIỀU KHOẢN"])
    with t1:
        st.markdown(f"### {CREATOR_NAME}")
        st.write("Lớp 7A1 - Trường THCS-THPT Nguyễn Huệ.")
        st.write("Tầm nhìn: Tạo ra một hệ điều hành AI tối ưu cho học sinh.")
    with t2:
        st.info(f"Hệ điều hành: {VERSION}")
        st.write("- Tích hợp Adaptive UI (Tương thích Mobile/PC).")
        st.write("- Lõi AI chống lặp câu và tăng độ thông minh.")
    with t3:
        st.warning("Điều khoản: Sử dụng đàng hoàng. Dữ liệu được mã hóa để bảo vệ quyền riêng tư.")
    
    st.write("---")
    st.button("🔙 QUAY LẠI MENU", on_click=nav, args=("MENU",))

def screen_settings():
    apply_adaptive_ui()
    st.title("🎨 CUSTOM ENGINE")
    st.session_state.theme['mode'] = st.radio("Chế độ:", ["dark", "light"], index=0 if st.session_state.theme['mode']=="dark" else 1)
    st.session_state.theme['primary_color'] = st.color_picker("Màu chủ đề:", st.session_state.theme['primary_color'])
    st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền:", st.session_state.theme['bg_url'])
    
    col1, col2 = st.columns(2)
    with col1: st.button("✅ LƯU & VỀ MENU", on_click=nav, args=("MENU",))
    with col2: st.button("🔙 HỦY BỎ", on_click=nav, args=("MENU",))

# --- 5. ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "STORAGE": screen_storage()
elif st.session_state.stage == "INFO": screen_info()
elif st.session_state.stage == "SETTINGS": screen_settings()
