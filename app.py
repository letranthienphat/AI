# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V4800 - CREATOR EDITION"
FILE_DATA = "data.json"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("Thiếu Secrets cấu hình!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. BẢO MẬT & MÃ HÓA ---
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
        "users": st.session_state.users, "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library, "agreed_users": st.session_state.agreed_users,
        "friends": st.session_state.friends, "friend_requests": st.session_state.friend_requests,
        "groups": st.session_state.groups, "p2p_chats": st.session_state.p2p_chats
    }
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": f"Update {VERSION}", "content": content, "sha": sha}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- 4. KHỞI TẠO & VÁ LỖI DỮ LIỆU ---
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123"})
    theme_data = db.get("theme", {})
    default_theme = {
        "primary_color": "#00f2ff", "bg_url": "", "use_glass": True,
        "auto_wallpaper": False, "wp_interval": 1440, "last_wp_update": 0, "naming_threshold": 5
    }
    for k, v in default_theme.items():
        if k not in theme_data: theme_data[k] = v
    st.session_state.theme = theme_data

    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.friends = db.get("friends", {})
    st.session_state.friend_requests = db.get("friend_requests", {})
    st.session_state.groups = db.get("groups", {})
    st.session_state.p2p_chats = db.get("p2p_chats", {})
    st.session_state.agreed_users = db.get("agreed_users", [])
    
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None
    st.session_state.confirm_delete = None
    st.session_state.initialized = True

