# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V3850 - CRYSTAL COMPLETE"
FILE_DATA = "data.json"

# Kiểm tra Secrets
try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("Lỗi: Thiếu cấu hình Secrets (GH_TOKEN, GH_REPO, GROQ_KEYS)!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. HỆ THỐNG ĐỒNG BỘ GITHUB ---
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
        payload = {"message": f"Nexus Sync {time.strftime('%H:%M:%S')}", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- 3. KHỞI TẠO DỮ LIỆU ---
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

# --- 4. GIAO DIỆN CRYSTAL GLASS (CHỮ ĐEN TRÊN KÍNH TRONG) ---
def apply_ui():
    t = st.session_state.theme
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] else "background-color: #0e1117;"
    
    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} }}
    
    /* ÉP CHỮ ĐEN ĐẬM TOÀN HỆ THỐNG */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, 
    .stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        color: #000000 !important;
        font-weight: 600 !important;
    }}

    /* LỚP KÍNH CRYSTAL (TRONG SUỐT VỪA PHẢI) */
    .glass-card, div[data-testid="stChatMessage"], [data-testid="stSidebar"], .stTabs {{
        background: rgba(255, 255, 255, 0.4) !important; 
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
    }}

    /* NÚT BẤM TƯƠNG PHẢN CAO */
    div.stButton > button {{
        width: 100%; border-radius: 10px; font-weight: 700;
        border: 2px solid #000000 !important;
        background: rgba(255, 255, 255, 0.6) !important;
        color: #000000 !important;
        transition: 0.3s;
    }}
    div.stButton > button:hover {{
        background: #000000 !important;
        color: #ffffff !important;
    }}

    /* SIDEBAR */
    [data-testid="stSidebar"] * {{ color: #000000 !important; }}
    
    /* Ô NHẬP LIỆU */
    input, textarea {{
        background: rgba(255, 255, 255, 0.7) !important;
        color: #000000 !important;
        border: 1px solid #000000 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÕI AI ---
def call_ai(messages):
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    system_prompt = f"Bạn là Nexus OS, trợ lý AI thông minh của {CREATOR_NAME}."
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system_prompt}] + messages,
        stream=True
    )

# --- 6. CÁC MÀN HÌNH CHỨC NĂNG ---

def screen_auth():
    apply_ui()
    st.title("🛡️ NEXUS OS GATEWAY")
    t1, t2, t3 = st.tabs(["🔑 LOGIN", "📝 REGISTER", "👤 GUEST"])
    
    with t1:
        u = st.text_input("Tài khoản", key="l_u")
        p = st.text_input("Mật khẩu", type="password", key="l_p")
        if st.button("ĐĂNG NHẬP"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU" if u in st.session_state.agreed_users else "TERMS"
                st.rerun()
            else: st.error("Sai thông tin!")

    with t2:
        nu = st.text_input("Tên tài khoản mới", key="r_u")
        np1 = st.text_input("Mật khẩu", type="password", key="r_p1")
        np2 = st.text_input("Xác nhận mật khẩu", type="password", key="r_p2")
        if st.button("ĐĂNG KÝ NGAY"):
            if not nu or not np1: st.warning("Vui lòng điền đủ thông tin!")
            elif np1 != np2: st.error("Mật khẩu xác nhận không khớp!")
            else:
                st.session_state.users[nu] = np1
                save_github()
                st.success("Đăng ký thành công! Hãy chuyển sang tab Login.")

    with t3:
        st.info("Quyền khách: Trải nghiệm nhanh, không lưu lịch sử.")
        if st.button("VÀO VỚI QUYỀN KHÁCH"):
            st.session_state.auth_status = "Guest"; st.session_state.stage = "TERMS"; st.rerun()

def screen_terms():
    apply_ui()
    st.title("📜 ĐIỀU KHOẢN SỬ DỤNG")
    st.markdown(f"""
    <div class="glass-card">
        <h3>Xin chào {st.session_state.auth_status.upper()}</h3>
        <p>1. Bạn đang sử dụng giao diện Crystal Clear của Nexus OS.</p>
        <p>2. Mọi thông tin đều được bảo mật và đồng bộ hóa Cloud.</p>
        <p>3. Đồng ý để tiếp tục sử dụng dịch vụ AI.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.checkbox("Tôi đồng ý và không cần hỏi lại") and st.button("TIẾP TỤC VÀO MENU"):
        if st.session_state.auth_status != "Guest":
            st.session_state.agreed_users.append(st.session_state.auth_status)
            save_github()
        st.session_state.stage = "MENU"; st.rerun()

def screen_menu():
    apply_ui()
    st.title(f"🚀 WELCOME, {st.session_status.upper() if hasattr(st.session_state, 'auth_status') else 'USER'}")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🧠 AI CHAT"): st.session_state.stage = "CHAT"; st.rerun()
    with col2:
        if st.button("🎨 SETTINGS"): st.session_state.stage = "SETTINGS"; st.rerun()
    with col3:
        if st.button("⚙️ INFO"): st.session_state.stage = "INFO"; st.rerun()
    if st.button("🚪 LOGOUT"):
        st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()

def screen_chat():
    apply_ui()
    with st.sidebar:
        st.header("📂 Library")
        if st.button("➕ NEW CHAT"): st.session_state.current_chat = None; st.rerun()
        for title in list(st.session_state.chat_library.keys()):
            if st.button(f"📄 {title[:15]}", key=title):
                st.session_state.current_chat = title; st.rerun()
        if st.button("🏠 BACK TO MENU"): st.session_state.stage = "MENU"; st.rerun()

    history = st.session_state.chat_library.get(st.session_state.current_chat, []) if st.session_state.current_chat else []
    for m in history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Nhập lệnh..."):
        if not st.session_state.current_chat:
            st.session_state.current_chat = prompt[:20]
            st.session_state.chat_library[st.session_state.current_chat] = []
        
        st.session_state.chat_library[st.session_state.current_chat].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            for chunk in call_ai(st.session_state.chat_library[st.session_state.current_chat]):
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)
        
        st.session_state.chat_library[st.session_state.current_chat].append({"role": "assistant", "content": full_response})
        if st.session_state.auth_status != "Guest": save_github()

def screen_settings():
    apply_ui()
    st.title("🎨 CÀI ĐẶT UI")
    st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền (URL):", st.session_state.theme['bg_url'])
    if st.button("LƯU THIẾT LẬP"):
        save_github(); st.success("Đã lưu!"); time.sleep(1); st.session_state.stage = "MENU"; st.rerun()
    if st.button("🔙 QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()

def screen_info():
    apply_ui()
    st.title("⚙️ THÔNG TIN PHIÊN BẢN")
    st.markdown(f"""
    <div class="glass-card">
        <p><b>Tên hệ thống:</b> Nexus OS</p>
        <p><b>Phiên bản:</b> {VERSION}</p>
        <p><b>Chủ sở hữu:</b> {CREATOR_NAME}</p>
        <hr>
        <p><b>Cập nhật:</b> Chế độ sương mờ Crystal Clear, Fix chữ đen, Đồng bộ Cloud GitHub.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔙 QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "TERMS": screen_terms()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "SETTINGS": screen_settings()
elif st.session_state.stage == "INFO": screen_info()
