import streamlit as st
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import mic_recorder
import qrcode
import base64
from langdetect import detect
import json

# --- 1. GIAO DIỆN "ULTIMATE" (CSS CHỐNG DÍNH & VISUAL CAO CẤP) ---
st.set_page_config(page_title="Nexus Ultimate v26", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Be Vietnam Pro', sans-serif; }

    /* MISSION CARD: Bảng nhiệm vụ đẹp, nổi bật */
    .mission-card {
        background: linear-gradient(135deg, #FF6B6B, #FF8E53);
        border-radius: 16px;
        padding: 20px;
        color: white;
        box-shadow: 0 10px 25px rgba(255, 107, 107, 0.4);
        margin-bottom: 20px;
        border: 2px solid white;
    }
    .mission-header { font-weight: 700; text-transform: uppercase; letter-spacing: 1px; font-size: 0.85rem; opacity: 0.9; }
    .mission-title { font-size: 1.3rem; font-weight: 800; margin: 8px 0; }

    /* CHỐNG DÍNH NÚT GỢI Ý (QUAN TRỌNG) */
    .stButton button {
        width: 100%;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: transform 0.2s;
    }
    .stButton button:active { transform: scale(0.98); }

    /* HIGHLIGHT POINTER: Chỉ dẫn vị trí */
    .focus-arrow {
        color: #FF4B4B; font-weight: bold; font-size: 1.2rem;
        animation: float 1s infinite alternate; text-align: center;
    }
    @keyframes float { from { transform: translateY(0); } to { transform: translateY(-5px); } }
    
    /* Ẩn bớt phần thừa để giao diện sạch */
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO DỮ LIỆU ---
if "messages" not in st.session_state: st.session_state.messages = []
if "suggestions" not in st.session_state: st.session_state.suggestions = []
if "guide_step" not in st.session_state: st.session_state.guide_step = 0 
if "onboarding_done" not in st.session_state: st.session_state.onboarding_done = False
if "v_speed" not in st.session_state: st.session_state.v_speed = 1.0 # Mặc định tốc độ chuẩn

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HÀM XỬ LÝ CHÍNH ---
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
        
        # Tạo gợi ý thật
        try:
            s_res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Gợi ý 3 câu hỏi tiếng Việt ngắn (dưới 6 từ) tiếp nối: {full[:100]}"}])
            raw_sug = s_res.choices[0].message.content
            # Tách và lọc sạch gợi ý
            st.session_state.suggestions = [s.strip().replace('- ','').replace('1. ','') for s in raw_sug.split('\n') if len(s) > 2][:3]
        except: pass
        
        # Tự động nhảy bước 1 -> 2
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.rerun()

# --- 4. SIDEBAR "MISSION CONTROL" (BẤT TỬ) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=60)
    st.title("Nexus Control")
    
    # --- KHU VỰC HƯỚNG DẪN (Luôn hiển thị nếu chưa xong) ---
    if st.session_state.guide_step > 0:
        step_titles = {
            1: "KHỞI ĐỘNG", 
            2: "TƯƠNG TÁC", 
            3: "GỢI Ý THÔNG MINH", 
            4: "QUẢN LÝ DỮ LIỆU"
        }
        step_descs = {
            1: "Hãy gõ hoặc nói 'Xin chào' vào ô chat bên dưới.",
            2: "Nhấn nút '🔊 NGHE' dưới tin nhắn của AI.",
            3: "Chọn một trong các nút Gợi ý màu trắng.",
            4: "Sử dụng tính năng Nhập/Xuất File bên dưới."
        }
        
        st.markdown(f"""
        <div class="mission-card">
            <div class="mission-header">NHIỆM VỤ {st.session_state.guide_step}/4</div>
            <div class="mission-title">{step_titles.get(st.session_state.guide_step)}</div>
            <div>{step_descs.get(st.session_state.guide_step)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Nút cứu hộ: Tự qua màn nếu bị kẹt
        c1, c2 = st.columns(2)
        if c1.button("✅ Xong bước này", help="Nhấn nếu bạn đã làm nhưng máy chưa nhận"):
            if st.session_state.guide_step < 4: st.session_state.guide_step += 1
            else: st.session_state.guide_step = 0; st.session_state.onboarding_done = True
            st.rerun()
        if c2.button("⏩ Bỏ qua hết"):
            st.session_state.guide_step = 0; st.session_state.onboarding_done = True; st.rerun()

    st.divider()
    
    # --- CÀI ĐẶT (ĐÃ KHÔI PHỤC TỐC ĐỘ) ---
    st.subheader("⚙️ Cài đặt")
    st.session_state.v_speed = st.slider("Tốc độ giọng đọc", 0.5, 2.0, 1.0, help="Chỉnh tốc độ nói của AI")
    
    st.subheader("📂 Dữ liệu")
    # Highlight Bước 4
    if st.session_state.guide_step == 4: st.markdown('<div class="focus-arrow">⬇️ THAO TÁC TẠI ĐÂY ⬇️</div>', unsafe_allow_html=True)
    
    with st.expander("Nhập / Xuất File JSON", expanded=(st.session_state.guide_step==4)):
        st.download_button("📤 Xuất dữ liệu", data=json.dumps(st.session_state.messages), file_name="nexus_chat.json", use_container_width=True)
        uploaded = st.file_uploader("📥 Nhập dữ liệu cũ", type="json")
        if uploaded and st.button("🔄 Khôi phục ngay"):
            st.session_state.messages = json.loads(uploaded.getvalue().decode("utf-8"))
            if st.session_state.guide_step == 4: 
                st.session_state.guide_step = 0; st.session_state.onboarding_done = True
            st.rerun()

    if st.button("🗑️ Xóa sạch hội thoại", use_container_width=True):
        st.session_state.messages = []; st.session_state.suggestions = []; st.rerun()

# --- 5. GIAO DIỆN CHÍNH ---
st.title("Nexus Ultimate v26 💎")

# Màn hình chào mừng (Zero State)
if st.session_state.guide_step == 0 and not st.session_state.onboarding_done:
    col_cen, _ = st.columns([2,1])
    with col_cen:
        st.info("👋 Chào mừng! Bạn có muốn tham gia hướng dẫn nhanh không?")
        if st.button("🚀 BẮT ĐẦU HƯỚNG DẪN", type="primary"):
            st.session_state.guide_step = 1; st.rerun()

# --- KHU VỰC CHAT ---
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            # Action Bar
            c1, c2, c3 = st.columns([1.5, 1.5, 5])
            with c1:
                # Highlight Bước 2
                if st.session_state.guide_step == 2: st.markdown('<div class="focus-arrow">👆 Bấm đây</div>', unsafe_allow_html=True)
                if st.button(f"🔊 NGHE", key=f"voice_{i}"):
                    # Logic Javascript đọc văn bản
                    clean_text = m["content"].replace('"', "'").replace('\n', ' ')
                    st.components.v1.html(f"<script>window.speechSynthesis.cancel(); var u=new SpeechSynthesisUtterance('{clean_text}'); u.lang='vi-VN'; u.rate={st.session_state.v_speed}; window.speechSynthesis.speak(u);</script>", height=0)
                    if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
            with c2:
                if st.button("📱 QR", key=f"qr_{i}"):
                    qr = qrcode.make(m["content"][:200]); buf = BytesIO(); qr.save(buf, format="PNG"); st.image(buf, width=150)

# --- KHU VỰC GỢI Ý (CHỐNG DÍNH TUYỆT ĐỐI) ---
st.write("<br>", unsafe_allow_html=True)
if st.session_state.suggestions:
    st.caption("💡 Gợi ý tiếp theo:")
    if st.session_state.guide_step == 3: st.markdown('<div class="focus-arrow">👇 Chọn 1 cái nhé</div>', unsafe_allow_html=True)
    
    # Dùng columns để tách nút -> Không bao giờ dính
    cols = st.columns(len(st.session_state.suggestions))
    for idx, sug in enumerate(st.session_state.suggestions):
        with cols[idx]:
            if st.button(sug, key=f"sug_{idx}", use_container_width=True):
                if st.session_state.guide_step == 3: st.session_state.guide_step = 4
                process_ai(sug); st.rerun()

# --- INPUT AREA ---
st.write("<br><br><br>", unsafe_allow_html=True)
if st.session_state.guide_step == 1: st.markdown('<div class="focus-arrow">👇 Bắt đầu tại đây</div>', unsafe_allow_html=True)

# Container dính đáy
with st.container():
    c_mic, c_input = st.columns([1, 8])
    with c_mic:
        audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_ult')
        if audio:
            transcript = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", audio['bytes']))
            process_ai(transcript.text); st.rerun()
    with c_input:
        inp = st.chat_input("Nhập tin nhắn...")
        if inp: process_ai(inp); st.rerun()
