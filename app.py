import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random
import time

# --- 1. CẤU HÌNH HỆ THỐNG & GIAO DIỆN ---
st.set_page_config(page_title="NEXUS OS v51.0", layout="wide", page_icon="🌐")

# Giao diện Cyberpunk/Dark Titan
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #0f172a 0%, #020617 100%); color: #e2e8f0; }
    [data-testid="stSidebar"] { background-color: rgba(15, 23, 42, 0.95) !important; border-right: 1px solid #1e293b; }
    
    /* Hiệu ứng thẻ App */
    .card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 16px;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .card:hover {
        border-color: #38bdf8;
        transform: translateY(-5px);
        box-shadow: 0 10px 25px -5px rgba(56, 189, 248, 0.3);
    }
    
    /* Bong bóng chat */
    .user-msg { background: #0284c7; color: white; padding: 12px; border-radius: 15px 15px 0 15px; margin: 10px 0 10px auto; width: fit-content; max-width: 80%; }
    .ai-msg { background: #1e293b; border-left: 4px solid #38bdf8; padding: 12px; border-radius: 15px 15px 15px 0; margin: 10px auto 10px 0; width: fit-content; max-width: 80%; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO DỮ LIỆU ---
if 'db_users' not in st.session_state:
    st.session_state.db_users = {"admin": "123", "user": "123"} # Tài khoản mặc định

if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'user_role': None,
        'user_name': None,
        'page': 'login',
        'messages': []
    })

# --- 3. LÕI XỬ LÝ AI ---
def nexus_ai_engine(prompt):
    try:
        keys = st.secrets["GROQ_KEYS"]
        client = OpenAI(api_key=random.choice(keys), base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        return response, "Groq"
    except:
        try:
            genai.configure(api_key=st.secrets["GEMINI_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            return model.generate_content(prompt, stream=True), "Gemini"
        except:
            return None, None

# --- 4. CÁC MÀN HÌNH ---

# A. TRANG ĐĂNG NHẬP / ĐĂNG KÝ
def show_auth():
    st.title("🌐 NEXUS QUANTUM LOGIN")
    tab1, tab2, tab3 = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký", "👤 Khách"])
    
    with tab1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("Xác thực hệ thống"):
            if u in st.session_state.db_users and st.session_state.db_users[u] == p:
                st.session_state.update({'logged_in': True, 'user_role': 'Member', 'user_name': u, 'page': 'dashboard'})
                st.rerun()
            else: st.error("Sai thông tin!")

    with tab2:
        new_u = st.text_input("Tên tài khoản mới")
        new_p = st.text_input("Mật khẩu mới", type="password")
        if st.button("Tạo tài khoản"):
            if new_u and new_p:
                st.session_state.db_users[new_u] = new_p
                st.success("Đăng ký thành công! Hãy quay lại Đăng nhập.")
            else: st.warning("Không được để trống.")

    with tab3:
        st.write("Truy cập với quyền hạn hạn chế.")
        if st.button("Vào chế độ Khách"):
            st.session_state.update({'logged_in': True, 'user_role': 'Guest', 'user_name': 'Guest_User', 'page': 'dashboard'})
            st.rerun()

# B. TRANG CHỦ (DASHBOARD)
def show_dashboard():
    st.title(f"🚀 Chào mừng, {st.session_state.user_name}")
    st.caption(f"Quyền hạn: {st.session_state.user_role}")
    
    cols = st.columns(3)
    with cols[0]:
        st.markdown('<div class="card"><h2>🤖</h2><h3>Neural Chat</h3><p>Trò chuyện với AI Llama 3.3</p></div>', unsafe_allow_html=True)
        if st.button("Mở Terminal"): st.session_state.page = 'chat'; st.rerun()
    with cols[1]:
        st.markdown('<div class="card"><h2>📊</h2><h3>Data Analys</h3><p>Phân tích dữ liệu (Sắp ra mắt)</p></div>', unsafe_allow_html=True)
        st.button("🔒 Locked", disabled=True, key="b1")
    with cols[2]:
        st.markdown('<div class="card"><h2>⚙️</h2><h3>Settings</h3><p>Cấu hình Nexus OS</p></div>', unsafe_allow_html=True)
        if st.button("Mở Cấu hình"): st.session_state.page = 'settings'; st.rerun()

# C. TRANG CHAT AI
def show_chat():
    st.subheader("💬 Nexus Neural Terminal")
    for m in st.session_state.messages:
        role = "user-msg" if m["role"] == "user" else "ai-msg"
        st.markdown(f'<div class="{role}">{m["content"]}</div>', unsafe_allow_html=True)

    if prompt := st.chat_input("Gửi lệnh cho Nexus..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            res_area = st.empty()
            full_text = ""
            resp, engine = nexus_ai_engine(st.session_state.messages[-1]["content"])
            if resp:
                if engine == "Groq":
                    for chunk in resp:
                        if chunk.choices[0].delta.content:
                            full_text += chunk.choices[0].delta.content
                            res_area.markdown(full_text)
                else:
                    for chunk in resp:
                        full_text += chunk.text
                        res_area.markdown(full_text)
                st.session_state.messages.append({"role": "assistant", "content": full_text})
            else:
                st.error("Lỗi kết nối!")

# --- 5. ĐIỀU HƯỚNG CHÍNH ---
if not st.session_state.logged_in:
    show_auth()
else:
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
        st.title("NEXUS MENU")
        if st.button("🏠 Trang chủ"): st.session_state.page = 'dashboard'; st.rerun()
        if st.button("🤖 AI Chat"): st.session_state.page = 'chat'; st.rerun()
        st.divider()
        if st.button("🚪 Đăng xuất"):
            st.session_state.logged_in = False
            st.rerun()

    if st.session_state.page == 'dashboard': show_dashboard()
    elif st.session_state.page == 'chat': show_chat()
    elif st.session_state.page == 'settings': st.write("Cài đặt hệ thống đang được cập nhật...")
