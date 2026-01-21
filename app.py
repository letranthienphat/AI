import streamlit as st
import time
import psutil
import pandas as pd
import numpy as np
from openai import OpenAI

# --- 1. OPTIMIZED CONFIGURATION ---
st.set_page_config(page_title="NEXUS V300", layout="wide", page_icon="🛡️", initial_sidebar_state="collapsed")

# Caching tài nguyên tĩnh để tăng hiệu suất
@st.cache_resource
def get_system_stats():
    return psutil.cpu_percent(), psutil.virtual_memory().percent

# Khởi tạo State gọn nhẹ
if 'stage' not in st.session_state: st.session_state.stage = "law"
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'suggestions' not in st.session_state: st.session_state.suggestions = ["Tóm tắt nội dung", "Dịch sang tiếng Anh", "Viết code Python", "Giải thích chi tiết", "Phân tích dữ liệu", "Tạo Email mẫu"]
if 'admin_clicks' not in st.session_state: st.session_state.admin_clicks = 0
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
if 'bg_url' not in st.session_state: st.session_state.bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072"

GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])

# --- 2. CSS "TITANIUM" - TƯƠNG PHẢN TUYỆT ĐỐI ---
def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    * {{ font-family: 'Roboto', sans-serif; }}

    /* Nền ứng dụng */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.9)), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}

    /* KHUNG ĐIỀU KHOẢN (QUAN TRỌNG: NỀN ĐEN - CHỮ TRẮNG) */
    .term-container {{
        background-color: #0d1117; /* Đen than chì */
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 30px;
        height: 60vh; /* Chiều cao cố định để scroll */
        overflow-y: auto; /* Cho phép cuộn */
        box-shadow: inset 0 0 20px #000000;
        margin-bottom: 20px;
    }}
    
    .term-text p, .term-text h3, .term-text li {{
        color: #c9d1d9 !important; /* Trắng xám dễ đọc */
        font-size: 16px;
        line-height: 1.6;
        text-align: justify;
    }}
    
    .term-text h3 {{
        color: #58a6ff !important; /* Xanh dương cho tiêu đề */
        border-bottom: 1px solid #30363d;
        padding-bottom: 10px;
        margin-top: 20px;
    }}

    /* UI CÁC KHỐI KHÁC */
    .glass-panel {{
        background: rgba(22, 27, 34, 0.95);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
    }}
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown label {{
        color: #ffffff !important;
    }}

    /* NÚT BẤM */
    div.stButton > button {{
        background: #238636; color: white; border: none;
        font-weight: bold; padding: 10px 24px; border-radius: 6px;
        width: 100%; transition: 0.2s;
    }}
    div.stButton > button:hover {{
        background: #2ea043;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. NỘI DUNG LUẬT CHUYÊN NGHIỆP (EULA) ---
def get_full_terms():
    return """
    <div class="term-text">
    <h3>CHƯƠNG I: ĐỊNH NGHĨA VÀ PHẠM VI</h3>
    <p>1.1. Thỏa thuận này ("Thỏa thuận") là hợp đồng pháp lý giữa người dùng cuối ("Bạn") và Trần Thiện Phát Lê ("Chủ sở hữu") về việc sử dụng phần mềm Nexus OS ("Hệ thống").</p>
    <p>1.2. Hệ thống được cung cấp dưới dạng "NGUYÊN TRẠNG" (AS-IS). Bằng việc truy cập, Bạn chấp nhận mọi rủi ro liên quan đến chất lượng và hiệu suất của Hệ thống.</p>
    
    <h3>CHƯƠNG II: QUYỀN SỞ HỮU TRÍ TUỆ</h3>
    <p>2.1. Hệ thống này thuộc quyền sở hữu độc quyền của Trần Thiện Phát Lê (Email: tranthienphatle@gmail.com). Mọi mã nguồn, giao diện, và thuật toán đều được bảo vệ.</p>
    <p>2.2. Bạn không được phép sao chép, sửa đổi, đảo ngược kỹ thuật (reverse engineer), hoặc phân phối lại Hệ thống này dưới bất kỳ hình thức nào nếu không có sự đồng ý bằng văn bản.</p>
    
    <h3>CHƯƠNG III: QUYỀN VÀ NGHĨA VỤ NGƯỜI DÙNG</h3>
    <p>3.1. Bạn cam kết sử dụng Hệ thống cho các mục đích hợp pháp. Nghiêm cấm sử dụng Hệ thống để tạo ra nội dung độc hại, lừa đảo, hoặc vi phạm pháp luật nước sở tại.</p>
    <p>3.2. Bạn chịu trách nhiệm hoàn toàn về các dữ liệu đầu vào (Input) và cách sử dụng kết quả đầu ra (Output) từ AI.</p>
    
    <h3>CHƯƠNG IV: BẢO MẬT VÀ DỮ LIỆU</h3>
    <p>4.1. Hệ thống không lưu trữ lịch sử trò chuyện vĩnh viễn. Mọi dữ liệu phiên làm việc sẽ bị xóa khi Bạn đóng trình duyệt (Session-based Privacy).</p>
    <p>4.2. Mặc dù chúng tôi nỗ lực bảo vệ an toàn thông tin, không có hệ thống nào là an toàn tuyệt đối trên không gian mạng.</p>
    
    <h3>CHƯƠNG V: ĐIỀU KHOẢN THI HÀNH</h3>
    <p>5.1. Chủ sở hữu có quyền đơn phương chấm dứt quyền truy cập của Bạn nếu phát hiện vi phạm.</p>
    <p>5.2. Bằng việc đánh dấu vào ô "Tôi đồng ý" bên dưới, Bạn xác nhận đã đọc, hiểu và đồng ý tuân thủ toàn bộ các điều khoản trên.</p>
    <p><i>(Kết thúc văn bản thỏa thuận - Bản cập nhật V300.0)</i></p>
    </div>
    """

# --- 4. LOGIC AI ---
def call_ai_smart(prompt):
    # Prompt tinh chỉnh để trả lời thông minh
    messages = [{"role": "system", "content": f"Bạn là Nexus, trợ lý AI chuyên nghiệp của {st.session_state.user_name}. Trả lời ngắn gọn, chính xác, không thừa lời."}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})
    
    # Logic gọi API tối ưu
    for key in GROQ_KEYS:
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)
        except: continue
    return None

