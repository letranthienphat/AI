# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH HỆ THỐNG ---
CONFIG = {
    "CREATOR": "Thiên Phát",
    "MASTER_PASS": "nexus os gateway",
    "VERSION": 12.0,
    "FILE_DATA": "nexus_vault_v12.json"
}

st.set_page_config(page_title="NEXUS ULTIMATE", layout="wide", initial_sidebar_state="collapsed")

# --- [2] GIAO DIỆN & NÚT HOME (FIX HIỂN THỊ) ---
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
    /* NÚT HOME NỔI - CHUẨN PHÁT YÊU CẦU */
    .floating-home {{
        position: fixed; top: 20px; left: 20px; width: 50px; height: 50px;
        background: rgba(255,255,255,0.2); border: 2px solid rgba(34, 211, 238, 0.6);
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        text-decoration: none; z-index: 10000; transition: 0.4s; opacity: 0.5;
        font-size: 24px; color: white !important;
    }}
    .floating-home:hover {{ opacity: 1; background: #22d3ee; transform: scale(1.1); box-shadow: 0 0 20px #22d3ee; }}
    
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    <a href="/?p=DASHBOARD" target="_self" class="floating-home">🏠</a>
    """, unsafe_allow_html=True)

# --- [3] ANTIBOT: SILENT MONITORING (FIX LỖI TRỐNG TRƠN) ---
def silent_antibot():
    if 'verified' not in st.session_state:
        _, center, _ = st.columns([1, 2, 1])
        with center:
            st.markdown("<h2 style='text-align:center;'>🛡️ SECURITY CHECK</h2>", unsafe_allow_html=True)
            tick = st.checkbox("Tôi không phải là người máy")
            
            # Theo dõi ngầm bằng thư viện
            try:
                browser_info = streamlit_js_eval(js_expressions="window.navigator.userAgent", key="bot_check")
                if tick:
                    if browser_info: # Nếu lấy được thông tin trình duyệt -> Người thật
                        with st.spinner("Đang phân tích hành vi..."):
                            time.sleep(1.5)
                            st.session_state.verified = True
                            st.rerun()
                    else:
                        st.warning("⚠️ Đang chờ tín hiệu xác thực thiết bị...")
            except:
                # Nếu thư viện lỗi, cho hiện nút bấm thủ công để không bị trống trang
                if tick and st.button("TIẾP TỤC"):
                    st.session_state.verified = True
                    st.rerun()
        st.stop()

# --- [4] DỮ LIỆU & PHÂN TẦNG CẬP NHẬT ---
def init_data():
    if 'db' not in st.session_state:
        # Giả lập database (Trong thực tế sẽ fetch từ GitHub)
        st.session_state.db = {
            "users": {CONFIG["CREATOR"]: CONFIG["MASTER_PASS"]},
            "pro_users": [],
            "blacklist": [],
            "codes": {"PHAT2026": "PRO_PERM"},
            "update_config": {
                "latest_v": 12.5,
                "release_date": "2026-03-25",
                "free_delay": 7
            }
        }

# --- [5] TRANG CÀI ĐẶT (GUEST & PRO) ---
def settings_page():
    st.header("⚙️ CÀI ĐẶT HỆ THỐNG")
    t1, t2, t3 = st.tabs(["💎 KÍCH HOẠT PRO", "🆙 CẬP NHẬT", "ℹ️ GIỚI THIỆU"])
    
    with t1:
        c_in = st.text_input("Mã kích hoạt (8 ký tự)").upper()
        if st.button("XÁC NHẬN MÃ"):
            if c_in in st.session_state.db["codes"]:
                st.session_state.db["pro_users"].append(st.session_state.user)
                st.success("💎 NÂNG CẤP PRO THÀNH CÔNG!")
            else: st.error("Mã không hợp lệ.")

    with t2:
        is_pro = st.session_state.user in st.session_state.db["pro_users"]
        st.write(f"Phiên bản hiện tại: **{CONFIG['VERSION']}**")
        if st.button("KIỂM TRA UPDATE"):
            conf = st.session_state.db["update_config"]
            available_date = datetime.strptime(conf["release_date"], "%Y-%m-%d") + timedelta(days=conf["free_delay"])
            
            if is_pro:
                st.success(f"Phát hiện bản {conf['latest_v']}! Bạn có quyền cập nhật ngay.")
            elif datetime.now() < available_date:
                st.warning(f"Bản cập nhật mới đang bị delay cho Guest. Vui lòng quay lại sau ngày {available_date.date()}.")
            else:
                st.success(f"Bản cập nhật {conf['latest_v']} đã sẵn sàng cho người dùng Free!")

    with t3:
        st.write("NEXUS OS v12.0 - Pháo đài số của Thiên Phát.")

# --- [6] ADMIN PANEL (FULL) ---
def admin_page():
    st.header("🛠️ QUẢN TRỊ VIÊN")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚙️ Cấu hình Guest")
        new_delay = st.number_input("Số ngày delay update", 0, 30, st.session_state.db["update_config"]["free_delay"])
        if st.button("CẬP NHẬT DELAY"):
            st.session_state.db["update_config"]["free_delay"] = new_delay
            st.success("Đã áp dụng!")
            
    with col2:
        st.subheader("🚫 Quản lý Blacklist")
        st.write(st.session_state.db["blacklist"])
        if st.button("XÓA BLACKLIST"):
            st.session_state.db["blacklist"] = []
            st.rerun()

# --- [7] ĐIỀU HƯỚNG CHÍNH ---
apply_ui()
silent_antibot()
init_data()

if 'page' not in st.session_state: st.session_state.page = "AUTH"

# Kiểm tra Blacklist
dev_id = hashlib.md5(st.context.headers.get("User-Agent", "none").encode()).hexdigest()[:10]
if dev_id in st.session_state.db["blacklist"]:
    st.error("🛑 THIẾT BỊ NÀY ĐÃ BỊ CHẶN VĨNH VIỄN.")
    st.stop()

# Xử lý Logic Trang
if st.session_state.page == "AUTH":
    st.title("🛡️ NEXUS LOGIN")
    u = st.text_input("Tài khoản")
    p = st.text_input("Mật khẩu", type="password")
    if st.button("ĐĂNG NHẬP"):
        if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
            st.session_state.user = u
            st.session_state.page = "DASHBOARD"
            st.rerun()
        else: st.error("Sai thông tin!")

elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 XIN CHÀO, {st.session_state.user}")
    cols = st.columns(4)
    if cols[0].button("🧠 AI"): st.session_state.page = "AI"; st.rerun()
    if cols[1].button("☁️ CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
    if cols[2].button("⚙️ CÀI ĐẶT"): st.session_state.page = "SETTINGS"; st.rerun()
    if cols[3].button("🛠️ ADMIN") and st.session_state.user == CONFIG["CREATOR"]:
        st.session_state.page = "ADMIN"; st.rerun()

elif st.session_state.page == "SETTINGS": settings_page()
elif st.session_state.page == "ADMIN": admin_page()
