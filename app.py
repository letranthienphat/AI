import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
from io import BytesIO

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="AI Zen Master", layout="wide", page_icon="🧘")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    .stChatMessage { border-radius: 15px; background: #f7f7f7; border: none; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    div[data-testid="stToolbar"] { visibility: hidden; }
    .stButton button { border-radius: 20px; font-weight: 600; transition: all 0.2s; }
    .stButton button:hover { transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM ĐỌC GIỌNG NÓI (JS BROWSER TTS) ---
def speak_js(text, speed):
    if not text: return ""
    clean_text = text.replace('"', "'").replace('\n', ' ')
    return f"""
    <script>
    window.speechSynthesis.cancel(); 
    var msg = new SpeechSynthesisUtterance("{clean_text}");
    msg.lang = 'vi-VN';
    msg.rate = {speed};
    window.speechSynthesis.speak(msg);
    </script>
    """

# --- 3. KHỞI TẠO STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "draft_text" not in st.session_state: st.session_state.draft_text = ""

# API Client
try:
    client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")
except:
    st.error("⚠️ Chưa cấu hình GROQ_API_KEY trong Secrets!")
    st.stop()

# --- 4. HÀM XỬ LÝ AI TRUNG TÂM ---
def process_response(user_input):
    if not user_input: return
    
    # Thêm tin nhắn user
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Gọi AI
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        try:
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    placeholder.markdown(full_res + "▌")
            placeholder.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            
            # Đọc phản hồi
            if st.session_state.auto_read:
                st.components.v1.html(speak_js(full_res, st.session_state.voice_speed), height=0)
                
        except Exception as e:
            st.error(f"Lỗi: {e}")

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Bảng Điều Khiển")
    st.session_state.voice_speed = st.slider("Tốc độ nói", 0.5, 2.0, 1.1)
    st.session_state.auto_read = st.toggle("Tự động đọc", value=True)
    
    st.divider()
    st.subheader("🚀 Chế độ Nhập liệu")
    # TÍNH NĂNG ĐỘT PHÁ: GỬI NGAY KHÔNG CẦN HỎI
    hands_free = st.toggle("⚡ Chế độ Rảnh tay (Gửi luôn)", value=False, help="Bật cái này lên thì nói xong gửi luôn, không hỏi lại nữa.")
    
    st.divider()
    if st.button("🗑️ Xóa Lịch Sử"):
        st.session_state.messages = []
        st.session_state.draft_text = ""
        st.rerun()

# --- 6. GIAO DIỆN CHÍNH ---
st.title("AI Zen Master 🧘")

# Hiển thị chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 7. INPUT AREA (LOGIC MỚI) ---
st.write("---")

# Logic Draft: Nếu có bản nháp thì hiện khung sửa, mic tạm ẩn để tránh xung đột
if st.session_state.draft_text and not hands_free:
    with st.container():
        st.info("📝 **Bản nháp giọng nói** (Sửa rồi nhấn Gửi)")
        edited_text = st.text_area("Nội dung:", value=st.session_state.draft_text, height=100, key="editor")
        
        c1, c2 = st.columns([1, 1])
        if c1.button("🚀 GỬI ĐI", type="primary", use_container_width=True):
            st.session_state.draft_text = "" # Xóa nháp TRƯỚC khi gửi
            process_response(edited_text)
            st.rerun()
            
        if c2.button("❌ HỦY BỎ", use_container_width=True):
            st.session_state.draft_text = "" # Xóa nháp
            st.rerun()

else:
    # Nếu không có nháp thì hiện Mic và Chat Input
    c_mic, c_input = st.columns([1, 10])
    
    with c_mic:
        # Mic Recorder
        audio_data = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_zen')
    
    # Xử lý ngay khi có Audio
    if audio_data:
        # Dùng Whisper Turbo
        with st.spinner("⚡"):
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo", 
                file=("voice.wav", audio_data['bytes']),
                language="vi"
            )
            text_result = transcript.text
            
            if hands_free:
                # Nếu bật Rảnh tay -> Gửi luôn
                process_response(text_result)
                st.rerun()
            else:
                # Nếu tắt Rảnh tay -> Lưu vào nháp để hiện khung sửa
                st.session_state.draft_text = text_result
                st.rerun()

    # Chat Input thường
    text_input = st.chat_input("Nhập tin nhắn...")
    if text_input:
        process_response(text_input)
        st.rerun()
