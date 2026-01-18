import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import qrcode
from io import BytesIO
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="AI Live Hub", layout="wide", page_icon="🎙️")

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "auto_read" not in st.session_state:
    st.session_state.auto_read = False

# --- HÀM XỬ LÝ ÂM THANH ---
def text_to_speech(text):
    tts = gTTS(text=text, lang='vi')
    fp = BytesIO()
    tts.write_to_fp(fp)
    return fp.getvalue()

# --- HÀM TẠO QR ---
def generate_qr_codes(text, chunk_size=1000):
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    qr_images = []
    for i, chunk in enumerate(chunks):
        qr = qrcode.make(f"Part {i+1}/{len(chunks)}:\n{chunk}")
        buf = BytesIO()
        qr.save(buf, format="PNG")
        qr_images.append(buf.getvalue())
    return qr_images

# --- 2. THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.title("🎙️ AI Live Settings")
    live_mode = st.checkbox("Chế độ Live (Tự động mở Mic)", value=False)
    
    st.divider()
    if st.button("📄 Tạo mã QR Lịch sử"):
        full_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        st.session_state.qr_results = generate_qr_codes(full_text)

    if st.button("🗑️ Xóa hội thoại"):
        st.session_state.messages = []
        st.rerun()

# --- 3. GIAO DIỆN CHAT ---
st.title("🤖 AI Voice & Live Assistant")

# Hiển thị QR (Nếu có)
if "qr_results" in st.session_state:
    cols = st.columns(len(st.session_state.qr_results))
    for idx, qr in enumerate(st.session_state.qr_results):
        with cols[idx]:
            st.image(qr, caption=f"Phần {idx+1}")
            # Trình duyệt sẽ tự hỏi vị trí lưu khi nhấn nút này
            st.download_button("💾 Lưu về máy", data=qr, file_name=f"chat_qr_part_{idx+1}.png", mime="image/png")

# Hiển thị hội thoại
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        # Nút đọc lại thủ công
        if m["role"] == "assistant":
            if st.button(f"🔊 Đọc", key=f"tts_{i}"):
                audio_data = text_to_speech(m["content"])
                st.audio(audio_data, format="audio/mp3", autoplay=True)

# --- 4. NHẬP LIỆU (GIỌNG NÓI & CHỮ) ---
st.write("---")
c1, c2 = st.columns([9, 1])

with c2:
    # Nút Micro để nói (STT)
    audio_input = mic_recorder(start_prompt="🎙️", stop_prompt="🛑", key='mic')

with c1:
    text_input = st.chat_input("Nhập tin nhắn hoặc nhấn Mic...")

# Xử lý Logic gửi tin
input_data = None
used_voice = False

if audio_input:
    # Ở phiên bản này, mic_recorder trả về audio. Trong thực tế cần gọi API STT (như OpenAI Whisper) 
    # để chuyển audio thành text. Để demo, ta giả định text từ audio.
    # LƯU Ý: mic_recorder cần kết nối API Whisper để dịch chính xác.
    input_data = "Tính năng nói đang được kết nối..." # Placeholder
    used_voice = True
elif text_input:
    input_data = text_input

if input_data:
    st.session_state.messages.append({"role": "user", "content": input_data})
    
    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                res_area.markdown(full_res + "▌")
        res_area.markdown(full_res)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        
        # Tự động đọc nếu dùng giọng nói hoặc bật Live Mode
        if used_voice or live_mode:
            audio_res = text_to_speech(full_res)
            st.audio(audio_res, format="audio/mp3", autoplay=True)
            
        if live_mode:
            st.info("Đang lắng nghe... (Live Mode)")
            # Live mode sẽ đợi bạn nhấn Mic tiếp theo
