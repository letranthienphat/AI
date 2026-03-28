# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random
from openai import OpenAI
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH HỆ THỐNG ---
SYSTEM_NAME = "NEXUS OS GATEWAY"
CREATOR = "Thiên Phát"
MASTER_PASS = "nexus os gateway"
FILE_DATA = "nexus_permanent_vault.json" # File lưu trữ vĩnh viễn

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS! Kiểm tra lại GitHub Secrets.")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide")

# --- [2] UI THEME & NÚT HOME NỔI ---
def apply_ui():
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
    }}
    /* Chữ đen viền xanh dương */
    h1, h2, h3, p, span, label, .stMarkdown {{
        color: #000 !important; font-weight: 800 !important;
        text-shadow: 1px 1px 2px #22d3ee, -1px -1px 2px #22d3ee;
    }}
    
    /* NÚT HOME NỔI - MỜ KHI KHÔNG RÊ CHUỘT */
    .floating-home {{
        position: fixed; bottom: 20px; right: 20px;
        width: 50px; height: 50px; background: rgba(34, 211, 238, 0.3);
        border: 2px solid #22d3ee; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; z-index: 9999; transition: 0.3s;
        text-decoration: none; font-size: 20px;
    }}
    .floating-home:hover {{ background: rgba(34, 211, 238, 1); opacity: 1; box-shadow: 0 0 20px #22d3ee; }}
    
    /* Fix Chat Overlap */
    .chat-box {{
        background: rgba(255, 255, 255, 0.8); border: 2px solid #22d3ee;
        border-radius: 10px; padding: 15px; margin: 10px 0; color: #000;
    }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    
    <a href="/?p=DASHBOARD" target="_self" class="floating-home" title="Về trang chủ">🏠</a>
    """, unsafe_allow_html=True)

# --- [3] KERNEL DỮ LIỆU (CHỐNG MẤT DỮ LIỆU) ---
def sync_get():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except: pass
    return {"users": {CREATOR: MASTER_PASS}, "status": {}, "codes": {}, "vault": {}, "chats": {}}

def sync_save():
    data = {
        "users": st.session_state.users, "status": st.session_state.status, 
        "codes": st.session_state.codes, "vault": st.session_state.vault, 
        "chats": st.session_state.chats
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Data Integrity Sync", "content": content, "sha": sha})
    except: pass

# --- [4] KHỞI CHẠY HỆ THỐNG ---
if 'boot' not in st.session_state:
    db = sync_get()
    # Gộp dữ liệu cũ để tránh mất tài khoản khi cập nhật code
    st.session_state.users = db.get("users", {CREATOR: MASTER_PASS})
    st.session_state.status = db.get("status", {})
    st.session_state.codes = db.get("codes", {})
    st.session_state.vault = db.get("vault", {})
    st.session_state.chats = db.get("chats", {})
    st.session_state.page = "AUTH"
    st.session_state.user = None
    st.session_state.boot = True

apply_ui()

# --- [5] ADMIN PANEL (FULL FEATURES) ---
def admin_page():
    st.header("🛠️ ADMIN COMMAND CENTER")
    if st.button("QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("✨ Tạo mã 8 ký tự")
        c_val = st.text_input("Nhập mã", max_chars=8).strip()
        c_multi = st.checkbox("Áp dụng nhiều tài khoản")
        c_perm = st.checkbox("Vĩnh viễn")
        c_days = st.number_input("Số ngày hiệu lực", 1, 365, 30)
        if st.button("PHÁT HÀNH MÃ"):
            if len(c_val) == 8:
                st.session_state.codes[c_val] = {"multi": c_multi, "perm": c_perm, "days": c_days, "used": []}
                sync_save(); st.success(f"✅ Đã tạo mã: {c_val}")
            else: st.error("Mã phải đủ 8 ký tự!")
    
    with col2:
        st.subheader("👥 Quản lý User")
        st.write(st.session_state.users)
        if st.button("RESET TOÀN BỘ CHATS"):
            st.session_state.chats = {}; sync_save(); st.warning("Đã xóa sạch lịch sử chat!")

# --- [6] AI CHAT (FIX KHÔNG PHẢN HỒI) ---
def ai_page():
    st.subheader("🧠 NEXUS AI TERMINAL")
    log = st.session_state.chats.setdefault(st.session_state.user, [])
    
    for m in log:
        with st.chat_message(m['role']): st.write(m['content'])
        
    if p := st.chat_input("Gửi lệnh cho AI..."):
        log.append({"role": "user", "content": p})
        with st.chat_message("user"): st.write(p)
        
        try:
            client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"system","content":f"Bạn là NEXUS OS của Thiên Phát. Hãy trả lời cực ngầu."}] + log[-5:]
            )
            ans = res.choices[0].message.content
            with st.chat_message("assistant"): st.write(ans)
            log.append({"role": "assistant", "content": ans})
            sync_save()
        except Exception as e:
            st.error(f"AI Error: {str(e)}")

# --- [7] ĐIỀU HƯỚNG CHÍNH ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h1 style='text-align:center;'>🏙️ NEXUS GATEWAY</h1>", unsafe_allow_html=True)
        u = st.text_input("Username").strip()
        p = st.text_input("Password", type="password").strip()
        if st.button("LOGIN"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.user = u; st.session_state.page = "DASHBOARD"; st.rerun()
        if st.button("REGISTER"):
            if u and p and u not in st.session_state.users:
                st.session_state.users[u] = p; sync_save(); st.success("Đã đăng ký!")

elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 {st.session_state.user}")
    st.write(f"Cấp độ: {st.session_state.status.get(st.session_state.user, 'FREE')}")
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        if st.button("🧠 AI"): st.session_state.page = "AI"; st.rerun()
    with c2:
        if st.button("☁️ CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
    with c3:
        if st.button("💎 PRO"): st.session_state.page = "UPGRADE"; st.rerun()
    with c4:
        if st.session_state.user == CREATOR:
            if st.button("🛠️ ADMIN"): st.session_state.page = "ADMIN"; st.rerun()

elif st.session_state.page == "ADMIN": admin_page()
elif st.session_state.page == "AI": ai_page()
# (Tính năng Cloud và Upgrade giữ nguyên như bản trước để tiết kiệm bộ nhớ code)
