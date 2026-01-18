import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
import json
from io import BytesIO

# --- 1. GIAO DIỆN THUẦN VIỆT & HIỆN ĐẠI ---
st.set_page_config(page_title="Nexus Vietnam v30", layout="wide", page_icon="🇻🇳")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Lexend', sans-serif; }
    
    /* Làm nổi bật khung chat AI */
    .stChatMessage { border-radius: 15px !important; border: 1px solid #e0e0e0 !important; margin-bottom: 10px; }
    
    /* Giao diện hướng dẫn chuyên nghiệp */
    .huong-dan-box {
        background: #e3f2fd;
        border-left: 5px solid #1976d2;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    /* Chống dính nút gợi ý */
    .stButton > button {
        width: 100%;
        border-radius: 12px !important;
        border: 1px solid #ddd !important;
        font-weight: 500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO DỮ LIỆU ---
if "messages" not in st.session_state: st.session_state.messages = []
if "suggestions" not in st.session_state: st.session_state.suggestions = []
if "guide_step" not in st.session_state: st.session_state.guide_step = 0
if "v_speed" not in st.session_state: st.session_state.v_speed = 1.0

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HÀM XỬ LÝ CHÍNH ---
def xoa_lich_su_huong_dan():
    st.session_state.messages = []
    st.session_state.suggestions = []

def goi_ai_tra_loi(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        p = st.empty(); full = ""
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", 
                                            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages], 
                                            stream=True)
        for chunk in res:
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                p.markdown(full + "▌")
        p.markdown(full)
        st.session_state.messages.append({"role": "assistant", "content": full})
        
        # Tự động tạo gợi ý thật bằng tiếng Việt
        try:
            s_res = client.chat.completions.create(model="llama-3.1-8b-instant", 
                messages=[{"role": "user", "content": f"Gợi ý 3 câu hỏi tiếng Việt cực ngắn từ: {full[:50]}"}])
            st.session_state.suggestions = [s.strip() for s in s_res.choices[0].message.content.split('\n') if len(s) > 3][:3]
        except: pass
        
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.rerun()

# --- 4. THANH ĐIỀU KHIỂN (SIDEBAR) ---
with st.sidebar:
    st.header("🇻🇳 Bảng Điều Khiển")
    
    if st.session_state.guide_step > 0:
        st.markdown(f"""<div class="huong-dan-box">
            <b>Bước {st.session_state.guide_step}/4</b><br>
            {["","Gửi tin nhắn chào","Nhấn nút Nghe câu trả lời","Chọn một gợi ý thông minh","Nhập dữ liệu cũ ở dưới"][st.session_state.guide_step]}
        </div>""", unsafe_allow_html=True)

    st.subheader("🔊 Giọng đọc")
    st.session_state.v_speed = st.slider("Tốc độ nói", 0.5, 2.0, 1.0)
    if st.button("🛑 Dừng đọc ngay", use_container_width=True):
        st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

    st.divider()
    st.subheader("💾 Dữ liệu & Tệp")
    
    # Nút Hoàn tất ở bước 4
    if st.session_state.guide_step == 4:
        if st.button("✅ HOÀN TẤT HƯỚNG DẪN", type="primary", use_container_width=True):
            xoa_lich_su_huong_dan()
            st.session_state.guide_step = 0
            st.success("Đã xóa lịch sử hướng dẫn!")
            st.rerun()

    # Xuất/Nhập JSON
    chat_json = json.dumps(st.session_state.messages, ensure_ascii=False)
    st.download_button("📤 Xuất dữ liệu", data=chat_json, file_name="nexus.json", use_container_width=True)
    up = st.file_uploader("📥 Nhập file cũ", type="json")
    if up and st.button("🔄 Khôi phục", use_container_width=True):
        st.session_state.messages = json.loads(up.getvalue().decode("utf-8"))
        st.rerun()

# --- 5. MÀN HÌNH CHÀO MỪNG ---
if st.session_state.guide_step == 0 and not st.session_state.messages:
    st.title("Chào mừng đến với Nexus Elite 💎")
    st.write("Bạn có muốn tôi hướng dẫn cách sử dụng không?")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 Bắt đầu hướng dẫn", type="primary", use_container_width=True):
            st.session_state.guide_step = 1
            st.rerun()
    with c2:
        if st.button("⏩ Bỏ qua", use_container_width=True):
            st.info("Bạn có thể bắt đầu sử dụng ngay.")
            
    # Tính năng Ghi nhớ với dấu Tick (Checkbox)
    st.checkbox("✔️ Ghi nhớ lựa chọn của tôi (không hỏi lại)", value=False)

# --- 6. KHUNG CHAT AI (ĐÃ CỦNG CỐ) ---
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            col1, col2, col3 = st.columns([1,1,4])
            with col1:
                if st.button("🔊 Nghe", key=f"v_{i}"):
                    clean = m["content"].replace('"', "'").replace('\n', ' ')
                    js = f"<script>window.speechSynthesis.cancel(); var u=new SpeechSynthesisUtterance('{clean}'); u.lang='vi-VN'; u.rate={st.session_state.v_speed}; window.speechSynthesis.speak(u);</script>"
                    st.components.v1.html(js, height=0)
                    if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
            with col2:
                if st.button("🔇 Dừng", key=f"s_{i}"):
                    st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

# --- GỢI Ý THÔNG MINH (CHỐNG DÍNH) ---
if st.session_state.suggestions:
    st.write("---")
    st.caption("💡 Gợi ý tiếp theo:")
    cols = st.columns(len(st.session_state.suggestions))
    for idx, sug in enumerate(st.session_state.suggestions):
        with cols[idx]:
            if st.button(sug, key=f"sug_{idx}", use_container_width=True):
                if st.session_state.guide_step == 3: st.session_state.guide_step = 4
                goi_ai_tra_loi(sug)

# --- KHU VỰC NHẬP LIỆU ---
st.write("<br><br><br>", unsafe_allow_html=True)
with st.container():
    c_mic, c_input = st.columns([1, 9])
    with c_mic:
        aud = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='mic_v30')
        if aud:
            trans = client.audio.transcriptions.create(model="whisper-large-v3-turbo", file=("v.wav", aud['bytes']))
            goi_ai_tra_loi(trans.text)
    with c_input:
        inp = st.chat_input("Nhập câu hỏi tại đây...")
        if inp:
            goi_ai_tra_loi(inp)
