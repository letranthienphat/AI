# -*- coding: utf-8 -*-
import streamlit as st
import time

# Cấu hình trang
st.set_page_config(page_title="NEXUS OS GATEWAY", layout="wide", initial_sidebar_state="collapsed")

def apply_samsung_style_animation():
    st.markdown("""
    <style>
    /* Nền đen tuyệt đối */
    .stApp { background-color: #000000 !important; }

    .boot-container {
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        height: 100vh; width: 100%; position: fixed; top: 0; left: 0; z-index: 9999; background: #000;
    }

    /* Hiệu ứng vẽ Logo NEXUS bằng đường nét (SVG) */
    .svg-logo {
        width: 200px; height: 200px;
        stroke: #ffffff; stroke-width: 2; fill: none;
        stroke-dasharray: 600; stroke-dashoffset: 600;
        animation: drawLogo 4s ease-in-out forwards, glow 2s infinite 4s;
    }

    @keyframes drawLogo {
        0% { stroke-dashoffset: 600; transform: rotate(-10deg) scale(0.8); opacity: 0; }
        50% { opacity: 1; }
        100% { stroke-dashoffset: 0; transform: rotate(0deg) scale(1); }
    }

    @keyframes glow {
        0%, 100% { filter: drop-shadow(0 0 5px #fff); }
        50% { filter: drop-shadow(0 0 20px #fff); }
    }

    /* Chuỗi chữ uốn lượn xuất hiện */
    .text-flow {
        font-family: 'Segoe UI', sans-serif;
        color: white; font-size: 1.8rem; font-weight: 300;
        position: absolute; opacity: 0;
        letter-spacing: 4px;
        animation: textSequence 3s ease-in-out forwards;
    }

    @keyframes textSequence {
        0% { opacity: 0; transform: scale(0.8) translateY(10px); filter: blur(10px); }
        30% { opacity: 1; transform: scale(1) translateY(0); filter: blur(0px); }
        70% { opacity: 1; transform: scale(1.05) translateY(0); filter: blur(0px); }
        100% { opacity: 0; transform: scale(1.1) translateY(-10px); filter: blur(10px); }
    }

    /* Delay cho từng câu chữ theo ý Phát */
    .t1 { animation-delay: 0.5s; }
    .t2 { animation-delay: 3.5s; }
    .t3 { animation-delay: 6.5s; }
    .t4 { animation-delay: 9.5s; font-weight: bold; color: #00f2ff; text-shadow: 0 0 15px #00f2ff; }
    .t5 { animation-delay: 12.5s; font-size: 2.5rem; }
    .t6 { animation-delay: 15.5s; font-size: 1.2rem; color: #888; }
    
    /* Logo cuối cùng xuất hiện nhịp nhàng */
    .final-nexus {
        position: absolute; opacity: 0;
        animation: fadeIn 5s ease-in-out 18.5s forwards;
        text-align: center;
    }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

    </style>

    <div class="boot-container">
        <div class="text-flow t1">WELCOME</div>
        <div class="text-flow t2">TO</div>
        <div class="text-flow t3">THIS</div>
        <div class="text-flow t4">SUPER A.I!</div>
        <div class="text-flow t5">NEXUS OS GATEWAY</div>
        <div class="text-flow t6">THE NEW VERSION IS RELEASE!</div>

        <div class="final-nexus">
            <svg class="svg-logo" viewBox="0 0 100 100">
                <rect x="10" y="10" width="80" height="80" rx="15" />
                <path d="M30 30 L70 70 M70 30 L30 70" stroke-width="4"/> </svg>
            <h2 style="color:white; margin-top:20px; letter-spacing:10px;">NEXUS</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

# -------------------- LOGIC CHÍNH --------------------
if 'stage' not in st.session_state:
    st.session_state.stage = "BOOT"

def main():
    if st.session_state.stage == "BOOT":
        apply_samsung_style_animation()
        # Chờ 24 giây để hoàn tất toàn bộ chuỗi animation
        time.sleep(24)
        st.session_state.stage = "LOGIN"
        st.rerun()

    elif st.session_state.stage == "LOGIN":
        st.markdown("<style>.stApp { background: #000; }</style>", unsafe_allow_html=True)
        st.title("🛡️ NEXUS OS GATEWAY")
        
        # Form đăng nhập với Spinner không đơ
        with st.form("login_form"):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            submitted = st.form_submit_button("LOGIN")
            
            if submitted:
                with st.spinner("🚀 Checking Security Gateway..."):
                    time.sleep(2)
                    st.success(f"Welcome back, {user}!")
                    # Ở đây Phát thêm logic lưu Version người dùng như bản trước nhé

if __name__ == "__main__":
    main()
