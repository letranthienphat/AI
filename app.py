# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import time, random, json, base64, requests

# -------------------- [1] CẤU HÌNH HỆ THỐNG --------------------
VERSION = "V5100"
CREATOR = "Lê Trần Thiên Phát"
FILE_DATA = "data.json"

WALLPAPERS = [
    "https://images.unsplash.com/photo-1614850523296-d8c1af93d400?q=80&w=2070",
    "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?q=80&w=2071",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072",
    "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=2070"
]

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
except:
    st.error("Cấu hình GitHub Secrets chưa đúng!")
    st.stop()

st.set_page_config(page_title="NEXUS GATEWAY", layout="wide", initial_sidebar_state="collapsed")

# -------------------- [2] FIX LỖI KEYERROR & LOAD DB --------------------
def load_db():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            data = json.loads(content)
            # FIX: Đảm bảo các key luôn tồn tại
            if "users" not in data: data["users"] = {"admin": "123", "Phát": "123"}
            if "user_versions" not in data: data["user_versions"] = {}
            return data
    except: pass
    return {"users": {"admin": "123", "Phát": "123"}, "user_versions": {}}

def save_db(data):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode()).decode()
    payload = {"message": f"Nexus Update {VERSION}", "content": content, "sha": sha}
    requests.put(url, headers=headers, json=payload)

# -------------------- [3] BOOT ANIMATION (SIÊU PHỨC TẠP) --------------------
def show_ultimate_boot():
    boot_html = f"""
    <style>
        body {{ background: black; margin: 0; overflow: hidden; display: flex; align-items: center; justify-content: center; height: 100vh; font-family: 'Inter', sans-serif; }}
        .stage {{ position: relative; width: 600px; height: 400px; display: flex; align-items: center; justify-content: center; }}
        
        /* Chữ uốn lượn biến hình */
        .text-morph {{
            position: absolute; color: white; font-size: 3rem; letter-spacing: 15px; font-weight: 200;
            opacity: 0; filter: blur(20px); animation: morphing 3.5s ease-in-out forwards;
        }}
        @keyframes morphing {{
            0% {{ opacity: 0; filter: blur(20px); transform: scale(0.8) translateY(20px); }}
            30% {{ opacity: 1; filter: blur(0px); transform: scale(1) translateY(0); }}
            70% {{ opacity: 1; filter: blur(0px); transform: scale(1.05); }}
            100% {{ opacity: 0; filter: blur(10px); transform: scale(1.2) translateY(-20px); }}
        }}

        /* Logo Drawing & Assembly */
        .logo-container {{ position: absolute; opacity: 0; animation: logoEntry 5s ease-out 18s forwards; }}
        @keyframes logoEntry {{ 0% {{ opacity: 0; transform: scale(0.5) rotate(-180deg); }} 100% {{ opacity: 1; transform: scale(1) rotate(0deg); }} }}

        .draw-path {{
            fill: none; stroke: white; stroke-width: 1.5; stroke-linecap: round;
            stroke-dasharray: 1000; stroke-dashoffset: 1000;
            animation: drawLine 4s ease-in-out 18.5s forwards;
        }}
        @keyframes drawLine {{ to {{ stroke-dashoffset: 0; }} }}

        .glimmer {{ animation: glimmer 2s infinite alternate 22s; }}
        @keyframes glimmer {{ from {{ filter: drop-shadow(0 0 2px #fff); }} to {{ filter: drop-shadow(0 0 15px #00f2ff); }} }}

        /* Timing Delays */
        .d1 {{ animation-delay: 0s; }} .d2 {{ animation-delay: 3s; }} .d3 {{ animation-delay: 6s; }}
        .d4 {{ animation-delay: 9s; color: #00f2ff; font-weight: bold; }}
        .d5 {{ animation-delay: 12s; font-size: 3.5rem; }} .d6 {{ animation-delay: 15s; font-size: 1.2rem; color: #666; }}
    </style>
    <div class="stage">
        <div class="text-morph d1">WELCOME</div>
        <div class="text-morph d2">TO</div>
        <div class="text-morph d3">THIS</div>
        <div class="text-morph d4">SUPER A.I!</div>
        <div class="text-morph d5">NEXUS GATEWAY</div>
        <div class="text-morph d6">THE NEW VERSION IS RELEASE!</div>

        <div class="logo-container glimmer">
            <svg viewBox="0 0 100 100" width="200" height="200">
                <circle class="draw-path" cx="50" cy="50" r="45" style="animation-duration: 6s;"/>
                <path class="draw-path" d="M30 30 L70 30 L70 70 L30 70 Z" />
                <path class="draw-path" d="M50 20 L50 80 M20 50 L80 50" style="animation-delay: 19s;"/>
                <path class="draw-path" d="M35 35 L65 65 M65 35 L35 65" style="animation-delay: 20s;"/>
            </svg>
            <h1 style="color:white; letter-spacing: 12px; margin-top:20px; font-weight: 100;">NEXUS OS</h1>
        </div>
    </div>
    """
    components.html(boot_html, height=800)

