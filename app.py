# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random
from openai import OpenAI
from datetime import datetime, timedelta

# --- [1] CONFIG ---
SYSTEM_NAME = "NEXUS OS GATEWAY"
CREATOR = "Thiên Phát"
MASTER_PASS = "nexus os gateway"
FILE_DATA = "nexus_vault_v3.json"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS!")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide")

# --- [2] UI THEME (FIX LỖI HIỂN THỊ) ---
def apply_ui():
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
    }}
    /* Chữ đen viền xanh dương sắc nét */
    h1, h2, h3, p, span, label, .stMarkdown {{
        color: #000000 !important;
        font-weight: 800 !important;
        text-shadow: 1px 1px 2px #22d3ee, -1px -1px 2px #22d3ee, 1px -1px 2px #22d3ee, -1px 1px 2px #22d3ee !important;
    }}
    /* Fix Cloud bị mất màn hình: Xóa bỏ các filter làm mờ hoặc đè lớp phủ */
    [data-testid="stHeader"] {{ visibility: hidden; }}
    
    /* Bong bóng chat kiểu mới - CHỐNG ĐÈ CHỮ */
    .chat-bubble {{
        background: rgba(255, 255, 255, 0.9);
        border: 2px solid #22d3ee;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        position: relative;
    }}
    .user-label {{
        color: #ff4b4b; /* Màu đỏ cho User */
        font-size: 0.8em;
        margin-bottom: 5px;
        display: block;
    }}
    .ai-label {{
        color: #00aaff; /* Màu xanh cho AI */
        font-size: 0.8em;
        margin-bottom: 5px;
        display: block;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- [3] DỮ LIỆU ---
def sync_get():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except: pass
    return {"users": {CREATOR: MASTER_PASS}, "status": {}, "codes": {}, "vault": {}}

def sync_save():
    data = {"users": st.session_state.users, "status": st.session_state.status, 
            "codes": st.session_state.codes, "vault": st.session_state.vault, "chats": st.session_state.chats}
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "System Update", "content": content, "sha": sha})
    except: pass

if 'boot' not in st.session_state:
    db = sync_get()
    st.session_state.update({
        "users": db.get("users", {CREATOR: MASTER_PASS}),
        "status": db.get("status", {}),
        "codes": db.get("codes", {}),
        "vault": db.get("vault", {}),
        "chats": db.get("chats", {}),
        "page": "AUTH", "user": None, "boot": True
    })

apply_ui()

# --- [4] LOGIC TRANG ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown(f"<h1 style='text-align:center;'>🏙️ {SYSTEM_NAME}</h1>", unsafe_allow_html=True)
        u = st.text_input("Tên định danh").strip()
        p = st.text_input("Mật mã", type="password").strip()
        if st.button("TRUY CẬP"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.user = u
                st.session_state.page = "DASHBOARD"
                st.rerun()
            else: st.error("❌ Sai thông tin!")
        if st.button("ĐĂNG KÝ"):
            if u and p and u not in st.session_state.users:
                st.session_state.users[u] = p
                sync_save(); st.success("✅ Thành công!")

elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 XIN CHÀO: {st.session_state.user}")
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
    if st.button("🔌 THOÁT"): st.session_state.page = "AUTH"; st.rerun()

# --- [5] ADMIN & UPGRADE (Mã 8 ký tự, Tick chọn) ---
elif st.session_state.page == "ADMIN":
    st.header("🛠️ QUẢN TRỊ VIÊN")
    if st.button("🔙"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    with st.expander("TẠO MÃ KÍCH HOẠT"):
        c_code = st.text_input("Mã (8 ký tự)", max_chars=8).strip()
        c_multi = st.checkbox("Áp dụng nhiều tài khoản")
        c_perm = st.checkbox("Vĩnh viễn")
        c_days = st.number_input("Số ngày (nếu không vĩnh viễn)", 1, 365, 30)
        if st.button("LƯU MÃ"):
            if len(c_code) == 8:
                st.session_state.codes[c_code] = {"multi": c_multi, "perm": c_perm, "days": c_days, "used": []}
                sync_save(); st.success("✅ Đã tạo mã!")

elif st.session_state.page == "UPGRADE":
    st.subheader("💎 NÂNG CẤP")
    if st.button("🔙"): st.session_state.page = "DASHBOARD"; st.rerun()
    code_in = st.text_input("Nhập mã 8 ký tự").strip()
    if st.button("KÍCH HOẠT"):
        if code_in in st.session_state.codes:
            info = st.session_state.codes[code_in]
            if not info['multi'] and len(info['used']) >= 1: st.error("❌ Mã đã dùng!")
            else:
                expiry = "VĨNH VIỄN" if info['perm'] else (datetime.now() + timedelta(days=info['days'])).strftime("%d/%m/%Y")
                st.session_state.status[st.session_state.user] = f"PRO-MAX ({expiry})"
                info['used'].append(st.session_state.user)
                sync_save(); st.balloons(); st.rerun()

# --- [6] CLOUD VAULT (FIX LỖI HIỂN THỊ) ---
elif st.session_state.page == "CLOUD":
    st.subheader("☁️ CLOUD VAULT")
    if st.button("🔙"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    user_files = st.session_state.vault.setdefault(st.session_state.user, [])
    up = st.file_uploader("Tải tệp")
    if up and st.button("LƯU"):
        user_files.append({"name": up.name, "data": base64.b64encode(up.getvalue()).decode(), "time": str(datetime.now())[:16]})
        sync_save(); st.rerun()
    
    for i, f in enumerate(user_files):
        c_n, c_d = st.columns([0.8, 0.2])
        c_n.write(f"📄 {f['name']}")
        c_d.download_button("📥", base64.b64decode(f['data']), file_name=f['name'], key=f"d_{i}")

# --- [7] AI CHAT (FIX ĐÈ CHỮ) ---
elif st.session_state.page == "AI":
    st.subheader("🧠 AI CHAT")
    if st.button("🔙"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    log = st.session_state.chats.setdefault(st.session_state.user, [])
    for m in log:
        label = "USER" if m['role'] == "user" else "NEXUS AI"
        class_name = "user-label" if m['role'] == "user" else "ai-label"
        st.markdown(f"""<div class="chat-bubble"><span class="{class_name}">{label}</span>{m['content']}</div>""", unsafe_allow_html=True)

    if p := st.chat_input("Hỏi gì đó..."):
        log.append({"role": "user", "content": p})
        # AI Logic... (Groq)
        sync_save(); st.rerun()
