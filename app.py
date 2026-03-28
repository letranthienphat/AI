# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random
from openai import OpenAI

# --- [1] CẤU HÌNH HỆ THỐNG ---
SYSTEM_NAME = "NEXUS OS GATEWAY"
CREATOR = "Thiên Phát"
DEFAULT_PASS = "nexus os gateway" # Đã sửa đúng mật khẩu của Phát
VERSION = "V9200 - FINAL GATE"
FILE_DATA = "nexus_vault.json"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS TRÊN GITHUB!")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] CSS DARK-CORE (CHỐNG NỀN TRẮNG TUYỆT ĐỐI) ---
def apply_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp {{ background-color: #050505 !important; color: #00FFCC !important; font-family: 'JetBrains Mono', monospace !important; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    
    /* Nút bấm NEXUS CYBERPUNK */
    div.stButton > button {{
        background: transparent !important;
        color: #00FFCC !important;
        border: 2px solid #00FFCC !important;
        border-radius: 0px !important;
        box-shadow: inset 0 0 10px #00FFCC;
        font-weight: bold;
        transition: 0.3s;
    }}
    div.stButton > button:hover {{
        background: #00FFCC !important;
        color: #000 !important;
        box-shadow: 0 0 30px #00FFCC;
    }}
    
    /* Ô nhập liệu */
    input {{ background-color: #000 !important; color: #00FFCC !important; border: 1px solid #00FFCC !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- [3] MÀN HÌNH KHỞI ĐỘNG (VẼ LOGO BẰNG SVG & CSS) ---
def show_splash():
    placeholder = st.empty()
    with placeholder.container():
        # Hiệu ứng vẽ logo bằng đường nét SVG (Không lo mất ảnh)
        st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 90vh;">
            <svg width="200" height="200" viewBox="0 0 100 100">
                <path d="M20 80 L50 20 L80 80 M50 20 L50 80" fill="none" stroke="#00FFCC" stroke-width="2" stroke-dasharray="300" stroke-dashoffset="300">
                    <animate attributeName="stroke-dashoffset" from="300" to="0" dur="4s" fill="freeze" />
                </path>
                <circle cx="50" cy="50" r="45" fill="none" stroke="#00FFCC" stroke-width="0.5" stroke-dasharray="300" stroke-dashoffset="300">
                    <animate attributeName="stroke-dashoffset" from="300" to="0" dur="5s" fill="freeze" />
                </circle>
            </svg>
            <h1 style="color: #00FFCC; margin-top: 30px; letter-spacing: 10px; font-family: 'JetBrains Mono';">NEXUS OS</h1>
            <p style="color: #00FFCC; opacity: 0.5;">AUTHENTICATING QUANTUM CORE...</p>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(5) # Đợi 5 giây
    placeholder.empty()

# --- [4] KERNEL DỮ LIỆU ---
def sync_get():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except: pass
    # Nếu chưa có file, tạo file mới với đúng pass của Phát
    return {"users": {CREATOR: DEFAULT_PASS}, "status": {CREATOR: "promax"}, "chats": {}}

def sync_save():
    data = {"users": st.session_state.users, "status": st.session_state.status, "chats": st.session_state.chats}
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "System Sync", "content": content, "sha": sha})
    except: pass

# --- [5] ĐIỀU KHIỂN ---
if 'boot' not in st.session_state:
    show_splash()
    db = sync_get()
    st.session_state.update({
        "users": db.get("users", {CREATOR: DEFAULT_PASS}),
        "status": db.get("status", {CREATOR: "promax"}),
        "chats": db.get("chats", {}),
        "page": "AUTH", "user": None, "boot": True
    })

apply_ui()

# --- [6] MÀN HÌNH ĐĂNG NHẬP ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:center;'>🌌 {SYSTEM_NAME}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>BUILD BY {CREATOR.upper()}</p>", unsafe_allow_html=True)
        
        # Trim dấu cách để tránh lỗi nhập dư
        u = st.text_input("IDENTIFIER (Tên)").strip()
        p = st.text_input("PASSCODE (Mật mã)", type="password").strip()
        
        if st.button("EXECUTE LOGIN"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.user = u
                st.session_state.page = "DASHBOARD"
                st.rerun()
            else:
                st.error("❌ Truy cập bị từ chối. Sai thông tin hoặc chưa đăng ký.")
        
        if st.button("GUEST ACCESS (Truy cập khách)"):
            st.session_state.user = "Guest"
            st.session_state.page = "DASHBOARD"
            st.rerun()

# --- [7] DASHBOARD ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 TERMINAL: {st.session_state.user}")
    
    # Ở đây Phát có thể thêm các tính năng khác tùy ý
    if st.button("🧠 AI NEXUS"):
        st.info("AI đang chờ lệnh từ Thiên Phát...")
        
    if st.button("🔌 SHUTDOWN"):
        st.session_state.page = "AUTH"
        st.rerun()
