# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V3800 - CRYSTAL CLEAR"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
    FILE_DATA = "data.json"
except:
    st.error("Thiếu Secrets!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. GIAO DIỆN KÍNH TRONG SUỐT (CRYSTAL GLASS) ---
def apply_ui():
    t = st.session_state.theme
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] else "background-color: #0e1117;"
    
    st.markdown(f"""
    <style>
    /* Nền ứng dụng - Trả lại hình nền mã nguồn */
    .stApp {{ {bg_style} }}

    /* CHỮ ĐEN ĐẬM - Để đọc được trên lớp kính trong */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, 
    .stMarkdown p, .stMarkdown li {{
        color: #000000 !important;
        font-weight: 600 !important;
    }}

    /* LỚP KÍNH TRONG SUỐT (CRYSTAL GLASS) */
    /* Giảm alpha xuống 0.35 để không còn bị trắng xóa */
    .glass-card, div[data-testid="stChatMessage"], [data-testid="stSidebar"] {{
        background: rgba(255, 255, 255, 0.35) !important; 
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 10px;
    }}

    /* NÚT BẤM - TRONG SUỐT CÓ VIỀN */
    div.stButton > button {{
        width: 100%; border-radius: 10px; font-weight: 700;
        border: 2px solid #000000 !important;
        background: rgba(255, 255, 255, 0.5) !important;
        color: #000000 !important;
    }}
    div.stButton > button:hover {{
        background: #000000 !important;
        color: #ffffff !important;
    }}

    /* SIDEBAR CHỮ ĐEN */
    [data-testid="stSidebar"] * {{
        color: #000000 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. MÀN HÌNH ĐIỀU KHOẢN ---
def screen_terms():
    apply_ui()
    st.title("📜 ĐIỀU KHOẢN SỬ DỤNG")
    
    st.markdown(f"""
    <div class="glass-card">
        <h3>Xác nhận quyền truy cập</h3>
        <p>Chào <b>{st.session_state.auth_status.upper()}</b>, bạn cần đồng ý để tiếp tục:</p>
        <ul>
            <li>Hệ thống ưu tiên trải nghiệm hình nền Crystal Clear.</li>
            <li>Dữ liệu được lưu trữ an toàn và riêng tư.</li>
            <li>Không spam lệnh AI để đảm bảo hiệu suất.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.checkbox("Tôi đã đọc và đồng ý") and st.button("TRUY CẬP NEXUS"):
        if st.session_state.auth_status != "Guest":
            st.session_state.agreed_users.append(st.session_state.auth_status)
            save_github() # Đảm bảo hàm này đã có trong code của anh
        st.session_state.stage = "MENU"; st.rerun()

# --- 4. LUỒNG XÁC THỰC (ĐĂNG KÝ 2 LẦN PASS) ---
def screen_auth():
    apply_ui()
    st.title("🛡️ NEXUS OS GATEWAY")
    t1, t2, t3 = st.tabs(["🔑 LOGIN", "📝 REGISTER", "👤 GUEST"])
    
    with t2:
        nu = st.text_input("Tên đăng ký", key="r_u")
        p1 = st.text_input("Mật khẩu", type="password", key="r_p1")
        p2 = st.text_input("Nhập lại mật khẩu", type="password", key="r_p2")
        if st.button("ĐĂNG KÝ TÀI KHOẢN"):
            if p1 == p2 and p1 != "":
                st.session_state.users[nu] = p1
                save_github()
                st.success("Xong! Qua tab Login nhé.")
            else: st.error("Mật khẩu không khớp!")
    
    with t3:
        st.info("Chế độ khách sẽ không lưu lại lịch sử chat.")
        if st.button("VÀO VỚI QUYỀN KHÁCH"):
            st.session_state.auth_status = "Guest"; st.session_state.stage = "TERMS"; st.rerun()
    # (Tab Login giữ nguyên logic cũ)

# (Đoạn mã điều hướng phía dưới giữ nguyên)
