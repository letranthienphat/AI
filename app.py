import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
import json
from io import BytesIO

# --- 1. GIAO DIỆN HIỆN ĐẠI & CHỐNG DÍNH ---
st.set_page_config(page_title="Nexus Apex v27", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Lexend', sans-serif; }

    /* Nút gợi ý chuyên nghiệp: Tự động xuống hàng, không dính nhau */
    .stButton > button {
        border-radius: 20px !important;
        font-weight: 500 !important;
        padding: 10px 20px !important;
        border: 1px solid #e0e0e0 !important;
        background: white !important;
        color: #333 !important;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        border-color: #FF4B4B !important;
        color: #FF4B4B !important;
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.1);
    }

    /* Bảng nhiệm vụ nổi bật */
    .mission-box {
        background: #1E1E1E;
        color: #00FFCC;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #00FFCC;
        margin-bottom: 20px;
    }
    
    /* Hiệu ứng chỉ dẫn */
    .pointer { color: #FF4B4B; font-weight: bold; animation: pulse 1s infinite; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE ---
for key in ['messages', 'suggestions', 'guide_step', 'v_speed', 'is_speaking']:
    if key not in st.session_state:
        defaults = {'messages': [], 'suggestions': [], 'guide_step': 0, 'v_speed': 1.0, 'is_speaking': False}
        st.session_state[key] = defaults[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HÀM ĐIỀU KHIỂN GIỌNG NÓI (JAVASCRIPT) ---
def voice_ctrl(text, action="speak"):
    if action == "speak":
        clean_text = text.replace('"', "'").replace('\n', ' ')
        js = f"""
        <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance("{clean_text}");
        msg.lang = 'vi-VN';
        msg.rate = {st.session_state.v_speed};
        window.speechSynthesis.speak(msg);
        </script>
        """
    else:
        js = "<script>window.speechSynthesis.cancel();</script>"
    st.components.v1.html(js, height=0)

# --- 4. XỬ LÝ AI ---
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
        
        # Gợi ý đột phá: Tách bạch rõ ràng
        try:
            s_res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Tạo 3 câu hỏi gợi ý ngắn gọn bằng tiếng Việt từ: {full[:50]}"}])
            st.session_state.suggestions = [s.strip() for s in s_res.choices[0].message.content.split('\n') if len(s) > 5][:3]
        except: pass

        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        voice_ctrl(full) # Tự động đọc
        st.rerun()

# --- 5. SIDEBAR: ĐIỀU KHIỂN TỐI THƯỢNG ---
with st.sidebar:
    st.title("Nexus Apex 🛡️")
    
    if st.session_state.guide_step > 0:
        st.markdown(f"""<div class="mission-box">
            <small>NHIỆM VỤ {st.session_state.guide_step}/4</small><br>
            <b>{["","Gửi lời chào","Thử Nghe & Dừng","Bấm Gợi ý","Quản lý File"][st.session_state.guide_step]}</b>
        </div>""", unsafe_allow_html=True)

    st.subheader("🔊 Điều khiển giọng nói")
    st.session_state.v_speed = st.slider("Tốc độ đọc", 0.5, 2.0, 1.0)
    if st.button("🛑 DỪNG ĐỌC NGAY", use_container_width=True, type="primary"):
        voice_ctrl("", "stop")
    
    st.divider()
    st.subheader("📂 Dữ liệu")
    with st.expander("Nhập/Xuất File JSON"):
        st.download_button("📤 Xuất JSON", data=json.dumps(st.session_state.messages), file_name="chat.json", use_container_width=True)
        up = st.file_uploader("📥 Nhập JSON", type="json")
        if up and st.button("🔄 Khôi phục"):
            st.session_state.messages = json.loads(up.getvalue().decode("utf-8"))
            st.rerun()

# --- 6. GIAO DIỆN CHÍNH ---
st.title("Hệ thống Trợ lý Nexus v27")

if st.session_state.guide_step == 0 and not st.session_state.messages:
    if st.button("✨ BẮT ĐẦU HƯỚNG DẪN"):
        st.session_state.guide_step = 1; st.rerun()

# HIỂN THỊ CHAT
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            c1, c2, c3, _ = st.columns([1, 1, 1, 4])
            with c1: 
                if st.button("🔊 Đọc", key=f"read_{i}"):
                    voice_ctrl(m["content"])
                    if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
            with c2:
                if st.button("📱 QR", key=f"qr_{i}"):
                    qr = qrcode.make(m["content"][:200]); buf = BytesIO(); qr.save(buf, format="PNG"); st.image(buf, width=150)
            with c3:
                # Nút dừng đọc ngay tại dòng chat
                if st.button("🔇 Dừng", key=f"stop_{i}"):
                    voice_ctrl("", "stop")

# GỢI Ý ĐỘT PHÁ (CHỐNG DÍNH NHAU)
if st.session_state.suggestions:
    st.write("---")
    st.caption("💡 Gợi ý tiếp theo:")
    # Chia cột để các nút không bao giờ dính nhau
    cols = st.columns(len(st.session_state.suggestions))
    for idx, sug in enumerate(st.session_state.suggestions):
        with cols[idx]:
            if st.button(sug, key=f"s_{idx}", use_container_width=True):
                if st.session_state.guide_step == 3: st.session_state.guide_step = 4
                process_ai(sug); st.rerun()

# INPUT CHÍNH
st.write("<br><br><br>", unsafe_allow_html=True)
with st.container():
    c1, c2 = st.columns([1, 8])
    with c1:
        aud = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v27')
        if aud:
            trans = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", aud['bytes']))
            process_ai(trans.text); st.rerun()
    with c2:
        if st.session_state.guide_step == 1: st.markdown('<p class="pointer">👇 Bắt đầu bằng cách nhập tin nhắn!</p>', unsafe_allow_html=True)
        inp = st.chat_input("Hỏi Nexus...")
        if inp: process_ai(inp); st.rerun()
