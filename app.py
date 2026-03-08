# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json

# --- 1. CẤU HÌNH & BỘ NHỚ ---
st.set_page_config(page_title="NEXUS V2500", layout="wide", initial_sidebar_state="expanded")

# Thông tin cố định
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V2500 - PERSISTENCE TITAN"

try:
    API_LIST = st.secrets.get("GROQ_KEYS", [])
    ACTIVE_KEY = API_LIST[0] if API_LIST else st.secrets.get("GROQ_KEY", "")
except:
    ACTIVE_KEY = ""

# Khởi tạo Session State
if 'stage' not in st.session_state: st.session_state.stage = "IDENTITY"
if 'user_data' not in st.session_state: st.session_state.user_data = {"name": "", "gender": "", "remember": False}
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'saved_chats' not in st.session_state: st.session_state.saved_chats = {} # {title: log}
if 'info_tab' not in st.session_state: st.session_state.info_tab = "CREATOR"

def nav(p): st.session_state.stage = p

# --- 2. HỆ THỐNG MÃ HÓA & TIỆN ÍCH ---
def encode_chat(log):
    json_str = json.dumps(log)
    return base64.b64encode(json_str.encode()).decode()

def decode_chat(data):
    try:
        json_str = base64.b64decode(data.encode()).decode()
        return json.loads(json_str)
    except: return None

