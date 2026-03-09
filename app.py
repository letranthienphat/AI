# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import time, random, json, base64, requests
from openai import OpenAI

# -------------------- [1] CẤU HÌNH & DATA --------------------
VERSION = "V5100"
CREATOR = "Lê Trần Thiên Phát"
FILE_DATA = "data.json"

# Danh sách hình nền ngẫu nhiên cho màn hình Login
WALLPAPERS = [
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072",
    "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?q=80&w=2071",
    "https://images.unsplash.com/photo-1502134249126-9f3755a50d78?q=80&w=2070",
    "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=2072"
]

# Kiểm tra Secrets
try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("Thiếu cấu hình Secrets (GH_TOKEN, GH_REPO, GROQ_KEYS)!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {VERSION}", layout="wide", initial_sidebar_state="collapsed")

# -------------------- [2] HÀM XỬ LÝ DỮ LIỆU GITHUB --------------------
def load_db():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            return json.loads(content)
    except: pass
    return {"users": {"admin": "123", "Phát": "123"}, "user_versions": {}}

def save_db(data):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode()).decode()
    payload = {"message": f"Update {VERSION}", "content": content, "sha": sha}
    requests.put(url, headers=headers, json=payload)

# -------------------- [3] HIỆU ỨNG BOOT (SAMSUNG STYLE) --------------------
def show_boot_animation():
    boot_html = f"""
    <style>
        body {{ background-color: black; margin: 0; overflow: hidden; display: flex; align-items: center; justify-content: center; height: 100vh; font-family: 'Segoe UI', sans-serif; }}
        .container {{ position: relative; text-align: center; width: 100%; }}
        
        .word {{ color: white; font-size: 40px; position: absolute; width: 100%; opacity: 0; letter-spacing: 8px; animation: flow 3s ease-in-out forwards; }}
        @keyframes flow {{
            0% {{ opacity: 0; transform: scale(0.6) translateY(30px); filter: blur(10px); }}
            30% {{ opacity: 1; transform: scale(1) translateY(0); filter: blur(0px); }}
            70% {{ opacity: 1; transform: scale(1.1); filter: blur(0px); }}
            100% {{ opacity: 0; transform: scale(1.2) translateY(-30px); filter: blur(10px); }}
        }}

        .logo-box {{ opacity: 0; animation: fadeIn 3s ease-in-out 18s forwards; }}
        @keyframes fadeIn {{ to {{ opacity: 1; }} }}

        svg {{ width: 150px; height: 150px; stroke: white; fill: none; stroke-width: 2; }}
        .path {{ stroke-dasharray: 1000; stroke-dashoffset: 1000; animation: draw 4s linear 18.5s forwards; }}
        @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}

        .w1 {{ animation-delay: 0s; }} .w2 {{ animation-delay: 3s; }} .w3 {{ animation-delay: 6s; }}
        .w4 {{ animation-delay: 9s; color: #00f2ff; text-shadow: 0 0 20px #00f2ff; }}
        .w5 {{ animation-delay: 12s; font-size: 50px; }} .w6 {{ animation-delay: 15s; font-size: 20px; color: #888; }}
    </style>
    <div class="container">
        <div class="word w1">WELCOME</div>
        <div class="word w2">TO</div>
        <div class="word w3">THIS</div>
        <div class="word w4">SUPER A.I!</div>
        <div class="word w5">NEXUS OS GATEWAY</div>
        <div class="word w6">THE NEW VERSION IS RELEASE!</div>
        
        <div class="logo-box">
            <svg viewBox="0 0 100 100">
                <rect class="path" x="10" y="10" width="80" height="80" rx="15" />
                <path class="path" d="M30 30 L70 70 M70 30 L30 70" />
            </svg>
            <h1 style="color:white; letter-spacing: 15px; margin-top: 20px;">NEXUS</h1>
        </div>
    </div>
    """
    components.html(boot_html, height=800)

# -------------------- [4] MÀN HÌNH ĐĂNG NHẬP (RANDOM WP) --------------------
def show_login():
    if 'bg' not in st.session_state: st.session_state.bg = random.choice(WALLPAPERS)
    
    st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("{st.session_state.bg}"); background-size: cover; }}
    .login-card {{
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px);
        padding: 50px; border-radius: 30px; border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center; max-width: 400px; margin: auto;
    }}
    h1, label {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='login-card'>", unsafe_allow_html=True)
    st.markdown("<h1>NEXUS GATEWAY</h1>", unsafe_allow_html=True)
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("ACCESS SYSTEM", use_container_width=True):
        db = load_db()
        if u in db["users"] and db["users"][u] == p:
            with st.spinner("🚀 Verifying Security..."):
                time.sleep(2)
                st.session_state.user = u
                # Lưu version người dùng
                db["user_versions"][u] = VERSION
                save_db(db)
                st.session_state.stage = "MAIN"
                st.rerun()
        else: st.error("Sai tài khoản hoặc mật khẩu!")
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------- [5] GIAO DIỆN CHÍNH (BÊN TRONG) --------------------
def show_main():
    st.markdown("""<style>
        .stApp { background: #0e1117; color: white; }
        [data-testid="stSidebar"] { background: rgba(255,255,255,0.05) !important; }
    </style>""", unsafe_allow_html=True)
    
    user = st.session_state.user
    st.sidebar.title(f"🚀 NEXUS {VERSION}")
    st.sidebar.write(f"Chào, **{user}**")
    
    menu = st.sidebar.radio("MENU GATEWAY", ["Dashboard", "AI Chat", "Social", "Settings"])
    
    if menu == "Dashboard":
        st.title("📊 HỆ THỐNG ĐIỀU KHIỂN")
        col1, col2 = st.columns(2)
        col1.metric("Phiên bản hiện tại", VERSION)
        col2.metric("Trạng thái Gateway", "ONLINE", delta="Stable")
        st.info(f"Chào mừng {user}. Hệ thống của bạn đang chạy ở phiên bản {VERSION}.")

    elif menu == "AI Chat":
        st.title("🧠 NEXUS SUPER AI")
        if "messages" not in st.session_state: st.session_state.messages = []
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Hỏi bất cứ điều gì..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                # Gọi API AI tại đây (giống các bản trước của bạn)
                response = f"Nexus AI đã nhận được lệnh: {prompt}"
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# -------------------- [6] ĐIỀU HƯỚNG --------------------
if 'stage' not in st.session_state: st.session_state.stage = "BOOT"

def main():
    if st.session_state.stage == "BOOT":
        show_boot_animation()
        time.sleep(23)
        st.session_state.stage = "LOGIN"
        st.rerun()
    elif st.session_state.stage == "LOGIN":
        show_login()
    elif st.session_state.stage == "MAIN":
        show_main()

if __name__ == "__main__":
    main()
