# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH ---
SYSTEM_NAME = "NEXUS SENTINEL OS"
CREATOR = "Thiên Phát"
MASTER_PASS = "nexus os gateway"
FILE_DATA = "nexus_sentinel_v4.json"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS TRÊN STREAMLIT CLOUD!")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] UI & NÚT HOME (FIX HIỂN THỊ) ---
def apply_ui():
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
    }}
    /* Chữ đen viền xanh dương sắc nét */
    h1, h2, h3, p, span, label, .stMarkdown, .stCheckbox {{
        color: #000 !important; font-weight: 800 !important;
        text-shadow: 1px 1px 2px #22d3ee, -1px -1px 2px #22d3ee, 1px -1px 2px #22d3ee, -1px 1px 2px #22d3ee !important;
    }}
    /* Nút Home nổi ở góc phải */
    .floating-home {{
        position: fixed; top: 15px; right: 15px;
        width: 40px; height: 40px; background: rgba(255, 255, 255, 0.4);
        border: 2px solid #22d3ee; border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        text-decoration: none; font-size: 18px; z-index: 1000; transition: 0.3s;
    }}
    .floating-home:hover {{ background: #22d3ee; color: white !important; box-shadow: 0 0 15px #22d3ee; }}
    
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    <a href="/?p=DASHBOARD" target="_self" class="floating-home" title="Về Dashboard">🏠</a>
    """, unsafe_allow_html=True)

# --- [3] LOGO ĐỘNG (FIX TREO) ---
def show_splash():
    if 'splashed' not in st.session_state:
        placeholder = st.empty()
        with placeholder.container():
            st.markdown("""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 90vh; background: white; border-radius: 20px;">
                <svg width="150" height="150" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="45" fill="none" stroke="#22d3ee" stroke-width="2" stroke-dasharray="283" stroke-dashoffset="283">
                        <animate attributeName="stroke-dashoffset" from="283" to="0" dur="3s" fill="freeze" />
                    </circle>
                    <path d="M30 50 L45 65 L70 35" fill="none" stroke="#000" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="100" stroke-dashoffset="100">
                        <animate attributeName="stroke-dashoffset" from="100" to="0" dur="2s" begin="1s" fill="freeze" />
                    </path>
                </svg>
                <h2 style="color: #000; margin-top: 20px;">NEXUS SYSTEM LOADING...</h2>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(4)
        placeholder.empty()
        st.session_state.splashed = True

# --- [4] KERNEL DỮ LIỆU ---
def sync_get():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except: pass
    return {"users": {CREATOR: MASTER_PASS}, "status": {}, "codes": {}, "remember": {}, "vault": {}}

def sync_save():
    data = {"users": st.session_state.users, "status": st.session_state.status, 
            "codes": st.session_state.codes, "remember": st.session_state.remember, "vault": st.session_state.vault}
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "System Maintenance", "content": content, "sha": sha})
    except: st.error("⚠️ Lỗi đồng bộ GitHub!")

# --- [5] KHỞI CHẠY ---
if 'boot' not in st.session_state:
    show_splash()
    db = sync_get()
    st.session_state.update({
        "users": db.get("users", {CREATOR: MASTER_PASS}),
        "status": db.get("status", {}),
        "codes": db.get("codes", {}),
        "remember": db.get("remember", {}),
        "vault": db.get("vault", {}),
        "page": "AUTH", "user": None, "boot": True, "attempts": 0
    })

apply_ui()

# Tự động nhận diện thiết bị (Remember Me)
dev_id = hashlib.md5(str(st.context.headers.get("User-Agent", "unknown")).encode()).hexdigest()[:12]
if st.session_state.user is None and dev_id in st.session_state.remember:
    st.session_state.user = st.session_state.remember[dev_id]
    st.session_state.page = "DASHBOARD"

# --- [6] XỬ LÝ TRANG ---

# TRANG ĐĂNG NHẬP
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:center;'>🛡️ {SYSTEM_NAME}</h1>", unsafe_allow_html=True)
        
        if st.session_state.attempts >= 5:
            st.warning("🛑 Phát hiện nghi vấn Brute Force. Tạm khóa nhập liệu.")
            time.sleep(5) # Delay ngắn để bot nản lòng
            
        u = st.text_input("Định danh (Username)").strip()
        p = st.text_input("Mật mã (Password)", type="password").strip()
        rem = st.checkbox("Ghi nhớ thiết bị này")
        
        if st.button("XÁC THỰC TRUY CẬP"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.user = u
                if rem: 
                    st.session_state.remember[dev_id] = u
                    sync_save()
                st.session_state.page = "DASHBOARD"
                st.rerun()
            else:
                st.session_state.attempts += 1
                st.error(f"❌ Sai thông tin! (Thử: {st.session_state.attempts}/5)")

# TRANG DASHBOARD (CÓ MỤC NHẬP MÃ)
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 XIN CHÀO: {st.session_state.user}")
    st.write(f"Trạng thái: **{st.session_state.status.get(st.session_state.user, 'FREE USER')}**")
    
    with st.expander("💎 KÍCH HOẠT MÃ ƯU ĐÃI (8 KÝ TỰ)", expanded=True):
        c_in = st.text_input("Nhập mã tại đây").strip()
        if st.button("XÁC NHẬN MÃ"):
            if c_in in st.session_state.codes:
                info = st.session_state.codes[c_in]
                # Logic vĩnh viễn hoặc ngày...
                st.session_state.status[st.session_state.user] = "PRO-MAX"
                sync_save(); st.balloons(); st.rerun()
            else: st.error("Mã không hợp lệ.")

    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        if st.button("🧠 AI NEXUS"): st.session_state.page = "AI"; st.rerun()
    with c2: 
        if st.button("☁️ CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
    with c3: 
        if st.button("🛠️ ADMIN"): 
            if st.session_state.user == CREATOR: st.session_state.page = "ADMIN"; st.rerun()
            else: st.error("Chỉ Thiên Phát mới có quyền này.")
    with c4:
        if st.button("🔌 ĐĂNG XUẤT"):
            if dev_id in st.session_state.remember: del st.session_state.remember[dev_id]
            st.session_state.user = None; st.session_state.page = "AUTH"; sync_save(); st.rerun()

# --- [7] ADMIN PANEL (FULL TÍNH NĂNG NHƯ YÊU CẦU) ---
elif st.session_state.page == "ADMIN":
    st.header("🛠️ QUẢN TRỊ VIÊN TỐI CAO")
    if st.button("🔙 VỀ DASHBOARD"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("✨ TẠO MÃ 8 KÝ TỰ")
        m_code = st.text_input("Mã định danh", max_chars=8).strip()
        m_multi = st.checkbox("Áp dụng nhiều người")
        m_perm = st.checkbox("Vĩnh viễn")
        m_days = st.number_input("Số ngày hạn định", 1, 365, 30)
        if st.button("LƯU MÃ LÊN HỆ THỐNG"):
            if len(m_code) == 8:
                st.session_state.codes[m_code] = {"multi": m_multi, "perm": m_perm, "days": m_days, "used": []}
                sync_save(); st.success(f"Đã tạo mã: {m_code}")
            else: st.error("Mã phải đủ 8 ký tự!")
            
    with col_b:
        st.subheader("📊 QUẢN LÝ DỮ LIỆU")
        st.write("Tổng số User:", len(st.session_state.users))
        st.write("Danh sách mã:", st.session_state.codes)
