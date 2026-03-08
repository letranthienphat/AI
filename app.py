# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests
from streamlit_javascript import st_javascript

# --- 1. CẤU HÌNH ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V3550 - CONTRAST FIX"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
    FILE_DATA = "data.json"
except:
    st.error("Thiếu Secrets!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. HÀM PHỤ TRỢ ---
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

# --- 4. TÍNH NĂNG TƯƠNG PHẢN TỰ ĐỘNG ---
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
                const brightness = (r*0.299 + g*0.587 + b*0.114);
                return brightness > 128 ? 'light' : 'dark';
            }}).catch(() => 'dark');
        """
        result = st_javascript(js_code)
        if result and result in ['light', 'dark']:
            if result != st.session_state.theme.get('bg_tone'):
                st.session_state.theme['bg_tone'] = result

# --- 5. LÕI GIAO DIỆN (FIX CHỮ ĐEN) ---
def apply_ui(force_light=False):
    t = st.session_state.theme
    tone = 'light' if force_light else t.get('bg_tone', 'dark')
    
    # Ép màu chữ dựa trên tông nền
    txt_color = "#000000" if tone == 'light' else "#ffffff"
    app_bg = "#ffffff" if (force_light or t['mode'] == 'light') else "#0e1117"
    card_bg = "rgba(255,255,255,0.8)" if tone == 'light' else "rgba(0,0,0,0.8)"
    
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if (t['bg_url'] and not force_light) else ""

    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} background-color: {app_bg}; }}
    
    /* Ép tất cả các thẻ văn bản phải theo màu txt_color */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, .stMarkdown p {{
        color: {txt_color} !important;
    }}
    
    /* Khung nội dung Điều khoản và Chat */
    .terms-box, div[data-testid="stChatMessageAssistant"], div[data-testid="stChatMessageUser"] {{
        background-color: {card_bg} !important;
        border-radius: 15px;
        padding: 20px;
        border-left: 5px solid {t['primary_color']} !important;
        backdrop-filter: blur(10px);
    }}

    div.stButton > button {{
        border: 2px solid {t['primary_color']} !important;
        background: {card_bg} !important; color: {txt_color} !important;
        font-weight: bold;
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{ background-color: {card_bg} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. CÁC MÀN HÌNH ---
def screen_auth():
    apply_ui(force_light=True) # Màn hình login luôn sáng để dễ nhìn
    st.title("🛡️ NEXUS OS GATEWAY")
    u = st.text_input("Username", key="u_login")
    p = st.text_input("Password", type="password", key="p_login")
    if st.button("TRUY CẬP"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.auth_status = u
            st.session_state.stage = "MENU" if u in st.session_state.agreed_users else "TERMS"
            st.rerun()
        else: st.error("Sai tài khoản!")

def screen_terms():
    detect_ui_tone() # Kích hoạt nhận diện màu ngay tại đây
    apply_ui()
    st.title("📜 ĐIỀU KHOẢN SỬ DỤNG")
    
    # Dùng div để bao bọc nội dung giúp dễ áp dụng CSS
    st.markdown(f"""
    <div class="terms-box">
        <h3>Chào mừng {st.session_state.auth_status.upper()}</h3>
        <p>Để tiếp tục sử dụng Nexus OS, bạn cần đồng ý với các điều khoản sau:</p>
        <ul>
            <li>Hệ thống AI được vận hành bởi công nghệ của {CREATOR_NAME}.</li>
            <li>Dữ liệu cá nhân và lịch sử chat được đồng bộ hóa bảo mật.</li>
            <li>Vui lòng không sử dụng AI cho các mục đích vi phạm cộng đồng.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    agree = st.checkbox("Tôi xác nhận đã đọc và đồng ý với điều khoản.")
    if agree and st.button("BẮT ĐẦU TRẢI NGHIỆM"):
        if st.session_state.auth_status != "Guest":
            if st.session_state.auth_status not in st.session_state.agreed_users:
                st.session_state.agreed_users.append(st.session_state.auth_status)
                save_github()
        st.session_state.stage = "MENU"; st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "TERMS": screen_terms()
elif st.session_state.stage == "MENU":
    detect_ui_tone()
    apply_ui()
    st.title(f"🚀 GIAO DIỆN CHÍNH")
    if st.button("🧠 AI CHAT"): st.session_state.stage = "CHAT"; st.rerun()
    if st.button("🎨 CÀI ĐẶT"): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT"): st.session_state.stage = "AUTH"; st.rerun()
