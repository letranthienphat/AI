import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
import json
import time
from io import BytesIO

# --- 1. GIAO DIỆN CHUYÊN NGHIỆP ---
st.set_page_config(page_title="Nexus Titanium v32", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Lexend', sans-serif; }
    
    /* Hiệu ứng chỉ dẫn cực kỹ */
    .spotlight-box {
        border: 3px solid #00FFC2 !important;
        box-shadow: 0 0 20px rgba(0, 255, 194, 0.4);
        border-radius: 15px; padding: 10px;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse { 0% { opacity: 0.8; } 50% { opacity: 1; } 100% { opacity: 0.8; } }

    .mui-ten { color: #FF4B4B; font-size: 20px; font-weight: bold; animation: bounce 0.6s infinite alternate; }
    @keyframes bounce { from { transform: translateY(0); } to { transform: translateY(-8px); } }
    
    .vung-mo { opacity: 0.2; pointer-events: none; filter: blur(2px); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE (CỐ ĐỊNH) ---
for key in ['messages', 'suggestions', 'guide_step', 'da_ghi_nho', 'v_speed', 'session_id']:
    if key not in st.session_state:
        st.session_state[key] = {
            'messages': [], 'suggestions': [], 'guide_step': 0, 
            'da_ghi_nho': False, 'v_speed': 1.0, 'session_id': str(time.time())
        }[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HÀM XỬ LÝ AI ---
def goi_ai_titan(prompt):
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
        
        # Cập nhật gợi ý với Key mới để tránh lỗi trùng lặp
        st.session_state.suggestions = ["Bạn khỏe không?", "Thời tiết thế nào?", "Kể chuyện cười"]
        st.session_state.session_id = str(time.time()) # Làm mới ID nút
        
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.rerun()

# --- 4. BẢNG ĐIỀU KHIỂN SIDEBAR ---
with st.sidebar:
    st.header("🛡️ ĐIỀU KHIỂN NEXUS")
    
    if st.session_state.guide_step > 0:
        st.error(f"📍 BƯỚC THỰC HÀNH {st.session_state.guide_step}/4")
        huong_dan = ["", 
            "Gõ 'Chào AI' vào ô chát đáy màn hình.",
            "Nhấn nút '🔊 NGHE' màu xanh ở dưới câu trả lời của AI.",
            "Nhấn một 'Gợi ý' bất kỳ phía trên ô chát.",
            "Kéo file JSON vào ô bên dưới và nhấn Hoàn tất."]
        st.write(huong_dan[st.session_state.guide_step])
        
        if st.session_state.guide_step == 4:
            if st.button("🏁 XÁC NHẬN HOÀN TẤT", type="primary", use_container_width=True):
                st.session_state.messages = []
                st.session_state.guide_step = 0
                st.rerun()

    st.divider()
    st.subheader("🔊 Giọng đọc")
    st.session_state.v_speed = st.slider("Tốc độ", 0.5, 2.0, 1.0)
    
    st.divider()
    st.subheader("📂 Dữ liệu")
    if st.session_state.guide_step == 4: st.markdown('<div class="mui-ten">👇 THỰC HÀNH Ở ĐÂY</div>', unsafe_allow_html=True)
    with st.container(border=(st.session_state.guide_step == 4)):
        st.download_button("📤 Xuất JSON", data=json.dumps(st.session_state.messages), file_name="chat.json", use_container_width=True)
        up = st.file_uploader("📥 Nhập dữ liệu cũ", type="json")
        if up: st.success("Đã nhận file! Hãy nhấn Hoàn tất.")

# --- 5. MÀN HÌNH CHÀO (GHI NHỚ LỰA CHỌN) ---
if st.session_state.guide_step == 0 and not st.session_state.messages and not st.session_state.da_ghi_nho:
    st.title("Nexus Elite: Trợ lý AI Chuyên Nghiệp")
    st.info("Chào bạn! Để bắt đầu, chúng ta hãy thực hành nhanh 4 bước sử dụng.")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 BẮT ĐẦU THỰC HÀNH", type="primary", use_container_width=True):
            st.session_state.guide_step = 1; st.rerun()
    with c2:
        if st.button("⏩ BỎ QUA", use_container_width=True):
            st.session_state.da_ghi_nho = True; st.rerun()
    
    # Dùng checkbox để ghi nhớ
    ghi_nho = st.checkbox("✔️ Ghi nhớ lựa chọn (Không hỏi lại lần sau)", value=True)
    if ghi_nho: st.session_state.da_ghi_nho = True

# --- 6. KHU VỰC THỰC HÀNH CHÍNH ---

# Hiển thị Chat (Mờ đi nếu đang ở bước 1 hoặc 4)
chat_blur = "vung-mo" if st.session_state.guide_step in [1, 4] else ""
st.markdown(f'<div class="{chat_blur}">', unsafe_allow_html=True)
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            if st.session_state.guide_step == 2: st.markdown('<div class="mui-ten">👆 NHẤN ĐỂ NGHE AI ĐỌC</div>', unsafe_allow_html=True)
            c1, c2, _ = st.columns([1,1,4])
            with c1:
                if st.button("🔊 NGHE", key=f"voice_{i}_{st.session_state.session_id}", type="primary" if st.session_state.guide_step == 2 else "secondary"):
                    clean = m["content"].replace('"', "'").replace('\n', ' ')
                    js = f"<script>window.speechSynthesis.cancel(); var u=new SpeechSynthesisUtterance('{clean}'); u.lang='vi-VN'; u.rate={st.session_state.v_speed}; window.speechSynthesis.speak(u);</script>"
                    st.components.v1.html(js, height=0)
                    if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
            with c2:
                if st.button("🔇 DỪNG", key=f"stop_{i}_{st.session_state.session_id}"):
                    st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)
st.markdown('</div>', unsafe_allow_html=True)

# Gợi ý (Bước 3)
if st.session_state.suggestions:
    sug_blur = "vung-mo" if st.session_state.guide_step in [1, 2, 4] else ""
    st.markdown(f'<div class="{sug_blur}">', unsafe_allow_html=True)
    st.divider()
    if st.session_state.guide_step == 3: st.markdown('<div class="mui-ten">👇 BẤM VÀO NÚT GỢI Ý NÀY</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for idx, sug in enumerate(st.session_state.suggestions):
        # SỬA LỖI TRÙNG KEY BẰNG CÁCH THÊM SESSION_ID VÀO KEY
        if cols[idx].button(f"✨ {sug}", key=f"s_{idx}_{st.session_state.session_id}", use_container_width=True):
            if st.session_state.guide_step == 3: st.session_state.guide_step = 4
            goi_ai_titan(sug)
    st.markdown('</div>', unsafe_allow_html=True)

# Nhập liệu (Bước 1)
in_blur = "vung-mo" if st.session_state.guide_step in [2, 3, 4] else ""
st.markdown(f'<div class="{in_blur}">', unsafe_allow_html=True)
st.write("<br><br><br>", unsafe_allow_html=True)
if st.session_state.guide_step == 1: st.markdown('<div class="mui-ten" style="margin-left:100px;">👇 THỰC HÀNH: GÕ VÀO ĐÂY</div>', unsafe_allow_html=True)
inp = st.chat_input("Nhập câu hỏi tại đây...")
if inp:
    goi_ai_titan(inp)
st.markdown('</div>', unsafe_allow_html=True)
