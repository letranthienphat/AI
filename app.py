import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder, speech_to_text
import time

# --- 1. SIÊU GIAO DIỆN AURORA DYNAMIC OS ---
st.set_page_config(page_title="Nexus Aurora v90", layout="wide", page_icon="✨")

st.markdown("""
    <style>
    /* Hình nền Động Aurora */
    @keyframes aurora {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .stApp {
        background: linear-gradient(-45deg, #EE7752, #E73C7E, #23A6D5, #23D5AB) !important;
        background-size: 400% 400% !important;
        animation: aurora 15s ease infinite !important;
    }

    /* Thẻ Glassmorphism siêu tương phản */
    .glass-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 25px;
        padding: 25px;
        border: 2px solid #FFFFFF;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    
    /* Chữ đen tuyền đặc biệt */
    h1, h2, h3, h4, p, b, span, label {
        color: #000000 !important;
        font-weight: 800 !important;
        text-shadow: 0px 0px 1px rgba(255,255,255,0.5);
    }

    /* Dock Taskbar */
    .dock {
        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
        background: rgba(255, 255, 255, 0.95);
        padding: 12px 40px; border-radius: 40px;
        display: flex; gap: 30px; z-index: 1000;
        border: 2px solid #23A6D5;
    }

    /* Nút gợi ý Gradient */
    .stButton > button {
        border-radius: 20px !important;
        background: white !important;
        color: #111111 !important;
        border: 2px solid #23A6D5 !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE ---
if 'page' not in st.session_state:
    st.session_state.update({
        'page': 'launcher', 'messages': [], 'guide_step': 0, 
        'done': False, 'v_speed': 1.0, 'live': False
    })

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HỆ THỐNG DOCK ĐIỀU HƯỚNG ---
st.markdown('<div class="dock">', unsafe_allow_html=True)
c_nav1, c_nav2, c_nav3 = st.columns(3)
with c_nav1:
    if st.button("🏠"): st.session_state.page = 'launcher'; st.rerun()
with c_nav2:
    if st.button("🤖"): st.session_state.page = 'ai'; st.rerun()
with c_nav3:
    if st.button("⚙️"): st.session_state.page = 'settings'; st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- 4. HƯỚNG DẪN GIẢ LẬP (SIMULATION) ---
if st.session_state.guide_step > 0 and not st.session_state.done:
    tasks = ["", 
             "📱 Nhấn vào App 'TRÍ TUỆ AI' trên màn hình.", 
             "🎤 Gõ/Nói điều gì đó với AI.", 
             "📄 Nhấn nút 'LƯU .TXT' (Hệ thống sẽ giả lập tải file)."]
    st.warning(f"🎯 **NHIỆM VỤ:** {tasks[st.session_state.guide_step]}")

# --- 5. APP LAUNCHER (HOME) ---
if st.session_state.page == 'launcher':
    st.title("✨ Nexus Aurora OS")
    st.markdown("### Hệ điều hành AI thế hệ mới")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔵\nTRÍ TUỆ AI", use_container_width=True):
            st.session_state.page = 'ai'
            if st.session_state.guide_step == 1: st.session_state.guide_step = 2
            st.rerun()
    with col2:
        if st.button("🟣\nCÀI ĐẶT", use_container_width=True):
            st.session_state.page = 'settings'; st.rerun()
            
    if st.session_state.guide_step == 0 and not st.session_state.done:
        if st.button("🚀 BẮT ĐẦU TRẢI NGHIỆM ĐỘT PHÁ", type="primary"):
            st.session_state.guide_step = 1; st.rerun()

# --- 6. AI ASSISTANT ---
elif st.session_state.page == 'ai':
    st.title("🤖 Trợ lý AI")
    
    # Khung Chat Glassmorphism
    with st.container():
        for i, m in enumerate(st.session_state.messages):
            with st.chat_message(m["role"]):
                st.markdown(f"#### {m['content']}")
                if m["role"] == "assistant":
                    if st.session_state.guide_step == 3:
                        if st.button("📄 LƯU .TXT (GIẢ LẬP)", key=f"sim_{i}"):
                            st.success("✅ Đã giả lập lưu file thành công! Bạn không cần tải thật.")
                            st.session_state.done = True; st.session_state.guide_step = 0; st.rerun()
                    else:
                        st.download_button("📝 Tải file .TXT", data=m['content'], file_name="chat.txt", key=f"real_{i}")

    # Gợi ý thông minh
    st.write("---")
    s_col1, s_col2 = st.columns(2)
    if s_col1.button("✨ Kể chuyện cười"): 
        st.session_state.messages.append({"role":"user","content":"Kể chuyện cười"}); st.rerun()
    if s_col2.button("✨ Lên lịch làm việc"):
        st.session_state.messages.append({"role":"user","content":"Lên lịch làm việc"}); st.rerun()

    # Nhập liệu
    inp = st.chat_input("Hỏi Nexus...")
    if inp:
        st.session_state.messages.append({"role": "user", "content": inp})
        if st.session_state.guide_step == 2: st.session_state.guide_step = 3
        # Logic gọi AI tại đây...
        st.rerun()

# --- 7. SETTINGS ---
elif st.session_state.page == 'settings':
    st.title("⚙️ Cài đặt")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.session_state.live = st.toggle("Chế độ Live Voice", st.session_state.live)
    st.session_state.v_speed = st.slider("Tốc độ đọc", 0.5, 2.0, st.session_state.v_speed)
    st.markdown('</div>', unsafe_allow_html=True)
