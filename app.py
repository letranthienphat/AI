import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder, speech_to_text
import time

# --- 1. CẤU HÌNH GIAO DIỆN SUNLIGHT ELITE ---
st.set_page_config(page_title="Nexus Live OS v50", layout="wide", page_icon="🎙️")

st.markdown("""
    <style>
    /* Ép buộc nền trắng và chữ ĐEN ĐẬM nhất có thể */
    .stApp { background-color: #FFFFFF !important; }
    p, span, h1, h2, h3, label, div, b { color: #000000 !important; font-weight: 600 !important; }
    
    /* Thanh bên siêu nổi bật */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA !important;
        border-right: 5px solid #FF4B4B !important; /* Viền đỏ cực mạnh */
    }
    .stSidebar .stButton button {
        background: linear-gradient(45deg, #FF4B4B, #FF8E53) !important;
        color: white !important;
        border-radius: 15px !important;
        height: 50px !important;
        font-size: 16px !important;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3) !important;
    }
    
    /* Box hướng dẫn AR rực rỡ giữa màn hình */
    .guide-box {
        background: #000000 !important; color: #FFFFFF !important;
        padding: 25px; border-radius: 25px;
        text-align: center; border: 4px solid #FF4B4B;
        box-shadow: 0 15px 40px rgba(0,0,0,0.5);
        z-index: 10000; position: relative;
    }
    .guide-box b, .guide-box p { color: white !important; }
    
    /* Giao diện chat Apple Style High-Contrast */
    .stChatMessage {
        background-color: #F0F2F6 !important;
        border: 2px solid #DDE1E7 !important;
        border-radius: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE ---
for key in ['messages', 'guide_step', 'done', 'v_speed', 'live_mode']:
    if key not in st.session_state:
        st.session_state[key] = {'messages': [], 'guide_step': 0, 'done': False, 'v_speed': 1.0, 'live_mode': False}[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HÀM XỬ LÝ ĐỘC QUYỀN ---
def save_to_txt(content):
    return content

def goi_ai(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        p = st.empty(); full = ""
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages], stream=True)
        for chunk in res:
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                p.markdown(f"### {full}")
        st.session_state.messages.append({"role": "assistant", "content": full})
        
        # Nếu đang ở bước hướng dẫn
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        
        # Tự động đọc nếu trong Live Mode
        if st.session_state.live_mode:
            js = f"<script>window.speechSynthesis.cancel(); var u=new SpeechSynthesisUtterance('{full.replace(chr(10), ' ')}'); u.lang='vi-VN'; window.speechSynthesis.speak(u);</script>"
            st.components.v1.html(js, height=0)
        st.rerun()

# --- 4. THANH BÊN (SIDEBAR) TÍNH NĂNG MẠNH ---
with st.sidebar:
    st.title("🚀 NEXUS EXCLUSIVE")
    
    if st.button("🎙️ CHẾ ĐỘ LIVE: " + ("ON" if st.session_state.live_mode else "OFF"), use_container_width=True):
        st.session_state.live_mode = not st.session_state.live_mode
        st.rerun()

    st.divider()
    st.subheader("💾 LƯU TRỮ .TXT")
    # Backup toàn bộ hội thoại thành file TXT
    full_history = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
    st.download_button("📤 XUẤT TOÀN BỘ (.TXT)", data=full_history, file_name="nexus_full_backup.txt", use_container_width=True)

    st.divider()
    if st.button("🗑️ XÓA SẠCH DỮ LIỆU", type="secondary", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# --- 5. HỆ THỐNG HƯỚNG DẪN TRỰC DIỆN ---
if st.session_state.guide_step > 0:
    steps = ["", 
             "🎤 BƯỚC 1: Hãy nhấn vào nút Micro bên dưới và nói 'Xin chào'.", 
             "🔊 BƯỚC 2: AI đang trả lời, hãy nhấn nút 'LƯU .TXT' dưới tin nhắn.", 
             "🏁 BƯỚC 3: Tuyệt vời! Nhấn 'HOÀN TẤT' để mở toàn bộ tính năng."]
    st.markdown(f'<div class="guide-box"><b>HƯỚNG DẪN SỬ DỤNG</b><br><p>{steps[st.session_state.guide_step]}</p></div>', unsafe_allow_html=True)

# --- 6. GIAO DIỆN CHÍNH ---
if not st.session_state.done and st.session_state.guide_step == 0:
    st.title("Nexus Live OS v50 💎")
    st.markdown("### Nền tảng trợ lý độc quyền - Trải nghiệm Live Voice & STT")
    if st.button("🚀 BẮT ĐẦU KHÁM PHÁ (GUIDED)", type="primary", use_container_width=True):
        st.session_state.guide_step = 1; st.rerun()
    if st.button("⏩ BỎ QUA HƯỚNG DẪN"):
        st.session_state.done = True; st.rerun()

if st.session_state.done or st.session_state.guide_step > 0:
    # Vùng hiển thị Chat
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(f"### {m['content']}")
            if m["role"] == "assistant":
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"🔊 ĐỌC LẠI", key=f"v_{i}"):
                        js = f"<script>window.speechSynthesis.cancel(); var u=new SpeechSynthesisUtterance('{m['content'].replace(chr(10), ' ')}'); u.lang='vi-VN'; window.speechSynthesis.speak(u);</script>"
                        st.components.v1.html(js, height=0)
                with c2:
                    if st.download_button(f"📄 LƯU .TXT", data=m['content'], file_name=f"chat_{i}.txt", key=f"t_{i}"):
                        if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()

    # Nút hoàn tất bước cuối
    if st.session_state.guide_step == 3:
        if st.button("🏁 HOÀN TẤT HƯỚNG DẪN", type="primary", use_container_width=True):
            st.session_state.done = True; st.session_state.guide_step = 0; st.rerun()

    # KHU VỰC NHẬP LIỆU ĐỘC QUYỀN (STT & TEXT)
    st.divider()
    col_stt, col_input = st.columns([1, 4])
    
    with col_stt:
        # Tính năng STT - Nói thành văn bản
        text_from_voice = speech_to_text(language='vi', start_prompt="🎤 NÓI", stop_prompt="🛑 DỪNG", key='stt')
        if text_from_voice:
            goi_ai(text_from_voice)

    with col_input:
        # Nhập liệu văn bản truyền thống
        inp = st.chat_input("Gõ nội dung hoặc dùng Mic bên cạnh...")
        if inp:
            goi_ai(inp)
