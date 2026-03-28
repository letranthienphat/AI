# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime, timedelta

# --- [1] KHỞI TẠO CẤU HÌNH CỐ ĐỊNH ---
CONFIG = {
    "CREATOR": "Thiên Phát",
    "MASTER_PASS": "nexus os gateway",
    "VERSION": "11.000",
    "FILE_DATA": "nexus_core_v11.json"
}

st.set_page_config(page_title="NEXUS OS", layout="wide", initial_sidebar_state="collapsed")

# --- [2] UI & NÚT HOME TÀNG HÌNH ---
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
        position: fixed; top: 15px; left: 15px; width: 42px; height: 42px;
        background: rgba(255,255,255,0.2); border: 1px solid rgba(34, 211, 238, 0.5);
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        text-decoration: none; z-index: 9999; transition: 0.5s; opacity: 0.4;
    }}
    .floating-home:hover {{ opacity: 1; background: #22d3ee; border: 2px solid white; }}
    </style>
    <a href="/?p=DASHBOARD" target="_self" class="floating-home">🏠</a>
    """, unsafe_allow_html=True)

# --- [3] ANTIBOT: GIÁM SÁT NGẦM (SILENT CHECK) ---
def silent_antibot():
    if 'verified' not in st.session_state:
        st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
        _, center, _ = st.columns([1, 2, 1])
        with center:
            st.markdown("### 🛡️ XÁC THỰC TRUY CẬP")
            # Chỉ hiện ô tick, không gợi ý hành vi
            check = st.checkbox("Tôi không phải là người máy")
            
            # Dùng JS lấy thông số thiết bị và thời gian thực
            screen_w = streamlit_js_eval(js_expressions="window.innerWidth", key="scr_w")
            
            if check:
                if screen_w: # Nếu JS trả về giá trị (không phải bot headless)
                    with st.spinner("Đang kiểm tra bảo mật..."):
                        time.sleep(1.2) # Tạo khoảng nghỉ để giả lập phân tích
                        st.session_state.verified = True
                        st.rerun()
                else:
                    st.error("🛑 Không thể xác định thiết bị. Truy cập bị từ chối.")
                    st.stop()
        st.stop()

# --- [4] QUẢN LÝ DỮ LIỆU GITHUB (PHÂN TẦNG MÃ NGUỒN) ---
def load_nexus_data():
    # Giả lập logic lấy từ GitHub: data.json sẽ có { "stable_code": "...", "beta_code": "..." }
    # Ở đây tôi gộp vào session_state để xử lý nội bộ
    if 'db' not in st.session_state:
        st.session_state.db = {
            "users": {CONFIG["CREATOR"]: CONFIG["MASTER_PASS"]},
            "pro_users": [],
            "blacklist": [],
            "codes": {"PHAT2026": {"type": "vinh-vien"}},
            "updates": {
                "stable": "V10.900",
                "beta": "V11.000",
                "delay_days": 7,
                "release_date": "2026-03-25"
            }
        }

# --- [5] TRANG CÀI ĐẶT (SETTINGS) ---
def settings_page():
    st.header("⚙️ CÀI ĐẶT & HỆ THỐNG")
    if st.button("🔙 QUAY LẠI DASHBOARD"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    t1, t2, t3 = st.tabs(["💎 KÍCH HOẠT", "🆙 CẬP NHẬT", "ℹ️ GIỚI THIỆU"])
    
    with t1:
        code_in = st.text_input("Nhập mã 8 ký tự", max_chars=8).upper()
        if st.button("XÁC NHẬN"):
            if code_in in st.session_state.db["codes"]:
                st.session_state.db["pro_users"].append(st.session_state.user)
                st.success("💎 Đã kích hoạt quyền lợi PRO!")
            else: st.error("Mã không hợp lệ!")

    with t2:
        is_pro = st.session_state.user in st.session_state.db["pro_users"]
        st.write(f"Phiên bản hiện tại: **{CONFIG['VERSION']}**")
        
        if st.button("KIỂM TRA CẬP NHẬT"):
            target_v = st.session_state.db["updates"]["beta"]
            if is_pro:
                st.success(f"Phát hiện bản {target_v}! Nhấn để tải về ngay.")
            else:
                st.warning(f"Bản {target_v} đang trong giai đoạn ưu tiên cho PRO. Người dùng FREE sẽ nhận được sau 7 ngày.")

    with t3:
        st.markdown(f"""
        **NEXUS OS** là hệ thống bảo mật cá nhân được phát triển bởi **{CONFIG['CREATOR']}**.
        - Trạng thái: Hoạt động bình thường
        - Bảo mật: Cấp độ 5 (Sentinel)
        """)

# --- [6] MAIN NAVIGATION ---
apply_ui()
silent_antibot() # Bước 1: Qua cửa bảo mật ngầm
load_nexus_data() # Bước 2: Tải dữ liệu

if 'page' not in st.session_state:
    st.session_state.page = "AUTH"

# Kiểm tra Blacklist thiết bị (Fingerprint)
dev_id = hashlib.md5(st.context.headers.get("User-Agent", "none").encode()).hexdigest()[:10]
if dev_id in st.session_state.db["blacklist"]:
    st.error("🛑 THIẾT BỊ NÀY ĐÃ BỊ CHẶN TRUY CẬP.")
    st.stop()

# --- XỬ LÝ TRANG ---
if st.session_state.page == "AUTH":
    st.title("🛡️ ĐĂNG NHẬP")
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("XÁC THỰC"):
        # Sửa lỗi MASTER_PASS bằng cách gọi từ CONFIG
        if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
            st.session_state.user = u
            st.session_state.page = "DASHBOARD"
            st.rerun()
        else:
            st.error("Sai thông tin!")

elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 XIN CHÀO, {st.session_state.user}")
    c = st.columns(4)
    if c[0].button("🧠 AI"): st.session_state.page = "AI"; st.rerun()
    if c[1].button("☁️ CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
    if c[2].button("⚙️ CÀI ĐẶT"): st.session_state.page = "SETTINGS"; st.rerun()
    if c[3].button("🛠️ ADMIN"): 
        if st.session_state.user == CONFIG["CREATOR"]:
            st.session_state.page = "ADMIN"
            st.rerun()

elif st.session_state.page == "SETTINGS":
    settings_page()

# Các mục AI, Cloud, Admin sẽ tiếp tục logic ở đây...
