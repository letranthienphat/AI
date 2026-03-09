# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V3900 - VISIBILITY FIX"
FILE_DATA = "data.json"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("Lỗi: Thiếu Secrets (GH_TOKEN, GH_REPO, GROQ_KEYS)!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. HỆ THỐNG GITHUB ---
def load_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            return json.loads(content)
    except: pass
    return {}

def save_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    master_data = {
        "users": st.session_state.users,
        "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library,
        "agreed_users": st.session_state.get('agreed_users', [])
    }
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(master_data, indent=4).encode()).decode()
        payload = {"message": f"Sync {time.strftime('%H:%M:%S')}", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- 3. KHỞI TẠO ---
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123"})
    st.session_state.theme = db.get("theme", {"primary_color": "#00f2ff", "bg_url": ""})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.agreed_users = db.get("agreed_users", [])
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None
    st.session_state.initialized = True

# --- 4. GIAO DIỆN CRYSTAL UI (FIX TÀNG HÌNH) ---
def apply_ui():
    t = st.session_state.theme
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] else "background-color: #0e1117;"
    
    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} }}
    
    /* TIÊU ĐỀ CHÍNH - PHẢI LUÔN SÁNG */
    .main-title {{
        color: {t['primary_color']} !important;
        text-align: center;
        font-size: 3rem;
        font-weight: 900;
        text-shadow: 0px 0px 15px {t['primary_color']};
        margin-bottom: 30px;
    }}

    /* CHỮ ĐEN TRONG CÁC KHỐI TRẮNG MỜ */
    .stApp p, .stApp span, .stApp label, .stMarkdown p, .stMarkdown li {{
        color: #000000 !important;
        font-weight: 600 !important;
    }}

    /* LỚP KÍNH CRYSTAL */
    .glass-card, div[data-testid="stChatMessage"], [data-testid="stSidebar"], .stTabs {{
        background: rgba(255, 255, 255, 0.45) !important; 
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 20px;
        padding: 20px;
    }}

    /* NÚT BẤM */
    div.stButton > button {{
        width: 100%; border-radius: 12px; font-weight: 800;
        border: 2px solid #000000 !important;
        background: rgba(255, 255, 255, 0.6) !important;
        color: #000000 !important;
    }}
    div.stButton > button:hover {{
        background: #000000 !important;
        color: #ffffff !important;
    }}

    /* Ô NHẬP LIỆU */
    input, textarea {{
        background: rgba(255, 255, 255, 0.8) !important;
        color: #000000 !important;
        border: 1px solid #000000 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. AI ENGINE ---
def call_ai(messages):
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": f"Nexus OS của {CREATOR_NAME}"}] + messages,
        stream=True
    )

# --- 6. SCREENS ---
def screen_auth():
    apply_ui()
    st.markdown(f'<h1 class="main-title">🛡️ NEXUS OS GATEWAY</h1>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["🔑 LOGIN", "📝 REGISTER", "👤 GUEST"])
    
    with t1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("XÁC THỰC"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU" if u in st.session_state.agreed_users else "TERMS"
                st.rerun()
            else: st.error("Lỗi thông tin!")

    with t2:
        nu = st.text_input("Tên đăng ký", key="r_u")
        np1 = st.text_input("Mật khẩu", type="password", key="r_p1")
        np2 = st.text_input("Nhập lại mật khẩu", type="password", key="r_p2")
        if st.button("TẠO TÀI KHOẢN"):
            if np1 == np2 and nu != "":
                st.session_state.users[nu] = np1
                save_github()
                st.success("Đã đăng ký! Hãy Login.")
            else: st.error("Mật khẩu không khớp!")

    with t3:
        if st.button("VÀO VỚI QUYỀN KHÁCH"):
            st.session_state.auth_status = "Guest"; st.session_state.stage = "TERMS"; st.rerun()

def screen_terms():
    apply_ui()
    st.markdown('<h1 class="main-title">📜 TERMS OF SERVICE</h1>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="glass-card">
        <h3>Chào {st.session_state.auth_status.upper()}</h3>
        <p>1. Hệ thống Crystal UI đã được tối ưu hiển thị.</p>
        <p>2. Dữ liệu chat được lưu trên Cloud cá nhân.</p>
        <p>3. Không sử dụng AI vào mục đích xấu.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.checkbox("Tôi đồng ý") and st.button("VÀO HỆ THỐNG"):
        if st.session_state.auth_status != "Guest":
            st.session_state.agreed_users.append(st.session_state.auth_status)
            save_github()
        st.session_state.stage = "MENU"; st.rerun()

def screen_menu():
    apply_ui()
    st.markdown(f'<h1 class="main-title">🚀 NEXUS MENU</h1>', unsafe_allow_html=True)
    st.write(f"Đang đăng nhập: **{st.session_state.auth_status.upper()}**")
    if st.button("🧠 AI CHAT"): st.session_state.stage = "CHAT"; st.rerun()
    if st.button("🎨 SETTINGS"): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.button("🚪 LOGOUT"):
        st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()

def screen_chat():
    apply_ui()
    with st.sidebar:
        st.header("📂 Library")
        if st.button("➕ NEW"): st.session_state.current_chat = None; st.rerun()
        for title in list(st.session_state.chat_library.keys()):
            if st.button(f"📄 {title[:15]}", key=title): st.session_state.current_chat = title; st.rerun()
        if st.button("🏠 MENU"): st.session_state.stage = "MENU"; st.rerun()

    history = st.session_state.chat_library.get(st.session_state.current_chat, []) if st.session_state.current_chat else []
    for m in history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("Nhập lệnh..."):
        if not st.session_state.current_chat:
            st.session_state.current_chat = p[:20]
            st.session_state.chat_library[st.session_state.current_chat] = []
        st.session_state.chat_library[st.session_state.current_chat].append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        with st.chat_message("assistant"):
            res = st.empty(); full = ""
            for chunk in call_ai(st.session_state.chat_library[st.session_state.current_chat]):
                if chunk.choices[0].delta.content:
                    full += chunk.choices[0].delta.content
                    res.markdown(full + "▌")
            res.markdown(full)
        st.session_state.chat_library[st.session_state.current_chat].append({"role": "assistant", "content": full})
        if st.session_state.auth_status != "Guest": save_github()

def screen_settings():
    apply_ui()
    st.markdown('<h1 class="main-title">🎨 UI SETTINGS</h1>', unsafe_allow_html=True)
    st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền:", st.session_state.theme['bg_url'])
    if st.button("LƯU & QUAY LẠI"): save_github(); st.session_state.stage = "MENU"; st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "TERMS": screen_terms()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "SETTINGS": screen_settings()
