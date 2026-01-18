import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64
from langdetect import detect
import re

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="AI Nexus v15 Persistent", layout="wide", page_icon="💾")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    div[data-testid="stChatMessage"] { border-radius: 15px; margin-bottom: 12px; border: 1px solid #f0f0f0; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
    .stButton > button { border-radius: 20px !important; border: 1px solid #007bff !important; background-color: #f8fbff !important; color: #007bff !important; font-weight: 600 !important; }
    .stButton > button:hover { background-color: #007bff !important; color: white !important; }
    .guide-box { padding: 20px; border-radius: 15px; background: #f1f8e9; border-left: 5px solid #4caf50; margin-bottom: 20px; }
    .stChatInputContainer { position: fixed; bottom: 0; background: white; z-index: 1000; padding: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM TRỢ NĂNG ---
def speak_js(text, speed, lang):
    clean = text.replace('"', "'").replace('\n', ' ')
    return f"<script>window.speechSynthesis.cancel(); var m=new SpeechSynthesisUtterance('{clean}'); m.lang='{lang}'; m.rate={speed}; window.speechSynthesis.speak(m);</script>"

def get_lang_code(text):
    try:
        l = detect(text)
        mapping = {"vi":"vi-VN", "en":"en-US", "ja":"ja-JP", "ko":"ko-KR"}
        return mapping.get(l, "vi-VN")
    except: return "vi-VN"

# --- 3. KHỞI TẠO STATE (LƯU TRỮ TÙY CHỌN) ---
if "messages" not in st.session_state: st.session_state.messages = []
if "suggestions" not in st.session_state: st.session_state.suggestions = ["Chào bạn", "Hướng dẫn tôi", "Kể chuyện", "Dịch thuật"]
if "voice_draft" not in st.session_state: st.session_state.voice_draft = ""

# Quản lý trạng thái Onboarding
if "onboarding_status" not in st.session_state: st.session_state.onboarding_status = "pending" # pending, show, hide
if "remember_onboarding" not in st.session_state: st.session_state.remember_onboarding = False

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 4. HÀM XỬ LÝ AI ---
def process_ai(user_input):
    st.session_state.messages.append({"role": "user", "content": user_input})
    lang = get_lang_code(user_input)
    with st.chat_message("assistant"):
        p = st.empty(); full = ""
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True
        )
        for chunk in res:
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                p.markdown(full + "▌")
        p.markdown(full)
        st.session_state.messages.append({"role": "assistant", "content": full})
        if st.session_state.get("auto_read", True):
            st.components.v1.html(speak_js(full, st.session_state.get("v_speed", 1.1), lang), height=0)
        try:
            sug_res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Dựa trên: '{full[:100]}', tạo 4 câu hỏi tiếp nối cực ngắn, cách nhau bằng dấu phẩy."}])
            st.session_state.suggestions = [s.strip() for s in re.split(',|\n', sug_res.choices[0].message.content) if s.strip()][:4]
        except: pass

# --- 5. SIDEBAR: BẢNG ĐIỀU KHIỂN ---
with st.sidebar:
    st.title("🛡️ Nexus v15 Pro")
    
    # NÚT BẬT HƯỚNG DẪN CỐ ĐỊNH
    if st.button("📖 Xem Hướng Dẫn Sử Dụng", use_container_width=True):
        st.session_state.onboarding_status = "show"
        st.rerun()
        
    st.divider()
    st.session_state.v_speed = st.slider("Tốc độ giọng đọc", 0.5, 2.0, 1.1)
    if st.button("🛑 DỪNG ĐỌC", type="primary", use_container_width=True):
        st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)
    
    st.divider()
    st.session_state.auto_read = st.toggle("Tự động đọc", value=True)
    
    st.subheader("💾 Dữ liệu")
    if st.button("🗑️ Xóa sạch hội thoại", use_container_width=True):
        st.session_state.messages = []
        # Nếu không chọn ghi nhớ thì reset luôn trạng thái HD
        if not st.session_state.remember_onboarding:
            st.session_state.onboarding_status = "pending"
        st.rerun()

# --- 6. GIAO DIỆN CHÍNH & XỬ LÝ ONBOARDING ---
st.title("AI Nexus: Persistent Master 💾")

# HIỂN THỊ CÂU HỎI HƯỚNG DẪN (Chỉ khi chưa ghi nhớ hoặc đang pending)
if st.session_state.onboarding_status == "pending":
    with st.container():
        st.info("👋 Bạn đã biết cách sử dụng các tính năng của AI Nexus chưa?")
        remember = st.checkbox("Ghi nhớ lựa chọn của tôi (lưu tùy chọn)", value=st.session_state.remember_onboarding)
        c1, c2 = st.columns(2)
        if c1.button("❌ Chưa, hướng dẫn tôi!", use_container_width=True):
            st.session_state.remember_onboarding = remember
            st.session_state.onboarding_status = "show"
            st.rerun()
        if c2.button("✅ Rồi, vào chat luôn!", use_container_width=True):
            st.session_state.remember_onboarding = remember
            st.session_state.onboarding_status = "hide"
            st.rerun()

# HIỂN THỊ BẢNG HƯỚNG DẪN
if st.session_state.onboarding_status == "show":
    st.markdown("""
    <div class="guide-box">
        <h3>🚀 Hướng dẫn sử dụng:</h3>
        <ul>
            <li><b>🎤 Mic:</b> Nói để nhập liệu, AI tự nhận diện ngôn ngữ.</li>
            <li><b>🔊 Nghe & Tải:</b> Nghe lại hoặc tải Mp3 từng tin nhắn.</li>
            <li><b>📱 QR:</b> Tạo mã QR để chia sẻ nhanh văn bản.</li>
            <li><b>💡 Gợi ý:</b> Nhấn các nút dưới cùng để hỏi nhanh theo ngữ cảnh.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Đã hiểu, đóng hướng dẫn", use_container_width=True):
        st.session_state.onboarding_status = "hide"
        st.rerun()

# HIỂN THỊ CHAT
if st.session_state.onboarding_status != "pending":
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant":
                c1, c2, c3 = st.columns([1,1,1])
                with c1:
                    if st.button("🔊 Nghe lại", key=f"r_{i}"):
                        st.components.v1.html(speak_js(m["content"], st.session_state.v_speed, get_lang_code(m["content"])), height=0)
                with c2:
                    try:
                        tts = gTTS(text=m["content"][:200], lang=get_lang_code(m["content"]).split('-')[0])
                        b = BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
                        st.markdown(f'<a href="data:audio/mp3;base64,{b64}" download="voice.mp3"><button style="width:100%; border-radius:15px; border:1px solid #ddd; padding:5px;">📥 Tải Mp3</button></a>', unsafe_allow_html=True)
                    except: pass
                with c3:
                    if st.button("📱 QR", key=f"qr_{i}"):
                        qr = qrcode.make(m["content"][:500]); buf = BytesIO(); qr.save(buf, format="PNG"); st.image(buf, width=120)

    # NÚT GỢI Ý NGUYÊN TỬ
    st.write("---")
    if st.session_state.suggestions:
        cols = st.columns(len(st.session_state.suggestions))
        for idx, sug in enumerate(st.session_state.suggestions):
            clean = re.sub(r'^\d+\.\s*|-\s*', '', sug).strip()
            if cols[idx].button(clean, key=f"s_{idx}_{hash(clean)}", use_container_width=True):
                process_ai(clean); st.rerun()

    # --- 7. INPUT AREA ---
    st.write("<br><br><br><br>", unsafe_allow_html=True)
    c_m, c_i = st.columns([1, 6])
    with c_m: audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v15')
    if audio:
        transcript = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']))
        process_ai(transcript.text); st.rerun()
    inp = st.chat_input("Nhập tin nhắn...")
    if inp: process_ai(inp); st.rerun()
