import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64

# --- 1. CẤU HÌNH UI RESPONSIVE & LIGHT MODE ---
st.set_page_config(page_title="AI Global Nexus", layout="wide", page_icon="🌐")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    div[data-testid="stChatMessage"] {
        border-radius: 15px;
        padding: 12px;
        margin-bottom: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
    /* Fixed Input Bar */
    .stChatInputContainer { position: fixed; bottom: 15px; z-index: 1000; }
    
    /* Stop Button Styling */
    .stop-btn {
        background-color: #ff4b4b !important;
        color: white !important;
        border-radius: 20px !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. JAVASCRIPT: ĐA NGÔN NGỮ & DỪNG ĐỌC ---
def speak_js(text, speed, lang_code):
    clean_text = text.replace('"', "'").replace('\n', ' ')
    return f"""
    <script>
    window.speechSynthesis.cancel();
    var msg = new SpeechSynthesisUtterance("{clean_text}");
    msg.lang = "{lang_code}";
    msg.rate = {speed};
    window.speechSynthesis.speak(msg);
    </script>
    """

def stop_speak_js():
    return "<script>window.speechSynthesis.cancel();</script>"

# --- 3. KHỞI TẠO STATE & API ---
if "messages" not in st.session_state: st.session_state.messages = []
if "voice_draft" not in st.session_state: st.session_state.voice_draft = ""

try:
    client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")
except:
    st.error("⚠️ Lỗi: Kiểm tra GROQ_API_KEY trong Streamlit Secrets!")
    st.stop()

# --- 4. CÔNG CỤ TẢI FILE & XỬ LÝ AI ---
def get_audio_download_link(text, lang):
    try:
        # Chuyển đổi mã ngôn ngữ Web sang mã gTTS (vd: vi-VN -> vi)
        gtts_lang = lang.split('-')[0]
        tts = gTTS(text=text, lang=gtts_lang)
        fp = BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        return f'<a href="data:audio/mp3;base64,{b64}" download="ai_speech.mp3" style="text-decoration:none;"><button style="background-color:#4CAF50; border:none; color:white; padding:4px 12px; border-radius:10px; cursor:pointer; font-size:12px;">📥 Tải .mp3</button></a>'
    except: return ""

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
            st.components.v1.html(speak_js(full, st.session_state.v_speed, st.session_state.target_lang), height=0)

# --- 5. SIDEBAR: ĐIỀU KHIỂN ĐA NĂNG ---
with st.sidebar:
    st.title("⚙️ AI Global Control")
    
    # CHỌN NGÔN NGỮ ĐỌC
    st.subheader("🌐 Ngôn ngữ đọc (TTS)")
    lang_options = {
        "Tiếng Việt": "vi-VN",
        "English (US)": "en-US",
        "English (UK)": "en-GB",
        "Français": "fr-FR",
        "日本語 (Japanese)": "ja-JP",
        "한국어 (Korean)": "ko-KR"
    }
    selected_lang_name = st.selectbox("Chọn giọng đọc:", list(lang_options.keys()))
    st.session_state.target_lang = lang_options[selected_lang_name]

    st.session_state.v_speed = st.slider("Tốc độ đọc", 0.5, 2.0, 1.1)
    
    # NÚT DỪNG ĐỌC KHẨN CẤP
    if st.button("🛑 DỪNG ĐỌC NGAY", use_container_width=True, type="primary"):
        st.components.v1.html(stop_speak_js(), height=0)
        st.toast("Đã dừng giọng nói!")

    st.divider()
    st.session_state.auto_read = st.toggle("Tự động đọc phản hồi", value=True)
    hands_free = st.toggle("⚡ Rảnh tay (Nói gửi luôn)", value=False)
    
    st.divider()
    st.subheader("💾 Dữ liệu")
    history_txt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
    c1, c2 = st.columns(2)
    with c1: st.download_button("📤 Xuất .txt", data=history_txt, file_name="history.txt")
    with c2: 
        if st.button("📱 QR"):
            qr = qrcode.make(history_txt[:1000]); b = BytesIO(); qr.save(b, format="PNG")
            st.image(b)

    if st.button("🗑️ Xóa sạch hội thoại"):
        st.session_state.messages = []; st.session_state.voice_draft = ""; st.rerun()

# --- 6. GIAO DIỆN CHÍNH ---
st.title("AI Global Nexus 🚀")

# Hiển thị chat
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            col_read, col_dl = st.columns([1, 4])
            with col_read:
                if st.button("🔊", key=f"r_{i}"):
                    st.components.v1.html(speak_js(m["content"], st.session_state.v_speed, st.session_state.target_lang), height=0)
            with col_dl:
                st.markdown(get_audio_download_link(m["content"], st.session_state.target_lang), unsafe_allow_html=True)

# --- 7. INPUT AREA (TỐI ƯU CHO MOBILE) ---
st.write("<div style='height:100px'></div>", unsafe_allow_html=True)

if st.session_state.voice_draft and not hands_free:
    with st.container():
        st.info("📝 Bản dịch giọng nói:")
        txt = st.text_area("", value=st.session_state.voice_draft, height=80)
        ca, cb = st.columns(2)
        if ca.button("🚀 GỬI", use_container_width=True):
            st.session_state.voice_draft = ""; process_ai(txt); st.rerun()
        if cb.button("🗑️ HỦY", use_container_width=True):
            st.session_state.voice_draft = ""; st.rerun()
else:
    c_m, c_i = st.columns([1, 8])
    with c_m:
        # Mic tự động nhận diện ngôn ngữ (Whisper Turbo)
        audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v7')
    
    if audio:
        with st.spinner("⚡..."):
            # Để language=None để Whisper tự nhận diện bạn đang nói tiếng Anh hay Việt
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']), language=None
            )
            if hands_free:
                process_ai(transcript.text); st.rerun()
            else:
                st.session_state.voice_draft = transcript.text; st.rerun()

    inp = st.chat_input("Nhập tin nhắn (Hỗ trợ đa ngôn ngữ)...")
    if inp:
        process_ai(inp); st.rerun()
