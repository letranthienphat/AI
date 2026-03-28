# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random
from openai import OpenAI
from datetime import datetime

# --- [1] CẤU HÌNH HỆ THỐNG ---
SYSTEM_NAME = "NEXUS OS GATEWAY"
CREATOR = "Thiên Phát"
VERSION = "V10.100 - CITY LIGHT"
FILE_DATA = "nexus_vault.json"
MASTER_PASS = "nexus os gateway" 

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS TRÊN GITHUB!")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] GIAO DIỆN CITY LIGHT (NỀN THÀNH PHỐ - CHỮ ĐEN VIỀN XANH) ---
def apply_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@700&display=swap');
    
    .stApp {{
        background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-attachment: fixed;
    }}
    
    /* Chữ đen viền xanh dương */
    h1, h2, h3, p, span, label, .stMarkdown {{
        color: black !important;
        font-family: 'Segoe UI', sans-serif !important;
        text-shadow: -1px -1px 0 #22d3ee, 1px -1px 0 #22d3ee, -1px 1px 0 #22d3ee, 1px 1px 0 #22d3ee;
        font-weight: bold !important;
    }}

    /* Nút bấm nổi bật */
    div.stButton > button {{
        background-color: rgba(255, 255, 255, 0.8) !important;
        color: black !important;
        border: 2px solid #22d3ee !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
    }}
    div.stButton > button:hover {{
        background-color: #22d3ee !important;
        color: white !important;
    }}

    /* Thẻ chứa nội dung (Glassmorphism sáng) */
    .stChatFloatingInputContainer, .stChatMessage {{
        background: rgba(255, 255, 255, 0.7) !important;
        border-radius: 15px !important;
    }}
    
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [3] MÀN HÌNH KHỞI ĐỘNG (5 GIÂY) ---
def show_splash():
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background: white;">
            <svg width="200" height="200" viewBox="0 0 100 100">
                <path d="M10 90 L50 10 L90 90 Z" fill="none" stroke="#22d3ee" stroke-width="3" stroke-dasharray="300" stroke-dashoffset="300">
                    <animate attributeName="stroke-dashoffset" from="300" to="0" dur="4s" fill="freeze" />
                </path>
                <circle cx="50" cy="55" r="20" fill="none" stroke="#22d3ee" stroke-width="1">
                    <animate attributeName="r" from="0" to="20" dur="4s" />
                </circle>
            </svg>
            <h1 style="color: black; margin-top: 20px; text-shadow: 0 0 10px #22d3ee;">NEXUS OS GATEWAY</h1>
            <p style="color: #555;">SYSTEM LOADING...</p>
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
        requests.put(url, headers=headers, json={"message": "System Maintenance Sync", "content": content, "sha": sha})
    except: st.error("⚠️ Lỗi đồng bộ dữ liệu!")

# --- [5] ĐIỀU KHIỂN ---
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
        st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:center;'>🌌 {SYSTEM_NAME}</h1>", unsafe_allow_html=True)
        
        u = st.text_input("Username").strip()
        p = st.text_input("Password", type="password").strip()
        
        if st.button("KÍCH HOẠT GATEWAY"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.user = u
                st.session_state.page = "DASHBOARD"
                st.rerun()
            else: st.error("❌ Sai thông tin truy cập!")
        
        st.markdown("<p style='text-align:center;'>Chưa có tài khoản? Nhập tên và pass rồi nhấn đăng ký bên dưới.</p>", unsafe_allow_html=True)
        if st.button("ĐĂNG KÝ MỚI"):
            if u and p and u not in st.session_state.users:
                st.session_state.users[u] = p
                st.session_state.status[u] = "FREE"
                sync_save(); st.success("✅ Đăng ký xong! Hãy nhấn Kích hoạt.")
            else: st.warning("⚠️ Tên trùng hoặc để trống.")

# --- [7] DASHBOARD ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🏙️ DASHBOARD | {st.session_state.user}")
    st.write(f"Cấp độ: `{st.session_state.status.get(st.session_state.user, 'FREE')}`")
    
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("🧠 AI CHAT"): st.session_state.page = "AI"; st.rerun()
    with c2: 
        if st.button("☁️ CLOUD VAULT"): st.session_state.page = "CLOUD"; st.rerun()
    with c3: 
        if st.button("💎 UPGRADE PRO"): st.session_state.page = "UPGRADE"; st.rerun()

    if st.button("🔌 THOÁT"): 
        st.session_state.page = "AUTH"; st.session_state.user = None; st.rerun()

# --- [8] CLOUD VAULT (FIXED) ---
elif st.session_state.page == "CLOUD":
    st.subheader("☁️ CLOUD STORAGE")
    if st.button("🔙 VỀ MENU"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    files = st.session_state.vault.setdefault(st.session_state.user, [])
    up = st.file_uploader("Chọn file tải lên")
    if up and st.button("LƯU VÀO MÂY"):
        b64 = base64.b64encode(up.getvalue()).decode()
        files.append({"name": up.name, "data": b64, "date": str(datetime.now())[:16]})
        sync_save(); st.success("✅ Đã lưu!"); st.rerun()
    
    for i, f in enumerate(files):
        col_n, col_d = st.columns([0.8, 0.2])
        col_n.write(f"📄 {f['name']} ({f['date']})")
        btn_data = base64.b64decode(f['data'])
        col_d.download_button("📥", data=btn_data, file_name=f['name'], key=f"dl_{i}")

# --- [9] UPGRADE PRO (FIXED) ---
elif st.session_state.page == "UPGRADE":
    st.subheader("💎 KÍCH HOẠT PRO-MAX")
    if st.button("🔙 VỀ MENU"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    code = st.text_input("Nhập mã kích hoạt").strip()
    if st.button("XÁC NHẬN MÃ"):
        if code == "PHAT_PRO_2026":
            st.session_state.status[st.session_state.user] = "PRO-MAX"
            sync_save() # Lưu ngay lập tức
            st.balloons()
            st.success("✅ Nâng cấp thành công! Cấp độ hiện tại: PRO-MAX")
            time.sleep(2)
            st.session_state.page = "DASHBOARD"
            st.rerun()
        else: st.error("❌ Mã không chính xác!")

# --- [10] AI CHAT ---
elif st.session_state.page == "AI":
    st.subheader("🧠 NEXUS AI TERMINAL")
    if st.button("🔙 VỀ MENU"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    chat_log = st.session_state.chats.setdefault(st.session_state.user, [])
    for m in chat_log:
        with st.chat_message(m['role']): st.write(m['content'])
        
    if p := st.chat_input("Nhập lệnh cho AI..."):
        chat_log.append({"role": "user", "content": p})
        with st.chat_message("user"): st.write(p)
        
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"system","content":f"Bạn là NEXUS OS của Thiên Phát."}] + chat_log[-10:]
        )
        ans = res.choices[0].message.content
        with st.chat_message("assistant"): st.write(ans)
        chat_log.append({"role": "assistant", "content": ans})
        sync_save()
