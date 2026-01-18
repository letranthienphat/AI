import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64
from langdetect import detect
import json

# --- 1. GIAO DIỆN ELITE & CHỈ DẪN ---
st.set_page_config(page_title="Nexus Pro v24", layout="wide", page_icon="🎯")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Lexend', sans-serif; }

    /* Hiệu ứng chỉ tay/mũi tên */
    .pointer-hint {
        color: #FF4B4B;
        font-weight: bold;
        animation: bounce 0.5s infinite alternate;
        margin-bottom: 5px;
    }
    @keyframes bounce { from { transform: translateY(0); } to { transform: translateY(-5px); } }

    /* Vùng sáng tập trung */
    .focus-point { border: 3px solid #FF4B4B !important; box-shadow: 0 0 20px rgba(255, 75, 75, 0.5) !important; border-radius: 15px; }
    .dimmed { opacity: 0.15; filter: blur(4px); pointer-events: none; transition: 0.5s; }
    
    /* Sidebar Mission Control */
    .sidebar-task { background: #f0f2f6; padding: 15px; border-radius: 15px; border-left: 5px solid #FF4B4B; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO ---
for key in ['messages', 'suggestions', 'guide_step', 'onboarding_done', 'v_speed']:
    if key not in st.session_state:
        st.session_state[key] = {'messages': [], 'suggestions': [], 'guide_step': 0, 'onboarding_done': False, 'v_speed': 1.1}[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HÀM XỬ LÝ AI ---
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
        
        # Gợi ý nội dung thật
        try:
            s_res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Gợi ý 3 câu hỏi tiếng Việt ngắn từ: {full[:100]}"}])
            st.session_state.suggestions = [s.strip() for s in s_res.choices[0].message.content.split(',') if s.strip()][:3]
        except: pass

        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.rerun()

# --- 4. THANH ĐIỀU HƯỚNG BÊN TRÁI (SIDEBAR) ---
with st.sidebar:
    st.header("🛡️ ĐIỀU KHIỂN HỆ THỐNG")
    
    # Khu vực hướng dẫn (Chỉ hiện khi đang trong Tour)
    if st.session_state.guide_step > 0:
        st.markdown(f'<div class="sidebar-task"><b>Nhiệm vụ {st.session_state.guide_step}/4</b><br>{["","Gửi tin nhắn ở đáy màn hình","Bấm nút Loa ở tin nhắn AI","Chọn Gợi ý ở trên thanh nhập","Dùng tính năng Nhập dữ liệu bên dưới"][st.session_state.guide_step]}</div>', unsafe_allow_html=True)
        if st.button("Bỏ qua tất cả hướng dẫn ⏩", use_container_width=True):
            st.session_state.guide_step = 0; st.session_state.onboarding_done = True; st.rerun()

    st.divider()
    st.subheader("⚙️ Cài đặt giọng đọc")
    st.session_state.v_speed = st.slider("Tốc độ", 0.5, 2.0, 1.1)
    
    st.divider()
    st.subheader("📂 QUẢN LÝ DỮ LIỆU")
    
    # Spotlight Bước 4: Nhập/Xuất dữ liệu
    step4_style = "focus-point" if st.session_state.guide_step == 4 else ""
    st.markdown(f'<div class="{step4_style}" style="padding:10px;">', unsafe_allow_html=True)
    
    # 1. TÍNH NĂNG XUẤT (EXPORT)
    chat_json = json.dumps(st.session_state.messages, ensure_ascii=False)
    st.download_button("📤 TẢI DỮ LIỆU VỀ MÁY", data=chat_json, file_name="nexus_chat.json", use_container_width=True)
    
    # 2. TÍNH NĂNG NHẬP (IMPORT) - ĐÃ KHÔI PHỤC
    st.write("---")
    file_up = st.file_uploader("📥 KÉO FILE JSON VÀO ĐÂY", type="json")
    if file_up:
        if st.button("🔄 KHÔI PHỤC DỮ LIỆU NGAY", use_container_width=True, type="primary"):
            st.session_state.messages = json.loads(file_up.getvalue().decode("utf-8"))
            if st.session_state.guide_step == 4: st.session_state.guide_step = 0; st.session_state.onboarding_done = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. GIAO DIỆN CHÍNH ---
st.title("Nexus Elite v24 🎯")

# Màn hình chào mừng
if st.session_state.guide_step == 0 and not st.session_state.onboarding_done:
    st.info("Chào mừng bạn! Hãy chọn 'Bắt đầu' để tôi hướng dẫn chi tiết từng vị trí tính năng.")
    if st.button("BẮT ĐẦU HƯỚNG DẪN ✨", type="primary"):
        st.session_state.guide_step = 1; st.rerun()

# HIỂN THỊ CHAT
chat_area = "dimmed" if st.session_state.guide_step in [1, 3, 4] else ""
st.markdown(f'<div class="{chat_area}">', unsafe_allow_html=True)
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            # Chỉ dẫn Bước 2
            if st.session_state.guide_step == 2: st.markdown('<div class="pointer-hint">👇 Bấm vào đây để nghe!</div>', unsafe_allow_html=True)
            col1, col2, _ = st.columns([1,1,5])
            btn_style = "focus-point" if st.session_state.guide_step == 2 else ""
            with col1:
                if st.button("🔊 NGHE", key=f"v_{i}", help="Nghe AI đọc câu trả lời"):
                    st.session_state.guide_step = 3; st.rerun()
            with col2:
                if st.button("📱 QR", key=f"q_{i}"):
                    qr = qrcode.make(m["content"][:300]); buf = BytesIO(); qr.save(buf, format="PNG"); st.image(buf, width=120)
st.markdown('</div>', unsafe_allow_html=True)

# GỢI Ý THÔNG MINH (Bước 3)
st.write("---")
sug_area = "dimmed" if st.session_state.guide_step in [1, 2, 4] else ""
st.markdown(f'<div class="{sug_area}">', unsafe_allow_html=True)
if st.session_state.suggestions:
    if st.session_state.guide_step == 3: st.markdown('<div class="pointer-hint">👉 Chọn một câu để hỏi tiếp nhanh!</div>', unsafe_allow_html=True)
    cols = st.columns(len(st.session_state.suggestions))
    for idx, sug in enumerate(st.session_state.suggestions):
        btn_focus = "focus-point" if st.session_state.guide_step == 3 else ""
        if cols[idx].button(f"✨ {sug}", key=f"s_{idx}", use_container_width=True):
            st.session_state.guide_step = 4; process_ai(sug); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# INPUT CHÍNH (Bước 1)
st.write("<br><br><br><br>", unsafe_allow_html=True)
in_area = "dimmed" if st.session_state.guide_step in [2, 3, 4] else ""
st.markdown(f'<div class="{in_area}" style="position:fixed; bottom:0; width:100%; background:white; padding:15px; left:0; z-index:1000;">', unsafe_allow_html=True)
if st.session_state.guide_step == 1: st.markdown('<div class="pointer-hint" style="margin-left:80px;">👇 Nhập tin nhắn hoặc nhấn Mic ở đây để bắt đầu!</div>', unsafe_allow_html=True)
c_mic, c_input = st.columns([1, 6])
with c_mic: audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_pro')
if audio:
    transcript = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']))
    process_ai(transcript.text); st.rerun()
inp = st.chat_input("Hỏi Nexus bất cứ điều gì...")
if inp: process_ai(inp); st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
