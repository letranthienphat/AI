# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V3750 - CLEAR CONTRAST"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
    FILE_DATA = "data.json"
except:
    st.error("Thiếu cấu hình Secrets!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. GIAO DIỆN SƯƠNG TRẮNG CHỮ ĐEN (WHITE GLASS) ---
def apply_ui():
    t = st.session_state.theme
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] else "background-color: #0e1117;"
    
    st.markdown(f"""
    <style>
    /* Nền ứng dụng */
    .stApp {{ {bg_style} }}

    /* ÉP CHỮ ĐEN TRÊN TOÀN HỆ THỐNG */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, 
    .stMarkdown p, .stMarkdown li, [data-testid="stHeader"] {{
        color: #000000 !important;
        font-weight: 500 !important;
    }}

    /* LỚP SƯƠNG TRẮNG MỜ (WHITE FROSTED GLASS) */
    .glass-card, div[data-testid="stChatMessage"], [data-testid="stSidebar"] {{
        background: rgba(255, 255, 255, 0.75) !important; /* Trắng sáng hơn */
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-radius: 15px;
        padding: 20px;
    }}

    /* NÚT BẤM - ĐẬM ĐÀ HƠN */
    div.stButton > button {{
        width: 100%; border-radius: 10px; font-weight: 700;
        border: 1px solid #000000 !important;
        background: rgba(255, 255, 255, 0.9) !important;
        color: #000000 !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }}
    div.stButton > button:hover {{
        background: {t['primary_color']} !important;
        color: #000000 !important;
        border-color: {t['primary_color']} !important;
    }}

    /* Ô NHẬP LIỆU - VIỀN ĐEN RÕ RÀNG */
    input, textarea {{
        background: rgba(255, 255, 255, 0.9) !important;
        color: #000000 !important;
        border: 1px solid #000000 !important;
    }}
    
    /* Fix cho sidebar chữ không bị lẫn */
    [data-testid="stSidebar"] * {{
        color: #000000 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. MÀN HÌNH ĐIỀU KHOẢN (ĐÃ FIX CHỮ ĐEN) ---
def screen_terms():
    apply_ui()
    st.title("📜 ĐIỀU KHOẢN SỬ DỤNG")
    
    # Nội dung nằm trong class glass-card để có sương trắng
    st.markdown(f"""
    <div class="glass-card">
        <h3 style="color: black;">Xác nhận truy cập - {st.session_state.auth_status.upper()}</h3>
        <p style="color: black;">1. Hệ thống Nexus OS ưu tiên tính minh bạch và bảo mật.</p>
        <p style="color: black;">2. Mọi hành vi spam hoặc phá hoại AI sẽ bị khóa tài khoản vĩnh viễn.</p>
        <p style="color: black;">3. Dữ liệu của bạn thuộc về bạn, Lê Trần Thiên Phát chỉ hỗ trợ nền tảng.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    agree = st.checkbox("Tôi đồng ý với các quy định trên.")
    if agree and st.button("TIẾP TỤC"):
        if st.session_state.auth_status != "Guest":
            if st.session_state.auth_status not in st.session_state.agreed_users:
                st.session_state.agreed_users.append(st.session_state.auth_status)
                # Hàm save_github() ở bản trước vẫn giữ nguyên nhé Phát
                from app import save_github
                save_github()
        st.session_state.stage = "MENU"; st.rerun()

# --- 4. MÀN HÌNH ĐĂNG KÝ (2 LẦN MẬT KHẨU) ---
def screen_auth():
    apply_ui()
    st.title("🛡️ NEXUS OS GATEWAY")
    t1, t2, t3 = st.tabs(["🔑 LOGIN", "📝 REGISTER", "👤 GUEST"])
    
    with t2:
        nu = st.text_input("Username mới", key="reg_u")
        np1 = st.text_input("Password", type="password", key="reg_p1")
        np2 = st.text_input("Confirm Password", type="password", key="reg_p2")
        if st.button("TẠO TÀI KHOẢN"):
            if np1 == np2 and len(np1) > 0:
                st.session_state.users[nu] = np1
                # save_github()
                st.success("Đã tạo! Qua tab Login để vào.")
            else: st.error("Mật khẩu không khớp hoặc trống!")
    # (Các phần login và guest giữ nguyên như V3700)
