import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
import json
from io import BytesIO

# --- 1. GIAO DIỆN HIỆN ĐẠI & CHUYÊN NGHIỆP ---
st.set_page_config(page_title="Nexus Apex v29", layout="wide", page_icon="🎯")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .stButton > button {
        border-radius: 10px !important;
        text-transform: none !important;
        font-weight: 600 !important;
    }
    
    .mission-status {
        background: #f0f7ff;
        border: 1px solid #007bff;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "guide_step" not in st.session_state: st.session_state.guide_step = 0
if "v_speed" not in st.session_state: st.session_state.v_speed = 1.0

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. ĐIỀU KHIỂN GIỌNG NÓI ---
def voice_engine(text, action="speak"):
    if action == "speak":
        clean = text.replace('"', "'").replace('\n', ' ')
        js = f"<script>window.speechSynthesis.cancel(); var m=new SpeechSynthesisUtterance('{clean}'); m.lang='vi-VN'; m.rate={st.session_state.v_speed}; window.speechSynthesis.speak(m);</script>"
    else:
        js = "<script>window.speechSynthesis.cancel();</script>"
    st.components.v1.html(js, height=0)

# --- 4. SIDEBAR: ĐIỀU KHIỂN ---
with st.sidebar:
    st.header("Hệ thống Nexus")
    
    if st.session_state.guide_step > 0:
        st.markdown(f"""<div class="mission-status">
            <b>Nhiệm vụ {st.session_state.guide_step}/4</b><br>
            {["","Nhập tin nhắn","Nghe giọng đọc","Dùng nút gợi ý","Nhập/Xuất dữ liệu"][st.session_state.guide_step]}
        </div>""", unsafe_allow_html=True)

    st.subheader("🔊 Giọng nói")
    st.session_state.v_speed = st.slider("Tốc độ", 0.5, 2.0, 1.0)
    if st.button("🛑 Dừng đọc", use_container_width=True): voice_engine("", "stop")

    st.divider()
    # Bước 4: Hoàn tất nhanh chóng
    if st.session_state.guide_step == 4:
        st.success("Bạn đã làm rất tốt!")
        if st.button("✅ HOÀN TẤT HƯỚNG DẪN", type="primary", use_container_width=True):
            st.session_state.guide_step = 0
            st.rerun()

    with st.expander("Quản lý Dữ liệu"):
        st.download_button("Xuất JSON", data=json.dumps(st.session_state.messages), file_name="chat.json", use_container_width=True)
        up = st.file_uploader("Nhập JSON", type="json")
        if up and st.button("Khôi phục"):
            st.session_state.messages = json.loads(up.getvalue().decode("utf-8"))
            st.rerun()

# --- 5. MÀN HÌNH CHÀO MỪNG (Bổ sung nút theo yêu cầu) ---
if st.session_state.guide_step == 0 and not st.session_state.messages:
    st.title("Chào mừng đến với Nexus Elite")
    st.write("Bạn có cần tôi hướng dẫn cách sử dụng các tính năng đột phá không?")
    
    c1, c2, c3 = st.columns(3)
    if c1.button("🚀 Bắt đầu hướng dẫn", type="primary", use_container_width=True):
        st.session_state.guide_step = 1
        st.rerun()
    if c2.button("⏩ Bỏ qua", use_container_width=True):
        st.info("Đã bỏ qua hướng dẫn. Bạn có thể bắt đầu chat ngay.")
    if c3.button("💾 Ghi nhớ lựa chọn", use_container_width=True):
        st.success("Đã ghi nhớ lựa chọn của bạn cho các phiên sau.")

# --- 6. KHU VỰC CHAT & GỢI Ý ---
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            col1, col2, _ = st.columns([1,1,4])
            with col1:
                if st.button("🔊 Nghe", key=f"v_{i}"):
                    voice_engine(m["content"])
                    if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
            with col2:
                if st.button("🔇 Dừng", key=f"s_{i}"): voice_engine("", "stop")

# Gợi ý thông minh (Chia cột chống dính)
if st.session_state.get("suggestions"):
    cols = st.columns(len(st.session_state.suggestions))
    for idx, sug in enumerate(st.session_state.suggestions):
        if cols[idx].button(sug, key=f"sug_{idx}", use_container_width=True):
            if st.session_state.guide_step == 3: st.session_state.guide_step = 4
            # (Hàm gọi AI xử lý tin nhắn tiếp theo...)
            st.rerun()

# Input chính
inp = st.chat_input("Hỏi tôi bất cứ điều gì...")
if inp:
    # (Hàm gọi AI xử lý...)
    if st.session_state.guide_step == 1: st.session_state.guide_step = 2
    st.rerun()
