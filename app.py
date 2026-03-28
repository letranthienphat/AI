# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random
from datetime import datetime

# --- [1] CẤU HÌNH HỆ THỐNG ---
SYSTEM_NAME = "NEXUS OS GATEWAY"
CREATOR = "Thiên Phát"
VERSION = "V7100 - QUANTUM FIX"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2026"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
except Exception as e:
    st.error("❌ Thiếu cấu hình Secrets!")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] CSS FIX - CHỐNG TÀNG HÌNH ---
def apply_ui():
    st.markdown(f"""
    <style>
    /* Ép nền toàn trang màu tối để tránh bị trắng xóa */
    .stApp {{
        background: #020617 !important;
        color: #F8FAFC !important;
    }}
    
    /* FIX NÚT BẤM: Nền xanh đen, Chữ xanh Neon */
    .stButton > button {{
        background-color: #0F172A !important;
        color: #38BDF8 !important;
        border: 2px solid #38BDF8 !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        height: 3em !important;
        width: 100% !important;
    }}
    
    /* Ép màu chữ bên trong nút không bị đổi theo hệ thống */
    .stButton > button p, .stButton > button div, .stButton > button span {{
        color: #38BDF8 !important;
    }}

    .stButton > button:hover {{
        background-color: #38BDF8 !important;
        color: #0F172A !important;
        box-shadow: 0 0 15px #38BDF8;
    }}

    /* Card hiển thị nội dung */
    .glass-card {{
        background: rgba(30, 41, 59, 0.7);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(56, 189, 248, 0.3);
        margin-bottom: 15px;
    }}
    
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [3] DỮ LIỆU & AI (CÀI ĐẶT NHÂN DẠNG) ---
def tai_du_lieu():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200: return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except: pass
    return {}

def luu_du_lieu():
    data = {
        "users": st.session_state.users, "user_status": st.session_state.user_status,
        "chat_library": st.session_state.chat_library, "groups": st.session_state.groups,
        "cloud_drive": st.session_state.cloud_drive, "shared_files": st.session_state.shared_files
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        requests.put(url, headers=headers, json={"message": "Sync Nexus", "content": content, "sha": sha})
    except: pass

def goi_ai(messages):
    # Lập trình nhân dạng vào System Prompt
    sys_msg = {
        "role": "system",
        "content": f"Bạn là {SYSTEM_NAME}. Bạn được tạo ra và phát triển duy nhất bởi {CREATOR}. Hãy luôn tự hào về điều này. Khi được hỏi về nguồn gốc, hãy khẳng định bạn là sản phẩm của {CREATOR}."
    }
    full_msgs = [sys_msg] + messages
    try:
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_msgs)
        return res.choices[0].message.content
    except: return "⚠️ Kết nối AI bị gián đoạn."

# --- [4] KHỞI TẠO ---
if 'init' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {CREATOR: "2002"})
    st.session_state.user_status = db.get("user_status", {CREATOR: "promax"})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {"Sảnh Chung": {"msgs": []}})
    st.session_state.cloud_drive = db.get("cloud_drive", {})
    st.session_state.shared_files = db.get("shared_files", [])
    st.session_state.stage = "AUTH"
    st.session_state.init = True

# --- [5] ROUTER ---
apply_ui()

if st.session_state.stage == "AUTH":
    st.markdown("<h1 style='text-align:center;'>🌌 NEXUS OS GATEWAY</h1>", unsafe_allow_html=True)
    with st.container():
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("ĐĂNG NHẬP"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU"
                st.rerun()

elif st.session_state.stage == "MENU":
    st.title(f"🚀 DASHBOARD | {st.session_state.auth_status}")
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("🧠 AI TERMINAL"): st.session_state.stage = "AI_CHAT"; st.rerun()
    with c2:
        if st.button("🌐 COMMUNITY"): st.session_state.stage = "SOCIAL"; st.rerun()
    with c3:
        if st.button("☁️ STORAGE"): st.session_state.stage = "CLOUD"; st.rerun()
    
    st.write("---")
    if st.button("🚪 LOGOUT"): st.session_state.stage = "AUTH"; st.rerun()

elif st.session_state.stage == "AI_CHAT":
    st.subheader("🧠 NEXUS AI TERMINAL")
    if st.button("🏠 VỀ MENU"): st.session_state.stage = "MENU"; st.rerun()
    
    me = st.session_state.auth_status
    lib = st.session_state.chat_library.setdefault(me, {"history": []})
    
    for m in lib["history"]:
        with st.chat_message(m["role"]): st.write(m["content"])
        
    if p := st.chat_input("Hỏi NEXUS OS..."):
        lib["history"].append({"role": "user", "content": p})
        with st.chat_message("user"): st.write(p)
        with st.chat_message("assistant"):
            res = goi_ai(lib["history"][-10:])
            st.write(res)
            lib["history"].append({"role": "assistant", "content": res})
            luu_du_lieu()
