# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(
    page_title="NEXUS V1300", 
    layout="wide", 
    page_icon="💠",
    initial_sidebar_state="collapsed"
)

OWNER_NAME = "Lê Trần Thiên Phát"
# CHÚ Ý: Dán mã API Groq của bạn vào đây
API_KEY_REAL = st.secrets.get("GROQ_KEY", "DÁN_API_KEY_CỦA_BẠN_VÀO_ĐÂY") 

# Quản lý trạng thái màn hình
if 'stage' not in st.session_state: st.session_state.stage = "LAW"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []

def set_stage(stage_name):
    st.session_state.stage = stage_name

# --- 2. GIAO DIỆN TITAN (TỐI ƯU ĐA THIẾT BỊ) ---
def apply_style():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;700;900&display=swap');
    
    * {{ font-family: 'Be Vietnam Pro', sans-serif; color: #FFFFFF; }}
    
    .stApp {{ background-color: #000000; }}

    /* LOGO SIÊU LỚN */
    .hero-logo {{
        text-align: center;
        padding: 60px 0 20px 0;
    }}
    .logo-text {{
        font-size: clamp(60px, 10vw, 120px);
        font-weight: 900;
        background: linear-gradient(to right, #00f2ff, #0072ff, #00f2ff);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 3s linear infinite;
        filter: drop-shadow(0 0 20px rgba(0, 242, 255, 0.4));
    }}
    @keyframes shine {{
        to {{ background-position: 200% center; }}
    }}

    /* CARD MENU LỚN */
    div.stButton > button {{
        width: 100% !important;
        background: #0a0a0a !important;
        border: 1px solid #222 !important;
        border-radius: 30px !important;
        padding: 60px 20px !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        display: flex;
        flex-direction: column;
    }}
    
    div.stButton > button:hover {{
        border-color: #00f2ff !important;
        background: rgba(0, 242, 255, 0.05) !important;
        box-shadow: 0 15px 40px rgba(0, 242, 255, 0.2);
        transform: scale(1.02);
    }}

    /* KHUNG ĐIỀU KHOẢN */
    .tos-container {{
        background: #050505;
        border: 1px solid #1a1a1a;
        padding: 40px;
        border-radius: 25px;
        height: 550px;
        overflow-y: auto;
        margin-bottom: 25px;
        box-shadow: inset 0 0 20px rgba(0,0,0,1);
    }}
    .tos-container h1, .tos-container h2 {{ color: #00f2ff; }}
    .tos-container p {{ color: #e0e0e0; line-height: 1.9; font-size: 1.15rem; }}

    /* CHAT BOX */
    div[data-testid="stChatMessage"] {{
        background: rgba(255,255,255,0.02);
        border: 1px solid #111;
        border-radius: 20px;
        margin-bottom: 15px;
    }}
    
    /* RESPONSIVE FIX */
    @media (max-width: 768px) {{
        div.stButton > button {{ padding: 40px 10px !important; font-size: 1.1rem !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI XỬ LÝ AI ---
def get_response(user_input):
    if "DÁN_API_KEY" in API_KEY_REAL:
        return "⚠️ Hệ thống chưa có API Key hợp lệ. Vui lòng kiểm tra lại mã nguồn."
    
    try:
        client = OpenAI(api_key=API_KEY_REAL, base_url="https://api.groq.com/openai/v1")
        system_msg = f"Bạn là Nexus OS, trợ lý thông minh do {OWNER_NAME} phát triển. Trả lời hữu ích, súc tích và tập trung vào người dùng."
        
        msgs = [{"role": "system", "content": system_msg}]
        for m in st.session_state.chat_log:
            msgs.append({"role": m["role"], "content": m["content"]})
        msgs.append({"role": "user", "content": user_input})

        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, stream=True)
    except Exception as e:
        return f"❌ Lỗi kết nối: {str(e)}"

# --- 4. CÁC MÀN HÌNH GIAO DIỆN ---

def show_law_screen():
    apply_style()
    st.markdown("<div class='hero-logo'><div class='logo-text'>NEXUS OS</div></div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="tos-container">
        <h1>📜 ĐIỀU KHOẢN DỊCH VỤ</h1>
        <p>Chào mừng bạn đã truy cập vào hệ thống Nexus V1300. Đây là sản phẩm trí tuệ được thiết kế và vận hành bởi <b>{OWNER_NAME}</b>.</p>
        <h2>1. Trải nghiệm người dùng hàng đầu</h2>
        <p>Giao diện được tối ưu hóa cho tất cả các thiết bị: Laptop, Máy tính bảng và Điện thoại di động. Bạn sẽ luôn có trải nghiệm mượt mà nhất.</p>
        <h2>2. Bảo mật dữ liệu</h2>
        <p>Mọi nội dung trò chuyện sẽ được xóa sạch sau khi bạn đóng trình duyệt. Chúng tôi không lưu giữ bí mật của người dùng.</p>
        <h2>3. Quyền hạn Admin</h2>
        <p>Admin <b>{OWNER_NAME}</b> có toàn quyền nâng cấp và thay đổi hệ thống để mang lại hiệu năng tốt nhất cho cộng đồng.</p>
        <h2>4. Trách nhiệm AI</h2>
        <p>AI trả lời dựa trên dữ liệu lớn, hãy sử dụng thông tin một cách thông thái. Nexus sẽ luôn đồng hành cùng bạn.</p>
        <p align="center"><i>(Vui lòng cuộn xuống để đọc hết và xác nhận)</i></p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("TÔI ĐÃ ĐỌC VÀ ĐỒNG Ý ✅", use_container_width=True):
        set_stage("MENU"); st.rerun()

def show_menu_screen():
    apply_style()
    st.markdown("<div class='hero-logo'><div class='logo-text'>MENU</div></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("💬\n\nKÍCH HOẠT CHAT AI", on_click=set_stage, args=("CHAT",))
    with col2:
        st.button("🛡️\n\nĐIỀU KHOẢN", on_click=set_stage, args=("LAW",))
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("ℹ️ THÔNG TIN HỆ THỐNG", use_container_width=True):
        set_stage("INFO"); st.rerun()

def show_chat_screen():
    apply_style()
    c1, c2 = st.columns([8, 2])
    c1.title("🧬 LÕI XỬ LÝ NEURAL")
    if c2.button("🏠 MENU", use_container_width=True):
        set_stage("MENU"); st.rerun()

    # Hiển thị lịch sử chat
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Hỏi Nexus bất cứ điều gì..."):
        st.session_state.chat_log.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            holder = st.empty(); full_res = ""
            stream = get_response(prompt)
            if isinstance(stream, str):
                st.error(stream)
            else:
                for chunk in stream:
                    content = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                    if content:
                        full_res += content
                        holder.markdown(full_res + "▌")
                holder.markdown(full_res)
                st.session_state.chat_log.append({"role": "assistant", "content": full_res})

# --- 5. ĐIỀU HƯỚNG CHÍNH ---
if st.session_state.stage == "LAW": show_law_screen()
elif st.session_state.stage == "MENU": show_menu_screen()
elif st.session_state.stage == "CHAT": show_chat_screen()
elif st.session_state.stage == "INFO":
    apply_style()
    st.title("⚙️ THÔNG TIN HỆ THỐNG")
    st.markdown(f"""
    <div style='background:#0a0a0a; padding:40px; border-radius:30px; border:1px solid #222;'>
        <h3>Nhà phát triển: {OWNER_NAME}</h3>
        <p>Phiên bản: Definitive Edition V1300</p>
        <p>Công nghệ: Streamlit + Groq Neural Cloud</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🏠 QUAY LẠI MENU"):
        set_stage("MENU"); st.rerun()
