# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V3150 - ULTRA CONTRAST"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
    FILE_DATA = "data.json"
except:
    st.error("Thiếu Secrets cấu hình!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. HỆ THỐNG ĐỒNG BỘ GITHUB ---

def load_from_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            return json.loads(content)
    except: return None
    return None

def save_to_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    master_data = {
        "users": st.session_state.users,
        "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library
    }
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    content = base64.b64encode(json.dumps(master_data, indent=4).encode()).decode()
    payload = {"message": f"Sync {time.strftime('%H:%M:%S')}", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
    requests.put(url, headers=headers, json=payload)

# --- 3. KHỞI TẠO DỮ LIỆU ---

if 'initialized' not in st.session_state:
    cloud_data = load_from_github()
    if cloud_data:
        st.session_state.users = cloud_data.get("users", {"admin": "123"})
        st.session_state.theme = cloud_data.get("theme", {"mode": "light", "primary_color": "#00f2ff", "bg_url": "", "bg_tone": "light"})
        st.session_state.chat_library = cloud_data.get("chat_library", {})
    else:
        st.session_state.users = {"admin": "123"}
        st.session_state.theme = {"mode": "light", "primary_color": "#00f2ff", "bg_url": "", "bg_tone": "light"}
        st.session_state.chat_library = {}
    st.session_state.initialized = True
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None

# --- 4. SMART UI ENGINE (FIX TƯƠNG PHẢN) ---

def apply_ui(force_light=False):
    t = st.session_state.theme
    bg_tone = t.get('bg_tone', 'light')
    
    # Chỉnh màu chữ tổng quát dựa trên tông nền
    txt = "#ffffff" if bg_tone == "dark" else "#000000"
    if force_light: txt = "#000000"

    bg_css = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] and not force_light else ""
    app_bg = "#ffffff" if force_light or t['mode'] == "light" else "#0e1117"
    card_bg = "rgba(0,0,0,0.6)" if bg_tone == "dark" else "rgba(255,255,255,0.6)"

    st.markdown(f"""
    <style>
    /* Nền ứng dụng */
    .stApp {{ {bg_css} background-color: {app_bg}; color: {txt} !important; }}
    
    /* Ép tất cả các loại chữ ở màn hình chính phải đổi màu */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, .stMarkdown p {{
        color: {txt} !important;
    }}

    /* Nút bấm Glassmorphism */
    div.stButton > button {{
        width: 100%; border-radius: 12px; font-weight: 700;
        border: 2px solid {t['primary_color']} !important;
        background: {card_bg} !important;
        color: {txt} !important;
        backdrop-filter: blur(10px);
    }}

    /* KHUNG CHAT AI (ASSISTANT) - Luôn nền trắng chữ đen để dễ đọc nội dung dài */
    div[data-testid="stChatMessageAssistant"] {{
        background-color: #ffffff !important;
        border-radius: 15px;
        border-left: 6px solid {t['primary_color']};
    }}
    div[data-testid="stChatMessageAssistant"] * {{
        color: #000000 !important;
    }}

    /* KHUNG CHAT NGƯỜI DÙNG (USER) */
    div[data-testid="stChatMessageUser"] {{
        background-color: {card_bg} !important;
        border-radius: 15px;
        border: 1px solid {t['primary_color']};
    }}
    div[data-testid="stChatMessageUser"] * {{
        color: {txt} !important;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{ background-color: {card_bg} !important; backdrop-filter: blur(15px); }}
    [data-testid="stSidebar"] * {{ color: {txt} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÕI AI ---

def call_ai(messages):
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    sys = f"Bạn là Nexus OS, AI do {CREATOR_NAME} tạo ra. Trả lời thông minh."
    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":sys}]+messages, stream=True)

# --- 6. MÀN HÌNH ---

def screen_auth():
    apply_ui(force_light=True)
    st.title("🛡️ NEXUS OS GATEWAY")
    t1, t2 = st.tabs(["Đăng nhập", "Đăng ký"])
    with t1:
        u = st.text_input("Tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("XÁC THỰC"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u; st.session_state.stage = "MENU"; st.rerun()
            else: st.error("Sai thông tin!")
    with t2:
        nu = st.text_input("Tên mới")
        np = st.text_input("Mật khẩu mới", type="password")
        if st.button("TẠO TÀI KHOẢN"):
            st.session_state.users[nu] = np; save_to_github(); st.success("Đã đồng bộ!")

def screen_chat():
    apply_ui()
    with st.sidebar:
        st.header("📂 Kho Lưu Trữ")
        if st.button("➕ CHAT MỚI"): st.session_state.current_chat = None; st.rerun()
        for title in list(st.session_state.chat_library.keys()):
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                if st.button(f"📄 {title[:12]}", key=title): st.session_state.current_chat = title; st.rerun()
            with c2:
                if st.button("❌", key=f"d_{title}"): del st.session_state.chat_library[title]; save_to_github(); st.rerun()
        st.button("🏠 MENU", on_click=lambda: setattr(st.session_state, 'stage', 'MENU'))

    if st.session_state.current_chat:
        st.subheader(f"📍 {st.session_state.current_chat}")
        history = st.session_state.chat_library[st.session_state.current_chat]
    else:
        st.info("Hãy gửi tin nhắn để bắt đầu.")
        history = []

    for m in history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if pr := st.chat_input("Nhập lệnh..."):
        if not st.session_state.current_chat:
            st.session_state.current_chat = pr[:20]; st.session_state.chat_library[st.session_state.current_chat] = []
            history = st.session_state.chat_library[st.session_state.current_chat]
        history.append({"role": "user", "content": pr})
        with st.chat_message("user"): st.markdown(pr)
        with st.chat_message("assistant"):
            box = st.empty(); full = ""
            for chunk in call_ai(history):
                c = chunk.choices[0].delta.content
                if c: full += c; box.markdown(full + "▌")
            box.markdown(full)
            history.append({"role": "assistant", "content": full})
            st.session_state.chat_library[st.session_state.current_chat] = history
            save_to_github(); st.rerun()

def screen_settings():
    apply_ui()
    st.title("🎨 THIẾT KẾ UI")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.theme['mode'] = st.radio("Chế độ hệ thống:", ["light", "dark"])
        st.session_state.theme['primary_color'] = st.color_picker("Màu nhấn:", st.session_state.theme['primary_color'])
    with c2:
        st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền:", st.session_state.theme['bg_url'])
        st.session_state.theme['bg_tone'] = st.radio("Tông màu ảnh nền:", ["light", "dark"])
    if st.button("🚀 LƯU VÀ ĐỒNG BỘ"): save_to_github(); st.session_state.stage = "MENU"; st.rerun()
    if st.button("🔙 QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "MENU":
    apply_ui()
    st.title(f"🚀 CHÀO {st.session_state.auth_status.upper()}")
    if st.button("🧠 KẾT NỐI AI"): st.session_state.stage = "CHAT"; st.rerun()
    if st.button("🎨 THIẾT KẾ UI"): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT"): st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "SETTINGS": screen_settings()
