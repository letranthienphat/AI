import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder, speech_to_text

# --- 1. GIAO DIỆN SÓNG ĐỘNG (DYNAMIC OCEAN) ---
st.set_page_config(page_title="Nexus Core v100", layout="wide")

st.markdown("""
    <style>
    @keyframes move { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    .stApp {
        background: linear-gradient(-45deg, #00c6ff, #0072ff, #3a1c71, #d76d77) !important;
        background-size: 400% 400% !important;
        animation: move 10s ease infinite !important;
    }
    /* Chữ Đen Tuyền - Tuyệt đối không bị mờ */
    h1, h2, h3, p, b, span, .stMarkdown { color: #000000 !important; font-weight: 800 !important; }
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px; padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin-bottom: 15px; border: 2px solid #FFFFFF;
    }
    .stButton > button {
        background: #FFFFFF !important; color: #0072ff !important;
        border: 2px solid #0072ff !important; border-radius: 15px !important;
        font-weight: bold !important; width: 100%; height: 60px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. QUẢN LÝ TRẠNG THÁI ---
if 'page' not in st.session_state:
    st.session_state.update({'page': 'launcher', 'messages': [], 'guide_step': 0, 'done': False})

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HƯỚNG DẪN TRÊN MÀN HÌNH ---
if st.session_state.guide_step > 0 and not st.session_state.done:
    steps = ["", "Bấm chọn '🤖 TRÍ TUỆ AI'", "Gõ tin nhắn bất kỳ", "Bấm 'LƯU TXT' (Mẫu)"]
    st.error(f"🎯 HƯỚNG DẪN: {steps[st.session_state.guide_step]}")

# --- 4. APP LAUNCHER (MÀN HÌNH CHỌN APP) ---
if st.session_state.page == 'launcher':
    st.title("🚀 NEXUS WORKSPACE")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖\nTRÍ TUỆ AI"):
            st.session_state.page = 'ai'
            if st.session_state.guide_step == 1: st.session_state.guide_step = 2
            st.rerun()
    with col2:
        if st.button("⚙️\nCÀI ĐẶT"): st.session_state.page = 'settings'; st.rerun()
    
    if st.session_state.guide_step == 0 and not st.session_state.done:
        if st.button("🌟 BẮT ĐẦU HƯỚNG DẪN"): st.session_state.guide_step = 1; st.rerun()

# --- 5. APP TRÍ TUỆ AI (CHÍNH) ---
elif st.session_state.page == 'ai':
    st.title("🤖 TRÍ TUỆ AI")
    if st.button("⬅️ THOÁT RA MÀN HÌNH CHÍNH"): st.session_state.page = 'launcher'; st.rerun()

    # Hiển thị hội thoại
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"]):
            st.markdown(f"**{m['content']}**")
            if m["role"] == "assistant":
                if st.session_state.guide_step == 3:
                    if st.button("📄 LƯU TXT (MẪU)"):
                        st.success("✅ Tuyệt vời! Bạn đã biết cách lưu dữ liệu. Hướng dẫn kết thúc.")
                        st.session_state.done = True; st.session_state.guide_step = 0; st.rerun()
                else:
                    st.download_button("📝 TẢI TXT", data=m['content'], file_name="chat.txt", key=f"dl_{i}")

    # GỢI Ý THÔNG MINH
    st.markdown("### ✨ Gợi ý cho bạn:")
    cols = st.columns(3)
    sugs = ["Kể chuyện hài", "Lập kế hoạch học tập", "Dịch sang tiếng Anh"]
    for idx, s in enumerate(sugs):
        if cols[idx].button(s):
            prompt = s
            st.session_state.messages.append({"role": "user", "content": prompt})
            # GỌI AI NGAY LẬP TỨC
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages])
            st.session_state.messages.append({"role": "assistant", "content": res.choices[0].message.content})
            st.rerun()

    # NHẬP LIỆU CHÍNH
    inp = st.chat_input("Hỏi AI ngay tại đây...")
    if inp:
        st.session_state.messages.append({"role": "user", "content": inp})
        if st.session_state.guide_step == 2: st.session_state.guide_step = 3
        # XỬ LÝ AI PHẢN HỒI
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages])
        st.session_state.messages.append({"role": "assistant", "content": res.choices[0].message.content})
        st.rerun()

# --- 6. APP CÀI ĐẶT ---
elif st.session_state.page == 'settings':
    st.title("⚙️ CÀI ĐẶT")
    if st.button("⬅️ QUAY LẠI"): st.session_state.page = 'launcher'; st.rerun()
    st.write("Cấu hình hệ thống tại đây.")
