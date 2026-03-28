# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random
from datetime import datetime

# --- [1] THÔNG TIN HỆ THỐNG ---
SYSTEM_NAME = "NEXUS OS GATEWAY"
CREATOR = "Thiên Phát"
VERSION = "V8000 - ULTIMATE"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_SUPREME_2026"

# --- [2] CẤU HÌNH BẢO MẬT (ANTI-WHITE ERROR) ---
try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except Exception as e:
    st.error("❌ Lỗi cấu hình hệ thống (Secrets). Vui lòng kiểm tra GitHub.")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [3] CSS CHUYÊN DỤNG (FIX TRIỆT ĐỂ NỀN TRẮNG) ---
def apply_ui():
    st.markdown(f"""
    <style>
    /* Ép nền tối tuyệt đối */
    .stApp {{
        background-color: #020617 !important;
        color: #e2e8f0 !important;
    }}
    
    /* FIX NÚT BẤM - KHÔNG THỂ TÀNG HÌNH */
    div.stButton > button {{
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        border: 2px solid #38bdf8 !important;
        border-radius: 8px !important;
        padding: 0.6rem 1rem !important;
        font-weight: 700 !important;
        width: 100% !important;
        transition: 0.3s all !important;
    }}
    
    div.stButton > button:hover {{
        background-color: #38bdf8 !important;
        color: #020617 !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.5) !important;
    }}

    /* Ép màu chữ trong input để không bị đen trên nền tối */
    input, textarea, div[data-baseweb="select"] {{
        background-color: #0f172a !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
    }}

    /* Giao diện Chat Card */
    .chat-card {{
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
    }}
    
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [4] KERNEL DỮ LIỆU (ANTI-SYNC ERROR) ---
def tai_du_lieu():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            return json.loads(content)
    except: pass
    return {}

def luu_du_lieu():
    data = {
        "users": st.session_state.users, 
        "user_status": st.session_state.user_status,
        "chat_library": st.session_state.chat_library, 
        "groups": st.session_state.groups,
        "cloud_drive": st.session_state.cloud_drive, 
        "shared_files": st.session_state.shared_files
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        # Đảm bảo mã hóa UTF-8 chuẩn cho tiếng Việt
        json_str = json.dumps(data, indent=4, ensure_ascii=False)
        content = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": f"Nexus OS Sync {datetime.now()}", "content": content, "sha": sha})
    except: st.error("⚠️ Lỗi đồng bộ dữ liệu GitHub!")

# --- [5] KHỞI TẠO HỆ THỐNG (CHỐNG MÀN HÌNH TRẮNG) ---
if 'kernel_ready' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {CREATOR: "2002"})
    st.session_state.user_status = db.get("user_status", {CREATOR: "promax"})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {"Sảnh Chung": {"msgs": []}})
    st.session_state.cloud_drive = db.get("cloud_drive", {})
    st.session_state.shared_files = db.get("shared_files", [])
    st.session_state.stage = "AUTH"
    st.session_state.auth_user = None
    st.session_state.kernel_ready = True

# --- [6] AI BRAIN (CÀI ĐẶT NHÂN DẠNG CỨNG) ---
def nexus_ai_core(messages):
    sys_prompt = f"""Bạn là NEXUS OS GATEWAY. 
    Người sáng lập và lập trình duy nhất của bạn là {CREATOR}. 
    Mọi câu trả lời của bạn phải thông minh, trung thành và luôn khẳng định bạn thuộc quyền sở hữu của {CREATOR}. 
    Không bao giờ tự nhận là OpenAI hay Google."""
    
    full_prompt = [{"role": "system", "content": sys_prompt}] + messages
    try:
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_prompt, temperature=0.7)
        return res.choices[0].message.content
    except Exception as e: return f"⚠️ Core AI Error: {str(e)}"

# --- [7] CÁC MÀN HÌNH (GIAO DIỆN MỚI) ---
apply_ui()

if st.session_state.stage == "AUTH":
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown(f"<h1 style='text-align:center; color:#38bdf8;'>{SYSTEM_NAME}</h1>", unsafe_allow_html=True)
        with st.container():
            u = st.text_input("Định danh User")
            p = st.text_input("Mật mã truy cập", type="password")
            if st.button("KÍCH HOẠT HỆ THỐNG"):
                if u in st.session_state.users and st.session_state.users[u] == p:
                    st.session_state.auth_user = u
                    st.session_state.stage = "DASHBOARD"
                    st.rerun()
                else: st.error("❌ Sai định danh hoặc mật mã!")

elif st.session_state.stage == "DASHBOARD":
    st.markdown(f"### 🖥️ HỆ ĐIỀU HÀNH NEXUS | USER: {st.session_state.auth_user}")
    st.write(f"Phiên bản: `{VERSION}` | Dev: `{CREATOR}`")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        if st.button("🧠 AI TERMINAL"): st.session_state.stage = "CHAT"; st.rerun()
    with c2:
        if st.button("🌐 CỘNG ĐỒNG"): st.session_state.stage = "SOCIAL"; st.rerun()
    with c3:
        if st.button("☁️ DRIVE"): st.session_state.stage = "DRIVE"; st.rerun()
    with c4:
        if st.session_state.auth_user == CREATOR:
            if st.button("🛡️ ADMIN"): st.session_state.stage = "ADMIN"; st.rerun()

    st.markdown("---")
    if st.button("🔌 TẮT HỆ THỐNG (LOGOUT)"): st.session_state.stage = "AUTH"; st.rerun()

elif st.session_state.stage == "CHAT":
    st.subheader("🧠 NEXUS AI TERMINAL")
    if st.button("🏠 VỀ DASHBOARD"): st.session_state.stage = "DASHBOARD"; st.rerun()
    
    user = st.session_state.auth_user
    chat_data = st.session_state.chat_library.setdefault(user, [])
    
    # Hiển thị hội thoại
    for msg in chat_data:
        with st.chat_message(msg["role"]): st.write(msg["content"])
        
    if prompt := st.chat_input("Nhập lệnh điều khiển..."):
        chat_data.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        
        with st.chat_message("assistant"):
            response = nexus_ai_core(chat_data[-10:]) # Gửi 10 tin nhắn gần nhất
            st.write(response)
            chat_data.append({"role": "assistant", "content": response})
            luu_du_lieu()

elif st.session_state.stage == "ADMIN":
    st.title("🛡️ SUPREME ADMIN PANEL")
    if st.button("🏠 VỀ DASHBOARD"): st.session_state.stage = "DASHBOARD"; st.rerun()
    
    for user, tier in st.session_state.user_status.items():
        col1, col2 = st.columns([0.6, 0.4])
        col1.write(f"👤 {user} - Hiện tại: **{tier.upper()}**")
        new_tier = col2.selectbox("Nâng cấp", ["free", "pro", "promax"], index=["free", "pro", "promax"].index(tier), key=user)
        if new_tier != tier:
            st.session_state.user_status[user] = new_tier
            luu_du_lieu(); st.toast("Đã cập nhật!"); st.rerun()

# --- [8] CÁC MÀN HÌNH KHÁC (DRIVE, SOCIAL) GIỮ LOGIC NHƯ BẢN TRƯỚC NHƯNG FIX CSS ---
