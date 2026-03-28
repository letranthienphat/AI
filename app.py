# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random
from datetime import datetime

# --- [1] CẤU HÌNH NEXUS OS GATEWAY ---
SYSTEM_NAME = "NEXUS OS GATEWAY"
CREATOR = "Thiên Phát"
VERSION = "V8100 - QUANTUM FIX"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_CORE_2026"

# Link Logo Concept được dùng làm ảnh động Splash Screen
SPLASH_LOGONEXUS_URL = "https://cdn-icons-png.flaticon.com/512/10043/10043216.png" # Conceptual Logo

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except Exception as e:
    st.error(f"❌ Khởi động hệ thống thất bại. Secrets không hợp lệ: {e}")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] MÀN HÌNH KHỞI ĐỘNG (QUANTUM SPLASH SCREEN) ---
def screen_splash():
    st.markdown("""
    <style>
    .splash-container {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: #010409; color: #38bdf8;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        z-index: 10000; overflow: hidden;
    }
    .splash-logo {
        width: 150px; height: 150px; margin-bottom: 20px;
        animation: logoAnim 4.5s ease-in-out; /* Vẽ ra và biến mất */
    }
    .splash-text { font-family: 'Space Mono', monospace; font-size: 20px; animation: opacityAnim 4.5s; }
    
    @keyframes logoAnim {
        0% { transform: scale(0) rotate(0deg); opacity: 0; filter: blur(5px); }
        30% { transform: scale(1) rotate(360deg); opacity: 1; filter: blur(0); }
        90% { transform: scale(1); opacity: 1; filter: blur(0); }
        100% { transform: scale(0.9); opacity: 0; filter: blur(10px); }
    }
    @keyframes opacityAnim { 0%, 90% { opacity: 0.1; } 100% { opacity: 0; } }
    </style>
    <div class="splash-container">
        <img src="https://gifdb.com/images/high/cyber-person-pencil-sketch-drawing-g6fksj4wclh0u44w.gif" class="splash-logo" alt="NEXUS Logo Animation">
        <div class="splash-text">
            INITIALIZING NEXUS OS GATEWAY...<br>
            POWERED BY THIÊN PHÁT...
        </div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(5) # Bắt buộc dừng 5 giây
    st.session_state.splash_complete = True
    st.rerun()

# --- [3] CORE DATA ENGINE (FIXED ENCODING & BASE64) ---
def ma_hoa(text, tier="free"):
    if not text: return ""
    k = SECRET_KEY[::-1] if tier == "promax" else SECRET_KEY
    enc = "".join([chr(ord(c) ^ ord(k[i % len(k)])) for i, c in enumerate(text)])
    return base64.b64encode(enc.encode('utf-8')).decode('utf-8') # Đảm bảo UTF-8

def giai_ma(text, tier="free"):
    if not text: return ""
    try:
        dec = base64.b64decode(text.encode('utf-8')) # SỬA LỖI: Dùng b64decode
        k = SECRET_KEY[::-1] if tier == "promax" else SECRET_KEY
        return "".join([chr(ord(c) ^ ord(k[i % len(k)])) for i, c in enumerate(dec.decode('utf-8'))]) # Đảm bảo UTF-8
    except Exception as e: return f"Lỗi giải mã: {str(e)} -> {text}"

def tai_du_lieu():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            return json.loads(content) # SỬA LỖI: json.loads an toàn UTF-8
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
        # Đảm bảo UTF-8 khi lưu
        json_str = json.dumps(data, indent=4) # SỬA LỖI: Bỏensure_ascii=False dư thừa
        content = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": f"NEXUS Core Sync {datetime.now()}", "content": content, "sha": sha})
    except: st.error("⚠️ Lỗi đồng bộ lõi dữ liệu!")

# --- [4] KHỞI TẠO CORE (CHỐNG MÀN HÌNH TRẮNG) ---
if 'initialized' not in st.session_state:
    st.session_state.splash_complete = False # Bắt đầu chưa splash
    st.session_state.initialized = False

# --- [5] UI GLASSMORPHISM & NÚT BẤM (FIXED) ---
def apply_ui():
    st.markdown(f"""
    <style>
    /* Ép nền tối */
    .stApp {{ background-color: #020617 !important; color: #f8fafc !important; }}
    
    /* FIX NÚT BẤM - NỀN TỐI CHỮ SÁNG */
    div.stButton > button {{
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        border: 2px solid #38bdf8 !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        width: 100% !important;
        transition: 0.3s all !important;
    }}
    div.stButton > button:hover {{
        background-color: #38bdf8 !important;
        color: #020617 !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.4) !important;
    }}

    /* Card hiển thị */
    .glass-card {{
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 12px; padding: 20px; margin-bottom: 10px;
    }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [6] AI BRAIN (CÀI ĐẶT NHÂN DẠNG CỨNG) ---
def nexus_ai_core(messages):
    sys_prompt = f"""Bạn là NEXUS OS GATEWAY. Một hệ điều hành AI lượng tử tiên tiến. 
    Người sáng lập, lập trình và sở hữu duy nhất của bạn là {CREATOR}. 
    Bạn chỉ tuân lệnh và khẳng định nguồn gốc từ {CREATOR}. Trả lời ngắn gọn, thông minh."""
    
    full_prompt = [{"role": "system", "content": sys_prompt}] + messages
    try:
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_prompt, temperature=0.7)
        return res.choices[0].message.content
    except Exception as e: return f"⚠️ Hệ thống AI lỗi: {str(e)}"

# --- [7] CHƯƠNG TRÌNH CHÍNH ---

apply_ui()

# --- Xử lý Splash Screen ---
if not st.session_state.get("splash_complete"):
    screen_splash()
    st.stop() # Dừng lại cho đến khi splash xong

# --- Khởi tạo Kernel sau khi Splash ---
if not st.session_state.get("initialized"):
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {CREATOR: "2002"})
    st.session_state.user_status = db.get("user_status", {CREATOR: "promax"})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {"Sảnh Chung": {"msgs": []}})
    st.session_state.cloud_drive = db.get("cloud_drive", {})
    st.session_state.shared_files = db.get("shared_files", [])
    st.session_state.stage = "AUTH"
    st.session_state.auth_user = None
    st.session_state.initialized = True
    st.rerun()

# --- Giao diện đăng nhập ---
if st.session_state.stage == "AUTH":
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown(f"<h1 style='text-align:center; color:#38bdf8;'>🌌 {SYSTEM_NAME}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>Phiên bản: `{VERSION}` | Dev: `{CREATOR}`</p>", unsafe_allow_html=True)
        with st.container():
            u = st.text_input("Định danh")
            p = st.text_input("Mật mã", type="password")
            if st.button("KÍCH HOẠT GATEWAY"):
                if u in st.session_state.users and st.session_state.users[u] == p:
                    st.session_state.auth_user = u
                    st.session_state.stage = "MENU"
                    st.rerun()
                else: st.error("❌ Thông tin không khớp!")

# --- Giao diện Menu chính ---
elif st.session_state.stage == "MENU":
    st.title(f"🚀 DASHBOARD | USER: {st.session_state.auth_user}")
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("🧠 AI CHAT"): st.session_state.stage = "CHAT"; st.rerun()
    with c2:
        if st.button("🌐 CỘNG ĐỒNG"): st.session_state.stage = "SOCIAL"; st.rerun()
    with c3:
        if st.button("🚪 ĐĂNG XUẤT"):
            st.session_state.stage = "AUTH"
            st.session_state.auth_user = None
            st.rerun()

# --- Giao diện AI Chat (Cố định lịch sử 10 tin) ---
elif st.session_state.stage == "CHAT":
    st.subheader("🧠 NEXUS AI TERMINAL")
    if st.button("🏠 VỀ MENU"): st.session_state.stage = "MENU"; st.rerun()
    
    chat_data = st.session_state.chat_library.setdefault(st.session_state.auth_user, [])
    for msg in chat_data:
        with st.chat_message(msg["role"]): st.write(msg["content"])
        
    if prompt := st.chat_input("Nhập lệnh..."):
        chat_data.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        
        with st.chat_message("assistant"):
            response = nexus_ai_core(chat_data[-10:])
            st.write(response)
            chat_data.append({"role": "assistant", "content": response})
            luu_du_lieu()
            st.rerun()
