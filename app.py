# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import json

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="NEXUS V1700", layout="wide", page_icon="🔮")

OWNER = "Lê Trần Thiên Phát"

# Lấy Keys bảo mật từ Secrets
def get_api_key():
    keys = st.secrets.get("GROQ_KEYS", [])
    if isinstance(keys, list) and len(keys) > 0: return keys[0]
    return st.secrets.get("GROQ_KEY", None)

ACTIVE_KEY = get_api_key()

# Khởi tạo Session State
if 'stage' not in st.session_state: st.session_state.stage = "LAW"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'dynamic_hints' not in st.session_state: 
    st.session_state.dynamic_hints = ["Giải mã tương lai", "Lập trình hệ thống", "Phân tích dữ liệu"]
if 'ui_blur' not in st.session_state: st.session_state.ui_blur = 15

def nav(page): st.session_state.stage = page

# --- 2. GIAO DIỆN SUPREME NEURAL (GLASSMORPHISM) ---
def apply_supreme_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;700;800&display=swap');
    
    * {{ font-family: 'Plus Jakarta Sans', sans-serif; color: #FFFFFF; }}
    
    .stApp {{
        background: radial-gradient(circle at top right, #0a0a2e, #000000, #050505);
    }}

    /* LOGO GRAVITY 3D */
    .logo-box {{
        text-align: center; padding: 70px 0;
        perspective: 1000px;
    }}
    .logo-text {{
        font-size: clamp(60px, 10vw, 110px);
        font-weight: 800;
        letter-spacing: -4px;
        background: linear-gradient(180deg, #FFFFFF 0%, #00f2ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 20px 30px rgba(0, 242, 255, 0.3));
        transform: rotateX(10deg);
    }}

    /* CARD MENU KÍNH MỜ */
    div.stButton > button {{
        width: 100% !important;
        height: 250px !important;
        background: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur({st.session_state.ui_blur}px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 40px !important;
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        transition: 0.6s cubic-bezier(0.165, 0.84, 0.44, 1);
        text-shadow: 0 5px 15px rgba(0,0,0,0.5);
    }}
    div.stButton > button:hover {{
        background: rgba(0, 242, 255, 0.08) !important;
        border-color: #00f2ff !important;
        box-shadow: 0 30px 60px rgba(0, 242, 255, 0.1);
        transform: scale(1.05) translateY(-10px);
    }}

    /* KHUNG ĐIỀU KHOẢN CAO CẤP */
    .tos-card {{
        background: rgba(10, 10, 10, 0.8);
        backdrop-filter: blur(30px);
        border: 1px solid rgba(255,255,255,0.05);
        padding: 60px;
        border-radius: 50px;
        height: 600px;
        overflow-y: auto;
        box-shadow: 0 50px 100px rgba(0,0,0,0.5);
    }}
    .tos-card h1 {{ font-size: 3rem; background: linear-gradient(90deg, #00f2ff, #fff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .tos-card p {{ font-size: 1.2rem; color: #ccc; line-height: 2; }}

    /* GỢI Ý ĐỘNG PILLS */
    .hint-btn div.stButton > button {{
        height: auto !important;
        padding: 10px 25px !important;
        font-size: 0.9rem !important;
        border-radius: 100px !important;
        background: rgba(255,255,255,0.05) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI AI & LOGIC GỢI Ý ĐỘNG ---
def generate_dynamic_hints(last_response):
    # Trích xuất từ khóa để tạo gợi ý
    try:
        client = OpenAI(api_key=ACTIVE_KEY, base_url="https://api.groq.com/openai/v1")
        prompt = f"Dựa vào nội dung này: '{last_response[:200]}', hãy tạo 3 câu hỏi gợi ý ngắn gọn (dưới 5 từ) tiếp theo. Trả về dạng JSON list: ['hỏi 1', 'hỏi 2', 'hỏi 3']"
        res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
        st.session_state.dynamic_hints = json.loads(res.choices[0].message.content)
    except:
        st.session_state.dynamic_hints = ["Tìm hiểu thêm", "Giải thích sâu hơn", "Ứng dụng thực tế"]

def call_nexus(prompt):
    if not ACTIVE_KEY: return "❌ Lỗi: Hệ thống chưa được cấu hình Secret Key."
    try:
        client = OpenAI(api_key=ACTIVE_KEY, base_url="https://api.groq.com/openai/v1")
        msgs = [{"role": "system", "content": f"Bạn là Nexus OS. Tác giả: {OWNER}. Bạn phải trả lời bằng tiếng Việt chuyên nghiệp."}]
        for m in st.session_state.chat_history: msgs.append(m)
        msgs.append({"role": "user", "content": prompt})
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, stream=True)
    except Exception as e: return f"⚠️ Kết nối gián đoạn: {str(e)}"

# --- 4. MÀN HÌNH CHỨC NĂNG ---

def screen_law():
    apply_supreme_ui()
    st.markdown("<div class='logo-box'><div class='logo-text'>NEXUS OS</div></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="tos-card">
        <h1>HIẾP ƯỚC NEURAL</h1>
        <p>Phiên bản V1700 được tối ưu hóa riêng cho <b>{OWNER}</b>.</p>
        <h2>1. Trí tuệ thích nghi</h2>
        <p>Nexus không chỉ phản hồi, nó tự học ngữ cảnh cuộc hội thoại để đưa ra các gợi ý động ngay lập tức.</p>
        <h2>2. Bảo mật Phantom</h2>
        <p>Mọi API Keys được lưu trữ trong lớp Secret cách ly hoàn toàn với mã nguồn thực thi.</p>
        <h2>3. Trải nghiệm thị giác</h2>
        <p>Giao diện Glassmorphism yêu cầu phần cứng đồ họa ổn định để hiển thị các lớp kính mờ chồng lên nhau.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("XÁC NHẬN VÀ KHỞI ĐỘNG HỆ THỐNG", use_container_width=True):
        nav("MENU"); st.rerun()

def screen_menu():
    apply_supreme_ui()
    st.markdown("<div class='logo-box'><div class='logo-text'>CENTRAL UNIT</div></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.button("🧠\n\nNEURAL CHAT", on_click=nav, args=("CHAT",))
    with c2: st.button("⚖️\n\nPROTOCOL", on_click=nav, args=("LAW",))
    with c3: st.button("🛠️\n\nSETTINGS", on_click=nav, args=("INFO",))

def screen_chat():
    apply_supreme_ui()
    col_h, col_m = st.columns([9, 1])
    col_h.title("🧬 Neural Interface")
    if col_m.button("🏠"): nav("MENU"); st.rerun()

    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # HIỂN THỊ GỢI Ý ĐỘNG
    st.write("---")
    st.markdown('<div class="hint-btn">', unsafe_allow_html=True)
    cols = st.columns(len(st.session_state.dynamic_hints))
    for i, hint in enumerate(st.session_state.dynamic_hints):
        if cols[i].button(hint, key=f"hint_{i}"):
            st.session_state.chat_history.append({"role": "user", "content": hint})
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if p := st.chat_input("Gửi thông điệp tới lõi xử lý..."):
        st.session_state.chat_history.append({"role": "user", "content": p})
        st.rerun()

    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        with st.chat_message("assistant"):
            holder = st.empty(); full = ""
            res = call_nexus(st.session_state.chat_history[-1]["content"])
            if isinstance(res, str): st.error(res)
            else:
                for chunk in res:
                    c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                    if c: full += c; holder.markdown(full + "█")
                holder.markdown(full)
                st.session_state.chat_history.append({"role": "assistant", "content": full})
                generate_dynamic_hints(full) # TỰ ĐỘNG CẬP NHẬT GỢI Ý
                st.rerun()

# --- 5. ĐIỀU HƯỚNG ---
if st.session_state.stage == "LAW": screen_law()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "INFO":
    apply_supreme_ui()
    st.title("🛠️ Cài đặt Hệ thống")
    st.session_state.ui_blur = st.slider("Độ mờ của kính (Glass Blur)", 0, 50, 15)
    st.write(f"Nhà phát triển: **{OWNER}**")
    if st.button("Quay lại"): nav("MENU"); st.rerun()
