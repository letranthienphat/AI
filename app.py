import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64
from langdetect import detect
import re

# --- 1. CẤU HÌNH GIAO DIỆN SIÊU CẤP (RESPONSIVE) ---
st.set_page_config(page_title="AI Nexus v13 Full", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    
    /* Bong bóng chat tinh tế */
    div[data-testid="stChatMessage"] {
        border-radius: 15px; margin-bottom: 12px;
        border: 1px solid #f0f0f0; box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }

    /* Action Bar dưới mỗi tin nhắn */
    .action-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
    
    /* Thiết kế nút Gợi ý (Atomic Buttons) */
    .stButton > button {
        border-radius: 20px !important;
        border: 1px solid #007bff !important;
        background-color: #f8fbff !important;
        color: #007bff !important;
        font-weight: 600 !important;
        transition: 0.3s;
    }
    .stButton > button:hover {
        background-color: #007bff !important;
        color: white !important;
    }

    /* Cố định Input Bar đáy màn hình */
    .stChatInputContainer { position: fixed; bottom: 0; background: white; z-index: 1000; padding: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM TRỢ NĂNG (VOICE, LANG, COPY) ---
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
if "suggestions" not in st.session_state: st.session_state.suggestions = ["Chào bạn", "Hôm nay có gì mới?", "Kể chuyện cười", "Dịch tiếng Anh"]
if "voice_draft" not in st.session_state: st.session_state.voice_draft = ""

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 4. HÀM XỬ LÝ AI & GỢI Ý TÁCH BIỆT ---
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
        
        # Tự động đọc
        if st.session_state.get("auto_read", True):
            st.components.v1.html(speak_js(full, st.session_state.get("v_speed", 1.1), lang), height=0)

        # Cập nhật gợi ý: Tách biệt từng ý thành từng phần tử mảng
        try:
            sug_res = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": f"Dựa trên câu trả lời: '{full[:150]}', tạo 4 câu hỏi tiếp nối cực ngắn. Trả về các câu cách nhau bằng dấu phẩy, không đánh số."}]
            )
            raw = sug_res.choices[0].message.content
            st.session_state.suggestions = [s.strip() for s in re.split(',|\n', raw) if s.strip()][:4]
        except: pass

# --- 5. SIDEBAR: TRUNG TÂM DỮ LIỆU & CÀI ĐẶT ---
with st.sidebar:
    st.title("⚙️ Hệ thống v13")
    st.session_state.v_speed = st.slider("Tốc độ đọc", 0.5, 2.0, 1.1)
    if st.button("🛑 DỪNG ĐỌC", type="primary", use_container_width=True):
        st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)
    
    st.divider()
    st.session_state.auto_read = st.toggle("Tự động đọc", value=True)
    hands_free = st.toggle("🎙️ Rảnh tay", value=False)
    
    # TÍNH NĂNG SAO LƯU (BACKUP)
    st.subheader("📂 Sao lưu & Phục hồi")
    history_raw = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
    
    st.download_button("📤 Xuất file .txt", data=history_raw, file_name="ai_chat_backup.txt", use_container_width=True)
    
    uploaded_file = st.file_uploader("📥 Nhập file .txt", type="txt")
    if uploaded_file:
        if st.button("🔄 Khôi phục ngay"):
            content = uploaded_file.getvalue().decode("utf-8")
            # Logic khôi phục đơn giản (có thể nâng cấp thêm)
            st.info("Đã nhận dữ liệu, hãy chat để tiếp tục!")

    if st.button("🗑️ Xóa sạch hội thoại", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# --- 6. GIAO DIỆN CHÍNH ---
st.title("AI Nexus v13: Legacy 💎")

# Hiển thị hội thoại
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            # Action Bar: Đầy đủ các nút
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                if st.button("🔊 Nghe lại", key=f"r_{i}"):
                    st.components.v1.html(speak_js(m["content"], st.session_state.v_speed, get_lang_code(m["content"])), height=0)
            with c2:
                # Tính năng Tải âm thanh
                try:
                    tts = gTTS(text=m["content"][:250], lang=get_lang_code(m["content"]).split('-')[0])
                    b = BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
                    st.markdown(f'<a href="data:audio/mp3;base64,{b64}" download="ai_voice.mp3"><button style="width:100%; border-radius:15px; border:1px solid #ddd; padding:5px; cursor:pointer;">📥 Tải Mp3</button></a>', unsafe_allow_html=True)
                except: pass
            with c3:
                # Tính năng QR Code cho từng tin nhắn (Nếu cần)
                if st.button("📱 QR", key=f"qr_{i}"):
                    qr = qrcode.make(m["content"][:500]); buf = BytesIO(); qr.save(buf, format="PNG")
                    st.image(buf, width=150)

# --- KHU VỰC NÚT GỢI Ý NGUYÊN TỬ (ATOMIC) ---
st.write("---")
st.caption("💡 Gợi ý cho bạn (Mỗi nút một ý):")
if st.session_state.suggestions:
    # Chia cột để mỗi nút nằm riêng biệt
    cols = st.columns(len(st.session_state.suggestions))
    for idx, sug in enumerate(st.session_state.suggestions):
        # Làm sạch văn bản gợi ý (bỏ số thứ tự, gạch đầu dòng)
        clean_sug = re.sub(r'^\d+\.\s*|-\s*', '', sug).strip().replace('"', '')
        if cols[idx].button(clean_sug, key=f"sug_{idx}_{hash(clean_sug)}", use_container_width=True):
            process_ai(clean_sug)
            st.rerun()

# --- 7. KHU VỰC NHẬP LIỆU (MOBILE READY) ---
st.write("<br><br><br><br>", unsafe_allow_html=True)

if st.session_state.voice_draft and not hands_free:
    with st.container():
        st.warning("🎙️ Bản dịch giọng nói:")
        txt = st.text_area("", value=st.session_state.voice_draft, height=80)
        ca, cb = st.columns(2)
        if ca.button("🚀 GỬI", use_container_width=True):
            st.session_state.voice_draft = ""; process_ai(txt); st.rerun()
        if cb.button("🗑️ HỦY", use_container_width=True):
            st.session_state.voice_draft = ""; st.rerun()
else:
    col_m, col_i = st.columns([1, 6])
    with col_m:
        audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v13')
    if audio:
        with st.spinner(""):
            transcript = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']))
            if hands_free: process_ai(transcript.text); st.rerun()
            else: st.session_state.voice_draft = transcript.text; st.rerun()

    inp = st.chat_input("Hỏi tôi bất cứ điều gì...")
    if inp: process_ai(inp); st.rerun()
