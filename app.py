import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder, speech_to_text
import time

# --- 1. CẤU HÌNH GIAO DIỆN WORKSPACE OS ---
st.set_page_config(page_title="Nexus Workspace OS", layout="wide", page_icon="🖥️")

st.markdown("""
    <style>
    /* Nền Gradient chuyên nghiệp */
    .stApp {
        background: linear-gradient(135deg, #F5F7FA 0%, #B8C6DB 100%) !important;
    }
    p, span, h1, h2, h3, label, div, b { color: #1A1A1A !important; font-weight: 700 !important; }

    /* App Launcher Icon Style */
    .app-card {
        background: white;
        border-radius: 24px;
        padding: 30px;
        text-align: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        border: 2px solid transparent;
        transition: 0.3s;
        cursor: pointer;
    }
    .app-card:hover {
        border: 2px solid #0078D4;
        transform: translateY(-5px);
    }
    
    /* Thanh gợi ý (Suggestion Chips) */
    .sug-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 10px;
    }
    .sug-btn {
        background: rgba(0, 120, 212, 0.1);
        color: #0078D4 !important;
        border: 1px solid #0078D4;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 14px;
        cursor: pointer;
    }

    /* Hướng dẫn kiểu Overlay trung tâm */
    .guide-box {
        background: #0078D4;
        color: white !important;
        padding: 20px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 20px;
        border: 3px solid white;
    }
    .guide-box p, .guide-box b { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE ---
if 'app_state' not in st.session_state:
    st.session_state.app_state = 'launcher' # launcher, ai_app, settings_app
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'guide_step' not in st.session_state:
    st.session_state.guide_step = 0
if 'done' not in st.session_state:
    st.session_state.done = False

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HÀM ĐIỀU KHIỂN ---
def switch_app(app_name):
    st.session_state.app_state = app_name
    if st.session_state.guide_step == 1: st.session_state.guide_step = 2
    st.rerun()

def send_ai(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Logic gọi AI tương tự các bản trước...
    # (Để ngắn gọn, tôi tập trung vào giao diện App)
    st.session_state.guide_step = 3 if st.session_state.guide_step == 2 else st.session_state.guide_step
    st.rerun()

# --- 4. HỆ THỐNG HƯỚNG DẪN ---
if st.session_state.guide_step > 0 and not st.session_state.done:
    tasks = ["", 
             "📱 BƯỚC 1: Chọn App **'TRỢ LÝ AI'** để bắt đầu.", 
             "💡 BƯỚC 2: Thử nhấn vào một **'CÂU GỢI Ý'** hiện trên bàn phím.", 
             "🏁 BƯỚC 3: Tuyệt vời! Nhấn **'XÁC NHẬN HOÀN TẤT'** trong mục Cài đặt."]
    st.markdown(f'<div class="guide-box"><b>LỘ TRÌNH KHÁM PHÁ</b><br><p>{tasks[st.session_state.guide_step]}</p></div>', unsafe_allow_html=True)

# --- 5. GIAO DIỆN APP LAUNCHER ---
if st.session_state.app_state == 'launcher':
    st.title("🚀 Nexus Workspace")
    st.write("Chọn một ứng dụng để làm việc:")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🤖\nTRỢ LÝ AI", use_container_width=True, height=150):
            switch_app('ai_app')
    with col2:
        if st.button("⚙️\nCÀI ĐẶT", use_container_width=True, height=150):
            switch_app('settings_app')
    with col3:
        if st.button("📁\nQUẢN LÝ FILE", use_container_width=True, height=150):
            st.warning("Tính năng đang phát triển...")

    if st.session_state.guide_step == 0 and not st.session_state.done:
        if st.button("🏁 BẮT ĐẦU HƯỚNG DẪN OS", type="primary"):
            st.session_state.guide_step = 1; st.rerun()

# --- 6. GIAO DIỆN ỨNG DỤNG AI ---
elif st.session_state.app_state == 'ai_app':
    st.title("🤖 Trợ lý Nexus")
    if st.button("⬅️ Quay lại màn hình chính"): switch_app('launcher')
    
    # Hiển thị tin nhắn...
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.write(m["content"])

    # THANH GỢI Ý (SUGGESTIONS)
    st.markdown('<div class="sug-container">', unsafe_allow_html=True)
    suggestions = ["Hôm nay có gì mới?", "Giúp tôi viết mail", "Tóm tắt cuộc gọi"]
    cols = st.columns(len(suggestions))
    for i, sug in enumerate(suggestions):
        if cols[i].button(sug):
            # Xử lý gửi gợi ý...
            st.session_state.messages.append({"role": "user", "content": sug})
            if st.session_state.guide_step == 2: st.session_state.guide_step = 1 # Chuyển bước
            st.rerun()
    
    # Nhập liệu...
    inp = st.chat_input("Nhập lệnh...")
    if inp: st.session_state.messages.append({"role": "user", "content": inp}); st.rerun()

# --- 7. GIAO DIỆN CÀI ĐẶT ---
elif st.session_state.app_state == 'settings_app':
    st.title("⚙️ Cấu hình Hệ thống")
    if st.button("⬅️ Quay lại màn hình chính"): switch_app('launcher')
    
    st.toggle("Chế độ Live Voice")
    st.slider("Tốc độ AI đọc", 0.5, 2.0, 1.0)
    
    if st.button("🏁 XÁC NHẬN HOÀN TẤT HƯỚNG DẪN", type="primary"):
        st.session_state.done = True; st.session_state.guide_step = 0; switch_app('launcher')
