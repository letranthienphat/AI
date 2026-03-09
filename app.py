# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random
from datetime import datetime
import streamlit_javascript as st_js
from user_agents import parse
import pandas as pd

# -------------------- [1] CẤU HÌNH HỆ THỐNG --------------------
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V5100"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

CHANGELOG = {
    "V5100": "• Giao diện Deep Black & White Neon.\n• Fix lỗi AttributeError tại User Agent.\n• Hệ thống Gateway mượt mà hơn."
}

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except Exception as e:
    st.error(f"Thiếu Secrets: {e}")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {VERSION}", layout="wide", initial_sidebar_state="collapsed")

# -------------------- [2] TIỆN ÍCH --------------------
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
    data = {
        "users": st.session_state.users,
        "user_versions": st.session_state.user_versions,
        "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library,
        "friends": st.session_state.friends,
        "friend_requests": st.session_state.friend_requests,
        "groups": st.session_state.groups,
        "p2p_chats": st.session_state.p2p_chats,
        "agreed_users": st.session_state.agreed_users,
        "login_history": st.session_state.login_history,
        "total_messages": st.session_state.total_messages
    }
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode()).decode()
        payload = {"message": f"Nexus Sync {VERSION}", "content": content, "sha": sha}
        requests.put(url, headers=headers, json=payload)
    except: pass

# -------------------- [3] KHỞI TẠO --------------------
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123", "Thiên Phát": "123"})
    st.session_state.user_versions = db.get("user_versions", {})
    st.session_state.theme = db.get("theme", {"primary_color": "#ffffff", "bg_url": ""})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.friends = db.get("friends", {})
    st.session_state.friend_requests = db.get("friend_requests", {})
    st.session_state.groups = db.get("groups", {})
    st.session_state.p2p_chats = db.get("p2p_chats", {})
    st.session_state.agreed_users = db.get("agreed_users", [])
    st.session_state.login_history = db.get("login_history", [])
    st.session_state.total_messages = db.get("total_messages", 0)
    st.session_state.stage = "GATEWAY"
    st.session_state.auth_status = None
    st.session_state.initialized = True

# -------------------- [4] GIAO DIỆN DARK MODE --------------------
def apply_ui():
    p_color = "#ffffff" # Màu chủ đạo trắng neon
    st.markdown(f"""
    <style>
    /* Nền đen hoàn toàn */
    .stApp {{
        background-color: #000000 !important;
    }}
    
    /* Chữ trắng và hiệu ứng Glow */
    h1, h2, h3, p, label, span, div, .stMarkdown p {{
        color: #ffffff !important;
        text-shadow: 0 0 8px rgba(255,255,255,0.6) !important;
    }}

    /* Khung trong suốt mờ */
    .glass-panel, [data-testid="stSidebar"], [data-testid="stChatMessage"] {{
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 15px !important;
    }}

    /* Nút bấm */
    .stButton > button {{
        border: 1px solid #ffffff !important;
        background: transparent !important;
        color: #ffffff !important;
        transition: 0.4s;
    }}
    .stButton > button:hover {{
        background: #ffffff !important;
        color: #000000 !important;
        box-shadow: 0 0 15px #ffffff;
    }}

    /* Gateway Animation */
    .gateway-wrapper {{
        display: flex; flex-direction: column; align-items: center; justify-content: center; height: 80vh;
    }}
    .nexus-logo {{
        width: 80px; height: 80px; border: 2px solid #ffffff;
        animation: rotate 6s linear infinite, glow 2s ease-in-out infinite;
    }}
    @keyframes rotate {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
    @keyframes glow {{ 0%, 100% {{ box-shadow: 0 0 10px #ffffff; }} 50% {{ box-shadow: 0 0 30px #ffffff; }} }}
    </style>
    """, unsafe_allow_html=True)

# -------------------- [5] MÀN HÌNH --------------------
def screen_gateway():
    apply_ui()
    st.markdown("""
    <div class="gateway-wrapper">
        <div class="nexus-logo"></div>
        <h1 style="letter-spacing: 10px; margin-top: 25px;">NEXUS GATEWAY</h1>
        <p style="opacity: 0.5;">AUTHENTICATING SYSTEM...</p>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(3)
    st.session_state.stage = "AUTH"
    st.rerun()

def screen_auth():
    apply_ui()
    st.markdown("<h1 style='text-align:center;'>🛡️ NEXUS OS LOGIN</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("ACCESS SYSTEM", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                with st.spinner("🚀 Verifying Gateway..."):
                    # FIX LỖI ATTRIBUTE ERROR: Kiểm tra sự tồn tại của st_js
                    try:
                        ua = st_js.get_user_agent()
                    except:
                        ua = "Unknown Device"
                    
                    st.session_state.auth_status = u
                    if u not in st.session_state.user_versions:
                        st.session_state.user_versions[u] = VERSION
                    save_github()
                    st.session_state.stage = "MENU"
                    st.rerun()
            else: st.error("Invalid Credentials")
        st.markdown('</div>', unsafe_allow_html=True)

def screen_menu():
    apply_ui()
    user = st.session_state.auth_status
    user_ver = st.session_state.user_versions.get(user, "V0")
    
    st.markdown(f"<h1 style='text-align:center;'>🚀 CENTER</h1>", unsafe_allow_html=True)
    
    # Thông báo cập nhật
    if user_ver != VERSION:
        st.warning(f"NEW UPDATE AVAILABLE: {VERSION}")
        if st.button("UPGRADE NOW"):
            st.session_state.user_versions[user] = VERSION
            save_github(); st.rerun()

    st.write(f"<p style='text-align:center;'>User: {user} | Ver: {user_ver}</p>", unsafe_allow_html=True)
    
    cols = st.columns(4)
    if cols[0].button("🧠 AI CHAT", use_container_width=True): st.session_state.stage = "CHAT"; st.rerun()
    if cols[1].button("🌐 SOCIAL", use_container_width=True): st.session_state.stage = "SOCIAL"; st.rerun()
    if cols[2].button("⚙️ SETTINGS", use_container_width=True): st.session_state.stage = "SETTINGS"; st.rerun()
    if cols[3].button("🚪 EXIT", use_container_width=True): 
        st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()

# -------------------- [6] ĐIỀU HƯỚNG --------------------
def main():
    if st.session_state.stage == "GATEWAY": screen_gateway()
    elif st.session_state.stage == "AUTH": screen_auth()
    elif st.session_state.stage == "MENU": screen_menu()
    elif st.session_state.stage == "CHAT": st.write("Màn hình Chat AI đang mở...") # Thay bằng hàm chat của anh

if __name__ == "__main__":
    main()
