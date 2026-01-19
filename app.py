import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random
import time

# --- 1. CẤU HÌNH GIAO DIỆN & HÌNH NỀN ---
st.set_page_config(page_title="NEXUS OS ULTIMATE", layout="wide", page_icon="💠")

# Khởi tạo trạng thái hệ thống
if 'bg_url' not in st.session_state:
    st.session_state.bg_url = "https://images.unsplash.com/photo-1614850523296-d8c1af93d400?q=80&w=2070" # Hình nền mặc định (Nebula)

# CSS cao cấp cho giao diện hệ điều hành
st.markdown(f"""
    <style>
    .stApp {{
        background: url("{st.session_state.bg_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    /* Làm mờ các panel để tạo hiệu ứng Glassmorphism */
    [data-testid="stSidebar"], .stMarkdown, .stChatFloatingInputContainer, .block-container {{
        background: rgba(15, 23, 42, 0.7) !important;
        backdrop-filter: blur(12px);
        border-radius: 15px;
        color: white !important;
    }}
    .stChatMessage {{ background: rgba(30, 41, 59, 0.6) !important; border: 1px solid rgba(255,255,255,0.1); }}
    
    /* Hiệu ứng Desktop Icons */
    .icon-card {{
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 20px;
        border-radius: 20px;
        text-align: center;
        transition: 0.4s;
    }}
    .icon-card:hover {{ background: rgba(56, 189, 248, 0.3); transform: scale(1.05); }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC AI ---
def get_ai_response(prompt):
    try:
        keys = st.secrets["GROQ_KEYS"]
        client = OpenAI(api_key=random.choice(keys), base_url="https://api.groq.com/openai/v1")
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}], stream=True), "Groq"
    except:
        try:
            genai.configure(api_key=st.secrets["GEMINI_KEY"])
            return genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt, stream=True), "Gemini"
        except: return None, None

# --- 3. QUẢN LÝ PHIÊN ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': 'Guest', 'page': 'auth', 'history': []})

# --- 4. CÁC PHÂN VÙNG CHỨC NĂNG ---

# A. MÀN HÌNH KHÓA (AUTH)
if not st.session_state.logged_in:
    st.title("🛡️ NEXUS GATEWAY")
    col1, col2 = st.columns(2)
    with col1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Xâm nhập hệ thống"):
            if u == "admin" and p == "123":
                st.session_state.update({'logged_in': True, 'user': u, 'role': 'Administrator', 'page': 'desktop'})
                st.rerun()
            else: st.error("Từ chối truy cập!")
    with col2:
        if st.button("Tiếp tục với quyền Khách"):
            st.session_state.update({'logged_in': True, 'user': 'Guest', 'role': 'Guest', 'page': 'desktop'})
            st.rerun()

# B. GIAO DIỆN CHÍNH (SIDEBAR & DESKTOP)
else:
    with st.sidebar:
        st.header("💠 Nexus OS")
        st.write(f"👤 {st.session_state.user} ({st.session_state.role})")
        st.divider()
        if st.button("🏠 Màn hình chính"): st.session_state.page = 'desktop'; st.rerun()
        if st.button("🤖 Neural Chat"): st.session_state.page = 'chat'; st.rerun()
        if st.button("⚙️ Cài đặt hệ thống"): st.session_state.page = 'settings'; st.rerun()
        st.divider()
        if st.button("🔴 Logout"): 
            st.session_state.logged_in = False
            st.rerun()

    # TRANG DESKTOP
    if st.session_state.page == 'desktop':
        st.title("🖥️ Workspace")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown('<div class="icon-card"><h1>🤖</h1><h3>Chat AI</h3></div>', unsafe_allow_html=True)
            if st.button("Mở Chat"): st.session_state.page = 'chat'; st.rerun()
        with c2:
            st.markdown('<div class="icon-card"><h1>⚙️</h1><h3>Settings</h3></div>', unsafe_allow_html=True)
            if st.button("Mở Cài đặt"): st.session_state.page = 'settings'; st.rerun()
        with c3:
            st.markdown('<div class="icon-card"><h1>📦</h1><h3>Apps</h3></div>', unsafe_allow_html=True)
            st.button("Soon...")

    # TRANG CHAT
    elif st.session_state.page == 'chat':
        st.title("💬 Neural Terminal")
        for m in st.session_state.history:
            with st.chat_message(m["role"]): st.write(m["content"])
        
        if p := st.chat_input("Nhập lệnh..."):
            st.session_state.history.append({"role": "user", "content": p})
            with st.chat_message("user"): st.write(p)
            with st.chat_message("assistant"):
                res_box = st.empty()
                full = ""
                resp, eng = get_ai_response(p)
                if resp:
                    for chunk in resp:
                        txt = chunk.choices[0].delta.content if eng == "Groq" else chunk.text
                        if txt: full += txt; res_box.markdown(full + "▌")
                    res_box.markdown(full)
                    st.session_state.history.append({"role": "assistant", "content": full})
                    st.caption(f"Engine: {eng}")

    # TRANG CÀI ĐẶT
    elif st.session_state.page == 'settings':
        st.title("⚙️ System Configuration")
        st.write("### 🖼️ Wallpaper")
        new_bg = st.text_input("Dán URL ảnh nền mới:", st.session_state.bg_url)
        if st.button("Cập nhật hình nền"):
            st.session_state.bg_url = new_bg
            st.rerun()
        
        st.divider()
        st.write("### 🛠️ Hardware Info")
        st.info(f"API Pool: 3 Groq Keys Active")
        st.warning(f"Quyền hạn của bạn: {st.session_state.role}")
