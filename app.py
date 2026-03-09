# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V4000 - ULTIMATE CONTROL"
FILE_DATA = "data.json"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("Thiếu cấu hình Secrets!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. ĐỒNG BỘ GITHUB ---
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
        "agreed_users": st.session_state.get('agreed_users', [])
    }
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": f"Nexus Update {time.strftime('%H:%M:%S')}", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- 3. KHỞI TẠO ---
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123"})
    st.session_state.theme = db.get("theme", {"primary_color": "#00f2ff", "bg_url": "", "use_glass": True})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.agreed_users = db.get("agreed_users", [])
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.initialized = True

# --- 4. ENGINE GIAO DIỆN TÙY BIẾN ---
def apply_ui():
    t = st.session_state.theme
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] else "background-color: #0e1117;"
    
    # Cấu hình lớp sương mờ
    glass_bg = "rgba(255, 255, 255, 0.4)" if t.get('use_glass', True) else "transparent"
    glass_blur = "blur(12px)" if t.get('use_glass', True) else "none"
    glass_border = "1px solid rgba(255, 255, 255, 0.3)" if t.get('use_glass', True) else "none"

    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} }}
    
    .main-title {{
        color: {t['primary_color']} !important;
        text-align: center; font-size: 2.8rem; font-weight: 900;
        text-shadow: 0px 0px 10px {t['primary_color']}; margin-bottom: 20px;
    }}

    .stApp p, .stApp span, .stApp label, .stMarkdown p, .stMarkdown li {{
        color: #000000 !important; font-weight: 600 !important;
    }}

    .glass-card, div[data-testid="stChatMessage"], [data-testid="stSidebar"], .stTabs {{
        background: {glass_bg} !important;
        backdrop-filter: {glass_blur} !important;
        border: {glass_border} !important;
        border-radius: 15px; padding: 15px;
    }}

    div.stButton > button {{
        width: 100%; border-radius: 10px; font-weight: 700;
        border: 2px solid {t['primary_color']} !important;
        background: rgba(255, 255, 255, 0.6) !important; color: #000000 !important;
    }}
    div.stButton > button:hover {{ background: {t['primary_color']} !important; color: #000000 !important; }}

    /* Sidebar text fix */
    [data-testid="stSidebarContent"] * {{ color: #000000 !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. SCREENS ---

def screen_auth():
    apply_ui()
    st.markdown('<h1 class="main-title">🛡️ NEXUS GATEWAY</h1>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["🔑 LOGIN", "📝 REGISTER", "👤 GUEST"])
    with t1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("TRUY CẬP"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU" if u in st.session_state.agreed_users else "TERMS"
                st.rerun()
    with t2:
        nu = st.text_input("Tên đăng ký", key="r_u")
        p1 = st.text_input("Mật khẩu", type="password", key="r_p1")
        p2 = st.text_input("Xác nhận lại", type="password", key="r_p2")
        if st.button("TẠO TÀI KHOẢN"):
            if p1 == p2 and nu != "":
                st.session_state.users[nu] = p1
                save_github(); st.success("Xong! Qua tab Login nhé.")

def screen_terms():
    apply_ui()
    st.markdown('<h1 class="main-title">📜 TERMS & INFO</h1>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="glass-card">
        <h3>Chào {st.session_state.auth_status.upper()} | Phiên bản: {VERSION}</h3>
        <p>• Tác giả: <b>{CREATOR_NAME}</b></p>
        <p>• Tính năng mới: Tùy chỉnh lớp sương, quản lý xóa chat.</p>
        <p>• Dữ liệu được mã hóa và bảo mật tuyệt đối.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.checkbox("Đồng ý với điều khoản") and st.button("VÀO HỆ THỐNG"):
        if st.session_state.auth_status != "Guest":
            st.session_state.agreed_users.append(st.session_state.auth_status)
            save_github()
        st.session_state.stage = "MENU"; st.rerun()

def screen_chat():
    apply_ui()
    with st.sidebar:
        st.header("📂 Library")
        if st.button("➕ NEW CHAT"): st.session_state.current_chat = None; st.rerun()
        st.write("---")
        # Danh sách chat kèm nút xóa
        for title in list(st.session_state.chat_library.keys()):
            col_t, col_d = st.columns([4, 1])
            with col_t:
                if st.button(f"📄 {title[:12]}", key=f"btn_{title}"):
                    st.session_state.current_chat = title; st.rerun()
            with col_d:
                if st.button("🗑️", key=f"del_{title}"):
                    del st.session_state.chat_library[title]
                    save_github(); st.rerun()
        st.write("---")
        if st.button("🏠 MENU"): st.session_state.stage = "MENU"; st.rerun()

    # Logic Chat giữ nguyên...
    # (Đoạn mã gọi API OpenAI/Groq giống bản trước)

def screen_settings():
    apply_ui()
    st.markdown('<h1 class="main-title">🎨 UI CUSTOMIZER</h1>', unsafe_allow_html=True)
    with st.container(border=True):
        st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền:", st.session_state.theme['bg_url'])
        st.session_state.theme['primary_color'] = st.color_picker("Màu chủ đạo (Buttons/Titles):", st.session_state.theme['primary_color'])
        st.session_state.theme['use_glass'] = st.toggle("Kích hoạt lớp sương mờ (Frosted Glass)", st.session_state.theme['use_glass'])
        
    if st.button("LƯU & ĐỒNG BỘ"):
        save_github(); st.success("Đã cập nhật!"); time.sleep(1); st.session_state.stage = "MENU"; st.rerun()
    if st.button("🔙 QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "TERMS": screen_terms()
elif st.session_state.stage == "MENU":
    apply_ui()
    st.markdown(f'<h1 class="main-title">🚀 NEXUS MENU</h1>', unsafe_allow_html=True)
    if st.button("🧠 AI CHAT"): st.session_state.stage = "CHAT"; st.rerun()
    if st.button("🎨 SETTINGS"): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.button("🚪 LOGOUT"): st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()
