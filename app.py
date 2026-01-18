import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64
from langdetect import detect

# --- 1. CẤU HÌNH UI MOBILE-FIRST ---
st.set_page_config(page_title="Nexus Mobile Pro", layout="wide", page_icon="📱")

st.markdown("""
    <style>
    /* Reset nền và font */
    .stApp { background-color: #ffffff; }
    
    /* Tối ưu Bong bóng Chat trên Mobile */
    div[data-testid="stChatMessage"] {
        border-radius: 18px;
        margin-bottom: 8px;
        max-width: 98% !important;
        padding: 10px !important;
        border: 1px solid #f0f0f0;
    }

    /* Tối ưu các nút trên Mobile: To hơn, dễ bấm */
    .stButton button {
        width: 100%;
        border-radius: 12px !important;
        height: 45px;
        margin-bottom: 5px;
    }

    /* Cố định Input Bar và làm nó gọn hơn */
    .stChatInputContainer {
        position: fixed;
        bottom: 5px;
        padding: 0 5px;
        z-index: 1000;
    }

    /* Sidebar Mobile - làm gọn các mục */
    section[data-testid="stSidebar"] > div { padding-top: 20px; }

    /* CSS cho nút Dừng khẩn cấp */
    .stButton > button[kind="primary"] {
        background-color: #ff4b4b;
        border: none;
    }
    
    @media (max-width: 600px) {
        .stTitle { font-size: 1.2rem !important; }
        .stMarkdown p { font-size: 14px; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. JAVASCRIPT: TTS ĐA NGÔN NGỮ ---
def speak_js(text, speed, lang):
    clean_text = text.replace('"', "'").replace('\n', ' ')
    return f"""
    <script>
    window.speechSynthesis.cancel();
    var msg = new SpeechSynthesisUtterance("{clean_text}");
    msg.lang = "{lang}";
    msg.rate = {speed};
    window.speechSynthesis.speak(msg);
    </script>
    """

def stop_speak_js():
    return "<script>window.speechSynthesis.cancel();</script>"

# --- 3. KHỞI TẠO API & STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "voice_draft" not in st.session_state: st.session_state.voice_draft = ""

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 4. HÀM NHẬN DIỆN NGÔN NGỮ & XỬ LÝ ---
def get_lang_code(text):
    try:
        lang = detect(text)
        # Map kết quả langdetect sang mã Web Speech API
        mapping = {"vi": "vi-VN", "en": "en-US", "ja": "ja-JP", "ko": "ko-KR", "fr": "fr-FR"}
        return mapping.get(lang, "vi-VN") # Mặc định là Việt
    except: return "vi-VN"

def get_audio_download(text, lang_code):
    try:
        tts = gTTS(text=text, lang=lang_code.split('-')[0])
        fp = BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        return f'<a href="data:audio/mp3;base64,{b64}" download="ai_voice.mp3"><button style="width:100%; background:#4CAF50; color:white; border:none; border-radius:10px; padding:5px; cursor:pointer;">📥 Tải Mp3</button></a>'
    except: return ""

def process_ai(user_input):
    st.session_state.messages.append({"role": "user", "content": user_input})
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
        
        # TỰ ĐỘNG NHẬN DIỆN NGÔN NGỮ PHẢN HỒI
        detected_lang = get_lang_code(full)
        if st.session_state.get("auto_read", True):
            st.components.v1.html(speak_js(full, st.session_state.v_speed, detected_lang), height=0)

# --- 5. SIDEBAR (TỐI ƯU MOBILE) ---
with st.sidebar:
    st.title("📱 Nexus Pro")
    st.session_state.v_speed = st.slider("Tốc độ", 0.5, 2.0, 1.1)
    
    if st.button("🛑 DỪNG ĐỌC", type="primary", use_container_width=True):
        st.components.v1.html(stop_speak_js(), height=0)
    
    st.divider()
    st.session_state.auto_read = st.toggle("Tự phát voice", value=True)
    hands_free = st.toggle("⚡ Rảnh tay (Gửi luôn)", value=False)
    
    with st.expander("💾 Quản lý dữ liệu"):
        hist = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        st.download_button("📤 Tải .txt", data=hist, file_name="chat.txt", use_container_width=True)
        if st.button("📱 Hiện QR", use_container_width=True):
            qr = qrcode.make(hist[:800]); b = BytesIO(); qr.save(b, format="PNG")
            st.image(b)
        if st.button("🗑️ Xóa sạch", use_container_width=True):
            st.session_state.messages = []; st.session_state.voice_draft = ""; st.rerun()

# --- 6. GIAO DIỆN CHÍNH ---
st.title("Nexus Mobile Pro 🚀")

# Hiển thị Chat
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            # Nút điều khiển trong mỗi tin nhắn AI
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("🔊 Đọc lại", key=f"r_{i}"):
                    l = get_lang_code(m["content"])
                    st.components.v1.html(speak_js(m["content"], st.session_state.v_speed, l), height=0)
            with c2:
                st.markdown(get_audio_download(m["content"], get_lang_code(m["content"])), unsafe_allow_html=True)

# Khoảng trống để không bị đè bởi Input Bar
st.write("<br><br><br><br>", unsafe_allow_html=True)

# --- 7. INPUT (MIC & CHAT) ---
if st.session_state.voice_draft and not hands_free:
    with st.container():
        st.info("📝 Sửa bản dịch:")
        txt = st.text_area("", value=st.session_state.voice_draft, height=100)
        c_ok, c_no = st.columns(2)
        if c_ok.button("🚀 GỬI"):
            st.session_state.voice_draft = ""; process_ai(txt); st.rerun()
        if c_no.button("🗑️ HỦY"):
            st.session_state.voice_draft = ""; st.rerun()
else:
    # Bố cục Mic và Chat Input tối ưu cho màn hình hẹp
    c_m, c_i = st.columns([1, 5])
    with c_m:
        audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v8')
    
    if audio:
        with st.spinner("⚡"):
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']), language=None
            )
            if hands_free:
                process_ai(transcript.text); st.rerun()
            else:
                st.session_state.voice_draft = transcript.text; st.rerun()

    inp = st.chat_input("Nhập tin nhắn...")
    if inp:
        process_ai(inp); st.rerun()
