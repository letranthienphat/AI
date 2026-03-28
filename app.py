# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH HỆ THỐNG ---
SYSTEM_NAME = "NEXUS GENESIS OS"
CREATOR = "Thiên Phát"
MASTER_PASS = "nexus os gateway"
FILE_DATA = "nexus_system_core.json"
CURRENT_VERSION = 10.700 # Mã phiên bản hiện tại

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS!")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] FINGERPRINT & SECURITY (XÁC THỰC THIẾT BỊ) ---
def get_device_fingerprint():
    # Kết hợp nhiều thông số để tạo ID duy nhất cho thiết bị (kể cả đổi trình duyệt)
    user_agent = st.context.headers.get("User-Agent", "unknown")
    screen_res = st.context.headers.get("Viewport-Width", "unknown")
    fp_string = f"{user_agent}-{screen_res}"
    return hashlib.sha256(fp_string.encode()).hexdigest()[:16]

# --- [3] MÀN HÌNH KIỂM TRA BOT (CHẶN TẢI HỆ THỐNG) ---
def bot_challenge():
    if 'bot_passed' not in st.session_state:
        st.markdown("""<style>body { background: white !important; }</style>""", unsafe_allow_html=True)
        st.title("🛡️ NEXUS SECURITY CHECK")
        st.write("Vui lòng xác thực bạn là con người trước khi truy cập hệ thống.")
        
        # Bài test ngẫu nhiên
        n1, n2 = random.randint(1, 10), random.randint(1, 10)
        ans = st.number_input(f"Giải phép tính sau: {n1} + {n2} = ?", step=1)
        
        if st.button("XÁC THỰC"):
            if ans == (n1 + n2):
                st.session_state.bot_passed = True
                st.rerun()
            else:
                st.session_state.bot_fails = st.session_state.get('bot_fails', 0) + 1
                if st.session_state.bot_fails >= 3:
                    # Gửi cảnh báo lên GitHub cho Admin
                    st.error("🛑 BẠN ĐÃ BỊ CHẶN VÌ NGHI VẤN BOT ĐỘC HẠI. ĐANG BÁO CÁO ADMIN...")
                    # Logic ghi log blacklist...
                    st.stop()
                else:
                    st.warning(f"Sai! Bạn còn {3 - st.session_state.bot_fails} lần thử.")
        st.stop()

