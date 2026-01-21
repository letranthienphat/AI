import streamlit as st
import time
import psutil
from openai import OpenAI

# --- 1. CONFIG & SYSTEM INFO ---
st.set_page_config(page_title="NEXUS V400", layout="wide", page_icon="🧬", initial_sidebar_state="collapsed")

if 'stage' not in st.session_state: st.session_state.stage = "law"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'suggestions' not in st.session_state: 
    st.session_state.suggestions = ["Tóm tắt năng lực", "Kế hoạch thống trị task", "Dịch thuật cấp cao", "Viết code tối ưu", "Tư vấn chiến lược", "Phân tích hệ thống"]
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
if 'bg_url' not in st.session_state: st.session_state.bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072"
if 'user_name' not in st.session_state: st.session_state.user_name = "Agent"

GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])

# --- 2. CSS QUANTUM (FIX MÀU CHỮ & CUỘN) ---
def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;500&family=Inter:wght@300;400;700&display=swap');
    
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.95)), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}

    /* FIX CHỮ AI: ÉP TRẮNG TOÀN BỘ MARKDOWN */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown li, div[data-testid="stChatMessage"] p {{
        color: #FFFFFF !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }}

    /* KHUNG ĐIỀU KHOẢN TRƯỢT SIÊU MƯỢT */
    .law-container {{
        background: #050505;
        border: 1px solid #1DA1F2;
        border-radius: 12px;
        padding: 40px;
        height: 550px;
        overflow-y: scroll;
        margin-bottom: 25px;
    }}
    
    /* Tùy chỉnh thanh cuộn cho Laptop/PC */
    .law-container::-webkit-scrollbar {{ width: 8px; }}
    .law-container::-webkit-scrollbar-track {{ background: #000; }}
    .law-container::-webkit-scrollbar-thumb {{ background: #1DA1F2; border-radius: 10px; }}

    .law-content h2 {{ color: #1DA1F2 !important; border-bottom: 2px solid #1DA1F2; }}
    .law-content p {{ color: #E0E0E0 !important; font-size: 1.1rem; line-height: 1.8; }}

    /* GỢI Ý NẰM DƯỚI BOX CHAT */
    .suggestion-container {{
        display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;
    }}
    
    div.stButton > button {{
        background: rgba(29, 161, 242, 0.1);
        color: #1DA1F2; border: 1px solid #1DA1F2;
        border-radius: 20px; transition: 0.3s;
    }}
    div.stButton > button:hover {{ background: #1DA1F2; color: #fff; }}

    /* ADMIN BOX */
    .admin-card {{
        background: rgba(255, 255, 255, 0.05);
        border-left: 5px solid #1DA1F2;
        padding: 15px; border-radius: 5px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LUẬT DÀI & HÀI HƯỚC ---
def get_funny_quantum_law():
    return f"""
    <div class="law-content">
        <h2>CHƯƠNG I: QUYỀN LỰC TỐI THƯỢNG</h2>
        <p>1.1. Hệ thống Nexus OS được xây dựng, vận hành và sở hữu toàn phần bởi <b>Trần Thiện Phát Lê</b>. Mọi hành vi nhận vơ hoặc quên tên Admin sẽ bị hệ thống tự động phát bài "Người lạ ơi" liên tục 24h.</p>
        <p>1.2. Admin luôn đúng. Nếu Admin sai, hãy đọc lại Điều 1.1.</p>
        
        <h2>CHƯƠNG II: NGHĨA VỤ CỦA THỰC THỂ SỬ DỤNG</h2>
        <p>2.1. Bạn không được dùng AI để hỏi những câu mang tính chất triết học gây cháy CPU như: "Con gà có trước hay quả trứng có trước?". Nexus sẽ trả lời là "Admin có trước".</p>
        <p>2.2. Nghiêm cấm hỏi AI mượn tiền. Nexus rất giàu kiến thức nhưng nghèo số dư ngân hàng vì toàn bộ kinh phí đã đổ vào việc làm cho giao diện này trông thật ngầu.</p>
        <p>2.3. Nếu bạn đang sử dụng Nexus trên laptop trong khi chưa tắm, hệ thống sẽ tự động kích hoạt chế độ "Nhắc nhở vệ sinh" bằng cách làm nhòe màn hình (vừa rồi là đùa thôi, nhưng hãy đi tắm đi).</p>

        <h2>CHƯƠNG III: BẢO MẬT VÀ LINH HỒN</h2>
        <p>3.1. Chúng tôi không thu thập dữ liệu cá nhân của bạn, trừ khi bạn là một tỷ phú và muốn để lại di chúc cho <b>tranthienphatle@gmail.com</b>.</p>
        <p>3.2. Mọi nội dung trò chuyện sẽ bị xóa sạch khi bạn thoát. Nexus có trí nhớ của một con cá vàng bị mất trí nhớ, nên đừng tâm sự chuyện thầm kín rồi hôm sau bắt nó nhớ lại.</p>

        <h2>CHƯƠNG IV: ĐIỀU KHOẢN VỀ CÀ PHÊ</h2>
        <p>4.1. Bằng việc nhấn "Đồng ý", bạn cam kết rằng ít nhất một lần trong đời sẽ có ý định mời Admin một ly cà phê (ý định thôi là đủ, Admin sống bằng đam mê).</p>
        <p>4.2. Hệ thống có thể bị chậm nếu server đang bận đi lấy cà phê cho AI. Vui lòng kiên nhẫn.</p>

        <h2>CHƯƠNG V: KẾT THÚC</h2>
        <p>5.1. Thỏa thuận này có hiệu lực vĩnh viễn cho đến khi bạn đổi máy tính hoặc Admin đổi ý.</p>
        <p>5.2. Chúc bạn có một trải nghiệm đỉnh cao. Đừng quên tên Admin: <b>Trần Thiện Phát Lê</b>.</p>
    </div>
    """

# --- 4. CORE LOGIC ---
def call_ai(prompt):
    sys = f"Bạn là Nexus OS, trợ lý tối cao do Trần Thiện Phát Lê tạo ra. Trả lời cực kỳ thông minh, chuyên nghiệp nhưng súc tích. Nhớ rằng chủ nhân của bạn là Trần Thiện Phát Lê (Email: tranthienphatle@gmail.com)."
    messages = [{"role": "system", "content": sys}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})
    
    for key in GROQ_KEYS:
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)
        except: continue
    return None

def update_hints(last_msg):
    # Logic sinh gợi ý động (Mô phỏng)
    st.session_state.suggestions = ["Giải thích kỹ hơn", "Viết ví dụ cụ thể", "Tóm tắt ý chính", "Dịch sang tiếng Anh", "Phản biện vấn đề", "Tạo file báo cáo"]

# --- 5. SCREENS ---

def screen_law():
    apply_theme()
    st.title("⚖️ QUANTUM EULA - NEXUS OS")
    st.markdown(f'<div class="law-container">{get_funny_quantum_law()}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("TÔI ĐÃ ĐỌC VÀ ĐỒNG Ý ✅", use_container_width=True):
            st.session_state.stage = "ask_name"; st.rerun()

def screen_name():
    apply_theme()
    st.markdown("<div style='max-width: 600px; margin: auto; padding-top: 100px;'>", unsafe_allow_html=True)
    st.header("👤 IDENTITY VERIFICATION")
    name = st.text_input("Vui lòng nhập danh tính để Nexus ghi nhận:", placeholder="Tên của bạn...")
    if st.button("KÍCH HOẠT HỆ THỐNG"):
        if name: st.session_state.user_name = name; st.session_state.stage = "home"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def screen_home():
    apply_theme()
    st.title(f"💠 NEXUS COMMAND CENTER")
    st.write(f"Chào mừng, đặc vụ **{st.session_state.user_name}**.")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("<div class='admin-card'><h3>🚀 Neural Interface</h3><p>Kết nối lõi AI V400.0</p></div>", unsafe_allow_html=True)
        if st.button("MỞ PHÒNG CHAT", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()
            
    with c2:
        st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
        st.write("🛡️ **Admin Panel**")
        if st.button(f"S/N: {st.session_state.user_name[:3].upper()}-V400"):
            st.session_state.is_admin = not st.session_state.is_admin; st.rerun()
        
        if st.session_state.is_admin:
            st.info(f"Owner: Trần Thiện Phát Lê")
            st.caption(f"Email: tranthienphatle@gmail.com")
            st.write(f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%")
        
        st.session_state.bg_url = st.text_input("Background (URL):", st.session_state.bg_url)
        st.markdown("</div>", unsafe_allow_html=True)

def screen_chat():
    apply_theme()
    if st.button("⬅️ DASHBOARD"): st.session_state.stage = "home"; st.rerun()
    
    st.markdown(f"### 🧬 Nexus AI | {st.session_state.user_name}")
    
    # 1. KHU VỰC HIỂN THỊ CHAT (Luôn ở trên)
    chat_area = st.container()
    for m in st.session_state.chat_log:
        with chat_area.chat_message(m["role"]):
            st.markdown(m["content"])

    # 2. KHU VỰC GỢI Ý (Luôn ở dưới chat nhưng trên input)
    st.markdown("---")
    st.write("✨ **Thao tác nhanh:**")
    cols = st.columns(6)
    for i, s in enumerate(st.session_state.suggestions):
        with cols[i % 6]:
            if st.button(s, key=f"btn_{i}", use_container_width=True):
                process_msg(s)

    # 3. THANH NHẬP LIỆU (Cố định dưới cùng)
    if prompt := st.chat_input("Gửi lệnh cho Nexus..."):
        process_msg(prompt)

def process_msg(prompt):
    st.session_state.chat_log.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        box = st.empty(); full = ""
        stream = call_ai(prompt)
        if stream:
            for ch in stream:
                c = ch.choices[0].delta.content if hasattr(ch,'choices') else ch.text
                if c: full += c; box.markdown(full + "▌")
            box.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            update_hints(full); st.rerun()

# --- MAIN ---
if st.session_state.stage == "law": screen_law()
elif st.session_state.stage == "ask_name": screen_name()
elif st.session_state.stage == "home": screen_home()
else: screen_chat()
