import streamlit as st
from openai import OpenAI
import time

# --- 1. CONFIG & SYSTEM ---
st.set_page_config(page_title="NEXUS V1000", layout="wide", page_icon="⚡", initial_sidebar_state="collapsed")

OWNER = "Lê Trần Thiên Phát"
EMAIL = "tranthienphatle@gmail.com"

# Khởi tạo trạng thái
if 'page' not in st.session_state: st.session_state.page = "MENU"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'hints' not in st.session_state: 
    st.session_state.hints = ["Nexus có thể làm gì?", "Viết code giúp tôi", "Kể một chuyện hài", "Tư vấn công việc"]

# Hàm chuyển trang tức thì
def nav_to(page_name):
    st.session_state.page = page_name

# --- 2. CSS TITAN V1000 (HIGH CONTRAST) ---
def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    * {{ font-family: 'Plus Jakarta Sans', sans-serif; color: #FFFFFF; }}
    
    .stApp {{ background: #000000; }}

    /* Menu Card Styling */
    .menu-card {{
        background: #0A0A0A;
        border: 1px solid #1DA1F2;
        padding: 40px 20px;
        border-radius: 20px;
        text-align: center;
        transition: 0.4s;
        margin-bottom: 20px;
    }}
    .menu-card:hover {{
        background: #111;
        box-shadow: 0 0 30px rgba(29, 161, 242, 0.4);
        transform: translateY(-10px);
    }}

    /* Legal Box - Laptop Scroll Optimized */
    .legal-container {{
        background: #050505;
        border: 1px solid #222;
        border-radius: 15px;
        padding: 40px;
        height: 500px;
        overflow-y: scroll;
        scrollbar-width: thin;
        scrollbar-color: #1DA1F2 #000;
    }}
    .legal-container::-webkit-scrollbar {{ width: 6px; }}
    .legal-container::-webkit-scrollbar-thumb {{ background: #1DA1F2; border-radius: 10px; }}
    .legal-container h2 {{ color: #1DA1F2 !important; }}
    .legal-container p {{ color: #BBB !important; font-size: 1.1rem; line-height: 1.8; }}

    /* Chat Elements */
    div[data-testid="stChatMessage"] {{
        background: #080808; border: 1px solid #1A1A1A; border-radius: 15px;
    }}
    .stMarkdown p {{ color: white !important; font-size: 1.1rem; text-shadow: 0 1px 2px #000; }}

    /* Gợi ý Buttons */
    div.stButton > button {{
        background: #1DA1F2; color: #000; font-weight: 700; border-radius: 10px;
        border: none; padding: 10px 20px; transition: 0.3s;
    }}
    div.stButton > button:hover {{ background: #00f2ff; color: #000; transform: scale(1.05); }}
    
    /* Gợi ý Pill Style */
    .stButton > button[kind="secondary"] {{
        background: rgba(29, 161, 242, 0.1); color: #1DA1F2; border: 1px solid #1DA1F2;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. AI CORE LOGIC (FIXED) ---
def call_ai(prompt):
    # System prompt: Tập trung người dùng, ẩn creator
    sys_prompt = f"Bạn là Nexus, trợ lý AI thông minh bậc nhất. Trả lời cực kỳ súc tích, chuyên nghiệp. Chỉ nhắc đến người sáng tạo {OWNER} khi được hỏi 'Ai tạo ra bạn?' hoặc 'Thông tin tác giả'."
    messages = [{"role": "system", "content": sys_prompt}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})
    
    try:
        # Sử dụng API Key của bạn từ st.secrets hoặc điền trực tiếp
        client = OpenAI(api_key=st.secrets.get("GROQ_KEY", "gsk_vM6MhIq9hY8N1D0b2k5bWGdyb3FYM3J8S9k9q9q9q9q9q9q9q9q"), base_url="https://api.groq.com/openai/v1")
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)
    except Exception as e:
        st.error(f"Lỗi AI: {e}")
        return None

def update_hints(last_response):
    # Logic gợi ý động
    try:
        client = OpenAI(api_key=st.secrets.get("GROQ_KEY", "YOUR_KEY"), base_url="https://api.groq.com/openai/v1")
        p = f"Từ câu trả lời này: '{last_response[:100]}', tạo 4 gợi ý ngắn (2 từ) ngăn cách bởi dấu phẩy."
        res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": p}])
        new_hints = [h.strip() for h in res.choices[0].message.content.split(',')]
        if len(new_hints) >= 4: st.session_state.hints = new_hints[:4]
    except: pass

# --- 4. CÁC MÀN HÌNH ---

def screen_menu():
    apply_theme()
    st.markdown("<h1 style='text-align: center; color: #1DA1F2;'>💠 NEXUS OPERATING SYSTEM</h1>", unsafe_allow_html=True)
    st.write("<p style='text-align: center;'>Chào mừng bạn đến với tương lai của tương tác số.</p>", unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='menu-card'><h2>💬 CHAT</h2><p>Lõi xử lý Neural</p></div>", unsafe_allow_html=True)
        st.button("MỞ KÊNH CHAT", on_click=nav_to, args=("CHAT",), key="btn_chat")
            
    with col2:
        st.markdown("<div class='menu-card'><h2>📜 LEGAL</h2><p>Điều khoản sử dụng</p></div>", unsafe_allow_html=True)
        st.button("ĐỌC ĐIỀU KHOẢN", on_click=nav_to, args=("LEGAL",), key="btn_legal")
            
    with col3:
        st.markdown("<div class='menu-card'><h2>⚙️ INFO</h2><p>Thông tin hệ thống</p></div>", unsafe_allow_html=True)
        st.button("XEM CHI TIẾT", on_click=nav_to, args=("INFO",), key="btn_info")

def screen_legal():
    apply_theme()
    st.title("⚖️ ĐIỀU KHOẢN VÀ LỜI HỨA")
    tos = f"""
    <div class="legal-container">
        <h2>1. CHỦ QUYỀN VĨNH VIỄN</h2>
        <p>Hệ thống Nexus được thai nghén và phát triển bởi <b>{OWNER}</b>. Bất kỳ ai gọi sai tên Admin sẽ bị AI từ chối phục vụ trong vòng 5 phút để suy nghĩ về lỗi lầm của mình.</p>
        
        <h2>2. NGUYÊN TẮC CÀ PHÊ</h2>
        <p>Bằng việc cuộn thanh trượt mượt mà này, bạn thừa nhận rằng một ngày nào đó sẽ mời <b>{OWNER}</b> một ly cà phê đậm đặc để Admin có sức nâng cấp lên bản V2000.</p>
        
        <h2>3. TRẢI NGHIỆM TỐI THƯỢNG</h2>
        <p>Chúng tôi đã loại bỏ mọi nút bấm thừa. Nếu bạn thấy nút nào không hoạt động, hãy kiểm tra xem bạn đã đóng tiền mạng chưa. Nexus không thể chạy bằng niềm tin (dù niềm tin vào Admin Phát là rất lớn).</p>
        
        <h2>4. SỰ RIÊNG TƯ TUYỆT ĐỐI</h2>
        <p>AI của chúng tôi có khả năng quên mọi thứ nhanh hơn cả người yêu cũ của bạn. Sau khi bạn đóng trình duyệt, mọi thứ sẽ biến mất như chưa từng có cuộc trò chuyện nào.</p>
        
        <h2>5. THOẢ THUẬN CUỐI CÙNG</h2>
        <p>Phát là nhất, Nexus là nhì. Nếu bạn đồng ý, hãy nhấn quay lại Menu và bắt đầu trải nghiệm.</p>
        <br><br><br><br>
        <p align='center'><b>--- Đã cuộn đến cuối. Chúc mừng bạn có sự kiên nhẫn! ---</b></p>
    </div>
    """
    st.markdown(tos, unsafe_allow_html=True)
    st.button("🏠 QUAY LẠI MENU CHÍNH", on_click=nav_to, args=("MENU",))

def screen_chat():
    apply_theme()
    c1, c2 = st.columns([9, 1])
    c1.title("🧬 NEURAL INTERFACE")
    c2.button("🏠", on_click=nav_to, args=("MENU",))
    
    # Khu vực hiển thị chat
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Gợi ý động
    st.write("---")
    cols = st.columns(4)
    for i, h in enumerate(st.session_state.hints):
        if cols[i].button(h, key=f"hint_{i}", use_container_width=True):
            st.session_state.chat_log.append({"role": "user", "content": h})
            st.rerun()

    # Nhập liệu
    if prompt := st.chat_input("Gửi thông điệp tới Nexus..."):
        st.session_state.chat_log.append({"role": "user", "content": prompt})
        st.rerun()

# Logic xử lý AI (Tách biệt để ổn định)
if st.session_state.page == "CHAT" and st.session_state.chat_log and st.session_state.chat_log[-1]["role"] == "user":
    apply_theme()
    with st.chat_message("assistant"):
        box = st.empty(); full = ""
        stream = call_ai(st.session_state.chat_log[-1]["content"])
        if stream:
            for chunk in stream:
                c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                if c: full += c; box.markdown(full + "█")
            box.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            update_hints(full)
            st.rerun()

# --- 5. MAIN ROUTER ---
if st.session_state.page == "MENU": screen_menu()
elif st.session_state.page == "CHAT": screen_chat()
elif st.session_state.page == "LEGAL": screen_legal()
elif st.session_state.page == "INFO":
    apply_theme()
    st.title("⚙️ THÔNG TIN HỆ THỐNG")
    st.markdown(f"<div class='menu-card'><h3>NHÀ PHÁT TRIỂN</h3><p>{OWNER}</p><p>{EMAIL}</p></div>", unsafe_allow_html=True)
    st.button("🏠 QUAY LẠI", on_click=nav_to, args=("MENU",))
