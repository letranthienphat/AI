# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V3700 - FROSTED GLASS"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
    FILE_DATA = "data.json"
except:
    st.error("Thiếu Secrets cấu hình!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. ĐỒNG BỘ GITHUB ---
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
        payload = {"message": "Sync Nexus", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
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
    st.session_state.initialized = True

# --- 4. SIÊU GIAO DIỆN SƯƠNG MỜ (GLASSMORPHISM) ---
def apply_ui():
    t = st.session_state.theme
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] else "background-color: #0e1117;"
    
    st.markdown(f"""
    <style>
    /* Nền ứng dụng */
    .stApp {{ {bg_style} }}

    /* LỚP SƯƠNG MỜ CHO CHỮ - Luôn dùng chữ trắng trên nền tối mờ */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, .stMarkdown p, .stMarkdown li {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
    }}

    /* Hộp nội dung sương mờ (Glass Box) */
    .glass-card {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 20px;
    }}

    /* Nút bấm */
    div.stButton > button {{
        width: 100%; border-radius: 12px; font-weight: 800;
        border: 2px solid {t['primary_color']} !important;
        background: rgba(0, 0, 0, 0.4) !important;
        color: #ffffff !important;
        backdrop-filter: blur(5px);
        transition: 0.3s;
    }}
    div.stButton > button:hover {{
        background: {t['primary_color']} !important;
        color: #000000 !important;
        box-shadow: 0px 0px 15px {t['primary_color']};
    }}

    /* Khung Chat */
    div[data-testid="stChatMessage"] {{
        background: rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: blur(10px);
        border-radius: 15px;
        margin: 10px 0;
        border: 1px solid rgba(255,255,255,0.1);
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: rgba(0, 0, 0, 0.6) !important;
        backdrop-filter: blur(20px);
    }}
    
    /* Ô nhập liệu */
    .stTextInput input, .stChatInputContainer textarea {{
        background: rgba(255,255,255,0.1) !important;
        color: white !important;
        border: 1px solid {t['primary_color']} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. MÀN HÌNH ---

def screen_auth():
    apply_ui()
    st.title("🛡️ NEXUS OS GATEWAY")
    tab1, tab2, tab3 = st.tabs(["🔑 ĐĂNG NHẬP", "📝 ĐĂNG KÝ", "👤 KHÁCH"])
    
    with tab1:
        u = st.text_input("Tên đăng nhập", key="login_u")
        p = st.text_input("Mật khẩu", type="password", key="login_p")
        if st.button("XÁC THỰC HỆ THỐNG"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU" if u in st.session_state.agreed_users else "TERMS"
                st.rerun()
            else: st.error("Sai tài khoản hoặc mật khẩu!")

    with tab2:
        nu = st.text_input("Tên tài khoản mới", key="reg_u")
        np1 = st.text_input("Mật khẩu mới", type="password", key="reg_p1")
        np2 = st.text_input("Xác nhận mật khẩu", type="password", key="reg_p2")
        if st.button("HOÀN TẤT ĐĂNG KÝ"):
            if not nu or not np1: st.warning("Không được để trống!")
            elif np1 != np2: st.error("Mật khẩu không khớp!")
            else:
                st.session_state.users[nu] = np1
                save_github(); st.success("Đăng ký thành công! Hãy chuyển sang tab Đăng nhập.")

    with tab3:
        st.write("Vào hệ thống mà không cần tài khoản. Lịch sử sẽ không được lưu.")
        if st.button("TRUY CẬP QUYỀN KHÁCH"):
            st.session_state.auth_status = "Guest"; st.session_state.stage = "TERMS"; st.rerun()

def screen_terms():
    apply_ui()
    st.title("📜 ĐIỀU KHOẢN SỬ DỤNG")
    st.markdown(f"""
    <div class="glass-card">
        <h3>Chào mừng {st.session_state.auth_status.upper()}</h3>
        <p>1. Bạn đang truy cập vào Nexus OS - Phiên bản Frosted Glass.</p>
        <p>2. Dữ liệu hội thoại được mã hóa và lưu trữ trên Cloud riêng biệt.</p>
        <p>3. Tuyệt đối không sử dụng AI cho các mục đích vi phạm pháp luật.</p>
    </div>
    """, unsafe_allow_html=True)
    
    agree = st.checkbox("Tôi đã đọc và đồng ý với điều khoản trên.")
    if agree and st.button("BẮT ĐẦU SỬ DỤNG"):
        if st.session_state.auth_status != "Guest":
            if st.session_state.auth_status not in st.session_state.agreed_users:
                st.session_state.agreed_users.append(st.session_state.auth_status)
                save_github()
        st.session_state.stage = "MENU"; st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "TERMS": screen_terms()
elif st.session_state.stage == "MENU":
    apply_ui()
    st.title(f"🚀 XIN CHÀO {st.session_state.auth_status.upper()}")
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("🧠 KẾT NỐI AI"): st.session_state.stage = "CHAT"; st.rerun()
    with c2: 
        if st.button("🎨 THIẾT KẾ UI"): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT"): 
        st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()
