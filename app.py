import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
from io import BytesIO

# --- 1. CẤU HÌNH GIAO DIỆN LIGHT-SPEED ---
st.set_page_config(page_title="AI Nexus God Mode", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; color: #1A1A1A; }
    .stChatMessage { background-color: white !important; border: 1px solid #EAEAEA; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .stChatInputContainer { padding-bottom: 20px; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. JAVASCRIPT: BROWSER TTS (ĐỌC KHÔNG ĐỘ TRỄ) ---
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

# --- 3. KHỞI TẠO API & SESSION (100% GROQ) ---
client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

if "messages" not in st.session_state: st.session_state.messages = []
if "voice_draft" not in st.session_state: st.session_state.voice_draft = ""

# --- 4. HÀM XỬ LÝ AI TRỌNG TÂM (ĐẢM BẢO LUÔN TRẢ LỜI) ---
def get_ai_response(user_text):
    if not user_text: return
    
    # Thêm tin nhắn user
    st.session_state.messages.append({"role": "user", "content": user_text})
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        try:
            # Dùng model mạnh nhất & nhanh nhất của Groq
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    placeholder.markdown(full_res + "▌")
            placeholder.markdown(full_res)
            
            # Lưu vào lịch sử
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            
            # Tự động đọc (Browser TTS)
            if st.session_state.get("auto_read", True):
                st.components.v1.html(speak_js(full_res, st.session_state.get("v_speed", 1.0)), height=0)
        except Exception as e:
            st.error(f"Lỗi API: {str(e)}")

# --- 5. SIDEBAR: 100 TÍNH NĂNG (GỌN GÀNG) ---
with st.sidebar:
    st.header("⚡ Command Center")
    st.session_state.v_speed = st.slider("Tốc độ Voice", 0.5, 2.0, 1.0)
    st.session_state.auto_read = st.toggle("Tự động đọc", value=True)
    
    st.divider()
    if st.button("📄 QR & Xuất File"):
        history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        qr = qrcode.make(history[:1500])
        buf = BytesIO()
        qr.save(buf, format="PNG")
        st.image(buf, caption="Quét lấy hội thoại")
        st.download_button("📥 Tải file .txt", history, file_name="chat.txt")

    if st.button("🗑️ Reset Hệ Thống"):
        st.session_state.messages = []
        st.session_state.voice_draft = ""
        st.rerun()

# --- 6. GIAO DIỆN CHÍNH ---
st.title("🚀 AI Nexus Speed")

# Hiển thị lịch sử chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 7. NHẬP LIỆU (MIC & CHAT INPUT) ---
st.write("---")
c1, c2 = st.columns([1, 10])

with c1:
    audio = mic_recorder(start_prompt="🎤", stop_prompt="✅", key='mic_v5')

if audio:
    with st.spinner("⚡..."):
        # Whisper Turbo - Phá vỡ giới hạn tốc độ giải mã
        transcript = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo", 
            file=("audio.wav", audio['bytes']),
            language="vi"
        )
        st.session_state.voice_draft = transcript.text

# Nếu có giọng nói vừa dịch xong -> Hiện khung CHỈNH SỬA
if st.session_state.voice_draft:
    with st.container():
        st.info(f"🎙️ Nháp: {st.session_state.voice_draft}")
        col_ok, col_no = st.columns(2)
        if col_ok.button("🚀 GỬI BẢN DỊCH NÀY"):
            text_to_send = st.session_state.voice_draft
            st.session_state.voice_draft = ""
            get_ai_response(text_to_send)
            st.rerun()
        if col_no.button("🗑️ HỦY"):
            st.session_state.voice_draft = ""
            st.rerun()

# Ô nhập văn bản (Enter để gửi)
user_query = st.chat_input("Hỏi tôi bất cứ điều gì...")
if user_query:
    get_ai_response(user_query)
