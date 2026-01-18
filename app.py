import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64
from langdetect import detect
import json

# --- 1. THEME & PROFESSIONAL CSS ---
st.set_page_config(page_title="AI Nexus Pro v22", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    /* Tổng thể font và màu sắc */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Glassmorphism cho bảng hướng dẫn */
    .guide-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        margin-bottom: 25px;
        border-left: 5px solid #007AFF;
    }

    /* Chat bubble chuyên nghiệp */
    div[data-testid="stChatMessage"] {
        background-color: #f8f9fa !important;
        border-radius: 18px !important;
        padding: 15px !important;
        border: none !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
    }

    /* Spotlight hiệu ứng mới */
    .active-zone {
        outline: 2px solid #007AFF;
        outline-offset: 5px;
        border-radius: 10px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { outline-color: rgba(0, 122, 255, 0.4); }
        50% { outline-color: rgba(0, 122, 255, 1); }
        100% { outline-color: rgba(0, 122, 255, 0.4); }
    }

    /* Input cố định sang trọng */
    .stChatInputContainer {
        padding-bottom: 20px !important;
        background: transparent !important;
    }
    
    .stButton > button {
        border-radius: 12px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.8rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM TRỢ NĂNG ---
def speak_js(text, speed, lang):
    clean = text.replace('"', "'").replace('\n', ' ')
    return f"<script>window.speechSynthesis.cancel(); var m=new SpeechSynthesisUtterance('{clean}'); m.lang='{lang}'; m.rate={speed}; window.speechSynthesis.speak(m);</script>"

# --- 3. KHỞI TẠO STATE ---
for key in ['messages', 'suggestions', 'guide_step', 'onboarding_done', 'v_speed']:
    if key not in st.session_state:
        defaults = {'messages': [], 'suggestions': [], 'guide_step': 0, 'onboarding_done': False, 'v_speed': 1.1}
        st.session_state[key] = defaults[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 4. HÀM XỬ LÝ AI ---
def process_ai(user_input):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("assistant"):
        p = st.empty(); full = ""
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages], stream=True)
        for chunk in res:
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                p.markdown(full + "▌")
        p.markdown(full)
        st.session_state.messages.append({"role": "assistant", "content": full})
        
        # Gợi ý thật sự dựa trên nội dung
        try:
            s_res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Tạo 3 câu hỏi ngắn từ: {full[:100]}"}])
            st.session_state.suggestions = [s.strip() for s in s_res.choices[0].message.content.split('\n') if s.strip()][:3]
        except: pass

        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.components.v1.html(speak_js(full, st.session_state.v_speed, "vi-VN"), height=0)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
    st.title("Nexus Control")
    
    if st.session_state.guide_step > 0:
        st.markdown(f"""
        <div class="guide-card">
            <small style="color: #007AFF; font-weight: bold;">MISSION CONTROL</small>
            <h4 style="margin: 5px 0;">Bước {st.session_state.guide_step}/4</h4>
            <p style="font-size: 0.9rem;">{["","Gửi tin nhắn mẫu","Thử nghe âm thanh","Chọn gợi ý thật","Sidebar & Lưu trữ"][st.session_state.guide_step]}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.session_state.v_speed = st.slider("Voice Speed", 0.5, 2.0, 1.1)
    
    if st.button("🔄 Reset Onboarding", use_container_width=True):
        st.session_state.guide_step = 1; st.rerun()
    
    st.divider()
    chat_json = json.dumps(st.session_state.messages, ensure_ascii=False)
    st.download_button("📤 Export Session", data=chat_json, file_name="session.json", use_container_width=True)

# --- 6. GIAO DIỆN CHÍNH ---
if st.session_state.guide_step == 0 and not st.session_state.onboarding_done:
    col_l, col_r = st.columns([2,1])
    with col_l:
        st.title("Welcome to Nexus Pro")
        st.write("Trải nghiệm trợ lý AI với giao diện tối giản và chuyên nghiệp.")
    with col_r:
        if st.button("Bắt đầu hướng dẫn ✨", use_container_width=True, type="primary"):
            st.session_state.guide_step = 1; st.rerun()
        if st.button("Bỏ qua", use_container_width=True):
            st.session_state.onboarding_done = True; st.rerun()

# KHU VỰC CHAT
chat_container = st.container()
with chat_container:
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant":
                c1, c2, c3 = st.columns([1,1,4])
                with c1:
                    if st.button("🔊", key=f"v_{i}"):
                        st.components.v1.html(speak_js(m["content"], st.session_state.v_speed, "vi-VN"), height=0)
                        if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
                with c2:
                    st.markdown("📱") # QR Placeholder chuyên nghiệp

# GỢI Ý (SUGGESTIONS)
if st.session_state.suggestions:
    st.write("")
    cols = st.columns(len(st.session_state.suggestions))
    for idx, sug in enumerate(st.session_state.suggestions):
        if cols[idx].button(f"🔹 {sug}", key=f"s_{idx}", use_container_width=True):
            if st.session_state.guide_step == 3: st.session_state.guide_step = 4
            process_ai(sug); st.rerun()

# INPUT CỐ ĐỊNH
st.write("<br><br><br>", unsafe_allow_html=True)
input_zone = "active-zone" if st.session_state.guide_step == 1 else ""
st.markdown(f'<div class="{input_zone}">', unsafe_allow_html=True)
inp = st.chat_input("Nhập lệnh hoặc yêu cầu tại đây...")
if inp: process_ai(inp); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.guide_step == 4:
    if st.button("HOÀN TẤT HÀNH TRÌNH 🎉", use_container_width=True, type="primary"):
        st.session_state.guide_step = 0; st.session_state.onboarding_done = True; st.rerun()
