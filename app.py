import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random
import time

# --- 1. THIẾT LẬP GIAO DIỆN TITAN DARK (UI GỐC) ---
st.set_page_config(page_title="Nexus OS V54", layout="wide", page_icon="💠")

# Khởi tạo hình nền
if 'bg' not in st.session_state:
    st.session_state.bg = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=2070"

# CSS chuẩn Titan Dark
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(5, 7, 10, 0.8), rgba(5, 7, 10, 0.8)), url("{st.session_state.bg}");
        background-size: cover;
        color: #ffffff !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: #0a0c10 !important;
        border-right: 1px solid #1e2630;
    }}
    .chat-user {{
        background: #0084ff; color: white; padding: 12px 16px;
        border-radius: 15px 15px 0 15px; margin: 8px 0 8px auto;
        max-width: 80%; width: fit-content;
    }}
    .chat-ai {{
        background: #1c1f26; color: #e0e0e0; padding: 12px 16px;
        border-radius: 15px 15px 15px 0; margin: 8px auto 8px 0;
        max-width: 80%; width: fit-content; border-left: 3px solid #00d2ff;
    }}
    .stButton>button {{
        width: 100%; border-radius: 8px; background: #1c1f26; 
        color: white; border: 1px solid #1e2630;
    }}
    .stButton>button:hover {{ border-color: #00d2ff; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. HỆ THỐNG TÀI KHOẢN (BÍ MẬT) ---
if 'users' not in st.session_state:
    st.session_state.users = {"admin": "8888"}  # Tài khoản chủ lực

if 'auth' not in st.session_state:
    st.session_state.update({
        'ok': False, 'user': None, 'role': 'Guest', 'page': 'home', 'chat_log': []
    })

# --- 3. LÕI XỬ LÝ AI ---
def call_ai(p):
    try:
        keys = st.secrets["GROQ_KEYS"]
        client = OpenAI(api_key=random.choice(keys), base_url="https://api.groq.com/openai/v1")
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": p}], stream=True), "Groq"
    except:
        try:
            genai.configure(api_key=st.secrets["GEMINI_KEY"])
            return genai.GenerativeModel('gemini-1.5-flash').generate_content(p, stream=True), "Gemini"
        except: return None, None

# --- 4. GIAO DIỆN ĐĂNG NHẬP / ĐĂNG KÝ ---
if not st.session_state.ok:
    st.title("💠 NEXUS OS GATEWAY")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔐 Đăng nhập")
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("Truy cập"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.update({'ok': True, 'user': u, 'role': 'Admin' if u == 'admin' else 'Member'})
                st.rerun()
            else: st.error("Sai thông tin!")
            
    with col2:
        st.subheader("📝 Tạo tài khoản")
        nu = st.text_input("Tên mới")
        np = st.text_input("Mật khẩu mới", type="password")
        if st.button("Đăng ký ngay"):
            if nu and np:
                st.session_state.users[nu] = np
                st.success("Xong! Đăng nhập đi bạn.")
            else: st.warning("Điền đủ vào chứ!")
    
    if st.button("👤 Vào xem với quyền Khách"):
        st.session_state.update({'ok': True, 'user': 'Khách', 'role': 'Guest'})
        st.rerun()

# --- 5. GIAO DIỆN CHÍNH (SIDEBAR ĐIỀU HƯỚNG) ---
else:
    with st.sidebar:
        st.title("💠 NEXUS OS")
        st.write(f"Chào, **{st.session_state.user}**")
        st.caption(f"Quyền hạn: {st.session_state.role}")
        st.divider()
        if st.button("🏠 Màn hình chính"): st.session_state.page = 'home'; st.rerun()
        if st.button("🤖 Trợ lý AI"): st.session_state.page = 'chat'; st.rerun()
        if st.button("🤫 Khu vực bí mật"): st.session_state.page = 'vault'; st.rerun()
        if st.button("⚙️ Cài đặt"): st.session_state.page = 'settings'; st.rerun()
        st.divider()
        if st.button("🔴 Thoát"): st.session_state.ok = False; st.rerun()

    # MÀN HÌNH CHỦ
    if st.session_state.page == 'home':
        st.title(f"Xin chào {st.session_state.user}!")
        st.info("Hệ thống Titan Dark đã sẵn sàng.")
        st.write("Dùng menu bên trái để bắt đầu khám phá.")

    # MÀN HÌNH CHAT
    elif st.session_state.page == 'chat':
        st.title("🤖 AI Terminal")
        for m in st.session_state.chat_log:
            role = "chat-user" if m["role"] == "user" else "chat-ai"
            st.markdown(f'<div class="{role}">{m["content"]}</div>', unsafe_allow_html=True)

        if p := st.chat_input("Hỏi gì đó..."):
            st.session_state.chat_log.append({"role": "user", "content": p})
            st.markdown(f'<div class="chat-user">{p}</div>', unsafe_allow_html=True)
            with st.empty():
                box = st.empty(); full = ""
                res, eng = call_ai(p)
                if res:
                    for chunk in res:
                        t = chunk.choices[0].delta.content if eng == "Groq" else chunk.text
                        if t: full += t; box.markdown(f'<div class="chat-ai">{full} ▌</div>', unsafe_allow_html=True)
                    box.markdown(f'<div class="chat-ai">{full}</div>', unsafe_allow_html=True)
                    st.session_state.chat_log.append({"role": "assistant", "content": full})

    # MÀN HÌNH BÍ MẬT
    elif st.session_state.page == 'vault':
        if st.session_state.role != 'Admin':
            st.error("⛔ Cảnh báo: Bạn không có quyền Admin để xem khu vực này!")
        else:
            st.title("🤫 PHÒNG BÍ MẬT (Chỉ Admin)")
            st.write("Nơi lưu trữ các file nhạy cảm và ghi chú ẩn.")
            st.text_area("Nhập nhật ký bí mật của bạn:", "Hôm nay tôi đã...")
            st.warning("Mọi dữ liệu ở đây sẽ mất khi Refresh trình duyệt (Bản Pro sẽ lưu vĩnh viễn).")

    # MÀN HÌNH CÀI ĐẶT
    elif st.session_state.page == 'settings':
        st.title("⚙️ Cài đặt")
        st.subheader("Đổi diện mạo")
        new_bg = st.text_input("Link ảnh nền:", st.session_state.bg)
        if st.button("Lưu thay đổi"):
            st.session_state.bg = new_bg
            st.rerun()
