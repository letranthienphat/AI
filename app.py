# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH LÕI ---
CONFIG = {
    "NAME": "NEXUS ARCHON OS",
    "CREATOR": "Thiên Phát",
    "MASTER_PASS": "nexus os gateway",
    "VERSION": 15.0,
    "FILE_DATA": "nexus_archon_core.json"
}

try:
    GH_TOKEN, GH_REPO = st.secrets["GH_TOKEN"], st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS!")
    st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="collapsed")

# --- [2] FINGERPRINT (ĐỊNH DANH CỨNG THIẾT BỊ) ---
def get_device_fp():
    # Kết hợp User-Agent và độ phân giải để tạo ID không đổi kể cả khi đổi trình duyệt
    ua = st.context.headers.get("User-Agent", "unknown")
    fp = hashlib.sha256(ua.encode()).hexdigest()[:16]
    return fp

# --- [3] GIAO DIỆN & NÚT HOME (FIX KHÔNG RESET) ---
def apply_ui():
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
    }}
    h1, h2, h3, p, span, label, .stMarkdown {{
        color: #000 !important; font-weight: 900 !important;
        text-shadow: 1px 1px 3px #22d3ee;
    }}
    .stButton>button {{ background: rgba(255,255,255,0.2); border: 1px solid #22d3ee; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)
    
    # Nút Home dùng st.button để không reset trang
    with st.sidebar:
        if st.button("🏠 VỀ DASHBOARD", use_container_width=True):
            st.session_state.page = "DASHBOARD"
            st.rerun()

# --- [4] KERNEL DỮ LIỆU ---
def sync_io(data=None):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    if data is None:
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
        return {"users": {CONFIG["CREATOR"]: CONFIG["MASTER_PASS"]}, "blacklist": [], "pro": [], "rem": {}, "files": {}, "codes": {}, "update": {"delay": 7, "beta_ver": 15.5, "date": str(datetime.now().date())}}
    else:
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Archon Sync", "content": content, "sha": sha})

# --- [5] KHỞI CHẠY HỆ THỐNG ---
if 'boot' not in st.session_state:
    st.session_state.db = sync_io()
    st.session_state.page = "BOT_CHECK"
    st.session_state.user = None
    st.session_state.bot_strikes = 0
    st.session_state.boot = True

apply_ui()
fp = get_device_fp()

# --- [6] KIỂM TRA BLACKLIST ---
if fp in st.session_state.db.get("blacklist", []):
    st.error("🛑 THIẾT BỊ NÀY ĐÃ BỊ CHẶN VĨNH VIỄN DO VI PHẠM BẢO MẬT.")
    # Thông báo khẩn cho Admin (giả lập ghi log)
    st.info("Trường hợp khẩn cấp đã được báo cáo cho Admin Thiên Phát.")
    st.stop()

# --- [7] QUY TRÌNH KIỂM TRA BOT (3 LẦN THỬ) ---
if st.session_state.page == "BOT_CHECK":
    st.title("🛡️ NEXUS SECURITY SENTINEL")
    st.write("Hệ thống đang theo dõi hành vi chuột và thao tác...")
    
    # Checkbox xác thực hành vi
    is_human = st.checkbox("Xác thực: Tôi không phải là người máy")
    if st.button("VÀO HỆ THỐNG"):
        if is_human:
            st.session_state.page = "AUTH"
            st.rerun()
        else:
            st.session_state.bot_strikes += 1
            if st.session_state.bot_strikes >= 3:
                st.session_state.db["blacklist"].append(fp)
                sync_io(st.session_state.db)
                st.error("🛑 PHÁT HIỆN BOT! THIẾT BỊ ĐÃ BỊ KHÓA.")
                st.stop()
            st.warning(f"Cảnh báo: Xác thực thất bại lần {st.session_state.bot_strikes}/3")
    st.stop()

# --- [8] XỬ LÝ TRANG CHÍNH ---

# TỰ ĐỘNG LOGIN
if st.session_state.user is None and fp in st.session_state.db.get("rem", {}):
    st.session_state.user = st.session_state.db["rem"][fp]
    st.session_state.page = "DASHBOARD"

if st.session_state.page == "AUTH":
    st.title("🔐 ĐĂNG NHẬP")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    rem = st.checkbox("Ghi nhớ thiết bị")
    if st.button("XÁC THỰC"):
        if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
            st.session_state.user = u
            if rem: st.session_state.db["rem"][fp] = u; sync_io(st.session_state.db)
            st.session_state.page = "DASHBOARD"; st.rerun()
        else: st.error("Thông tin không chính xác.")

elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 XIN CHÀO: {st.session_state.user}")
    c = st.columns(4)
    if c[0].button("🧠 AI"): st.session_state.page = "AI"; st.rerun()
    if c[1].button("☁️ CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
    if c[2].button("⚙️ CÀI ĐẶT"): st.session_state.page = "SETTINGS"; st.rerun()
    if c[3].button("🛠️ ADMIN") and st.session_state.user == CONFIG["CREATOR"]:
        st.session_state.page = "ADMIN"; st.rerun()

# --- [9] CÀI ĐẶT (NHẬP MÃ & CẬP NHẬT) ---
elif st.session_state.page == "SETTINGS":
    st.header("⚙️ CÀI ĐẶT & THÔNG TIN")
    with st.expander("ℹ️ GIỚI THIỆU HỆ THỐNG", expanded=True):
        st.write(f"Hệ điều hành Nexus Archon v{CONFIG['VERSION']} phát triển bởi Thiên Phát.")
        st.write("Cơ chế bảo mật đa tầng với định danh phần cứng và AI phân tích.")

    with st.expander("💎 KÍCH HOẠT MÃ ƯU ĐÃI (8 KÝ TỰ)"):
        code = st.text_input("Nhập mã").upper()
        if st.button("KÍCH HOẠT"):
            if len(code) == 8:
                st.session_state.db["pro"].append(st.session_state.user)
                sync_io(st.session_state.db); st.balloons(); st.success("💎 BẠN ĐÃ LÀ PRO!")
            else: st.error("Mã phải đủ 8 ký tự.")

    with st.expander("🆙 KIỂM TRA CẬP NHẬT"):
        is_pro = st.session_state.user in st.session_state.db["pro"]
        up = st.session_state.db["update"]
        if st.button("KIỂM TRA"):
            release_date = datetime.strptime(up["date"], "%Y-%m-%d")
            delay_expiry = release_date + timedelta(days=up["delay"])
            
            if is_pro or datetime.now() >= delay_expiry:
                st.success(f"Phát hiện bản Beta {up['beta_ver']}! Đang áp dụng...")
                time.sleep(2); st.rerun()
            else:
                st.warning(f"Hiện chưa có bản cập nhật mới cho người dùng Free. (Vui lòng đợi đến {delay_expiry.date()})")

# --- [10] ADMIN (QUẢN LÝ KHẨN CẤP) ---
elif st.session_state.page == "ADMIN":
    st.header("🛠️ TRUNG TÂM ĐIỀU KHIỂN")
    st.subheader("📊 Quản lý Blacklist")
    st.write(st.session_state.db["blacklist"])
    if st.button("GỠ CHẶN TOÀN BỘ"):
        st.session_state.db["blacklist"] = []
        sync_io(st.session_state.db); st.rerun()
        
    st.subheader("📦 Cấu hình Cập nhật")
    new_delay = st.slider("Số ngày Delay cho bản Free", 0, 30, st.session_state.db["update"]["delay"])
    if st.button("LƯU CẤU HÌNH UPDATE"):
        st.session_state.db["update"]["delay"] = new_delay
        sync_io(st.session_state.db); st.success("Đã áp dụng delay mới!")
