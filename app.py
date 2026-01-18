import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="AI Ultra Speed", layout="wide", page_icon="⚡")

# CSS tối giản, tập trung vào khung chat
st.markdown("""
    <style>
    .stChatFloatingInputContainer { bottom: 20px; }
    div[data-testid="stStatusWidget"] { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

if "messages" not in st.session_state: st.session_state.messages = []
if "interrupt" not in st.session_state: st.session_state.interrupt = False

def text_to_speech(text, speed=1.0):
    try:
        tts = gTTS(text=text, lang='vi')
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()
    except: return None

# --- 2. THANH BÊN ---
with st.sidebar:
    st.title("⚡ Speed Control")
    speed = st.slider("Tốc độ đọc", 0.5, 2.0, 1.0, 0.1)
    if st.button("🛑 NGẮT LỜI"):
        st.session_state.interrupt = True
        st.rerun()
    if st.button("🗑️ Xóa chat"):
        st.session_state.messages = []
        st.rerun()

# --- 3. KHUNG CHAT ---
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            audio = text_to_speech(m["content"], speed)
            if audio: st.audio(audio, format="audio/mp3")

# --- 4. NHẬP LIỆU SIÊU TỐC ---
# Đặt Mic và Chat Input gần nhau
col_mic, col_empty = st.columns([1, 10])
with col_mic:
    audio_record = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_turbo')

# Khởi tạo biến nội dung gửi
input_content = ""

# ƯU TIÊN 1: Xử lý giọng nói (Chỉ chạy khi nhấn dừng Mic)
if audio_record:
    with st.spinner("⚡ Đang dịch..."):
        with open("temp.wav", "wb") as f:
            f.write(audio_record['bytes'])
        with open("temp.wav", "rb") as af:
            # Dùng bản Turbo để tốc độ nhanh nhất
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo", 
                file=af, 
                language="vi"
            )
            input_content = transcript.text

# ƯU TIÊN 2: Xử lý gõ phím (Nhấn Enter gửi ngay)
prompt = st.chat_input("Nhập tin nhắn...")

# QUYẾT ĐỊNH GỬI: Nếu có từ phím HOẶC từ Mic
final_msg = prompt if prompt else input_content

if final_msg:
    st.session_state.interrupt = False
    st.session_state.messages.append({"role": "user", "content": final_msg})
    
    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True
        )
        
        for chunk in response:
            if st.session_state.interrupt: break
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                res_area.markdown(full_res + "▌")
        
        res_area.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        st.rerun()
