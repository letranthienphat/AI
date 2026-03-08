# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests
from streamlit_javascript import st_javascript

# --- 1. CẤU HÌNH HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V3500 - STABILITY PRO"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
    FILE_DATA = "data.json"
except:
    st.error("Lỗi: Thiếu cấu hình Secrets trên Streamlit Cloud!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. HỆ THỐNG GITHUB ---
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
        payload = {"message": "Sync", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- 3. KHỞI TẠO ---
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123"})
    st.session_state.theme = db.get("theme", {"mode": "dark", "primary_color": "#00f2ff", "bg_url": "", "bg_tone": "dark"})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.agreed_users = db.get("agreed_users", [])
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.initialized = True

# --- 4. AUTO-VISION (SMART SENSOR) ---
def detect_ui_tone():
    if st.session_state.theme.get('bg_url'):
        js_code = f"""
        fetch("{st.session_state.theme['bg_url']}")
            .then(res => res.blob())
            .then(createImageBitmap)
            .then(img => {{
                const cvs = document.createElement('canvas');
                const ctx = cvs.getContext('2d');
                cvs.width = 1; cvs.height = 1;
                ctx.drawImage(img, 0, 0, 1, 1);
                const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
                return (r*0.299 + g*0.587 + b*0.114) > 128 ? 'light' : 'dark';
            }}).catch(() => 'dark');
        """
        result = st_javascript(js_code)
        if result and result in ['light', 'dark']:
            if result != st.session_state.theme.get('bg_tone'):
                st.session_state.theme['bg_tone'] = result

# --- 5. UI ENGINE ---
def apply_ui(force_light=False):
    t = st.session_state.theme
    tone = 'light' if force_light else t.get('bg_tone', 'dark')
    txt = "#000000" if tone == 'light' else "#ffffff"
    app_bg = "#ffffff" if force_light or t['mode'] == 'light' else "#0e1117"
    card_bg = "rgba(255,255,255,0.7)" if tone == 'light' else "rgba(0,0,0,0.7)"
    
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if (t['bg_url'] and not force_light) else ""

    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} background-color: {app_bg}; }}
    * {{ color: {txt} !important; }}
    div.stButton > button {{
        width: 100%; border-radius: 12px; font-weight: bold;
        border: 2px solid {t['primary_color']} !important;
        background: {card_bg} !important; backdrop-filter: blur(10px);
    }}
    div[data-testid="stChatMessageAssistant"], div[data-testid="stChatMessageUser"] {{
        background-color: {card_bg} !important; border-left: 5px solid {t['primary_color']} !important;
        backdrop-filter: blur(10px); border-radius: 15px;
    }}
    [data-testid="stSidebar"] {{ background-color: {card_bg} !important; }}
    input {{ color: black !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. MÀN HÌNH ---
def screen_auth():
    apply_ui(force_light=True)
    st.title("🛡️ NEXUS OS GATEWAY")
    tab1, tab2, tab3 = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký", "👤 Khách"])
    with tab1:
        u = st.text_input("Username", key="u_in")
        p = st.text_input("Password", type="password", key="p_in")
        if st.button("TRUY CẬP HỆ THỐNG", key="btn_login"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU" if u in st.session_state.agreed_users else "TERMS"
                st.rerun()
            else: st.error("Sai thông tin!")
    with tab3:
        if st.button("VÀO QUYỀN KHÁCH", key="btn_guest"):
            st.session_state.auth_status = "Guest"; st.session_state.stage = "TERMS"; st.rerun()

def screen_terms():
    apply_ui()
    st.title("📜 ĐIỀU KHOẢN")
    st.write(f"Hệ điều hành Nexus OS - Tác giả: {CREATOR_NAME}")
    st.markdown("1. Dữ liệu được bảo mật.\n2. Không vi phạm pháp luật.")
    agree = st.checkbox("Đã đọc và đồng ý")
    if agree and st.button("XÁC NHẬN"):
        if st.session_state.auth_status != "Guest":
            if st.session_state.auth_status not in st.session_state.agreed_users:
                st.session_state.agreed_users.append(st.session_state.auth_status)
                save_github()
        st.session_state.stage = "MENU"; st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "TERMS": screen_terms()
elif st.session_state.stage == "MENU":
    detect_ui_tone() # Chạy ngầm
    apply_ui()
    st.title(f"🚀 CHÀO {st.session_state.auth_status.upper()}")
    if st.button("🧠 KẾT NỐI AI"): st.session_state.stage = "CHAT"; st.rerun()
    if st.button("🎨 CÀI ĐẶT"): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT"): st.session_state.stage = "AUTH"; st.rerun()
elif st.session_state.stage == "SETTINGS":
    apply_ui()
    st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền:", st.session_state.theme['bg_url'])
    if st.button("LƯU"): save_github(); st.session_state.stage = "MENU"; st.rerun()