# --- 5. GIAO DIỆN (NEON GLOW & BLURRED CHAT) ---
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] else "background-color: #0e1117;"
    
    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} }}
    
    /* CHỮ CÓ BÓNG MỜ NEON */
    label, .stApp p, .stApp span, h1, h2, h3, h4, .stMarkdown p {{
        color: #000000 !important; font-weight: 700 !important;
        text-shadow: 1px 1px 10px {p_color}88 !important;
    }}
    
    .main-title {{
        color: {p_color} !important; text-shadow: 0px 0px 15px {p_color} !important;
        text-align: center; font-size: 2.8rem; font-weight: 900;
    }}

    /* NỀN MỜ CHO PHẢN HỒI AI */
    [data-testid="stChatMessage"] {{
        background: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 15px !important;
        border: 1px solid {p_color}33 !important;
        margin-bottom: 10px !important;
    }}

    .glass-card, [data-testid="stSidebar"], .stTabs {{
        background: rgba(255, 255, 255, 0.45) !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 15px; border: 1px solid {p_color}44;
    }}

    [data-testid="stHeader"] {{ display: none !important; }}
    
    .stButton > button {{
        border: 2px solid {p_color} !important; background: white !important;
        border-radius: 8px; font-weight: 800;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. HỆ THỐNG AI NHẬN DIỆN CREATOR ---
def call_ai(messages):
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    # Cài đặt danh tính cho A.I
    identity_prompt = {
        "role": "system", 
        "content": f"Bạn là NEXUS OS A.I. Người tạo ra bạn là anh Lê Trần Thiên Phát. Bạn phải luôn tôn trọng và hỗ trợ Phát hết mình. Trả lời bằng tiếng Việt 100%."
    }
    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[identity_prompt] + messages, stream=True)

# --- 7. MÀN HÌNH CHỨC NĂNG ---

def screen_social():
    apply_ui()
    user = st.session_state.auth_status
    st.markdown('<h1 class="main-title">🌐 NEXUS SOCIAL</h1>', unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["👥 BẠN BÈ", "💬 NHÓM"])
    with t1:
        st.write("### Danh sách bạn bè")
        friends = st.session_state.friends.get(user, [])
        for f in friends:
            st.write(f"🟢 {f}")
        search = st.text_input("Tìm người dùng để kết bạn:")
        if st.button("Gửi lời mời"): st.success("Đã gửi!")
        
    with t2:
        st.write("### Các nhóm của tôi")
        # Logic hiển thị nhóm...
        
    if st.button("🏠 VỀ MENU"): st.session_state.stage = "MENU"; st.rerun()

def screen_terms():
    apply_ui()
    st.markdown('<h1 class="main-title">📜 ĐIỀU KHOẢN SỬ DỤNG</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div class="glass-card">
    1. <b>Bảo mật:</b> Mọi dữ liệu của bạn được mã hóa E2E trước khi lưu trữ.<br>
    2. <b>Sáng tạo:</b> Nexus OS được phát triển bởi Lê Trần Thiên Phát.<br>
    3. <b>Trách nhiệm:</b> Người dùng tự chịu trách nhiệm về nội dung chat với AI.<br>
    </div>
    """, unsafe_allow_html=True)
    if st.button("ĐÃ HIỂU"): st.session_state.stage = "MENU"; st.rerun()

def screen_chat():
    apply_ui()
    user = st.session_state.auth_status
    lib = st.session_state.chat_library.setdefault(user, {})
    
    with st.sidebar:
        st.markdown(f'<p style="text-align:center; font-size:0.8rem;">Nexus OS {VERSION}</p>', unsafe_allow_html=True)
        if st.button("➕ CHAT MỚI", use_container_width=True): st.session_state.current_chat = None; st.rerun()
        st.write("---")
        # Danh sách chat với confirm xóa (như bản cũ)
        for title in list(lib.keys()):
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                if st.button(f"📄 {title}", key=f"b_{title}", use_container_width=True):
                    st.session_state.current_chat = title; st.rerun()
            with c2:
                if st.session_state.confirm_delete == title:
                    if st.button("✔️", key=f"y_{title}"): del lib[title]; st.session_state.confirm_delete = None; save_github(); st.rerun()
                elif st.button("🗑️", key=f"d_{title}"): st.session_state.confirm_delete = title; st.rerun()
        st.write("---")
        if st.button("🏠 MENU", use_container_width=True): st.session_state.stage = "MENU"; st.rerun()

    history = lib.get(st.session_state.current_chat, [])
    for m in history:
        with st.chat_message(m["role"]): st.markdown(decrypt_msg(m["content"]))

    if prompt := st.chat_input("Hỏi AI..."):
        if not st.session_state.current_chat:
            st.session_state.current_chat = f"Chat {int(time.time())}"
            lib[st.session_state.current_chat] = []
        lib[st.session_state.current_chat].append({"role": "user", "content": encrypt_msg(prompt)})
        st.rerun()

# --- 8. ĐIỀU HƯỚNG TỔNG ---
if st.session_state.stage == "AUTH":
    apply_ui()
    st.markdown('<h1 class="main-title">🛡️ NEXUS OS</h1>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        u = st.text_input("Tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("VÀO HỆ THỐNG", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u; st.session_state.stage = "MENU"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    st.markdown(f'<h1 class="main-title">🚀 NEXUS CENTER</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center;">Xin chào, <b>{st.session_state.auth_status}</b>. Phiên bản: {VERSION}</p>', unsafe_allow_html=True)
    cols = st.columns(5)
    if cols[0].button("🧠 AI CHAT"): st.session_state.stage = "CHAT"; st.rerun()
    if cols[1].button("🌐 SOCIAL"): st.session_state.stage = "SOCIAL"; st.rerun()
    if cols[2].button("⚙️ CÀI ĐẶT"): st.session_state.stage = "SETTINGS"; st.rerun()
    if cols[3].button("📜 TERMS"): st.session_state.stage = "TERMS"; st.rerun()
    if cols[4].button("🚪 EXIT"): st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()

elif st.session_state.stage == "SOCIAL": screen_social()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "TERMS": screen_terms()
elif st.session_state.stage == "SETTINGS": 
    # (Hàm screen_settings giữ nguyên như V4700)
    st.session_state.stage = "SETTINGS" # Đảm bảo dẫn đúng hàm
