# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json

# --- 1. KHỞI TẠO HẰNG SỐ HỆ THỐNG (FIX LỖI NAMEERROR) ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V2650 - NEBULA STABILITY"

st.set_page_config(page_title=f"NEXUS {VERSION}", layout="wide")

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
if 'chat_library' not in st.session_state: st.session_state.chat_library = {"Cuộc trò chuyện mới": []}
if 'current_chat' not in st.session_state: st.session_state.current_chat = "Cuộc trò chuyện mới"

def nav(p): st.session_state.stage = p

# --- 2. DYNAMIC CSS ENGINE ---
def apply_custom_ui():
    theme = st.session_state.theme
    bg_style = f"background-image: url('{theme['bg_url']}'); background-size: cover;" if theme['bg_url'] else ""
    text_color = "#ffffff" if theme['mode'] == "dark" else "#000000"
    app_bg = "#000000" if theme['mode'] == "dark" else "#f0f2f5"
    card_bg = "rgba(10, 10, 10, 0.9)" if theme['mode'] == "dark" else "rgba(255, 255, 255, 0.9)"
    border_color = "#333" if theme['mode'] == "dark" else "#ddd"

    st.markdown(f"""
    <style>
    .stApp {{ background: {app_bg}; {bg_style} background-attachment: fixed; color: {text_color}; }}
    
    /* NÚT BẤM CÓ HIỆU ỨNG SÁNG VIỀN */
    div.stButton > button {{
        width: 100% !important; border-radius: 15px !important;
        background: {card_bg} !important; color: {text_color} !important;
        border: 1px solid {border_color} !important;
        font-weight: 700 !important; transition: all 0.2s;
    }}
    div.stButton > button:active {{
        border-color: {theme['primary_color']} !important;
        box-shadow: 0 0 20px {theme['primary_color']} !important;
        transform: scale(0.98);
    }}

    /* PHẢN HỒI AI */
    div[data-testid="stChatMessageAssistant"] {{
        background: #FFFFFF !important; border-radius: 20px !important;
        padding: 20px !important; border-left: 5px solid {theme['primary_color']} !important;
    }}
    div[data-testid="stChatMessageAssistant"] * {{ color: #000000 !important; font-weight: 500; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. MÀN HÌNH CHỨC NĂNG ---

def screen_auth():
    apply_custom_ui()
    st.markdown("<h1 style='text-align:center;'>NEXUS GATEWAY</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký", "👤 Khách"])
    with t1:
        u = st.text_input("Tên đăng nhập", key="login_u")
        p = st.text_input("Mật khẩu", type="password", key="login_p")
        if st.button("XÁC THỰC ACCESS"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = "User"; st.session_state.logged_in_user = u
                nav("MENU"); st.rerun()
            else: st.error("Sai thông tin!")
    with t2:
        nu = st.text_input("Tên đăng nhập mới")
        np = st.text_input("Mật khẩu mới", type="password")
        if st.button("ĐĂNG KÝ NGAY"):
            st.session_state.users[nu] = np; st.success("Thành công!"); time.sleep(1)
    with t3:
        if st.button("TIẾP TỤC VỚI GUEST"):
            st.session_state.auth_status = "Guest"; st.session_state.logged_in_user = "Guest"
            nav("MENU"); st.rerun()

def screen_menu():
    apply_custom_ui()
    st.markdown(f"### ⚡ Central Hub | {st.session_state.logged_in_user}")
    c = st.columns(2)
    with c[0]:
        st.button("🧠 NEURAL CHAT", on_click=nav, args=("CHAT",))
        st.button("📂 DỮ LIỆU", on_click=nav, args=("STORAGE",))
    with c[1]:
        st.button("🎨 GIAO DIỆN", on_click=nav, args=("SETTINGS",))
        st.button("⚙️ THÔNG TIN", on_click=nav, args=("INFO",))
    st.write("---")
    st.button("🚪 ĐĂNG XUẤT", on_click=nav, args=("AUTH",))

def screen_settings():
    apply_custom_ui()
    st.title("🎨 CUSTOM ENGINE")
    st.session_state.theme['mode'] = st.radio("Chế độ:", ["dark", "light"], index=0 if st.session_state.theme['mode']=="dark" else 1)
    st.session_state.theme['primary_color'] = st.color_picker("Màu chủ đề:", st.session_state.theme['primary_color'])
    st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền:", st.session_state.theme['bg_url'])
    
    col1, col2 = st.columns(2)
    with col1: st.button("✅ LƯU CẤU HÌNH", on_click=nav, args=("MENU",))
    with col2: st.button("🔙 QUAY LẠI", on_click=nav, args=("MENU",))

def screen_chat():
    apply_custom_ui()
    with st.sidebar:
        st.header("📚 Thư viện Chat")
        n = st.text_input("Tên chat mới:")
        if st.button("➕ TẠO"):
            if n: st.session_state.chat_library[n] = []; st.session_state.current_chat = n; st.rerun()
        st.write("---")
        for t in list(st.session_state.chat_library.keys()):
            if st.button(f"📄 {t}"): st.session_state.current_chat = t; st.rerun()
        st.write("---")
        st.button("🏠 VỀ MENU CHÍNH", on_click=nav, args=("MENU",))

    st.subheader(f"📍 {st.session_state.current_chat}")
    log = st.session_state.chat_library[st.session_state.current_chat]
    for m in log:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("Gửi lệnh cho Nexus..."):
        log.append({"role": "user", "content": p})
        st.rerun()

    if log and log[-1]["role"] == "user":
        with st.chat_message("assistant"):
            box = st.empty(); full = ""
            # Logic gọi AI Groq/OpenAI (giả lập để đảm bảo code chạy ngay)
            full = f"Xin chào, tôi là Nexus OS {VERSION}. Tôi đang xử lý yêu cầu của anh..."
            for c in full:
                box.markdown(full[:full.find(c)+1] + "▌"); time.sleep(0.01)
            box.markdown(full)
            log.append({"role": "assistant", "content": full})
            st.rerun()

def screen_storage():
    apply_custom_ui()
    st.title("📂 QUẢN LÝ DỮ LIỆU")
    opt = st.selectbox("Phạm vi xuất:", ["Toàn bộ", "Chỉ cuộc chat hiện tại"])
    if st.button("TẠO FILE XUẤT"):
        data = st.session_state.chat_library if opt=="Toàn bộ" else {st.session_state.current_chat: st.session_state.chat_library[st.session_state.current_chat]}
        enc = base64.b64encode(json.dumps(data).encode()).decode()
        st.download_button("💾 TẢI FILE .TXT MÃ HÓA", data=enc, file_name="nexus_data.txt")
    
    st.write("---")
    st.button("🔙 QUAY LẠI MENU", on_click=nav, args=("MENU",))

def screen_info():
    apply_custom_ui()
    st.title("⚙️ THÔNG TIN HỆ THỐNG")
    t1, t2, t3 = st.tabs(["👤 Người tạo", "📊 Phiên bản", "📜 Điều khoản"])
    with t1: 
        st.markdown(f"### {CREATOR_NAME}")
        st.write("Lớp 7A1 - Trường THCS-THPT Nguyễn Huệ.")
    with t2: 
        st.info(f"Hệ điều hành: {VERSION}")
        st.write("- Đã sửa lỗi NameError VERSION.")
        st.write("- Tối ưu hóa nút điều hướng Back.")
    with t3: 
        st.write("Sử dụng đúng mục đích. Mọi dữ liệu thuộc về Lê Trần Thiên Phát.")
    
    st.write("---")
    st.button("🔙 QUAY LẠI MENU", on_click=nav, args=("MENU",))

# --- 4. ĐIỀU HƯỚNG CHÍNH ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "SETTINGS": screen_settings()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "STORAGE": screen_storage()
elif st.session_state.stage == "INFO": screen_info()
