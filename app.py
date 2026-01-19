import streamlit as st
from openai import OpenAI

# --- 1. GIAO DIỆN SÓNG ĐỘNG (DYNAMIC AURORA) ---
st.set_page_config(page_title="Nexus Sentinel v120", layout="wide")

st.markdown("""
    <style>
    @keyframes move { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    .stApp {
        background: linear-gradient(-45deg, #00c6ff, #0072ff, #3a1c71, #d76d77) !important;
        background-size: 400% 400% !important;
        animation: move 12s ease infinite !important;
    }
    /* Sửa lỗi nút bấm cao 120px bằng CSS */
    div.stButton > button {
        height: 120px !important;
        border-radius: 20px !important;
        background: rgba(255, 255, 255, 0.9) !important;
        color: #000000 !important;
        font-weight: 800 !important;
        font-size: 20px !important;
        border: 2px solid #FFFFFF !important;
    }
    /* Typography AI: Chữ đen tuyền, sạch sẽ cho giọng đọc mượt */
    .ai-bubble {
        background: rgba(255, 255, 255, 0.98);
        border-radius: 15px; padding: 25px;
        color: #000000 !important; font-size: 1.15rem;
        line-height: 1.7; border-left: 8px solid #0072ff;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    /* Giao diện nhập PIN 4 số ngang */
    .pin-row { display: flex; gap: 10px; justify-content: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE (CHỐNG LỖI) ---
if 'page' not in st.session_state:
    st.session_state.update({
        'page': 'auth', 'user': '', 'user_type': '', 'messages': [],
        'logo_clicks': 0, 'admin_unlocked': False, 'ok_clicks': 0,
        'is_blocked': False, 'logs': [], 'msg_count': 0
    })

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. KIỂM TRA CHẶN THIẾT BỊ ---
if st.session_state.is_blocked:
    st.error("🚫 HỆ THỐNG PHÁT HIỆN VI PHẠM: THIẾT BỊ ĐÃ BỊ CHẶN.")
    if st.button("🆘 GỬI ĐƠN XIN GỠ CHẶN"):
        st.session_state.logs.append(f"Yêu cầu gỡ chặn từ: {st.session_state.user}")
        st.success("Yêu cầu đã được gửi tới bảng điều khiển ẩn.")
    st.stop()

# --- 4. MÀN HÌNH ĐĂNG NHẬP / ĐĂNG KÝ / KHÁCH ---
if st.session_state.page == 'auth':
    st.title("🔑 Hệ thống Đăng nhập Nexus")
    mode = st.radio("Chế độ truy cập:", ["Đăng ký", "Đăng nhập", "Khách"], horizontal=True)
    name = st.text_input("Tên sử dụng:", placeholder="Nhập tên của bạn...")
    
    if mode != "Khách":
        # Sửa lỗi: Dùng text_input với type="password"
        st.text_input("Mật khẩu:", type="password")
        st.warning("⚠️ CẢNH BÁO: Lịch sử có thể bị mất. Đề nghị sao lưu bằng .txt thường xuyên.")
    else:
        st.info("💡 CHẾ ĐỘ KHÁCH: Lịch sử không lưu trực tiếp, chỉ lưu qua tính năng xuất .txt")

    if st.button("XÁC NHẬN"):
        if name:
            st.session_state.user = name
            st.session_state.user_type = mode
            st.session_state.page = 'launcher'
            st.rerun()
        else: st.error("Vui lòng nhập tên sử dụng!")

# --- 5. MÀN HÌNH CHỌN APP (LAUNCHER) ---
elif st.session_state.page == 'launcher':
    col_l, col_r = st.columns([1, 9])
    with col_l:
        # Nhấn logo 10 lần để mở khóa menu ẩn
        if st.button("💎", key="logo"):
            st.session_state.logo_clicks += 1
            if st.session_state.logo_clicks >= 10:
                st.session_state.page = 'hidden_menu'
                st.rerun()
    with col_r:
        st.title(f"Nexus OS - {st.session_state.user}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🤖\nTRÍ TUỆ AI"): st.session_state.page = 'ai'; st.rerun()
    with c2:
        if st.button("⚙️\nCÀI ĐẶT"): st.session_state.page = 'settings'; st.rerun()

# --- 6. ỨNG DỤNG AI (TYPOGRAPHY & RESPONSE FIXED) ---
elif st.session_state.page == 'ai':
    st.title("🤖 AI Assistant")
    if st.button("🏠 VỀ MÀN HÌNH CHÍNH"): st.session_state.page = 'launcher'; st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            if m["role"] == "assistant":
                # AI bubble với văn bản sạch cho giọng đọc
                st.markdown(f'<div class="ai-bubble">{m["content"]}</div>', unsafe_allow_html=True)
            else: st.write(m["content"])

    # Thanh gợi ý
    cols = st.columns(2)
    p_sug = ""
    if cols[0].button("✨ Kế hoạch làm việc"): p_sug = "Lập kế hoạch làm việc hiệu quả"
    if cols[1].button("✨ Giải thích AI"): p_sug = "AI là gì? Giải thích đơn giản"

    inp = st.chat_input("Nhập câu hỏi của bạn...")
    query = inp if inp else p_sug

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        st.session_state.msg_count += 1
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages])
        # Sửa typography: Loại bỏ toàn bộ in đậm ** để đọc văn bản mượt hơn
        ans = res.choices[0].message.content.replace("**", "").replace("__", "")
        st.session_state.messages.append({"role": "assistant", "content": ans})
        st.rerun()

# --- 7. ỨNG DỤNG CÀI ĐẶT ---
elif st.session_state.page == 'settings':
    st.title("⚙️ Cài đặt & Thông tin")
    if st.button("🏠 Quay lại"): st.session_state.page = 'launcher'; st.rerun()
    
    st.write(f"**Người sử dụng:** {st.session_state.user}")
    st.write(f"**Trạng thái:** {st.session_state.user_type}")
    
    st.divider()
    # Tính năng lưu TXT độc quyền
    full_log = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
    st.download_button("📤 XUẤT LỊCH SỬ (.TXT)", data=full_log, file_name="nexus_chat.txt", use_container_width=True)

# --- 8. MENU MẬT MÃ BÍ MẬT ---
elif st.session_state.page == 'hidden_menu':
    st.title("Xác thực Mật khẩu")
    st.write("Nhập mã PIN 4 chữ số:")
    
    # Bố cục 4 ô nhập nằm ngang
    c_p = st.columns(4)
    v1 = c_p[0].text_input("", key="v1", max_chars=1)
    v2 = c_p[1].text_input("", key="v2", max_chars=1)
    v3 = c_p[2].text_input("", key="v3", max_chars=1)
    v4 = c_p[3].text_input("", key="v4", max_chars=1)

    # Nút OK sáng khi đủ 4 số, mờ khi chưa đủ
    ready = all([v1, v2, v3, v4])
    is_trick = not any([v1, v2, v3, v4]) # Để trống 4 ô

    if st.button("OK", disabled=(not ready and not is_trick)):
        if is_trick:
            st.session_state.ok_clicks += 1
            if st.session_state.ok_clicks >= 4:
                st.session_state.admin_unlocked = True
        else:
            st.error("Mã PIN sai. Truy cập bị từ chối.")

    if st.session_state.admin_unlocked:
        st.success("🔓 ĐÃ TRUY CẬP BẢNG ĐIỀU KHIỂN ẨN")
        col_m, col_u = st.columns(2)
        col_m.metric("Tổng tin nhắn", st.session_state.msg_count)
        col_u.write(f"Người dùng hiện tại: {st.session_state.user}")
        
        st.write("📝 Danh sách yêu cầu gỡ chặn:")
        for log in st.session_state.logs: st.text(log)
        
        if st.button("🚫 CHẶN THIẾT BỊ NÀY VĨNH VIỄN", type="primary"):
            st.session_state.is_blocked = True
            st.rerun()

    if st.button("Thoát"):
        st.session_state.page = 'launcher'
        st.session_state.logo_clicks = 0
        st.session_state.ok_clicks = 0
        st.rerun()
