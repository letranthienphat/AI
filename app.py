# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V4400 - GLOW & ALIGN FIX"
FILE_DATA = "data.json"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("Thiếu cấu hình Secrets!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. HỆ THỐNG BẢO MẬT ---
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

def encrypt_msg(text):
    if not text: return text
    encoded = "".join([chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(text)])
    return base64.b64encode(encoded.encode()).decode()

def decrypt_msg(text):
    if not text: return text
    try:
        decoded = base64.b64decode(text.encode()).decode()
        return "".join([chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(decoded)])
    except: return text

# --- 3. ĐỒNG BỘ GITHUB ---
def load_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except: pass
    return {}

def save_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    data = {
        "users": st.session_state.users,
        "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library,
        "agreed_users": st.session_state.agreed_users,
        "friends": st.session_state.get('friends', {}),
        "friend_requests": st.session_state.get('friend_requests', {}),
        "groups": st.session_state.get('groups', {}),
        "p2p_chats": st.session_state.get('p2p_chats', {})
    }
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": "Nexus Sync", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- 4. KHỞI TẠO BIẾN (FIX LỖI CRASH) ---
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123"})
    st.session_state.theme = db.get("theme", {
        "primary_color": "#00f2ff", "bg_url": "", "use_glass": True,
        "auto_wallpaper": False, "wp_interval": 1440, "last_wp_update": 0
    })
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.agreed_users = db.get("agreed_users", [])
    
    # KHAI BÁO CÁC BIẾN TRÁNH LỖI ATTRIBUTEERROR
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None # Đã thêm để sửa lỗi
    st.session_state.confirm_delete = None
    st.session_state.initialized = True

# --- 5. ENGINE GIAO DIỆN ---
def apply_ui():
    t = st.session_state.theme
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] else "background-color: #0e1117;"
    
    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} }}
    
    /* HIỆU ỨNG GLOW CHO TẤT CẢ CHỮ */
    .stApp p, .stApp span, .stApp label, h1, h2, h3, h4, .stMarkdown p {{
        color: #000000 !important;
        font-weight: 700 !important;
        text-shadow: 1px 1px 3px rgba(255, 255, 255, 0.5), 0px 0px 5px {t['primary_color']}44 !important;
    }}
    
    .main-title, .glow-text {{
        color: {t['primary_color']} !important;
        text-shadow: 0px 0px 15px {t['primary_color']} !important;
        text-transform: uppercase;
    }}

    .glass-card, [data-testid="stSidebar"], .stTabs {{
        background: rgba(255, 255, 255, 0.45) !important;
        backdrop-filter: blur(12px) !important;
        border-radius: 15px; padding: 20px;
    }}

    /* FIX NÚT BẤM VÀ CĂN CHỈNH THÙNG RÁC SIDEBAR */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: row"] {{
        align-items: center !important;
    }}

    [data-testid="stSidebar"] div.stButton > button {{
        white-space: normal !important;
        height: auto !important;
        text-align: left !important;
        padding: 8px 12px !important;
        line-height: 1.2 !important;
        display: flex; align-items: center;
    }}

    div.stButton > button {{
        width: 100%; border-radius: 10px; font-weight: 800;
        border: 2px solid {t['primary_color']} !important;
        background: rgba(255,255,255,0.8) !important; color: #000000 !important;
    }}
    div.stButton > button:hover {{ background: {t['primary_color']} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. MÀN HÌNH CHỨC NĂNG ---

def screen_auth():
    apply_ui()
    st.markdown('<h1 class="main-title">🛡️ NEXUS OS GATEWAY</h1>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        u = st.text_input("Tên tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("ĐĂNG NHẬP"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU"; st.rerun()
            else: st.error("Sai thông tin!")
        st.markdown('</div>', unsafe_allow_html=True)

def screen_chat():
    apply_ui()
    user = st.session_state.auth_status
    lib = st.session_state.chat_library.setdefault(user, {})

    with st.sidebar:
        st.markdown(f'<h2 class="glow-text">📂 THƯ VIỆN</h2>', unsafe_allow_html=True)
        if st.button("➕ CHAT MỚI"): st.session_state.current_chat = None; st.rerun()
        st.write("---")
        
        for title in list(lib.keys()):
            # Sử dụng cột để căn chỉnh thùng rác ngay ngắn
            c_btn, c_del = st.columns([0.8, 0.2])
            with c_btn:
                if st.button(f"📄 {title}", key=f"btn_{title}"):
                    st.session_state.current_chat = title; st.rerun()
            with c_del:
                if st.session_state.confirm_delete == title:
                    if st.button("✔️", key=f"y_{title}"):
                        del lib[title]; st.session_state.confirm_delete = None; save_github(); st.rerun()
                else:
                    if st.button("🗑️", key=f"d_{title}"):
                        st.session_state.confirm_delete = title; st.rerun()
        
        st.write("---")
        if st.button("🏠 VỀ MENU"): st.session_state.stage = "MENU"; st.rerun()

    st.write(f"Đang làm việc tại: **{st.session_state.current_chat or 'Phiên chat mới'}**")
    # ... logic chat AI ...

def screen_settings():
    apply_ui()
    st.markdown('<h1 class="main-title">⚙️ CÀI ĐẶT HỆ THỐNG</h1>', unsafe_allow_html=True)
    user = st.session_state.auth_status
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="glow-text">👤 Tên đăng nhập</h3>', unsafe_allow_html=True)
        st.text_input("Tên hiện tại:", value=user, disabled=True)
        
        st.write("---")
        st.markdown('<h3 class="glow-text">🔐 Đổi mật khẩu</h3>', unsafe_allow_html=True)
        # Các nhãn này giờ sẽ có bóng mờ nhờ CSS mới
        old_p = st.text_input("Nhập mật khẩu cũ:", type="password")
        new_p = st.text_input("Nhập mật khẩu mới:", type="password")
        if st.button("LƯU MẬT KHẨU"):
            if st.session_state.users[user] == old_p:
                st.session_state.users[user] = new_p; save_github(); st.success("Đã đổi!")
            else: st.error("Sai mật khẩu cũ!")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="glow-text">🎨 Giao diện</h3>', unsafe_allow_html=True)
        st.session_state.theme['primary_color'] = st.color_picker("Màu Neon chủ đạo:", st.session_state.theme['primary_color'])
        st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền:", st.session_state.theme['bg_url'])
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🔙 QUAY LẠI MENU"): st.session_state.stage = "MENU"; st.rerun()

# --- 7. ĐIỀU HƯỚNG TỔNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "MENU":
    apply_ui()
    st.markdown('<h1 class="main-title">🚀 NEXUS MENU</h1>', unsafe_allow_html=True)
    if st.button("🧠 AI CHAT"): st.session_state.stage = "CHAT"; st.rerun()
    if st.button("⚙️ SETTINGS"): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.button("🚪 LOGOUT"): st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "SETTINGS": screen_settings()
