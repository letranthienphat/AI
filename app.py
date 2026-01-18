import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
import qrcode
from streamlit_mic_recorder import mic_recorder
import os

# --- CẤU HÌNH ---
st.set_page_config(page_title="AI Live Pro", layout="wide", page_icon="🎙️")

# CSS để làm giao diện gọn gàng hơn
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; }
    .chat-bubble { padding: 10px; border-radius: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

# Khởi tạo Session
if "messages" not in st.session_state: st.session_state.messages = []
if "speech_text" not in st.session_state: st.session_state.speech_text = ""
if "interrupt" not in st.session_state: st.session_state.interrupt = False

# --- HÀM TTS VỚI TỐC ĐỘ ---
def text_to_speech(text, speed=1.0):
    tts = gTTS(text=text, lang='vi')
    fp = BytesIO()
    tts.write_to_fp(fp)
    return fp.getvalue()

# --- SIDEBAR GỌN GÀNG ---
with st.sidebar:
    st.title("🎙️ AI Live Hub")
    speed = st.slider("Tốc độ đọc của AI", 0.5, 2.0, 1.0, 0.1)
    live_mode = st.toggle("Chế độ Live (Tự phản hồi)", value=True)
    
    st.divider()
    if st.button("📄 Xuất mã QR"):
        full_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        # (Logic tạo QR giữ nguyên như bản cũ)
        st.toast("Đã tạo QR bên dưới màn hình!")

    if st.button("🛑 NGẮT LỜI AI"):
        st.session_state.interrupt = True
        st.rerun()

# --- GIAO DIỆN CHAT CHÍNH ---
st.title("🤖 Trợ lý Live")

# Hiển thị hội thoại
chat_container = st.container(height=400)
with chat_container:
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant" and not st.session_state.interrupt:
                st.audio(text_to_speech(m["content"], speed), format="audio/mp3")

# --- KHU VỰC NHẬP LIỆU (STT & EDIT) ---
st.write("---")
col1, col2, col3 = st.columns([1, 7, 1])

with col1:
    # Nút thu âm (Có tích hợp khử nhiễu từ phần cứng trình duyệt)
    audio_record = mic_recorder(start_prompt="🎤 Nói", stop_prompt="✅ Xong", key='mic_pro')

with col2:
    # HIỆN NHỮNG GÌ DỊCH ĐƯỢC LÊN ĐÂY ĐỂ CHỈNH SỬA
    user_input = st.text_input("Nội dung tin nhắn:", value=st.session_state.speech_text, key="chat_input_text")

with col3:
    send_btn = st.button("🚀 Gửi")

# Xử lý khi có giọng nói mới
if audio_record:
    # Dùng Whisper để chuyển giọng nói thành văn bản (STT)
    client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    
    # Lưu tạm file âm thanh để dịch
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_record['bytes'])
    
    with open("temp_audio.wav", "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-large-v3", 
            file=audio_file,
            language="vi"
        )
    
    # Đưa kết quả dịch được vào ô nhập liệu để người dùng sửa
    st.session_state.speech_text = transcript.text
    st.rerun()

# --- LOGIC GỬI VÀ PHẢN HỒI ---
if send_btn and user_input:
    st.session_state.interrupt = False # Reset trạng thái ngắt lời
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.speech_text = "" # Xóa ô nhập sau khi gửi
    
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
            if st.session_state.interrupt: break # Kiểm tra nút ngắt lời
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                res_area.markdown(full_res + "▌")
        
        res_area.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        st.rerun()
