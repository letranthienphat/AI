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

# --- 1. CẤU HÌNH UI (GIAO DIỆN KHÔNG CHE CHẮN) ---
st.set_page_config(page_title="Nexus v21 Crystal", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    /* Làm sáng thành phần được hướng dẫn */
    .spotlight-active { border: 3px solid #00c853 !important; box-shadow: 0 0 15px rgba(0,200,83,0.3); border-radius: 15px; }
    .dimmed { opacity: 0.3; filter: blur(1px); pointer-events: none; transition: 0.3s; }
    
    /* Bảng hướng dẫn dạng Banner mỏng ở đỉnh trang, không che tin nhắn */
    .guide-banner {
        background-color: #f1f8e9;
        border-left: 10px solid #00c853;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 10px;
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
        return {"vi":"vi-VN", "en":"en-US"}.get(l, "vi-VN")
    except: return "vi-VN"

# --- 3. KHỞI TẠO STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "suggestions" not in st.session_state: st.session_state.suggestions = []
if "guide_step" not in st.session_state: st.session_state.guide_step = 0 
if "onboarding_done" not in st.session_state: st.session_state.onboarding_done = False
if "v_speed" not in st.session_state: st.session_state.v_speed = 1.1

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 4. HÀM XỬ LÝ AI & GỢI Ý THẬT ---
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
        
        # TẠO GỢI Ý THẬT TỪ NỘI DUNG
        try:
            s_res = client.chat.completions.create(
                model="llama-3.1-8b-instant", 
                messages=[{"role": "user", "content": f"Tạo 3 câu hỏi tiếp nối cực ngắn cho: '{full[:100]}'. Trả về các câu cách nhau bằng dấu phẩy."}]
            )
            st.session_state.suggestions = [s.strip() for s in s_res.choices[0].message.content.split(',') if s.strip()][:3]
        except:
            st.session_state.suggestions = ["Bạn khỏe không?", "Kể chuyện cười", "Dịch tiếng Anh"]

        # Chuyển bước hướng dẫn
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.components.v1.html(speak_js(full, st.session_state.v_speed, get_lang_code(full)), height=0)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Cài đặt")
    if st.button("📖 Chạy lại hướng dẫn", use_container_width=True):
        st.session_state.guide_step = 1
        st.session_state.onboarding_done = False
        st.rerun()
    st.divider()
    st.session_state.v_speed = st.slider("Tốc độ đọc", 0.5, 2.0, 1.1)
    
    st.subheader("💾 Dữ liệu")
    chat_json = json.dumps(st.session_state.messages, ensure_ascii=False)
    st.download_button("📤 Xuất file JSON", data=chat_json, file_name="chat.json", use_container_width=True)
    
    if st.button("🗑️ Xóa sạch hội thoại", use_container_width=True):
        st.session_state.messages = []; st.session_state.suggestions = []; st.rerun()

# --- 6. GIAO DIỆN CHÍNH & HƯỚNG DẪN DẠNG BANNER ---
st.title("AI Nexus Crystal 💎")

# Nếu đang hướng dẫn, hiện Banner ở đầu trang (không che tin nhắn)
if 1 <= st.session_state.guide_step <= 4:
    missions = {
        1: "🎯 **BƯỚC 1:** Gửi tin nhắn đầu tiên (gõ hoặc nói) để bắt đầu.",
        2: "🎯 **BƯỚC 2:** AI đã phản hồi thật! Thử nhấn nút **🔊 Nghe** dưới tin nhắn AI.",
        3: "🎯 **BƯỚC 3:** Các **Gợi ý thật** đã xuất hiện phía dưới. Hãy nhấn thử một cái!",
        4: "🎯 **BƯỚC 4:** Hoàn tất! Bạn có thể quản lý tốc độ và dữ liệu ở Sidebar."
    }
    st.markdown(f'<div class="guide-banner">{missions[st.session_state.guide_step]}</div>', unsafe_allow_html=True)
    
    c_skip1, c_skip2 = st.columns([2,1])
    if st.session_state.guide_step == 4:
        if c_skip1.button("✅ HOÀN TẤT & CHAT TỰ DO", use_container_width=True, type="primary"):
            st.session_state.guide_step = 0
            st.session_state.onboarding_done = True
            st.rerun()
    else:
        if c_skip1.button("⏩ Bỏ qua hướng dẫn", use_container_width=True):
            st.session_state.guide_step = 0
            st.session_state.onboarding_done = True
            st.rerun()

# --- HIỂN THỊ CHAT ---
# Image tag minh họa luồng chat không bị che chắn


for i, m in enumerate(st.session_state.messages):
    is_active = (st.session_state.guide_step == 2 and m["role"] == "assistant")
    style = "spotlight-active" if is_active else ("dimmed" if st.session_state.guide_step in [1,3,4] else "")
    
    st.markdown(f'<div class="{style}">', unsafe_allow_html=True)
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🔊 Nghe", key=f"v_{i}"):
                    st.components.v1.html(speak_js(m["content"], st.session_state.v_speed, get_lang_code(m["content"])), height=0)
                    if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
            with c2:
                tts = gTTS(text=m["content"][:100], lang="vi")
                b = BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
                st.markdown(f'<a href="data:audio/mp3;base64,{b64}" download="voice.mp3"><button style="width:100%; border-radius:10px; border:1px solid #ddd; padding:5px; cursor:pointer;">📥 Tải</button></a>', unsafe_allow_html=True)
            with c3:
                if st.button("📱 QR", key=f"q_{i}"):
                    qr = qrcode.make(m["content"][:300]); buf = BytesIO(); qr.save(buf, format="PNG"); st.image(buf, width=100)
    st.markdown('</div>', unsafe_allow_html=True)

# --- NÚT GỢI Ý THẬT ---
st.write("---")
sug_style = "spotlight-active" if st.session_state.guide_step == 3 else ("dimmed" if st.session_state.guide_step in [1,2,4] else "")
st.markdown(f'<div class="{sug_style}">', unsafe_allow_html=True)
if st.session_state.suggestions:
    st.caption("💡 Gợi ý dựa trên nội dung chat:")
    cols = st.columns(len(st.session_state.suggestions))
    for idx, sug in enumerate(st.session_state.suggestions):
        if cols[idx].button(sug, key=f"s_btn_{idx}_{hash(sug)}", use_container_width=True):
            if st.session_state.guide_step == 3: st.session_state.guide_step = 4
            process_ai(sug); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- INPUT AREA ---
st.write("<br><br><br><br>", unsafe_allow_html=True)
in_style = "spotlight-active" if st.session_state.guide_step == 1 else ("dimmed" if st.session_state.guide_step in [2,3,4] else "")
st.markdown(f'<div class="{in_style}" style="position:fixed; bottom:0; width:100%; background:white; padding:10px; left:0; z-index:1000;">', unsafe_allow_html=True)
cm, ci = st.columns([1, 6])
with cm: 
    audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v21')
    if audio:
        transcript = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']))
        process_ai(transcript.text); st.rerun()
inp = st.chat_input("Nhập tin nhắn...")
if inp: process_ai(inp); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
