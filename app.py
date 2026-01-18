import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64
from langdetect import detect, detect_langs

# --- 1. CẤU HÌNH UI SIÊU CẤP (RESPONSIVE) ---
st.set_page_config(page_title="AI Nexus Omni", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    /* Mobile-first: Tối ưu khoảng cách và kích thước nút */
    .stApp { transition: all 0.3s; }
    div[data-testid="stChatMessage"] {
        border-radius: 15px; margin-bottom: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    
    /* Thanh Action Bar dưới mỗi tin nhắn */
    .action-bar { display: flex; gap: 5px; margin-top: 10px; flex-wrap: wrap; }
    .action-btn { 
        background: #f0f2f5; border: none; border-radius: 8px; 
        padding: 5px 12px; font-size: 12px; cursor: pointer;
    }

    /* Fixed Input Bar cho Mobile */
    .stChatInputContainer { position: fixed; bottom: 0; left: 0; right: 0; background: white; z-index: 1000; padding: 10px 5%; }

    /* Nút bấm nổi bật */
    button[kind="primary"] { background-color: #007bff !important; border: none; }
    button[kind="secondary"] { background-color: #6c757d !important; }

    /* CSS cho Suggestion Chips */
    .chip {
        display: inline-block; padding: 5px 15px; margin: 5px;
        background: #e1f5fe; border: 1px solid #01579b;
        border-radius: 20px; font-size: 13px; cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. JAVASCRIPT: ĐIỀU KHIỂN NÂNG CAO ---
def get_js_tools(text, speed, lang):
    clean_text = text.replace('"', "'").replace('\n', ' ')
    return f"""
    <script>
    // Hàm đọc
    window.speak = () => {{
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance("{clean_text}");
        msg.lang = "{lang}"; msg.rate = {speed};
        window.speechSynthesis.speak(msg);
    }};
    // Hàm copy
    window.copyText = () => {{
        navigator.clipboard.writeText("{clean_text}");
        alert("Đã sao chép vào bộ nhớ tạm!");
    }};
    </script>
    """

# --- 3. KHỞI TẠO STATE & API ---
if "messages" not in st.session_state: st.session_state.messages = []
if "voice_draft" not in st.session_state: st.session_state.voice_draft = ""
if "theme" not in st.session_state: st.session_state.theme = "Light"

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 4. HÀM XỬ LÝ NGÔN NGỮ CHIẾM ƯU THẾ ---
def get_dominant_lang(text):
    try:
        # Lấy danh sách các ngôn ngữ được nhận diện
        langs = detect_langs(text)
        # Lấy ngôn ngữ có xác suất cao nhất
        main_lang = langs[0].lang
        mapping = {"vi": "vi-VN", "en": "en-US", "ja": "ja-JP", "ko": "ko-KR", "fr": "fr-FR", "zh": "zh-CN"}
        return mapping.get(main_lang, "vi-VN")
    except: return "vi-VN"

def get_audio_download(text, lang_code):
    try:
        tts = gTTS(text=text, lang=lang_code.split('-')[0])
        fp = BytesIO(); tts.write_to_fp(fp); b64 = base64.b64encode(fp.getvalue()).decode()
        return f'data:audio/mp3;base64,{b64}'
    except: return ""

# --- 5. SIDEBAR: SIÊU ĐIỀU KHIỂN ---
with st.sidebar:
    st.title("⚡ Nexus Terminal")
    st.session_state.v_speed = st.slider("Tốc độ đọc", 0.5, 2.0, 1.1)
    
    col_stop, col_clear = st.columns(2)
    with col_stop:
        if st.button("🛑 Dừng đọc", use_container_width=True):
            st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)
    with col_clear:
        if st.button("🗑️ Reset", use_container_width=True):
            st.session_state.messages = []; st.rerun()

    st.divider()
    st.session_state.auto_read = st.toggle("Tự động phát âm thanh", value=True)
    hands_free = st.toggle("🎙️ Rảnh tay (Nói & Gửi)", value=False)
    
    st.subheader("📤 Xuất dữ liệu")
    history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
    st.download_button("📥 Tải File .txt", data=history_text, file_name="chat_nexus.txt", use_container_width=True)
    if st.button("📱 Tạo mã QR", use_container_width=True):
        qr = qrcode.make(history_text[:500]); buf = BytesIO(); qr.save(buf, format="PNG")
        st.image(buf)

# --- 6. GIAO DIỆN CHÍNH ---
st.title("AI Nexus Omni ⚡")

# Gợi ý nhanh (Quick Chips)
suggestions = ["Tóm tắt đoạn chat", "Dịch sang tiếng Anh", "Giải thích chi tiết hơn", "Viết code ví dụ"]
cols_suggest = st.columns(len(suggestions))
for i, suggest in enumerate(suggestions):
    if cols_suggest[i].button(suggest, key=f"sug_{i}"):
        st.session_state.messages.append({"role": "user", "content": suggest})
        # Logic xử lý AI sẽ được trigger ở dưới

# HIỂN THỊ CHAT
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            # ACTION BAR
            lang = get_dominant_lang(m["content"])
            audio_data = get_audio_download(m["content"], lang)
            
            col1, col2, col3, col4 = st.columns([1,1,1,1])
            with col1:
                if st.button("🔊 Đọc", key=f"speak_{i}"):
                    st.components.v1.html(get_js_tools(m["content"], st.session_state.v_speed, lang) + "<script>window.speak();</script>", height=0)
            with col2:
                st.markdown(f'<a href="{audio_data}" download="voice_{i}.mp3" style="text-decoration:none;"><button style="width:100%; border-radius:10px; border:1px solid #ddd; cursor:pointer;">📥 Tải</button></a>', unsafe_allow_html=True)
            with col3:
                if st.button("📋 Copy", key=f"copy_{i}"):
                    st.components.v1.html(get_js_tools(m["content"], 1, lang) + "<script>window.copyText();</script>", height=0)
            with col4:
                if st.button("🌐 Dịch", key=f"trans_{i}"):
                    st.info("Tính năng dịch đang được nâng cấp...")

# --- 7. INPUT AREA (ĐA PHƯƠNG THỨC) ---
st.write("<br><br><br><br>", unsafe_allow_html=True)

def process_ai_logic(text):
    st.session_state.messages.append({"role": "user", "content": text})
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
        if st.session_state.auto_read:
            lang = get_dominant_lang(full)
            st.components.v1.html(get_js_tools(full, st.session_state.v_speed, lang) + "<script>window.speak();</script>", height=0)

# Nhập liệu giọng nói
if st.session_state.voice_draft and not hands_free:
    with st.container():
        st.info("📝 Bản nháp:")
        v_text = st.text_area("", value=st.session_state.voice_draft)
        if st.button("🚀 Gửi ngay", use_container_width=True):
            st.session_state.voice_draft = ""; process_ai_logic(v_text); st.rerun()
else:
    c_mic, c_in = st.columns([1, 6])
    with c_mic:
        audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v9')
    if audio:
        with st.spinner(""):
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo", file=("v.wav", audio['bytes'])
            )
            if hands_free: process_ai_logic(transcript.text); st.rerun()
            else: st.session_state.voice_draft = transcript.text; st.rerun()

    prompt = st.chat_input("Hỏi tôi bất cứ điều gì...")
    if prompt:
        process_ai_logic(prompt); st.rerun()
