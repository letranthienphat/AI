import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import time

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="AI Voice Commander", layout="wide", page_icon="🔥")

# CSS: Tối ưu hóa khoảng cách, làm đẹp nút bấm và cố định khung chat
st.markdown("""
    <style>
    .stTextArea textarea { font-size: 16px; background-color: #f0f2f6; border-radius: 10px; }
    .stButton button { border-radius: 20px; font-weight: bold; }
    div[data-testid="stChatMessageContent"] { background-color: #ffffff; border-radius: 15px; padding: 10px; border: 1px solid #e0e0e0; }
    .draft-box { border: 2px solid #4CAF50; padding: 15px; border-radius: 15px; background-color: #e8f5e9; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# API SETUP
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

# --- QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
if "messages" not in st.session_state: st.session_state.messages = []
if "voice_draft" not in st.session_state: st.session_state.voice_draft = None # Lưu bản nháp giọng nói
if "last_read_index" not in st.session_state: st.session_state.last_read_index = -1 # Để không đọc lại tin cũ
if "processing" not in st.session_state: st.session_state.processing = False

# --- HÀM XỬ LÝ ---
def text_to_speech(text, speed=1.0):
    try:
        tts = gTTS(text=text, lang='vi')
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()
    except: return None

def process_ai_response():
    """Gửi tin nhắn đến AI và nhận phản hồi stream"""
    st.session_state.processing = True
    full_res = ""
    res_area = st.empty()
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                res_area.markdown(full_res + "▌")
        
        res_area.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
    except Exception as e:
        st.error(f"Lỗi AI: {e}")
    finally:
        st.session_state.processing = False
        st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Bảng Điều Khiển")
    speed = st.slider("Tốc độ đọc", 0.5, 2.0, 1.0, 0.1)
    auto_read = st.toggle("Tự động đọc tin mới", value=True)
    
    st.divider()
    if st.button("🗑️ Xóa Lịch Sử Chat"):
        st.session_state.messages = []
        st.session_state.voice_draft = None
        st.session_state.last_read_index = -1
        st.rerun()

# --- GIAO DIỆN CHÍNH ---
st.title("🔥 AI Voice Commander")

# 1. HIỂN THỊ LỊCH SỬ CHAT
chat_container = st.container()
with chat_container:
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            
            # Logic đọc giọng nói thông minh: Chỉ đọc tin nhắn MỚI NHẤT của AI
            if m["role"] == "assistant":
                # Nút đọc thủ công luôn hiện
                if st.button("🔊", key=f"read_{i}"):
                    audio = text_to_speech(m["content"], speed)
                    st.audio(audio, format="audio/mp3", autoplay=True)
                
                # Tự động đọc (Chỉ đọc 1 lần khi tin nhắn vừa xuất hiện)
                if auto_read and i > st.session_state.last_read_index:
                    st.session_state.last_read_index = i # Cập nhật đã đọc tin này rồi
                    audio = text_to_speech(m["content"], speed)
                    if audio:
                        st.audio(audio, format="audio/mp3", autoplay=True)

# 2. KHU VỰC TƯƠNG TÁC (ĐỘT PHÁ Ở ĐÂY)
st.divider()

# Nếu đang có bản nháp giọng nói -> Hiện giao diện CHỈNH SỬA ĐẶC BIỆT
if st.session_state.voice_draft is not None:
    st.markdown('<div class="draft-box">🎙️ <b>Chế độ chỉnh sửa giọng nói</b></div>', unsafe_allow_html=True)
    
    # Text Area điền sẵn nội dung từ Mic
    edited_text = st.text_area("Nội dung đã nghe được (Sửa lại nếu cần):", 
                               value=st.session_state.voice_draft, 
                               height=100,
                               key="draft_editor")
    
    col_confirm, col_cancel = st.columns([1, 1])
    with col_confirm:
        if st.button("🚀 GỬI NGAY (Enter)", type="primary", use_container_width=True):
            if edited_text.strip():
                st.session_state.messages.append({"role": "user", "content": edited_text})
                st.session_state.voice_draft = None # Xóa nháp
                process_ai_response()
    
    with col_cancel:
        if st.button("❌ Hủy bỏ", use_container_width=True):
            st.session_state.voice_draft = None
            st.rerun()

# Nếu KHÔNG có bản nháp -> Hiện giao diện NHẬP LIỆU CHUẨN (Mic + Chat Input)
else:
    c1, c2 = st.columns([1, 8])
    
    with c1:
        # Nút Mic
        audio_data = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_main')
    
    with c2:
        # Chat Input thường
        user_input = st.chat_input("Gõ tin nhắn hoặc nhấn Mic bên trái...")

    # LOGIC XỬ LÝ INPUT
    
    # Trường hợp A: Có Audio mới
    if audio_data:
        with st.spinner("⚡ Đang phân tích giọng nói..."):
            with open("voice_temp.wav", "wb") as f:
                f.write(audio_data['bytes'])
            with open("voice_temp.wav", "rb") as af:
                transcript = client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo", file=af, language="vi"
                )
            # LƯU VÀO DRAFT VÀ RELOAD ĐỂ HIỆN KHUNG SỬA
            st.session_state.voice_draft = transcript.text
            st.rerun()

    # Trường hợp B: Người dùng gõ phím Enter
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        process_ai_response()
