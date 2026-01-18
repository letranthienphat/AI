import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
import json
from io import BytesIO

# --- 1. GIAO DIỆN LUXURY & CHỐNG XUNG ĐỘT UI ---
st.set_page_config(page_title="Nexus Black Diamond", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0E1117; }

    /* Hướng dẫn kiểu Neon */
    .guide-highlight {
        background: rgba(0, 255, 194, 0.1);
        border: 2px solid #00FFC2;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 0 15px rgba(0, 255, 194, 0.3);
    }
    
    /* Nút gợi ý kiểu Thẻ (Card) - Chống dính tuyệt đối */
    .stButton > button {
        border-radius: 12px !important;
        background-color: #1A1C24 !important;
        color: #E0E0E0 !important;
        border: 1px solid #30363D !important;
        padding: 12px !important;
        transition: 0.3s;
    }
    .stButton > button:hover {
        border-color: #00FFC2 !important;
        color: #00FFC2 !important;
        transform: translateY(-2px);
    }

    /* Mũi tên chỉ dẫn động */
    .pointer-anim {
        color: #00FFC2;
        font-weight: bold;
        animation: blink 0.8s infinite;
        text-align: center;
        margin-bottom: 5px;
    }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO HỆ THỐNG ---
for key in ['messages', 'suggestions', 'guide_step', 'v_speed']:
    if key not in st.session_state:
        st.session_state[key] = {'messages': [], 'suggestions': [], 'guide_step': 0, 'v_speed': 1.0}[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. ĐIỀU KHIỂN GIỌNG NÓI ---
def voice_engine(text, action="speak"):
    if action == "speak":
        clean = text.replace('"', "'").replace('\n', ' ')
        js = f"""<script>window.speechSynthesis.cancel(); var m=new SpeechSynthesisUtterance("{clean}");
                 m.lang='vi-VN'; m.rate={st.session_state.v_speed}; window.speechSynthesis.speak(m);</script>"""
    else:
        js = "<script>window.speechSynthesis.cancel();</script>"
    st.components.v1.html(js, height=0)

# --- 4. XỬ LÝ AI ---
def chat_engine(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        p = st.empty(); full = ""
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages], stream=True)
        for chunk in res:
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                p.markdown(full + "▌")
        p.markdown(full)
        st.session_state.messages.append({"role": "assistant", "content": full})
        
        # Gợi ý nội dung (Tách riêng biệt)
        try:
            s_res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Gợi ý 3 câu hỏi tiếng Việt cực ngắn cho: {full[:50]}"}])
            st.session_state.suggestions = [s.strip() for s in s_res.choices[0].message.content.split('\n') if len(s) > 5][:3]
        except: pass
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.rerun()

# --- 5. SIDEBAR: MISSION CONTROL & DATA ---
with st.sidebar:
    st.title("💎 NEXUS ELITE")
    
    # Bảng hướng dẫn "Bất tử"
    if st.session_state.guide_step > 0:
        st.markdown(f"""<div class="guide-highlight">
            <small style="color:#00FFC2">NHIỆM VỤ {st.session_state.guide_step}/4</small><br>
            <b>{["","Nhập tin nhắn đầu tiên","Nhấn nút '🔊 Nghe'","Chọn một gợi ý","Nhập/Xuất File Dữ liệu"][st.session_state.guide_step]}</b>
        </div>""", unsafe_allow_html=True)
        if st.button("⏩ Bỏ qua hướng dẫn", use_container_width=True):
            st.session_state.guide_step = 0; st.rerun()

    st.subheader("🔊 Giọng nói")
    st.session_state.v_speed = st.slider("Tốc độ đọc", 0.5, 2.0, 1.0)
    if st.button("🛑 DỪNG ĐỌC NGAY", type="primary", use_container_width=True):
        voice_engine("", "stop")

    st.divider()
    st.subheader("📂 Dữ liệu")
    if st.session_state.guide_step == 4: st.markdown('<div class="pointer-anim">⬇️ THAO TÁC Ở ĐÂY</div>', unsafe_allow_html=True)
    
    # Nhập/Xuất File
    chat_json = json.dumps(st.session_state.messages, ensure_ascii=False)
    st.download_button("📤 Xuất File JSON", data=chat_json, file_name="nexus_chat.json", use_container_width=True)
    
    up_file = st.file_uploader("📥 Nhập File dữ liệu", type="json")
    if up_file and st.button("🔄 Khôi phục dữ liệu", use_container_width=True):
        st.session_state.messages = json.loads(up_file.getvalue().decode("utf-8"))
        st.session_state.guide_step = 0; st.rerun()

# --- 6. GIAO DIỆN CHÍNH ---
st.title("Hệ thống Nexus Black Diamond")

if st.session_state.guide_step == 0 and not st.session_state.messages:
    if st.button("✨ BẮT ĐẦU TRẢI NGHIỆM"):
        st.session_state.guide_step = 1; st.rerun()

# HIỂN THỊ CHAT
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            # Chỉ dẫn bước 2
            if st.session_state.guide_step == 2: st.markdown('<div class="pointer-anim">👆 Nhấn vào "Nghe"</div>', unsafe_allow_html=True)
            
            c1, c2, c3, _ = st.columns([1,1,1,4])
            with c1:
                if st.button("🔊 Nghe", key=f"v_{i}"):
                    voice_engine(m["content"])
                    if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
            with c2:
                if st.button("📱 QR", key=f"q_{i}"):
                    qr = qrcode.make(m["content"][:200]); buf = BytesIO(); qr.save(buf, format="PNG"); st.image(buf, width=150)
            with c3:
                if st.button("🔇 Dừng", key=f"s_{i}"): voice_engine("", "stop")

# GỢI Ý (CHỐNG DÍNH)
if st.session_state.suggestions:
    st.write("---")
    if st.session_state.guide_step == 3: st.markdown('<div class="pointer-anim">👇 Chọn một gợi ý để tiếp tục</div>', unsafe_allow_html=True)
    
    # Chia cột tỉ lệ bằng nhau để nút không dính
    s_cols = st.columns(len(st.session_state.suggestions))
    for idx, sug in enumerate(st.session_state.suggestions):
        with s_cols[idx]:
            if st.button(f"🔹 {sug}", key=f"sug_{idx}", use_container_width=True):
                if st.session_state.guide_step == 3: st.session_state.guide_step = 4
                chat_engine(sug); st.rerun()

# NHẬP LIỆU
st.write("<br><br><br>", unsafe_allow_html=True)
if st.session_state.guide_step == 1: st.markdown('<div class="pointer-anim" style="text-align:left; margin-left:100px;">👇 Gõ lời chào vào đây</div>', unsafe_allow_html=True)
with st.container():
    c_mic, c_input = st.columns([1, 9])
    with c_mic:
        aud = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v28')
        if aud:
            trans = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", aud['bytes']))
            chat_engine(trans.text); st.rerun()
    with c_input:
        inp = st.chat_input("Hỏi Nexus bất cứ điều gì...")
        if inp: chat_engine(inp); st.rerun()
