# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import json

# --- 1. HỆ THỐNG CỐT LÕI ---
st.set_page_config(page_title="NEXUS V1900", layout="wide", initial_sidebar_state="collapsed")

OWNER = "Lê Trần Thiên Phát"

# Quản lý Secret Keys an toàn
try:
    API_LIST = st.secrets.get("GROQ_KEYS", [])
    ACTIVE_KEY = API_LIST[0] if API_LIST else st.secrets.get("GROQ_KEY", "")
except:
    ACTIVE_KEY = ""

# Khởi tạo Session
if 'stage' not in st.session_state: st.session_state.stage = "LAW"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'bg_url' not in st.session_state: st.session_state.bg_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1964"
if 'deep_hints' not in st.session_state: 
    st.session_state.deep_hints = ["Phân tích kiến trúc hệ thống", "Viết code Python tối ưu", "Lập kế hoạch kinh doanh 2026"]

def nav(p): st.session_state.stage = p

# --- 2. CSS CYBER-GLASS UI (SIÊU ĐẸP & TƯƠNG PHẢN) ---
def apply_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Inter:wght@300;400;700&display=swap');
    
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("{st.session_state.bg_url}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}

    /* SIÊU LOGO QUANTUM */
    .logo-container {{ text-align: center; padding: 60px 0; }}
    .logo-text {{
        font-family: 'Orbitron', sans-serif;
        font-size: clamp(40px, 10vw, 100px);
        font-weight: 900;
        background: linear-gradient(90deg, #fff, #00f2ff, #fff);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 5s linear infinite;
    }}
    @keyframes shine {{ to {{ background-position: 200% center; }} }}

    /* NÚT BẤM HÀO QUANG (MENU) */
    div.stButton > button {{
        width: 100% !important;
        height: 220px !important;
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(0, 242, 255, 0.3) !important;
        border-radius: 30px !important;
        font-family: 'Orbitron', sans-serif !important;
        font-size: 1.5rem !important;
        transition: 0.4s all ease;
    }}
    div.stButton > button:hover {{
        border-color: #00f2ff !important;
        box-shadow: 0 0 40px rgba(0, 242, 255, 0.4);
        transform: translateY(-10px) scale(1.02);
    }}

    /* PHẢN HỒI AI (TƯƠNG PHẢN CAO) */
    div[data-testid="stChatMessageAssistant"] {{
        background: rgba(40, 44, 52, 0.95) !important;
        border-left: 5px solid #00f2ff !important;
        border-radius: 15px !important;
        padding: 30px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .stMarkdown p {{ color: #ffffff !important; font-size: 1.2rem; }}

    /* GỢI Ý ĐỘNG (PILLS) */
    .hint-box div.stButton > button {{
        height: auto !important; padding: 10px 20px !important;
        font-size: 0.9rem !important; border-radius: 50px !important;
        background: #00f2ff !important; color: #000 !important;
        font-weight: 700 !important;
    }}

    /* ĐIỀU KHOẢN */
    .tos-box {{
        background: rgba(0,0,0,0.9); padding: 50px; border-radius: 40px;
        border: 1px solid #333; height: 500px; overflow-y: auto;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI TRÍ TUỆ (DEEP REASONING) ---
def call_quantum_ai(prompt):
    if not ACTIVE_KEY: return "⚠️ API Key missing in Secrets!"
    try:
        client = OpenAI(api_key=ACTIVE_KEY, base_url="https://api.groq.com/openai/v1")
        msgs = [{"role": "system", "content": f"Bạn là Nexus OS v1900. Tác giả: {OWNER}. Trả lời chuyên sâu, chuyên gia."}]
        for m in st.session_state.chat_log: msgs.append(m)
        msgs.append({"role": "user", "content": prompt})

        # Logic gợi ý sâu: Phân tích intent người dùng
        if "code" in prompt.lower(): st.session_state.deep_hints = ["Tối ưu hóa bộ nhớ", "Thêm comment giải thích", "Viết Unit Test"]
        elif "marketing" in prompt.lower(): st.session_state.deep_hints = ["Lập chiến dịch Viral", "Phân tích đối thủ", "Tính ROI"]
        else: st.session_state.deep_hints = ["Mở rộng ý tưởng này", "Tìm điểm yếu của giải pháp", "Tóm tắt hành động"]

        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, stream=True)
    except Exception as e: return f"Error: {str(e)}"

# --- 4. MÀN HÌNH ---

def show_law():
    apply_ui()
    st.markdown("<div class='logo-container'><div class='logo-text'>NEXUS OS</div></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="tos-box">
        <h1 style='color:#00f2ff; font-family:Orbitron;'>HIẾP ƯỚC QUANTUM</h1>
        <p>Phiên bản V1900 tối ưu hóa cho <b>{OWNER}</b>.</p>
        <p>• <b>Visuals:</b> Giao diện nút bấm Hào quang (Glow) và hình nền động.</p>
        <p>• <b>Intelligence:</b> Gợi ý hành động sâu dựa trên ngữ cảnh thời gian thực.</p>
        <p>• <b>Security:</b> Bảo vệ API Key tuyệt đối trong lớp Secrets.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("XÁC NHẬN VÀ TRUY CẬP 🚀", use_container_width=True):
        nav("MENU"); st.rerun()

def show_menu():
    apply_ui()
    st.markdown("<div class='logo-container'><div class='logo-text'>QUANTUM HUB</div></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.button("🧠\nCHAT CORE", on_click=nav, args=("CHAT",))
    with c2: st.button("🖼️\nSCENERY", on_click=nav, args=("INFO",))
    with c3: st.button("📜\nLEGAL", on_click=nav, args=("LAW",))

def show_chat():
    apply_ui()
    col_a, col_b = st.columns([9, 1])
    col_a.markdown("<h2 style='font-family:Orbitron; color:#00f2ff;'>NEURAL INTERFACE</h2>", unsafe_allow_html=True)
    if col_b.button("🏠"): nav("MENU"); st.rerun()

    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # GỢI Ý SÂU (PILLS)
    st.write("---")
    st.markdown('<div class="hint-box">', unsafe_allow_html=True)
    cols = st.columns(len(st.session_state.deep_hints))
    for i, h in enumerate(st.session_state.deep_hints):
        if cols[i].button(h, key=f"h_{i}"):
            st.session_state.chat_log.append({"role": "user", "content": h})
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if p := st.chat_input("Giao tiếp với Nexus Quantum..."):
        st.session_state.chat_log.append({"role": "user", "content": p})
        st.rerun()

    if st.session_state.chat_log and st.session_state.chat_log[-1]["role"] == "user":
        with st.chat_message("assistant"):
            box = st.empty(); full = ""
            res = call_quantum_ai(st.session_state.chat_log[-1]["content"])
            if isinstance(res, str): st.error(res)
            else:
                for chunk in res:
                    c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                    if c: full += c; box.markdown(full + "█")
                box.markdown(full)
                st.session_state.chat_log.append({"role": "assistant", "content": full})
                st.rerun()

def show_info():
    apply_ui()
    st.markdown("<h2 style='font-family:Orbitron;'>CÀI ĐẶT GIAO DIỆN</h2>", unsafe_allow_html=True)
    url = st.text_input("Dán link hình nền HTTPS (Unsplash/Pinterest):", value=st.session_state.bg_url)
    if st.button("CẬP NHẬT HÌNH NỀN"):
        st.session_state.bg_url = url
        st.rerun()
    
    st.markdown("---")
    st.write(f"Developer: **{OWNER}**")
    st.button("QUAY LẠI MENU", on_click=nav, args=("MENU",))

# --- 5. ĐIỀU HƯỚNG ---
if st.session_state.stage == "LAW": show_law()
elif st.session_state.stage == "MENU": show_menu()
elif st.session_state.stage == "CHAT": show_chat()
elif st.session_state.stage == "INFO": show_info()
