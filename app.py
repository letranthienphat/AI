import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
import json
from io import BytesIO

# --- 1. GIAO DIỆN & HIỆU ỨNG CHỈ TAY (CSS) ---
st.set_page_config(page_title="Nexus Masterclass v31", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Lexend', sans-serif; }
    
    /* Hiệu ứng khoanh vùng đỏ rực rỡ */
    .spotlight {
        border: 4px solid #FF4B4B !important;
        box-shadow: 0 0 20px #FF4B4B !important;
        border-radius: 15px !important;
        padding: 10px;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse { 0% { opacity: 0.7; } 50% { opacity: 1; } 100% { opacity: 0.7; } }

    /* Mũi tên chỉ dẫn nhấp nháy */
    .chi-dan {
        color: #FF4B4B;
        font-size: 24px;
        font-weight: bold;
        animation: bounce 0.5s infinite alternate;
    }
    @keyframes bounce { from { transform: translateY(0); } to { transform: translateY(-10px); } }
    
    /* Làm mờ các vùng không quan trọng khi hướng dẫn */
    .vung-mo { opacity: 0.2; pointer-events: none; filter: blur(2px); transition: 0.5s; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE (CÓ GHI NHỚ) ---
for key in ['messages', 'suggestions', 'guide_step', 'v_speed', 'da_ghi_nho']:
    if key not in st.session_state:
        st.session_state[key] = {'messages': [], 'suggestions': [], 'guide_step': 0, 'v_speed': 1.0, 'da_ghi_nho': False}[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. LOGIC HƯỚNG DẪN THỰC HÀNH ---
def hoan_tat_huong_dan():
    st.session_state.messages = []
    st.session_state.suggestions = []
    st.session_state.guide_step = 0
    if ghi_nho_checkbox:
        st.session_state.da_ghi_nho = True
    st.rerun()

def goi_ai(prompt):
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
        
        # Gợi ý cực rõ
        st.session_state.suggestions = ["Bạn khỏe không?", "Kể chuyện cười đi", "AI là gì?"]
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.rerun()

# --- 4. SIDEBAR (BẢNG ĐIỀU KHIỂN CHI TIẾT) ---
with st.sidebar:
    st.header("🇻🇳 TRUNG TÂM ĐIỀU KHIỂN")
    
    if st.session_state.guide_step > 0:
        st.error(f"📍 BƯỚC {st.session_state.guide_step}: THỰC HÀNH NGAY")
        nhiem_vu = [
            "",
            "👇 Gõ 'Xin chào' vào ô nhập liệu bên dưới.",
            "🔊 Nhấn nút 'NGHE' màu xanh dưới câu trả lời của AI.",
            "✨ Nhấn vào một trong các 'Nút gợi ý' vừa xuất hiện.",
            "📥 Kéo file JSON vào ô 'Nhập file' bên dưới đây."
        ]
        st.write(nhiem_vu[st.session_state.guide_step])
        
        if st.session_state.guide_step == 4:
            st.markdown("---")
            if st.button("🏁 XÁC NHẬN HOÀN TẤT", type="primary", use_container_width=True):
                hoan_tat_huong_dan()

    st.divider()
    st.subheader("🔊 Giọng nói")
    st.session_state.v_speed = st.slider("Tốc độ", 0.5, 2.0, 1.0)
    
    st.divider()
    # Khu vực Nhập/Xuất (Spotlight ở bước 4)
    if st.session_state.guide_step == 4: st.markdown('<div class="chi-dan">👇 THỰC HÀNH TẠI ĐÂY</div>', unsafe_allow_html=True)
    with st.container(border=(st.session_state.guide_step == 4)):
        st.download_button("📤 Xuất dữ liệu", data=json.dumps(st.session_state.messages), file_name="chat.json", use_container_width=True)
        up = st.file_uploader("📥 Nhập file JSON", type="json")
        if up: st.success("Đã nhận file! Bây giờ hãy nhấn nút Hoàn tất ở trên.")

# --- 5. MÀN HÌNH CHÀO (KHÔNG HỎI LẠI NẾU ĐÃ GHI NHỚ) ---
if st.session_state.guide_step == 0 and not st.session_state.messages and not st.session_state.da_ghi_nho:
    st.title("Chào mừng đến với Nexus Elite 💎")
    st.info("Để sử dụng hiệu quả, bạn cần 1 phút thực hành hướng dẫn cực kỹ.")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 BẮT ĐẦU THỰC HÀNH", type="primary", use_container_width=True):
            st.session_state.guide_step = 1; st.rerun()
    with c2:
        if st.button("⏩ BỎ QUA LUÔN", use_container_width=True):
            st.session_state.da_ghi_nho = True; st.rerun()
    
    ghi_nho_checkbox = st.checkbox("✔️ Ghi nhớ lựa chọn (Không bao giờ hỏi lại bảng này)", value=True)

# --- 6. KHU VỰC CHAT & THỰC HÀNH ---

# Hiển thị Chat
vung_chat = "vung-mo" if st.session_state.guide_step in [1, 4] else ""
st.markdown(f'<div class="{vung_chat}">', unsafe_allow_html=True)
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            # Spotlight bước 2
            if st.session_state.guide_step == 2: st.markdown('<div class="chi-dan">👆 NHẤN NÚT NÀY</div>', unsafe_allow_html=True)
            c1, c2, _ = st.columns([1,1,4])
            with c1:
                if st.button("🔊 NGHE", key=f"v_{i}", type=("primary" if st.session_state.guide_step == 2 else "secondary")):
                    if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
            with c2:
                if st.button("🛑 DỪNG", key=f"s_{i}"):
                    st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)
st.markdown('</div>', unsafe_allow_html=True)

# Gợi ý thông minh (Bước 3)
if st.session_state.suggestions:
    vung_sug = "vung-mo" if st.session_state.guide_step in [1, 2, 4] else ""
    st.markdown(f'<div class="{vung_sug}">', unsafe_allow_html=True)
    st.divider()
    if st.session_state.guide_step == 3: st.markdown('<div class="chi-dan">👇 BẤM VÀO 1 TRONG 3 NÚT NÀY</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for idx, sug in enumerate(st.session_state.suggestions):
        if cols[idx].button(f"✨ {sug}", key=f"s_{idx}", use_container_width=True):
            if st.session_state.guide_step == 3: st.session_state.guide_step = 4
            goi_ai(sug)
    st.markdown('</div>', unsafe_allow_html=True)

# Nhập liệu (Bước 1)
vung_in = "vung-mo" if st.session_state.guide_step in [2, 3, 4] else ""
st.markdown(f'<div class="{vung_in}">', unsafe_allow_html=True)
st.write("<br><br><br>", unsafe_allow_html=True)
if st.session_state.guide_step == 1: st.markdown('<div class="chi-dan" style="margin-left:100px;">👇 THỰC HÀNH: GÕ VÀO ĐÂY</div>', unsafe_allow_html=True)
with st.container():
    inp = st.chat_input("Nhập câu hỏi của bạn...")
    if inp: goi_ai(inp)
st.markdown('</div>', unsafe_allow_html=True)
