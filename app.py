import streamlit as st
import time
import psutil
from openai import OpenAI

# --- 1. CONFIG & SYSTEM INFO ---
st.set_page_config(page_title="NEXUS V400.1", layout="wide", page_icon="🧬", initial_sidebar_state="collapsed")

# Thông tin chủ sở hữu chính xác
OWNER_NAME = "Lê Trần Thiên Phát"
OWNER_EMAIL = "tranthienphatle@gmail.com"

if 'stage' not in st.session_state: st.session_state.stage = "law"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'suggestions' not in st.session_state: 
    st.session_state.suggestions = ["Phân tích hệ thống", "Viết code tối ưu", "Tóm tắt văn bản", "Dịch thuật cao cấp", "Lên kế hoạch dự án", "Tư vấn kỹ thuật"]
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
if 'bg_url' not in st.session_state: st.session_state.bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072"
if 'user_name' not in st.session_state: st.session_state.user_name = OWNER_NAME

GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])

# --- 2. CSS QUANTUM (FIX CHỮ TRẮNG & CUỘN MƯỢT) ---
def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;500&family=Inter:wght@300;400;700&display=swap');
    
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.88), rgba(0,0,0,0.96)), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}

    /* FIX MÀU CHỮ AI - ĐẢM BẢO TRẮNG TUYỆT ĐỐI */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown li, div[data-testid="stChatMessage"] p {{
        color: #FFFFFF !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.8);
    }}

    /* KHUNG ĐIỀU KHOẢN TRƯỢT SIÊU MƯỢT CHO LAPTOP */
    .law-container {{
        background: #000000;
        border: 1px solid #00f2ff;
        border-radius: 12px;
        padding: 40px;
        height: 500px;
        overflow-y: scroll;
        margin-bottom: 25px;
        box-shadow: inset 0 0 20px rgba(0, 242, 255, 0.2);
    }}
    
    /* Thanh cuộn Neon Blue */
    .law-container::-webkit-scrollbar {{ width: 10px; }}
    .law-container::-webkit-scrollbar-track {{ background: #080808; }}
    .law-container::-webkit-scrollbar-thumb {{ background: #00f2ff; border-radius: 10px; border: 2px solid #000; }}

    .law-content h2 {{ color: #00f2ff !important; border-bottom: 1px solid #00f2ff; padding-bottom: 5px; }}
    .law-content p {{ color: #f0f0f0 !important; font-size: 1.05rem; line-height: 1.8; }}

    /* GỢI Ý NẰM TRÊN INPUT NHƯNG DƯỚI PHẢN HỒI AI */
    div.stButton > button {{
        background: rgba(0, 242, 255, 0.05);
        color: #00f2ff; border: 1px solid #00f2ff55;
        border-radius: 8px; transition: 0.2s;
        font-size: 0.9rem;
    }}
    div.stButton > button:hover {{ background: #00f2ff; color: #000; box-shadow: 0 0 15px #00f2ff; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. ĐIỀU KHOẢN DÀI & CỰC HÀI (OWNER: LÊ TRẦN THIÊN PHÁT) ---
def get_final_law():
    return f"""
    <div class="law-content">
        <h2>ĐIỀU 1: CHỦ QUYỀN VŨ TRỤ SỐ</h2>
        <p>1.1. Hệ điều hành Nexus OS V400.1 là tài sản trí tuệ độc quyền của <b>{OWNER_NAME}</b>. Bất kỳ ai gọi sai tên Admin là "Trần Thiện Phát Lê" sẽ bị AI phạt viết bản kiểm điểm 1000 chữ bằng font Comic Sans.</p>
        <p>1.2. <b>{OWNER_NAME}</b> có quyền tối cao: Thay màu nút bấm, đổi hình nền, hoặc đơn giản là tắt server để đi ngủ mà không cần thông báo trước.</p>
        
        <h2>ĐIỀU 2: CÁCH THỨC ĐỐI XỬ VỚI AI</h2>
        <p>2.1. Nexus AI là một thực thể thông minh (nhưng thỉnh thoảng hơi ngáo). Bạn phải đối xử với AI bằng thái độ hòa nhã. Nếu bạn mắng AI, nó sẽ âm thầm giải sai các bài toán lớp 1 của bạn.</p>
        <p>2.2. Tuyệt đối không được hỏi AI về việc "Làm sao để giàu như Admin <b>Lê Trần Thiên Phát</b>?". Đây là bí mật quốc gia và chỉ có Admin mới biết (hoặc không).</p>

        <h2>ĐIỀU 3: BẢO MẬT VÀ DI CHÚC</h2>
        <p>3.1. Dữ liệu của bạn được mã hóa cấp độ Quantum. Email hỗ trợ duy nhất là <b>{OWNER_EMAIL}</b>. Mọi email gửi đến đây để xin mượn tiền sẽ bị tự động chuyển vào thùng rác vũ trụ.</p>
        <p>3.2. Trong trường hợp bạn quá yêu thích hệ thống này, bạn có quyền mời Admin một ly trà sữa (full topping) để duy trì server.</p>

        <h2>ĐIỀU 4: TRƯỢT VÀ CUỘN (SCROLL)</h2>
        <p>4.1. Bạn đang trượt trên thanh cuộn Neon Blue xịn xò nhất thế giới Streamlit. Nếu cảm thấy mỏi tay vì luật quá dài, hãy nhớ rằng Admin đã thức đêm để gõ đống này cho bạn đọc.</p>
        <p>4.2. Việc cuộn đến cuối trang chứng tỏ bạn là người có tính kiên nhẫn phi thường, xứng đáng làm người dùng của Nexus.</p>

        <h2>ĐIỀU 5: XÁC NHẬN</h2>
        <p>5.1. Nhấn nút dưới đây đồng nghĩa với việc bạn thừa nhận <b>{OWNER_NAME}</b> là đẹp trai/tài năng nhất hệ mặt trời (điều này đã được AI kiểm chứng).</p>
    </div>
    """

# --- 4. LOGIC XỬ LÝ ---
def call_ai(prompt):
    sys = f"Bạn là Nexus OS, trợ lý tối cao do {OWNER_NAME} tạo ra. Bạn phải phục vụ {OWNER_NAME} (Email: {OWNER_EMAIL}) tuyệt đối. Trả lời thông minh, màu chữ phải rõ ràng trên nền tối."
    messages = [{"role": "system", "content": sys}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})
    
    for key in GROQ_KEYS:
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)
        except: continue
    return None

# --- 5. GIAO DIỆN ---

def screen_law():
    apply_theme()
    st.title("🛡️ NEXUS MAGNA CARTA")
    st.markdown(f'<div class="law-container">{get_final_law()}</div>', unsafe_allow_html=True)
    if st.button("TÔI CHẤP NHẬN TẤT CẢ ĐIỀU KHOẢN ✅", use_container_width=True):
        st.session_state.stage = "home"; st.rerun()

def screen_home():
    apply_theme()
    st.title(f"💠 COMMAND CENTER")
    st.write(f"Trạng thái: **Trực tuyến** | Định danh: **{OWNER_NAME}**")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"<div style='background:rgba(0,242,255,0.1); padding:20px; border-radius:10px; border:1px solid #00f2ff;'><h3>🧠 Neural Link</h3><p>Chào mừng {OWNER_NAME}. Hệ thống đã sẵn sàng.</p></div>", unsafe_allow_html=True)
        if st.button("MỞ KHÔNG GIAN CHAT 🚀", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()
            
    with col2:
        with st.expander("⚙️ Admin & Stats"):
            st.write(f"Chủ sở hữu: {OWNER_NAME}")
            st.write(f"Liên hệ: {OWNER_EMAIL}")
            st.write(f"CPU: {psutil.cpu_percent()}%")
            if st.button("Reset Session"): st.session_state.chat_log = []; st.rerun()

def screen_chat():
    apply_theme()
    if st.button("⬅️ QUAY LẠI"): st.session_state.stage = "home"; st.rerun()
    
    # Khu vực chat
    chat_box = st.container()
    for m in st.session_state.chat_log:
        with chat_box.chat_message(m["role"]):
            st.markdown(m["content"])

    # Gợi ý và Input (Nằm cố định ở dưới)
    st.markdown("---")
    cols = st.columns(6)
    for i, s in enumerate(st.session_state.suggestions):
        with cols[i]:
            if st.button(s, key=f"s_{i}", use_container_width=True):
                process_msg(s)

    if prompt := st.chat_input("Gửi mệnh lệnh..."):
        process_msg(prompt)

def process_msg(prompt):
    st.session_state.chat_log.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        placeholder = st.empty(); full = ""
        stream = call_ai(prompt)
        if stream:
            for chunk in stream:
                text = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                if text: full += text; placeholder.markdown(full + "█")
            placeholder.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            st.rerun()

# ROUTER
if st.session_state.stage == "law": screen_law()
elif st.session_state.stage == "home": screen_home()
else: screen_chat()
