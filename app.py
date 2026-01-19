import streamlit as st
from openai import OpenAI
import time
from datetime import datetime

# --- 1. CẤU HÌNH TITAN OS (DARK MODE ENFORCED) ---
st.set_page_config(page_title="Nexus Titan OS v300", layout="wide", page_icon="🪐")

st.markdown("""
    <style>
    /* ÉP BUỘC CHẾ ĐỘ TỐI - KHÔNG THỂ BỊ LỖI TRẮNG/TRẮNG */
    .stApp {
        background: linear-gradient(180deg, #0b0f19 0%, #16222A 100%) !important;
        color: #FFFFFF !important;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, p, div, span, label { color: #FFFFFF !important; }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #333;
    }

    /* App Icon Grid */
    .app-grid {
        display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; padding: 20px;
    }
    .app-icon {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px; padding: 20px; text-align: center;
        cursor: pointer; transition: 0.3s; height: 150px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
    }
    .app-icon:hover {
        background: rgba(0, 200, 255, 0.2); border: 1px solid #00c8ff;
        transform: translateY(-5px);
    }
    .app-emoji { font-size: 40px; margin-bottom: 10px; }
    .app-name { font-weight: bold; font-size: 16px; color: #fff; }

    /* Chat Bubbles */
    .chat-user {
        background: #007bff; color: white; padding: 10px 15px;
        border-radius: 15px 15px 0 15px; margin: 5px 0; text-align: right;
        margin-left: auto; max-width: 70%;
    }
    .chat-ai {
        background: #2b2b2b; color: #e0e0e0; padding: 10px 15px;
        border-radius: 15px 15px 15px 0; margin: 5px 0; text-align: left;
        border-left: 4px solid #00c8ff; max-width: 70%;
    }
    
    /* Input Fields Fix */
    input, textarea {
        background-color: #1a1a1a !important; color: white !important;
        border: 1px solid #444 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INIT SYSTEM STATE ---
if 'system' not in st.session_state:
    st.session_state.update({
        'system': True, 'page': 'auth', 'user': None,
        'messages': [{"role": "system", "content": "Bạn là Nexus, trợ lý ảo trong hệ điều hành Titan OS."}], 
        'notes': [], 'feedbacks': [], 'admin_unlocked': False,
        'logo_clicks': 0, 'ok_clicks': 0, 'blocked': False,
        'settings': {'brightness': 80, 'vol': 50, 'ai_speed': 1.0}
    })

client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. GLOBAL SIDEBAR (THANH ĐIỀU HƯỚNG BÊN TRÁI) ---
# Sidebar luôn hiển thị để người dùng quay về bất cứ lúc nào
if st.session_state.page != 'auth':
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user}")
        st.divider()
        if st.button("🏠 MÀN HÌNH CHÍNH", use_container_width=True):
            st.session_state.page = 'home'; st.rerun()
        
        st.markdown("### 📱 Ứng dụng chạy nền")
        if st.button("🤖 AI Chat", use_container_width=True): st.session_state.page = 'chat'; st.rerun()
        if st.button("📝 Ghi chú", use_container_width=True): st.session_state.page = 'notes'; st.rerun()
        if st.button("⚙️ Cài đặt", use_container_width=True): st.session_state.page = 'settings'; st.rerun()
        
        st.divider()
        st.markdown("### 🗂 Lịch sử phiên")
        with st.expander("Xem nhật ký nhanh"):
             for m in st.session_state.messages:
                 if m['role'] == 'user': st.caption(f"Bạn: {m['content'][:20]}...")

# --- 4. TRANG ĐĂNG NHẬP (AUTH) ---
if st.session_state.page == 'auth':
    st.title("🪐 NEXUS TITAN OS")
    st.write("Đăng nhập để khởi động hệ điều hành.")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Tên định danh:")
        pwd = st.text_input("Mật khẩu:", type="password")
        if st.button("KHỞI ĐỘNG (ĐĂNG NHẬP)", type="primary"):
            if name:
                st.session_state.user = name
                st.session_state.page = 'home'
                st.rerun()
    with col2:
        st.info("Chế độ Khách (Guest Mode) không cần mật khẩu.")
        if st.button("VÀO NHANH (KHÁCH)"):
            st.session_state.user = "Guest"
            st.session_state.page = 'home'
            st.rerun()

# --- 5. MÀN HÌNH CHÍNH (OS LAUNCHER) ---
elif st.session_state.page == 'home':
    # Trigger Admin bí mật (Logo click)
    c_head, _ = st.columns([1, 15])
    if c_head.button("💠"):
        st.session_state.logo_clicks += 1
        if st.session_state.logo_clicks >= 10:
            st.session_state.page = 'admin_gate'; st.rerun()
            
    st.title(f"Xin chào, {st.session_state.user}")
    st.write("Chọn một ứng dụng để bắt đầu:")
    
    # Lưới ứng dụng (Grid)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🤖\nTRỢ LÝ AI", use_container_width=True, height=120): st.session_state.page = 'chat'; st.rerun()
    with c2:
        if st.button("📝\nGHI CHÚ", use_container_width=True, height=120): st.session_state.page = 'notes'; st.rerun()
    with c3:
        if st.button("⚙️\nCÀI ĐẶT", use_container_width=True, height=120): st.session_state.page = 'settings'; st.rerun()
    with c4:
        if st.button("📩\nPHẢN HỒI", use_container_width=True, height=120): st.session_state.page = 'feedback'; st.rerun()
    
    st.write("") # Spacer
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        if st.button("🧮\nMÁY TÍNH", use_container_width=True, height=120): st.warning("App Máy tính đang cập nhật...")
    with c6:
        if st.button("📁\nFILE", use_container_width=True, height=120): st.warning("Trình quản lý file đang xây dựng...")

# --- 6. ỨNG DỤNG CHAT (AI CORE - FIXED) ---
elif st.session_state.page == 'chat':
    st.title("🤖 Nexus Intelligence")
    
    # 1. HIỂN THỊ LỊCH SỬ TRƯỚC (QUAN TRỌNG ĐỂ KHÔNG MẤT TIN NHẮN)
    chat_container = st.container()
    with chat_container:
        for m in st.session_state.messages:
            if m["role"] == "system": continue # Ẩn system prompt
            if m["role"] == "user":
                st.markdown(f'<div class="chat-user">{m["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-ai">{m["content"]}</div>', unsafe_allow_html=True)

    # 2. XỬ LÝ INPUT
    prompt = st.chat_input("Nhập lệnh cho Nexus...")
    
    if prompt:
        # Append User Msg
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Rerun ngay lập tức để hiện tin nhắn user lên màn hình
        st.rerun()

    # 3. LOGIC TRẢ LỜI (CHẠY SAU KHI RERUN)
    # Kiểm tra nếu tin nhắn cuối là user thì AI mới trả lời
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with chat_container:
            with st.empty():
                full_res = ""
                # GỬI TOÀN BỘ CONTEXT (LỊCH SỬ) CHO AI
                stream = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content.replace("**", "")
                        st.markdown(f'<div class="chat-ai">{full_res} ▌</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="chat-ai">{full_res}</div>', unsafe_allow_html=True)
        
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        # Không rerun ở đây để tránh loop vô tận, stream đã hiển thị rồi.

# --- 7. ỨNG DỤNG CÀI ĐẶT (100 OPTIONS GIẢ LẬP) ---
elif st.session_state.page == 'settings':
    st.title("⚙️ Control Center")
    
    tab1, tab2, tab3 = st.tabs(["Hiển thị", "Âm thanh", "Hệ thống"])
    
    with tab1:
        st.session_state.settings['brightness'] = st.slider("Độ sáng màn hình", 0, 100, st.session_state.settings['brightness'])
        st.toggle("Chế độ bảo vệ mắt", True)
        st.toggle("Hiệu ứng chuyển cảnh (Animations)", True)
        st.select_slider("Kích thước font chữ", options=["Nhỏ", "Vừa", "Lớn", "Siêu lớn"], value="Vừa")
    
    with tab2:
        st.session_state.settings['vol'] = st.slider("Âm lượng hệ thống", 0, 100, st.session_state.settings['vol'])
        st.toggle("Âm thanh bàn phím", False)
        st.toggle("Đọc tin nhắn tự động", True)
    
    with tab3:
        st.write("Thông tin phiên bản: Titan OS v300 (Stable)")
        st.write(f"User ID: {st.session_state.user}")
        if st.button("Xóa dữ liệu bộ nhớ đệm"): st.success("Đã dọn dẹp RAM!")

# --- 8. ỨNG DỤNG GHI CHÚ ---
elif st.session_state.page == 'notes':
    st.title("📝 Ghi chú cá nhân")
    new_note = st.text_area("Nhập ghi chú mới:")
    if st.button("Lưu ghi chú"):
        st.session_state.notes.append(f"{datetime.now().strftime('%H:%M')}: {new_note}")
        st.success("Đã lưu.")
    
    st.write("---")
    st.write("Danh sách ghi chú:")
    for n in st.session_state.notes:
        st.info(n)

# --- 9. ADMIN CỔNG SAU (BACKDOOR) ---
elif st.session_state.page == 'admin_gate':
    st.title("🔐 Security Layer 4")
    st.write("Nhập mã xác thực:")
    
    c = st.columns(4)
    v1 = c[0].text_input("", key="p1", max_chars=1)
    v2 = c[1].text_input("", key="p2", max_chars=1)
    v3 = c[2].text_input("", key="p3", max_chars=1)
    v4 = c[3].text_input("", key="p4", max_chars=1)
    
    # TRICK: ĐỂ TRỐNG VÀ BẤM OK 4 LẦN
    is_empty = not any([v1, v2, v3, v4])
    
    if st.button("XÁC NHẬN (OK)"):
        if is_empty:
            st.session_state.ok_clicks += 1
            if st.session_state.ok_clicks >= 4:
                st.session_state.admin_unlocked = True
        else:
            st.error("Truy cập bị từ chối.")

    if st.session_state.admin_unlocked:
        st.warning("⚠️ BẢNG ĐIỀU KHIỂN QUẢN TRỊ VIÊN")
        st.write(f"Đang theo dõi người dùng: {st.session_state.user}")
        st.json(st.session_state.messages) # Xem toàn bộ log chat dưới dạng JSON
        if st.button("🛑 CHẶN THIẾT BỊ"):
            st.session_state.blocked = True; st.rerun()
    
    if st.button("Thoát"):
        st.session_state.page = 'home'; st.session_state.ok_clicks = 0; st.rerun()

# --- 10. APP PHẢN HỒI ---
elif st.session_state.page == 'feedback':
    st.title("📩 Gửi ý kiến")
    fb = st.text_area("Bạn muốn cải thiện điều gì?")
    if st.button("Gửi tới Admin"):
        st.session_state.feedbacks.append({"user": st.session_state.user, "time": str(datetime.now()), "msg": fb})
        st.success("Đã gửi!")
