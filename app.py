import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import base64

# --- CẤU HÌNH ---
st.set_page_config(page_title="AI Nexus Gen", layout="wide", page_icon="⚡")

# API SETUP
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
# Sử dụng OpenAI API cho cả Chat, Audio và Image (Giả định bạn dùng OpenAI hoặc DALL-E)
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", GROQ_API_KEY)) 

# --- JAVASCRIPT ĐỘT PHÁ (Xử lý Cuộn trang và Tốc độ đọc Instant) ---
st.markdown("""
    <script>
    // 1. Tự động cuộn xuống dưới cùng khi có tin nhắn mới
    const observer = new MutationObserver(() => {
        const chatContainer = window.parent.document.querySelector('section.main');
        chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });
    });
    observer.observe(window.parent.document.body, { childList: true, subtree: true });

    // 2. Hàm thay đổi tốc độ audio ngay lập tức
    window.changeAudioSpeed = (speed) => {
        const audios = window.parent.document.querySelectorAll('audio');
        audios.forEach(audio => { audio.playbackRate = speed; });
    }
    </script>
    """, unsafe_allow_html=True)

# CSS làm đẹp giao diện
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #eee; }
    .stChatInputContainer { position: fixed; bottom: 20px; z-index: 1000; }
    .img-gen-card { border: 2px solid #7000ff; border-radius: 15px; padding: 10px; background: #f9f0ff; }
    </style>
    """, unsafe_allow_html=True)

# --- QUẢN LÝ TRẠNG THÁI ---
if "messages" not in st.session_state: st.session_state.messages = []
if "voice_draft" not in st.session_state: st.session_state.voice_draft = None
if "playback_speed" not in st.session_state: st.session_state.playback_speed = 1.0

# --- CÔNG CỤ XỬ LÝ ---
def text_to_speech(text):
    tts = gTTS(text=text, lang='vi')
    fp = BytesIO()
    tts.write_to_fp(fp)
    b64 = base64.b64encode(fp.getvalue()).decode()
    return f'<audio autoplay class="voice-audio" controls style="width:100%; height:30px;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

def generate_image(prompt):
    try:
        response = client.images.generate(
            model="dall-e-3", prompt=prompt, n=1, size="1024x1024"
        )
        return response.data[0].url
    except:
        return "https://via.placeholder.com/1024x1024.png?text=Loi+Tao+Anh"

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚡ Nexus Control")
    speed = st.slider("Tốc độ phát (Áp dụng tức thì)", 0.5, 2.0, st.session_state.playback_speed, 0.1)
    if speed != st.session_state.playback_speed:
        st.session_state.playback_speed = speed
        st.components.v1.html(f"<script>window.changeAudioSpeed({speed})</script>", height=0)
    
    st.divider()
    mode = st.radio("Chế độ phản hồi", ["Thông minh", "Chỉ tạo ảnh 🎨"])

# --- GIAO DIỆN CHAT ---
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image_url" in m:
            st.image(m["image_url"], caption="Hình ảnh được tạo bởi AI")
        if m["role"] == "assistant" and i == len(st.session_state.messages) - 1:
            st.markdown(text_to_speech(m["content"]), unsafe_allow_html=True)

# --- KHU VỰC NHẬP LIỆU ---
st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True) # Tạo khoảng trống cho chat input

col_mic, col_input = st.columns([1, 9])
with col_mic:
    audio_data = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic')

# Xử lý input giọng nói
if audio_data and not st.session_state.voice_draft:
    with st.spinner("Đang nghe..."):
        with open("temp.wav", "wb") as f: f.write(audio_data['bytes'])
        with open("temp.wav", "rb") as af:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=af)
            st.session_state.voice_draft = transcript.text
            st.rerun()

# Hiển thị bản nháp giọng nói để sửa
if st.session_state.voice_draft:
    with st.container():
        st.info(f"🎙️ Nháp: {st.session_state.voice_draft}")
        c1, c2 = st.columns(2)
        if c1.button("🚀 Gửi ngay"):
            user_msg = st.session_state.voice_draft
            st.session_state.voice_draft = None
            # Tự động nhận diện ý định tạo ảnh
            img_keywords = ["vẽ", "tạo hình", "ảnh", "bức tranh"]
            if any(k in user_msg.lower() for k in img_keywords) or mode == "Chỉ tạo ảnh 🎨":
                with st.spinner("🎨 Đang vẽ..."):
                    url = generate_image(user_msg)
                    st.session_state.messages.append({"role": "user", "content": user_msg})
                    st.session_state.messages.append({"role": "assistant", "content": "Đây là tác phẩm của bạn:", "image_url": url})
            else:
                st.session_state.messages.append({"role": "user", "content": user_msg})
                res = client.chat.completions.create(
                    model="gpt-4o", # Hoặc model bạn có
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
                st.session_state.messages.append({"role": "assistant", "content": res.choices[0].message.content})
            st.rerun()
        if c2.button("🗑️ Hủy"):
            st.session_state.voice_draft = None
            st.rerun()

# Chat input mặc định
user_input = st.chat_input("Nhập tin nhắn...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    # Logic tương tự cho chat input (AI hoặc Ảnh)
    st.rerun()
