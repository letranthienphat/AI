import streamlit as st
from openai import OpenAI

# --- 1. GIAO DIỆN SÓNG ĐỘNG & TYPOGRAPHY MỚI ---
st.set_page_config(page_title="Nexus OS v115", layout="wide")

st.markdown("""
    <style>
    @keyframes move { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    .stApp {
        background: linear-gradient(-45deg, #00c6ff, #0072ff, #3a1c71, #d76d77) !important;
        background-size: 400% 400% !important;
        animation: move 12s ease infinite !important;
    }
    /* Sửa lỗi nút bấm có độ cao bằng CSS */
    div.stButton > button {
        height: 120px !important;
        border-radius: 20px !important;
        background: rgba(255, 255, 255, 0.9) !important;
        color: #000000 !important;
        font-weight: 800 !important;
        font-size: 20px !important;
        border: 2px solid #FFFFFF !important;
    }
    .ai-bubble {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px; padding: 20px;
        color: #000000 !important; font-size: 1.1rem;
        border-left: 8px solid #0072ff; margin-bottom: 10px;
    }
    /* Ô nhập PIN 4 số nằm ngang */
    .pin-container { display: flex; gap: 10px; justify-content: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE ---
if 'page' not in st.session_state:
    st.session_state.update({
        'page': 'auth', 'user': None, 'user_type': None, 'messages': [],
        'logo_clicks': 0, 'admin_unlocked': False, 'ok_clicks': 0,
        'is_blocked': False, 'logs': [], 'msg_count': 0
    })

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. KIỂM TRA CHẶN ---
if st.session_state.is_blocked:
    st.error("🚫 THIẾT BỊ NÀY ĐÃ BỊ HỆ THỐNG CHẶN.")
    if st.button("🆘 GỬI YÊU CẦU GỠ CHẶN"):
        st.session_state.logs.append(f"Yêu cầu gỡ chặn từ: {st.session_state.user}")
        st.success("Yêu cầu đã gửi.")
    st.stop()

# --- 4. MÀN HÌNH ĐĂNG NHẬP / ĐĂNG KÝ / KHÁCH ---
if st.session_state.page == 'auth':
    st.title("🔑 Hệ thống Đăng nhập")
    mode = st.radio("Chế độ:", ["Đăng nhập", "Đăng ký", "Khách"], horizontal=True)
    name = st.text_input("Tên sử dụng:", key="user_input")
    
    if mode != "Khách":
        st.password_input("Mật khẩu:")
        st.warning("⚠️ Cảnh báo: Lịch sử có thể bị mất. Đề nghị sao lưu bằng .txt thường xuyên.")
    else:
        st.info("💡 Chế độ Khách: Không lưu lịch sử trực tiếp, chỉ lưu qua .txt")

    if st.button("TRUY CẬP"):
        if name:
            st.session_state.user = name
            st.session_state.user_type = mode
            st.session_state.page = 'launcher'
            st.rerun()
        else: st.error("Hãy nhập tên sử dụng!")

# --- 5. APP LAUNCHER ---
elif st.session_state.page == 'launcher':
    col_logo, col_title = st.columns([1, 9])
    with col_logo:
        if st.button("💎", key="logo_btn"):
            st.session_state.logo_clicks += 1
            if st.session_state.logo_clicks >= 10:
                st.session_state.page = 'hidden_menu'
                st.rerun()
    with col_title:
        st.title(f"Nexus OS - {st.session_state.user}")

    c1, c2 = st.columns(2)
    if c1.button("🤖\nTRÍ TUỆ AI"): st.session_state.page = 'ai'; st.rerun()
    if c2.button("⚙️\nCÀI ĐẶT"): st.session_state.page = 'settings'; st.rerun()

# --- 6. AI APP (FIX PHẢN HỒI & TYPOGRAPHY) ---
elif st.session_state.page == 'ai':
    st.title("🤖 AI Assistant")
    if st.button("🏠 Quay lại"): st.session_state.page = 'launcher'; st.rerun()

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            if m["role"] == "assistant":
                st.markdown(f'<div class="ai-bubble">{m["content"]}</div>', unsafe_allow_html=True)
            else: st.write(m["content"])

    # Gợi ý
    cols = st.columns(2)
    if cols[0].button("✨ Kế hoạch tuần"): p = "Lập kế hoạch tuần"
    elif cols[1].button("✨ Giải đáp khoa học"): p = "Giải thích thuyết tương đối"
    else: p = None

    inp = st.chat_input("Nhập tin nhắn...")
    final_p = inp if inp else p

    if final_p:
        st.session_state.messages.append({"role": "user", "content": final_p})
        st.session_state.msg_count += 1
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages])
        # Xóa in đậm để AI đọc văn bản mượt hơn
        clean_text = res.choices[0].message.content.replace("**", "").replace("__", "")
        st.session_state.messages.append({"role": "assistant", "content": clean_text})
        st.rerun()

# --- 7. SETTINGS ---
elif st.session_state.page == 'settings':
    st.title("⚙️ Thông tin & Cài đặt")
    if st.button("🏠 Quay lại"): st.session_state.page = 'launcher'; st.rerun()
    
    st.write(f"Tên: {st.session_state.user}")
    st.write(f"Loại: {st.session_state.user_type}")
    
    full_txt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
    st.download_button("📤 SAO LƯU .TXT", data=full_txt, file_name="history.txt")

# --- 8. MENU MẬT MÃ (EASTER EGG) ---
elif st.session_state.page == 'hidden_menu':
    st.title("Mật khẩu")
    st.write("Vui lòng nhập mã PIN 4 số để tiếp tục:")
    
    cols = st.columns(4)
    v1 = cols[0].text_input("", key="v1", max_chars=1)
    v2 = cols[1].text_input("", key="v2", max_chars=1)
    v3 = cols[2].text_input("", key="v3", max_chars=1)
    v4 = cols[3].text_input("", key="v4", max_chars=1)

    # Nút OK mờ nếu chưa nhập đủ 4 số
    ready = all([v1, v2, v3, v4])
    # Trường hợp đặc biệt: Nếu cả 4 ô trống vẫn cho nhấn để thực hiện mẹo mở khóa
    is_empty_trick = not any([v1, v2, v3, v4])

    if st.button("OK", disabled=(not ready and not is_empty_trick)):
        if is_empty_trick:
            st.session_state.ok_clicks += 1
            if st.session_state.ok_clicks >= 4:
                st.session_state.admin_unlocked = True
        else:
            st.error("Mã PIN không chính xác.")

    if st.session_state.admin_unlocked:
        st.success("🔓 ADMIN DASHBOARD")
        col_a, col_b = st.columns(2)
        col_a.metric("Số tin nhắn", st.session_state.msg_count)
        col_b.write(f"User: {st.session_state.user}")
        
        st.write("Nhật ký yêu cầu gỡ chặn:")
        for log in st.session_state.logs: st.text(log)
        
        if st.button("🚫 CHẶN THIẾT BỊ NÀY", type="primary"):
            st.session_state.is_blocked = True
            st.rerun()

    if st.button("Thoát"):
        st.session_state.page = 'launcher'
        st.session_state.logo_clicks = 0
        st.session_state.ok_clicks = 0
        st.rerun()
