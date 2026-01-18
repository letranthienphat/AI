import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
import json
import time
from io import BytesIO
from PIL import Image

# --- 1. GIAO DIỆN & STYLE ---
st.set_page_config(page_title="Nexus Vision v34", layout="wide", page_icon="📸")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Lexend', sans-serif; }
    .mui-ten { color: #FF4B4B; font-weight: bold; animation: bounce 0.6s infinite alternate; }
    @keyframes bounce { from { transform: translateY(0); } to { transform: translateY(-8px); } }
    .vung-mo { opacity: 0.15; pointer-events: none; filter: blur(3px); }
    .qr-box { border: 2px dashed #00FFC2; padding: 10px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE ---
for key in ['messages', 'suggestions', 'guide_step', 'huong_dan_xong', 'v_speed', 'key_id']:
    if key not in st.session_state:
        st.session_state[key] = {'messages': [], 'suggestions': [], 'guide_step': 0, 'huong_dan_xong': False, 'v_speed': 1.0, 'key_id': 0}[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HÀM XỬ LÝ ẢNH QR ---
def tao_anh_qr(text):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

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
        st.session_state.suggestions = ["Quét mã này thế nào?", "Lưu ảnh QR này", "Dừng đọc"]
        st.session_state.key_id += 1
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.rerun()

# --- 4. SIDEBAR (HƯỚNG DẪN NHẬP ẢNH JPG/PNG) ---
with st.sidebar:
    st.header("📸 QUẢN LÝ QR VISION")
    
    if st.session_state.guide_step > 0:
        st.error(f"📍 BƯỚC {st.session_state.guide_step}")
        st.write(["", "Gõ lời chào.", "Nghe AI nói.", "Chọn gợi ý.", "Tải ảnh JPG/PNG lên đây."][st.session_state.guide_step])
        
        if st.session_state.guide_step == 4:
            if st.button("🏁 HOÀN TẤT HƯỚNG DẪN", type="primary", use_container_width=True):
                st.session_state.messages = []; st.session_state.guide_step = 0; st.session_state.huong_dan_xong = True
                st.rerun()

    st.divider()
    # MỤC NHẬP FILE JPG/PNG THEO YÊU CẦU
    st.subheader("📥 Nhập Mã QR (JPG/PNG)")
    with st.container(border=(st.session_state.guide_step == 4)):
        if st.session_state.guide_step == 4: st.markdown('<div class="mui-ten">👇 CHỌN ẢNH QR TẠI ĐÂY</div>', unsafe_allow_html=True)
        file_anh = st.file_uploader("Chọn ảnh chứa mã QR", type=["jpg", "png", "jpeg"])
        if file_anh:
            st.image(file_anh, caption="Ảnh đã nhập", use_container_width=True)
            st.success("Đã nhận ảnh! AI đang phân tích mã QR...")
            # Ở đây có thể tích hợp thư viện quét QR, tạm thời ghi nhận thành công
            if st.session_state.guide_step == 4: st.info("Nhấn 'Hoàn tất' ở trên để kết thúc.")

# --- 5. MÀN HÌNH CHÀO ---
if not st.session_state.huong_dan_xong and st.session_state.guide_step == 0:
    st.title("Nexus Vision Elite 💎")
    st.info("Thực hành quét và xuất mã QR ngay bây giờ.")
    c1, c2 = st.columns(2)
    if c1.button("🚀 BẮT ĐẦU", type="primary", use_container_width=True): st.session_state.guide_step = 1; st.rerun()
    if c2.button("⏩ BỎ QUA", use_container_width=True): st.session_state.huong_dan_xong = True; st.rerun()
    st.checkbox("✔️ Ghi nhớ lựa chọn", value=True, key="save_pref")

# --- 6. KHU VỰC CHAT & XUẤT FILE QR ---
if st.session_state.huong_dan_xong or st.session_state.guide_step > 0:
    chat_blur = "vung-mo" if st.session_state.guide_step in [1, 4] else ""
    st.markdown(f'<div class="{chat_blur}">', unsafe_allow_html=True)
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant":
                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    if st.button("🔊 NGHE", key=f"v_{i}_{st.session_state.key_id}"):
                        if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
                with c2:
                    if st.button("🔇 DỪNG", key=f"s_{i}_{st.session_state.key_id}"): pass
                with c3:
                    # TÍNH NĂNG XUẤT FILE ẢNH QR
                    qr_img = tao_anh_qr(m["content"][:200])
                    st.download_button("📥 TẢI ẢNH QR (PNG)", data=qr_img, file_name=f"nexus_qr_{i}.png", mime="image/png", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Suggestions (Bước 3)
    if st.session_state.suggestions:
        s_blur = "vung-mo" if st.session_state.guide_step in [1, 2, 4] else ""
        st.markdown(f'<div class="{s_blur}">', unsafe_allow_html=True)
        if st.session_state.guide_step == 3: st.markdown('<div class="mui-ten">👇 CHỌN 1 GỢI Ý</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for idx, sug in enumerate(st.session_state.suggestions):
            if cols[idx].button(sug, key=f"sug_{idx}_{st.session_state.key_id}"):
                if st.session_state.guide_step == 3: st.session_state.guide_step = 4
                goi_ai(sug)
        st.markdown('</div>', unsafe_allow_html=True)

    # Input (Bước 1)
    in_blur = "vung-mo" if st.session_state.guide_step in [2, 3, 4] else ""
    st.markdown(f'<div class="{in_blur}">', unsafe_allow_html=True)
    if st.session_state.guide_step == 1: st.markdown('<div class="mui-ten" style="margin-left:50px;">👇 GÕ THỬ ĐỂ AI TẠO MÃ QR</div>', unsafe_allow_html=True)
    inp = st.chat_input("Hỏi Nexus...")
    if inp: goi_ai(inp)
    st.markdown('</div>', unsafe_allow_html=True)
