import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
from io import BytesIO

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="AI Ultimate Manager", layout="wide", page_icon="💼")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; color: #212529; }
    .stChatMessage { border-radius: 12px; border: 1px solid #dee2e6; background: white; }
    div[data-testid="stToolbar"] { visibility: hidden; }
    .control-btn { border: 2px solid #0d6efd; color: #0d6efd; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. JAVASCRIPT: TTS & IMPORT/EXPORT ---
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

def stop_speak_js():
    return "<script>window.speechSynthesis.cancel();</script>"

# --- 3. KHỞI TẠO STATE & API ---
if "messages" not in st.session_state: st.session_state.messages = []
if "draft_text" not in st.session_state: st.session_state.draft_text = ""

try:
    client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")
except:
    st.error("⚠️ Lỗi: Chưa có GROQ_API_KEY trong Secrets!")
    st.stop()

# --- 4. HÀM XỬ LÝ DỮ LIỆU ---
def format_chat_history():
    return "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])

def parse_history_file(file_content):
    """Đọc file .txt và khôi phục lịch sử chat"""
    lines = file_content.split('\n')
    new_history = []
    current_role = None
    current_content = []
    
    for line in lines:
        if line.startswith("USER: "):
            if current_role: # Lưu tin nhắn trước đó
                new_history.append({"role": current_role, "content": "\n".join(current_content)})
            current_role = "user"
            current_content = [line.replace("USER: ", "")]
        elif line.startswith("ASSISTANT: "):
            if current_role:
                new_history.append({"role": current_role, "content": "\n".join(current_content)})
            current_role = "assistant"
            current_content = [line.replace("ASSISTANT: ", "")]
        else:
            if current_content: current_content.append(line)
            
    if current_role: # Lưu tin cuối cùng
        new_history.append({"role": current_role, "content": "\n".join(current_content)})
    
    return new_history

def process_response(user_input):
    if not user_input: return
    st.session_state.messages.append({"role": "user", "content": user_input})
    
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
            
            if st.session_state.auto_read:
                st.components.v1.html(speak_js(full_res, st.session_state.voice_speed), height=0)
        except Exception as e:
            st.error(f"Lỗi: {e}")

# --- 5. SIDEBAR: TRUNG TÂM QUẢN LÝ ---
with st.sidebar:
    st.header("🎛️ Điều Khiển")
    
    # 5.1. GIỌNG NÓI
    col_voice1, col_voice2 = st.columns(2)
    with col_voice1:
        st.session_state.voice_speed = st.slider("Tốc độ", 0.5, 2.0, 1.1)
    with col_voice2:
        st.write("") # Spacer
        st.write("")
        if st.button("🔇 DỪNG ĐỌC", type="primary"):
            st.components.v1.html(stop_speak_js(), height=0)
            
    st.session_state.auto_read = st.toggle("Tự động đọc tin mới", value=True)
    
    st.divider()
    
    # 5.2. QUẢN LÝ DỮ LIỆU (IMPORT / EXPORT)
    st.subheader("💾 Dữ liệu Chat")
    
    # XUẤT (EXPORT)
    history_text = format_chat_history()
    col_ex1, col_ex2 = st.columns(2)
    with col_ex1:
        st.download_button("📥 Tải .txt", data=history_text, file_name="chat_history.txt", mime="text/plain")
    with col_ex2:
        if st.button("📱 Xem QR"):
            if not history_text:
                st.warning("Chưa có tin nhắn!")
            else:
                qr = qrcode.make(history_text[:1000]) # Giới hạn 1000 ký tự cho QR dễ quét
                buf = BytesIO()
                qr.save(buf, format="PNG")
                st.image(buf, caption="Quét để lấy nội dung chat")

    # NHẬP (IMPORT)
    uploaded_file = st.file_uploader("📂 Nhập lại lịch sử (.txt)", type="txt")
    if uploaded_file is not None:
        string_data = uploaded_file.getvalue().decode("utf-8")
        if st.button("🔄 Khôi phục cuộc trò chuyện"):
            restored_msgs = parse_history_file(string_data)
            if restored_msgs:
                st.session_state.messages = restored_msgs
                st.success("Đã khôi phục thành công! Hãy chat tiếp.")
                st.rerun()
            else:
                st.error("File lỗi hoặc định dạng không đúng.")

    st.divider()
    hands_free = st.toggle("⚡ Rảnh tay (Nói gửi luôn)", value=False)
    if st.button("🗑️ Xóa Sạch Chat"):
        st.session_state.messages = []
        st.session_state.draft_text = ""
        st.rerun()

# --- 6. GIAO DIỆN CHÍNH ---
st.title("AI Ultimate Manager 💼")

# HIỂN THỊ CHAT
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        # Nút đọc lại thủ công cho từng tin nhắn
        if m["role"] == "assistant":
            if st.button("🔊", key=f"read_{hash(m['content'])}"):
                st.components.v1.html(speak_js(m["content"], st.session_state.voice_speed), height=0)

# --- 7. INPUT AREA ---
st.write("---")

if st.session_state.draft_text and not hands_free:
    with st.container():
        st.info("📝 **Bản nháp giọng nói:**")
        edited_text = st.text_area("Sửa nội dung:", value=st.session_state.draft_text, height=100)
        c1, c2 = st.columns(2)
        if c1.button("🚀 GỬI", type="primary", use_container_width=True):
            st.session_state.draft_text = ""
            process_response(edited_text)
            st.rerun()
        if c2.button("❌ HỦY", use_container_width=True):
            st.session_state.draft_text = ""
            st.rerun()
else:
    c_mic, c_input = st.columns([1, 10])
    with c_mic:
        audio_data = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_manager')
    
    if audio_data:
        with st.spinner("⚡ Whisper đang dịch..."):
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo", file=("voice.wav", audio_data['bytes']), language="vi"
            )
            text_result = transcript.text
            
            if hands_free:
                process_response(text_result)
                st.rerun()
            else:
                st.session_state.draft_text = text_result
                st.rerun()

    text_input = st.chat_input("Nhập tin nhắn...")
    if text_input:
        process_response(text_input)
        st.rerun()
