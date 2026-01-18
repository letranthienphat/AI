import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64
from langdetect import detect
import re
import json

# --- 1. CẤU HÌNH UI & CSS ---
st.set_page_config(page_title="Nexus v18 Fixed", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .spotlight-active { border: 4px solid #007bff !important; box-shadow: 0 0 30px rgba(0,123,255,0.5); background: #f0f7ff !important; z-index: 999; }
    .dimmed { opacity: 0.2; filter: blur(2px); pointer-events: none; transition: 0.5s; }
    .floating-guide {
        position: fixed; top: 15%; left: 50%; transform: translateX(-50%);
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3); z-index: 1000;
        width: 90%; max-width: 450px; border-top: 5px solid #007bff;
    }
    .stApp { background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM HỖ TRỢ ---
def speak_js(text, speed, lang):
    clean = text.replace('"', "'").replace('\n', ' ')
    return f"<script>window.speechSynthesis.cancel(); var m=new SpeechSynthesisUtterance('{clean}'); m.lang='{lang}'; m.rate={speed}; window.speechSynthesis.speak(m);</script>"

def get_lang_code(text):
    try:
        l = detect(text)
        mapping = {"vi":"vi-VN", "en":"en-US", "ja":"ja-JP", "ko":"ko-KR"}
        return mapping.get(l, "vi-VN")
    except: return "vi-VN"

# --- 3. KHỞI TẠO STATE (QUAN TRỌNG) ---
if "messages" not in st.session_state: st.session_state.messages = []
if "suggestions" not in st.session_state: st.session_state.suggestions = ["Chào bạn", "Tính năng mới", "Kể chuyện"]
if "guide_step" not in st.session_state: st.session_state.guide_step = 0 
if "remember_choice" not in st.session_state: st.session_state.remember_choice = False
if "onboarding_done" not in st.session_state: st.session_state.onboarding_done = False

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 4. HÀM XỬ LÝ AI ---
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
        if st.session_state.get("auto_read", True):
            st.components.v1.html(speak_js(full, st.session_state.v_speed, lang), height=0)
        try:
            s_res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Tạo 4 câu hỏi tiếp nối ngắn cho: '{full[:100]}', ngăn cách bằng dấu phẩy."}])
            st.session_state.suggestions = [s.strip() for s in s_res.choices[0].message.content.split(',') if s.strip()][:4]
        except: pass

# --- 5. SIDEBAR: FULL OPTION ---
with st.sidebar:
    st.title("🛡️ Nexus Terminal")
    if st.button("📖 Chạy lại hướng dẫn mẫu", use_container_width=True):
        st.session_state.onboarding_done = False
        st.session_state.guide_step = 1
        st.rerun()
    
    st.divider()
    st.session_state.v_speed = st.slider("Tốc độ đọc", 0.5, 2.0, 1.1)
    st.session_state.auto_read = st.toggle("Tự động đọc", value=True)
    
    st.divider()
    st.subheader("💾 Dữ liệu & Lưu trữ")
    chat_data = json.dumps(st.session_state.messages, ensure_ascii=False)
    st.download_button("📤 Xuất file lưu trữ (.json)", data=chat_data, file_name="nexus_chat.json", use_container_width=True)
    
    up = st.file_uploader("📥 Nhập file cũ", type="json")
    if up:
        if st.button("🔄 Khôi phục dữ liệu"):
            st.session_state.messages = json.loads(up.getvalue().decode("utf-8"))
            st.rerun()

    if st.button("🗑️ Xóa sạch hội thoại", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# --- 6. GIAO DIỆN CHÍNH & TOUR HƯỚNG DẪN ---
st.title("AI Nexus v18 🛡️")

# Màn hình hỏi Onboarding (chỉ hiện 1 lần nếu không chọn remember)
if not st.session_state.onboarding_done and st.session_state.guide_step == 0:
    with st.container():
        st.info("👋 Chào bạn! Bạn muốn xem hướng dẫn tương tác mẫu hay bắt đầu ngay?")
        rem = st.checkbox("Ghi nhớ lựa chọn này (Lưu vào bộ nhớ phiên)")
        c1, c2 = st.columns(2)
        if c1.button("✨ Xem hướng dẫn mẫu"):
            st.session_state.onboarding_done = rem
            st.session_state.messages = [{"role":"user","content":"Dùng thử mẫu"},{"role":"assistant","content":"Đây là tin nhắn mẫu. Hãy nhấn các nút 🔊 Nghe, 📥 Tải bên dưới để thử!"}]
            st.session_state.guide_step = 1
            st.rerun()
        if c2.button("🚀 Bắt đầu ngay"):
            st.session_state.onboarding_done = rem
            st.session_state.guide_step = 0
            st.rerun()

# Bảng hướng dẫn nổi (Floating Guide)
if 1 <= st.session_state.guide_step <= 4:
    guides = {1: "🎤 **BƯỚC 1:** Dùng Mic hoặc Chat Input bên dưới để nhập liệu.",
              2: "🔊 **BƯỚC 2:** Thử nhấn nút Nghe/Tải ở tin nhắn mẫu này!",
              3: "💡 **BƯỚC 3:** Các nút gợi ý giúp bạn hỏi nhanh hơn.",
              4: "⚙️ **BƯỚC 4:** Cài đặt tốc độ và Lưu trữ ở Sidebar."}
    st.markdown(f'<div class="floating-guide"><h4>🎯 Hướng dẫn {st.session_state.guide_step}/4</h4><p>{guides[st.session_state.guide_step]}</p></div>', unsafe_allow_html=True)
    if st.button(f"Xong bước {st.session_state.guide_step} ➡️", use_container_width=True):
        st.session_state.guide_step = (st.session_state.guide_step + 1) if st.session_state.guide_step < 4 else 0
        st.rerun()

# --- HIỂN THỊ CHAT (FIXED KEYS) ---
for i, m in enumerate(st.session_state.messages):
    # Highlight nếu đang ở bước 2
    step_style = "spotlight-active" if (st.session_state.guide_step == 2 and m["role"] == "assistant") else ("dimmed" if st.session_state.guide_step not in [0,2] else "")
    st.markdown(f'<div class="{step_style}">', unsafe_allow_html=True)
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            c1, c2, c3 = st.columns(3)
            with c1: # Key duy nhất: v_ + index
                if st.button("🔊 Nghe", key=f"v_btn_{i}"):
                    st.components.v1.html(speak_js(m["content"], st.session_state.v_speed, get_lang_code(m["content"])), height=0)
            with c2: # Key duy nhất: d_ + index
                tts = gTTS(text=m["content"][:100], lang="vi")
                b = BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
                st.markdown(f'<a href="data:audio/mp3;base64,{b64}" download="voice.mp3"><button style="width:100%; border-radius:10px; border:1px solid #ddd; padding:5px; cursor:pointer;" id="d_btn_{i}">📥 Tải</button></a>', unsafe_allow_html=True)
            with c3: # Key duy nhất: q_ + index
                if st.button("📱 QR", key=f"q_btn_{i}"):
                    qr = qrcode.make(m["content"][:300]); buf = BytesIO(); qr.save(buf, format="PNG"); st.image(buf, width=100)
    st.markdown('</div>', unsafe_allow_html=True)

# --- NÚT GỢI Ý (FIXED KEYS) ---
st.write("---")
sug_style = "spotlight-active" if st.session_state.guide_step == 3 else ("dimmed" if st.session_state.guide_step not in [0,3] else "")
st.markdown(f'<div class="{sug_style}">', unsafe_allow_html=True)
if st.session_state.suggestions:
    cols = st.columns(len(st.session_state.suggestions))
    for idx, sug in enumerate(st.session_state.suggestions):
        # Key cực kỳ an toàn: s_ + hash nội dung + index
        if cols[idx].button(sug.strip(), key=f"sug_atomic_{idx}_{hash(sug)}", use_container_width=True):
            process_ai(sug); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- INPUT AREA ---
st.write("<br><br><br><br>", unsafe_allow_html=True)
in_style = "spotlight-active" if st.session_state.guide_step == 1 else ("dimmed" if st.session_state.guide_step not in [0,1] else "")
st.markdown(f'<div class="{in_style}" style="position:fixed; bottom:0; width:100%; background:white; padding:10px; left:0;">', unsafe_allow_html=True)
c_m, c_i = st.columns([1, 6])
with c_m: audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v18')
if audio:
    transcript = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']))
    process_ai(transcript.text); st.rerun()
inp = st.chat_input("Nhập tin nhắn tại đây...")
if inp: process_ai(inp); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
