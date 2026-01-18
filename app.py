import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder, speech_to_text
import time

# --- 1. CẤU HÌNH GIAO DIỆN HORIZON OS (GRADIENT BACKGROUND) ---
st.set_page_config(page_title="Nexus Horizon OS v55", layout="wide", page_icon="🌄")

st.markdown("""
    <style>
    /* Hình nền Gradient "Chạng vạng" */
    .stApp {
        background: linear-gradient(135deg, #A8C0FF 0%, #3F2B96 100%) !important;
        background-attachment: fixed; /* Giữ cố định khi cuộn */
        color: #000000 !important;
    }
    
    /* Đảm bảo chữ luôn đen rõ nét trên nền gradient */
    p, span, h1, h2, h3, label, div, b { color: #000000 !important; font-weight: 600 !important; }
    
    /* Thanh bên "Pha lê" */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.85) !important; /* Hơi trong suốt */
        border-right: 3px solid #6A5ACD !important; /* Viền tím Lavender */
        border-radius: 15px; margin: 10px;
    }
    .stSidebar .stButton button {
        background: #6A5ACD !important; /* Màu tím Lavender */
        color: white !important;
        border-radius: 12px !important;
        height: 45px !important;
        font-size: 15px !important;
        box-shadow: 0 4px 10px rgba(106, 90, 205, 0.4) !important;
        border: none;
    }
    
    /* Box hướng dẫn "Đèn hiệu" */
    .beacon-guide {
        background: linear-gradient(45deg, #89CFF0, #4682B4) !important; /* Xanh da trời */
        color: #FFFFFF !important;
        padding: 25px; border-radius: 25px;
        text-align: center; border: 4px solid #FFFFFF;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 10000; position: relative;
        animation: pulse-beacon 1.5s infinite; /* Hiệu ứng nhấp nháy nhẹ */
    }
    @keyframes pulse-beacon {
        0% { transform: scale(1); opacity: 0.9; }
        50% { transform: scale(1.02); opacity: 1; }
        100% { transform: scale(1); opacity: 0.9; }
    }
    .beacon-guide b, .beacon-guide p { color: white !important; }
    
    /* Giao diện chat hiện đại, bo tròn */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.95) !important; /* Hơi trong suốt trên nền gradient */
        border: 1px solid #E0E0E0 !important;
        border-radius: 20px !important;
        padding: 15px !important;
        margin-bottom: 12px !important;
    }

    /* Nút mic lớn, dễ bấm trên điện thoại */
    [data-testid="stMicRecorder"] button {
        background: #FF4B4B !important; color: white !important;
        border-radius: 50% !important; /* Nút tròn */
        width: 60px; height: 60px; font-size: 24px;
        box-shadow: 0 5px 15px rgba(255, 75, 75, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE (CHỐNG LỖI "XIN CHÀO") ---
for key in ['messages', 'guide_step', 'done', 'v_speed', 'live_mode', 'init_run']:
    if key not in st.session_state:
        st.session_state[key] = {
            'messages': [], 'guide_step': 0, 'done': False, 
            'v_speed': 1.0, 'live_mode': False, 'init_run': True
        }[key]

# Chạy lần đầu sẽ bỏ qua màn hình chào nếu đã "done"
if st.session_state.init_run and st.session_state.done:
    st.session_state.guide_step = 0
    st.session_state.init_run = False
elif st.session_state.init_run:
    st.session_state.init_run = False # Đánh dấu đã chạy init

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HÀM XỬ LÝ ĐỘC QUYỀN ---
def save_to_txt(content):
    return content # Trả về nội dung để nút download xử lý

def goi_ai(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"): # Avatar cho user
        st.markdown(f"**{prompt}**") # Hiện tin nhắn của user

    with st.chat_message("assistant", avatar="🤖"): # Avatar cho AI
        p = st.empty(); full = ""
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages], stream=True)
        for chunk in res:
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                p.markdown(f"**{full}**")
        st.session_state.messages.append({"role": "assistant", "content": full})
        
        # Logic hướng dẫn
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        
        # Tự động đọc trong Live Mode
        if st.session_state.live_mode:
            js = f"<script>window.speechSynthesis.cancel(); var u=new SpeechSynthesisUtterance('{full.replace(chr(10), ' ')}'); u.lang='vi-VN'; u.rate={st.session_state.v_speed}; window.speechSynthesis.speak(u);</script>"
            st.components.v1.html(js, height=0)
        st.rerun()

# --- 4. THANH BÊN (SIDEBAR) PHA LÊ & TÍNH NĂNG ---
with st.sidebar:
    st.title("🌌 HORIZON OS")
    
    # Nút Live Mode
    if st.button("🎙️ LIVE MODE: " + ("ON" if st.session_state.live_mode else "OFF"), use_container_width=True):
        st.session_state.live_mode = not st.session_state.live_mode
        st.rerun()

    st.divider()
    st.subheader("🔊 Cài đặt Giọng nói")
    st.session_state.v_speed = st.slider("Tốc độ", 0.5, 2.0, 1.0, key="slider_speed")
    if st.button("🛑 DỪNG ĐỌC", use_container_width=True):
        st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

    st.divider()
    st.subheader("💾 Quản lý Dữ liệu")
    # Xuất toàn bộ lịch sử ra TXT
    full_history = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
    st.download_button("📤 XUẤT LỊCH SỬ (.TXT)", data=full_history, file_name="nexus_chat_history.txt", use_container_width=True)

    # Nhập dữ liệu từ TXT (nâng cấp hiển thị)
    uploaded_txt = st.file_uploader("📥 NHẬP FILE .TXT", type="txt")
    if uploaded_txt:
        content = uploaded_txt.getvalue().decode("utf-8")
        if st.button("🔄 KHÔI PHỤC TỪ .TXT", use_container_width=True):
            # Tạm thời append vào để hiển thị, không parse lại thành tin nhắn riêng lẻ để đơn giản
            st.session_state.messages.append({"role": "assistant", "content": f"**Dữ liệu từ file đã nạp:**\n```\n{content}\n```"})
            st.rerun()

    st.divider()
    if st.button("🗑️ XÓA TOÀN BỘ CHAT", type="secondary", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# --- 5. HỆ THỐNG HƯỚNG DẪN "ĐÈN HIỆU" TRỰC TIẾP ---
if st.session_state.guide_step > 0 and not st.session_state.done:
    steps = ["", 
             "🎤 BƯỚC 1: Hãy nhấn **Nút Mic Tròn** bên dưới và nói <b>'Xin chào Nexus'</b>.", 
             "🔊 BƯỚC 2: AI đã trả lời! Bây giờ, hãy nhấn nút <b>'📄 LƯU .TXT'</b> dưới tin nhắn đó.", 
             "🏁 BƯỚC 3: Hoàn hảo! Nhấn <b>'HOÀN TẤT HƯỚNG DẪN'</b> để mở khóa toàn bộ sức mạnh."]
    st.markdown(f'<div class="beacon-guide"><b>HƯỚNG DẪN SỬ DỤNG</b><br><p>{steps[st.session_state.guide_step]}</p></div>', unsafe_allow_html=True)

# --- 6. GIAO DIỆN CHÍNH ---
if not st.session_state.done and st.session_state.guide_step == 0:
    st.title("Nexus Horizon OS 🌌")
    st.markdown("### Trợ lý AI thế hệ mới với giao diện tinh tế và Live Voice.")
    if st.button("🚀 BẮT ĐẦU KHÁM PHÁ (HƯỚNG DẪN)", type="primary", use_container_width=True):
        st.session_state.guide_step = 1; st.session_state.messages = []; st.rerun() # Xóa tin nhắn cũ khi bắt đầu
    if st.button("⏩ BỎ QUA HƯỚNG DẪN", use_container_width=True):
        st.session_state.done = True; st.rerun()

if st.session_state.done or st.session_state.guide_step > 0:
    # HIỂN THỊ TIN NHẮN CHAT
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"], avatar="👤" if m["role"] == "user" else "🤖"):
            st.markdown(f"**{m['content']}**")
            if m["role"] == "assistant":
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"🔊 ĐỌC LẠI", key=f"read_{i}", use_container_width=True):
                        js = f"<script>window.speechSynthesis.cancel(); var u=new SpeechSynthesisUtterance('{m['content'].replace(chr(10), ' ')}'); u.lang='vi-VN'; u.rate={st.session_state.v_speed}; window.speechSynthesis.speak(u);</script>"
                        st.components.v1.html(js, height=0)
                with c2:
                    # Nút lưu TXT (nhấp nháy ở bước 2)
                    if st.download_button(f"📄 LƯU .TXT", data=m['content'], file_name=f"chat_{i}.txt", key=f"save_txt_{i}", use_container_width=True):
                        if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()

    # NÚT HOÀN TẤT HƯỚNG DẪN (CHỈ HIỆN Ở BƯỚC 3)
    if st.session_state.guide_step == 3:
        st.write("<br><br>", unsafe_allow_html=True)
        if st.button("🏁 HOÀN TẤT HƯỚNG DẪN", type="primary", use_container_width=True):
            st.session_state.done = True; st.session_state.guide_step = 0; st.session_state.messages = []; st.rerun()

    # KHU VỰC NHẬP LIỆU (STT & TEXT)
    st.divider()
    col_mic, col_input = st.columns([1, 4])
    
    with col_mic:
        # TÍNH NĂNG STT - NÚT MIC TRÒN (NHẤP NHÁY Ở BƯỚC 1)
        # Sử dụng key động để tránh lỗi trùng lặp khi rerun
        audio_data = mic_recorder(
            start_prompt="🎤 BẮT ĐẦU", stop_prompt="🛑 DỪNG",
            key=f"stt_mic_{st.session_state.guide_step}_{len(st.session_state.messages)}"
        )
        if audio_data:
            transcribed_text = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("audio.wav", audio_data['bytes'])).text
            if transcribed_text:
                goi_ai(transcribed_text)

    with col_input:
        # NHẬP LIỆU VĂN BẢN (CHỈ DÙNG KHI KHÔNG PHẢI BƯỚC HƯỚNG DẪN MIC)
        if st.session_state.guide_step != 1:
            inp = st.chat_input("Gõ tin nhắn hoặc dùng Mic bên cạnh...")
            if inp:
                goi_ai(inp)
