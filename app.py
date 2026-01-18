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

# --- 1. CẤU HÌNH GIAO DIỆN (UI) ---
st.set_page_config(page_title="Nexus v20 Final", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    .spotlight-active { border: 4px solid #00c853 !important; box-shadow: 0 0 25px rgba(0,200,83,0.4); background: #f1f8e9 !important; z-index: 999; }
    .dimmed { opacity: 0.2; filter: blur(3px); pointer-events: none; transition: 0.4s; }
    .floating-guide {
        position: fixed; top: 10%; left: 50%; transform: translateX(-50%);
        background: white; padding: 20px; border-radius: 20px;
        box-shadow: 0 15px 50px rgba(0,0,0,0.3); z-index: 1000;
        width: 90%; max-width: 500px; border-bottom: 6px solid #00c853;
    }
    .stApp { background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM TRỢ NĂNG ---
def speak_js(text, speed, lang):
    clean = text.replace('"', "'").replace('\n', ' ')
    return f"<script>window.speechSynthesis.cancel(); var m=new SpeechSynthesisUtterance('{clean}'); m.lang='{lang}'; m.rate={speed}; window.speechSynthesis.speak(m);</script>"

def get_lang_code(text):
    try:
        l = detect(text)
        return {"vi":"vi-VN", "en":"en-US"}.get(l, "vi-VN")
    except: return "vi-VN"

# --- 3. KHỞI TẠO TRẠNG THÁI (STATE) ---
if "messages" not in st.session_state: st.session_state.messages = []
if "suggestions" not in st.session_state: st.session_state.suggestions = ["💡 Gợi ý mẫu 1", "🎭 Gợi ý mẫu 2", "🧬 Gợi ý mẫu 3"]
if "guide_step" not in st.session_state: st.session_state.guide_step = 0 
if "onboarding_done" not in st.session_state: st.session_state.onboarding_done = False
if "v_speed" not in st.session_state: st.session_state.v_speed = 1.1

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
        # Logic nhảy bước hướng dẫn
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        # Tự động đọc
        st.components.v1.html(speak_js(full, st.session_state.v_speed, get_lang_code(full)), height=0)

# --- 5. SIDEBAR: ĐẦY ĐỦ TÍNH NĂNG ---
with st.sidebar:
    st.title("⚙️ Cài đặt & Dữ liệu")
    if st.button("📖 Xem lại hướng dẫn", use_container_width=True):
        st.session_state.guide_step = 1
        st.session_state.onboarding_done = False
        st.rerun()
    
    st.divider()
    st.session_state.v_speed = st.slider("Tốc độ giọng đọc", 0.5, 2.0, 1.1)
    
    st.divider()
    st.subheader("💾 Lưu trữ JSON")
    chat_json = json.dumps(st.session_state.messages, ensure_ascii=False)
    st.download_button("📤 Xuất file lưu trữ", data=chat_json, file_name="nexus_chat.json", mime="application/json", use_container_width=True)
    
    up = st.file_uploader("📥 Nhập file đã lưu", type="json")
    if up:
        if st.button("🔄 Khôi phục ngay"):
            st.session_state.messages = json.loads(up.getvalue().decode("utf-8"))
            st.rerun()

    if st.button("🗑️ Xóa sạch hội thoại", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# --- 6. GIAO DIỆN CHÍNH & HƯỚNG DẪN ---
st.title("AI Nexus v20 Final 💎")

# Màn hình bắt đầu (Hỏi Onboarding)
if st.session_state.guide_step == 0 and not st.session_state.onboarding_done:
    with st.container():
        st.info("👋 Chào mừng! Bạn muốn tham gia hướng dẫn thực hành hay bỏ qua?")
        c1, c2 = st.columns(2)
        if c1.button("🚀 Bắt đầu thực hành"):
            st.session_state.guide_step = 1
            st.rerun()
        if c2.button("⏩ Bỏ qua tất cả"):
            st.session_state.onboarding_done = True
            st.rerun()

# BẢNG HƯỚNG DẪN NỔI (Spotlight Guide)
if 1 <= st.session_state.guide_step <= 4:
    missions = {
        1: "🎯 **BƯỚC 1:** Thử gõ hoặc dùng Mic 🎤 gửi một tin nhắn bất kỳ!",
        2: "🎯 **BƯỚC 2:** AI đã trả lời. Hãy nhấn nút **🔊 Nghe** bên dưới tin nhắn.",
        3: "🎯 **BƯỚC 3:** Thử nhấn vào một **nút gợi ý** màu xanh để chat nhanh.",
        4: "🎯 **BƯỚC 4:** Tuyệt vời! Bạn có thể quản lý dữ liệu ở Sidebar bên trái."
    }
    with st.container():
        st.markdown(f'<div class="floating-guide"><h4>Nhiệm vụ {st.session_state.guide_step}/4</h4><p>{missions[st.session_state.guide_step]}</p></div>', unsafe_allow_html=True)
        if st.button("Bỏ qua hướng dẫn ❌", use_container_width=True):
            st.session_state.guide_step = 0
            st.session_state.onboarding_done = True
            st.rerun()

# --- HIỂN THỊ CHAT ---
for i, m in enumerate(st.session_state.messages):
    is_step_2 = (st.session_state.guide_step == 2 and m["role"] == "assistant")
    style = "spotlight-active" if is_step_2 else ("dimmed" if st.session_state.guide_step in [1,3,4] else "")
    st.markdown(f'<div class="{style}">', unsafe_allow_html=True)
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🔊 Nghe", key=f"v_btn_{i}"):
                    st.components.v1.html(speak_js(m["content"], st.session_state.v_speed, get_lang_code(m["content"])), height=0)
                    if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
            with c2:
                # Tải Mp3
                tts = gTTS(text=m["content"][:200], lang="vi")
                b = BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
                st.markdown(f'<a href="data:audio/mp3;base64,{b64}" download="voice.mp3"><button style="width:100%; border-radius:15px; border:1px solid #ddd; padding:5px; cursor:pointer;">📥 Tải</button></a>', unsafe_allow_html=True)
            with c3:
                if st.button("📱 QR", key=f"q_btn_{i}"):
                    qr = qrcode.make(m["content"][:300]); buf = BytesIO(); qr.save(buf, format="PNG"); st.image(buf, width=100)
    st.markdown('</div>', unsafe_allow_html=True)

# --- NÚT GỢI Ý ---
st.write("---")
sug_style = "spotlight-active" if st.session_state.guide_step == 3 else ("dimmed" if st.session_state.guide_step != 0 and st.session_state.guide_step != 3 else "")
st.markdown(f'<div class="{sug_style}">', unsafe_allow_html=True)
cols = st.columns(len(st.session_state.suggestions))
for idx, sug in enumerate(st.session_state.suggestions):
    if cols[idx].button(sug.strip(), key=f"sug_btn_{idx}_{hash(sug)}", use_container_width=True):
        if st.session_state.guide_step == 3: st.session_state.guide_step = 4
        process_ai(sug); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- INPUT AREA ---
st.write("<br><br><br><br>", unsafe_allow_html=True)
in_style = "spotlight-active" if st.session_state.guide_step == 1 else ("dimmed" if st.session_state.guide_step != 0 and st.session_state.guide_step != 1 else "")
st.markdown(f'<div class="{in_style}" style="position:fixed; bottom:0; width:100%; background:white; padding:10px; left:0; z-index:1001;">', unsafe_allow_html=True)
col_m, col_i = st.columns([1, 6])
with col_m: 
    audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_final')
    if audio:
        transcript = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']))
        process_ai(transcript.text); st.rerun()
inp = st.chat_input("Nhập tin nhắn để bắt đầu...")
if inp: process_ai(inp); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.guide_step == 4:
    if st.button("🎉 Hoàn tất hướng dẫn", use_container_width=True):
        st.session_state.guide_step = 0
        st.session_state.onboarding_done = True
        st.rerun()
