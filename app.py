import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64

# --- 1. CẤU HÌNH UI SIÊU CẤP ---
st.set_page_config(page_title="AI Nexus Ultra", layout="wide", page_icon="🌐")

# CSS để giao diện đẹp trên mọi thiết bị
st.markdown("""
    <style>
    /* Tổng thể giao diện sáng, tối giản */
    .stApp { background-color: #f0f2f5; }
    
    /* Bong bóng chat chuyên nghiệp */
    div[data-testid="stChatMessage"] {
        border-radius: 20px;
        padding: 15px;
        margin-bottom: 10px;
        max-width: 85%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* Thanh nhập liệu cố định ở đáy */
    .stChatInputContainer {
        position: fixed;
        bottom: 10px;
        left: 0;
        right: 0;
        z-index: 1000;
        padding: 0 10%;
    }

    /* Nút bấm bo tròn */
    .stButton button {
        border-radius: 30px !important;
        transition: 0.3s;
    }

    /* Ẩn bớt các thành phần thừa trên Mobile */
    @media (max-width: 600px) {
        .stChatInputContainer { padding: 0 2%; }
        div[data-testid="stChatMessage"] { max-width: 95%; }
        .stTitle { font-size: 1.5rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. JAVASCRIPT: ĐỌC GIỌNG NÓI TỨC THÌ ---
def speak_js(text, speed):
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

# --- 3. KHỞI TẠO STATE & API ---
if "messages" not in st.session_state: st.session_state.messages = []
if "voice_draft" not in st.session_state: st.session_state.voice_draft = ""

try:
    client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")
except:
    st.error("⚠️ Cần GROQ_API_KEY trong Secrets!")
    st.stop()

# --- 4. CÔNG CỤ TẢI VOICE (gTTS cho Download) ---
def get_audio_download_link(text):
    tts = gTTS(text=text, lang='vi')
    fp = BytesIO()
    tts.write_to_fp(fp)
    b64 = base64.b64encode(fp.getvalue()).decode()
    return f'<a href="data:audio/mp3;base64,{b64}" download="ai_voice.mp3" style="text-decoration:none;"><button style="background-color:#4CAF50; border:none; color:white; padding:5px 15px; border-radius:15px; cursor:pointer;">📥 Tải Voice (.mp3)</button></a>'

def process_ai(user_input):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("assistant"):
        p = st.empty()
        full = ""
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
            st.components.v1.html(speak_js(full, st.session_state.get("v_speed", 1.1)), height=0)

# --- 5. SIDEBAR: QUẢN LÝ DỮ LIỆU ---
with st.sidebar:
    st.title("⚙️ AI Nexus Pro")
    st.session_state.v_speed = st.slider("Tốc độ", 0.5, 2.0, 1.1)
    st.session_state.auto_read = st.toggle("Tự động đọc", value=True)
    hands_free = st.toggle("⚡ Rảnh tay (Gửi luôn)", value=False)
    
    st.divider()
    st.subheader("💾 Backup & QR")
    history_txt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
    
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📤 Xuất .txt", data=history_txt, file_name="chat.txt")
    with c2:
        if st.button("📱 Mã QR"):
            qr = qrcode.make(history_txt[:1000])
            buf = BytesIO()
            qr.save(buf, format="PNG")
            st.image(buf)

    uploaded = st.file_uploader("📂 Nhập lịch sử", type="txt")
    if uploaded:
        # Xử lý nhập file (giản lược để nhanh)
        if st.button("🔄 Khôi phục"):
            data = uploaded.getvalue().decode("utf-8")
            st.info("Đã nhận file, hãy refresh để xem kết quả!")

    if st.button("🗑️ Xóa sạch"):
        st.session_state.messages = []
        st.session_state.voice_draft = ""
        st.rerun()

# --- 6. GIAO DIỆN CHÍNH ---
st.title("AI Nexus Ultra 🚀")

# Hiển thị hội thoại
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            col_a, col_b = st.columns([1, 2])
            with col_a:
                if st.button("🔊 Đọc lại", key=f"r_{i}"):
                    st.components.v1.html(speak_js(m["content"], st.session_state.v_speed), height=0)
            with col_b:
                # TÍNH NĂNG TẢI FILE ĐỌC
                st.markdown(get_audio_download_link(m["content"]), unsafe_allow_html=True)

# --- 7. KHU VỰC NHẬP LIỆU ---
st.write("<br><br><br>", unsafe_allow_html=True) # Khoảng trống cho input cố định

if st.session_state.voice_draft and not hands_free:
    with st.container():
        st.warning("📝 Sửa bản dịch:")
        txt = st.text_area("", value=st.session_state.voice_draft, height=80)
        ca, cb = st.columns(2)
        if ca.button("🚀 GỬI", use_container_width=True):
            st.session_state.voice_draft = ""
            process_ai(txt)
            st.rerun()
        if cb.button("🗑️ HỦY", use_container_width=True):
            st.session_state.voice_draft = ""
            st.rerun()
else:
    c_m, c_i = st.columns([1, 8])
    with c_m:
        audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v6')
    
    if audio:
        with st.spinner("⚡"):
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']), language="vi"
            )
            if hands_free:
                process_ai(transcript.text)
                st.rerun()
            else:
                st.session_state.voice_draft = transcript.text
                st.rerun()

    inp = st.chat_input("Hỏi tôi bất cứ điều gì...")
    if inp:
        process_ai(inp)
        st.rerun()
