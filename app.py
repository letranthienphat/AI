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
VERSION_NAME = "GATEWAY EDITION"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

# Nhật ký cập nhật
CHANGELOG = {
    "V5100": "• Đã thêm hiệu ứng NEXUS GATEWAY khi khởi động.\n• Hệ thống đồng bộ phiên bản người dùng (User Version Control).\n• Sửa lỗi treo màn hình khi xác thực bảo mật.\n• Tối ưu hóa giao diện Glassmorphism và Neon Glow."
}

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except Exception as e:
    st.error(f"Thiếu Secrets trên Streamlit: {e}")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {VERSION}", layout="wide", initial_sidebar_state="collapsed")

# -------------------- [2] MÃ HÓA & TIỆN ÍCH --------------------
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

# -------------------- [3] ĐỒNG BỘ GITHUB --------------------
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

# -------------------- [4] KHỞI TẠO TRẠNG THÁI --------------------
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123", "Thiên Phát": "123"})
    st.session_state.user_versions = db.get("user_versions", {})
    st.session_state.theme = db.get("theme", {"primary_color": "#00f2ff", "bg_url": "", "auto_wallpaper": False, "wp_interval": 1440, "last_wp_update": 0, "naming_threshold": 5})
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

# -------------------- [5] GIAO DIỆN & HIỆU ỨNG --------------------
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg = f"url('{t['bg_url']}')" if t['bg_url'] else "#0e1117"
    
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg} no-repeat center fixed; background-size: cover; }}
    
    /* Neon Text */
    h1, h2, h3, p, label, .stMarkdown p {{
        color: white !important; font-weight: 600 !important;
        text-shadow: 0 0 10px {p_color}, 0 0 5px {p_color}AA !important;
    }}
    
    /* Glassmorphism */
    .glass-panel, [data-testid="stSidebar"], [data-testid="stChatMessage"] {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 20px !important;
        border: 1px solid {p_color}44 !important;
        padding: 20px;
    }}
    
    /* Nút bấm */
    .stButton > button {{
        border: 2px solid {p_color} !important;
        background: transparent !important;
        color: white !important;
        border-radius: 12px;
        transition: 0.3s;
    }}
    .stButton > button:hover {{ background: {p_color} !important; color: black !important; box-shadow: 0 0 20px {p_color}; }}
    
    /* Animation Gateway */
    .gateway-box {{ display: flex; flex-direction: column; align-items: center; justify-content: center; height: 70vh; }}
    .logo-ring {{
        width: 120px; height: 120px; border: 4px solid {p_color}; border-radius: 30%;
        animation: rotateLogo 8s linear infinite, pulseLogo 2s ease-in-out infinite;
        box-shadow: 0 0 30px {p_color};
    }}
    @keyframes rotateLogo {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
    @keyframes pulseLogo {{ 0%, 100% {{ opacity: 0.6; scale: 1; }} 50% {{ opacity: 1; scale: 1.1; }} }}
    </style>
    """, unsafe_allow_html=True)

# -------------------- [6] LOGIC XỬ LÝ --------------------
def screen_gateway():
    apply_ui()
    st.markdown(f"""
    <div class="gateway-box">
        <div class="logo-ring"></div>
        <h1 style="margin-top:30px; letter-spacing: 8px;">NEXUS GATEWAY</h1>
        <p style="opacity: 0.7;">Bản quyền thuộc về {CREATOR_NAME}</p>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(3.5)
    st.session_state.stage = "AUTH"
    st.rerun()

def screen_auth():
    apply_ui()
    st.markdown("<h1 style='text-align:center;'>🛡️ XÁC THỰC HỆ THỐNG</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        u = st.text_input("Tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("ĐĂNG NHẬP GATEWAY", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                with st.spinner("Đang khởi tạo môi trường bảo mật..."):
                    ua = st_js.get_user_agent() # Lấy thông tin thiết bị
                    st.session_state.auth_status = u
                    if u not in st.session_state.user_versions:
                        st.session_state.user_versions[u] = VERSION
                    save_github()
                    st.session_state.stage = "MENU"
                    st.rerun()
            else: st.error("Tài khoản hoặc mật khẩu không chính xác.")
        st.markdown('</div>', unsafe_allow_html=True)

def screen_menu():
    apply_ui()
    user = st.session_state.auth_status
    st.markdown(f"<h1 style='text-align:center;'>🚀 NEXUS CENTER</h1>", unsafe_allow_html=True)
    
    # Kiểm tra phiên bản người dùng
    user_ver = st.session_state.user_versions.get(user, "Cũ")
    if user_ver != VERSION:
        st.warning(f"🔔 PHÁT HIỆN BẢN CẬP NHẬT MỚI: {VERSION}")
        with st.expander("Xem chi tiết bản cập nhật"):
            st.write(CHANGELOG.get(VERSION, "Nâng cấp hệ thống."))
            if st.button("CẬP NHẬT NGAY"):
                st.session_state.user_versions[user] = VERSION
                save_github()
                st.rerun()

    st.write(f"<p style='text-align:center;'>Xin chào, <b>{user}</b> | Phiên bản: {user_ver}</p>", unsafe_allow_html=True)
    
    cols = st.columns(5)
    if cols[0].button("🧠 AI CHAT"): st.session_state.stage = "CHAT"; st.rerun()
    if cols[1].button("🌐 SOCIAL"): st.session_state.stage = "SOCIAL"; st.rerun()
    if cols[2].button("⚙️ SETTINGS"): st.session_state.stage = "SETTINGS"; st.rerun()
    if cols[3].button("🛡️ ADMIN") and "Thiên Phát" in user: st.session_state.stage = "ADMIN"; st.rerun()
    if cols[4].button("🚪 EXIT"): st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()

# -------------------- [7] MÀN HÌNH AI CHAT --------------------
def call_ai(msgs):
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    sys = {"role": "system", "content": f"Bạn là AI của NEXUS OS. Phát là chủ nhân của bạn. Bạn đang nói chuyện với {st.session_state.auth_status}."}
    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[sys]+msgs, stream=True)

def screen_chat():
    apply_ui()
    user = st.session_state.auth_status
    lib = st.session_state.chat_library.setdefault(user, {})
    
    with st.sidebar:
        st.write("### 📂 LỊCH SỬ")
        if st.button("➕ CHAT MỚI", use_container_width=True): st.session_state.current_chat = None; st.rerun()
        for t in list(lib.keys()):
            if st.button(f"📄 {t[:15]}", use_container_width=True): st.session_state.current_chat = t; st.rerun()
        if st.button("🏠 VỀ MENU", use_container_width=True): st.session_state.stage = "MENU"; st.rerun()

    st.subheader(f"💬 {st.session_state.current_chat or 'Phiên thảo luận mới'}")
    
    history = lib.get(st.session_state.current_chat, [])
    for m in history:
        with st.chat_message(m["role"]): st.write(decrypt_msg(m["content"]))

    if p := st.chat_input("Gửi tin nhắn cho Nexus AI..."):
        if not st.session_state.current_chat: 
            st.session_state.current_chat = f"Chat_{int(time.time())}"
            lib[st.session_state.current_chat] = []
        
        lib[st.session_state.current_chat].append({"role": "user", "content": encrypt_msg(p)})
        with st.chat_message("user"): st.write(p)
        
        with st.chat_message("assistant"):
            res_box = st.empty(); full_res = ""
            msgs = [{"role": m["role"], "content": decrypt_msg(m["content"])} for m in lib[st.session_state.current_chat]]
            for chunk in call_ai(msgs):
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    res_box.markdown(full_res + "▌")
            res_box.markdown(full_res)
        
        lib[st.session_state.current_chat].append({"role": "assistant", "content": encrypt_msg(full_res)})
        save_github(); st.rerun()

# -------------------- [8] ĐIỀU HƯỚNG CHÍNH --------------------
def main():
    if st.session_state.stage == "GATEWAY": screen_gateway()
    elif st.session_state.stage == "AUTH": screen_auth()
    elif st.session_state.stage == "MENU": screen_menu()
    elif st.session_state.stage == "CHAT": screen_chat()
    # Các màn hình khác (Social, Admin, Settings) Phát có thể thêm tương tự.

if __name__ == "__main__":
    main()
