import streamlit as st
from openai import OpenAI
import time

# --- 1. SIÊU GIAO DIỆN DYNAMIC FLOW ---
st.set_page_config(page_title="Nexus Flow OS v130", layout="wide")

st.markdown("""
    <style>
    /* Hình nền động Aurora Flow */
    @keyframes gradient { 0% {background-position: 0% 50%;} 50% {background-position: 100% 50%;} 100% {background-position: 0% 50%;} }
    .stApp {
        background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #00d2ff) !important;
        background-size: 400% 400% !important;
        animation: gradient 15s ease infinite !important;
    }

    /* Thẻ tin nhắn Glassmorphism */
    .ai-bubble {
        background: rgba(255, 255, 255, 0.95);
        color: #000000 !important;
        padding: 20px; border-radius: 15px;
        margin-bottom: 10px; border-left: 10px solid #00d2ff;
        font-size: 18px; font-weight: 600;
    }

    /* Thanh gợi ý cuộn ngang */
    .sug-container {
        display: flex; overflow-x: auto; white-space: nowrap;
        gap: 10px; padding: 10px 0; scrollbar-width: none;
    }
    .sug-chip {
        background: rgba(0, 210, 255, 0.2);
        border: 1px solid #00d2ff; color: white !important;
        padding: 5px 15px; border-radius: 20px; font-size: 13px;
    }

    /* Ô nhập PIN kiểu điện thoại */
    .pin-input input {
        text-align: center; font-size: 24px !important;
        border-radius: 10px !important; border: 2px solid #00d2ff !important;
        background: white !important; color: black !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO TRẠNG THÁI ---
if 'page' not in st.session_state:
    st.session_state.update({
        'page': 'auth', 'user': '', 'messages': [], 'scroll_speed': 2,
        'ok_clicks': 0, 'admin_unlocked': False, 'show_all_sugs': False
    })

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. HÀM TỰ ĐỘNG CUỘN (AUTO-SCROLL JS) ---
def auto_scroll():
    js = f"""
    <script>
        var body = window.parent.document.querySelector(".main");
        body.scrollTo({{ top: body.scrollHeight, behavior: 'smooth' }});
    </script>
    """
    st.components.v1.html(js, height=0)

# --- 4. MÀN HÌNH ĐĂNG NHẬP (GIAO DIỆN MỚI) ---
if st.session_state.page == 'auth':
    st.title("🛡️ NEXUS GATEWAY")
    name = st.text_input("Tên định danh:", placeholder="Nhập tên sử dụng...")
    mode = st.selectbox("Vai trò:", ["Đăng ký", "Khách"])
    
    if st.button("KHỞI CHẠY HỆ THỐNG", use_container_width=True):
        if name:
            st.session_state.user = name
            st.session_state.page = 'launcher'
            st.rerun()

# --- 5. MÀN HÌNH CHỌN APP ---
elif st.session_state.page == 'launcher':
    col_logo, _ = st.columns([1, 10])
    if col_logo.button("💎"): 
        st.session_state.page = 'hidden_menu'
        st.rerun()
    
    st.title(f"Xin chào, {st.session_state.user}")
    col1, col2 = st.columns(2)
    if col1.button("🤖\nTRÍ TUỆ AI"): st.session_state.page = 'ai'; st.rerun()
    if col2.button("⚙️\nCÀI ĐẶT"): st.session_state.page = 'settings'; st.rerun()

# --- 6. ỨNG DỤNG AI (STREAMING & DYNAMIC SUGGESTIONS) ---
elif st.session_state.page == 'ai':
    st.title("🤖 Nexus AI Core")
    if st.button("⬅️ Quay lại"): st.session_state.page = 'launcher'; st.rerun()

    # Hiển thị lịch sử chat
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            if m["role"] == "assistant":
                st.markdown(f'<div class="ai-bubble">{m["content"]}</div>', unsafe_allow_html=True)
            else: st.write(m["content"])

    # GỢI Ý ĐỘNG (Dynamic Chips)
    sug_list = ["Kế hoạch 2026", "Học AI", "Viết Code Python", "Dịch thuật", "Sáng tác nhạc", "Kể chuyện đêm khuya"]
    st.write("✨ Gợi ý nhanh:")
    
    # Khu vực gợi ý nhỏ gọn
    sug_cols = st.columns([8, 1])
    with sug_cols[0]:
        # Giả lập thanh cuộn bằng nút nhỏ
        s_cols = st.columns(4)
        for idx, s in enumerate(sug_list[:4]):
            if s_cols[idx].button(f"🔹 {s}", key=f"s_{idx}"):
                prompt = s
                # Logic gọi AI nằm bên dưới
    with sug_cols[1]:
        if st.button("..."): st.session_state.show_all_sugs = not st.session_state.show_all_sugs
    
    if st.session_state.show_all_sugs:
        st.info("💡 Tất cả gợi ý: " + ", ".join(sug_list))

    # NHẬP LIỆU & STREAMING
    inp = st.chat_input("Hỏi bất cứ điều gì...")
    if inp:
        st.session_state.messages.append({"role": "user", "content": inp})
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            
            # STREAMING TRỰC TIẾP
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content.replace("**", "")
                    full_response += text
                    placeholder.markdown(f'<div class="ai-bubble">{full_response} ▌</div>', unsafe_allow_html=True)
                    # Tự động cuộn dựa theo tốc độ đọc
                    time.sleep(0.05 / st.session_state.scroll_speed) 
                    auto_scroll()
            
            placeholder.markdown(f'<div class="ai-bubble">{full_response}</div>', unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.rerun()

# --- 7. CÀI ĐẶT & XEM TRƯỚC TỐC ĐỘ ---
elif st.session_state.page == 'settings':
    st.title("⚙️ Trung tâm điều khiển")
    if st.button("🏠 Quay lại"): st.session_state.page = 'launcher'; st.rerun()
    
    st.subheader("⏱️ Tốc độ Auto-Scroll")
    speed = st.slider("Điều chỉnh (1x - 5x):", 1, 5, st.session_state.scroll_speed)
    st.session_state.scroll_speed = speed
    
    st.write("🔍 Xem trước tốc độ cuộn:")
    st.info("Dòng chữ này sẽ được cuộn lên khi có nội dung mới xuất hiện...")

# --- 8. MENU MẬT MÃ (OTP STYLE) ---
elif st.session_state.page == 'hidden_menu':
    st.title("Nhập mã PIN")
    st.write("Giao diện bảo mật 4-lớp")
    
    # OTP Input Style
    c_pin = st.columns(4)
    v1 = c_pin[0].text_input("", key="v1", max_chars=1, help="Số 1")
    v2 = c_pin[1].text_input("", key="v2", max_chars=1, help="Số 2")
    v3 = c_pin[2].text_input("", key="v3", max_chars=1, help="Số 3")
    v4 = c_pin[3].text_input("", key="v4", max_chars=1, help="Số 4")

    # Logic Nút OK (Mờ nếu chưa nhập đủ, trừ khi dùng mẹo)
    ready = all([v1, v2, v3, v4])
    is_trick = not any([v1, v2, v3, v4])

    if st.button("XÁC NHẬN OK", disabled=(not ready and not is_trick)):
        if is_trick:
            st.session_state.ok_clicks += 1
            if st.session_state.ok_clicks >= 4:
                st.session_state.admin_unlocked = True
        else:
            st.error("PIN không hợp lệ.")

    if st.session_state.admin_unlocked:
        st.success("🔓 ADMIN ACCESS GRANTED")
        if st.button("🚫 CHẶN THIẾT BỊ"): st.warning("Đã chặn.")
    
    if st.button("Thoát"): 
        st.session_state.page = 'launcher'
        st.session_state.ok_clicks = 0
        st.rerun()
