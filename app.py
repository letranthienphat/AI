# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random
from openai import OpenAI
from datetime import datetime

# --- [1] CẤU HÌNH HỆ THỐNG ---
SYSTEM_NAME = "NEXUS OS GATEWAY"
CREATOR = "Thiên Phát"
VERSION = "V9100 - UNIVERSAL"
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

# --- [2] GIAO DIỆN DARK-MODE TUYỆT ĐỐI ---
def apply_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    .stApp {{ background-color: #020617 !important; color: #38bdf8 !important; font-family: 'Orbitron', sans-serif; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    
    /* Nút bấm NEXUS */
    div.stButton > button {{
        background: rgba(15, 23, 42, 0.8) !important;
        color: #38bdf8 !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 4px !important;
        width: 100% !important;
        height: 3em !important;
        transition: 0.3s;
    }}
    div.stButton > button:hover {{
        background: #38bdf8 !important;
        color: #020617 !important;
        box-shadow: 0 0 20px #38bdf8;
    }}
    
    /* Ô nhập liệu */
    input {{ background-color: #0f172a !important; color: #fff !important; border: 1px solid #1e293b !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- [3] MÀN HÌNH KHỞI ĐỘNG (5 GIÂY) ---
def show_splash():
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(f"""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 90vh;">
            <img src="https://i.pinimg.com/originals/3f/82/3f/3f823f0099459341499252084799066b.gif" width="300" style="border-radius: 20px;">
            <h2 style="color: #38bdf8; margin-top: 20px; letter-spacing: 5px;">INITIALIZING NEXUS OS</h2>
            <p style="color: #64748b;">A PRODUCT BY {CREATOR.upper()}</p>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(5)
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
    return {"users": {CREATOR: "2002"}, "status": {CREATOR: "promax"}, "chats": {}, "drive": {}}

def sync_save():
    data = {
        "users": st.session_state.users, "status": st.session_state.status,
        "chats": st.session_state.chats, "drive": st.session_state.drive
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Sync", "content": content, "sha": sha})
    except: st.error("⚠️ Lỗi đồng bộ GitHub!")

# --- [5] TRÌNH ĐIỀU KHIỂN ---
if 'boot' not in st.session_state:
    show_splash()
    db = sync_get()
    st.session_state.update({
        "users": db.get("users", {CREATOR: "2002"}),
        "status": db.get("status", {CREATOR: "promax"}),
        "chats": db.get("chats", {}),
        "drive": db.get("drive", {}),
        "page": "AUTH", "user": None, "boot": True
    })

apply_ui()

# --- [6] MÀN HÌNH ĐĂNG NHẬP & ĐĂNG KÝ ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown(f"<h1 style='text-align:center;'>🌌 {SYSTEM_NAME}</h1>", unsafe_allow_html=True)
        
        tab_login, tab_reg, tab_guest = st.tabs(["🔐 ĐĂNG NHẬP", "📝 ĐĂNG KÝ", "👤 KHÁCH"])
        
        with tab_login:
            u = st.text_input("Username", key="li_u")
            p = st.text_input("Password", type="password", key="li_p")
            if st.button("XÁC THỰC"):
                if u in st.session_state.users and st.session_state.users[u] == p:
                    st.session_state.user = u
                    st.session_state.page = "DASHBOARD"
                    st.rerun()
                else: st.error("❌ Sai thông tin!")

        with tab_reg:
            nu = st.text_input("Username mới", key="rg_u")
            np = st.text_input("Password mới", type="password", key="rg_p")
            if st.button("TẠO TÀI KHOẢN"):
                if nu and np and nu not in st.session_state.users:
                    st.session_state.users[nu] = np
                    st.session_state.status[nu] = "free"
                    sync_save()
                    st.success("✅ Đã tạo! Hãy qua tab Đăng nhập.")
                else: st.warning("⚠️ Tên đã tồn tại hoặc để trống.")

        with tab_guest:
            st.info("Chế độ Khách sẽ không lưu lại lịch sử chat.")
            if st.button("VÀO VỚI TƯ CÁCH KHÁCH"):
                st.session_state.user = "Guest_" + str(random.randint(100,999))
                st.session_state.page = "DASHBOARD"
                st.rerun()

# --- [7] DASHBOARD ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 NEXUS DASHBOARD | {st.session_state.user}")
    
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("🧠 AI TERMINAL"): st.session_state.page = "CHAT"; st.rerun()
    with c2: 
        if st.button("☁️ CLOUD STORAGE"): st.session_state.page = "CLOUD"; st.rerun()
    with c3:
        if st.button("🔌 THOÁT"): 
            st.session_state.page = "AUTH"; st.session_state.user = None; st.rerun()

    st.markdown("---")
    st.write(f"Hệ điều hành được phát triển bởi **{CREATOR}**")

# --- [8] AI CHAT (FIXED) ---
elif st.session_state.page == "CHAT":
    st.subheader("🧠 NEXUS AI TERMINAL")
    if st.button("🔙 VỀ DASHBOARD"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    user_chat = st.session_state.chats.setdefault(st.session_state.user, [])
    for m in user_chat:
        with st.chat_message(m['role']): st.write(m['content'])
        
    if p := st.chat_input("Nhập lệnh..."):
        user_chat.append({"role": "user", "content": p})
        with st.chat_message("user"): st.write(p)
        
        # Gọi AI (Rút gọn cho nhanh)
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"system","content":f"Bạn là NEXUS OS của {CREATOR}."}] + user_chat[-5:]
        )
        ans = res.choices[0].message.content
        with st.chat_message("assistant"): st.write(ans)
        user_chat.append({"role": "assistant", "content": ans})
        sync_save()
