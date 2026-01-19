import streamlit as st
from openai import OpenAI
import time
from datetime import datetime

# --- 1. CẤU HÌNH HỆ THỐNG & GIAO DIỆN DARK MODE ---
st.set_page_config(page_title="Nexus OS v400", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    /* 1. Giao diện tối hoàn toàn (Fix lỗi trắng chữ) */
    .stApp {
        background-color: #0E1117 !important;
        color: #FFFFFF !important;
    }
    
    /* 2. Fix lỗi nút bấm màn hình chính */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        border: 1px solid #333;
        background-color: #262730;
        color: white;
        transition: 0.3s;
        font-weight: bold;
        padding: 20px 10px; /* Tăng độ cao bằng padding thay vì height cố định */
    }
    div.stButton > button:hover {
        border-color: #00d2ff;
        color: #00d2ff;
        background-color: #1a1c24;
    }

    /* 3. Bong bóng chat giao diện mới */
    .chat-user {
        background: linear-gradient(135deg, #007bff, #00d2ff);
        color: white; padding: 12px 18px;
        border-radius: 18px 18px 0 18px;
        margin: 5px 0 5px auto; /* Căn phải */
        max-width: 80%; width: fit-content;
        box-shadow: 0 2px 10px rgba(0,123,255,0.2);
    }
    .chat-ai {
        background: #2b2b2b; color: #e0e0e0;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 0;
        margin: 5px auto 5px 0; /* Căn trái */
        max-width: 80%; width: fit-content;
        border-left: 4px solid #00d2ff;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    /* 4. Ẩn menu mặc định của Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. KHỞI TẠO STATE (TRÁNH LỖI MẤT DỮ LIỆU) ---
if 'init_v400' not in st.session_state:
    st.session_state.update({
        'init_v400': True,
        'page': 'auth', 
        'user': 'Khách',
        'messages': [],  # Lưu toàn bộ chat để hiển thị
        'feedbacks': [],
        'admin_unlocked': False,
        'ok_clicks': 0,
        'logo_clicks': 0,
        'blocked': False
    })

# Cấu hình Client AI
client = OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

# --- 3. SIDEBAR ĐIỀU HƯỚNG ---
if st.session_state.page != 'auth':
    with st.sidebar:
        st.markdown(f"### 👤 User: {st.session_state.user}")
        st.divider()
        if st.button("🏠 TRANG CHỦ"): st.session_state.page = 'home'; st.rerun()
        if st.button("🤖 CHAT AI"): st.session_state.page = 'chat'; st.rerun()
        if st.button("⚙️ CÀI ĐẶT"): st.session_state.page = 'settings'; st.rerun()
        
        st.divider()
        st.caption("Công cụ nhanh:")
        if st.button("🗑️ Xóa lịch sử Chat"):
            st.session_state.messages = []
            st.toast("Đã dọn dẹp bộ nhớ!", icon="🧹")
            st.rerun()

# --- 4. TRANG ĐĂNG NHẬP (AUTH) ---
if st.session_state.page == 'auth':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🛡️ NEXUS LOGIN")
        st.write("Hệ điều hành bảo mật v400")
        
        name = st.text_input("Tên định danh:")
        # Input password chuẩn
        pwd = st.text_input("Mật khẩu:", type="password")
        
        c1, c2 = st.columns(2)
        if c1.button("ĐĂNG NHẬP"):
            if name:
                st.session_state.user = name
                st.session_state.page = 'home'
                st.rerun()
            else: st.error("Vui lòng nhập tên!")
            
        if c2.button("CHẾ ĐỘ KHÁCH"):
            st.session_state.user = "Khách vãng lai"
            st.session_state.page = 'home'
            st.rerun()

# --- 5. TRANG CHỦ (HOME DASHBOARD) ---
elif st.session_state.page == 'home':
    # Trigger Admin ẩn (Click logo 10 lần)
    c_logo, _ = st.columns([1, 10])
    if c_logo.button("💠"):
        st.session_state.logo_clicks += 1
        if st.session_state.logo_clicks >= 10:
            st.session_state.page = 'admin_gate'; st.rerun()

    st.title("📱 Màn hình chính")
    st.markdown("---")

    # Lưới ứng dụng (Grid Layout)
    # Dùng st.columns chuẩn để không bị vỡ giao diện
    col1, col2 = st.columns(2)
    with col1:
        st.info("🤖 **TRỢ LÝ AI**")
        if st.button("Mở Chatbot AI"): st.session_state.page = 'chat'; st.rerun()
        
        st.warning("📩 **PHẢN HỒI**")
        if st.button("Gửi ý kiến"): st.session_state.page = 'feedback'; st.rerun()

    with col2:
        st.success("⚙️ **CÀI ĐẶT**")
        if st.button("Cấu hình hệ thống"): st.session_state.page = 'settings'; st.rerun()

        st.error("🔐 **ADMIN**")
        if st.button("Khu vực quản trị"): 
            st.toast("Bạn cần nhập mã bí mật!", icon="🔒")

# --- 6. CHAT AI (FIX LỖI RATE LIMIT & CRASH) ---
elif st.session_state.page == 'chat':
    st.title("🤖 Nexus AI Core")
    
    # Hiển thị lịch sử chat
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            st.info("👋 Hãy nói 'Xin chào' để bắt đầu!")
        
        for m in st.session_state.messages:
            if m["role"] == "user":
                st.markdown(f'<div class="chat-user">{m["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-ai">{m["content"]}</div>', unsafe_allow_html=True)

    # Input (Luôn nằm dưới cùng)
    if prompt := st.chat_input("Nhập tin nhắn..."):
        # 1. Hiện tin nhắn người dùng ngay lập tức
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            st.markdown(f'<div class="chat-user">{prompt}</div>', unsafe_allow_html=True)

        # 2. Xử lý AI trả lời (Có Try-Except chống sập)
        with chat_container:
            status_box = st.empty()
            status_box.caption("🔄 AI đang suy nghĩ...")
            
            try:
                full_res = ""
                # FIX LỖI RATE LIMIT: CHỈ GỬI 6 TIN NHẮN CUỐI CÙNG (CONTEXT WINDOW)
                recent_history = st.session_state.messages[-6:] 
                
                stream = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": m["role"], "content": m["content"]} for m in recent_history],
                    stream=True,
                    max_tokens=1024 # Giới hạn độ dài trả lời để tránh lỗi
                )
                
                status_box.empty() # Xóa dòng 'đang suy nghĩ'
                res_box = st.empty()
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        text = chunk.choices[0].delta.content.replace("**", "") # Xóa in đậm
                        full_res += text
                        res_box.markdown(f'<div class="chat-ai">{full_res} ▌</div>', unsafe_allow_html=True)
                
                res_box.markdown(f'<div class="chat-ai">{full_res}</div>', unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                
            except Exception as e:
                status_box.error(f"⚠️ Lỗi kết nối AI: {str(e)}")
                st.error("Server quá tải. Vui lòng bấm 'Xóa lịch sử Chat' ở Sidebar và thử lại.")

# --- 7. ADMIN GATE (MẸO MỞ KHÓA) ---
elif st.session_state.page == 'admin_gate':
    st.title("🔐 Cổng bảo mật lớp 4")
    st.write("Nhập mã PIN 4 số:")
    
    c = st.columns(4)
    v1 = c[0].text_input("", key="p1", max_chars=1)
    v2 = c[1].text_input("", key="p2", max_chars=1)
    v3 = c[2].text_input("", key="p3", max_chars=1)
    v4 = c[3].text_input("", key="p4", max_chars=1)
    
    # MẸO: ĐỂ TRỐNG + BẤM OK 4 LẦN
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
        st.success("🔓 ADMIN DASHBOARD - ĐÃ MỞ KHÓA")
        st.metric("Tổng tin nhắn đã lưu", len(st.session_state.messages))
        st.write("Nhật ký phản hồi:")
        for fb in st.session_state.feedbacks: st.text(fb)
        
        if st.button("🚫 CHẶN NGƯỜI DÙNG NÀY"):
            st.session_state.blocked = True
            st.session_state.page = 'auth'
            st.rerun()

    if st.button("Thoát"):
        st.session_state.page = 'home'
        st.session_state.ok_clicks = 0
        st.rerun()

# --- 8. SETTINGS & FEEDBACK ---
elif st.session_state.page == 'settings':
    st.title("⚙️ Cài đặt")
    st.toggle("Chế độ tối (Luôn bật)", True, disabled=True)
    st.slider("Tốc độ AI", 1, 10, 5)
    if st.button("Quay lại"): st.session_state.page = 'home'; st.rerun()

elif st.session_state.page == 'feedback':
    st.title("📩 Gửi phản hồi")
    txt = st.text_area("Nhập nội dung:")
    if st.button("Gửi"):
        st.session_state.feedbacks.append(f"{datetime.now()}: {txt}")
        st.success("Đã gửi!")
        time.sleep(1)
        st.session_state.page = 'home'; st.rerun()
    if st.button("Hủy"): st.session_state.page = 'home'; st.rerun()
