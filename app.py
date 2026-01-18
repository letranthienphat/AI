import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
import time
from io import BytesIO

# --- 1. GIAO DIỆN & STYLE CHUYÊN NGHIỆP ---
st.set_page_config(page_title="Nexus v35", layout="wide", page_icon="📝")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Lexend', sans-serif; }
    
    /* Chỉ dẫn thực hành cực kỹ */
    .mui-ten { color: #FF4B4B; font-weight: bold; animation: bounce 0.6s infinite alternate; }
    @keyframes bounce { from { transform: translateY(0); } to { transform: translateY(-8px); } }
    
    /* Làm mờ để tập trung thực hành */
    .vung-mo { opacity: 0.15; pointer-events: none; filter: blur(3px); }
    
    /* Khung nổi bật cho phần QR */
    .qr-download-box { border: 1px solid #00FFC2; padding: 10px; border-radius: 8px; background: #f0fffb; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE ---
for key in ['messages', 'suggestions', 'guide_step', 'huong_dan_xong', 'v_speed', 'key_id']:
    if key not in st.session_state:
        st.session_state[key] = {'messages': [], 'suggestions': [], 'guide_step': 0, 'huong_dan_xong': False, 'v_speed': 1.0, 'key_id': 0}[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HÀM XỬ LÝ DỮ LIỆU .TXT & QR ---
def convert_to_txt(messages):
    """Chuyển hội thoại thành định dạng text thuần túy"""
    output = ""
    for m in messages:
        role = "AI: " if m["role"] == "assistant" else "Bạn: "
        output += f"{role}{m['content']}\n\n"
    return output

def tao_anh_qr(text):
    qr = qrcode.make(text)
    buf = BytesIO()
    qr.save(buf, format="PNG")
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
        st.session_state.suggestions = ["Bạn tên là gì?", "Giúp tôi tóm tắt", "Dừng đọc lại"]
        st.session_state.key_id += 1
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.rerun()

# --- 4. SIDEBAR (BẢNG ĐIỀU KHIỂN & SAO LƯU .TXT) ---
with st.sidebar:
    st.header("🇻🇳 ĐIỀU KHIỂN NEXUS")
    
    if st.session_state.guide_step > 0:
        st.error(f"📍 THỰC HÀNH BƯỚC {st.session_state.guide_step}")
        task = ["", "Gõ lời chào.", "Nghe AI nói.", "Chọn gợi ý.", "Sao lưu file .txt hoặc nhập ảnh QR."][st.session_state.guide_step]
        st.write(task)
        
        if st.session_state.guide_step == 4:
            if st.button("🏁 XÁC NHẬN HOÀN TẤT", type="primary", use_container_width=True):
                st.session_state.messages = []; st.session_state.guide_step = 0; st.session_state.huong_dan_xong = True
                st.rerun()

    st.divider()
    st.subheader("💾 Sao lưu & Phục hồi (.txt)")
    # Xuất file .txt
    txt_data = convert_to_txt(st.session_state.messages)
    st.download_button("📤 Xuất file .txt", data=txt_data, file_name="nhat_ky_nexus.txt", use_container_width=True)
    
    # Nhập file .txt
    up_txt = st.file_uploader("📥 Nhập dữ liệu .txt", type="txt")
    if up_txt:
        # Xử lý đơn giản để đưa vào khung chat
        content = up_txt.getvalue().decode("utf-8")
        if st.button("🔄 Khôi phục văn bản"):
            st.session_state.messages.append({"role": "assistant", "content": f"Đã khôi phục dữ liệu từ file:\n\n{content}"})
            st.rerun()

    st.divider()
    st.subheader("📸 Nhập Mã QR (Ảnh)")
    up_img = st.file_uploader("Chọn ảnh JPG/PNG", type=["jpg", "png"])
    if up_img: st.image(up_img, caption="Mã QR đã nạp", use_container_width=True)

# --- 5. MÀN HÌNH CHÀO (GHI NHỚ) ---
if not st.session_state.huong_dan_xong and st.session_state.guide_step == 0:
    st.title("Nexus Master v35 💎")
    st.info("Chào bạn! Hãy thực hành 4 bước để làm chủ công cụ.")
    c1, c2 = st.columns(2)
    if c1.button("🚀 BẮT ĐẦU", type="primary", use_container_width=True): st.session_state.guide_step = 1; st.rerun()
    if c2.button("⏩ BỎ QUA", use_container_width=True): st.session_state.huong_dan_xong = True; st.rerun()
    st.checkbox("✔️ Ghi nhớ lựa chọn", value=True, key="save_me")

# --- 6. KHUNG CHAT & XUẤT ẢNH QR ---
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
                    # Xuất mã QR dưới dạng file ảnh PNG
                    qr_file = tao_anh_qr(m["content"][:250])
                    st.download_button("🖼️ Tải ảnh QR (PNG)", data=qr_file, file_name=f"qr_code_{i}.png", mime="image/png", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Gợi ý (Bước 3)
    if st.session_state.suggestions:
        s_blur = "vung-mo" if st.session_state.guide_step in [1, 2, 4] else ""
        st.markdown(f'<div class="{s_blur}">', unsafe_allow_html=True)
        if st.session_state.guide_step == 3: st.markdown('<div class="mui-ten">👇 CHỌN 1 GỢI Ý ĐỂ TIẾP TỤC</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for idx, sug in enumerate(st.session_state.suggestions):
            if cols[idx].button(sug, key=f"sug_{idx}_{st.session_state.key_id}"):
                if st.session_state.guide_step == 3: st.session_state.guide_step = 4
                goi_ai(sug)
        st.markdown('</div>', unsafe_allow_html=True)

    # Input (Bước 1)
    in_blur = "vung-mo" if st.session_state.guide_step in [2, 3, 4] else ""
    st.markdown(f'<div class="{in_blur}">', unsafe_allow_html=True)
    if st.session_state.guide_step == 1: st.markdown('<div class="mui-ten">👇 THỰC HÀNH: GÕ VÀO ĐÂY</div>', unsafe_allow_html=True)
    inp = st.chat_input("Nhập tin nhắn...")
    if inp: goi_ai(inp)
    st.markdown('</div>', unsafe_allow_html=True)
