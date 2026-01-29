# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="NEXUS V2200", layout="wide", initial_sidebar_state="collapsed")

OWNER_NAME = "Lê Trần Thiên Phát"
OWNER_INFO = "Lớp 7A1 - Trường THCS-THPT Nguyễn Huệ"

try:
    API_LIST = st.secrets.get("GROQ_KEYS", [])
    ACTIVE_KEY = API_LIST[0] if API_LIST else st.secrets.get("GROQ_KEY", "")
except:
    ACTIVE_KEY = ""

# Khởi tạo Session
if 'stage' not in st.session_state: st.session_state.stage = "LAW"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'info_sub' not in st.session_state: st.session_state.info_sub = "CREATOR"

def nav(p): st.session_state.stage = p

# --- 2. CSS TITAN ELITE (TƯƠNG PHẢN CỰC ĐẠI & MOBILE OPTIMIZED) ---
def apply_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-color: #000000; color: #ffffff; }}

    /* LOGO */
    .logo-text {{
        font-size: clamp(40px, 12vw, 85px);
        font-weight: 900; text-align: center; padding: 40px 0;
        background: linear-gradient(180deg, #ffffff, #555);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}

    /* NÚT BẤM TO (DỄ BẤM TRÊN ĐIỆN THOẠI) */
    div.stButton > button {{
        width: 100% !important; min-height: 90px !important;
        background: #0f0f0f !important; border: 1px solid #333 !important;
        border-radius: 20px !important; color: #fff !important;
        font-size: 1.2rem !important; font-weight: 800 !important;
        margin-bottom: 12px; transition: 0.2s;
    }}
    div.stButton > button:hover {{ border-color: #ffffff; background: #1a1a1a; }}

    /* PHẢN HỒI AI (TRẮNG TUYẾT - CHỮ ĐEN) */
    .stChatMessage.assistant {{
        background: #FFFFFF !important;
        border-radius: 20px !important;
        padding: 25px !important;
        margin: 15px 0 !important;
        box-shadow: 0 8px 30px rgba(255,255,255,0.1);
    }}
    .stChatMessage.assistant * {{ color: #000000 !important; font-weight: 500; line-height: 1.6; }}

    /* HIỆP ƯỚC */
    .law-box {{
        background: #050505; border: 1px solid #222; padding: 35px;
        border-radius: 30px; height: 480px; overflow-y: auto;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI AI (XÁC THỰC DANH TÍNH) ---
def call_nexus_ai(prompt):
    if not ACTIVE_KEY: return "⚠️ Lỗi: Chưa cấu hình API Key!"
    try:
        client = OpenAI(api_key=ACTIVE_KEY, base_url="https://api.groq.com/openai/v1")
        # NẠP DANH TÍNH CHUẨN
        instr = f"Bạn là Nexus OS V2200. Người tạo ra bạn là Lê Trần Thiên Phát (anh ấy), học sinh lớp 7A1 Nguyễn Huệ. Tuyệt đối không nói bạn là Meta AI. Hãy gọi người dùng là Lê Trần Thiên Phát và dùng 'anh ấy' để nhắc về người tạo."
        
        return client.chat.completions.create(model="llama-3.3-70b-versatile", 
                                            messages=[{"role": "system", "content": instr},
                                                      {"role": "user", "content": prompt}], 
                                            stream=True)
    except Exception as e: return f"Lỗi kết nối: {str(e)}"

# --- 4. MÀN HÌNH ---

def screen_law():
    apply_ui()
    st.markdown("<div class='logo-text'>NEXUS V2200</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="law-box">
        <h1 style='color:white;'>HIỆP ƯỚC TITAN ELITE</h1>
        <p>Chào mừng <b>{OWNER_NAME}</b> đến với phiên bản tối thượng.</p>
        <p>• <b>Danh tính:</b> Hệ thống xác nhận bạn là người tạo ra duy nhất.</p>
        <p>• <b>Thị giác:</b> Phản hồi AI được tinh chỉnh độ tương phản cực cao, dễ đọc trên mọi thiết bị.</p>
        <p>• <b>Tốc độ:</b> Hiệu ứng chạy chữ mang lại cảm giác xử lý thời gian thực.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("XÁC NHẬN & VÀO HUB ⚡", use_container_width=True):
        nav("MENU"); st.rerun()

def screen_menu():
    apply_ui()
    st.markdown("<div class='logo-text'>CENTRAL HUB</div>", unsafe_allow_html=True)
    st.button("💬 NEURAL CHAT", on_click=nav, args=("CHAT",))
    st.button("🛠️ CHI TIẾT HỆ THỐNG", on_click=nav, args=("INFO",))
    st.button("📜 ĐIỀU KHOẢN", on_click=nav, args=("LAW",))

def screen_chat():
    apply_ui()
    st.markdown("<h3 style='text-align:center;'>NEURAL INTERFACE</h3>", unsafe_allow_html=True)
    
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("Nhập lệnh cho Nexus..."):
        st.session_state.chat_log.append({"role": "user", "content": p})
        st.rerun()

    if st.session_state.chat_log and st.session_state.chat_log[-1]["role"] == "user":
        with st.chat_message("assistant"):
            box = st.empty(); full = ""
            res = call_nexus_ai(st.session_state.chat_log[-1]["content"])
            if isinstance(res, str): st.error(res)
            else:
                # HIỆU ỨNG CHẠY CHỮ
                for chunk in res:
                    c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                    if c:
                        full += c
                        box.markdown(full + "▌") # Con trỏ đang chạy
                        time.sleep(0.01) # Tốc độ chạy chữ
                box.markdown(full)
                st.session_state.chat_log.append({"role": "assistant", "content": full})
                st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.button("🏠 QUAY LẠI MENU", on_click=nav, args=("MENU",), use_container_width=True)

def screen_info():
    apply_ui()
    st.markdown("<div class='logo-text'>SYSTEM INFO</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    if col1.button("👤 NGƯỜI SÁNG TẠO"): st.session_state.info_sub = "CREATOR"
    if col2.button("📊 PHIÊN BẢN & LỊCH SỬ"): st.session_state.info_sub = "VERSION"

    st.markdown("---")
    if st.session_state.info_sub == "CREATOR":
        st.markdown(f"""
        <div style='background:#111; padding:30px; border-radius:20px; border-left:5px solid #fff;'>
            <h3>Người sáng tạo duy nhất</h3>
            <h1 style='color:#fff;'>{OWNER_NAME}</h1>
            <p style='font-size:1.3rem; color:#888;'>{OWNER_INFO}</p>
            <p>Mọi thuật toán và giao diện đều được tinh chỉnh dưới sự giám sát của anh ấy.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background:#111; padding:30px; border-radius:20px;'>
            <h3>Thông tin phiên bản</h3>
            <p>• <b>Phiên bản:</b> V2200 - Titan Elite</p>
            <p>• <b>Cập nhật:</b> 29/01/2026</p>
            <h3>Lịch sử cập nhật</h3>
            <p>- Thêm hiệu ứng chạy chữ (Typewriter).<br>
            - Tách mục Info thành 2 nút bấm riêng biệt.<br>
            - Tăng độ tương phản phản hồi AI (White-Black theme).<br>
            - Sửa lỗi định danh AI (Người tạo: Lê Trần Thiên Phát).</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.button("🏠 QUAY LẠI MENU", on_click=nav, args=("MENU",))

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "LAW": screen_law()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "INFO": screen_info()
