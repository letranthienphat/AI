import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64
from langdetect import detect
import re
import json

# --- 1. CẤU HÌNH UI SPOTLIGHT ---
st.set_page_config(page_title="Nexus v19 Active", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    .spotlight-active { border: 4px solid #00c853 !important; box-shadow: 0 0 25px rgba(0,200,83,0.4); background: #f1f8e9 !important; z-index: 999; }
    .dimmed { opacity: 0.15; filter: blur(3px); pointer-events: none; transition: 0.4s; }
    .floating-guide {
        position: fixed; top: 12%; left: 50%; transform: translateX(-50%);
        background: white; padding: 25px; border-radius: 20px;
        box-shadow: 0 15px 50px rgba(0,0,0,0.3); z-index: 1000;
        width: 85%; max-width: 450px; border-bottom: 6px solid #00c853;
        text-align: center;
    }
    .stApp { background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM HỖ TRỢ ---
def speak_js(text, speed, lang):
    clean = text.replace('"', "'").replace('\n', ' ')
    return f"<script>window.speechSynthesis.cancel(); var m=new SpeechSynthesisUtterance('{clean}'); m.lang='{lang}'; m.rate={speed}; window.speechSynthesis.speak(m);</script>"

def get_lang_code(text):
    try:
        l = detect(text)
        mapping = {"vi":"vi-VN", "en":"en-US"}
        return mapping.get(l, "vi-VN")
    except: return "vi-VN"

# --- 3. KHỞI TẠO STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "suggestions" not in st.session_state: st.session_state.suggestions = ["💡 Cho tôi lời khuyên", "🎭 Kể một truyện ngắn", "🧬 Giải thích Quantum"]
if "guide_step" not in st.session_state: st.session_state.guide_step = 0 
if "onboarding_done" not in st.session_state: st.session_state.onboarding_done = False

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 4. LOGIC AI ---
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
        # Nếu đang ở bước 1, tự động sang bước 2 sau khi có câu trả lời
        if st.session_state.guide_step == 1:
            st.session_state.guide_step = 2

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("💎 Nexus Terminal")
    if st.button("📖 Khởi động lại hướng dẫn", use_container_width=True):
        st.session_state.guide_step = 1
        st.session_state.messages = []
        st.rerun()
    st.session_state.v_speed = st.slider("Tốc độ đọc", 0.5, 2.0, 1.1)
    if st.button("🗑️ Xóa hội thoại", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# --- 6. GIAO DIỆN CHÍNH & HƯỚNG DẪN THỰC HÀNH ---
st.title("AI Nexus: Active Learning 🎓")

# Màn hình bắt đầu
if st.session_state.guide_step == 0 and not st.session_state.onboarding_done:
    st.info("Chào bạn! Để sử dụng thành thạo, hãy tham gia khóa hướng dẫn thực hành nhanh (30 giây).")
    if st.button("Bắt đầu thực hành ngay 🚀", use_container_width=True):
        st.session_state.guide_step = 1
        st.rerun()

# BẢNG HƯỚNG DẪN NHIỆM VỤ (Floating Mission Control)
if 1 <= st.session_state.guide_step <= 4:
    missions = {
        1: "🎯 **NHIỆM VỤ 1:** Hãy gõ nội dung vào ô Chat hoặc dùng Mic 🎤 bên dưới để gửi tin nhắn đầu tiên!",
        2: "🎯 **NHIỆM VỤ 2:** AI đã trả lời! Bây giờ hãy nhấn nút **🔊 Nghe** để kiểm tra giọng đọc.",
        3: "🎯 **NHIỆM VỤ 3:** Tuyệt vời! Thử nhấn vào một **nút gợi ý** màu xanh để xem AI phản hồi nhanh.",
        4: "🎯 **NHIỆM VỤ 4:** Cuối cùng, hãy nhấn vào **Sidebar (thanh trái)** để tùy chỉnh tốc độ đọc."
    }
    st.markdown(f'<div class="floating-guide"><h4>Nhiệm vụ {st.session_state.guide_step}/4</h4><p>{missions[st.session_state.guide_step]}</p></div>', unsafe_allow_html=True)
    
    # Nút bỏ qua hướng dẫn
    if st.button("Bỏ qua hướng dẫn ❌", size="small"):
        st.session_state.guide_step = 0
        st.session_state.onboarding_done = True
        st.rerun()

# --- HIỂN THỊ CHAT ---
for i, m in enumerate(st.session_state.messages):
    # Làm sáng tin nhắn AI ở bước 2
    step_style = "spotlight-active" if (st.session_state.guide_step == 2 and m["role"] == "assistant") else ("dimmed" if st.session_state.guide_step in [1,3,4] else "")
    st.markdown(f'<div class="{step_style}">', unsafe_allow_html=True)
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🔊 Nghe", key=f"v_{i}"):
                    st.components.v1.html(speak_js(m["content"], st.session_state.v_speed, get_lang_code(m["content"])), height=0)
                    if st.session_state.guide_step == 2: # Hoàn thành bước 2 khi nhấn Nghe
                        st.session_state.guide_step = 3
                        st.rerun()
            with c2:
                # Tải Mp3
                tts = gTTS(text=m["content"][:100], lang="vi")
                b = BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
                st.markdown(f'<a href="data:audio/mp3;base64,{b64}" download="voice.mp3"><button style="width:100%; border-radius:10px; border:1px solid #ddd; padding:5px; cursor:pointer;">📥 Tải</button></a>', unsafe_allow_html=True)
            with c3:
                if st.button("📱 QR", key=f"q_{i}"):
                    qr = qrcode.make(m["content"][:300]); buf = BytesIO(); qr.save(buf, format="PNG"); st.image(buf, width=100)
    st.markdown('</div>', unsafe_allow_html=True)

# --- NÚT GỢI Ý ---
st.write("---")
sug_style = "spotlight-active" if st.session_state.guide_step == 3 else ("dimmed" if st.session_state.guide_step != 0 and st.session_state.guide_step != 3 else "")
st.markdown(f'<div class="{sug_style}">', unsafe_allow_html=True)
if st.session_state.suggestions:
    cols = st.columns(len(st.session_state.suggestions))
    for idx, sug in enumerate(st.session_state.suggestions):
        if cols[idx].button(sug.strip(), key=f"s_{idx}_{hash(sug)}", use_container_width=True):
            if st.session_state.guide_step == 3: # Hoàn thành bước 3 khi nhấn Gợi ý
                st.session_state.guide_step = 4
            process_ai(sug); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- INPUT AREA ---
st.write("<br><br><br><br>", unsafe_allow_html=True)
in_style = "spotlight-active" if st.session_state.guide_step == 1 else ("dimmed" if st.session_state.guide_step != 0 and st.session_state.guide_step != 1 else "")
st.markdown(f'<div class="{in_style}" style="position:fixed; bottom:0; width:100%; background:white; padding:10px; left:0;">', unsafe_allow_html=True)
c_m, col_inp = st.columns([1, 6])
with c_m: 
    audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v19')
    if audio and st.session_state.guide_step == 1:
        # Tự động xử lý và nhảy bước nếu dùng mic ở bước 1
        transcript = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']))
        process_ai(transcript.text); st.rerun()
inp = st.chat_input("Nhập tin nhắn để thực hành...")
if inp: 
    process_ai(inp); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# Kết thúc tour ở bước 4 nếu người dùng tương tác Sidebar (phát hiện qua hành động slider)
if st.session_state.guide_step == 4:
    if st.button("Hoàn tất hướng dẫn! 🎉", use_container_width=True):
        st.session_state.guide_step = 0
        st.session_state.onboarding_done = True
        st.rerun()
