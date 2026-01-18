import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64
from langdetect import detect

# --- 1. CẤU HÌNH UI GRID POWER (NÚT TÁCH BIỆT) ---
st.set_page_config(page_title="Nexus Grid Power", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    /* Nền trắng sang trọng */
    .stApp { background-color: #ffffff; }
    
    /* Hiệu ứng nút gợi ý tách biệt hoàn toàn */
    .suggestion-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 12px;
        margin: 15px 0;
    }
    
    /* Ép các nút Streamlit trong khu vực gợi ý phải trông đẹp hơn */
    div.stButton > button {
        width: 100%;
        border-radius: 12px !important;
        border: 1px solid #007bff !important;
        background-color: #f0f7ff !important;
        color: #007bff !important;
        font-weight: 500;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    div.stButton > button:hover {
        background-color: #007bff !important;
        color: white !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* Action bar cho từng tin nhắn */
    .action-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }

    /* Input cố định đáy */
    .stChatInputContainer { position: fixed; bottom: 0; background: white; z-index: 1000; padding: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM HỖ TRỢ NGÔN NGỮ & VOICE ---
def speak_js(text, speed, lang):
    clean = text.replace('"', "'").replace('\n', ' ')
    return f"<script>window.speechSynthesis.cancel(); var m=new SpeechSynthesisUtterance('{clean}'); m.lang='{lang}'; m.rate={speed}; window.speechSynthesis.speak(m);</script>"

def get_lang_code(text):
    try:
        l = detect(text)
        mapping = {"vi":"vi-VN", "en":"en-US", "ja":"ja-JP", "ko":"ko-KR", "fr":"fr-FR"}
        return mapping.get(l, "vi-VN")
    except: return "vi-VN"

# --- 3. KHỞI TẠO STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "suggestions" not in st.session_state: st.session_state.suggestions = ["Chào bạn!", "Bạn khỏe không?", "Dịch tin nhắn", "Kể chuyện cười"]
if "voice_draft" not in st.session_state: st.session_state.voice_draft = ""

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 4. HÀM XỬ LÝ CHÍNH ---
def process_ai(user_input):
    st.session_state.messages.append({"role": "user", "content": user_input})
    lang = get_lang_code(user_input)
    
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
        
        # Phát voice tự động
        if st.session_state.get("auto_read", True):
            st.components.v1.html(speak_js(full, st.session_state.v_speed, lang), height=0)

        # CẬP NHẬT GỢI Ý ĐỘNG (DYNAMIC)
        try:
            sug_res = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": f"Dựa trên: '{full[:150]}', tạo 4 câu hỏi tiếp nối cực ngắn (2-4 từ). Ngôn ngữ: {lang}. Trả về dạng: câu 1, câu 2, câu 3, câu 4"}]
            )
            st.session_state.suggestions = sug_res.choices[0].message.content.split(',')
        except: pass

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Điều khiển")
    st.session_state.v_speed = st.slider("Tốc độ đọc", 0.5, 2.0, 1.1)
    if st.button("🛑 DỪNG ĐỌC", type="primary", use_container_width=True):
        st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)
    st.session_state.auto_read = st.toggle("Tự động đọc", value=True)
    hands_free = st.toggle("🎙️ Rảnh tay", value=False)
    
    if st.button("🗑️ Xóa hội thoại", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# --- 6. GIAO DIỆN CHÍNH ---
st.title("Nexus Grid Power ⚡")

# Hiển thị hội thoại
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            # Action Bar (Nút chức năng dưới tin nhắn)
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                if st.button("🔊 Nghe lại", key=f"r_{i}"):
                    st.components.v1.html(speak_js(m["content"], st.session_state.v_speed, get_lang_code(m["content"])), height=0)
            with c2:
                # Nút tải mp3
                try:
                    tts = gTTS(text=m["content"][:250], lang=get_lang_code(m["content"]).split('-')[0])
                    b = BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
                    st.markdown(f'<a href="data:audio/mp3;base64,{b64}" download="voice.mp3"><button style="width:100%; border-radius:12px; border:1px solid #ddd; padding:6px; cursor:pointer;">📥 Tải về</button></a>', unsafe_allow_html=True)
                except: pass
            with c3:
                if st.button("📋 Copy", key=f"cp_{i}"):
                    st.toast("Đã sao chép!")

# KHU VỰC GỢI Ý (Nút bấm tách biệt hoàn toàn)
st.write("---")
st.caption("🔍 Gợi ý thông minh cho bạn:")
# Sử dụng container để bao bọc các nút gợi ý tách biệt
with st.container():
    # Chia thành các cột nhỏ để tạo hiệu ứng tách biệt từng nút
    sug_cols = st.columns(len(st.session_state.suggestions))
    for idx, sug in enumerate(st.session_state.suggestions):
        clean_sug = sug.strip().replace('"', '')
        if sug_cols[idx].button(clean_sug, key=f"sug_{idx}_{hash(clean_sug)}", use_container_width=True):
            process_ai(clean_sug)
            st.rerun()

# --- 7. INPUT (MIC & TEXT) ---
st.write("<br><br><br><br>", unsafe_allow_html=True)

if st.session_state.voice_draft and not hands_free:
    with st.container():
        st.warning("🎙️ Sửa bản dịch:")
        txt = st.text_area("", value=st.session_state.voice_draft, height=70)
        c_ok, c_no = st.columns(2)
        if c_ok.button("🚀 GỬI"):
            st.session_state.voice_draft = ""; process_ai(txt); st.rerun()
        if c_no.button("🗑️ HỦY"):
            st.session_state.voice_draft = ""; st.rerun()
else:
    c_m, c_i = st.columns([1, 6])
    with c_m:
        audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v11')
    if audio:
        with st.spinner(""):
            transcript = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']))
            if hands_free: process_ai(transcript.text); st.rerun()
            else: st.session_state.voice_draft = transcript.text; st.rerun()

    inp = st.chat_input("Hỏi tôi bất cứ điều gì...")
    if inp: process_ai(inp); st.rerun()
