# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random
from openai import OpenAI
from datetime import datetime

# --- [1] CẤU HÌNH HỆ THỐNG ---
SYSTEM_NAME = "NEXUS OS GATEWAY"
CREATOR = "Thiên Phát"
VERSION = "V9000 - GENESIS"
FILE_DATA = "nexus_vault.json"
SECRET_KEY = "NEXUS_SUPREME_PROTOCOL_2026"

# Kiểm tra Secrets
try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except Exception as e:
    st.error("🛑 CRITICAL ERROR: Hệ thống thiếu API Keys trong Secrets!")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] CSS BOOT LOADER (FIX LỖI HIỂN THỊ) ---
def apply_os_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Ép nền đen sâu cho toàn bộ ứng dụng */
    .stApp {{
        background-color: #050505 !important;
        color: #00FFCC !important;
        font-family: 'JetBrains Mono', monospace !important;
    }}
    
    /* Giao diện Nút bấm Cyberpunk */
    div.stButton > button {{
        background: linear-gradient(45deg, #000, #111) !important;
        color: #00FFCC !important;
        border: 1px solid #00FFCC !important;
        border-radius: 5px !important;
        padding: 10px 24px !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: 0.4s;
        width: 100% !important;
    }}
    div.stButton > button:hover {{
        background: #00FFCC !important;
        color: #000 !important;
        box-shadow: 0 0 20px #00FFCC;
    }}

    /* Input & TextArea */
    input, textarea {{
        background-color: #111 !important;
        color: #00FFCC !important;
        border: 1px solid #333 !important;
    }}
    
    /* Ẩn Header mặc định của Streamlit */
    [data-testid="stHeader"] {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [3] MÀN HÌNH KHỞI ĐỘNG (ANIMATED LOGO DRAWING) ---
def show_splash_screen():
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(f"""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 80vh; background-color: #050505;">
            <img src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndXIzZzh3bm9oZnd4eGZyeXo1eGZyeXo1eGZyeXo1Z3p6ayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7TKMGpxX3Olt9S5q/giphy.gif" 
                 style="width: 300px; filter: hue-rotate(180deg) brightness(1.5);">
            
            <h1 style="color: #00FFCC; font-family: 'JetBrains Mono'; margin-top: 20px; letter-spacing: 5px; border-right: 5px solid; width: fit-content; overflow: hidden; white-space: nowrap; animation: typing 2s steps(20, end), blink .75s step-end infinite;">
                NEXUS OS GATEWAY
            </h1>
            <p style="color: #666;">CREATED BY {CREATOR.upper()}</p>
        </div>
        <style>
        @keyframes typing {{ from {{ width: 0 }} to {{ width: 100% }} }}
        @keyframes blink {{ from, to {{ border-color: transparent }} 50% {{ border-color: #00FFCC }} }}
        </style>
        """, unsafe_allow_html=True)
        time.sleep(5) # Chạy đúng 5 giây
    placeholder.empty()

# --- [4] KERNEL DỮ LIỆU (FIXED UTF-8 & GITHUB SYNC) ---
def xor_cipher(text):
    if not text: return ""
    return "".join([chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(text)])

def sync_get():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            return json.loads(content)
    except: pass
    return {}

def sync_save():
    data = {
        "users": st.session_state.users, "status": st.session_state.status,
        "chats": st.session_state.chats, "drive": st.session_state.drive,
        "global_msgs": st.session_state.global_msgs
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "System Sync", "content": content, "sha": sha})
    except: st.error("⚠️ Sync Failure!")

# --- [5] AI ENGINE (NEXUS INTELLIGENCE) ---
def ask_nexus(messages):
    sys_prompt = f"Bạn là NEXUS OS GATEWAY, được Thiên Phát lập trình. Hãy trả lời cực kỳ ngầu, sắc bén và trung thành."
    msgs = [{"role": "system", "content": sys_prompt}] + messages
    try:
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs)
        return res.choices[0].message.content
    except: return "❌ Mất kết nối tới Quantum AI."

# --- [6] MAIN LOGIC ---

# Khởi tạo state
if 'boot' not in st.session_state:
    show_splash_screen()
    db = sync_get()
    st.session_state.users = db.get("users", {CREATOR: "2002"})
    st.session_state.status = db.get("status", {CREATOR: "promax"})
    st.session_state.chats = db.get("chats", {})
    st.session_state.drive = db.get("drive", {})
    st.session_state.global_msgs = db.get("global_msgs", [])
    st.session_state.page = "AUTH"
    st.session_state.user = None
    st.session_state.boot = True

apply_os_theme()

# --- Màn hình Đăng nhập ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;'>NEXUS OS LOGIN</h1>", unsafe_allow_html=True)
        u = st.text_input("IDENTIFIER")
        p = st.text_input("PASSCODE", type="password")
        if st.button("ACCESS GATEWAY"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.user = u
                st.session_state.page = "DASHBOARD"
                st.rerun()
            else: st.error("❌ Invalid Credentials")

# --- Dashboard chính ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🌌 {SYSTEM_NAME} | {st.session_state.user}")
    st.write(f"Access Level: `{st.session_state.status.get(st.session_state.user, 'free').upper()}`")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🧠 AI TERMINAL"): st.session_state.page = "AI_CHAT"; st.rerun()
    with col2:
        if st.button("🌐 NETWORK"): st.session_state.page = "SOCIAL"; st.rerun()
    with col3:
        if st.button("☁️ CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
    with col4:
        if st.button("🔌 LOGOUT"): 
            st.session_state.page = "AUTH"; st.session_state.user = None; st.rerun()

# --- AI Terminal ---
elif st.session_state.page == "AI_CHAT":
    st.subheader("🧠 NEXUS QUANTUM TERMINAL")
    if st.button("🔙 BACK"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    chat_history = st.session_state.chats.setdefault(st.session_state.user, [])
    for m in chat_history:
        with st.chat_message(m['role']): st.write(m['content'])
        
    if p := st.chat_input("Enter command..."):
        chat_history.append({"role": "user", "content": p})
        with st.chat_message("user"): st.write(p)
        with st.chat_message("assistant"):
            res = ask_nexus(chat_history[-10:])
            st.write(res)
            chat_history.append({"role": "assistant", "content": res})
            sync_save()
            st.rerun()

# --- Cloud Drive ---
elif st.session_state.page == "CLOUD":
    st.subheader("☁️ PERSONAL VAULT")
    if st.button("🔙 BACK"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    files = st.session_state.drive.setdefault(st.session_state.user, [])
    up = st.file_uploader("Upload sensitive data")
    if up and st.button("SECURE FILE"):
        b64 = base64.b64encode(up.getvalue()).decode()
        files.append({"name": up.name, "data": b64, "time": str(datetime.now())})
        sync_save(); st.toast("File Secured!"); st.rerun()
        
    for i, f in enumerate(files):
        c1, c2 = st.columns([0.8, 0.2])
        c1.write(f"📄 {f['name']} | {f['time']}")
        if c2.button("🗑️", key=f"del_{i}"):
            files.pop(i); sync_save(); st.rerun()
