import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder, speech_to_text
import time

# --- 1. CẤU HÌNH GIAO DIỆN QUANTUM OS (DEEP SEA GRADIENT) ---
st.set_page_config(page_title="Nexus Quantum OS v60", layout="wide", page_icon="🖥️")

st.markdown("""
    <style>
    /* Nền OS Deep Sea Gradient */
    .stApp {
        background: linear-gradient(160deg, #E0EAFC 0%, #CFDEF3 100%) !important;
        background-attachment: fixed;
    }
    
    /* Chữ đen tuyền High-Contrast */
    p, span, h1, h2, h3, label, div, b { color: #000000 !important; font-weight: 700 !important; }

    /* Sidebar Start Menu Style */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-right: 4px solid #0078D4 !important; /* Màu xanh Windows OS */
        box-shadow: 5px 0 15px rgba(0,0,0,0.1);
    }

    /* Các Module Card */
    .os-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid #0078D4;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }

    /* Bảng hướng dẫn Step-by-Step */
    .step-overlay {
        background: #0078D4; color: white !important;
        padding: 20px; border-radius: 15px;
        text-align: center; border: 3px solid #FFFFFF;
        box-shadow: 0 10px 30px rgba(0,120,212,0.5);
        margin-bottom: 15px;
    }
    .step-overlay b, .step-overlay p { color: white !important; }

    /* Nút bấm kiểu OS Modern */
    .stButton > button {
        border-radius: 10px !important;
        border: 2px solid #0078D4 !important;
        background: white !important;
        color: #0078D4 !important;
        transition: 0.3s !important;
    }
    .stButton > button:hover {
        background: #0078D4 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE (CHỐNG LẶP LẠI) ---
for key in ['messages', 'guide_step', 'done', 'v_speed', 'live_mode', 'app_mode']:
    if key not in st.session_state:
        st.session_state[key] = {
            'messages': [], 'guide_step': 0, 'done': False, 
            'v_speed': 1.0, 'live_mode': False, 'app_mode': '🤖 A.I.'
        }[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. SIDEBAR: START MENU ---
with st.sidebar:
    st.title("🖥️ Nexus OS")
    st.markdown("---")
    # Mục chọn Module chính
    st.session_state.app_mode = st.radio("TRÌNH ĐIỀU KHIỂN", ["🤖 A.I.", "⚙️ CÀI ĐẶT"], label_visibility="collapsed")
    
    st.markdown("---")
    if st.button("🔴 TẮT HỆ THỐNG / RESET", use_container_width=True):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

# --- 4. HƯỚNG DẪN SMART STEP ---
if st.session_state.guide_step > 0 and not st.session_state.done:
    steps = ["", 
             "🎯 BƯỚC 1: Hãy gõ lời chào vào thanh nhập liệu bên dưới.", 
             "📄 BƯỚC 2: Nhấn nút 'LƯU .TXT' để thử nghiệm tính năng sao lưu.", 
             "⚙️ BƯỚC 3: Vào mục 'CÀI ĐẶT' ở bên trái để cấu hình hệ thống."]
    st.markdown(f'<div class="step-overlay"><b>HỆ THỐNG DẪN LỐI</b><br><p>{steps[st.session_state.guide_step]}</p></div>', unsafe_allow_html=True)

# --- 5. MODULE 1: ⚙️ CÀI ĐẶT ---
if st.session_state.app_mode == "⚙️ CÀI ĐẶT":
    st.title("⚙️ Cấu hình Hệ thống")
    with st.container(border=True):
        st.subheader("🔊 Giọng nói & Live Mode")
        st.session_state.live_mode = st.toggle("Kích hoạt Live Mode (Tự động đọc)", st.session_state.live_mode)
        st.session_state.v_speed = st.slider("Tốc độ giọng đọc AI", 0.5, 2.0, st.session_state.v_speed)
        
        st.divider()
        st.subheader("💾 Quản lý Dữ liệu .TXT")
        full_history = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        st.download_button("📤 XUẤT TOÀN BỘ NHẬT KÝ (.TXT)", data=full_history, file_name="nexus_os_backup.txt", use_container_width=True)
        
        st.divider()
        if st.button("🏁 HOÀN TẤT THIẾT LẬP & HƯỚNG DẪN"):
            st.session_state.done = True
            st.session_state.guide_step = 0
            st.success("Hệ thống đã sẵn sàng!")
            st.rerun()

# --- 6. MODULE 2: 🤖 A.I. ---
else:
    st.title("🤖 Trình mô phỏng A.I.")
    
    # Màn hình chào nếu chưa làm hướng dẫn
    if not st.session_state.done and st.session_state.guide_step == 0:
        st.markdown('<div class="os-card"><h3>Chào mừng đến với Nexus OS</h3><p>Hệ thống AI đa nhiệm thế hệ mới đã khởi chạy thành công.</p></div>', unsafe_allow_html=True)
        if st.button("🚀 BẮT ĐẦU HƯỚNG DẪN", type="primary"):
            st.session_state.guide_step = 1; st.rerun()

    # Khu vực chat
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(f"#### {m['content']}")
            if m["role"] == "assistant":
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🔊 ĐỌC", key=f"r_{i}"):
                        js = f"<script>window.speechSynthesis.cancel(); var u=new SpeechSynthesisUtterance('{m['content'].replace(chr(10), ' ')}'); u.lang='vi-VN'; u.rate={st.session_state.v_speed}; window.speechSynthesis.speak(u);</script>"
                        st.components.v1.html(js, height=0)
                with col2:
                    if st.download_button(f"📄 LƯU .TXT", data=m['content'], file_name=f"log_{i}.txt", key=f"s_{i}"):
                        if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()

    # Nhập liệu
    st.divider()
    col_mic, col_in = st.columns([1, 5])
    with col_mic:
        voice = speech_to_text(language='vi', start_prompt="🎤", stop_prompt="🛑", key="os_mic")
    with col_in:
        inp = st.chat_input("Nhập lệnh cho AI...")
        if voice: inp = voice # Ưu tiên giọng nói
        
    if inp:
        st.session_state.messages.append({"role": "user", "content": inp})
        with st.chat_message("assistant"):
            p = st.empty(); full = ""
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages], stream=True)
            for chunk in res:
                if chunk.choices[0].delta.content:
                    full += chunk.choices[0].delta.content
                    p.markdown(f"#### {full}")
            st.session_state.messages.append({"role": "assistant", "content": full})
            if st.session_state.guide_step == 1: st.session_state.guide_step = 2
            if st.session_state.live_mode:
                js = f"<script>window.speechSynthesis.cancel(); var u=new SpeechSynthesisUtterance('{full.replace(chr(10), ' ')}'); u.lang='vi-VN'; window.speechSynthesis.speak(u);</script>"
                st.components.v1.html(js, height=0)
            st.rerun()
