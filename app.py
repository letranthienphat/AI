import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
import qrcode
from streamlit_mic_recorder import mic_recorder

# --- 1. CẤU HÌNH GIAO DIỆN CHUẨN CHAT ---
st.set_page_config(page_title="AI Live Pro v3", layout="wide", page_icon="🎙️")

# CSS để cố định khung chat và làm đẹp giao diện
st.markdown("""
    <style>
    .stChatFloatingInputContainer { bottom: 20px; }
    .main { background-color: #ffffff; }
    div[data-testid="stVerticalBlock"] > div:has(div.stButton) {
        display: flex; align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

if "messages" not in st.session_state: st.session_state.messages = []
if "speech_text" not in st.session_state: st.session_state.speech_text = ""
if "interrupt" not in st.session_state: st.session_state.interrupt = False

def text_to_speech(text, speed=1.0):
    tts = gTTS(text=text, lang='vi')
    fp = BytesIO()
    tts.write_to_fp(fp)
    return fp.getvalue()

# --- 2. SIDEBAR QUẢN LÝ ---
with st.sidebar:
    st.title("🎙️ Cấu hình Live")
    speed = st.slider("Tốc độ AI đọc", 0.5, 2.0, 1.0, 0.1)
    st.divider()
    if st.button("🛑 NGẮT LỜI CHATBOT"):
        st.session_state.interrupt = True
        st.rerun()
    if st.button("🗑️ Xóa lịch sử"):
        st.session_state.messages = []
        st.rerun()

# --- 3. HIỂN THỊ CHAT (TỰ ĐỘNG CUỘN) ---
st.title("🤖 Trợ lý Thông minh")

# Container hiển thị nội dung chat để không bị đè bởi thanh nhập liệu
chat_placeholder = st.container()
with chat_placeholder:
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant":
                st.audio(text_to_speech(m["content"], speed), format="audio/mp3")

# --- 4. KHU VỰC NHẬP LIỆU THÔNG MINH ---
# Phần này xử lý việc "Dịch giọng nói xong hiện lên để sửa"
st.write("---")
col_mic, col_status = st.columns([1, 5])
with col_mic:
    audio_record = mic_recorder(start_prompt="🎤 Nói", stop_prompt="✅ Dịch", key='mic_v3')

if audio_record:
    with st.spinner("Đang khử nhiễu và dịch..."):
        client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        with open("temp.wav", "wb") as f:
            f.write(audio_record['bytes'])
        with open("temp.wav", "rb") as af:
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3", 
                file=af, 
                language="vi"
            )
        # Lưu vào session để hiện lên chat_input
        st.session_state.speech_text = transcript.text
        st.rerun()

# Ô NHẬP LIỆU CHÍNH: Nhấn Enter là gửi, tự động xóa chữ sau khi gửi
# Nếu có văn bản từ giọng nói, nó sẽ hiện sẵn ở đây để bạn sửa
prompt = st.chat_input("Nhập tin nhắn hoặc sửa nội dung đã nói...", key="main_input")

# Logic gửi tin (hỗ trợ cả Enter và click nút gửi của chat_input)
final_input = prompt if prompt else (None if not st.session_state.speech_text else None)

# Nếu người dùng sửa nội dung dịch hoặc gõ mới
if prompt:
    input_to_send = prompt
    st.session_state.speech_text = "" # Xóa bộ nhớ đệm giọng nói
    
    st.session_state.interrupt = False
    st.session_state.messages.append({"role": "user", "content": input_to_send})
    
    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        
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

# Hiển thị thông báo nếu có văn bản đang chờ gửi từ Mic
if st.session_state.speech_text:
    st.info(f"💡 Nội dung vừa dịch: **{st.session_state.speech_text}**\n\n(Hãy copy vào ô chat hoặc gõ đè để sửa trước khi nhấn Enter)")
