# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json

# --- 1. THÔNG TIN CHỦ SỞ HỮU ---
CREATOR_NAME = "Lê Trần Thiên Phát"
CREATOR_INFO = "Lớp 7A1 - Trường THCS-THPT Nguyễn Huệ"
VERSION = "V2850 - DATA CONTROL"

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

try:
    API_LIST = st.secrets.get("GROQ_KEYS", [])
    ACTIVE_KEY = API_LIST[0] if API_LIST else st.secrets.get("GROQ_KEY", "")
except:
    ACTIVE_KEY = ""

# Khởi tạo Session State
if 'users' not in st.session_state: st.session_state.users = {"admin": "123", "phat": "2026"}
if 'auth_status' not in st.session_state: st.session_state.auth_status = None
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = ""
if 'user_gender' not in st.session_state: st.session_state.user_gender = "Bạn"
if 'stage' not in st.session_state: st.session_state.stage = "AUTH"
if 'theme' not in st.session_state:
    st.session_state.theme = {"mode": "dark", "primary_color": "#00f2ff", "bg_url": ""}
if 'chat_library' not in st.session_state: st.session_state.chat_library = {}
if 'current_chat' not in st.session_state: st.session_state.current_chat = None
if 'dynamic_hints' not in st.session_state: st.session_state.dynamic_hints = ["Nexus là ai?", "Giúp tôi học tập", "Kể chuyện"]

def nav(p): st.session_state.stage = p

