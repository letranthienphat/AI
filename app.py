# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI

# --- 1. CẤU HÌNH HỆ THỐNG TỐI THƯỢNG ---
st.set_page_config(
    page_title="NEXUS SUPREME", 
    layout="wide", 
    page_icon="🌌",
    initial_sidebar_state="collapsed"
)

# --- 2. QUẢN LÝ DỮ LIỆU & SECRETS ---
OWNER = "Lê Trần Thiên Phát"
# Lấy Key từ Streamlit Secrets
try:
    API_KEY = st.secrets["GROQ_KEY"]
except:
    API_KEY = ""

if 'stage' not in st.session_state: st.session_state.stage = "LAW"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'bg_link' not in st.session_state: 
    st.session_state.bg_link = "https://images.unsplash.com/photo-1614850523296-d8c1af93d400?q=80&w=2070"
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = ["Nexus làm được gì?", "Viết code Python", "Sáng tác thơ", "Lên lịch làm việc"]

def nav(s): st.session_state.stage = s

# --- 3. CSS SUPREME UI (Tương phản cao, Đa thiết bị) ---
def apply_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    * {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
    
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.9)), url("{st.session_state.bg_link}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* LOGO 5D HIỆU ỨNG GƯƠNG */
    .logo-box {{
        text-align: center; padding: 40px 0;
    }}
    .logo-main {{
        font-size: clamp(50px, 8vw, 100px);
        font-weight: 800;
        color: #fff;
        text-transform: uppercase;
        letter-spacing: -2px;
        background: linear-gradient(135deg, #00f2ff 0%, #0072ff 50%, #ffffff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 10px 20px rgba(0, 242, 255, 0.3));
    }}

    /* MENU CARDS CẢI TIẾN */
    div.stButton > button {{
        width: 100% !important;
        height: 220px !important;
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 30px !important;
        font-size: 1.4rem !important;
        font-weight: 600 !important;
        transition: 0.5s cubic-bezier(0.19, 1, 0.22, 1);
    }}
    div.stButton > button:hover {{
        background: rgba(0, 242, 255, 0.1) !important;
        border-color: #00f2ff !important;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5), 0 0 20px rgba(0,242,255,0.2);
        transform: translateY(-10px) scale(1.02);
    }}

    /* ĐIỀU KHOẢN HIỆN ĐẠI */
    .tos-card {{
        background: rgba(0, 0, 0, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 50px;
        border-radius: 40px;
        height: 500px;
        overflow-y: auto;
        color: #fff;
    }}
    .tos-card::-webkit-scrollbar {{ width: 5px; }}
    .tos-card::-webkit-scrollbar-thumb {{ background: #00f2ff; border-radius: 10px; }}
    
    /* GỢI Ý PILLS */
    .sug-pill {{
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 8px 15px;
        border-radius: 100px;
        display: inline-block;
        margin: 5px;
        font-size: 0.9rem;
    }}

    /* CHAT BUBBLES */
    div[data-testid="stChatMessage"] {{
        background: rgba(0, 0, 0, 0.6) !important;
        backdrop-filter: blur(10px);
        border-radius: 20px !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        margin-bottom: 20px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. HÀM XỬ LÝ AI ---
def call_nexus(p):
    if not API_KEY: return "⚠️ Lỗi: Không tìm thấy GROQ_KEY trong mục Secrets!"
    try:
        client = OpenAI(api_key=API_KEY, base_url="https://api.groq.com/openai/v1")
        msgs = [{"role": "system", "content": f"Bạn là Nexus OS. Tác giả: {OWNER}. Tập trung hỗ trợ người dùng."}]
        for m in st.session_state.chat_log: msgs.append(m)
        msgs.append({"role": "user", "content": p})
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, stream=True)
    except Exception as e: return f"❌ Lỗi: {str(e)}"

# --- 5. MÀN HÌNH ---

def screen_law():
    apply_ui()
    st.markdown("<div class='logo-box'><div class='logo-main'>NEXUS</div></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="tos-card">
        <h1 style='color:#00f2ff'>📜 CHÍNH SÁCH VẬN HÀNH V1400</h1>
        <p>Hệ thống tối thượng này được điêu khắc bởi <b>{OWNER}</b>.</p>
        <h2>• TRẢI NGHIỆM ĐA NỀN TẢNG</h2>
        <p>Nexus tự động thích nghi với màn hình Laptop và Mobile, đảm bảo tốc độ phản hồi dưới 1 giây.</p>
        <h2>• CÁ NHÂN HÓA HÌNH NỀN</h2>
        <p>Bạn có quyền thay đổi linh hồn của giao diện thông qua liên kết hình nền HTTPS tại mục cài đặt.</p>
        <h2>• BẢO MẬT & SECRETS</h2>
        <p>Mọi chìa khóa API đều được lưu trữ an toàn trong lớp bảo mật Secret của hệ thống.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("TÔI ĐỒNG Ý VÀ KHỞI CHẠY 🚀", use_container_width=True):
        nav("MENU"); st.rerun()

def screen_menu():
    apply_ui()
    st.markdown("<div class='logo-box'><div class='logo-main'>NEXUS HUB</div></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.button("💬\n\nAI CHAT CORE", on_click=nav, args=("CHAT",))
    with c2: st.button("🌌\n\nSETTINGS", on_click=nav, args=("INFO",))
    with c3: st.button("📜\n\nLEGAL", on_click=nav, args=("LAW",))

def screen_chat():
    apply_ui()
    col_a, col_b = st.columns([9, 1])
    col_a.title("🧬 Neural Interface")
    if col_b.button("🏠"): nav("MENU"); st.rerun()

    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Gợi ý thông minh
    st.write("---")
    cols = st.columns(len(st.session_state.suggestions))
    for i, s in enumerate(st.session_state.suggestions):
        if cols[i].button(s, key=f"s_{i}"):
            st.session_state.chat_log.append({"role": "user", "content": s})
            st.rerun()

    if p := st.chat_input("Hỏi Nexus..."):
        st.session_state.chat_log.append({"role": "user", "content": p})
        st.rerun()

    if st.session_state.chat_log and st.session_state.chat_log[-1]["role"] == "user":
        with st.chat_message("assistant"):
            holder = st.empty(); full = ""
            res = call_nexus(st.session_state.chat_log[-1]["content"])
            if isinstance(res, str): st.error(res)
            else:
                for chunk in res:
                    c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                    if c: full += c; holder.markdown(full + "▌")
                holder.markdown(full)
                st.session_state.chat_log.append({"role": "assistant", "content": full})

# --- 6. CÀI ĐẶT HÌNH NỀN ---
def screen_info():
    apply_ui()
    st.title("⚙️ Cài đặt Hệ thống")
    new_bg = st.text_input("Dán link hình nền HTTPS mới:", value=st.session_state.bg_link)
    if st.button("Cập nhật hình nền"):
        st.session_state.bg_link = new_bg
        st.success("Đã cập nhật giao diện!")
        st.rerun()
    st.write(f"Nhà phát triển: **{OWNER}**")
    st.button("🏠 Quay lại Menu", on_click=nav, args=("MENU",))

# --- ROUTER ---
if st.session_state.stage == "LAW": screen_law()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "INFO": screen_info()
