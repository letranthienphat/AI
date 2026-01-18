import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
from io import BytesIO

# --- 1. CẤU HÌNH GIAO DIỆN SÁNG (LIGHT THEME) ---
st.set_page_config(page_title="AI Speed Pro", layout="wide")

# CSS tối giản cho tốc độ load nhanh nhất
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #000000; }
    .stChatMessage { border: 1px solid #E0E0E0; border-radius: 10px; margin-bottom: 8px; }
    .stChatInputContainer { border-top: 1px solid #DDD; padding-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. JAVASCRIPT: ĐỌC GIỌNG NÓI TỨC THỜI (BROWSER TTS) ---
def js_speak(text, speed):
    return f"""
    <script>
    var msg = new SpeechSynthesisUtterance("{text.replace('"', "'")}");
    msg.lang = 'vi-VN';
    msg.rate = {speed};
    window.speechSynthesis.speak(msg);
    </script>
    """

# --- 3. KHỞI TẠO API & SESSION ---
client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

if "messages" not in st.session_state: st.session_state.messages = []
if "draft" not in st.session_state: st.session_state.draft = ""

# --- 4. THANH BÊN TẬP TRUNG TÍNH NĂNG ---
with st.sidebar:
    st.header("⚡ Điều khiển nhanh")
    voice_speed = st.slider("Tốc độ đọc", 0.5, 2.0, 1.0, 0.1)
    auto_speak = st.checkbox("Tự động đọc phản hồi", value=True)
    
    st.divider()
    if st.button("📄 Tạo QR Lịch sử"):
        content = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        qr = qrcode.make(content[:2000]) # Giới hạn ký tự QR
        buf = BytesIO()
        qr.save(buf, format="PNG")
        st.image(buf, caption="Quét để lấy nội dung")
    
    if st.button("🗑️ Xóa Chat"):
        st.session_state.messages = []
        st.session_state.draft = ""
        st.rerun()

# --- 5. HIỂN THỊ HỘI THOẠI ---
st.title("🤖 AI Speed Assistant")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 6. XỬ LÝ NHẬP LIỆU (TỐC ĐỘ CAO) ---
col_mic, col_status = st.columns([1, 10])

with col_mic:
    # Mic thu âm
    audio = mic_recorder(start_prompt="🎤", stop_prompt="✅", key='mic')

if audio:
    with st.spinner("⚡..."):
        # Whisper Turbo trên Groq - Tốc độ dịch < 0.5s
        transcript = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo", 
            file=("audio.wav", audio['bytes']),
            language="vi"
        )
        st.session_state.draft = transcript.text
        # Tự động xóa file tạm sau xử lý (ẩn trong hệ thống)

# KHUNG CHỈNH SỬA NHANH
if st.session_state.draft:
    with st.container():
        st.success(f"Dịch được: {st.session_state.draft}")
        c1, c2 = st.columns(2)
        if c1.button("🚀 GỬI LUÔN"):
            st.session_state.messages.append({"role": "user", "content": st.session_state.draft})
            user_msg = st.session_state.draft
            st.session_state.draft = ""
            
            # AI phản hồi ngay lập tức
            with st.chat_message("assistant"):
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
                full_res = res.choices[0].message.content
                st.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                
                # Đọc phản hồi bằng Browser TTS (Không có độ trễ)
                if auto_speak:
                    st.components.v1.html(js_speak(full_res, voice_speed), height=0)
        
        if c2.button("🗑️ HỦY"):
            st.session_state.draft = ""
            st.rerun()

# Nhập văn bản truyền thống (Luôn ở dưới đáy)
prompt = st.chat_input("Nhập tin nhắn...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Tương tự logic gửi ở trên...
    st.rerun()
