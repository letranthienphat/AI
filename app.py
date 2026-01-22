import streamlit as st
from openai import OpenAI
import time

# --- 1. CONFIG & IDENTITY ---
st.set_page_config(page_title="NEXUS V1100", layout="wide", page_icon="🧬", initial_sidebar_state="collapsed")

OWNER = "Lê Trần Thiên Phát"
# CHÚ Ý: Điền API Key của bạn vào đây hoặc trong st.secrets
GROQ_API_KEY = st.secrets.get("GROQ_KEY", "ĐIỀN_MÃ_API_CỦA_BẠN_VÀO_ĐÂY") 

if 'page' not in st.session_state: st.session_state.page = "MENU"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'hints' not in st.session_state: 
    st.session_state.hints = ["Nexus có thể làm gì?", "Viết code Python", "Lên kế hoạch du lịch", "Phân tích dữ liệu"]

def nav_to(page_name):
    st.session_state.page = page_name

# --- 2. CSS QUANTUM (BIẾN BUTTON THÀNH CARD) ---
def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    
    .stApp {{ background: #000000; color: #FFFFFF; }}

    /* BIẾN ST.BUTTON THÀNH THẺ CARD NHẤN ĐƯỢC */
    div.stButton > button {{
        width: 100%;
        height: 250px;
        background: rgba(20, 20, 20, 0.8) !important;
        border: 1px solid rgba(0, 242, 255, 0.2) !important;
        border-radius: 20px !important;
        color: white !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        transition: 0.4s all ease-in-out;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }}
    
    div.stButton > button:hover {{
        background: rgba(0, 242, 255, 0.1) !important;
        border-color: #00f2ff !important;
        box-shadow: 0 0 30px rgba(0, 242, 255, 0.3);
        transform: translateY(-10px);
    }}

    /* Tinh chỉnh nút quay lại và nút chat nhỏ */
    .small-btn div.stButton > button {{
        height: auto !important;
        padding: 10px !important;
        font-size: 1rem !important;
    }}

    /* Khung điều khoản */
    .legal-box {{
        background: #050505;
        border: 1px solid #222;
        padding: 40px;
        height: 500px;
        overflow-y: scroll;
        border-radius: 20px;
    }}
    .legal-box h2 {{ color: #00f2ff; }}
    .legal-box p {{ color: #ccc; line-height: 1.8; font-size: 1.1rem; }}

    /* Chat Styling */
    div[data-testid="stChatMessage"] {{
        background: rgba(255,255,255,0.03); border-radius: 15px; border: 1px solid #222;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. AI ENGINE ---
def call_ai(prompt):
    if "ĐIỀU_MÃ_API" in GROQ_API_KEY:
        st.error("Lỗi: Bạn chưa điền API Key vào mã nguồn!")
        return None
        
    client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    sys_prompt = f"Bạn là Nexus, trợ lý AI cao cấp. Phục vụ người dùng tận tâm. Chỉ nhắc đến người sáng tạo {OWNER} khi được hỏi về tác giả."
    
    messages = [{"role": "system", "content": sys_prompt}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})
    
    try:
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}")
        return None

# --- 4. CÁC PHÂN HỆ MÀN HÌNH ---

def show_menu():
    apply_theme()
    st.markdown("<h1 style='text-align: center; margin-bottom: 50px; color: #00f2ff;'>💠 NEXUS QUANTUM HUB</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    # Ở đây mỗi nút bấm đóng vai trò là một cái Card lớn
    with col1:
        st.button("💬\n\nAI CHAT CORE", on_click=nav_to, args=("CHAT",))
            
    with col2:
        st.button("⚖️\n\nLEGAL PROTOCOL", on_click=nav_to, args=("LEGAL",))
            
    with col3:
        st.button("⚙️\n\nSYSTEM INFO", on_click=nav_to, args=("INFO",))

def show_chat():
    apply_theme()
    st.markdown('<div class="small-btn">', unsafe_allow_html=True)
    c1, c2 = st.columns([9, 1])
    c1.title("🧬 NEURAL INTERFACE")
    c2.button("🏠", on_click=nav_to, args=("MENU",))
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Hiển thị hội thoại
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Gợi ý
    st.write("---")
    cols = st.columns(4)
    for i, h in enumerate(st.session_state.hints):
        if cols[i].button(h, key=f"h_{i}"):
            st.session_state.chat_log.append({"role": "user", "content": h})
            st.rerun()

    if prompt := st.chat_input("Hỏi bất cứ điều gì..."):
        st.session_state.chat_log.append({"role": "user", "content": prompt})
        st.rerun()

    # Xử lý phản hồi AI
    if st.session_state.chat_log and st.session_state.chat_log[-1]["role"] == "user":
        with st.chat_message("assistant"):
            box = st.empty(); full = ""
            stream = call_ai(st.session_state.chat_log[-1]["content"])
            if stream:
                for chunk in stream:
                    c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                    if c: full += c; box.markdown(full + "▌")
                box.markdown(full)
                st.session_state.chat_log.append({"role": "assistant", "content": full})
                st.rerun()

def show_legal():
    apply_theme()
    st.title("📜 ĐIỀU KHOẢN")
    st.markdown(f"""
    <div class="legal-box">
        <h2>1. ĐẶC QUYỀN CỦA PHÁT</h2>
        <p>Hệ thống này được tối ưu hóa bởi <b>{OWNER}</b>. Mọi trải nghiệm mượt mà bạn đang thấy đều đến từ sự cầu toàn của Admin.</p>
        <h2>2. TRẢI NGHIỆM KHÔNG NÚT THỪA</h2>
        <p>Ở phiên bản V1100, chúng tôi loại bỏ các nút bấm nhỏ. Toàn bộ các thẻ Card ở Menu giờ đây đều có thể nhấn trực tiếp. Đây là tiêu chuẩn trải nghiệm hàng đầu.</p>
        <h2>3. BẢO MẬT</h2>
        <p>Nexus không lưu giữ bất kỳ dữ liệu nào sau khi bạn đóng trình duyệt. Quyền riêng tư là ưu tiên số 1.</p>
    </div>
    """, unsafe_allow_html=True)
    st.button("🏠 QUAY LẠI MENU", on_click=nav_to, args=("MENU",))

# --- 5. ĐIỀU HƯỚNG ---
if st.session_state.page == "MENU": show_menu()
elif st.session_state.page == "CHAT": show_chat()
elif st.session_state.page == "LEGAL": show_legal()
elif st.session_state.page == "INFO":
    apply_theme()
    st.title("⚙️ THÔNG TIN")
    st.write(f"Nhà phát triển: **{OWNER}**")
    st.button("🏠 QUAY LẠI", on_click=nav_to, args=("MENU",))
