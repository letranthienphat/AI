# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="NEXUS V2400", layout="wide", initial_sidebar_state="collapsed")

CREATOR_NAME = "Lê Trần Thiên Phát"
CREATOR_DETAILS = "Học sinh lớp 7A1 - Trường THCS-THPT Nguyễn Huệ"

try:
    API_LIST = st.secrets.get("GROQ_KEYS", [])
    ACTIVE_KEY = API_LIST[0] if API_LIST else st.secrets.get("GROQ_KEY", "")
except:
    ACTIVE_KEY = ""

# Khởi tạo Session State
if 'stage' not in st.session_state: st.session_state.stage = "IDENTITY"
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'hints' not in st.session_state: st.session_state.hints = ["Nexus là gì?", "Ai tạo ra bạn?", "Khám phá tính năng"]
if 'info_tab' not in st.session_state: st.session_state.info_tab = "CREATOR"

def nav(p): st.session_state.stage = p

# --- 2. CSS "PLASMA GLOW" & TƯƠNG PHẢN CỰC ĐẠI ---
def apply_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-color: #000000; color: #ffffff; }}

    /* LOGO */
    .logo-text {{
        font-size: clamp(40px, 12vw, 85px);
        font-weight: 900; text-align: center; padding: 30px 0;
        color: #ffffff; letter-spacing: -3px; text-transform: uppercase;
    }}

    /* NÚT BẤM SÁNG VIỀN PLASMA KHI NHẤN */
    div.stButton > button {{
        width: 100% !important; min-height: 85px !important;
        background: #0a0a0a !important; border: 2px solid #222 !important;
        border-radius: 20px !important; color: #fff !important;
        font-size: 1.2rem !important; font-weight: 800 !important;
        transition: all 0.1s ease; margin-bottom: 12px;
    }}
    div.stButton > button:active {{
        border-color: #00f2ff !important;
        box-shadow: 0 0 30px #00f2ff !important;
        transform: scale(0.97);
    }}
    div.stButton > button:hover {{ border-color: #555; }}

    /* PHẢN HỒI AI (TRẮNG TUYẾT - CHỮ ĐEN) */
    .stChatMessage.assistant {{
        background: #FFFFFF !important; border-radius: 22px !important;
        padding: 25px !important; margin: 15px 0 !important;
        box-shadow: 0 10px 40px rgba(0,242,255,0.1);
    }}
    .stChatMessage.assistant * {{ color: #000000 !important; font-weight: 500; font-size: 1.15rem; }}

    /* HIỆP ƯỚC & INFO BOX */
    .content-box {{
        background: #050505; border: 1px solid #222; padding: 30px;
        border-radius: 30px; height: 500px; overflow-y: auto;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI AI & GỢI Ý ĐỘNG ĐA NGƯỜI DÙNG ---
def call_nexus_core(prompt):
    if not ACTIVE_KEY: return "⚠️ Missing API Key!"
    try:
        client = OpenAI(api_key=ACTIVE_KEY, base_url="https://api.groq.com/openai/v1")
        is_owner = st.session_state.user_name.lower() == CREATOR_NAME.lower()
        
        system_instr = f"""Bạn là Nexus OS. Người tạo ra bạn là {CREATOR_NAME} (anh ấy). 
        Người đang trò chuyện với bạn là {st.session_state.user_name}. 
        Nếu người dùng là {CREATOR_NAME}, hãy phục vụ với thái độ tôn trọng nhất. 
        Nếu là người khác, hãy lịch sự nhưng luôn khẳng định {CREATOR_NAME} là chủ nhân của bạn.
        Tuyệt đối không nhận là Meta AI. Trả lời đàng hoàng, chuyên nghiệp."""
        
        # LOGIC GỢI Ý ĐỘNG THEO NGỮ CẢNH
        low_p = prompt.lower()
        if "học" in low_p: st.session_state.hints = ["Mẹo nhớ lâu", "Giải toán khó", "Viết văn mẫu"]
        elif "ai" in low_p or "tạo" in low_p: st.session_state.hints = ["Về Thiên Phát", "Tính năng Nexus", "Lịch sử bản V2400"]
        else: st.session_state.hints = ["Phân tích sâu", "Lập trình tối ưu", "Kể chuyện thư giãn"]

        return client.chat.completions.create(model="llama-3.3-70b-versatile", 
                                            messages=[{"role": "system", "content": system_instr},
                                                      {"role": "user", "content": prompt}], 
                                            stream=True)
    except Exception as e: return f"Error: {str(e)}"

# --- 4. CÁC MÀN HÌNH ---

def screen_identity():
    apply_ui()
    st.markdown("<div class='logo-text'>NEXUS GATEWAY</div>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<h3 style='text-align:center;'>XÁC MINH DANH TÍNH NGƯỜI DÙNG</h3>", unsafe_allow_html=True)
        name = st.text_input("Vui lòng nhập tên của bạn để tiếp tục:", placeholder="Nhập tên tại đây...")
        if st.button("TRUY CẬP HỆ THỐNG 🔓"):
            if name:
                st.session_state.user_name = name
                nav("LAW"); st.rerun()
            else: st.warning("Vui lòng nhập danh tính.")

def screen_law():
    apply_ui()
    st.markdown("<div class='logo-text'>HIỆP ƯỚC</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="content-box">
        <h1 style='color:#00f2ff;'>📜 ĐIỀU KHOẢN TITAN V2400</h1>
        <p>Xin chào <b>{st.session_state.user_name}</b>,</p>
        <h3>1. Bản quyền trí tuệ</h3>
        <p>Hệ thống này thuộc sở hữu trí tuệ của <b>{CREATOR_NAME}</b> (Lớp 7A1 Nguyễn Huệ). Mọi hành vi nhận vơ sẽ bị AI cười nhạo.</p>
        <h3>2. Trách nhiệm người dùng</h3>
        <p>Dùng Nexus để trở nên thông minh hơn, không dùng để gian lận hay làm việc xấu. AI có mắt ở khắp nơi (đùa thôi!).</p>
        <h3>3. Hào quang nút bấm</h3>
        <p>Mỗi khi bạn nhấn nút và nó sáng lên, hãy nhớ rằng đó là công sức của Kiến trúc sư Phát đã thức đêm để code hiệu ứng Plasma cho bạn xem đấy.</p>
        <h3>4. Quyền riêng tư</h3>
        <p>Nội dung của bạn sẽ được giữ kín, trừ khi bạn hỏi những câu quá ngớ ngẩn khiến AI phải đi kể với chủ nhân của nó.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("TÔI ĐÃ HIỂU VÀ ĐỒNG Ý ✅"): nav("MENU"); st.rerun()

def screen_menu():
    apply_ui()
    welcome = f"Chào chủ nhân {CREATOR_NAME}!" if st.session_state.user_name.lower() == CREATOR_NAME.lower() else f"Chào khách quý {st.session_state.user_name}!"
    st.markdown(f"<div class='logo-text'>NEXUS HUB</div><p style='text-align:center; color:#00f2ff;'>{welcome}</p>", unsafe_allow_html=True)
    
    st.button("🧠 NEURAL INTERFACE (CHAT)", on_click=nav, args=("CHAT",))
    st.button("📊 THÔNG TIN HỆ THỐNG", on_click=nav, args=("INFO",))
    st.button("🔄 ĐỔI NGƯỜI DÙNG", on_click=nav, args=("IDENTITY",))

def screen_chat():
    apply_ui()
    st.markdown("<h3 style='text-align:center; color:#00f2ff;'>🧬 NEURAL CORE</h3>", unsafe_allow_html=True)
    
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # GỢI Ý ĐỘNG
    st.write("---")
    cols = st.columns(len(st.session_state.hints))
    for i, h in enumerate(st.session_state.hints):
        if cols[i].button(h, key=f"hint_{i}"):
            st.session_state.chat_log.append({"role": "user", "content": h})
            st.rerun()

    if p := st.chat_input("Gửi thông điệp..."):
        st.session_state.chat_log.append({"role": "user", "content": p})
        st.rerun()

    if st.session_state.chat_log and st.session_state.chat_log[-1]["role"] == "user":
        with st.chat_message("assistant"):
            box = st.empty(); full = ""
            res = call_nexus_core(st.session_state.chat_log[-1]["content"])
            if isinstance(res, str): st.error(res)
            else:
                for chunk in res:
                    c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                    if c:
                        full += c
                        box.markdown(full + "▌")
                        time.sleep(0.01) # Typewriter effect
                box.markdown(full)
                st.session_state.chat_log.append({"role": "assistant", "content": full})
                st.rerun()
    
    st.button("🏠 QUAY LẠI MENU", on_click=nav, args=("MENU",), use_container_width=True)

def screen_info():
    apply_ui()
    st.markdown("<div class='logo-text'>SYSTEM INFO</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("👤 NGƯỜI SÁNG TẠO"): st.session_state.info_tab = "CREATOR"
    with c2: 
        if st.button("📜 PHIÊN BẢN & LỊCH SỬ"): st.session_state.info_tab = "VERSION"

    st.markdown("---")
    if st.session_state.info_tab == "CREATOR":
        st.markdown(f"""
        <div style='background:#111; padding:30px; border-radius:20px; border-left:5px solid #00f2ff;'>
            <h2 style='color:#fff;'>Lê Trần Thiên Phát</h2>
            <p style='font-size:1.2rem; color:#00f2ff;'><b>{CREATOR_DETAILS}</b></p>
            <p>Anh ấy là bộ não đằng sau toàn bộ hệ điều hành Nexus. Mọi chi tiết từ màu sắc nút bấm đến logic AI đều được anh ấy phê duyệt.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='background:#111; padding:30px; border-radius:20px;'>
            <h3>Thông tin Nexus V2400</h3>
            <p>• <b>Phiên bản:</b> V2400 Multi-Identity Titan</p>
            <p>• <b>Ngày phát hành:</b> 29/01/2026</p>
            <h3>Lịch sử cập nhật:</h3>
            <p>- Thêm cổng định danh người dùng đầu vào.<br>
            - Nâng cấp nút bấm Plasma Glow (Sáng viền khi nhấn).<br>
            - Tối ưu hóa phản hồi AI: Trắng tinh khiết - Chữ đen đậm.<br>
            - Tách biệt hoàn toàn mục Người sáng tạo và Lịch sử hệ thống.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.button("🏠 QUAY LẠI MENU", on_click=nav, args=("MENU",))

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "IDENTITY": screen_identity()
elif st.session_state.stage == "LAW": screen_law()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "INFO": screen_info()
