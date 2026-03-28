# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime, timedelta

# --- [1] CONFIG ---
SYSTEM_NAME = "NEXUS PRO-SENTINEL"
CREATOR = "Thiên Phát"
VERSION = "10.900"
FILE_DATA = "nexus_data_v6.json"

st.set_page_config(page_title=SYSTEM_NAME, layout="wide")

# --- [2] GIAO DIỆN MÀU SẮC THÀNH PHỐ ---
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
    /* Nút Home nổi mờ mờ */
    .floating-home {{
        position: fixed; top: 15px; left: 15px; width: 45px; height: 45px;
        background: rgba(255,255,255,0.3); border: 2px solid #22d3ee;
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        text-decoration: none; z-index: 9999; transition: 0.3s; opacity: 0.6;
    }}
    .floating-home:hover {{ opacity: 1; background: #22d3ee; }}
    </style>
    <a href="/?p=DASHBOARD" target="_self" class="floating-home">🏠</a>
    """, unsafe_allow_html=True)

# --- [3] ANTIBOT: THEO DÕI CHUỘT & CLICK ---
def antibot_gate():
    if 'human_verified' not in st.session_state:
        st.title("🛡️ XÁC THỰC HỆ THỐNG")
        st.write("Vui lòng tick vào ô bên dưới và di chuyển chuột để kích hoạt NEXUS.")
        
        # Sử dụng thư viện để lấy thông tin chuột/vị trí
        mouse_pos = streamlit_js_eval(js_expressions="window.innerWidth", key="mouse_track")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            is_human = st.checkbox("Tôi không phải là người máy")
        
        if is_human:
            # Nếu có phản hồi từ thư viện (tức là JS đang chạy) và đã tick
            if mouse_pos:
                with st.spinner("Đang phân tích hành vi..."):
                    time.sleep(1.5)
                    st.session_state.human_verified = True
                    st.rerun()
            else:
                st.warning("⚠️ Đang kiểm tra tín hiệu chuột...")
        st.stop()

# --- [4] CÀI ĐẶT (SETTINGS) ---
def settings_page():
    st.header("⚙️ CÀI ĐẶT HỆ THỐNG")
    if st.button("🔙 VỀ DASHBOARD"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["💎 KÍCH HOẠT", "🆙 CẬP NHẬT", "ℹ️ THÔNG TIN"])
    
    with tab1:
        st.subheader("Nhập mã 8 ký tự")
        code = st.text_input("Mã ưu đãi", max_chars=8)
        if st.button("ÁP DỤNG"):
            if code in st.session_state.codes:
                st.session_state.status[st.session_state.user] = "PRO"
                st.success("Đã kích hoạt bản PRO vĩnh viễn!")
            else: st.error("Mã không chính xác.")

    with tab2:
        st.subheader("Kiểm tra phiên bản")
        is_pro = st.session_state.status.get(st.session_state.user) == "PRO"
        if st.button("CẬP NHẬT NGAY"):
            if is_pro:
                st.info("Đang kiểm tra mã nguồn mới trên GitHub...")
                st.success("Bản PRO: Đã cập nhật thành công bản mới nhất!")
            else:
                st.warning("Bản FREE: Admin đã đặt delay 7 ngày cho mã nguồn này.")

    with tab3:
        st.write(f"Hệ điều hành: {SYSTEM_NAME}")
        st.write(f"Phiên bản: {VERSION}")
        st.write("Ghi chú: Hệ thống đang giám sát hành vi chống Bot độc hại.")

# --- [5] ADMIN PANEL ---
def admin_page():
    st.header("🛠️ ADMIN CENTER")
    if st.button("🔙 VỀ"): st.session_state.page = "DASHBOARD"; st.rerun()
    
    st.subheader("Cấu hình Cập nhật")
    delay = st.slider("Số ngày delay cho bản Free", 0, 30, 7)
    if st.button("Lưu cấu hình"):
        st.session_state.config['delay'] = delay
        st.success("Đã lưu!")

# --- [6] MAIN NAVIGATION ---
apply_ui()
antibot_gate()

if 'boot' not in st.session_state:
    st.session_state.update({
        "page": "AUTH", "user": None, "boot": True,
        "status": {}, "codes": {"PHAT2026": {"multi": True}}, "config": {"delay": 7}
    })

if st.session_state.page == "AUTH":
    st.title("🛡️ ĐĂNG NHẬP")
    u = st.text_input("Tài khoản")
    p = st.text_input("Mật khẩu", type="password")
    if st.button("TRUY CẬP"):
        if u == CREATOR and p == MASTER_PASS:
            st.session_state.user = u; st.session_state.page = "DASHBOARD"; st.rerun()
        else: st.error("Sai thông tin!")

elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 CHÀO {st.session_state.user}")
    col = st.columns(4)
    if col[0].button("🧠 AI"): st.session_state.page = "AI"; st.rerun()
    if col[1].button("☁️ CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
    if col[2].button("⚙️ CÀI ĐẶT"): st.session_state.page = "SETTINGS"; st.rerun()
    if col[3].button("🛠️ ADMIN"): st.session_state.page = "ADMIN"; st.rerun()

elif st.session_state.page == "SETTINGS":
    settings_page()
