# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V3100 - INTELLI-SOVEREIGN"

# Lấy thông tin bảo mật từ Secrets
try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
    FILE_DATA = "data.json"
except Exception as e:
    st.error("Lỗi: Thiếu cấu hình Secrets (GH_TOKEN, GH_REPO, hoặc GROQ_KEYS).")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. HỆ THỐNG ĐỒNG BỘ GITHUB (SYNC ENGINE) ---

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
    payload = {"message": f"Nexus Sync: {time.strftime('%H:%M:%S')}", "content": content}
    if sha: payload["sha"] = sha
    
    requests.put(url, headers=headers, json=payload)

# --- 3. KHỞI TẠO DỮ LIỆU ---

if 'initialized' not in st.session_state:
    cloud_data = load_from_github()
    if cloud_data:
        st.session_state.users = cloud_data.get("users", {"admin": "123"})
        st.session_state.theme = cloud_data.get("theme", {
            "mode": "light", 
            "primary_color": "#00f2ff", 
            "bg_url": "", 
            "bg_tone": "light"
        })
        st.session_state.chat_library = cloud_data.get("chat_library", {})
    else:
        st.session_state.users = {"admin": "123"}
        st.session_state.theme = {"mode": "light", "primary_color": "#00f2ff", "bg_url": "", "bg_tone": "light"}
        st.session_state.chat_library = {}
    
    st.session_state.initialized = True
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None

# --- 4. GIAO DIỆN THÍCH ỨNG (SMART UI ENGINE) ---

def apply_ui(force_light=False):
    t = st.session_state.theme
    bg_tone = t.get('bg_tone', 'light')
    
    if force_light:
        txt_color = "#1a1a1a"
        app_bg = "#ffffff"
        card_bg = "rgba(240, 240, 240, 0.9)"
    else:
        # Tự động đổi màu chữ dựa trên lựa chọn người dùng
        txt_color = "#ffffff" if bg_tone == "dark" else "#1a1a1a"
        app_bg = "#0e1117" if t['mode'] == "dark" else "#ffffff"
        card_bg = "rgba(0,0,0,0.5)" if bg_tone == "dark" else "rgba(255,255,255,0.5)"

    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if (t['bg_url'] and not force_light) else f"background-color: {app_bg};"

    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} color: {txt_color}; }}
    
    /* Chỉnh màu chữ toàn hệ thống */
    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp span, .stApp label, .stApp div {{
        color: {txt_color} !important;
    }}
    
    /* Nút bấm hiệu ứng kính (Glassmorphism) */
    div.stButton > button {{
        width: 100%; border-radius: 12px; font-weight: 700;
        border: 2px solid {t['primary_color']}; 
        background: {card_bg} !important; 
        color: {txt_color} !important;
        backdrop-filter: blur(12px);
        transition: 0.3s;
    }}
    div.stButton > button:hover {{ border-color: #ffffff; box-shadow: 0 0 15px {t['primary_color']}; }}

    /* Bong bóng chat AI - Luôn rõ ràng */
    div[data-testid="stChatMessageAssistant"] {{
        background: #ffffff !important; border-radius: 18px;
        border-left: 6px solid {t['primary_color']};
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }}
    div[data-testid="stChatMessageAssistant"] * {{ color: #000000 !important; font-weight: 500; }}
    
    /* Sidebar thích ứng */
    [data-testid="stSidebar"] {{ background-color: {card_bg} !important; backdrop-filter: blur(20px); }}
    [data-testid="stSidebar"] * {{ color: {txt_color} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÕI AI GROQ ---

def call_ai(messages):
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    sys_prompt = f"Bạn là Nexus OS, AI do {CREATOR_NAME} tạo ra. Trả lời thông minh, gãy gọn, không lặp từ."
    full_messages = [{"role": "system", "content": sys_prompt}] + messages
    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_messages, stream=True)

# --- 6. CÁC MÀN HÌNH ---

def screen_auth():
    apply_ui(force_light=True)
    st.title("🛡️ NEXUS OS GATEWAY")
    st.info(f"Hệ điều hành AI của {CREATOR_NAME}")
    tab1, tab2 = st.tabs(["🔒 Đăng nhập", "📝 Đăng ký"])
    with tab1:
        u = st.text_input("Tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("TRUY CẬP HỆ THỐNG"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU"; st.rerun()
            else: st.error("Sai thông tin đăng nhập!")
    with tab2:
        nu = st.text_input("Username mới")
        np = st.text_input("Mật khẩu mới", type="password")
        if st.button("TẠO TÀI KHOẢN VĨNH VIỄN"):
            if nu:
                st.session_state.users[nu] = np
                save_to_github(); st.success("Đã đồng bộ lên Cloud GitHub!"); time.sleep(1)

def screen_chat():
    apply_ui()
    with st.sidebar:
        st.header("📂 Kho Lưu Trữ")
        if st.button("➕ PHIÊN CHAT MỚI"): st.session_state.current_chat = None; st.rerun()
        st.write("---")
        for title in list(st.session_state.chat_library.keys()):
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                if st.button(f"📄 {title[:15]}", key=title): st.session_state.current_chat = title; st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{title}"):
                    del st.session_state.chat_library[title]
                    save_to_github(); st.rerun()
        st.write("---")
        st.button("🏠 VỀ MENU", on_click=lambda: setattr(st.session_state, 'stage', 'MENU'))

    if st.session_state.current_chat:
        st.subheader(f"📍 {st.session_state.current_chat}")
        history = st.session_state.chat_library[st.session_state.current_chat]
    else:
        st.info("Hãy gửi tin nhắn để khởi tạo phiên làm việc mới.")
        history = []

    for m in history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Nhập lệnh cho Nexus..."):
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
    st.title("🎨 TÙY CHỈNH GIAO DIỆN CAO CẤP")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.theme['mode'] = st.radio("Chủ đề hệ thống:", ["light", "dark"])
        st.session_state.theme['primary_color'] = st.color_picker("Màu chủ đạo (Viền/Nút):", st.session_state.theme['primary_color'])
    with c2:
        st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền (Direct Link):", st.session_state.theme['bg_url'])
        st.session_state.theme['bg_tone'] = st.radio("Tông màu của ảnh nền:", ["light", "dark"], help="Chọn 'light' nếu ảnh nền sáng (chữ sẽ thành đen), chọn 'dark' nếu ảnh tối (chữ sẽ thành trắng).")

    st.write("---")
    if st.button("🚀 LƯU VÀ ĐỒNG BỘ VĨNH VIỄN"):
        save_to_github(); st.session_state.stage = "MENU"; st.rerun()
    if st.button("🔙 QUAY LẠI"):
        st.session_state.stage = "MENU"; st.rerun()

# --- 7. ĐIỀU HƯỚNG CHÍNH ---
if st.session_state.stage == "AUTH":
    screen_auth()
elif st.session_state.stage == "MENU":
    apply_ui()
    st.title(f"🚀 CHÀO MỪNG {st.session_state.auth_status.upper()}")
    st.write(f"Trạng thái hệ thống: **Ổn định** | Phiên bản: **{VERSION}**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧠 KẾT NỐI AI"): st.session_state.stage = "CHAT"; st.rerun()
    with col2:
        if st.button("🎨 THIẾT KẾ UI"): st.session_state.stage = "SETTINGS"; st.rerun()
    st.write("---")
    if st.button("🚪 ĐĂNG XUẤT"): 
        st.session_state.auth_status = None
        st.session_state.stage = "AUTH"; st.rerun()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "SETTINGS": screen_settings()
