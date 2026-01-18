import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64
from langdetect import detect

# --- 1. CẤU HÌNH UI SIÊU CẤP ---
st.set_page_config(page_title="Nexus Context Master", layout="wide", page_icon="🧠")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    /* Bong bóng chat tinh tế */
    div[data-testid="stChatMessage"] {
        border-radius: 15px; margin-bottom: 12px;
        border: 1px solid #f0f0f0; box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    /* Thanh Suggestion Chips */
    .chip-container { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
    .stButton button { border-radius: 20px !important; transition: 0.2s; }
    /* Input dính đáy cho Mobile */
    .stChatInputContainer { position: fixed; bottom: 0; background: white; z-index: 1000; padding: 10px 0; }
    @media (max-width: 600px) { .stChatInputContainer { padding: 5px; } }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CÔNG CỤ HỖ TRỢ (JS & NGÔN NGỮ) ---
def speak_js(text, speed, lang):
    clean = text.replace('"', "'").replace('\n', ' ')
    return f"<script>window.speechSynthesis.cancel(); var m=new SpeechSynthesisUtterance('{clean}'); m.lang='{lang}'; m.rate={speed}; window.speechSynthesis.speak(m);</script>"

def get_lang_full(text):
    try:
        l = detect(text)
        mapping = {"vi":"vi-VN", "en":"en-US", "ja":"ja-JP", "ko":"ko-KR", "fr":"fr-FR", "zh":"zh-CN"}
        return mapping.get(l, "vi-VN")
    except: return "vi-VN"

# --- 3. KHỞI TẠO STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "suggestions" not in st.session_state: st.session_state.suggestions = ["Chào buổi sáng!", "Kể tôi nghe một chuyện vui", "Dịch giúp tôi một câu"]
if "voice_draft" not in st.session_state: st.session_state.voice_draft = ""

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 4. HÀM XỬ LÝ AI VÀ GỢI Ý ĐỘNG ---
def process_ai(user_input):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 1. Phát hiện ngôn ngữ đầu vào để ép AI trả lời tương ứng
    user_lang = get_lang_full(user_input)
    
    with st.chat_message("assistant"):
        p = st.empty(); full = ""
        # Gọi Groq cho phản hồi chính
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": f"Respond primarily in the language detected: {user_lang}"}] + 
                     [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True
        )
        for chunk in res:
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                p.markdown(full + "▌")
        p.markdown(full)
        st.session_state.messages.append({"role": "assistant", "content": full})
        
        # 2. Tự động đọc đúng ngôn ngữ
        if st.session_state.get("auto_read", True):
            st.components.v1.html(speak_js(full, st.session_state.get("v_speed", 1.1), user_lang), height=0)

        # 3. TẠO GỢI Ý ĐỘNG (Dựa trên ngữ cảnh vừa trả lời)
        try:
            sug_res = client.chat.completions.create(
                model="llama-3.1-8b-instant", # Model nhỏ để cực nhanh
                messages=[{"role": "user", "content": f"Dựa trên câu trả lời này: '{full[:200]}', hãy đưa ra 3 câu hỏi gợi ý ngắn gọn (dưới 6 từ) mà người dùng có thể muốn hỏi tiếp. Ngôn ngữ: {user_lang}. Chỉ trả về các câu hỏi cách nhau bằng dấu phẩy."}]
            )
            new_sugs = sug_res.choices[0].message.content.split(',')
            st.session_state.suggestions = [s.strip() for s in new_sugs if s.strip()][:3]
        except: pass

# --- 5. SIDEBAR: ĐIỀU KHIỂN TỔNG LỰC ---
with st.sidebar:
    st.title("🛡️ Nexus v10")
    st.session_state.v_speed = st.slider("Tốc độ giọng đọc", 0.5, 2.0, 1.1)
    if st.button("🛑 DỪNG ĐỌC", type="primary", use_container_width=True):
        st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)
    
    st.divider()
    st.session_state.auto_read = st.toggle("Tự động đọc", value=True)
    hands_free = st.toggle("🎙️ Rảnh tay (Nói & Gửi)", value=False)
    
    with st.expander("📂 Quản lý & Xuất bản"):
        hist = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        st.download_button("📥 Tải lịch sử .txt", data=hist, file_name="chat.txt", use_container_width=True)
        if st.button("📱 Tạo mã QR", use_container_width=True):
            qr = qrcode.make(hist[:600]); buf = BytesIO(); qr.save(buf, format="PNG"); st.image(buf)
        if st.button("🗑️ Xóa sạch chat", use_container_width=True):
            st.session_state.messages = []; st.rerun()

# --- 6. GIAO DIỆN CHÁNH ---
st.title("AI Nexus: Context Master 🧠")

# HIỂN THỊ CHAT
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            # Action Bar cho từng tin nhắn
            c1, c2, c3 = st.columns([1,1,1])
            with c1:
                if st.button("🔊 Nghe lại", key=f"r_{i}"):
                    st.components.v1.html(speak_js(m["content"], st.session_state.v_speed, get_lang_full(m["content"])), height=0)
            with c2:
                # Tải mp3
                try:
                    tts = gTTS(text=m["content"][:200], lang=get_lang_full(m["content"]).split('-')[0])
                    b = BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
                    st.markdown(f'<a href="data:audio/mp3;base64,{b64}" download="voice.mp3"><button style="width:100%; border-radius:15px; border:1px solid #ddd; padding:5px;">📥 Tải</button></a>', unsafe_allow_html=True)
                except: pass
            with c3:
                if st.button("📋 Copy", key=f"cp_{i}"):
                    st.toast("Đã sao chép!") # Giản lược copy cho nhanh

# GỢI Ý ĐỘNG (DƯỚI PHẢN HỒI MỚI NHẤT)
st.write("---")
st.caption("💡 Gợi ý cho bạn:")
cols = st.columns(len(st.session_state.suggestions))
for idx, sug in enumerate(st.session_state.suggestions):
    if cols[idx].button(sug, key=f"sug_btn_{idx}", use_container_width=True):
        process_ai(sug)
        st.rerun()

# --- 7. NHẬP LIỆU ---
st.write("<br><br><br><br>", unsafe_allow_html=True)

if st.session_state.voice_draft and not hands_free:
    with st.container():
        st.info("🎙️ Chỉnh sửa giọng nói:")
        txt = st.text_area("", value=st.session_state.voice_draft, height=80)
        ca, cb = st.columns(2)
        if ca.button("🚀 GỬI", use_container_width=True):
            st.session_state.voice_draft = ""; process_ai(txt); st.rerun()
        if cb.button("🗑️ HỦY", use_container_width=True):
            st.session_state.voice_draft = ""; st.rerun()
else:
    c_m, c_i = st.columns([1, 6])
    with c_m:
        audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v10')
    if audio:
        with st.spinner(""):
            transcript = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']))
            if hands_free: process_ai(transcript.text); st.rerun()
            else: st.session_state.voice_draft = transcript.text; st.rerun()

    inp = st.chat_input("Hỏi tôi bất cứ điều gì...")
    if inp:
        process_ai(inp); st.rerun()
