# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="NEXUS V2100", layout="wide", initial_sidebar_state="collapsed")

# Thông tin chủ nhân (Chỉ hiện trong Info hoặc khi AI được hỏi)
OWNER_NAME = "Anh ấy"
OWNER_DETAILS = "Học sinh lớp 7A1 - Trường THCS-THPT Nguyễn Huệ"

try:
    API_LIST = st.secrets.get("GROQ_KEYS", [])
    ACTIVE_KEY = API_LIST[0] if API_LIST else st.secrets.get("GROQ_KEY", "")
except:
    ACTIVE_KEY = ""

if 'stage' not in st.session_state: st.session_state.stage = "LAW"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'hints' not in st.session_state: 
    st.session_state.hints = ["Nexus có thể giúp gì?", "Phân tích dữ liệu", "Sáng tạo nội dung"]

def nav(p): st.session_state.stage = p

# --- 2. GIAO DIỆN TITAN MINIMALIST (TỐI ƯU TƯƠNG PHẢN) ---
def apply_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-color: #000000; }}

    /* LOGO TỐI GIẢN */
    .logo-box {{ text-align: center; padding: 50px 0; }}
    .logo-text {{
        font-size: clamp(40px, 10vw, 80px);
        font-weight: 900; color: #ffffff;
        letter-spacing: -2px; text-transform: uppercase;
    }}

    /* NÚT BẤM MENU LỚN (MOBILE FRIENDLY) */
    div.stButton > button {{
        width: 100% !important; min-height: 100px !important;
        background: #0a0a0a !important; border: 1px solid #222 !important;
        border-radius: 20px !important; color: #ffffff !important;
        font-size: 1.2rem !important; font-weight: 700 !important;
        transition: 0.3s; margin-bottom: 10px;
    }}
    div.stButton > button:hover {{
        border-color: #ffffff !important; background: #111111 !important;
        transform: translateY(-3px);
    }}

    /* KHUNG CHAT AI (TƯƠNG PHẢN CỰC ĐẠI) */
    .stChatMessage.assistant {{
        background: #FFFFFF !important;
        border-radius: 20px !important;
        padding: 25px !important;
        margin-bottom: 20px;
    }}
    .stChatMessage.assistant * {{ color: #000000 !important; font-size: 1.15rem; line-height: 1.6; }}

    /* GỢI Ý ĐỘNG */
    .hint-container div.stButton > button {{
        min-height: 45px !important; height: auto !important;
        background: #ffffff !important; color: #000 !important;
        border-radius: 50px !important; font-size: 0.9rem !important;
    }}

    /* ĐIỀU KHOẢN */
    .law-card {{
        background: #050505; border: 1px solid #1a1a1a;
        padding: 40px; border-radius: 30px; height: 450px; overflow-y: auto;
    }}
    .law-card h1 {{ color: #ffffff; }}
    .law-card p {{ color: #888; line-height: 1.8; }}

    /* NÚT BACK CỐ ĐỊNH Ở CUỐI */
    .nav-footer {{
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: rgba(0,0,0,0.8); backdrop-filter: blur(10px);
        padding: 10px; text-align: center; border-top: 1px solid #222;
        z-index: 100;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI AI ---
def get_ai_res(prompt):
    if not ACTIVE_KEY: return "⚠️ Hệ thống chưa sẵn sàng. Vui lòng kiểm tra Secret Key."
    try:
        client = OpenAI(api_key=ACTIVE_KEY, base_url="https://api.groq.com/openai/v1")
        # AI Biết về chủ nhân nhưng chỉ nói khi được hỏi
        system_msg = f"Bạn là Nexus OS. Chủ nhân của bạn là {OWNER_NAME} ({OWNER_DETAILS}). Chỉ nhắc đến thông tin lớp/trường khi anh ấy hỏi hoặc đề cập đến."
        
        # Gợi ý động theo thời gian thực
        if "học" in prompt.lower() or "toán" in prompt.lower():
            st.session_state.hints = ["Giải toán nâng cao", "Viết văn sáng tạo", "Phương pháp nhớ nhanh"]
        elif "code" in prompt.lower():
            st.session_state.hints = ["Tối ưu logic", "Tìm lỗi sai", "Giải thích mã"]
        else:
            st.session_state.hints = ["Nói sâu hơn về ý này", "Cho ví dụ minh họa", "Tóm tắt ngắn gọn"]

        return client.chat.completions.create(model="llama-3.3-70b-versatile", 
                                            messages=[{"role": "system", "content": system_msg},
                                                      {"role": "user", "content": prompt}], 
                                            stream=True)
    except Exception as e: return f"❌ Lỗi: {str(e)}"

# --- 4. MÀN HÌNH ---

def screen_law():
    apply_ui()
    st.markdown("<div class='logo-box'><div class='logo-text'>NEXUS OS</div></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="law-card">
        <h1>📜 HIỆP ƯỚC PHIÊN BẢN V2100</h1>
        <p>Chào mừng <b>{OWNER_NAME}</b>. Bạn đang sử dụng hệ điều hành AI tối giản Titan.</p>
        <h2>1. Bảo mật tối đa</h2>
        <p>Mọi thông tin cá nhân của bạn được mã hóa và cất giữ trong phần giới thiệu hệ thống. Không hiển thị công khai ở giao diện ngoài.</p>
        <h2>2. Tương tác mượt mà</h2>
        <p>Giao diện được thiết kế để tập trung vào nội dung cuộc trò chuyện. Các nút bấm được tối ưu hóa cho cả máy tính và điện thoại.</p>
        <h2>3. Trí tuệ thích nghi</h2>
        <p>Nexus sẽ học hỏi phong cách của bạn để đưa ra các phản hồi ngày càng chính xác và hữu ích hơn.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("XÁC NHẬN DỊCH VỤ", use_container_width=True):
        nav("MENU"); st.rerun()

def screen_menu():
    apply_ui()
    st.markdown("<div class='logo-box'><div class='logo-text'>CENTRAL UNIT</div></div>", unsafe_allow_html=True)
    st.button("🧠 KÍCH HOẠT NEURAL CHAT", on_click=nav, args=("CHAT",))
    st.button("🛠️ CHI TIẾT HỆ THỐNG", on_click=nav, args=("INFO",))
    st.button("📜 ĐIỀU KHOẢN", on_click=nav, args=("LAW",))

def screen_chat():
    apply_ui()
    st.markdown("<h3 style='color:white; text-align:center;'>NEURAL INTERFACE</h3>", unsafe_allow_html=True)
    
    # Khu vực chat
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Gợi ý động chân trang
    st.write("---")
    cols = st.columns(len(st.session_state.hints))
    for i, h in enumerate(st.session_state.hints):
        if cols[i].button(h, key=f"hint_{i}"):
            st.session_state.chat_log.append({"role": "user", "content": h})
            st.rerun()

    if p := st.chat_input("Nhập lệnh cho Nexus..."):
        st.session_state.chat_log.append({"role": "user", "content": p})
        st.rerun()

    if st.session_state.chat_log and st.session_state.chat_log[-1]["role"] == "user":
        with st.chat_message("assistant"):
            placeholder = st.empty(); full_text = ""
            res = get_ai_res(st.session_state.chat_log[-1]["content"])
            if isinstance(res, str): st.error(res)
            else:
                for chunk in res:
                    content = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                    if content: full_text += content; placeholder.markdown(full_text + "█")
                placeholder.markdown(full_text)
                st.session_state.chat_log.append({"role": "assistant", "content": full_text})
                st.rerun()
    
    # Nút Quay về cố định ở dưới cùng
    st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
    with st.container():
        st.button("🏠 QUAY LẠI MENU CHÍNH", on_click=nav, args=("MENU",), use_container_width=True)

def screen_info():
    apply_ui()
    st.markdown("<div class='logo-box'><div class='logo-text'>SYSTEM INFO</div></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='background:#0a0a0a; padding:30px; border-radius:20px; border:1px solid #222;'>
        <h2 style='color:white;'>Người tạo ra: {OWNER_NAME}</h2>
        <p style='color:#00f2ff; font-size:1.2rem;'><b>{OWNER_DETAILS}</b></p>
        <p style='color:#888;'>Phiên bản: V2100 Minimalist Titan</p>
        <p style='color:#888;'>Cốt lõi: Llama-3.3-70B Neural Engine</p>
        <hr style='border-color:#222;'>
        <p style='color:#555;'>Mọi thông tin chi tiết về anh ấy chỉ được lưu trữ tại đây nhằm đảm bảo tính thẩm mỹ cho giao diện chính.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🏠 QUAY LẠI MENU"): nav("MENU"); st.rerun()

# --- 5. ĐIỀU HƯỚNG ---
if st.session_state.stage == "LAW": screen_law()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "INFO": screen_info()
