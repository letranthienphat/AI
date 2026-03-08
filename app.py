# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V3000 - ETERNAL SOVEREIGN"

# Lấy thông tin từ Secrets
GITHUB_TOKEN = st.secrets["GH_TOKEN"]
REPO_NAME = st.secrets["GH_REPO"]
FILE_DATA = "data.json"
GROQ_API_KEYS = st.secrets["GROQ_KEYS"]

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
        "chat_library": st.session_state.chat_library,
        "last_sync": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    
    content = base64.b64encode(json.dumps(master_data, indent=4).encode()).decode()
    payload = {"message": f"Update {time.strftime('%H:%M:%S')}", "content": content}
    if sha: payload["sha"] = sha
    
    requests.put(url, headers=headers, json=payload)

# --- 3. KHỞI TẠO DỮ LIỆU ---

if 'initialized' not in st.session_state:
    cloud_data = load_from_github()
    if cloud_data:
        st.session_state.users = cloud_data.get("users", {"admin": "123"})
        st.session_state.theme = cloud_data.get("theme", {"mode": "light", "primary_color": "#00f2ff", "bg_url": ""})
        st.session_state.chat_library = cloud_data.get("chat_library", {})
    else:
        st.session_state.users = {"admin": "123"}
        st.session_state.theme = {"mode": "light", "primary_color": "#00f2ff", "bg_url": ""}
        st.session_state.chat_library = {}
    
    st.session_state.initialized = True
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None

# --- 4. GIAO DIỆN (UI ENGINE) ---

def apply_ui(force_light=False):
    t = st.session_state.theme
    is_dark = t['mode'] == "dark" and not force_light
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if (t['bg_url'] and not force_light) else ""
    app_bg = "#ffffff" if not is_dark else "#0e1117"
    txt_color = "#1a1a1a" if not is_dark else "#ffffff"
    card_bg = "rgba(255,255,255,0.9)" if not is_dark else "rgba(30,30,30,0.9)"
    
    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} background-color: {app_bg}; color: {txt_color}; }}
    div.stButton > button {{
        width: 100%; border-radius: 12px; font-weight: 700;
        border: 1px solid {t['primary_color']}; background: {card_bg}; color: {txt_color};
    }}
    div[data-testid="stChatMessageAssistant"] {{
        background: #ffffff !important; color: #000000 !important;
        border-left: 5px solid {t['primary_color']}; border-radius: 15px;
    }}
    div[data-testid="stChatMessageAssistant"] * {{ color: #000000 !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÕI AI GROQ ---

def call_ai(messages):
    # Sử dụng khóa đầu tiên trong danh sách (anh có thể thêm logic xoay vòng khóa ở đây)
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    sys_prompt = f"Bạn là Nexus OS, sản phẩm trí tuệ của {CREATOR_NAME}. Trả lời ngắn gọn, thông minh, không lặp lại."
    full_messages = [{"role": "system", "content": sys_prompt}] + messages
    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_messages, stream=True)

# --- 6. MÀN HÌNH ---

def screen_auth():
    apply_ui(force_light=True)
    st.title("🛡️ NEXUS OS GATEWAY")
    st.write(f"Sản phẩm của {CREATOR_NAME}")
    tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký"])
    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("XÁC THỰC"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU"; st.rerun()
            else: st.error("Sai thông tin!")
    with tab2:
        nu = st.text_input("Tạo Username")
        np = st.text_input("Tạo Password", type="password")
        if st.button("ĐĂNG KÝ"):
            st.session_state.users[nu] = np
            save_to_github(); st.success("Đã đăng ký vĩnh viễn!"); time.sleep(1)

def screen_chat():
    apply_ui()
    with st.sidebar:
        st.header("📂 Thư viện")
        if st.button("➕ PHIÊN MỚI"): st.session_state.current_chat = None; st.rerun()
        st.write("---")
        for title in list(st.session_state.chat_library.keys()):
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                if st.button(f"📄 {title[:15]}", key=title): st.session_state.current_chat = title; st.rerun()
            with c2:
                if st.button("❌", key=f"del_{title}"):
                    del st.session_state.chat_library[title]
                    save_to_github(); st.rerun()
        st.button("🏠 MENU", on_click=lambda: setattr(st.session_state, 'stage', 'MENU'))

    if st.session_state.current_chat:
        st.subheader(f"📍 {st.session_state.current_chat}")
        history = st.session_state.chat_library[st.session_state.current_chat]
    else:
        st.info("Hãy đặt câu hỏi để bắt đầu.")
        history = []

    for m in history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Nhập lệnh..."):
        if not st.session_state.current_chat:
            st.session_state.current_chat = prompt[:25]
            st.session_state.chat_library[st.session_state.current_chat] = []
            history = st.session_state.chat_library[st.session_state.current_chat]
        
        history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            box = st.empty(); full = ""
            for chunk in call_ai(history):
                content = chunk.choices[0].delta.content
                if content:
                    full += content
                    box.markdown(full + "▌")
            box.markdown(full)
            history.append({"role": "assistant", "content": full})
            st.session_state.chat_library[st.session_state.current_chat] = history
            save_to_github(); st.rerun()

def screen_settings():
    apply_ui()
    st.title("🎨 CÀI ĐẶT")
    st.session_state.theme['mode'] = st.radio("Chủ đề:", ["light", "dark"], index=0 if st.session_state.theme['mode']=="light" else 1)
    st.session_state.theme['primary_color'] = st.color_picker("Màu nhấn:", st.session_state.theme['primary_color'])
    st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền:", st.session_state.theme['bg_url'])
    if st.button("LƯU VÀ ĐỒNG BỘ"):
        save_to_github(); st.session_state.stage = "MENU"; st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "MENU":
    apply_ui(); st.title(f"🚀 CHÀO {st.session_state.auth_status.upper()}")
    if st.button("🧠 BẮT ĐẦU CHAT AI"): st.session_state.stage = "CHAT"; st.rerun()
    if st.button("🎨 TÙY CHỈNH GIAO DIỆN"): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT"): st.session_state.stage = "AUTH"; st.rerun()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "SETTINGS": screen_settings()
