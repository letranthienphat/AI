# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time

# --- 1. CONFIG & SECRETS ---
st.set_page_config(page_title="NEXUS V1800", layout="wide", initial_sidebar_state="collapsed")

OWNER = "Lê Trần Thiên Phát"
# Hệ thống tự động lấy danh sách Keys từ Secret
try:
    API_LIST = st.secrets.get("GROQ_KEYS", [])
    ACTIVE_KEY = API_LIST[0] if API_LIST else st.secrets.get("GROQ_KEY", "")
except:
    ACTIVE_KEY = ""

# Khởi tạo trạng thái
if 'stage' not in st.session_state: st.session_state.stage = "LAW"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'hints' not in st.session_state: 
    st.session_state.hints = ["Tương lai của AI", "Sáng tạo nghệ thuật", "Tối ưu mã nguồn"]

def set_page(p): st.session_state.stage = p

# --- 2. CSS "LIQUID DARK" UI (CỰC ĐẸP & TƯƠNG PHẢN) ---
def apply_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syncopate:wght@400;700&family=Plus+Jakarta+Sans:wght@300;500;800&display=swap');
    
    .stApp {{
        background: radial-gradient(circle at 50% 50%, #0d0d0d 0%, #000000 100%);
        color: #ffffff;
    }}

    /* LOGO NEON BREATHING */
    .logo-container {{
        text-align: center; padding: 80px 0;
        animation: pulse 4s ease-in-out infinite;
    }}
    .logo-text {{
        font-family: 'Syncopate', sans-serif;
        font-size: clamp(40px, 8vw, 90px);
        font-weight: 700;
        letter-spacing: 15px;
        color: #fff;
        text-shadow: 0 0 20px rgba(255,255,255,0.8), 0 0 40px rgba(255,255,255,0.4);
        text-transform: uppercase;
    }}
    @keyframes pulse {{
        0%, 100% {{ transform: scale(1); opacity: 0.8; }}
        50% {{ transform: scale(1.05); opacity: 1; }}
    }}

    /* CARD MENU "ONE-TAP" */
    div.stButton > button {{
        width: 100% !important;
        height: 280px !important;
        background: rgba(255, 255, 255, 0.01) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 40px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        transition: 0.5s all cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}
    div.stButton > button:hover {{
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: #fff !important;
        box-shadow: 0 0 50px rgba(255, 255, 255, 0.1);
        transform: translateY(-15px);
    }}

    /* ĐIỀU KHOẢN HIỆN ĐẠI (TƯƠNG PHẢN CỰC ĐẠI) */
    .law-box {{
        background: rgba(255,255,255,0.02);
        backdrop-filter: blur(20px);
        border: 1px solid #222;
        padding: 60px;
        border-radius: 40px;
        height: 550px;
        overflow-y: auto;
    }}
    .law-box h1 {{ font-family: 'Syncopate'; font-size: 2rem; color: #fff; margin-bottom: 30px; }}
    .law-box p {{ font-size: 1.2rem; color: #aaa; line-height: 2; }}

    /* CHAT BUBBLES */
    div[data-testid="stChatMessage"] {{
        background: #080808 !important;
        border: 1px solid #111 !important;
        border-radius: 25px !important;
        padding: 25px !important;
        margin-bottom: 20px;
    }}
    .stMarkdown p {{ color: #ffffff !important; font-size: 1.15rem; line-height: 1.7; }}

    /* HINT PILLS (REAL-TIME STYLE) */
    .hint-container {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }}
    .hint-pill div.stButton > button {{
        height: auto !important; padding: 12px 25px !important;
        font-size: 0.9rem !important; border-radius: 100px !important;
        background: #fff !important; color: #000 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. AI CORE & REAL-TIME HINTS ---
def call_ai(prompt):
    if not ACTIVE_KEY: return "❌ Hệ thống chưa có Key."
    try:
        client = OpenAI(api_key=ACTIVE_KEY, base_url="https://api.groq.com/openai/v1")
        msgs = [{"role": "system", "content": f"Bạn là Nexus OS. Tác giả: {OWNER}. Trả lời tiếng Việt cực kỳ thông minh."}]
        for m in st.session_state.chat_log: msgs.append(m)
        msgs.append({"role": "user", "content": prompt})
        
        # Cập nhật gợi ý thực tế dựa trên nội dung (Real-time Logic)
        if "code" in prompt.lower(): st.session_state.hints = ["Tối ưu thuật toán", "Giải thích dòng code", "Sửa lỗi Bug"]
        elif "chuyện" in prompt.lower(): st.session_state.hints = ["Kể tiếp đoạn cuối", "Thêm kịch tính", "Đổi nhân vật"]
        else: st.session_state.hints = ["Phân tích sâu hơn", "Ví dụ cụ thể", "Tóm tắt ý chính"]

        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, stream=True)
    except Exception as e: return f"Error: {str(e)}"

# --- 4. CÁC MÀN HÌNH ---

def show_law():
    apply_ui()
    st.markdown("<div class='logo-container'><div class='logo-text'>NEXUS</div></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="law-box">
        <h1>HIẾP ƯỚC V1800</h1>
        <p>Chào mừng <b>{OWNER}</b>. Đây là giao diện Neural Symphony.</p>
        <p>• <b>Thị giác:</b> Trải nghiệm độ tương phản cực hạn giữa nền đen tuyền và chữ trắng tuyết.</p>
        <p>• <b>Tương tác:</b> Toàn bộ hệ thống Menu giờ đây là các thẻ Card cảm ứng. Nhấn là mở.</p>
        <p>• <b>Trí tuệ:</b> Gợi ý sẽ tự động biến đổi theo ngữ cảnh ngay khi bạn gửi tin nhắn.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("XÁC NHẬN ĐIỀU KHOẢN ✅", use_container_width=True):
        set_page("MENU"); st.rerun()

def show_menu():
    apply_ui()
    st.markdown("<div class='logo-container'><div class='logo-text'>CENTRAL</div></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.button("🧠\nCHAT CORE", on_click=set_page, args=("CHAT",))
    with c2: st.button("⚙️\nSETTINGS", on_click=set_page, args=("INFO",))

def show_chat():
    apply_ui()
    col_a, col_b = st.columns([9, 1])
    col_a.markdown("<h2 style='font-family:Syncopate;'>NEURAL INTERFACE</h2>", unsafe_allow_html=True)
    if col_b.button("🏠"): set_page("MENU"); st.rerun()

    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # HIỂN THỊ GỢI Ý THỜI GIAN THỰC
    st.write("---")
    cols = st.columns(len(st.session_state.hints))
    for i, h in enumerate(st.session_state.hints):
        if cols[i].button(h, key=f"h_{i}"):
            st.session_state.chat_log.append({"role": "user", "content": h})
            st.rerun()

    if p := st.chat_input("Giao tiếp với Nexus..."):
        st.session_state.chat_history = st.session_state.chat_log.append({"role": "user", "content": p})
        st.rerun()

    if st.session_state.chat_log and st.session_state.chat_log[-1]["role"] == "user":
        with st.chat_message("assistant"):
            box = st.empty(); full = ""
            res = call_ai(st.session_state.chat_log[-1]["content"])
            if isinstance(res, str): st.error(res)
            else:
                for chunk in res:
                    c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                    if c: full += c; box.markdown(full + "█")
                box.markdown(full)
                st.session_state.chat_log.append({"role": "assistant", "content": full})
                st.rerun()

# --- 5. ROUTER ---
if st.session_state.stage == "LAW": show_law()
elif st.session_state.stage == "MENU": show_menu()
elif st.session_state.stage == "CHAT": show_chat()
elif st.session_state.stage == "INFO":
    apply_ui()
    st.title("HỆ THỐNG")
    st.write(f"Sở hữu bởi: {OWNER}")
    if st.button("Quay lại"): set_page("MENU"); st.rerun()