def generate_actions(last_msg):
    # Tạo gợi ý dựa trên ngữ cảnh (Giả lập logic nhanh để tăng hiệu suất)
    # Trong thực tế có thể gọi thêm 1 API call nhỏ ở đây
    base_actions = ["Tóm tắt lại", "Giải thích thêm", "Dịch sang Anh", "Ví dụ thực tế", "Phản biện lại", "Viết Code mẫu"]
    st.session_state.suggestions = base_actions # Cập nhật nhanh

# --- 5. GIAO DIỆN CHÍNH ---

def screen_law_v3():
    apply_theme()
    st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
    st.title("⚖️ ĐIỀU KHOẢN SỬ DỤNG (EULA)")
    
    # HIỂN THỊ LUẬT TRONG KHUNG SCROLL RIÊNG BIỆT (KHẮC PHỤC LỖI HIỂN THỊ)
    st.markdown(f"<div class='term-container'>{get_full_terms()}</div>", unsafe_allow_html=True)
    
    # Checkbox xác nhận chuyên nghiệp
    agree = st.checkbox("Tôi xác nhận đã đọc toàn bộ điều khoản và đồng ý tuân thủ.", value=False)
    
    if st.button("TIẾP TỤC TRUY CẬP ➡️", disabled=not agree):
        st.session_state.stage = "ask_name"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def screen_name():
    apply_theme()
    st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
    st.subheader("🔒 XÁC THỰC NGƯỜI DÙNG")
    name = st.text_input("Vui lòng nhập tên định danh:", placeholder="User ID...")
    if st.button("KẾT NỐI"):
        if name:
            st.session_state.user_name = name; st.session_state.stage = "home"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def screen_home():
    apply_theme()
    st.title(f"💠 NEXUS DASHBOARD")
    
    # Layout 2 cột hiệu quả
    c1, c2 = st.columns([7, 3])
    
    with c1:
        st.markdown("<div class='glass-panel'><h3>💬 Neural Chat Interface</h3><p>Truy cập lõi AI hiệu suất cao.</p></div>", unsafe_allow_html=True)
        if st.button("MỞ KHUNG CHAT", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()
            
    with c2:
        st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
        st.write("⚙️ **Cài đặt nhanh**")
        st.session_state.bg_url = st.text_input("URL Hình nền:", st.session_state.bg_url)
        
        # Admin Gate Tối ưu
        if st.button("Nexus Core V300.0"):
            st.session_state.admin_clicks += 1
            if st.session_state.admin_clicks >= 5: st.session_state.is_admin = not st.session_state.is_admin; st.rerun()
        
        if st.session_state.is_admin:
            st.success("🔓 ADMIN MODE")
            st.caption(f"Owner: Trần Thiện Phát Lê")
            st.caption("Email: tranthienphatle@gmail.com")
            
            # Thống kê hiệu suất thật
            cpu, mem = get_system_stats()
            st.progress(cpu/100, text=f"CPU: {cpu}%")
            st.progress(mem/100, text=f"RAM: {mem}%")
            
            # Fake data analytics
            data = pd.DataFrame(np.random.randn(10, 2), columns=['In', 'Out'])
            st.area_chart(data, height=150)
            
        st.markdown("</div>", unsafe_allow_html=True)

def screen_chat():
    apply_theme()
    # Header nhỏ gọn
    h1, h2 = st.columns([1, 10])
    with h1: 
        if st.button("⬅️"): st.session_state.stage = "home"; st.rerun()
    with h2: st.markdown(f"**NEXUS CHAT** | {st.session_state.user_name}")

    # Khung chat
    chat_box = st.container()
    for m in st.session_state.chat_log:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    # Gợi ý thông minh (Smart Chips)
    st.write("")
    suggestions = st.session_state.suggestions
    cols = st.columns(6) # Chia làm 6 cột cho 6 gợi ý trên 1 hàng ngang (trên PC)
    for i, s in enumerate(suggestions):
        with cols[i % 6]:
            if st.button(s, key=f"s_{i}", use_container_width=True):
                process_msg(s)

    if prompt := st.chat_input("Nhập tin nhắn..."):
        process_msg(prompt)

def process_msg(prompt):
    st.session_state.chat_log.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        box = st.empty(); full = ""
        stream = call_ai_smart(prompt)
        if stream:
            for chunk in stream:
                c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                if c: full += c; box.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            generate_actions(full) # Cập nhật gợi ý sau khi trả lời
            st.rerun()

# --- MAIN ROUTER ---
if st.session_state.stage == "law": screen_law_v3()
elif st.session_state.stage == "ask_name": screen_name()
elif st.session_state.stage == "home": screen_home()
else: screen_chat()
