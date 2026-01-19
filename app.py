import streamlit as st
from openai import OpenAI
import time
import json

# --- 1. GIAO DIỆN AURORA OS V110 ---
st.set_page_config(page_title="Nexus OS v110", layout="wide")
st.markdown("""
    <style>
    @keyframes move { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    .stApp {
        background: linear-gradient(-45deg, #00c6ff, #0072ff, #3a1c71, #d76d77) !important;
        background-size: 400% 400% !important;
        animation: move 12s ease infinite !important;
    }
    /* Typography AI - Chữ đen, rõ, không ký tự thừa cho giọng đọc */
    .ai-bubble {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px; padding: 20px;
        color: #000000 !important; font-size: 1.1rem;
        line-height: 1.6; border-left: 5px solid #0072ff;
    }
    /* Pin Input Style */
    .pin-box { border: 2px solid #0072ff; border-radius: 10px; text-align: center; font-size: 20px; width: 50px; }
    /* Nút mờ/sáng */
    .stButton > button:disabled { opacity: 0.3 !important; cursor: not-allowed !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO HỆ THỐNG ---
if 'init_v110' not in st.session_state:
    st.session_state.update({
        'init_v110': True, 'page': 'auth', 'user': None, 'user_type': None, 
        'messages': [], 'logo_clicks': 0, 'admin_unlocked': False,
        'wrong_attempts': 0, 'is_blocked': False, 'msg_count': 0, 'logs': []
    })

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. KIỂM TRA CHẶN THIẾT BỊ ---
if st.session_state.is_blocked:
    st.error("🚫 THIẾT BỊ NÀY ĐÃ BỊ CHẶN TRUY CẬP.")
    st.info("Thông tin thiết bị đã được ghi nhận trên hệ thống Admin.")
    if st.button("🆘 GỬI YÊU CẦU GỠ CHẶN"):
        st.session_state.logs.append(f"Yêu cầu gỡ chặn từ {st.session_state.user}")
        st.success("Yêu cầu đã được gửi đến bảng điều khiển.")
    st.stop()

# --- 4. HÀM XỬ LÝ AI ---
def chat_ai(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.msg_count += 1
    try:
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages])
        clean_ans = res.choices[0].message.content.replace("**", "") # Xóa in đậm để AI đọc mượt
        st.session_state.messages.append({"role": "assistant", "content": clean_ans})
    except:
        st.error("AI không phản hồi. Kiểm tra lại kết nối.")

# --- 5. MÀN HÌNH ĐĂNG NHẬP / GUEST ---
if st.session_state.page == 'auth':
    st.title("🔐 ĐĂNG NHẬP NEXUS OS")
    mode = st.radio("Chọn phương thức:", ["Đăng ký", "Đăng nhập", "Khách (Guest)"], horizontal=True)
    name = st.text_input("Tên sử dụng:", placeholder="Nhập tên của bạn...")
    
    if mode != "Khách (Guest)":
        pwd = st.text_input("Mật khẩu:", type="password")
        st.warning("⚠️ Cảnh báo: Lịch sử trò chuyện có thể bị mất do cache trình duyệt. Hãy luôn sao lưu bằng .txt")
    
    if st.button("XÁC NHẬN TRUY CẬP"):
        if name:
            st.session_state.user = name
            st.session_state.user_type = mode
            st.session_state.page = 'launcher'
            st.rerun()
        else: st.error("Vui lòng nhập tên!")

# --- 6. GIAO DIỆN CHÍNH (LAUNCHER) ---
elif st.session_state.page == 'launcher':
    # Click logo 10 lần
    col_l, col_r = st.columns([1, 8])
    with col_l:
        if st.button("💎", key="logo"):
            st.session_state.logo_clicks += 1
            if st.session_state.logo_clicks >= 10:
                st.session_state.page = 'hidden_menu'
                st.rerun()
    with col_r:
        st.title(f"Xin chào, {st.session_state.user}!")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🤖\nTRÍ TUỆ AI", height=150): st.session_state.page = 'ai'; st.rerun()
    with c2:
        if st.button("⚙️\nCÀI ĐẶT", height=150): st.session_state.page = 'settings'; st.rerun()
    with c3:
        if st.button("🚪\nĐĂNG XUẤT"): st.session_state.page = 'auth'; st.rerun()

# --- 7. APP: AI ASSISTANT ---
elif st.session_state.page == 'ai':
    st.subheader(f"🤖 Trợ lý Nexus | {st.session_state.user_type}")
    if st.button("🏠 Home"): st.session_state.page = 'launcher'; st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            if m["role"] == "assistant":
                st.markdown(f'<div class="ai-bubble">{m["content"]}</div>', unsafe_allow_html=True)
            else:
                st.write(m["content"])

    # Thanh gợi ý
    cols = st.columns(3)
    sug_list = ["Lập thời gian biểu", "Giải thích về AI", "Tạo file backup"]
    for idx, s in enumerate(sug_list):
        if cols[idx].button(s): chat_ai(s); st.rerun()

    inp = st.chat_input("Hỏi tôi...")
    if inp: chat_ai(inp); st.rerun()

# --- 8. APP: CÀI ĐẶT ---
elif st.session_state.page == 'settings':
    st.title("⚙️ Cài đặt & Thông tin")
    if st.button("🏠 Home"): st.session_state.page = 'launcher'; st.rerun()
    
    st.write(f"**Người dùng:** {st.session_state.user}")
    st.write(f"**Loại tài khoản:** {st.session_state.user_type}")
    
    # Tính năng sao lưu luôn có sẵn
    full_txt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
    st.download_button("📤 SAO LƯU HỘI THOẠI (.TXT)", data=full_txt, file_name="nexus_backup.txt")

# --- 9. MENU ẨN (HIDDEN ADMIN) ---
elif st.session_state.page == 'hidden_menu':
    st.title("Mật khẩu")
    cols = st.columns(4)
    p1 = cols[0].text_input("", key="p1", max_chars=1)
    p2 = cols[1].text_input("", key="p2", max_chars=1)
    p3 = cols[2].text_input("", key="p3", max_chars=1)
    p4 = cols[3].text_input("", key="p4", max_chars=1)
    
    btn_ready = all([p1, p2, p3, p4]) or (not p1 and not p2 and not p3 and not p4)
    
    if st.button("OK", disabled=not btn_ready):
        # Logic mở khóa bí mật: nhấn OK 4 lần khi 4 ô trống
        if not p1 and not p2 and not p3 and not p4:
            st.session_state.wrong_attempts += 1
            if st.session_state.wrong_attempts >= 4:
                st.session_state.admin_unlocked = True
        else:
            st.error("Sai mã PIN.")

    if st.session_state.admin_unlocked:
        st.success("🔓 QUYỀN TRUY CẬP ADMIN ĐƯỢC THIẾT LẬP")
        st.divider()
        st.subheader("📊 Bảng điều khiển ẩn")
        col_a, col_b = st.columns(2)
        col_a.metric("Số lần chat", st.session_state.msg_count)
        col_a.write(f"Thiết bị: Trình duyệt Web")
        col_b.write(f"User hiện tại: {st.session_state.user}")
        
        st.write("💬 Nhật ký yêu cầu:")
        for log in st.session_state.logs: st.text(log)
        
        if st.button("🚫 CHẶN THIẾT BỊ NÀY"):
            st.session_state.is_blocked = True
            st.rerun()
            
    if st.button("Thoát"): 
        st.session_state.page = 'launcher'
        st.session_state.logo_clicks = 0
        st.session_state.wrong_attempts = 0
        st.rerun()
