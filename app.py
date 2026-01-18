import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import json
import time

# --- 1. GIAO DIỆN & STYLE ---
st.set_page_config(page_title="Nexus Stability v33", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Lexend', sans-serif; }
    
    /* Chỉ dẫn cực kỳ rõ ràng */
    .spotlight { border: 3px solid #00FFC2 !important; box-shadow: 0 0 15px #00FFC2; border-radius: 10px; padding: 5px; }
    .mui-ten { color: #FF4B4B; font-weight: bold; animation: bounce 0.6s infinite alternate; margin-bottom: 5px; }
    @keyframes bounce { from { transform: translateY(0); } to { transform: translateY(-8px); } }
    .vung-mo { opacity: 0.15; pointer-events: none; filter: blur(3px); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE (TÁCH BIỆT LOGIC) ---
# Dùng "huong_dan_xong" để kiểm soát hiển thị thay vì phụ thuộc trực tiếp vào checkbox
for key in ['messages', 'suggestions', 'guide_step', 'huong_dan_xong', 'v_speed', 'key_id']:
    if key not in st.session_state:
        st.session_state[key] = {
            'messages': [], 'suggestions': [], 'guide_step': 0, 
            'huong_dan_xong': False, 'v_speed': 1.0, 'key_id': 0
        }[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HÀM XỬ LÝ ---
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
        st.session_state.suggestions = ["Bạn khỏe không?", "Giải thích về AI", "Kể chuyện vui"]
        st.session_state.key_id += 1 # Đổi key để không bị trùng nút
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.rerun()

# --- 4. THANH ĐIỀU KHIỂN (SIDEBAR) ---
with st.sidebar:
    st.header("🇻🇳 BẢNG ĐIỀU KHIỂN")
    
    if st.session_state.guide_step > 0:
        st.error(f"📍 THỰC HÀNH: BƯỚC {st.session_state.guide_step}")
        st.write(["", "Gõ lời chào bên dưới.", "Nhấn nút '🔊 NGHE' ở tin nhắn AI.", "Nhấn vào 1 nút 'Gợi ý'.", "Kéo file vào ô dưới rồi nhấn Xong."][st.session_state.guide_step])
        
        if st.session_state.guide_step == 4:
            if st.button("🏁 HOÀN TẤT & XÓA NHÁP", type="primary", use_container_width=True):
                st.session_state.messages = []; st.session_state.guide_step = 0; st.session_state.huong_dan_xong = True
                st.rerun()

    st.divider()
    st.session_state.v_speed = st.slider("Tốc độ đọc", 0.5, 2.0, 1.0)
    
    # Khu vực Nhập file (Chỉ sáng ở bước 4)
    st.subheader("📂 Dữ liệu")
    with st.container(border=(st.session_state.guide_step == 4)):
        if st.session_state.guide_step == 4: st.markdown('<div class="mui-ten">👇 KÉO FILE VÀO ĐÂY</div>', unsafe_allow_html=True)
        up = st.file_uploader("Nhập file JSON", type="json")
        if up: st.success("Đã nhận file! Nhấn 'Hoàn tất' ở trên.")

# --- 5. GIAO DIỆN CHÀO MỪNG (CẢI TIẾN AN TOÀN) ---
# Chỉ hiện màn hình chào nếu CHƯA làm hướng dẫn xong VÀ CHƯA ở trong các bước hướng dẫn
if not st.session_state.huong_dan_xong and st.session_state.guide_step == 0:
    st.title("Chào mừng bạn đến với Nexus Elite")
    st.info("Hãy dành 1 phút để thực hành 4 bước sử dụng cơ bản.")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 BẮT ĐẦU THỰC HÀNH", type="primary", use_container_width=True):
            st.session_state.guide_step = 1; st.rerun()
    with c2:
        if st.button("⏩ BỎ QUA", use_container_width=True):
            st.session_state.huong_dan_xong = True; st.rerun()
    
    # Dấu tick ghi nhớ - Sử dụng key cố định để tránh mất giao diện
    ghi_nho = st.checkbox("✔️ Ghi nhớ lựa chọn (Không hỏi lại lần sau)", value=True, key="cb_ghi_nho")
    if ghi_nho and st.session_state.huong_dan_xong:
        # Nếu đã làm xong và có tick, lưu trạng thái vĩnh viễn (giả lập)
        pass

# --- 6. KHU VỰC CHAT CHÍNH (LUÔN HIỆN HỮU) ---
# Giao diện chat chỉ ẩn khi màn hình chào đang hiện. Một khi đã "Bắt đầu" hoặc "Bỏ qua", nó sẽ hiện mãi mãi.
if st.session_state.huong_dan_xong or st.session_state.guide_step > 0:
    
    # Chat History
    chat_blur = "vung-mo" if st.session_state.guide_step in [1, 4] else ""
    st.markdown(f'<div class="{chat_blur}">', unsafe_allow_html=True)
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant":
                if st.session_state.guide_step == 2: st.markdown('<div class="mui-ten">👆 BẤM ĐỂ NGHE</div>', unsafe_allow_html=True)
                c1, c2, _ = st.columns([1,1,4])
                with c1:
                    if st.button("🔊 NGHE", key=f"v_{i}_{st.session_state.key_id}"):
                        js = f"<script>window.speechSynthesis.cancel(); var u=new SpeechSynthesisUtterance('{m['content'].replace(chr(10), ' ')}'); u.lang='vi-VN'; u.rate={st.session_state.v_speed}; window.speechSynthesis.speak(u);</script>"
                        st.components.v1.html(js, height=0)
                        if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
                with c2:
                    if st.button("🔇 DỪNG", key=f"s_{i}_{st.session_state.key_id}"):
                        st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)
    st.markdown('</div>', unsafe_allow_html=True)

    # Suggestions
    if st.session_state.suggestions:
        sug_blur = "vung-mo" if st.session_state.guide_step in [1, 2, 4] else ""
        st.markdown(f'<div class="{sug_blur}">', unsafe_allow_html=True)
        if st.session_state.guide_step == 3: st.markdown('<div class="mui-ten">👇 CHỌN 1 CÂU GỢI Ý</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for idx, sug in enumerate(st.session_state.suggestions):
            if cols[idx].button(sug, key=f"sug_{idx}_{st.session_state.key_id}", use_container_width=True):
                if st.session_state.guide_step == 3: st.session_state.guide_step = 4
                goi_ai(sug)
        st.markdown('</div>', unsafe_allow_html=True)

    # Input Area
    in_blur = "vung-mo" if st.session_state.guide_step in [2, 3, 4] else ""
    st.markdown(f'<div class="{in_blur}">', unsafe_allow_html=True)
    if st.session_state.guide_step == 1: st.markdown('<div class="mui-ten" style="margin-left:100px;">👇 GÕ THỬ TẠI ĐÂY</div>', unsafe_allow_html=True)
    inp = st.chat_input("Nhập câu hỏi...")
    if inp: goi_ai(inp)
    st.markdown('</div>', unsafe_allow_html=True)
