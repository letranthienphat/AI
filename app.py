# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH ---
SYSTEM_NAME = "NEXUS SENTINEL OS"
CREATOR = "Thiên Phát"
MASTER_PASS = "nexus os gateway"
FILE_DATA = "nexus_sentinel_vault.json"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS!")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide")

# --- [2] CSS CUSTOM (LOGO ĐỘNG & NÚT HOME & CHỮ VIỀN) ---
def apply_ui():
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
    }}
    h1, h2, h3, p, span, label, .stMarkdown, .stCheckbox {{
        color: #000 !important; font-weight: 800 !important;
        text-shadow: 1px 1px 2px #22d3ee, -1px -1px 2px #22d3ee;
    }}
    /* Nút Home nổi */
    .floating-home {{
        position: fixed; top: 20px; right: 20px;
        width: 45px; height: 45px; background: rgba(255, 255, 255, 0.5);
        border: 2px solid #22d3ee; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        text-decoration: none; font-size: 20px; z-index: 9999;
    }}
    .floating-home:hover {{ background: #22d3ee; opacity: 1; }}
    
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    <a href="/?p=DASHBOARD" target="_self" class="floating-home">🏠</a>
    """, unsafe_allow_html=True)

# --- [3] LOGO ĐỘNG SVG (VẼ MẠCH) ---
def show_splash():
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 90vh; background: white;">
            <svg width="200" height="200" viewBox="0 0 100 100">
                <path d="M10 50 L30 50 L40 30 L60 70 L70 50 L90 50" fill="none" stroke="#22d3ee" stroke-width="3" stroke-dasharray="200" stroke-dashoffset="200">
                    <animate attributeName="stroke-dashoffset" from="200" to="0" dur="3s" fill="freeze" />
                </path>
                <circle cx="50" cy="50" r="45" fill="none" stroke="#000" stroke-width="1" stroke-dasharray="300" stroke-dashoffset="300">
                    <animate attributeName="stroke-dashoffset" from="300" to="0" dur="4s" fill="freeze" />
                </circle>
            </svg>
            <h2 style="color: #22d3ee; letter-spacing: 5px;">NEXUS ACTIVATING...</h2>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(4)
    placeholder.empty()

# --- [4] BẢO MẬT: PHÂN TÍCH HÀNH VI (ANTIBOT) ---
def check_bot():
    # Giả lập giám sát tọa độ (Sử dụng JavaScript ngầm)
    st.components.v1.html("""
        <script>
        let moves = [];
        document.onmousemove = function(e) {
            moves.push({x: e.pageX, y: e.pageY});
            if(moves.length > 50) moves.shift();
        }
        // Gửi tín hiệu về Streamlit nếu phát hiện đường thẳng tắp
        </script>
    """, height=0)
    
# --- [5] DỮ LIỆU VÀ ĐỊNH DANH THIẾU BỊ ---
def get_device_id():
    # Tạo mã định danh dựa trên User-Agent (Đơn giản nhưng hiệu quả cho Remember Me)
    ua = st.query_params.get("ua", "default")
    return hashlib.md5(ua.encode()).hexdigest()[:10]

def sync_get():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except: pass
    return {"users": {CREATOR: MASTER_PASS}, "status": {}, "codes": {}, "remember": {}}

def sync_save():
    data = {"users": st.session_state.users, "status": st.session_state.status, 
            "codes": st.session_state.codes, "remember": st.session_state.remember}
    # (Hàm put lên GitHub giữ nguyên cấu trúc cũ)
    pass 

# --- [6] XỬ LÝ TRANG ---
if 'boot' not in st.session_state:
    show_splash()
    db = sync_get()
    st.session_state.update({
        "users": db.get("users", {CREATOR: MASTER_PASS}),
        "status": db.get("status", {}),
        "codes": db.get("codes", {}),
        "remember": db.get("remember", {}),
        "login_attempts": 0, "page": "AUTH", "user": None, "boot": True
    })

apply_ui()
check_bot()

# Tự động đăng nhập nếu có Ghi nhớ thiết bị
dev_id = get_device_id()
if st.session_state.user is None and dev_id in st.session_state.remember:
    st.session_state.user = st.session_state.remember[dev_id]
    st.session_state.page = "DASHBOARD"

# --- [7] MÀN HÌNH AUTH ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown(f"<h1 style='text-align:center;'>🛡️ {SYSTEM_NAME}</h1>", unsafe_allow_html=True)
        
        if st.session_state.login_attempts > 5:
            st.error("🛑 PHÁT HIỆN HÀNH VI ĐÁNH CẮP DỮ LIỆU. TẠM KHÓA 1 PHÚT.")
            time.sleep(60)
            st.session_state.login_attempts = 0

        u = st.text_input("Username").strip()
        p = st.text_input("Password", type="password").strip()
        rem = st.checkbox("Ghi nhớ đăng nhập trên thiết bị này")
        
        if st.button("XÁC THỰC"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.user = u
                if rem: st.session_state.remember[dev_id] = u; sync_save()
                st.session_state.page = "DASHBOARD"
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                st.error(f"❌ Sai mật khẩu! Lần thử: {st.session_state.login_attempts}/5")

# --- [8] DASHBOARD & MỤC NHẬP MÃ ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 XIN CHÀO, {st.session_state.user}")
    
    with st.container():
        st.markdown("### 💎 KÍCH HOẠT MÃ ƯU ĐÃI")
        c_in = st.text_input("Nhập mã 8 ký tự tại đây", max_chars=8).strip()
        if st.button("KÍCH HOẠT NGAY"):
            if c_in in st.session_state.codes:
                # Logic nâng cấp Pro (như bản trước)
                st.success("✅ NÂNG CẤP THÀNH CÔNG!")
            else: st.error("Mã không tồn tại.")

    # Menu chính (AI, Cloud, Admin...)
    # ... (Giữ nguyên các nút như cũ)

# --- [9] ADMIN PANEL ---
elif st.session_state.page == "ADMIN":
    # Giao diện Admin với tính năng tạo mã (đã hoàn thiện ở bản trước)
    pass