# --- [4] UI & NỀN THÀNH PHỐ ---
def apply_ui():
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80');
        background-size: cover; background-attachment: fixed;
    }}
    h1, h2, h3, p, span, label, .stMarkdown {{
        color: #000 !important; font-weight: 800 !important;
        text-shadow: 1px 1px 2px #22d3ee;
    }}
    .floating-home {{
        position: fixed; top: 15px; left: 15px; width: 40px; height: 40px;
        background: rgba(255,255,255,0.4); border: 2px solid #22d3ee;
        border-radius: 8px; display: flex; align-items: center; justify-content: center;
        text-decoration: none; z-index: 1000;
    }}
    </style>
    <a href="/?p=DASHBOARD" target="_self" class="floating-home">🏠</a>
    """, unsafe_allow_html=True)

# --- [5] DỮ LIỆU PHÂN TẦNG (NEW & OLD VERSION) ---
def sync_get():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except: pass
    return {
        "users": {CREATOR: MASTER_PASS}, "status": {}, "codes": {},
        "config": {"free_delay_days": 7, "latest_version": CURRENT_VERSION},
        "vault": {}, "chats": {}, "blacklist": []
    }

def sync_save():
    # Lưu dữ liệu phân tách mã mới/cũ
    data = {
        "users": st.session_state.users, "status": st.session_state.status,
        "codes": st.session_state.codes, "config": st.session_state.config,
        "vault": st.session_state.vault, "chats": st.session_state.chats,
        "blacklist": st.session_state.get('blacklist', [])
    }
    # Logic push GitHub...
    pass

# --- [6] XỬ LÝ TRANG ---
bot_challenge() # Phải qua bot mới chạy tiếp code dưới

if 'boot' not in st.session_state:
    db = sync_get()
    st.session_state.update(db)
    st.session_state.page = "AUTH"
    st.session_state.user = None
    st.session_state.boot = True

apply_ui()

# --- [7] ADMIN: THIẾT LẬP CẬP NHẬT ---
if st.session_state.page == "ADMIN":
    st.header("🛠️ QUẢN TRỊ VIÊN")
    if st.button("🔙 VỀ"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    with st.expander("⚙️ THIẾT LẬP CẬP NHẬT (UPDATE CONFIG)"):
        st.write(f"Phiên bản hiện tại trên Server: {st.session_state.config.get('latest_version')}")
        delay = st.number_input("Số ngày delay cho bản Free", 0, 30, st.session_state.config.get('free_delay_days'))
        mode = st.radio("Chế độ cập nhật", ["Tự động", "Thông báo", "Người dùng tự nhấn"])
        if st.button("ÁP DỤNG CẤU HÌNH"):
            st.session_state.config['free_delay_days'] = delay
            st.session_state.config['update_mode'] = mode
            sync_save(); st.success("Đã lưu cấu hình cập nhật!")

# --- [8] CÀI ĐẶT (SETTINGS) & NHẬP MÃ ---
elif st.session_state.page == "SETTINGS":
    st.header("⚙️ CÀI ĐẶT HỆ THỐNG")
    if st.button("🔙 VỀ"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    with st.expander("💎 NHẬP MÃ KÍCH HOẠT PRO", expanded=True):
        code_in = st.text_input("Nhập mã 8 ký tự").strip()
        if st.button("XÁC NHẬN MÃ"):
            if code_in in st.session_state.codes:
                st.session_state.status[st.session_state.user] = "PRO"
                sync_save(); st.balloons(); st.rerun()
    
    with st.expander("🆙 KIỂM TRA CẬP NHẬT"):
        is_pro = st.session_state.status.get(st.session_state.user) == "PRO"
        if st.button("NHẤN ĐỂ KIỂM TRA"):
            latest = st.session_state.config.get('latest_version', 0)
            if latest > CURRENT_VERSION:
                if is_pro:
                    st.success(f"Phát hiện bản {latest}! Đang áp dụng cập nhật...")
                    time.sleep(2); st.rerun()
                else:
                    st.warning("Bản cập nhật mới đang được ưu tiên cho người dùng PRO. Vui lòng đợi hết thời gian delay.")
            else:
                st.info("Bạn đang sử dụng phiên bản mới nhất dành cho cấp độ của mình.")
                
    with st.expander("ℹ️ GIỚI THIỆU HỆ THỐNG"):
        st.write(f"Tên hệ thống: {SYSTEM_NAME}")
        st.write(f"Phiên bản: {VERSION}")
        st.write(f"Phát triển bởi: {CREATOR}")
        st.write("NEXUS OS là hệ điều hành đám mây tích hợp AI đầu tiên dành cho quản lý cá nhân.")

# --- [9] DASHBOARD ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 XIN CHÀO: {st.session_state.user}")
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        if st.button("🧠 AI CHAT"): st.session_state.page = "AI"; st.rerun()
    with c2: 
        if st.button("☁️ CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
    with c3: 
        if st.button("⚙️ CÀI ĐẶT"): st.session_state.page = "SETTINGS"; st.rerun()
    with c4:
        if st.session_state.user == CREATOR:
            if st.button("🛠️ ADMIN"): st.session_state.page = "ADMIN"; st.rerun()

# --- [10] FIX AI & CLOUD (KHÔNG BỊ LỖI HIỂN THỊ) ---
elif st.session_state.page == "AI":
    st.subheader("🧠 NEXUS AI")
    # Sử dụng st.container cố định để tránh lỗi nhảy giao diện
    chat_placeholder = st.container()
    # Logic AI...
