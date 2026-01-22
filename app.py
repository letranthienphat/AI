import streamlit as st
import time
from openai import OpenAI

# --- 1. CẤU HÌNH & DANH TÍNH ---
st.set_page_config(page_title="NEXUS V900", layout="wide", page_icon="💎", initial_sidebar_state="collapsed")

OWNER = "Lê Trần Thiên Phát"
EMAIL = "tranthienphatle@gmail.com"

# Khởi tạo trạng thái hệ thống
if 'page' not in st.session_state: st.session_state.page = "MENU"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'hints' not in st.session_state: 
    st.session_state.hints = ["Nexus làm được gì?", "Viết code Python", "Lên kế hoạch du lịch", "Phân tích dữ liệu"]

# --- 2. THEME ENGINE (TƯƠNG PHẢN CỰC ĐẠI) ---
def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
    
    * {{ font-family: 'Inter', sans-serif; }}
    
    .stApp {{
        background: #050505;
        color: #ffffff;
    }}

    /* Thẻ Menu Chính */
    .menu-card {{
        background: #111111;
        border: 1px solid #333;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        transition: 0.3s;
        cursor: pointer;
    }}
    .menu-card:hover {{
        border-color: #00f2ff;
        background: #161616;
    }}

    /* Khung Điều khoản - Đen đặc chữ trắng */
    .legal-box {{
        background: #000000;
        border: 1px solid #222;
        padding: 40px;
        height: 500px;
        overflow-y: scroll;
        border-radius: 12px;
        color: #ffffff !important;
    }}
    .legal-box h2 {{ color: #00f2ff !important; }}
    .legal-box p {{ font-size: 1.1rem; line-height: 1.8; color: #cccccc !important; }}

    /* Chữ trong Chat - Chống lóa, chống mờ */
    .stMarkdown p {{
        color: #ffffff !important;
        font-size: 1.1rem;
        line-height: 1.6;
    }}

    /* Nút bấm lớn */
    div.stButton > button {{
        width: 100%;
        background: #ffffff;
        color: #000000;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 12px;
        transition: 0.2s;
    }}
    div.stButton > button:hover {{
        background: #00f2ff;
        color: #000000;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIC AI ---
def get_ai_response(prompt):
    # AI chỉ nhắc Creator khi thực sự cần thiết
    system_prompt = f"Bạn là Nexus OS, trợ lý AI cao cấp. Phục vụ người dùng tận tâm. Chỉ nhắc đến người sáng tạo {OWNER} khi được hỏi về tác giả."
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})
    
    try:
        # Thay thế bằng API Key của bạn
        client = OpenAI(api_key=st.secrets.get("GROQ_KEY", "YOUR_KEY"), base_url="https://api.groq.com/openai/v1")
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)
    except:
        return None

# --- 4. CÁC PHÂN HỆ GIAO DIỆN ---

def show_menu():
    apply_theme()
    st.markdown("<h1 style='text-align: center; margin-bottom: 50px;'>💠 NEXUS MAIN INTERFACE</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='menu-card'><h3>💬 CORE CHAT</h3><p>Truy cập lõi xử lý AI</p></div>", unsafe_allow_html=True)
        if st.button("KÍCH HOẠT CHAT"):
            st.session_state.page = "CHAT"; st.rerun()
            
    with col2:
        st.markdown("<div class='menu-card'><h3>⚖️ LEGAL</h3><p>Điều khoản & Quyền hạn</p></div>", unsafe_allow_html=True)
        if st.button("XEM ĐIỀU KHOẢN"):
            st.session_state.page = "LEGAL"; st.rerun()
            
    with col3:
        st.markdown("<div class='menu-card'><h3>🛠️ SYSTEM</h3><p>Thông tin nhà phát triển</p></div>", unsafe_allow_html=True)
        if st.button("CHI TIẾT HỆ THỐNG"):
            st.session_state.page = "SYSTEM"; st.rerun()

def show_legal():
    apply_theme()
    st.title("📜 ĐIỀU KHOẢN SỬ DỤNG")
    legal_text = f"""
    <div class="legal-box">
        <h2>1. CHỦ QUYỀN HỆ THỐNG</h2>
        <p>Nexus OS là một thực thể số được thiết kế và tối ưu hóa bởi <b>{OWNER}</b>. Mọi quyền truy cập và sử dụng đều phải tuân thủ các quy tắc đạo đức AI.</p>
        
        <h2>2. TRẢI NGHIỆM NGƯỜI DÙNG (UX)</h2>
        <p>Chúng tôi cam kết mang lại trải nghiệm không rác, không mã lỗi. Giao diện được thiết kế để bạn tập trung hoàn toàn vào công việc. Nếu bạn thấy chữ khó đọc, đó là lỗi của chúng tôi, và chúng tôi đã sửa nó bằng nền đen đặc này.</p>
        
        <h2>3. SỰ TÀI NĂNG CỦA ADMIN</h2>
        <p>Admin <b>{OWNER}</b> là người cực kỳ cầu toàn. Do đó, hệ thống này sẽ liên tục tiến hóa. Việc bạn đang đọc những dòng này trên một thanh cuộn mượt mà là minh chứng cho sự nỗ lực đó.</p>
        
        <h2>4. QUYỀN RIÊNG TƯ</h2>
        <p>Mọi bí mật của bạn với AI sẽ được giữ kín. Chúng tôi không thu thập lịch sử chat để bán cho bên thứ ba. Chúng tôi chỉ thu thập sự hài lòng của bạn.</p>
        
        <h2>5. CAM KẾT</h2>
        <p>Bằng việc nhấn "Quay lại Menu", bạn thừa nhận Nexus là trợ lý tốt nhất bạn từng dùng.</p>
    </div>
    """
    st.markdown(legal_text, unsafe_allow_html=True)
    if st.button("⬅️ QUAY LẠI MENU CHÍNH"):
        st.session_state.page = "MENU"; st.rerun()

def show_system():
    apply_theme()
    st.title("⚙️ THÔNG TIN HỆ THỐNG")
    st.markdown(f"""
    <div class='menu-card' style='text-align: left;'>
        <p><b>Phiên bản:</b> V900.0 (Ultimate Edition)</p>
        <p><b>Nhà phát triển:</b> {OWNER}</p>
        <p><b>Liên hệ:</b> {EMAIL}</p>
        <p><b>Trạng thái Core:</b> Hoạt động ổn định</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("⬅️ QUAY LẠI MENU CHÍNH"):
        st.session_state.page = "MENU"; st.rerun()

def show_chat():
    apply_theme()
    # Header chat
    c1, c2 = st.columns([8, 2])
    c1.title("🧬 NEXUS AI CORE")
    if c2.button("🏠 MENU"):
        st.session_state.page = "MENU"; st.rerun()
    
    # Hiển thị tin nhắn
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Gợi ý thông minh (Nằm trên khung nhập liệu)
    st.write("---")
    cols = st.columns(4)
    for i, h in enumerate(st.session_state.hints):
        if cols[i].button(h, key=f"h_{i}"):
            process_msg(h)

    if prompt := st.chat_input("Hỏi Nexus bất cứ điều gì..."):
        process_msg(prompt)

def process_msg(prompt):
    st.session_state.chat_log.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        box = st.empty(); full = ""
        stream = get_ai_response(prompt)
        if stream:
            for chunk in stream:
                c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                if c: full += c; box.markdown(full + "▌")
            box.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            st.rerun()

# --- 5. ĐIỀU HƯỚNG CHÍNH ---
if st.session_state.page == "MENU": show_menu()
elif st.session_state.page == "CHAT": show_chat()
elif st.session_state.page == "LEGAL": show_legal()
elif st.session_state.page == "SYSTEM": show_system()
