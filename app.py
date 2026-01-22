import streamlit as st
import time
from openai import OpenAI

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="NEXUS V800", layout="wide", page_icon="🛡️")

CREATOR_NAME = "Lê Trần Thiên Phát"
CREATOR_EMAIL = "tranthienphatle@gmail.com"

if 'stage' not in st.session_state: st.session_state.stage = "Home"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'suggestions' not in st.session_state: 
    st.session_state.suggestions = ["Nexus có thể làm gì?", "Lên lịch trình hôm nay", "Viết code mẫu", "Tóm tắt kiến thức"]
if 'bg_url' not in st.session_state: 
    st.session_state.bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072"

GROQ_KEYS = st.secrets.get("GROQ_KEYS", ["YOUR_KEY_HERE"])

# --- 2. CSS TITAN (TƯƠNG PHẢN TUYỆT ĐỐI) ---
def apply_titan_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}

    /* Nền ứng dụng */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.95)), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}

    /* KHUNG CHỮ TƯƠNG PHẢN CAO */
    .glass-card {{
        background: rgba(10, 10, 15, 0.95); /* Đen gần như đặc để đọc rõ chữ */
        border: 1px solid rgba(0, 242, 255, 0.2);
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.8);
    }}

    /* Điều khoản (Sửa lỗi tương phản) */
    .tos-container {{
        background: #050505;
        border: 2px solid #333;
        border-radius: 12px;
        padding: 30px;
        height: 500px;
        overflow-y: scroll;
        color: #FFFFFF !important;
    }}
    .tos-container h2 {{ color: #00f2ff !important; margin-top: 20px; }}
    .tos-container p {{ font-size: 1.1rem; line-height: 1.8; color: #E0E0E0 !important; }}

    /* Fix chữ trong Chat */
    .stMarkdown p, .stMarkdown li {{
        color: #FFFFFF !important;
        text-shadow: 0 1px 2px rgba(0,0,0,1);
        font-size: 1.05rem;
    }}

    /* Sidebar Menu */
    [data-testid="stSidebar"] {{
        background-color: #0A0A0A !important;
        border-right: 1px solid #222;
    }}
    
    /* Gợi ý (Buttons) */
    div.stButton > button {{
        background: rgba(0, 242, 255, 0.1);
        color: #00f2ff; border: 1px solid #00f2ff55;
        border-radius: 8px; transition: 0.3s;
    }}
    div.stButton > button:hover {{ background: #00f2ff; color: #000; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. NỘI DUNG ĐIỀU KHOẢN ---
def get_tos_content():
    return f"""
    <div class="tos-container">
        <h2>🛡️ HIẾP ƯỚC NGƯỜI DÙNG V800.0</h2>
        <p>Chào mừng bạn đến với Nexus, hệ điều hành AI được tinh chỉnh bởi <b>{CREATOR_NAME}</b>. Vui lòng đọc kỹ các điều khoản để đảm bảo trải nghiệm tốt nhất.</p>
        
        <h2>1. TRẢI NGHIỆM NGƯỜI DÙNG</h2>
        <p>Chúng tôi đặt sự tiện lợi của bạn lên hàng đầu. AI sẽ trả lời trọng tâm, chính xác và chỉ nhắc đến nhà phát triển khi được yêu cầu. Giao diện được tối ưu hóa cho cả Laptop và thiết bị di động.</p>
        
        <h2>2. BẢO MẬT TUYỆT ĐỐI</h2>
        <p>Nexus không lưu trữ dữ liệu cá nhân của bạn trên máy chủ lâu dài. Mọi cuộc trò chuyện chỉ có giá trị trong phiên làm việc hiện tại.</p>
        
        <h2>3. QUYỀN SỞ HỮU</h2>
        <p>Hệ thống này là sản phẩm trí tuệ của <b>{CREATOR_NAME}</b>. Bạn có quyền sử dụng kết quả từ AI cho công việc và học tập một cách hợp pháp.</p>
        
        <h2>4. ĐIỀU KHOẢN HÀI HƯỚC</h2>
        <p>Nếu bạn thấy AI trả lời quá thông minh, đừng quá ngạc nhiên, đó là tính năng. Nếu AI trả lời hơi "ngáo", đó là lỗi tại server đang bận đi lấy cà phê cho Admin.</p>
        
        <p align="center"><i>(Cuộn xuống để xem hết và bấm xác nhận bên dưới)</i></p>
    </div>
    """

# --- 4. AI CORE ---
def call_ai(prompt):
    sys_msg = f"Bạn là Nexus, trợ lý AI thông minh được tạo bởi {CREATOR_NAME}. Tập trung vào trải nghiệm người dùng, trả lời súc tích. Chỉ nhắc creator khi được hỏi."
    messages = [{"role": "system", "content": sys_msg}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})
    
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)
    except Exception as e:
        st.error("Kết nối AI gián đoạn."); return None

# --- 5. MÀN HÌNH ---

def screen_home():
    apply_titan_theme()
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.title("💠 NEXUS DASHBOARD")
    st.write(f"Hệ thống vận hành bởi công nghệ AI tiến hóa. Chào mừng bạn.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("💡 **Gợi ý:** Bạn có thể bắt đầu bằng việc yêu cầu Nexus tóm tắt một chủ đề phức tạp hoặc viết code cho một ứng dụng.")
        if st.button("MỞ PHÒNG CHAT AI 🚀", use_container_width=True):
            st.session_state.stage = "Chat"; st.rerun()
    with col2:
        st.write("**Thông tin phiên bản:**")
        st.caption("Version: V800.0 (Titan)")
        st.caption(f"Nhà phát triển: {CREATOR_NAME}")
    st.markdown("</div>", unsafe_allow_html=True)

def screen_law():
    apply_titan_theme()
    st.title("⚖️ ĐIỀU KHOẢN & ĐIỀU KIỆN")
    st.markdown(get_tos_content(), unsafe_allow_html=True)
    if st.button("TÔI ĐỒNG Ý VÀ TIẾP TỤC ✅", use_container_width=True):
        st.session_state.stage = "Home"; st.rerun()

def screen_chat():
    apply_titan_theme()
    st.title("🧬 NEXUS CHAT CORE")
    
    # Hiển thị hội thoại
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Gợi ý
    st.markdown("---")
    cols = st.columns(4)
    for i, sug in enumerate(st.session_state.suggestions):
        if cols[i].button(sug, key=f"s_{i}", use_container_width=True):
            process_msg(sug)

    if prompt := st.chat_input("Nhập câu hỏi tại đây..."):
        process_msg(prompt)

def process_msg(prompt):
    st.session_state.chat_log.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        placeholder = st.empty(); full = ""
        stream = call_ai(prompt)
        if stream:
            for chunk in stream:
                c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                if c: full += c; placeholder.markdown(full + "▌")
            placeholder.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            st.rerun()

# --- 6. MENU CHÍNH (SIDEBAR) ---
apply_titan_theme()
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=100)
    st.title("NEXUS MENU")
    choice = st.radio("Chuyển trang:", ["🏠 Trang chủ", "💬 Chat AI", "📜 Điều khoản"])
    
    st.write("---")
    if st.button("Làm mới cuộc trò chuyện"):
        st.session_state.chat_log = []; st.rerun()
    
    # Logic chuyển trang từ Menu
    if choice == "🏠 Trang chủ": st.session_state.stage = "Home"
    elif choice == "💬 Chat AI": st.session_state.stage = "Chat"
    elif choice == "📜 Điều khoản": st.session_state.stage = "Law"

# ĐIỀU HƯỚNG MÀN HÌNH CHÍNH
if st.session_state.stage == "Home": screen_home()
elif st.session_state.stage == "Law": screen_law()
else: screen_chat()
