import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64
from langdetect import detect
import json

# --- 1. CẤU HÌNH GIAO DIỆN CAO CẤP ---
st.set_page_config(page_title="Nexus Elite v23", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    /* Nhúng Font chữ chuyên nghiệp */
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Lexend', sans-serif; }

    /* Thiết kế Thẻ Hướng dẫn (Glassmorphism) */
    .mission-box {
        background: linear-gradient(135deg, #007AFF, #00C7FF);
        color: white;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0, 122, 255, 0.3);
        margin-bottom: 25px;
    }

    /* Bong bóng Chat hiện đại */
    div[data-testid="stChatMessage"] {
        border-radius: 20px !important;
        border: 1px solid #f0f2f6 !important;
        background-color: white !important;
        padding: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03) !important;
    }

    /* Nút bấm tùy chỉnh */
    .stButton > button {
        border-radius: 30px !important;
        padding: 10px 25px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    /* Hiệu ứng mờ nền khi hướng dẫn */
    .focus-dim { opacity: 0.1; filter: blur(5px); pointer-events: none; transition: 0.5s; }
    
    /* Input dính đáy sang trọng */
    .stChatInputContainer {
        border-top: 1px solid #eee !important;
        padding: 20px 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM XỬ LÝ ---
def speak_js(text, speed, lang):
    clean = text.replace('"', "'").replace('\n', ' ')
    return f"<script>window.speechSynthesis.cancel(); var m=new SpeechSynthesisUtterance('{clean}'); m.lang='{lang}'; m.rate={speed}; window.speechSynthesis.speak(m);</script>"

# --- 3. KHỞI TẠO DỮ LIỆU ---
for key in ['messages', 'suggestions', 'guide_step', 'onboarding_done', 'v_speed']:
    if key not in st.session_state:
        st.session_state[key] = {'messages': [], 'suggestions': [], 'guide_step': 0, 'onboarding_done': False, 'v_speed': 1.1}[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 4. TRUNG TÂM XỬ LÝ AI ---
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
        
        # Gợi ý thật sự bằng tiếng Việt
        try:
            s_res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Dựa trên nội dung: {full[:100]}, hãy gợi ý 3 câu hỏi ngắn tiếp theo bằng tiếng Việt, cách nhau bởi dấu phẩy."}])
            st.session_state.suggestions = [s.strip() for s in s_res.choices[0].message.content.split(',') if s.strip()][:3]
        except: pass

        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.components.v1.html(speak_js(full, st.session_state.v_speed, "vi-VN"), height=0)

# --- 5. BẢNG ĐIỀU KHIỂN (SIDEBAR) ---
with st.sidebar:
    st.markdown("## 🛡️ HỆ THỐNG NEXUS")
    
    if st.session_state.guide_step > 0:
        st.markdown(f"""
        <div class="mission-box">
            <small>TIẾN TRÌNH HƯỚNG DẪN</small>
            <h3 style="margin: 0;">Nhiệm vụ {st.session_state.guide_step}/4</h3>
            <div style="background: rgba(255,255,255,0.2); height: 8px; border-radius: 4px; margin: 10px 0;">
                <div style="background: white; width: {st.session_state.guide_step*25}%; height: 100%; border-radius: 4px;"></div>
            </div>
            <p style="font-size: 0.85rem;">{["","Gửi lời chào đầu tiên","Dùng thử giọng đọc AI","Chọn một gợi ý thông minh","Quản lý cài đặt & Dữ liệu"][st.session_state.guide_step]}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Bỏ qua hướng dẫn ⏩", use_container_width=True):
            st.session_state.guide_step = 0; st.session_state.onboarding_done = True; st.rerun()

    st.subheader("🔊 Giọng đọc")
    st.session_state.v_speed = st.slider("Tốc độ", 0.5, 2.0, 1.1)
    
    st.subheader("📂 Dữ liệu")
    if st.button("🗑️ Xóa hội thoại", use_container_width=True):
        st.session_state.messages = []; st.rerun()
    
    data_json = json.dumps(st.session_state.messages, ensure_ascii=False)
    st.download_button("📤 Lưu trữ phiên chat", data=data_json, file_name="nexus_chat.json", use_container_width=True)

# --- 6. GIAO DIỆN CHÍNH ---
if st.session_state.guide_step == 0 and not st.session_state.onboarding_done:
    st.markdown("""
        <div style="text-align: center; padding: 50px 0;">
            <h1 style="font-size: 3rem; color: #1d1d1f;">Chào mừng tới Nexus Elite</h1>
            <p style="color: #86868b; font-size: 1.2rem;">Trợ lý AI chuyên nghiệp với ngôn ngữ tiếng Việt hoàn toàn.</p>
        </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if st.button("BẮT ĐẦU TRẢI NGHIỆM ✨", use_container_width=True, type="primary"):
            st.session_state.guide_step = 1; st.rerun()

# KHU VỰC HIỂN THỊ CHAT
chat_style = "focus-dim" if st.session_state.guide_step in [1, 4] else ""
st.markdown(f'<div class="{chat_style}">', unsafe_allow_html=True)
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            col1, col2, _ = st.columns([1,1,5])
            if col1.button("🔊 Nghe", key=f"v_{i}"):
                st.components.v1.html(speak_js(m["content"], st.session_state.v_speed, "vi-VN"), height=0)
                if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
            if col2.button("📱 QR", key=f"q_{i}"):
                qr = qrcode.make(m["content"][:300]); buf = BytesIO(); qr.save(buf, format="PNG"); st.image(buf, width=120)
st.markdown('</div>', unsafe_allow_html=True)

# GỢI Ý THÔNG MINH (PILLS)
if st.session_state.suggestions:
    st.write("---")
    sug_style = "focus-dim" if st.session_state.guide_step in [1, 2] else ""
    st.markdown(f'<div class="{sug_style}">', unsafe_allow_html=True)
    st.caption("💡 Gợi ý cho bạn:")
    cols = st.columns(len(st.session_state.suggestions))
    for idx, sug in enumerate(st.session_state.suggestions):
        if cols[idx].button(f"✨ {sug}", key=f"s_{idx}", use_container_width=True):
            if st.session_state.guide_step == 3: st.session_state.guide_step = 4
            process_ai(sug); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# NHẬP LIỆU (COMMAND CENTER)
st.write("<br><br><br>", unsafe_allow_html=True)
in_style = "focus-dim" if st.session_state.guide_step in [2, 3] else ""
st.markdown(f'<div class="{in_style}" style="position:fixed; bottom:0; width:100%; background:white; padding:10px; left:0;">', unsafe_allow_html=True)
c_mic, c_input = st.columns([1, 6])
with c_mic:
    audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_elite')
    if audio:
        transcript = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']))
        process_ai(transcript.text); st.rerun()
inp = st.chat_input("Hỏi Nexus bất cứ điều gì...")
if inp: process_ai(inp); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# KẾT THÚC HƯỚNG DẪN
if st.session_state.guide_step == 4:
    st.markdown("""<div style="position: fixed; top: 20%; right: 20px; width: 300px; z-index: 9999;">""", unsafe_allow_html=True)
    if st.button("HOÀN TẤT & KHÁM PHÁ NGAY 🚀", type="primary", use_container_width=True):
        st.session_state.guide_step = 0; st.session_state.onboarding_done = True; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
