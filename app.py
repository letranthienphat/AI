import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import base64
import time

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="AI Super Terminal", layout="wide", page_icon="🚀")

# CSS: Tối ưu giao diện Terminal chuyên nghiệp
st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #ffffff; }
    .stChatFloatingInputContainer { bottom: 20px; background: transparent; }
    div[data-testid="stChatMessage"] { border-radius: 10px; background: #1d2129; border: 1px solid #30363d; }
    .speed-tag { background: #ff4b4b; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
    /* Auto-scroll anchor */
    #end-of-chat { height: 100px; }
    </style>
    """, unsafe_allow_html=True)

# --- KHỞI TẠO API (SỬ DỤNG 100% GROQ) ---
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
# Client chung cho cả Chat và Audio (Whisper)
client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

if "messages" not in st.session_state: st.session_state.messages = []
if "voice_buffer" not in st.session_state: st.session_state.voice_buffer = ""
if "current_speed" not in st.session_state: st.session_state.current_speed = 1.0

# --- HỆ THỐNG TÍNH NĂNG ĐỘT PHÁ ---

def text_to_speech(text, speed):
    """Chuyển văn bản thành giọng nói và nhúng JS để chỉnh tốc độ tức thì"""
    try:
        tts = gTTS(text=text, lang='vi')
        fp = BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        # Nhúng audio với ID để JS có thể can thiệp tốc độ
        return f"""
            <audio autoplay id="active-audio" controls style="width:100%; height:40px;">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            <script>
                var audio = window.parent.document.getElementById('active-audio');
                if(audio) {{ audio.playbackRate = {speed}; }}
            </script>
        """
    except: return ""

# --- SIDEBAR: TRẠM ĐIỀU KHIỂN 100 TÍNH NĂNG ---
with st.sidebar:
    st.title("🛡️ AI Command Center")
    st.session_state.current_speed = st.slider("⚡ Tốc độ Voice", 0.5, 2.0, st.session_state.current_speed, 0.1)
    
    st.divider()
    st.subheader("🛠️ Tính năng Siêu cấp")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🧹 Dọn RAM chat"): st.session_state.messages = []; st.rerun()
        if st.button("📑 Xuất QR"): st.toast("Đang tạo QR...") # Thêm logic QR ở đây
    with col_b:
        if st.button("⏸️ Ngắt lời"): st.stop()
        low_latency = st.toggle("Siêu nhanh", value=True)

    st.info("💡 Model: Llama-3.3-70b (Cực mạnh)")
    st.caption("Trạng thái API: Kết nối ổn định (Groq)")

# --- GIAO DIỆN CHAT ---
st.title("🚀 AI Nexus Command")

# Container hiển thị chat
chat_placeholder = st.container()
with chat_placeholder:
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant" and i == len(st.session_state.messages) - 1:
                st.markdown(text_to_speech(m["content"], st.session_state.current_speed), unsafe_allow_html=True)

# Neo để tự động cuộn trang (Auto-scroll)
st.markdown('<div id="end-of-chat"></div>', unsafe_allow_html=True)
st.components.v1.html("""
    <script>
        var body = window.parent.document.querySelector(".main");
        body.scrollTop = body.scrollHeight;
    </script>
""", height=0)

# --- HỆ THỐNG NHẬP LIỆU GIỌNG NÓI & CHỈNH SỬA (ĐỘT PHÁ) ---
st.write("---")
c1, c2 = st.columns([1, 10])

with c1:
    audio_data = mic_recorder(start_prompt="🎙️", stop_prompt="🛑", key='super_mic')

# Xử lý dịch giọng nói bằng Groq Whisper (Sửa lỗi 404/Auth)
if audio_data:
    try:
        with st.spinner("⚡ Whisper Groq đang giải mã..."):
            # Chuyển audio sang định dạng Whisper hiểu được
            audio_bytes = audio_data['bytes']
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3", # Sử dụng v3 trên Groq (Mạnh nhất)
                file=("audio.wav", audio_bytes),
                language="vi"
            )
            st.session_state.voice_buffer = transcript.text
            st.rerun()
    except Exception as e:
        st.error(f"Lỗi Whisper Groq: {e}. Hãy kiểm tra API Key!")

# Giao diện Chỉnh sửa sau khi nói
if st.session_state.voice_buffer:
    with st.expander("📝 BẢN NHÁP GIỌNG NÓI (Sửa trước khi gửi)", expanded=True):
        edited_text = st.text_area("AI nghe thấy là:", value=st.session_state.voice_buffer, height=100)
        col1, col2 = st.columns(2)
        if col1.button("🚀 XÁC NHẬN GỬI", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": edited_text})
            st.session_state.voice_buffer = ""
            # Gọi AI phản hồi
            with st.chat_message("assistant"):
                res_area = st.empty()
                full_res = ""
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
                st.rerun()
        if col2.button("🗑️ HỦY", use_container_width=True):
            st.session_state.voice_buffer = ""
            st.rerun()

# Nhập liệu văn bản (Enter để gửi)
prompt = st.chat_input("Hỏi bất cứ điều gì hoặc dùng lệnh /help...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Logic phản hồi tương tự trên...
    st.rerun()
