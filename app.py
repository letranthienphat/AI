# -*- coding: utf-8 -*-
import streamlit as st
import time, random

# -------------------- [1] CẤU HÌNH HỆ THỐNG --------------------
VERSION = "V5100"
CREATOR = "Lê Trần Thiên Phát"

# Danh sách hình nền ngẫu nhiên (Phát có thể thay link ảnh của mình vào đây)
WALLPAPERS = [
    "https://images.unsplash.com/photo-1614850523296-d8c1af93d400?q=80&w=2070",
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1964",
    "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=2070",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072"
]

st.set_page_config(page_title=f"NEXUS GATEWAY {VERSION}", layout="wide", initial_sidebar_state="collapsed")

# -------------------- [2] HIỆU ỨNG KHỞI ĐỘNG (SAMSUNG STYLE) --------------------
def boot_animation():
    # Chọn ngẫu nhiên 1 hình nền để tải trước (cache) trong lúc chờ
    if 'bg_login' not in st.session_state:
        st.session_state.bg_login = random.choice(WALLPAPERS)

    st.markdown(f"""
    <style>
    .stApp {{ background-color: #000000 !important; }}
    
    .boot-box {{
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        height: 100vh; width: 100%; position: fixed; top: 0; left: 0; z-index: 9999; background: #000;
    }}

    /* Chữ uốn lượn */
    .word {{
        color: white; font-family: 'Segoe UI', sans-serif; font-size: 2.5rem;
        position: absolute; opacity: 0; letter-spacing: 5px;
        animation: flowText 3s ease-in-out forwards;
    }}

    @keyframes flowText {{
        0% {{ opacity: 0; transform: scale(0.5) translateY(30px); filter: blur(15px); }}
        30% {{ opacity: 1; transform: scale(1) translateY(0); filter: blur(0px); }}
        70% {{ opacity: 1; transform: scale(1.1); filter: blur(0px); }}
        100% {{ opacity: 0; transform: scale(1.2) translateY(-30px); filter: blur(15px); }}
    }}

    /* Logo vẽ bằng nét (SVG) */
    .nexus-svg {{
        width: 180px; height: 180px; opacity: 0;
        animation: drawPath 4s ease-in-out 18.5s forwards, neonGlow 2s infinite 22.5s;
    }}
    
    .path-line {{
        fill: none; stroke: white; stroke-width: 2;
        stroke-dasharray: 1000; stroke-dashoffset: 1000;
        animation: drawing 4s linear 18.5s forwards;
    }}

    @keyframes drawing {{ to {{ stroke-dashoffset: 0; }} }}
    @keyframes drawPath {{ from {{ opacity: 0; transform: scale(0.8); }} to {{ opacity: 1; transform: scale(1); }} }}
    @keyframes neonGlow {{ 0%, 100% {{ filter: drop-shadow(0 0 5px #fff); }} 50% {{ filter: drop-shadow(0 0 20px #fff); }} }}

    /* Điều chỉnh thời gian xuất hiện */
    .w1 {{ animation-delay: 0.5s; }}
    .w2 {{ animation-delay: 3.5s; }}
    .w3 {{ animation-delay: 6.5s; }}
    .w4 {{ animation-delay: 9.5s; color: #00f2ff; font-weight: bold; }}
    .w5 {{ animation-delay: 12.5s; font-size: 3rem; }}
    .w6 {{ animation-delay: 15.5s; font-size: 1.5rem; color: #888; }}
    </style>

    <div class="boot-box">
        <div class="word w1">WELCOME</div>
        <div class="word w2">TO</div>
        <div class="word w3">THIS</div>
        <div class="word w4">SUPER A.I!</div>
        <div class="word w5">NEXUS OS GATEWAY</div>
        <div class="word w6">THE NEW VERSION IS RELEASE!</div>
        
        <div class="nexus-svg">
            <svg viewBox="0 0 100 100">
                <rect class="path-line" x="10" y="10" width="80" height="80" rx="15" />
                <path class="path-line" d="M30 30 L70 70 M70 30 L30 70" />
            </svg>
            <h2 style="color:white; text-align:center; letter-spacing:10px; font-family: sans-serif;">NEXUS</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

# -------------------- [3] MÀN HÌNH ĐĂNG NHẬP (HÌNH NỀN NGẪU NHIÊN) --------------------
def login_screen():
    bg = st.session_state.bg_login
    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("{bg}");
        background-size: cover; background-position: center;
    }}
    .login-card {{
        background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(15px);
        padding: 40px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.2);
        max-width: 450px; margin: auto; margin-top: 100px;
    }}
    h1, label, p {{ color: white !important; text-shadow: 0 0 10px rgba(0,0,0,0.5); }}
    .stButton>button {{
        width: 100%; border-radius: 10px; background: transparent; border: 1px solid white; color: white;
    }}
    .stButton>button:hover {{ background: white; color: black; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-card'>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;'>NEXUS ACCESS</h1>", unsafe_allow_html=True)
    
    with st.container():
        user = st.text_input("Tài khoản")
        pw = st.text_input("Mật khẩu", type="password")
        
        if st.button("XÁC THỰC GATEWAY"):
            with st.spinner("🚀 Đang kiểm tra bảo mật..."):
                time.sleep(2) # Giả lập kiểm tra bảo mật (hiện vòng xoay không đơ)
                st.session_state.auth_user = user
                st.session_state.stage = "MENU"
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------- [4] ĐIỀU HƯỚNG CHÍNH --------------------
if 'stage' not in st.session_state:
    st.session_state.stage = "BOOT"

def main():
    if st.session_state.stage == "BOOT":
        boot_animation()
        time.sleep(24) # Tổng thời gian animation
        st.session_state.stage = "LOGIN"
        st.rerun()
    
    elif st.session_state.stage == "LOGIN":
        login_screen()

if __name__ == "__main__":
    main()
