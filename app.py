# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json

# --- 1. KHỞI TẠO HỆ THỐNG ---
st.set_page_config(page_title="NEXUS V2600", layout="wide")

# Cấu hình chủ nhân
CREATOR_NAME = "Lê Trần Thiên Phát"

# Khởi tạo các biến hệ thống trong Session State
if 'users' not in st.session_state: st.session_state.users = {"admin": "123"} # Demo đơn giản
if 'auth_status' not in st.session_state: st.session_state.auth_status = None # None, "User", "Guest"
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = ""
if 'stage' not in st.session_state: st.session_state.stage = "AUTH"

# Cấu hình giao diện cá nhân
if 'theme' not in st.session_state:
    st.session_state.theme = {
        "mode": "dark",
        "primary_color": "#00f2ff",
        "bg_url": ""
    }

# Quản lý Chat: { "Tên chat": [log_list] }
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
    .stApp {{
        background: {app_bg};
        {bg_style}
        background-attachment: fixed;
        color: {text_color};
    }}
    
    /* PLASMA GLOW BUTTONS */
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

    /* AI RESPONSE BUBBLE (HIGH CONTRAST) */
    div[data-testid="stChatMessageAssistant"] {{
        background: #FFFFFF !important; border-radius: 20px !important;
        padding: 20px !important; border: 2px solid {theme['primary_color']} !important;
    }}
    div[data-testid="stChatMessageAssistant"] * {{ color: #000000 !important; font-weight: 500; }}
    
    /* INPUT FIELD */
    .stTextInput input {{ background: {card_bg} !important; color: {text_color} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. MÀN HÌNH CHỨC NĂNG ---

def screen_auth():
    apply_custom_ui()
    st.markdown("<h1 style='text-align:center;'>NEXUS AUTH GATEWAY</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký", "👤 Khách"])
    
    with tab1:
        u = st.text_input("Tên đăng nhập", key="login_u")
        p = st.text_input("Mật khẩu", type="password", key="login_p")
        if st.button("XÁC THỰC"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = "User"; st.session_state.logged_in_user = u
                nav("MENU"); st.rerun()
            else: st.error("Sai thông tin!")
            
    with tab2:
        nu = st.text_input("Tạo tên đăng nhập")
        np = st.text_input("Tạo mật khẩu", type="password")
        if st.button("TẠO TÀI KHOẢN"):
            st.session_state.users[nu] = np; st.success("Đã đăng ký!"); time.sleep(1)
            
    with tab3:
        st.info("Chế độ khách: Dữ liệu sẽ không được lưu sau khi thoát.")
        if st.button("VÀO VỚI TƯ CÁCH KHÁCH"):
            st.session_state.auth_status = "Guest"; st.session_state.logged_in_user = "Guest"
            nav("MENU"); st.rerun()

def screen_menu():
    apply_custom_ui()
    st.markdown(f"### Chào mừng, {st.session_state.logged_in_user}")
    cols = st.columns(2)
    with cols[0]:
        st.button("💬 BẮT ĐẦU CHAT", on_click=nav, args=("CHAT",))
        st.button("📂 QUẢN LÝ DỮ LIỆU", on_click=nav, args=("STORAGE",))
    with cols[1]:
        st.button("🎨 TÙY CHỈNH GIAO DIỆN", on_click=nav, args=("SETTINGS",))
        st.button("⚙️ THÔNG TIN HỆ THỐNG", on_click=nav, args=("INFO",))
    st.button("🚪 ĐĂNG XUẤT", on_click=nav, args=("AUTH",))

def screen_settings():
    apply_custom_ui()
    st.title("🎨 CUSTOM ENGINE")
    st.session_state.theme['mode'] = st.radio("Chế độ hiển thị:", ["dark", "light"], index=0 if st.session_state.theme['mode']=="dark" else 1)
    st.session_state.theme['primary_color'] = st.color_picker("Chọn màu chủ đề:", st.session_state.theme['primary_color'])
    st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền (URL):", st.session_state.theme['bg_url'])
    if st.button("LƯU CẤU HÌNH"): nav("MENU"); st.rerun()

def screen_chat():
    apply_custom_ui()
    # Sidebar quản lý tên cuộc trò chuyện
    with st.sidebar:
        st.header("📚 Thư viện Chat")
        new_name = st.text_input("Tạo cuộc trò chuyện mới:")
        if st.button("➕ Thêm mới"):
            if new_name:
                st.session_state.chat_library[new_name] = []
                st.session_state.current_chat = new_name; st.rerun()
        
        st.write("---")
        for title in list(st.session_state.chat_library.keys()):
            if st.button(f"📄 {title}", key=f"btn_{title}"):
                st.session_state.current_chat = title; st.rerun()

    st.subheader(f"📍 Đang chat: {st.session_state.current_chat}")
    
    current_log = st.session_state.chat_library[st.session_state.current_chat]
    for m in current_log:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Nhập lệnh..."):
        current_log.append({"role": "user", "content": prompt})
        st.rerun()

    if current_log and current_log[-1]["role"] == "user":
        with st.chat_message("assistant"):
            box = st.empty(); full = ""
            # Giả lập AI Call (Sử dụng Groq/OpenAI của bạn ở đây)
            # ... (Phần call AI giữ nguyên như bản V2500)
            full = "Đây là phản hồi chuyên nghiệp từ Nexus V2600 dành cho anh ấy."
            for char in full:
                box.markdown(full[:full.find(char)+1] + "▌"); time.sleep(0.01)
            box.markdown(full)
            current_log.append({"role": "assistant", "content": full})
            st.rerun()

    st.button("🏠 VỀ MENU", on_click=nav, args=("MENU",))

def screen_storage():
    apply_ui = apply_custom_ui()
    st.title("📂 QUẢN LÝ XUẤT DỮ LIỆU")
    
    option = st.selectbox("Chọn nội dung muốn xuất:", ["Toàn bộ hệ thống", "Chỉ cuộc trò chuyện hiện tại"])
    
    if st.button("CHUẨN BỊ FILE XUẤT"):
        data_to_export = st.session_state.chat_library if option == "Toàn bộ hệ thống" else {st.session_state.current_chat: st.session_state.chat_library[st.session_state.current_chat]}
        encoded = base64.b64encode(json.dumps(data_to_export).encode()).decode()
        st.download_button("TẢI VỀ FILE .TXT MÃ HÓA", data=encoded, file_name=f"nexus_export_{st.session_state.logged_in_user}.txt")
    
    st.button("🏠 QUAY LẠI", on_click=nav, args=("MENU",))

def screen_info():
    apply_custom_ui()
    st.title("⚙️ THÔNG TIN & ĐIỀU KHOẢN")
    t1, t2, t3 = st.tabs(["👤 Người sáng tạo", "📊 Phiên bản", "📜 Điều khoản"])
    with t1: st.write(f"Được thiết kế bởi: **{CREATOR_NAME}** (7A1 Nguyễn Huệ)")
    with t2: st.write(f"Phiên bản: {VERSION} | Nebula Custom Engine")
    with t3: st.write("Điều khoản: Hài hước nhưng đàng hoàng. Không nhận vơ, không quậy phá!")
    
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.write(f"Sản phẩm của **{CREATOR_NAME}**")
    st.button("🏠 VỀ MENU", on_click=nav, args=("MENU",))

# --- 4. ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "SETTINGS": screen_settings()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "STORAGE": screen_storage()
elif st.session_state.stage == "INFO": screen_info()
