# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI

# --- 1. CONFIG & IDENTITY ---
st.set_page_config(
    page_title="NEXUS V1200", 
    layout="wide", 
    page_icon="💠",
    initial_sidebar_state="collapsed"
)

OWNER_NAME = "Le Tran Thien Phat"
# LƯU Ý: Vui lòng dán API Key thật của bạn vào đây (Ví dụ: "gsk_...")
API_KEY_INPUT = st.secrets.get("GROQ_KEY", "YOUR_API_KEY_HERE") 

# Khởi tạo trạng thái (Bắt đầu từ màn hình LAW)
if 'stage' not in st.session_state: st.session_state.stage = "LAW"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

def change_stage(new_stage):
    st.session_state.stage = new_stage

# --- 2. CSS MASTER ENGINE (RESPONSIVE & HIGH CONTRAST) ---
def apply_universal_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;700&display=swap');
    
    :root {{
        --neon-blue: #00f2ff;
        --bg-dark: #000000;
        --card-bg: #0a0a0a;
    }}

    * {{ font-family: 'Lexend', sans-serif; color: #ffffff; }}
    
    .stApp {{ background-color: var(--bg-dark); }}

    /* LOGO APP TO & ĐẸP */
    .logo-container {{
        text-align: center;
        padding: 40px 0;
    }}
    .main-logo {{
        font-size: 80px;
        font-weight: 800;
        background: linear-gradient(45deg, #00f2ff, #0072ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 15px rgba(0, 242, 255, 0.5));
        margin-bottom: 10px;
        cursor: pointer;
    }}

    /* CARD MENU TỰ THÍCH NGHI (RESPONSIVE) */
    div.stButton > button {{
        width: 100% !important;
        background: var(--card-bg) !important;
        border: 1px solid #333 !important;
        border-radius: 24px !important;
        padding: 50px 20px !important;
        transition: 0.3s all ease;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 700 !important;
    }}
    
    div.stButton > button:hover {{
        border-color: var(--neon-blue) !important;
        box-shadow: 0 0 40px rgba(0, 242, 255, 0.2);
        transform: translateY(-5px);
    }}

    /* KHUNG ĐIỀU KHOẢN (Tối ưu cho mọi thiết bị) */
    .legal-scroll {{
        background: #050505;
        border: 1px solid #222;
        padding: 30px;
        border-radius: 20px;
        height: 60vh;
        overflow-y: auto;
        margin-bottom: 20px;
        border-left: 4px solid var(--neon-blue);
    }}
    .legal-scroll h1 {{ color: var(--neon-blue); }}
    .legal-scroll p {{ color: #aaa; line-height: 1.8; font-size: 1.1rem; }}

    /* Fix lỗi hiển thị chat */
    div[data-testid="stChatMessage"] {{
        background: rgba(255,255,255,0.03);
        border-radius: 15px;
    }}
    
    /* Responsive cho điện thoại */
    @media (max-width: 768px) {{
        .main-logo {{ font-size: 50px; }}
        div.stButton > button {{ padding: 30px 10px !important; font-size: 1rem !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. AI HANDLER (FIX ASCII ERROR) ---
def call_nexus_ai(user_prompt):
    if "YOUR_API_KEY" in API_KEY_INPUT:
        return "He thong chua co API Key. Vui long kiem tra lai."
        
    try:
        client = OpenAI(api_key=API_KEY_INPUT, base_url="https://api.groq.com/openai/v1")
        # System prompt dung tieng Anh de tranh loi encoding trong header neu co
        sys_instr = f"You are Nexus OS by {OWNER_NAME}. Focus on user needs. Answer in Vietnamese."
        
        msgs = [{"role": "system", "content": sys_instr}]
        for m in st.session_state.chat_history:
            msgs.append({"role": m["role"], "content": m["content"]})
        msgs.append({"role": "user", "content": user_prompt})

        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, stream=True)
        return response
    except Exception as e:
        return f"Error: {str(e)}"

# --- 4. MÀN HÌNH CHỨC NĂNG ---

def screen_law():
    apply_universal_theme()
    st.markdown("""
        <div class='logo-container'>
            <div class='main-logo'>NEXUS OS</div>
            <p>UNIVERSAL MASTER EDITION</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="legal-scroll">
        <h1>📜 DIEU KHOAN SU DUNG</h1>
        <p>Chao mung ban den voi he dieu hanh tri tue duoc phat trien boi <b>{OWNER_NAME}</b>.</p>
        <h2>1. Trai nghiem nguoi dung</h2>
        <p>Chung toi toi uu hoa giao dien cho ca Laptop, Tablet va Smartphone. Ban co the truy cap Nexus o bat cu dau.</p>
        <h2>2. Quyen rieng tu</h2>
        <p>Moi du lieu tro chuyen se bi xoa bo sau khi phien lam viec ket thuc. Chung toi ton trong su rieng tu tuyet doi cua ban.</p>
        <h2>3. Ban quyen</h2>
        <p>San pham thuoc so huu cua <b>{OWNER_NAME}</b>. Vui long khong sao chep duoi moi hinh thuc.</p>
        <h2>4. Hieu nang</h2>
        <p>He thong su dung cong nghe Neural Network tien tien nhat de phan hoi cau hoi cua ban.</p>
        <p><i>(Cuon xuong de xac nhan va vao menu chinh)</i></p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("TOI DONG Y VOI CAC DIEU KHOAN ✅", use_container_width=True):
        change_stage("MENU"); st.rerun()

def screen_menu():
    apply_universal_theme()
    st.markdown("""
        <div class='logo-container'>
            <div class='main-logo'>NEXUS HUB</div>
            <p>Chon mot giao thuc de bat dau</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Grid thich nghi
    col1, col2 = st.columns(2)
    with col1:
        st.button("💬\n\nKICH HOAT CHAT AI", on_click=change_stage, args=("CHAT",))
    with col2:
        st.button("📊\n\nHE THONG & INFO", on_click=change_stage, args=("INFO",))
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📜 DOC LAI DIEU KHOAN", use_container_width=True):
        change_stage("LAW"); st.rerun()

def screen_chat():
    apply_universal_theme()
    c1, c2 = st.columns([8, 2])
    c1.title("🧬 NEURAL CORE")
    if c2.button("🏠 MENU", use_container_width=True):
        change_stage("MENU"); st.rerun()
        
    # Chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Nhap thong diep..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            placeholder = st.empty(); full_res = ""
            stream = call_nexus_ai(prompt)
            if isinstance(stream, str):
                st.error(stream)
            else:
                for chunk in stream:
                    content = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                    if content:
                        full_res += content
                        placeholder.markdown(full_res + "▌")
                placeholder.markdown(full_res)
                st.session_state.chat_history.append({"role": "assistant", "content": full_res})

# --- 5. ĐIỀU HƯỚNG CHÍNH ---
if st.session_state.stage == "LAW": screen_law()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "INFO":
    apply_universal_theme()
    st.title("⚙️ THONG TIN")
    st.write(f"Developer: **{OWNER_NAME}**")
    st.write("Version: V1200 Universal Master")
    if st.button("🏠 QUAY LAI MENU"):
        change_stage("MENU"); st.rerun()
