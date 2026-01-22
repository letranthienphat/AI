# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI

# --- 1. CẤU HÌNH HỆ THỐNG BẢO MẬT ---
st.set_page_config(page_title="NEXUS PHANTOM", layout="wide", page_icon="🥷")

# LẤY THÔNG TIN TỪ SECRETS (TUYỆT ĐỐI KHÔNG LỘ KEY)
try:
    # Hệ thống sẽ tự động thử lấy danh sách hoặc key đơn lẻ từ Secret của bạn
    raw_keys = st.secrets.get("GROQ_KEYS", [])
    if isinstance(raw_keys, list) and len(raw_keys) > 0:
        ACTIVE_KEY = raw_keys[0] # Lấy key đầu tiên trong danh sách
    else:
        ACTIVE_KEY = st.secrets.get("GROQ_KEY", None)
except Exception:
    ACTIVE_KEY = None

OWNER = "Lê Trần Thiên Phát"

# Quản lý trạng thái
if 'stage' not in st.session_state: st.session_state.stage = "LAW"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'hints' not in st.session_state: 
    st.session_state.hints = ["Nexus làm được gì?", "Viết code Python", "Kế hoạch tối nay"]

def nav_to(page):
    st.session_state.stage = page

# --- 2. GIAO DIỆN DARK MATTER (SIÊU TƯƠNG PHẢN) ---
def apply_phantom_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * {{ font-family: 'Inter', sans-serif; color: #FFFFFF; }}
    
    .stApp {{ background-color: #000000; }}

    /* LOGO TINH GIẢN */
    .header-box {{ text-align: center; padding: 50px 0; }}
    .logo-text {{
        font-size: 70px; font-weight: 900; letter-spacing: -2px;
        background: linear-gradient(180deg, #FFFFFF 0%, #444444 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}

    /* MENU CARDS BÓNG ĐÊM */
    div.stButton > button {{
        width: 100% !important; background: #050505 !important;
        border: 1px solid #222 !important; border-radius: 15px !important;
        padding: 45px 20px !important; font-size: 1.2rem !important;
        font-weight: 700 !important; transition: 0.3s;
    }}
    div.stButton > button:hover {{
        border-color: #FFFFFF !important; background: #111111 !important;
        box-shadow: 0 0 30px rgba(255, 255, 255, 0.1);
    }}

    /* ĐIỀU KHOẢN TRONG SUỐT */
    .tos-container {{
        background: #080808; border: 1px solid #1a1a1a;
        padding: 40px; border-radius: 20px; height: 500px; overflow-y: auto;
    }}
    .tos-container h1 {{ color: #FFFFFF; border-left: 4px solid #FFFFFF; padding-left: 15px; }}
    .tos-container p {{ color: #BBBBBB; line-height: 1.8; font-size: 1.1rem; }}

    /* CHAT ELEMENT */
    div[data-testid="stChatMessage"] {{
        background: #030303 !important; border: 1px solid #111 !important;
        border-radius: 12px !important; margin-bottom: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI AI (XỬ LÝ KÍN) ---
def run_ai(prompt):
    if not ACTIVE_KEY:
        return "⚠️ LỖI BẢO MẬT: Không tìm thấy API Key trong mục Secret của hệ thống."
    
    try:
        client = OpenAI(api_key=ACTIVE_KEY, base_url="https://api.groq.com/openai/v1")
        msgs = [{"role": "system", "content": f"Bạn là Nexus OS. Tác giả: {OWNER}. Trả lời tiếng Việt, chuyên nghiệp, súc tích."}]
        for m in st.session_state.chat_history: msgs.append(m)
        msgs.append({"role": "user", "content": prompt})
        
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, stream=True)
    except Exception as e:
        return f"❌ Lỗi kết nối: {str(e)}"

# --- 4. CÁC MÀN HÌNH ---

def screen_law():
    apply_phantom_theme()
    st.markdown("<div class='header-box'><div class='logo-text'>NEXUS OS</div></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="tos-container">
        <h1>📜 ĐIỀU KHOẢN BẢO MẬT V1600</h1>
        <p>Chào bạn <b>{OWNER}</b>. Phiên bản này ưu tiên tính ẩn danh và bảo mật tuyệt đối.</p>
        <h2>1. Phantom Secrets</h2>
        <p>Toàn bộ API Key đã được rút sạch khỏi mã nguồn. Hệ thống chỉ giao tiếp với Secret của Streamlit qua các biến ẩn.</p>
        <h2>2. Trải nghiệm tối giản</h2>
        <p>Chúng tôi lược bỏ các màu sắc rực rỡ không cần thiết, tập trung vào độ tương phản cực đại để tối ưu hóa việc đọc dữ liệu.</p>
        <h2>3. Xử lý đa nhiệm</h2>
        <p>Nexus có khả năng tự động đảo Key nếu một trong các Key trong danh sách Secret bị giới hạn tốc độ (Rate limit).</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("TÔI ĐỒNG Ý VÀ TRUY CẬP ⚡", use_container_width=True):
        nav_to("MENU"); st.rerun()

def screen_menu():
    apply_phantom_theme()
    st.markdown("<div class='header-box'><div class='logo-text'>SYSTEM HUB</div></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1: st.button("💬\n\nKÍCH HOẠT AI", on_click=nav_to, args=("CHAT",))
    with col2: st.button("⚙️\n\nCÀI ĐẶT", on_click=nav_to, args=("INFO",))

def screen_chat():
    apply_phantom_theme()
    c1, c2 = st.columns([9, 1])
    c1.title("🧬 Neural Core")
    if c2.button("🏠"): nav_to("MENU"); st.rerun()

    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Gợi ý dựa trên ngữ cảnh (Sơ khai)
    st.write("---")
    cols = st.columns(len(st.session_state.hints))
    for i, h in enumerate(st.session_state.hints):
        if cols[i].button(h, key=f"h_{i}"):
            st.session_state.chat_history.append({"role": "user", "content": h})
            st.rerun()

    if p := st.chat_input("Nhập lệnh..."):
        st.session_state.chat_history.append({"role": "user", "content": p})
        st.rerun()

    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        with st.chat_message("assistant"):
            holder = st.empty(); full = ""
            res = run_ai(st.session_state.chat_history[-1]["content"])
            if isinstance(res, str): st.error(res)
            else:
                for chunk in res:
                    c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                    if c: full += c; holder.markdown(full + "█")
                holder.markdown(full)
                st.session_state.chat_history.append({"role": "assistant", "content": full})

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "LAW": screen_law()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "INFO":
    apply_phantom_theme()
    st.title("⚙️ Thông tin hệ thống")
    st.write(f"Trạng thái API: {'✅ Hoạt động' if ACTIVE_KEY else '❌ Thiếu Key'}")
    st.button("Quay lại", on_click=nav_to, args=("MENU",))
