import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
import json
import time
from io import BytesIO

# --- 1. GIAO DIỆN SUNLIGHT HIGH-CONTRAST (CHỐNG MẤT CHỮ) ---
st.set_page_config(page_title="Nexus Prime v45", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    /* Ép buộc nền trắng và chữ ĐEN ĐẬM */
    :root { --primary: #0044FF; }
    .stApp { background-color: #FFFFFF !important; }
    
    /* Đảm bảo chữ luôn đen rõ nét */
    p, span, h1, h2, h3, label, div { color: #000000 !important; font-weight: 500; }
    .stMarkdown p { color: #111111 !important; line-height: 1.6; }
    
    /* Sidebar nổi bật với màu sắc mạnh */
    [data-testid="stSidebar"] {
        background-color: #F0F2F5 !important;
        border-right: 3px solid #0044FF !important;
    }
    .stSidebar [data-testid="stButton"] button {
        background-color: #0044FF !important;
        color: white !important;
        border-radius: 12px;
        border: 2px solid #002288;
        font-weight: bold;
    }
    
    /* Box hướng dẫn trung tâm màu đỏ nổi bật */
    .huong-dan-ar {
        background: #FFEBEE; border: 3px solid #D32F2F;
        padding: 20px; border-radius: 20px;
        text-align: center; margin-bottom: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .huong-dan-ar b { color: #D32F2F !important; font-size: 1.2rem; }

    /* Nút bấm tin nhắn */
    .msg-btn { border-radius: 10px !important; margin-top: 10px; }
    
    /* Vùng mờ để thực hành */
    .blur-focus { opacity: 0.1; pointer-events: none; filter: blur(4px); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO DỮ LIỆU ---
for key in ['messages', 'guide_step', 'huong_dan_xong', 'v_speed', 'key_id']:
    if key not in st.session_state:
        st.session_state[key] = {'messages': [], 'guide_step': 0, 'huong_dan_xong': False, 'v_speed': 1.0, 'key_id': 0}[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HÀM XỬ LÝ (QR, TEXT, AI) ---
def tao_qr_anh(text):
    qr = qrcode.make(text)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def goi_ai(p):
    st.session_state.messages.append({"role": "user", "content": p})
    with st.chat_message("assistant"):
        placeholder = st.empty(); full = ""
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages], stream=True)
        for chunk in res:
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                placeholder.markdown(f"**{full}**") # Chữ đậm cho rõ
        st.session_state.messages.append({"role": "assistant", "content": full})
        st.session_state.key_id += 1
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.rerun()

# --- 4. SIDEBAR - TÍNH NĂNG CŨ & MỚI ---
with st.sidebar:
    st.title("🛡️ NEXUS MENU")
    
    st.subheader("🔊 Giọng nói")
    st.session_state.v_speed = st.slider("Tốc độ", 0.5, 2.0, 1.0)
    if st.button("🛑 DỪNG ĐỌC TỨC THÌ", use_container_width=True):
        st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)

    st.divider()
    st.subheader("📂 Dữ liệu .TXT")
    # Xuất file TXT
    full_txt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
    st.download_button("📤 XUẤT FILE .TXT", data=full_txt, file_name="nexus_backup.txt", use_container_width=True)
    
    # Nhập file TXT
    up_txt = st.file_uploader("📥 NHẬP FILE .TXT", type="txt")
    if up_txt and st.button("🔄 KHÔI PHỤC NGAY", use_container_width=True):
        content = up_txt.getvalue().decode("utf-8")
        st.session_state.messages.append({"role": "assistant", "content": f"Dữ liệu đã nạp:\n{content}"})
        st.rerun()

    st.divider()
    if st.button("🗑️ XÓA TOÀN BỘ CHAT", type="secondary", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# --- 5. HƯỚNG DẪN TRÊN MÀN HÌNH CHÍNH ---
if st.session_state.guide_step > 0:
    tasks = ["", 
             "👇 BƯỚC 1: Gõ 'Chào Nexus' vào ô phía dưới màn hình.", 
             "🔊 BƯỚC 2: Nhấn nút 'NGHE' dưới câu trả lời AI.", 
             "🖼️ BƯỚC 3: Nhấn 'LƯU QR' để tải ảnh mã hóa về máy.", 
             "🏁 BƯỚC 4: Nhấn nút 'HOÀN TẤT' rực rỡ bên dưới."]
    st.markdown(f"""<div class="huong-dan-ar"><b>📍 NHIỆM VỤ</b><br>{tasks[st.session_state.guide_step]}</div>""", unsafe_allow_html=True)

# --- 6. GIAO DIỆN CHAT CHÍNH ---
if not st.session_state.huong_dan_xong and st.session_state.guide_step == 0:
    st.title("Nexus Prime Elite 💎")
    st.write("Chào mừng bạn! Hệ thống đã sẵn sàng với độ tương phản cao nhất.")
    c1, c2 = st.columns(2)
    if c1.button("🚀 BẮT ĐẦU HƯỚNG DẪN", type="primary", use_container_width=True):
        st.session_state.guide_step = 1; st.rerun()
    if c2.button("⏩ BỎ QUA", use_container_width=True):
        st.session_state.huong_dan_xong = True; st.rerun()
    st.checkbox("✔️ Ghi nhớ lựa chọn luôn mở sáng", value=True, key="save_v45")

if st.session_state.huong_dan_xong or st.session_state.guide_step > 0:
    # Vùng chat (Mờ khi đang ở bước 1/4)
    chat_blur = "blur-focus" if st.session_state.guide_step in [1, 4] else ""
    st.markdown(f'<div class="{chat_blur}">', unsafe_allow_html=True)
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(f"**{m['content']}**")
            if m["role"] == "assistant":
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"🔊 NGHE", key=f"v_{i}_{st.session_state.key_id}"):
                        js = f"<script>window.speechSynthesis.cancel(); var u=new SpeechSynthesisUtterance('{m['content'].replace(chr(10), ' ')}'); u.lang='vi-VN'; u.rate={st.session_state.v_speed}; window.speechSynthesis.speak(u);</script>"
                        st.components.v1.html(js, height=0)
                        if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
                with col2:
                    qr_img = tao_qr_anh(m["content"][:250])
                    if st.download_button(f"🖼️ LƯU QR", data=qr_img, file_name=f"qr_{i}.png", mime="image/png", key=f"q_{i}"):
                        if st.session_state.guide_step == 3: st.session_state.guide_step = 4; st.rerun()
                with col3:
                    st.download_button("📝 TXT", data=m['content'], file_name="chat.txt", key=f"t_{i}")
    st.markdown('</div>', unsafe_allow_html=True)

    # Nút Hoàn tất Bước 4
    if st.session_state.guide_step == 4:
        st.write("<br>"*2, unsafe_allow_html=True)
        if st.button("🏁 HOÀN TẤT VÀ XÓA LỊCH SỬ NHÁP", type="primary", use_container_width=True):
            st.session_state.messages = []; st.session_state.guide_step = 0; st.session_state.huong_dan_xong = True
            st.rerun()

    # Input (Mờ khi ở các bước trung gian)
    in_blur = "blur-focus" if st.session_state.guide_step in [2, 3, 4] else ""
    st.markdown(f'<div class="{in_blur}">', unsafe_allow_html=True)
    inp = st.chat_input("Viết tin nhắn cho Nexus...")
    if inp: goi_ai(inp)
    st.markdown('</div>', unsafe_allow_html=True)
