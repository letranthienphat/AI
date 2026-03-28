# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random
from openai import OpenAI
from datetime import datetime

# --- [1] CẤU HÌNH HỆ THỐNG ---
SYSTEM_NAME = "NEXUS OS GATEWAY"
CREATOR = "Thiên Phát"
VERSION = "V10.000 - ULTIMATE"
FILE_DATA = "nexus_vault.json"
MASTER_PASS = "nexus os gateway" # Mật mã của Phát

# Kiểm tra Secrets
try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS TRÊN GITHUB!")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] GIAO DIỆN CYBERCORE ---
def apply_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp {{ background-color: #030712 !important; color: #22d3ee !important; font-family: 'JetBrains Mono', monospace !important; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    
    /* Nút bấm NEXUS */
    div.stButton > button {{
        background: rgba(34, 211, 238, 0.1) !important;
        color: #22d3ee !important;
        border: 1px solid #22d3ee !important;
        border-radius: 2px !important;
        width: 100% !important;
        transition: 0.3s;
    }}
    div.stButton > button:hover {{ background: #22d3ee !important; color: #030712 !important; box-shadow: 0 0 15px #22d3ee; }}
    
    /* Input */
    input {{ background-color: #0f172a !important; color: #fff !important; border: 1px solid #334155 !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- [3] LOGO VẼ TỰ ĐỘNG (5 GIÂY) ---
def show_splash():
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 90vh;">
            <svg width="150" height="150" viewBox="0 0 100 100">
                <polygon points="50,5 95,95 5,95" fill="none" stroke="#22d3ee" stroke-width="2" stroke-dasharray="300" stroke-dashoffset="300">
                    <animate attributeName="stroke-dashoffset" from="300" to="0" dur="4s" fill="freeze" />
                </polygon>
                <path d="M30 60 Q50 20 70 60" fill="none" stroke="#22d3ee" stroke-width="1">
                    <animate attributeName="opacity" from="0" to="1" dur="5s" />
                </path>
            </svg>
            <h1 style="color: #22d3ee; margin-top: 20px; letter-spacing: 8px;">NEXUS CORE</h1>
            <p style="color: #64748b; font-size: 12px;">SYSTEM INITIALIZING...</p>
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
    return {"users": {CREATOR: MASTER_PASS}, "status": {CREATOR: "PRO-MAX"}, "chats": {}, "vault": {}}

def sync_save():
    data = {
        "users": st.session_state.users, 
        "status": st.session_state.status, 
        "chats": st.session_state.chats,
        "vault": st.session_state.vault
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Ultimate Sync", "content": content, "sha": sha})
    except: st.error("⚠️ Sync Error!")

# --- [5] XỬ LÝ TRANG ---
if 'boot' not in st.session_state:
    show_splash()
    db = sync_get()
    st.session_state.update({
        "users": db.get("users", {CREATOR: MASTER_PASS}),
        "status": db.get("status", {CREATOR: "PRO-MAX"}),
        "chats": db.get("chats", {}),
        "vault": db.get("vault", {}),
        "page": "AUTH", "user": None, "boot": True
    })

apply_ui()

# --- [6] AUTH GATEWAY ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:center;'>🌌 {SYSTEM_NAME}</h1>", unsafe_allow_html=True)
        
        tab_in, tab_up = st.tabs(["🔐 ĐĂNG NHẬP", "📝 ĐĂNG KÝ"])
        with tab_in:
            u = st.text_input("Username").strip()
            p = st.text_input("Password", type="password").strip()
            if st.button("XÁC THỰC HỆ THỐNG"):
                if u in st.session_state.users and st.session_state.users[u] == p:
                    st.session_state.user = u
                    st.session_state.page = "DASHBOARD"
                    st.rerun()
                else: st.error("❌ Sai thông tin!")
        with tab_up:
            nu = st.text_input("Username mới").strip()
            np = st.text_input("Password mới", type="password").strip()
            if st.button("GHI DANH"):
                if nu and np and nu not in st.session_state.users:
                    st.session_state.users[nu] = np
                    st.session_state.status[nu] = "FREE"
                    sync_save(); st.success("✅ Đã tạo! Mời đăng nhập.")
                else: st.warning("⚠️ Lỗi tên trùng hoặc để trống.")

# --- [7] DASHBOARD ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 NEXUS TERMINAL | {st.session_state.user}")
    st.write(f"Cấp độ: `{st.session_state.status.get(st.session_state.user, 'FREE')}`")
    
    # Grid Menu
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        if st.button("🧠 AI TERMINAL"): st.session_state.page = "AI"; st.rerun()
    with c2: 
        if st.button("☁️ CLOUD VAULT"): st.session_state.page = "CLOUD"; st.rerun()
    with c3:
        if st.button("💎 NÂNG CẤP PRO"): st.session_state.page = "UPGRADE"; st.rerun()
    with c4:
        if st.session_state.user == CREATOR:
            if st.button("🛠️ ADMIN"): st.session_state.page = "ADMIN"; st.rerun()

    if st.button("🔌 ĐĂNG XUẤT"): 
        st.session_state.page = "AUTH"; st.session_state.user = None; st.rerun()

# --- [8] CLOUD VAULT (UPLOAD & DOWNLOAD) ---
elif st.session_state.page == "CLOUD":
    st.subheader("☁️ NEXUS CLOUD STORAGE")
    if st.button("🔙 VỀ"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    files = st.session_state.vault.setdefault(st.session_state.user, [])
    
    up = st.file_uploader("Tải tệp lên đám mây")
    if up and st.button("XÁC NHẬN TẢI LÊN"):
        b64 = base64.b64encode(up.getvalue()).decode()
        files.append({"name": up.name, "data": b64, "date": str(datetime.now())[:16]})
        sync_save(); st.success("✅ Đã lưu vào Cloud!"); st.rerun()
    
    st.write("---")
    for i, f in enumerate(files):
        col_n, col_d = st.columns([0.8, 0.2])
        col_n.write(f"📄 {f['name']} ({f['date']})")
        # Cho phép tải về
        btn_data = base64.b64decode(f['data'])
        col_d.download_button("📥 Tải", data=btn_data, file_name=f['name'], key=f"dl_{i}")

# --- [9] UPGRADE PRO ---
elif st.session_state.page == "UPGRADE":
    st.subheader("💎 NÂNG CẤP HỆ THỐNG")
    if st.button("🔙 VỀ"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    code = st.text_input("Nhập mã PRO (Liên hệ Thiên Phát để lấy mã)").strip()
    if st.button("KÍCH HOẠT"):
        if code == "PHAT_PRO_2026": # Mã mẫu
            st.session_state.status[st.session_state.user] = "PRO-MAX"
            sync_save(); st.balloons(); st.success("💎 CHÚC MỪNG! BẠN ĐÃ LÀ PRO-MAX."); st.rerun()
        else: st.error("❌ Mã không hợp lệ!")

# --- [10] AI TERMINAL ---
elif st.session_state.page == "AI":
    st.subheader("🧠 NEXUS AI (Powered by Groq)")
    if st.button("🔙 VỀ"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    chat_log = st.session_state.chats.setdefault(st.session_state.user, [])
    for m in chat_log:
        with st.chat_message(m['role']): st.write(m['content'])
        
    if p := st.chat_input("Gửi lệnh..."):
        chat_log.append({"role": "user", "content": p})
        with st.chat_message("user"): st.write(p)
        
        # Gọi AI
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"system","content":f"Bạn là NEXUS OS của {CREATOR}."}] + chat_log[-10:]
        )
        ans = res.choices[0].message.content
        with st.chat_message("assistant"): st.write(ans)
        chat_log.append({"role": "assistant", "content": ans})
        sync_save()
