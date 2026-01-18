import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder, speech_to_text
import time

# --- 1. SIÊU GIAO DIỆN NEXUS GLASS OS ---
st.set_page_config(page_title="Nexus OS v80", layout="wide", page_icon="🌐")

st.markdown("""
    <style>
    /* Nền OS Premium */
    .stApp {
        background: radial-gradient(circle at top right, #E0EAFC, #CFDEF3) !important;
        background-attachment: fixed;
    }
    
    /* Chữ siêu rõ nét */
    p, span, h1, h2, h3, label, div, b { color: #111111 !important; font-weight: 700 !important; }

    /* Thanh điều hướng Dock dưới cùng */
    .nav-dock {
        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(15px);
        padding: 10px 30px; border-radius: 30px;
        border: 1px solid rgba(255,255,255,0.5);
        display: flex; gap: 20px; z-index: 1000;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }

    /* Card App Pha lê */
    .crystal-card {
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(10px);
        border-radius: 25px; padding: 20px;
        border: 1px solid rgba(255,255,255,0.3);
        margin-bottom: 20px; text-align: center;
    }

    /* Gợi ý kiểu "Floating Chips" */
    .sug-chip {
        background: #0078D4 !important; color: white !important;
        border-radius: 15px !important; padding: 5px 15px !important;
        font-size: 13px !important; margin: 2px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE AN TOÀN ---
if 'init' not in st.session_state:
    st.session_state.update({
        'init': True, 'page': 'home', 'messages': [], 
        'guide_step': 0, 'done': False, 'v_speed': 1.0, 'live': False
    })

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. LOGIC XỬ LÝ AI ---
def ask_nexus(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        p = st.empty(); full = ""
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages], stream=True)
        for chunk in res:
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                p.markdown(f"### {full}")
        st.session_state.messages.append({"role": "assistant", "content": full})
        if st.session_state.guide_step == 2: st.session_state.guide_step = 3
        if st.session_state.live:
            js = f"<script>window.speechSynthesis.cancel(); var u=new SpeechSynthesisUtterance('{full.replace(chr(10), ' ')}'); u.lang='vi-VN'; u.rate={st.session_state.v_speed}; window.speechSynthesis.speak(u);</script>"
            st.components.v1.html(js, height=0)
        st.rerun()

# --- 4. HƯỚNG DẪN SMART OVERLAY ---
if st.session_state.guide_step > 0 and not st.session_state.done:
    tasks = ["", 
             "🏠 BƯỚC 1: Tại màn hình chính, nhấn vào App **'TRÍ TUỆ AI'**.", 
             "🎤 BƯỚC 2: Nhấn Micro hoặc chọn 1 **'GỢI Ý'** để trò chuyện.", 
             "⚙️ BƯỚC 3: Vào **'CÀI ĐẶT'** để hoàn tất và lưu .TXT."]
    st.info(f"**📍 NHIỆM VỤ:** {tasks[st.session_state.guide_step]}")

# --- 5. NAVIGATION DOCK (LUÔN HIỆN) ---
st.markdown('<div class="nav-dock">', unsafe_allow_html=True)
col_nav1, col_nav2, col_nav3 = st.columns(3)
with col_nav1:
    if st.button("🏠 Home"): st.session_state.page = 'home'; st.rerun()
with col_nav2:
    if st.button("🤖 AI"): st.session_state.page = 'ai'; st.rerun()
with col_nav3:
    if st.button("⚙️ Cài đặt"): st.session_state.page = 'settings'; st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- 6. PHÂN CHIA MODULE APPS ---

# --- PAGE: HOME (LAUNCHER) ---
if st.session_state.page == 'home':
    st.title("🌐 Nexus Home")
    st.write("Chào mừng bạn trở lại với Hệ điều hành Quantum.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="crystal-card">', unsafe_allow_html=True)
        if st.button("🤖\nTRÍ TUỆ AI", use_container_width=True):
            st.session_state.page = 'ai'
            if st.session_state.guide_step == 1: st.session_state.guide_step = 2
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="crystal-card">', unsafe_allow_html=True)
        if st.button("⚙️\nCÀI ĐẶT", use_container_width=True):
            st.session_state.page = 'settings'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.guide_step == 0 and not st.session_state.done:
        if st.button("🚀 BẮT ĐẦU HƯỚNG DẪN", type="primary"): 
            st.session_state.guide_step = 1; st.rerun()

# --- PAGE: AI ASSISTANT ---
elif st.session_state.page == 'ai':
    st.title("🤖 Nexus AI Engine")
    
    # Hiển thị chat
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(f"#### {m['content']}")
            if m["role"] == "assistant":
                if st.download_button("📄 Lưu .TXT", data=m['content'], file_name=f"chat_{i}.txt", key=f"dl_{i}"): pass

    # Gợi ý thông minh (Floating Suggestions)
    st.markdown("---")
    sugs = ["Kể một câu chuyện", "Viết một đoạn code", "Lập kế hoạch tập luyện"]
    cols = st.columns(len(sugs))
    for idx, s in enumerate(sugs):
        if cols[idx].button(f"✨ {s}", key=f"sug_{idx}"):
            ask_nexus(s)

    # Input (STT + Text)
    col_mic, col_in = st.columns([1, 6])
    with col_mic:
        voice = speech_to_text(language='vi', start_prompt="🎤", stop_prompt="🛑", key="mic_ai")
        if voice: ask_nexus(voice)
    with col_in:
        inp = st.chat_input("Hỏi tôi bất cứ điều gì...")
        if inp: ask_nexus(inp)

# --- PAGE: SETTINGS ---
elif st.session_state.page == 'settings':
    st.title("⚙️ Trung tâm Hệ thống")
    
    with st.expander("🔊 Cài đặt Live Voice", expanded=True):
        st.session_state.live = st.toggle("Live Mode (Tự động đọc)", st.session_state.live)
        st.session_state.v_speed = st.slider("Tốc độ", 0.5, 2.0, st.session_state.v_speed)

    with st.expander("💾 Sao lưu Nhật ký (.TXT)", expanded=True):
        full_log = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        st.download_button("📤 Tải về toàn bộ lịch sử", data=full_log, file_name="nexus_full_log.txt", use_container_width=True)

    if st.session_state.guide_step == 3:
        if st.button("🏁 HOÀN TẤT HƯỚNG DẪN", type="primary", use_container_width=True):
            st.session_state.done = True; st.session_state.guide_step = 0; st.session_state.page = 'home'; st.rerun()