# --- 3. CSS PLASMA GLOW & HIGH CONTRAST ---
def apply_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-color: #000000; color: #ffffff; }}
    
    /* NÚT BẤM PLASMA GLOW */
    div.stButton > button {{
        width: 100% !important; min-height: 60px !important;
        background: #0a0a0a !important; border: 1px solid #333 !important;
        border-radius: 15px !important; color: #fff !important;
        font-weight: 700 !important; transition: all 0.1s ease;
    }}
    div.stButton > button:active {{
        border-color: #00f2ff !important;
        box-shadow: 0 0 20px #00f2ff !important;
        transform: scale(0.98);
    }}

    /* PHẢN HỒI AI TRẮNG TUYẾT */
    div[data-testid="stChatMessageAssistant"] {{
        background: #FFFFFF !important; border-radius: 20px !important;
        padding: 20px !important; margin: 10px 0 !important;
    }}
    div[data-testid="stChatMessageAssistant"] * {{ color: #000000 !important; font-size: 1.1rem; }}

    /* THANH SIDEBAR */
    section[data-testid="stSidebar"] {{ background-color: #050505 !important; border-right: 1px solid #222; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. CÁC MÀN HÌNH ---

def screen_identity():
    apply_ui()
    st.markdown("<h1 style='text-align:center;'>NEXUS IDENTITY</h1>", unsafe_allow_html=True)
    with st.container():
        name = st.text_input("Tên định danh:", value=st.session_state.user_data['name'])
        gender = st.radio("Giới tính:", ["Nam", "Nữ", "Khác"], horizontal=True)
        remember = st.checkbox("Ghi nhớ đăng nhập trên thiết bị này", value=st.session_state.user_data['remember'])
        
        if st.button("KHỞI CHẠY HỆ THỐNG 🚀"):
            if name:
                st.session_state.user_data = {"name": name, "gender": gender, "remember": remember}
                nav("MENU"); st.rerun()
            else: st.warning("Vui lòng nhập tên.")

def screen_menu():
    apply_ui()
    st.markdown(f"<h1 style='text-align:center;'>NEXUS HUB</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#888;'>Người dùng: {st.session_state.user_data['name']} | {st.session_state.user_data['gender']}</p>", unsafe_allow_html=True)
    
    st.button("💬 TRUY CẬP NEURAL CORE", on_click=nav, args=("CHAT",))
    st.button("📂 QUẢN LÝ LƯU TRỮ", on_click=nav, args=("STORAGE",))
    st.button("⚙️ THÔNG TIN & ĐIỀU KHOẢN", on_click=nav, args=("INFO",))
    st.button("🔄 THOÁT / ĐỔI ID", on_click=nav, args=("IDENTITY",))

def screen_chat():
    apply_ui()
    with st.sidebar:
        st.title("Nexus History")
        search = st.text_input("Tìm cuộc trò chuyện...")
        for title in st.session_state.saved_chats:
            if search.lower() in title.lower():
                if st.button(f"📄 {title}", key=f"save_{title}"):
                    st.session_state.chat_log = st.session_state.saved_chats[title]
                    st.rerun()
        st.write("---")
        if st.button("🏠 VỀ MENU"): nav("MENU"); st.rerun()

    st.markdown("### 🧬 NEURAL INTERFACE")
    
    # Hiển thị Chat
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("Nhập lệnh..."):
        st.session_state.chat_log.append({"role": "user", "content": p})
        st.rerun()

    if st.session_state.chat_log and st.session_state.chat_log[-1]["role"] == "user":
        with st.chat_message("assistant"):
            box = st.empty(); full = ""
            client = OpenAI(api_key=ACTIVE_KEY, base_url="https://api.groq.com/openai/v1")
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "Bạn là Nexus AI chuyên nghiệp. Trả lời trung lập, tập trung vào kiến thức. Không tự nhắc tên người tạo trừ khi được hỏi."},
                          {"role": "user", "content": st.session_state.chat_log[-1]["content"]}],
                stream=True
            )
            for chunk in res:
                c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                if c:
                    full += c
                    box.markdown(full + "▌")
                    time.sleep(0.005)
            box.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            st.rerun()

def screen_storage():
    apply_ui()
    st.title("📂 QUẢN LÝ LƯU TRỮ")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Xuất dữ liệu")
        if st.session_state.chat_log:
            chat_data = encode_chat(st.session_state.chat_log)
            st.download_button("TẢI VỀ FILE .TXT (MÃ HÓA)", data=chat_data, file_name="nexus_chat.txt")
        else: st.info("Chưa có cuộc trò chuyện để lưu.")
        
        title_save = st.text_input("Tên lưu trữ tạm thời:")
        if st.button("LƯU VÀO THƯ VIỆN APP"):
            if title_save:
                st.session_state.saved_chats[title_save] = st.session_state.chat_log
                st.success(f"Đã lưu '{title_save}'")
    
    with col2:
        st.subheader("Nhập dữ liệu")
        uploaded_file = st.file_uploader("Tải lên file .txt mã hóa", type="txt")
        if uploaded_file is not None:
            raw_data = uploaded_file.read().decode()
            decoded = decode_chat(raw_data)
            if decoded:
                if st.button("KHÔI PHỤC CUỘC TRÒ CHUYỆN"):
                    st.session_state.chat_log = decoded
                    nav("CHAT"); st.rerun()
            else: st.error("File không hợp lệ hoặc bị lỗi mã hóa.")

    st.button("🏠 QUAY LẠI", on_click=nav, args=("MENU",))

def screen_info():
    apply_ui()
    st.title("⚙️ SYSTEM INFORMATION")
    t1, t2, t3 = st.tabs(["👤 NGƯỜI SÁNG TẠO", "📊 HỆ THỐNG", "📜 ĐIỀU KHOẢN"])
    
    with t1:
        st.markdown(f"### Kiến trúc sư trưởng: **{CREATOR_NAME}**")
        st.write("Học sinh lớp 7A1 - Trường THCS-THPT Nguyễn Huệ.")
        st.info("Chịu trách nhiệm toàn bộ về thiết kế giao diện và vận hành logic của Nexus.")
        
    with t2:
        st.write(f"**Phiên bản:** {VERSION}")
        st.write("**Lịch sử cập nhật:**")
        st.write("- Tích hợp cổng giới tính và Ghi nhớ đăng nhập.")
        st.write("- Hệ thống lưu trữ/xuất/nhập file mã hóa.")
        st.write("- AI trung lập, tối ưu hóa sự riêng tư của người tạo.")
        
    with t3:
        st.markdown("""
        1. **Sử dụng:** Người dùng cam kết sử dụng hệ thống vào mục đích lành mạnh.
        2. **Dữ liệu:** File xuất ra được mã hóa Base64 để bảo mật nội dung cơ bản.
        3. **Quyền hạn:** **Lê Trần Thiên Phát** giữ quyền tối cao đối với mã nguồn này.
        """)

    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.write(f"© 2026 Nexus OS by **{CREATOR_NAME}**")
    st.button("🏠 QUAY LẠI MENU", on_click=nav, args=("MENU",))

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "IDENTITY": screen_identity()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "STORAGE": screen_storage()
elif st.session_state.stage == "INFO": screen_info()
