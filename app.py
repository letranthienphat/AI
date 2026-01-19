import streamlit as st
from openai import OpenAI
import time
from datetime import datetime

# --- 1. CẤU HÌNH GIAO DIỆN "MONOLITH" ---
st.set_page_config(page_title="Nexus OS v200", layout="wide", page_icon="💠")

st.markdown("""
    <style>
    /* Nền động Supernova */
    @keyframes galaxy { 
        0% { background-position: 0% 50%; } 
        50% { background-position: 100% 50%; } 
        100% { background-position: 0% 50%; } 
    }
    .stApp {
        background: linear-gradient(-45deg, #141E30, #243B55, #4ca1af, #c4e0e5) !important;
        background-size: 400% 400% !important;
        animation: galaxy 20s ease infinite !important;
    }
    
    /* Typography chuẩn OS */
    h1, h2, h3 { color: #FFFFFF !important; text-shadow: 0 0 10px rgba(0,255,255,0.5); }
    p, span, div { color: #E0E0E0 !important; font-size: 16px; }
    
    /* Card giao diện lớn (Dashboard) */
    .big-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        transition: 0.3s;
        margin-bottom: 20px;
    }
    .big-card:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: scale(1.02);
        border: 1px solid #00d2ff;
        box-shadow: 0 0 20px rgba(0, 210, 255, 0.4);
    }

    /* AI Bubble - Chữ đen trên nền trắng cho dễ đọc */
    .ai-bubble {
        background: #FFFFFF; color: #000000 !important;
        padding: 20px; border-radius: 15px 15px 15px 0;
        margin-bottom: 10px; border-left: 5px solid #00d2ff;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .user-bubble {
        background: #00d2ff; color: #000000 !important;
        padding: 15px; border-radius: 15px 15px 0 15px;
        text-align: right; margin-bottom: 10px; font-weight: bold;
    }

    /* Nút bấm to rõ */
    div.stButton > button {
        width: 100%; height: 60px; border-radius: 12px; font-weight: bold; font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. QUẢN LÝ DỮ LIỆU TẬP TRUNG (SESSION STATE) ---
if 'init_v200' not in st.session_state:
    st.session_state.update({
        'init_v200': True,
        'page': 'auth',         # auth, home, chat, settings, feedback, admin
        'user': None,
        'role': None,           # Member, Guest
        'messages': [],
        'chat_history': [],     # Lưu danh sách các cuộc trò chuyện cũ
        'feedbacks': [],        # Lưu phản hồi gửi về admin
        'admin_unlocked': False,
        'logo_clicks': 0,
        'ok_clicks': 0,
        'blocked': False
    })

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. LOGIC CHẶN THIẾT BỊ ---
if st.session_state.blocked:
    st.error("⛔ THIẾT BỊ ĐÃ BỊ CHẶN TRUY CẬP VĨNH VIỄN.")
    st.stop()

# --- 4. SIDEBAR: LỊCH SỬ TRÒ CHUYỆN ---
if st.session_state.page != 'auth':
    with st.sidebar:
        st.title("🗂️ Hồ Sơ")
        st.write(f"Xin chào, **{st.session_state.user}**")
        st.caption(f"Vai trò: {st.session_state.role}")
        
        if st.session_state.role == "Thành viên":
            st.divider()
            st.subheader("Lịch sử trò chuyện")
            if not st.session_state.chat_history:
                st.info("Chưa có cuộc trò chuyện nào được lưu.")
            else:
                for idx, chat in enumerate(st.session_state.chat_history):
                    if st.button(f"📅 {chat['time']}", key=f"hist_{idx}"):
                        st.session_state.messages = chat['msgs']
                        st.session_state.page = 'chat'
                        st.rerun()
        else:
            st.warning("⚠️ Chế độ Khách: Lịch sử không được lưu.")
        
        st.divider()
        if st.button("🚪 Đăng xuất"):
            st.session_state.page = 'auth'
            st.session_state.messages = []
            st.rerun()

# --- 5. PAGE: XÁC THỰC (LOGIN) ---
if st.session_state.page == 'auth':
    col_main, _ = st.columns([1, 1]) # Căn giữa
    with col_main:
        st.title("💠 NEXUS LOGIN")
        st.markdown("Hệ điều hành trí tuệ nhân tạo thế hệ mới.")
        
        tab1, tab2 = st.tabs(["ĐĂNG NHẬP / ĐĂNG KÝ", "KHÁCH VÃNG LAI"])
        
        with tab1:
            u_name = st.text_input("Tên tài khoản:")
            u_pass = st.text_input("Mật khẩu:", type="password")
            if st.button("🚀 ĐĂNG NHẬP HỆ THỐNG", type="primary"):
                if u_name and u_pass:
                    st.session_state.user = u_name
                    st.session_state.role = "Thành viên"
                    st.session_state.page = 'home'
                    st.rerun()
                else: st.error("Vui lòng nhập đủ thông tin!")
        
        with tab2:
            g_name = st.text_input("Tên hiển thị:")
            if st.button("🌟 TRUY CẬP NGAY"):
                if g_name:
                    st.session_state.user = g_name
                    st.session_state.role = "Khách"
                    st.session_state.page = 'home'
                    st.rerun()
                else: st.error("Hãy nhập tên để chúng tôi gọi bạn!")

# --- 6. PAGE: MÀN HÌNH CHÍNH (HOME DASHBOARD) ---
elif st.session_state.page == 'home':
    # Header & Secret Logo Trigger
    c1, c2 = st.columns([1, 10])
    if c1.button("💠", key="secret_trigger"):
        st.session_state.logo_clicks += 1
        if st.session_state.logo_clicks >= 10:
            st.session_state.page = 'admin_auth'; st.rerun()
    c2.title("Nexus Dashboard")

    # Các thẻ Cards lớn
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="big-card"><h3>🤖<br>AI CHATBOT</h3><p>Trợ lý ảo thông minh</p></div>', unsafe_allow_html=True)
        if st.button("Mở Chatbot"): st.session_state.page = 'chat'; st.rerun()
        
    with col2:
        st.markdown('<div class="big-card"><h3>⚙️<br>CÀI ĐẶT</h3><p>Thông tin & Cấu hình</p></div>', unsafe_allow_html=True)
        if st.button("Vào Cài đặt"): st.session_state.page = 'settings'; st.rerun()

    with col3:
        st.markdown('<div class="big-card"><h3>📩<br>PHẢN HỒI</h3><p>Gửi ý kiến cho Admin</p></div>', unsafe_allow_html=True)
        if st.button("Gửi Phản hồi"): st.session_state.page = 'feedback'; st.rerun()

# --- 7. PAGE: AI CHAT (CORE) ---
elif st.session_state.page == 'chat':
    st.title("🤖 Nexus AI")
    if st.button("⬅️ Trở về Dashboard"): st.session_state.page = 'home'; st.rerun()

    # Chat UI
    for m in st.session_state.messages:
        if m["role"] == "user":
            st.markdown(f'<div class="user-bubble">{m["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ai-bubble">{m["content"]}</div>', unsafe_allow_html=True)

    # Input & Logic
    prompt = st.chat_input("Nhập tin nhắn...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Streaming response
        with st.empty():
            full_res = ""
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    txt = chunk.choices[0].delta.content.replace("**", "") # Làm sạch văn bản
                    full_res += txt
                    st.markdown(f'<div class="ai-bubble">{full_res} ▌</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="ai-bubble">{full_res}</div>', unsafe_allow_html=True)
        
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        
        # Tự động lưu lịch sử nếu là Member
        if st.session_state.role == "Thành viên":
            # Logic đơn giản: Lưu phiên chat hiện tại vào history
            curr_session = {'time': datetime.now().strftime("%H:%M %d/%m"), 'msgs': st.session_state.messages}
            # Cập nhật phiên mới nhất hoặc thêm mới (ở đây thêm mới để demo)
            if not st.session_state.chat_history or st.session_state.chat_history[-1]['msgs'] != st.session_state.messages:
                 st.session_state.chat_history.append(curr_session)

# --- 8. PAGE: PHẢN HỒI (FEEDBACK) ---
elif st.session_state.page == 'feedback':
    st.title("📩 Gửi phản hồi hệ thống")
    st.write("Ý kiến của bạn giúp Nexus hoàn thiện hơn.")
    
    fb_content = st.text_area("Nội dung phản hồi:", height=150)
    
    col_a, col_b = st.columns(2)
    if col_a.button("Gửi ngay", type="primary"):
        if fb_content:
            # Lưu phản hồi vào session state (Admin sẽ thấy)
            new_fb = {
                "user": st.session_state.user,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "content": fb_content
            }
            st.session_state.feedbacks.append(new_fb)
            st.success("✅ Phản hồi đã được gửi đến Admin!")
            time.sleep(1)
            st.session_state.page = 'home'; st.rerun()
        else:
            st.error("Nội dung trống!")
    
    if col_b.button("Hủy bỏ"): st.session_state.page = 'home'; st.rerun()

# --- 9. PAGE: CÀI ĐẶT & GIỚI THIỆU ---
elif st.session_state.page == 'settings':
    st.title("⚙️ Cài đặt hệ thống")
    if st.button("⬅️ Trở về Dashboard"): st.session_state.page = 'home'; st.rerun()
    
    tab_info, tab_sys = st.tabs(["ℹ️ GIỚI THIỆU HỆ THỐNG", "🛠️ TÙY CHỈNH"])
    
    with tab_info:
        st.markdown("""
        ### 💠 NEXUS INTELLIGENCE OS v200
        
        **1. Sứ mệnh cốt lõi:**
        Nexus được sinh ra không chỉ để trả lời câu hỏi, mà để trở thành người bạn đồng hành số hóa (Digital Companion). Chúng tôi tập trung vào trải nghiệm người dùng liền mạch (Seamless UX) và khả năng xử lý ngôn ngữ tự nhiên vượt trội.
        
        **2. Kiến trúc Bảo mật:**
        - **Mã hóa:** Dữ liệu phiên làm việc được mã hóa cục bộ.
        - **Ẩn danh:** Chế độ Khách đảm bảo không lưu vết (Zero-trace).
        - **Admin Shield:** Hệ thống quản trị ẩn 4 lớp bảo vệ.
        
        **3. Công nghệ lõi:**
        Sử dụng mô hình ngôn ngữ lớn (LLM) Llama-3 70B với khả năng suy luận đa chiều, kết hợp với giao diện Streamlit được tùy biến sâu (Deep Customization) bằng CSS/JS Injection.
        """)
        st.info("Phiên bản hiện tại: v200.0.1 (Stable Build)")

    with tab_sys:
        st.toggle("Chế độ tiết kiệm pin", False)
        st.toggle("Tự động đọc tin nhắn (Voice)", True)
        st.slider("Độ trong suốt giao diện", 0, 100, 20)

# --- 10. PAGE: ADMIN AUTH & DASHBOARD (ẨN) ---
elif st.session_state.page == 'admin_auth':
    st.title("🛡️ Admin Gate")
    st.markdown("Nhập mã truy cập 4 số:")
    
    c = st.columns(4)
    v1 = c[0].text_input("", key="a1", max_chars=1)
    v2 = c[1].text_input("", key="a2", max_chars=1)
    v3 = c[2].text_input("", key="a3", max_chars=1)
    v4 = c[3].text_input("", key="a4", max_chars=1)
    
    # Logic Trick: Để trống 4 ô và bấm OK 4 lần
    is_empty = not any([v1, v2, v3, v4])
    
    if st.button("XÁC NHẬN (OK)"):
        if is_empty:
            st.session_state.ok_clicks += 1
            if st.session_state.ok_clicks >= 4:
                st.session_state.admin_unlocked = True
                st.rerun()
        else:
            st.error("Truy cập bị từ chối.")

    if st.session_state.admin_unlocked:
        st.divider()
        st.success("🔓 ADMIN DASHBOARD UNLOCKED")
        st.write(f"👋 Xin chào Admin. Đang giám sát phiên của: **{st.session_state.user}**")
        
        st.subheader("📬 Hộp thư phản hồi (Real-time)")
        if not st.session_state.feedbacks:
            st.info("Chưa có phản hồi nào.")
        else:
            for fb in st.session_state.feedbacks:
                with st.expander(f"Từ: {fb['user']} | Lúc: {fb['time']}"):
                    st.write(fb['content'])
        
        st.divider()
        st.subheader("🚨 Kiểm soát thiết bị")
        if st.button("🚫 CHẶN USER NÀY", type="primary"):
            st.session_state.blocked = True
            st.session_state.page = 'auth' # Đá văng ra
            st.rerun()
            
    if st.button("Thoát Admin"):
        st.session_state.page = 'home'
        st.session_state.logo_clicks = 0
        st.session_state.ok_clicks = 0
        st.rerun()
