# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests
import streamlit_javascript as st_js

# -------------------- [1] CẤU HÌNH & DỮ LIỆU --------------------
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V5100"
FILE_DATA = "data.json"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
except:
    st.error("Vui lòng kiểm tra Secrets GH_TOKEN và GH_REPO!")
    st.stop()

st.set_page_config(page_title="NEXUS OS GATEWAY", layout="wide", initial_sidebar_state="collapsed")

# -------------------- [2] GIAO DIỆN & ANIMATION --------------------
def apply_gateway_ui():
    st.markdown("""
    <style>
    /* Nền đen sâu hoàn toàn */
    .stApp { background-color: #000000 !important; }
    
    /* Container chính */
    .gateway-container {
        display: flex; justify-content: center; align-items: center;
        height: 100vh; width: 100%; position: fixed;
        top: 0; left: 0; z-index: 9999; background: #000;
    }

    /* Kiểu chữ uốn lượn và mượt mà */
    .intro-text {
        font-family: 'Courier New', Courier, monospace;
        color: white; font-size: 3rem; font-weight: bold;
        position: absolute; opacity: 0;
        text-align: center; letter-spacing: 5px;
        filter: blur(10px);
        animation: waveFlow 3s ease-in-out forwards;
    }

    @keyframes waveFlow {
        0% { opacity: 0; transform: translateY(20px) scale(0.9); filter: blur(15px); }
        20% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0px); }
        80% { opacity: 1; transform: translateY(0) scale(1.05); filter: blur(0px); }
        100% { opacity: 0; transform: translateY(-20px) scale(1.1); filter: blur(15px); }
    }

    /* Biểu tượng Gateway cuối cùng */
    .nexus-logo {
        width: 150px; height: 150px; border: 3px solid white;
        border-radius: 20px; opacity: 0;
        animation: finalLogo 5s ease-in-out 18s forwards; /* Hiện sau 18 giây chuỗi chữ */
        display: flex; justify-content: center; align-items: center;
        box-shadow: 0 0 50px rgba(255,255,255,0.2);
    }
    
    .nexus-logo::after {
        content: "NEXUS"; color: white; font-size: 1.2rem; letter-spacing: 3px;
        animation: pulse 2s infinite;
    }

    @keyframes finalLogo {
        0% { opacity: 0; transform: scale(0.5) rotate(-45deg); }
        20% { opacity: 1; transform: scale(1) rotate(0deg); }
        100% { opacity: 1; transform: scale(1); }
    }

    @keyframes pulse {
        0%, 100% { opacity: 0.5; } 50% { opacity: 1; text-shadow: 0 0 20px white; }
    }

    /* Trình tự delay cho từng chữ */
    .t1 { animation-delay: 0s; }
    .t2 { animation-delay: 3s; }
    .t3 { animation-delay: 6s; }
    .t4 { animation-delay: 9s; color: #00f2ff; text-shadow: 0 0 20px #00f2ff; } /* Super A.I! */
    .t5 { animation-delay: 12s; font-size: 3.5rem; }
    .t6 { animation-delay: 15s; font-size: 1.5rem; color: #aaa; }
    </style>

    <div class="gateway-container">
        <div class="intro-text t1">WELCOME</div>
        <div class="intro-text t2">TO</div>
        <div class="intro-text t3">THIS</div>
        <div class="intro-text t4">SUPER A.I!</div>
        <div class="intro-text t5">NEXUS OS GATEWAY</div>
        <div class="intro-text t6">THE NEW VERSION IS RELEASE!</div>
        <div class="nexus-logo"></div>
    </div>
    """, unsafe_allow_html=True)

# -------------------- [3] LOGIC XỬ LÝ --------------------
if 'stage' not in st.session_state:
    st.session_state.stage = "GATEWAY"

def main():
    if st.session_state.stage == "GATEWAY":
        apply_gateway_ui()
        # Tổng thời gian: 3s * 6 câu + 5s logo = ~23 giây
        # Nhưng để mượt, ta chờ xong các chữ rồi mới chuyển sang Login
        time.sleep(23) 
        st.session_state.stage = "AUTH"
        st.rerun()

    elif st.session_state.stage == "AUTH":
        # CSS cho màn hình đăng nhập (Nền đen chữ trắng)
        st.markdown("""<style>
            .stApp { background-color: #000000 !important; }
            h1, p, label { color: white !important; }
            .stButton>button { border: 1px solid white !important; background: transparent !important; color: white !important; }
        </style>""", unsafe_allow_html=True)
        
        st.markdown("<h1 style='text-align:center;'>🛡️ NEXUS LOGIN</h1>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("LOGIN", use_container_width=True):
                with st.spinner("Đang kiểm tra bảo mật..."):
                    time.sleep(2) # Giả lập kiểm tra bảo mật
                    st.success("Truy cập thành công!")
                    # Lưu logic phiên bản tại đây như yêu cầu trước của Phát
                    st.session_state.stage = "MENU"
                    st.rerun()

if __name__ == "__main__":
    main()
