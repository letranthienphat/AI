import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
from io import BytesIO

# --- 1. THIẾT LẬP HỆ ĐIỀU HÀNH SUNLIGHT (FORCE LIGHT MODE) ---
st.set_page_config(page_title="Nexus OS Genesis", layout="wide", page_icon="☀️")

st.markdown("""
    <style>
    /* Ép buộc màu sáng cấp độ cao nhất */
    :root { --primary: #0066FF; }
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    [data-testid="stHeader"], [data-testid="stSidebar"] {
        background-color: #F0F2F6 !important;
        border-right: 1px solid #E0E0E0;
    }
    
    /* Giao diện tin nhắn kiểu Apple Style */
    .stChatMessage {
        background-color: #F2F2F7 !important;
        border-radius: 20px !important;
        padding: 15px !important;
        margin-bottom: 15px !important;
        border: 1px solid #E5E5EA !important;
    }

    /* Bảng hướng dẫn trung tâm - Đột phá */
    .nexus-guide {
        position: fixed; top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        width: 85%; max-width: 400px;
        background: white; border: 4px solid #0066FF;
        border-radius: 30px; padding: 25px;
        z-index: 9999; text-align: center;
        box-shadow: 0 20px 50px rgba(0,0,0,0.3);
    }
    .nexus-guide h2 { color: #0066FF !important; }
    
    /* Hiệu ứng nhấp nháy cho nút cần bấm */
    .active-btn {
        border: 3px solid #FF3B30 !important;
        animation: pulse-red 1s infinite;
    }
    @keyframes pulse-red { 
        0% { box-shadow: 0 0 0 0px rgba(255, 59, 48, 0.7); }
        100% { box-shadow: 0 0 0 15px rgba(255, 59, 48, 0); }
    }

    /* Tối ưu nút bấm trên điện thoại */
    .stButton > button {
        height: 55px !important; border-radius: 18px !important;
        font-weight: 700 !important; font-size: 17px !important;
        transition: 0.3s !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE ---
for key in ['messages', 'guide_step', 'done', 'v_speed']:
    if key not in st.session_state:
        st.session_state[key] = {'messages': [], 'guide_step': 0, 'done': False, 'v_speed': 1.0}[key]

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. LOGIC HƯỚNG DẪN TẬN TÌNH ---
if st.session_state.guide_step > 0:
    titles = ["", "BƯỚC 1: LỜI CHÀO", "BƯỚC 2: NGHE THỬ", "BƯỚC 3: DỮ LIỆU", "BƯỚC 4: HOÀN TẤT"]
    tasks = [
        "",
        "Gõ <b>'Xin chào'</b> vào ô dưới cùng để kích hoạt AI.",
        "Nhấn nút <b>'🔊 NGHE'</b> để kiểm tra giọng nói.",
        "Nhấn <b>'🖼️ LƯU QR'</b> để tập xuất file hình ảnh.",
        "Mọi thứ đã sẵn sàng. Nhấn nút <b>'XÁC NHẬN'</b> để bắt đầu!"
    ]
    st.markdown(f"""
        <div class="nexus-guide">
            <h2>{titles[st.session_state.guide_step]}</h2>
            <p style="font-size: 1.1rem; color: #333;">{tasks[st.session_state.guide_step]}</p>
        </div>
    """, unsafe_allow_html=True)

# --- 4. HÀM XỬ LÝ CHÍNH ---
def process_chat(p):
    st.session_state.messages.append({"role": "user", "content": p})
    with st.chat_message("assistant"):
        placeholder = st.empty(); full = ""
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages], stream=True)
        for chunk in res:
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                placeholder.markdown(full + "▌")
        placeholder.markdown(full)
        st.session_state.messages.append({"role": "assistant", "content": full})
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.rerun()

# --- 5. GIAO DIỆN HỆ ĐIỀU HÀNH ---

# Màn hình bắt đầu
if not st.session_state.done and st.session_state.guide_step == 0:
    st.title("☀️ NEXUS OS: GENESIS")
    st.markdown("### Giao diện kỷ nguyên mới. Sáng hơn, mượt hơn.")
    if st.button("🚀 BẮT ĐẦU TRẢI NGHIỆM", type="primary", use_container_width=True):
        st.session_state.guide_step = 1; st.rerun()
    st.checkbox("✔️ Ghi nhớ lựa chọn và luôn mở chế độ sáng", value=True)

# Khu vực hiển thị tin nhắn
if st.session_state.done or st.session_state.guide_step > 0:
    # Làm mờ nếu đang ở các bước hướng dẫn
    blur_style = "filter: blur(8px); pointer-events: none;" if st.session_state.guide_step in [1, 4] else ""
    st.markdown(f'<div style="{blur_style}">', unsafe_allow_html=True)
    
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.write(m["content"])
            if m["role"] == "assistant":
                c1, c2, c3 = st.columns(3)
                with c1:
                    # Nút Nghe (Sẽ nhấp nháy ở bước 2)
                    if st.button("🔊 NGHE", key=f"v_{i}", use_container_width=True, type="primary" if st.session_state.guide_step == 2 else "secondary"):
                        if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
                with c2:
                    # Xuất QR (Sẽ nhấp nháy ở bước 3)
                    qr = qrcode.make(m["content"][:200]); buf = BytesIO(); qr.save(buf, format="PNG")
                    if st.download_button("🖼️ LƯU QR", data=buf.getvalue(), file_name="nexus_qr.png", use_container_width=True):
                        if st.session_state.guide_step == 3: st.session_state.guide_step = 4; st.rerun()
                with c3:
                    # Xuất file .txt sao lưu
                    txt_data = f"BẠN: {st.session_state.messages[-2]['content']}\nAI: {m['content']}"
                    st.download_button("📝 LƯU .TXT", data=txt_data, file_name="nexus_chat.txt", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Nút Xác nhận cuối cùng
    if st.session_state.guide_step == 4:
        st.write("<br>"*5, unsafe_allow_html=True)
        if st.button("🏁 XÁC NHẬN HOÀN TẤT", type="primary", use_container_width=True):
            st.session_state.messages = []; st.session_state.guide_step = 0; st.session_state.done = True
            st.rerun()

    # Thanh nhập liệu đáy màn hình
    st.markdown(f'<div style="{"opacity: 0.1;" if st.session_state.guide_step in [2, 3, 4] else ""}">', unsafe_allow_html=True)
    inp = st.chat_input("Hãy viết gì đó...")
    if inp: process_chat(inp)
    st.markdown('</div>', unsafe_allow_html=True)

# --- SIDEBAR (CHỈ DÀNH CHO CÀI ĐẶT SÂU) ---
with st.sidebar:
    st.subheader("⚙️ Cài đặt hệ thống")
    st.slider("Tốc độ giọng nói", 0.5, 2.0, 1.0)
    if st.button("🗑️ Xóa sạch hội thoại", use_container_width=True):
        st.session_state.messages = []; st.rerun()
