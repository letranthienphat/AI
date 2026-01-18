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

# --- 1. CẤU HÌNH UI SPOTLIGHT ---
st.set_page_config(page_title="Nexus v16 Spotlight", layout="wide", page_icon="🔦")

st.markdown("""
    <style>
    /* Hiệu ứng làm nổi bật (Spotlight) */
    .spotlight {
        border: 3px solid #ff4b4b !important;
        box-shadow: 0 0 20px #ff4b4b !important;
        background-color: #fffde7 !important;
        transition: 0.5s;
    }
    .dimmed { opacity: 0.3; filter: blur(2px); pointer-events: none; }
    
    /* Giao diện chung */
    .stApp { background-color: #ffffff; }
    div[data-testid="stChatMessage"] { border-radius: 15px; border: 1px solid #f0f0f0; }
    .stButton > button { border-radius: 20px !important; font-weight: 600 !important; }
    
    /* Input dính đáy */
    .stChatInputContainer { position: fixed; bottom: 0; background: white; z-index: 1000; padding: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM TRỢ NĂNG ---
def speak_js(text, speed, lang):
    clean = text.replace('"', "'").replace('\n', ' ')
    return f"<script>window.speechSynthesis.cancel(); var m=new SpeechSynthesisUtterance('{clean}'); m.lang='{lang}'; m.rate={speed}; window.speechSynthesis.speak(m);</script>"

def get_lang_code(text):
    try:
        l = detect(text)
        mapping = {"vi":"vi-VN", "en":"en-US", "ja":"ja-JP", "ko":"ko-KR"}
        return mapping.get(l, "vi-VN")
    except: return "vi-VN"

# --- 3. KHỞI TẠO STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "suggestions" not in st.session_state: st.session_state.suggestions = ["Chào bạn", "HD chi tiết", "Kể chuyện", "Dịch thuật"]
if "guide_step" not in st.session_state: st.session_state.guide_step = 0 # 0: Chưa bắt đầu, 1-4: Các bước HD
if "onboarding_done" not in st.session_state: st.session_state.onboarding_done = False

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 4. HÀM XỬ LÝ DỮ LIỆU ---
def save_chat():
    data = json.dumps(st.session_state.messages, ensure_ascii=False)
    return data

def load_chat(json_str):
    try:
        st.session_state.messages = json.loads(json_str)
        st.success("Đã khôi phục dữ liệu!")
    except:
        st.error("File không hợp lệ!")

# --- 5. SIDEBAR (KHÔI PHỤC FULL TÍNH NĂNG) ---
with st.sidebar:
    st.title("🔦 Nexus Terminal")
    
    # Spotlight Bước 4: Sidebar & Backup
    sidebar_class = "spotlight" if st.session_state.guide_step == 4 else ""
    st.markdown(f'<div class="{sidebar_class}">', unsafe_allow_html=True)
    
    if st.button("📖 Xem lại hướng dẫn", use_container_width=True):
        st.session_state.guide_step = 1
        st.rerun()

    st.divider()
    st.subheader("💾 Quản lý dữ liệu")
    chat_json = save_chat()
    st.download_button("📤 Xuất file lưu trữ (JSON)", data=chat_json, file_name="nexus_backup.json", mime="application/json", use_container_width=True)
    
    uploaded_file = st.file_uploader("📥 Nhập file lưu trữ", type="json")
    if uploaded_file:
        if st.button("🔄 Khôi phục ngay"):
            load_chat(uploaded_file.getvalue().decode("utf-8"))
            st.rerun()

    if st.button("🗑️ Xóa hết hội thoại", use_container_width=True):
        st.session_state.messages = []; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. HỆ THỐNG HƯỚNG DẪN CHI TIẾT (SPOTLIGHT) ---
if st.session_state.guide_step > 0 and st.session_state.guide_step <= 4:
    with st.container():
        if st.session_state.guide_step == 1:
            st.info("🎯 **BƯỚC 1: NHẬP LIỆU** - Dùng Mic 🎤 để nói hoặc Chat Input ở đáy để nhập tin nhắn.")
        elif st.session_state.guide_step == 2:
            st.info("🎯 **BƯỚC 2: PHẢN HỒI** - AI sẽ trả lời và tự động đọc bằng ngôn ngữ tương ứng.")
        elif st.session_state.guide_step == 3:
            st.info("🎯 **BƯỚC 3: TIỆN ÍCH** - Dưới mỗi câu trả lời có nút 🔊 (Nghe lại), 📥 (Tải Mp3) và 📱 (QR Code).")
        elif st.session_state.guide_step == 4:
            st.info("🎯 **BƯỚC 4: LƯU TRỮ** - Sidebar bên trái giúp bạn xuất/nhập dữ liệu để không bị mất chat.")
        
        if st.button("Tiếp theo ➡️", use_container_width=True):
            st.session_state.guide_step += 1
            if st.session_state.guide_step > 4:
                st.session_state.onboarding_done = True
            st.rerun()

# --- 7. GIAO DIỆN CHÍNH ---
st.title("AI Nexus v16: Spotlight 🔦")

# Kiểm tra nếu chưa từng Onboarding
if not st.session_state.onboarding_done and st.session_state.guide_step == 0:
    st.warning("👋 Chào mừng! Bạn có cần tôi hướng dẫn chi tiết cách dùng không?")
    col_a, col_b = st.columns(2)
    if col_a.button("Cần chứ! (Bắt đầu Tour)", use_container_width=True):
        st.session_state.guide_step = 1
        st.rerun()
    if col_b.button("Không, tôi biết rồi", use_container_width=True):
        st.session_state.onboarding_done = True
        st.rerun()

# HIỂN THỊ CHAT (Áp dụng hiệu ứng Dimmed nếu đang HD bước khác)
chat_class = "dimmed" if st.session_state.guide_step in [1, 4] else ""
st.markdown(f'<div class="{chat_class}">', unsafe_allow_html=True)

for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            # Spotlight Bước 3: Tiện ích
            btn_class = "spotlight" if st.session_state.guide_step == 3 else ""
            st.markdown(f'<div class="{btn_class}" style="padding:10px; border-radius:10px">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🔊 Nghe", key=f"v_{i}"):
                    st.components.v1.html(speak_js(m["content"], 1.1, get_lang_code(m["content"])), height=0)
            with c2:
                try:
                    tts = gTTS(text=m["content"][:200], lang=get_lang_code(m["content"]).split('-')[0])
                    b = BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
                    st.markdown(f'<a href="data:audio/mp3;base64,{b64}" download="voice.mp3"><button style="width:100%; border-radius:15px; border:1px solid #ddd; padding:5px;">📥 Tải</button></a>', unsafe_allow_html=True)
                except: pass
            with c3:
                if st.button("📱 QR", key=f"q_{i}"):
                    qr = qrcode.make(m["content"][:500]); buf = BytesIO(); qr.save(buf, format="PNG"); st.image(buf, width=100)
            st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# NÚT GỢI Ý (Spotlight Bước 2)
st.write("---")
sug_class = "spotlight" if st.session_state.guide_step == 2 else ""
st.markdown(f'<div class="{sug_class}">', unsafe_allow_html=True)
cols = st.columns(len(st.session_state.suggestions))
for idx, sug in enumerate(st.session_state.suggestions):
    if cols[idx].button(sug.strip(), key=f"s_{idx}", use_container_width=True):
        # Hàm xử lý chat (process_ai bỏ qua để tối giản code hiển thị)
        pass 
st.markdown('</div>', unsafe_allow_html=True)

# INPUT AREA (Spotlight Bước 1)
st.write("<br><br><br><br>", unsafe_allow_html=True)
input_class = "spotlight" if st.session_state.guide_step == 1 else ""
st.markdown(f'<div class="{input_class}" style="position:fixed; bottom:0; width:100%; background:white; padding:10px;">', unsafe_allow_html=True)
# (Phần Mic và Chat Input đặt ở đây)
st.chat_input("Nhập tin nhắn để thử nghiệm...")
st.markdown('</div>', unsafe_allow_html=True)