# -------------------- [4] MÀN HÌNH ĐĂNG NHẬP (LỘNG LẪY) --------------------
def show_login():
    if 'bg' not in st.session_state: st.session_state.bg = random.choice(WALLPAPERS)
    
    st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("{st.session_state.bg}"); background-size: cover; }}
    .login-box {{
        background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(25px);
        padding: 60px; border-radius: 40px; border: 1px solid rgba(255,255,255,0.1);
        text-align: center; max-width: 450px; margin: auto; box-shadow: 0 25px 50px rgba(0,0,0,0.5);
    }}
    /* Logo màu sáng phát sáng */
    .bright-logo {{
        font-size: 3rem; font-weight: bold; color: white; letter-spacing: 10px;
        text-shadow: 0 0 20px rgba(255,255,255,0.8); margin-bottom: 30px;
    }}
    .stTextInput>div>div>input {{ background: rgba(255,255,255,0.05) !important; color: white !important; border: 1px solid rgba(255,255,255,0.2) !important; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("<div class='bright-logo'>NEXUS</div>", unsafe_allow_html=True)
    
    u = st.text_input("ACCESS KEY (USERNAME)")
    p = st.text_input("SECURITY PIN", type="password")
    
    if st.button("INITIALIZE GATEWAY", use_container_width=True):
        db = load_db()
        if u in db["users"] and db["users"][u] == p:
            with st.spinner("🚀 Đang đồng bộ phiên bản & kiểm tra Gateway..."):
                time.sleep(2)
                # FIX LỖI KEYERROR: Đảm bảo key user_versions có sẵn
                if "user_versions" not in db: db["user_versions"] = {}
                db["user_versions"][u] = VERSION
                save_db(db)
                st.session_state.user = u
                st.session_state.stage = "MAIN"
                st.rerun()
        else: st.error("Truy cập bị từ chối!")
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------- [5] BÊN TRONG HỆ THỐNG --------------------
def show_main():
    st.markdown("<style>.stApp { background: #000; color: white; }</style>", unsafe_allow_html=True)
    st.sidebar.title("NEXUS GATEWAY")
    st.sidebar.info(f"User: {st.session_state.user}\nVersion: {VERSION}")
    
    menu = st.sidebar.selectbox("Lệnh hệ thống", ["Trang chủ", "AI Chat v2", "Quản trị viên"])
    
    if menu == "Trang chủ":
        st.title("🌌 CHÀO MỪNG ĐẾN VỚI NEXUS GATEWAY")
        st.write("Hệ thống đã sẵn sàng. Mọi tính năng đã được nâng cấp lên mức tối đa.")
    
    elif menu == "AI Chat v2":
        # Phần chat xịn sò của bạn
        st.title("🧠 NEXUS SUPER AI")
        st.chat_message("assistant").write("Tôi là trí tuệ nhân tạo NEXUS. Tôi có thể giúp gì cho Phát?")

# -------------------- [6] ĐIỀU HƯỚNG --------------------
if 'stage' not in st.session_state: st.session_state.stage = "BOOT"

def main():
    if st.session_state.stage == "BOOT":
        show_ultimate_boot()
        time.sleep(25) # Tổng thời gian hiệu ứng
        st.session_state.stage = "LOGIN"
        st.rerun()
    elif st.session_state.stage == "LOGIN":
        show_login()
    elif st.session_state.stage == "MAIN":
        show_main()

if __name__ == "__main__":
    main()
