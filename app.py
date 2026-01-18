import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import qrcode
import time
from io import BytesIO

# --- 1. ÉP BUỘC GIAO DIỆN SÁNG & TỐI ƯU MOBILE ---
st.set_page_config(page_title="Nexus Sunlight v36", layout="wide", page_icon="☀️")

st.markdown("""
    <style>
    /* Ép giao diện luôn sáng */
    :root { --primary-color: #007BFF; }
    .stApp { background-color: #FFFFFF !important; color: #1A1A1A !important; }
    [data-testid="stSidebar"] { background-color: #F8F9FA !important; }
    p, h1, h2, h3, span, label { color: #1A1A1A !important; }
    
    /* Box hướng dẫn trung tâm (Cực kỹ cho điện thoại) */
    .guide-overlay {
        position: fixed; top: 15%; left: 5%; right: 5%;
        background: #007BFF; color: white !important;
        padding: 20px; border-radius: 20px;
        z-index: 1000; box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        text-align: center; border: 3px solid #FFFFFF;
    }
    .guide-overlay p, .guide-overlay b { color: white !important; }
    
    /* Nút bấm Mobile to và rõ */
    .stButton > button {
        width: 100%; border-radius: 15px !important;
        padding: 12px !important; font-size: 16px !important;
        background: #FFFFFF !important; border: 1px solid #DDD !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Mũi tên chỉ dẫn nhấp nháy */
    .mui-ten-mobile {
        color: #FF4B4B; font-size: 30px; text-align: center;
        animation: bounce 0.6s infinite alternate;
    }
    @keyframes bounce { from { transform: translateY(0); } to { transform: translateY(-10px); } }
    
    /* Vùng mờ */
    .vung-mo { opacity: 0.1; pointer-events: none; filter: blur(5px); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE ---
for key in ['messages', 'suggestions', 'guide_step', 'huong_dan_xong', 'v_speed', 'key_id']:
    if key not in st.session_state:
        st.session_state[key] = {'messages': [], 'suggestions': [], 'guide_step': 0, 'huong_dan_xong': False, 'v_speed': 1.0, 'key_id': 0}[key]

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
        st.session_state.suggestions = ["Bạn tên là gì?", "Tạo mã QR này", "Dừng đọc"]
        st.session_state.key_id += 1
        if st.session_state.guide_step == 1: st.session_state.guide_step = 2
        st.rerun()

# --- 4. HỆ THỐNG HƯỚNG DẪN NỔI (OVERLAY) ---
if st.session_state.guide_step > 0:
    noi_dung = [
        "",
        "🎯 BƯỚC 1: Hãy gõ 'Xin chào' vào ô chát dưới cùng màn hình để bắt đầu.",
        "🔊 BƯỚC 2: Rất tốt! Bây giờ hãy nhấn nút 'NGHE' bên dưới câu trả lời của tôi.",
        "✨ BƯỚC 3: Tuyệt vời! Hãy chọn 1 câu hỏi gợi ý để xem cách tôi trả lời nhanh.",
        "💾 BƯỚC 4: Cuối cùng, hãy nhấn nút 'XÁC NHẬN' phía dưới để lưu cấu hình."
    ]
    st.markdown(f"""
        <div class="guide-overlay">
            <b>HƯỚNG DẪN THỰC HÀNH</b><br>
            <p>{noi_dung[st.session_state.guide_step]}</p>
        </div>
    """, unsafe_allow_html=True)

# --- 5. GIAO DIỆN CHÍNH ---
st.title("☀️ Nexus Sunlight")

# Màn hình chào (Chỉ hiện khi chưa xong hướng dẫn)
if not st.session_state.huong_dan_xong and st.session_state.guide_step == 0:
    st.markdown("### Chào mừng bạn! 💎")
    st.write("Giao diện đã được tối ưu cho điện thoại và luôn sáng để bạn dễ quan sát.")
    if st.button("🚀 BẮT ĐẦU THỰC HÀNH (4 BƯỚC)", type="primary"):
        st.session_state.guide_step = 1; st.rerun()
    if st.button("⏩ BỎ QUA"):
        st.session_state.huong_dan_xong = True; st.rerun()
    st.checkbox("✔️ Ghi nhớ lựa chọn", value=True, key="save_mode")

# KHU VỰC CHAT
if st.session_state.huong_dan_xong or st.session_state.guide_step > 0:
    # 1. Danh sách chat
    chat_blur = "vung-mo" if st.session_state.guide_step in [1, 4] else ""
    st.markdown(f'<div class="{chat_blur}">', unsafe_allow_html=True)
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant":
                if st.session_state.guide_step == 2: st.markdown('<div class="mui-ten-mobile">👆 BẤM ĐỂ NGHE</div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🔊 NGHE", key=f"v_{i}_{st.session_state.key_id}"):
                        if st.session_state.guide_step == 2: st.session_state.guide_step = 3; st.rerun()
                with c2:
                    qr_file = qrcode.make(m["content"][:200])
                    buf = BytesIO(); qr_file.save(buf, format="PNG")
                    st.download_button("🖼️ LƯU QR", data=buf.getvalue(), file_name=f"qr_{i}.png", mime="image/png")
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. Gợi ý (Mobile Grid)
    if st.session_state.suggestions:
        s_blur = "vung-mo" if st.session_state.guide_step in [1, 2, 4] else ""
        st.markdown(f'<div class="{s_blur}">', unsafe_allow_html=True)
        st.divider()
        if st.session_state.guide_step == 3: st.markdown('<div class="mui-ten-mobile">👇 CHỌN 1 CÂU</div>', unsafe_allow_html=True)
        for idx, sug in enumerate(st.session_state.suggestions):
            if st.button(f"✨ {sug}", key=f"s_{idx}_{st.session_state.key_id}"):
                if st.session_state.guide_step == 3: st.session_state.guide_step = 4; st.rerun()
                goi_ai(sug)
    st.markdown('</div>', unsafe_allow_html=True)

    # 3. Nút xác nhận hoàn tất (Bước 4 - Hiện to giữa màn hình chat)
    if st.session_state.guide_step == 4:
        st.write("<br><br>", unsafe_allow_html=True)
        if st.button("🏁 XÁC NHẬN HOÀN TẤT & SAO LƯU .TXT", type="primary"):
            # Logic xuất file .txt (giả lập)
            st.session_state.messages = []; st.session_state.guide_step = 0; st.session_state.huong_dan_xong = True
            st.rerun()

    # 4. Input đáy màn hình
    in_blur = "vung-mo" if st.session_state.guide_step in [2, 3, 4] else ""
    st.markdown(f'<div class="{in_blur}">', unsafe_allow_html=True)
    if st.session_state.guide_step == 1: st.markdown('<div class="mui-ten-mobile">👇 GÕ TẠI ĐÂY</div>', unsafe_allow_html=True)
    inp = st.chat_input("Nhập tin nhắn...")
    if inp: goi_ai(inp)
    st.markdown('</div>', unsafe_allow_html=True)
