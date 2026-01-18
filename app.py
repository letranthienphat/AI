import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64
from langdetect import detect
import json

# --- 1. GIAO DIỆN HIỆN ĐẠI (KHÔNG DÍNH CHỮ) ---
st.set_page_config(page_title="Nexus Sovereign v25", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Lexend', sans-serif; background-color: #f4f7f9; }

    /* Thẻ gợi ý tách biệt, chuyên nghiệp */
    .sug-card {
        background: white;
        border: 1px solid #e0e6ed;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        margin: 5px;
        transition: 0.3s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Mũi tên chỉ dẫn động */
    .arrow-pointer {
        color: #ff4b4b;
        font-size: 20px;
        font-weight: bold;
        text-align: center;
        animation: slide 0.6s infinite alternate;
    }
    @keyframes slide { from { transform: translateX(0); } to { transform: translateX(10px); } }

    /* Làm nổi bật khu vực quan trọng */
    .highlight-zone {
        border: 2px dashed #ff4b4b !important;
        background: rgba(255, 75, 75, 0.05) !important;
        padding: 15px;
        border-radius: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC HỆ THỐNG ---
for key in ['messages', 'suggestions', 'guide_step', 'onboarding_done']:
    if key not in st.session_state:
        st.session_state[key] = {'messages': [], 'suggestions': [], 'guide_step': 0, 'onboarding_done': False}[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

def process_ai(user_input):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("assistant"):
        p = st.empty(); full = ""
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages], stream=True)
        for chunk in res:
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                p.markdown(full + "▌")
        p.markdown(full)
        st.session_state.messages.append({"role": "assistant", "content": full})
        
        # Gợi ý thật, tách bạch
        try:
            s_res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Gợi ý 3 câu hỏi tiếng Việt ngắn từ nội dung này. Chỉ trả về 3 câu, cách nhau dấu phẩy: {full[:100]}"}])
            st.session_state.suggestions = [s.strip() for s in s_res.choices[0].message.content.split(',') if len(s) > 2][:3]
        except: pass
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.rerun()

# --- 3. SIDEBAR: NHẬP DỮ LIỆU & HƯỚNG DẪN ---
with st.sidebar:
    st.title("🛡️ Trung tâm Nexus")
    
    if st.session_state.guide_step > 0:
        st.info(f"📍 Nhiệm vụ {st.session_state.guide_step}/4")
        st.write(["","Nhập tin nhắn bên dưới","Nhấn nút Nghe","Thử chọn gợi ý","Dùng tính năng Nhập File"][st.session_state.guide_step])
        if st.button("Bỏ qua hướng dẫn", use_container_width=True):
            st.session_state.guide_step = 0; st.session_state.onboarding_done = True; st.rerun()

    st.divider()
    st.subheader("📂 QUẢN LÝ FILE")
    
    # Spotlight Bước 4: Nhập dữ liệu
    if st.session_state.guide_step == 4:
        st.markdown('<div class="arrow-pointer">⬇️ NHẬP FILE TẠI ĐÂY ⬇️</div>', unsafe_allow_html=True)
    
    with st.container(border=(st.session_state.guide_step == 4)):
        # Xuất dữ liệu
        chat_data = json.dumps(st.session_state.messages, ensure_ascii=False)
        st.download_button("📤 Tải lịch sử chat (.json)", data=chat_data, file_name="history.json", use_container_width=True)
        
        # Nhập dữ liệu (Tính năng bạn yêu cầu)
        st.write("---")
        uploaded_file = st.file_uploader("📥 Nhập dữ liệu cũ", type="json", help="Chọn file .json bạn đã tải về trước đó")
        if uploaded_file:
            if st.button("🔄 KHÔI PHỤC NGAY", type="primary", use_container_width=True):
                st.session_state.messages = json.loads(uploaded_file.getvalue().decode("utf-8"))
                st.session_state.guide_step = 0; st.session_state.onboarding_done = True
                st.rerun()

# --- 4. GIAO DIỆN CHAT ---
st.title("Nexus Sovereign Elite 🛡️")

if st.session_state.guide_step == 0 and not st.session_state.onboarding_done:
    if st.button("🚀 BẮT ĐẦU HƯỚNG DẪN CHI TIẾT", type="primary"):
        st.session_state.guide_step = 1; st.rerun()

# Vùng hiển thị tin nhắn
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            col1, col2, _ = st.columns([1.2, 1, 4])
            with col1:
                # Bước 2: Nghe
                is_focus = "border: 2px solid red;" if st.session_state.guide_step == 2 else ""
                if st.button(f"🔊 Nghe lại", key=f"v_{i}", help="Nghe AI đọc"):
                    if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
            with col2:
                if st.button(f"📱 QR", key=f"q_{i}"):
                    qr = qrcode.make(m["content"][:200]); buf = BytesIO(); qr.save(buf, format="PNG"); st.image(buf, width=150)

# --- 5. KHU VỰC GỢI Ý & INPUT (KHÔNG DÍNH NHAU) ---
st.write("<br>", unsafe_allow_html=True) # Tạo khoảng cách

# Bước 3: Gợi ý
if st.session_state.suggestions:
    st.markdown("##### 💡 Gợi ý câu hỏi tiếp theo:")
    # Sử dụng columns để dàn hàng ngang chuyên nghiệp, không dính chữ
    cols = st.columns(len(st.session_state.suggestions))
    for idx, sug in enumerate(st.session_state.suggestions):
        with cols[idx]:
            if st.button(sug, key=f"s_{idx}", use_container_width=True):
                if st.session_state.guide_step == 3: st.session_state.guide_step = 4
                process_ai(sug); st.rerun()

# Bước 1: Nhập liệu
st.write("<br><br><br><br>", unsafe_allow_html=True)
with st.container():
    # Ghim input xuống đáy và tạo khoảng cách với phần trên
    c_mic, c_input = st.columns([1, 8])
    with c_mic:
        audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v25')
        if audio:
            transcript = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']))
            process_ai(transcript.text); st.rerun()
    with c_input:
        # Làm nổi bật ô chat ở bước 1
        if st.session_state.guide_step == 1: st.markdown('<div class="arrow-pointer">⬆️ GÕ TIN NHẮN VÀO ĐÂY ⬆️</div>', unsafe_allow_html=True)
        inp = st.chat_input("Hỏi điều gì đó...")
        if inp: process_ai(inp); st.rerun()
