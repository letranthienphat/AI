# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH LÕI ---
CONFIG = {
    "NAME": "NEXUS OS GATEWAY",
    "CREATOR": "Thiên Phát",
    "MASTER_PASS": "nexus os gateway",
    "VERSION": "16.5 Pro",
    "FILE_DATA": "nexus_gateway_data.json"
}

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except Exception as e:
    st.error("🛑 THIẾU SECRETS TRÊN STREAMLIT CLOUD.")
    st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="expanded")

# --- [2] FINGERPRINT ---
def get_device_fp():
    ua = st.context.headers.get("User-Agent", "UnknownDevice")
    return hashlib.sha256(ua.encode()).hexdigest()[:16]

# --- [3] KERNEL DỮ LIỆU ---
def sync_io(data=None):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    if data is None:
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
        return {"users": {CONFIG["CREATOR"]: CONFIG["MASTER_PASS"]}, "blacklist": [], "pro_users": [], "pro_devices": [], "rem": {}, "files": {}, "codes": {"PHAT2026": "VIP"}, "update_cfg": {"delay": 7, "latest": "17.0", "date": str(datetime.now().date())}}
    else:
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Pro Sync", "content": content, "sha": sha})

# --- [4] UI & NAVIGATION ---
def apply_ui():
    st.markdown("""<style>
    .stApp { background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80'); background-size: cover; background-attachment: fixed; }
    h1, h2, h3, p, span, label, .stMarkdown { color: #111 !important; font-weight: 800 !important; text-shadow: 1px 1px 3px #22d3ee; }
    [data-testid="stHeader"] { visibility: hidden; }
    </style>""", unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown(f"### 🛡️ {CONFIG['NAME']}")
        # HIỂN THỊ TRẠNG THÁI PRO NGAY SIDEBAR
        is_pro = st.session_state.get('is_pro', False)
        st.info(f"Trạng thái: {'💎 PRO' if is_pro else '🆓 GUEST'}")
        
        if st.session_state.get('page') not in ["BOT_CHECK", "AUTH"]:
            if st.button("🏠 VỀ DASHBOARD", use_container_width=True):
                st.session_state.page = "DASHBOARD"; st.rerun()
            if st.button("🔌 ĐĂNG XUẤT", use_container_width=True):
                fp = get_device_fp()
                if fp in st.session_state.db["rem"]: del st.session_state.db["rem"][fp]
                sync_io(st.session_state.db)
                st.session_state.user = None; st.session_state.page = "AUTH"; st.rerun()

# --- [5] LOGIC KHỞI CHẠY ---
if 'boot' not in st.session_state:
    st.session_state.db = sync_io()
    st.session_state.page = "BOT_CHECK"
    st.session_state.user = None
    st.session_state.strikes = 0
    st.session_state.boot = True
    st.session_state.is_pro = False

apply_ui()
fp = get_device_fp()

if fp in st.session_state.db.get("blacklist", []):
    st.error("🛑 THIẾT BỊ BỊ KHÓA."); st.stop()

# --- [6] BOT CHECK ---
if st.session_state.page == "BOT_CHECK":
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<h2 style='text-align:center;'>🛡️ SECURITY GATEWAY</h2>", unsafe_allow_html=True)
        scr_w = streamlit_js_eval(js_expressions="window.innerWidth", key="bot_monitor")
        is_human = st.checkbox("Tôi không phải là người máy")
        if st.button("TIẾP TỤC", use_container_width=True):
            if is_human and scr_w: st.session_state.page = "AUTH"; st.rerun()
            else:
                st.session_state.strikes += 1
                if st.session_state.strikes >= 3:
                    st.session_state.db["blacklist"].append(fp); sync_io(st.session_state.db)
                    st.error("🛑 ĐÃ KHÓA THIẾT BỊ."); st.stop()
                st.error(f"Thất bại {st.session_state.strikes}/3.")
    st.stop()

# --- [7] AUTO-LOGIN & CHECK PRO ---
if st.session_state.user is None and fp in st.session_state.db.get("rem", {}):
    st.session_state.user = st.session_state.db["rem"][fp]
    st.session_state.page = "DASHBOARD"

# KIỂM TRA QUYỀN PRO (Ghi nhớ Pro)
if st.session_state.user:
    # Nếu User nằm trong list Pro HOẶC Thiết bị này đã được kích hoạt Pro
    if (st.session_state.user in st.session_state.db.get("pro_users", []) or 
        fp in st.session_state.db.get("pro_devices", [])):
        st.session_state.is_pro = True

# --- [8] AUTH PAGE ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown(f"<h1 style='text-align:center;'>{CONFIG['NAME']}</h1>", unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        rem = st.checkbox("Ghi nhớ thiết bị này")
        if st.button("TRUY CẬP", use_container_width=True):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                if rem: st.session_state.db["rem"][fp] = u; sync_io(st.session_state.db)
                st.session_state.page = "DASHBOARD"; st.rerun()
            else: st.error("❌ Từ chối truy cập.")

# --- [9] DASHBOARD ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 XIN CHÀO: {st.session_state.user}")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🧠 AI NEXUS"): st.session_state.page = "AI"; st.rerun()
    if c2.button("☁️ CLOUD DRIVE"): st.session_state.page = "CLOUD"; st.rerun()
    if c3.button("⚙️ CÀI ĐẶT"): st.session_state.page = "SETTINGS"; st.rerun()
    if c4.button("🛠️ ADMIN") and st.session_state.user == CONFIG["CREATOR"]:
        st.session_state.page = "ADMIN"; st.rerun()

# --- [10] SETTINGS (NHẬP MÃ PRO) ---
elif st.session_state.page == "SETTINGS":
    st.header("⚙️ CÀI ĐẶT HỆ THỐNG")
    tab1, tab2 = st.tabs(["💎 KÍCH HOẠT PRO", "🆙 CẬP NHẬT"])
    
    with tab1:
        if st.session_state.is_pro:
            st.success("✨ Tài khoản của bạn đã ở trạng thái PRO vĩnh viễn.")
        else:
            st.subheader("Nhập mã Pro (8 ký tự)")
            pro_code = st.text_input("Mã kích hoạt", max_chars=8).upper()
            if st.button("XÁC NHẬN MÃ"):
                if pro_code in st.session_state.db.get("codes", {}):
                    # Lưu Pro cho cả User và Thiết bị (Ghi nhớ tuyệt đối)
                    if st.session_state.user not in st.session_state.db["pro_users"]:
                        st.session_state.db["pro_users"].append(st.session_state.user)
                    if fp not in st.session_state.db["pro_devices"]:
                        st.session_state.db["pro_devices"].append(fp)
                    
                    sync_io(st.session_state.db)
                    st.session_state.is_pro = True
                    st.balloons()
                    st.success("💎 KÍCH HOẠT THÀNH CÔNG! Trạng thái Pro đã được ghi nhớ vĩnh viễn.")
                    time.sleep(1); st.rerun()
                else: st.error("Mã không hợp lệ hoặc đã hết hạn.")

    with tab2:
        cfg = st.session_state.db["update_cfg"]
        st.write(f"Version: {CONFIG['VERSION']}")
        if st.button("KIỂM TRA UPDATE"):
            release_date = datetime.strptime(cfg["date"], "%Y-%m-%d")
            free_date = release_date + timedelta(days=cfg["delay"])
            if st.session_state.is_pro or datetime.now() >= free_date:
                st.success(f"Bản V{cfg['latest']} đã sẵn sàng.")
            else:
                st.warning(f"Bản mới đang khóa (Delay {cfg['delay']} ngày cho Guest). Mở lại vào {free_date.date()}.")

# AI, CLOUD, ADMIN (Giữ nguyên như bản cũ của bạn)...
elif st.session_state.page == "AI":
    st.header("🧠 AI NEXUS")
    if st.button("🔙 VỀ"): st.session_state.page = "DASHBOARD"; st.rerun()
    st.write("Tính năng AI đang hoạt động...")
# (Thêm các phần Cloud/Admin tương tự bản trước để hoàn thiện file)
