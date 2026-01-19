import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random

# --- 1. CẤU HÌNH GIAO DIỆN TITAN DARK (CHUẨN GỐC) ---
st.set_page_config(page_title="Nexus OS V54.1", layout="wide")

# Khởi tạo dữ liệu nếu chưa có
if 'users' not in st.session_state:
    st.session_state.users = {"admin": "8888"}
if 'auth' not in st.session_state:
    st.session_state.auth = {'ok': False, 'user': None, 'role': 'Guest', 'page': 'home'}
if 'chat_log' not in st.session_state:
    st.session_state.chat_log = []
if 'bg' not in st.session_state:
    st.session_state.bg = "https://wallpaperaccess.com/full/1155013.jpg"

# CSS Đẹp như bản đầu tiên
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("{st.session_state.bg}");
        background-size: cover; color: white;
    }}
    [data-testid="stSidebar"] {{ background-color: #0a0c10 !important; border-right: 1px solid #1e2630; }}
    .chat-user {{ background: #0084ff; padding: 12px; border-radius: 15px 15px 0 15px; margin: 10px 0 10px auto; width: fit-content; max-width: 80%; }}
    .chat-ai {{ background: #1c1f26; border-left: 3px solid #00d2ff; padding: 12px; border-radius: 15px 15px 15px 0; margin: 10px auto 10px 0; width: fit-content; max-width: 80%; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM GỌI AI ---
def get_response(prompt):
    try:
        keys = st.secrets["GROQ_KEYS"]
        client = OpenAI(api_key=random.choice(keys), base_url="https://api.groq.com/openai/v1")
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}], stream=True), "Groq"
    except:
        try:
            genai.configure(api_key=st.secrets["GEMINI_KEY"])
            return genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt, stream=True), "Gemini"
        except: return None, None

# --- 3. MÀN HÌNH ĐĂNG NHẬP (NẾU CHƯA AUTH) ---
if not st.session_state.auth['ok']:
    st.title("💠 NEXUS OS GATEWAY")
    tab1, tab2 = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký"])
    
    with tab1:
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("Truy cập"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth.update({'ok': True, 'user': u, 'role': 'Admin' if u == 'admin' else 'Member'})
                st.rerun()
            else: st.error("Sai tài khoản rồi!")
            
    with tab2:
        nu = st.text_input("Tên tài khoản mới")
        np = st.text_input("Mật khẩu mới", type="password")
        if st.button("Đăng ký tài khoản"):
            if nu and np:
                st.session_state.users[nu] = np
                st.success("Đăng ký xong! Qua tab Đăng nhập để vào nhé.")
            else: st.warning("Vui lòng điền đủ thông tin.")
    
    if st.button("👤 Vào quyền Khách"):
        st.session_state.auth.update({'ok': True, 'user': 'Guest', 'role': 'Guest'})
        st.rerun()

# --- 4. GIAO DIỆN CHÍNH ---
else:
    with st.sidebar:
        st.title("💠 NEXUS MENU")
        st.write(f"Cấp độ: **{st.session_state.auth['role']}**")
        st.divider()
        menu = st.selectbox("Menu", ["Màn hình chính", "Chat AI", "Phòng bí mật 🕵️", "Cài đặt"])
        if st.button("🚪 Đăng xuất"):
            st.session_state.auth['ok'] = False
            st.rerun()

    if menu == "Màn hình chính":
        st.title(f"Chào mừng, {st.session_state.auth['user']}")
        st.info("Hệ thống Titan Dark đang hoạt động bình thường.")

    elif menu == "Chat AI":
        st.title("🤖 Neural Terminal")
        for m in st.session_state.chat_log:
            role = "chat-user" if m["role"] == "user" else "chat-ai"
            st.markdown(f'<div class="{role}">{m["content"]}</div>', unsafe_allow_html=True)

        if p := st.chat_input("Hỏi gì đó..."):
            st.session_state.chat_log.append({"role": "user", "content": p})
            st.rerun()
        
        # Xử lý phản hồi AI
        if st.session_state.chat_log and st.session_state.chat_log[-1]["role"] == "user":
            with st.chat_message("assistant"):
                box = st.empty(); full = ""
                res, eng = get_response(st.session_state.chat_log[-1]["content"])
                if res:
                    for chunk in res:
                        t = chunk.choices[0].delta.content if eng == "Groq" else chunk.text
                        if t: full += t; box.markdown(f'<div class="chat-ai">{full} ▌</div>', unsafe_allow_html=True)
                    box.markdown(f'<div class="chat-ai">{full}</div>', unsafe_allow_html=True)
                    st.session_state.chat_log.append({"role": "assistant", "content": full})

    elif menu == "Phòng bí mật 🕵️":
        if st.session_state.auth['role'] != 'Admin':
            st.error("⛔ Bạn không có quyền Admin để xem khu vực này!")
        else:
            st.title("🤫 PHÒNG BÍ MẬT")
            st.write("Dữ liệu tuyệt mật của bạn nằm ở đây.")
            st.text_area("Ghi chú bí mật:", "Chỉ có 'admin' mới thấy cái này...")

    elif menu == "Cài đặt":
        st.title("⚙️ Cài đặt")
        new_bg = st.text_input("Dán link hình nền mới:", st.session_state.bg)
        if st.button("Lưu thay đổi"):
            st.session_state.bg = new_bg
            st.rerun()