# --- 2. CSS ENGINE (ĐẶC BIỆT: LIGHT MODE CHO AUTH) ---
def apply_ui(force_light=False):
    t = st.session_state.theme
    is_dark = t['mode'] == "dark" and not force_light
    
    bg = f"background-image: url('{t['bg_url']}'); background-size: cover;" if (t['bg_url'] and not force_light) else ""
    app_bg = "#ffffff" if (not is_dark) else "#000000"
    txt = "#1a1a1a" if (not is_dark) else "#ffffff"
    card_bg = "rgba(240, 240, 240, 0.9)" if (not is_dark) else "rgba(30, 30, 30, 0.8)"
    
    st.markdown(f"""
    <style>
    .stApp {{ background: {app_bg}; {bg} background-attachment: fixed; color: {txt}; }}
    
    /* NÚT BẤM */
    div.stButton > button {{
        width: 100% !important; border-radius: 12px !important;
        background: {card_bg} !important; color: {txt} !important;
        border: 1px solid #ddd !important; font-weight: 700 !important;
        padding: 10px !important; transition: 0.2s;
    }}
    div.stButton > button:active {{
        border-color: {t['primary_color']} !important;
        box-shadow: 0 0 20px {t['primary_color']} !important;
    }}

    /* AI CHAT BUBBLE */
    div[data-testid="stChatMessageAssistant"] {{
        background: #FFFFFF !important; border-radius: 15px !important;
        padding: 20px !important; border-left: 6px solid {t['primary_color']} !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }}
    div[data-testid="stChatMessageAssistant"] * {{ color: #000000 !important; }}

    /* NÚT XÓA MINI */
    .delete-btn {{ color: #ff4b4b !important; font-size: 0.8rem; cursor: pointer; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI AI ---
def get_nexus_response(messages):
    client = OpenAI(api_key=ACTIVE_KEY, base_url="https://api.groq.com/openai/v1")
    sys_prompt = f"Bạn là Nexus OS, AI của {CREATOR_NAME}. Xưng hô với người dùng là {st.session_state.user_gender}. Trả lời thông minh, không lặp lại."
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": sys_prompt}] + messages,
        temperature=0.8, stream=True
    )

# --- 4. CÁC MÀN HÌNH ---

def screen_auth():
    apply_ui(force_light=True) # Luôn để giao diện sáng ở khởi động
    st.markdown("<h1 style='text-align:center; color:#1a1a1a;'>NEXUS OS GATEWAY</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#555;'>Created by {CREATOR_NAME}</p>", unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký", "👤 Khách"])
    with t1:
        u = st.text_input("Tài khoản", key="l_u")
        p = st.text_input("Mật khẩu", type="password", key="l_p")
        if st.button("TRUY CẬP"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status, st.session_state.logged_in_user = "User", u
                nav("MENU"); st.rerun()
            else: st.error("Thông tin không chính xác.")
    with t2:
        nu = st.text_input("Username mới")
        np = st.text_input("Mật khẩu mới", type="password")
        gen = st.selectbox("Giới tính:", ["Nam", "Nữ", "Khác"])
        if st.button("XÁC NHẬN ĐĂNG KÝ"):
            st.session_state.users[nu] = np
            st.session_state.user_gender = gen
            st.success("Đã đăng ký!"); time.sleep(0.5)
    with t3:
        if st.button("TIẾP TỤC VỚI GUEST"):
            st.session_state.auth_status, st.session_state.logged_in_user = "Guest", "Guest"
            nav("MENU"); st.rerun()

def screen_chat():
    apply_ui()
    with st.sidebar:
        st.header("📂 Thư viện Chat")
        if st.button("➕ PHIÊN MỚI"): st.session_state.current_chat = None; st.rerun()
        st.write("---")
        
        # Danh sách chat với tính năng Xóa
        for title in list(st.session_state.chat_library.keys()):
            col_t, col_d = st.columns([0.8, 0.2])
            with col_t:
                if st.button(f"📄 {title[:15]}", key=f"chat_{title}"):
                    st.session_state.current_chat = title; st.rerun()
            with col_d:
                if st.button("❌", key=f"del_{title}"):
                    del st.session_state.chat_library[title]
                    if st.session_state.current_chat == title: st.session_state.current_chat = None
                    st.rerun()
        st.write("---")
        st.button("🏠 MENU", on_click=nav, args=("MENU",))

    # Giao diện Chat chính
    if st.session_state.current_chat:
        st.subheader(f"📍 {st.session_state.current_chat}")
        history = st.session_state.chat_library[st.session_state.current_chat]
    else:
        st.info("Hãy bắt đầu một câu hỏi để tạo phiên chat mới.")
        history = []

    for m in history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Hỏi Nexus..."):
        if not st.session_state.current_chat:
            # Tự động đặt tên
            st.session_state.current_chat = prompt[:20] + "..." if len(prompt)>20 else prompt
            st.session_state.chat_library[st.session_state.current_chat] = []
            history = st.session_state.chat_library[st.session_state.current_chat]
        
        history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            box = st.empty(); full = ""
            for chunk in get_nexus_response(history):
                c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                if c:
                    full += c
                    box.markdown(full + "▌")
            box.markdown(full)
            history.append({"role": "assistant", "content": full})
            st.session_state.chat_library[st.session_state.current_chat] = history
            st.rerun()

def screen_storage():
    apply_ui()
    st.title("📂 QUẢN LÝ TẢI XUỐNG")
    
    if not st.session_state.chat_library:
        st.warning("Không có cuộc trò chuyện nào để tải.")
    else:
        # Chọn cuộc trò chuyện cụ thể
        options = ["Tất cả"] + list(st.session_state.chat_library.keys())
        selected = st.selectbox("Chọn cuộc trò chuyện muốn tải:", options)
        
        if st.button("CHUẨN BỊ FILE"):
            data = st.session_state.chat_library if selected == "Tất cả" else {selected: st.session_state.chat_library[selected]}
            enc = base64.b64encode(json.dumps(data).encode()).decode()
            st.download_button(f"💾 TẢI {selected.upper()}", data=enc, file_name=f"nexus_{selected}.txt")
            
    st.button("🔙 QUAY LẠI", on_click=nav, args=("MENU",))

# --- CÁC MÀN HÌNH CÒN LẠI (GIỮ NGUYÊN LOGIC) ---
def screen_menu():
    apply_ui(); st.markdown(f"### 🚀 Dashboard | {st.session_state.logged_in_user}")
    c = st.columns(2)
    with c[0]: st.button("🧠 CHAT AI", on_click=nav, args=("CHAT",))
    with c[0]: st.button("📂 LƯU TRỮ", on_click=nav, args=("STORAGE",))
    with c[1]: st.button("🎨 GIAO DIỆN", on_click=nav, args=("SETTINGS",))
    with c[1]: st.button("⚙️ THÔNG TIN", on_click=nav, args=("INFO",))
    st.button("🚪 ĐĂNG XUẤT", on_click=nav, args=("AUTH",))

def screen_settings():
    apply_ui(); st.title("🎨 CÀI ĐẶT")
    st.session_state.theme['mode'] = st.radio("Chủ đề:", ["dark", "light"])
    st.session_state.theme['primary_color'] = st.color_picker("Màu chủ đạo:", st.session_state.theme['primary_color'])
    st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền:", st.session_state.theme['bg_url'])
    st.button("✅ LƯU", on_click=nav, args=("MENU",))

def screen_info():
    apply_ui(); st.title("⚙️ INFO")
    st.write(f"Sản phẩm của: **{CREATOR_NAME}**")
    st.write(f"Phiên bản: {VERSION}")
    st.button("🔙 QUAY LẠI", on_click=nav, args=("MENU",))

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "STORAGE": screen_storage()
elif st.session_state.stage == "SETTINGS": screen_settings()
elif st.session_state.stage == "INFO": screen_info()
