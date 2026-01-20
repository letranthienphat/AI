import streamlit as st
import time
import json
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai

# --- 1. CẤU HÌNH HỆ THỐNG & SESSION STATE ---
st.set_page_config(page_title="NEXUS V70.0 - PRESTIGE", layout="wide", page_icon="🛡️")

if 'stage' not in st.session_state: st.session_state.stage = "terms" # terms -> hub -> chat
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'bg_url' not in st.session_state: st.session_state.bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072"
if 'dynamic_hints' not in st.session_state: st.session_state.dynamic_hints = ["Bắt đầu vụ án", "Kiểm tra hệ thống", "Phân tích bối cảnh"]

GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# --- 2. GIAO DIỆN TƯƠNG PHẢN CAO & HIỆU ỨNG KÍNH (CSS) ---
def apply_style():
    st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.9)), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}
    /* Panel kính cường lực */
    .glass-panel {{
        background: rgba(15, 20, 25, 0.95);
        border: 1px solid #00f2ff44;
        border-radius: 15px; padding: 25px;
        margin-bottom: 20px; color: white;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }}
    .hint-btn {{
        background: rgba(0, 242, 255, 0.1);
        border: 1px solid #00f2ff;
        color: #00f2ff !important;
        border-radius: 20px; padding: 5px 15px;
        cursor: pointer; transition: 0.3s;
    }}
    /* Chat message contrast */
    [data-testid="stChatMessage"] {{
        background: rgba(10, 10, 15, 0.98) !important;
        border: 1px solid #333 !important;
        color: #fff !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. CÁC MODULE GIAO DIỆN ---

def show_terms():
    """Màn hình Điều khoản & Thông tin phiên bản"""
    apply_style()
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.container():
        st.markdown("""
        <div class='glass-panel'>
            <h1 style='color:#00f2ff; text-align:center;'>🛡️ ĐIỀU KHOẢN SỬ DỤNG NEXUS OS</h1>
            <hr>
            <p><b>Phiên bản:</b> V70.0 (Prestige Build)</p>
            <p><b>Mô tả:</b> Hệ thống trí tuệ nhân tạo chuyên dụng cho phân tích dữ liệu và hỗ trợ thám tử tư. 
            Tích hợp lõi xử lý đa tầng (Groq & Gemini).</p>
            <div style='height: 200px; overflow-y: scroll; border: 1px solid #333; padding: 10px; background: #000;'>
                1. Dữ liệu hội thoại được lưu trữ tạm thời trong Session State.<br>
                2. Người dùng chịu trách nhiệm về nội dung nhập liệu.<br>
                3. Hệ thống tự động đặt tên cuộc hội thoại để tối ưu quản lý.<br>
                4. Tính năng Gợi ý Động sẽ phân tích bối cảnh để hỗ trợ thao tác nhanh.<br>
                5. Bản quyền thuộc về Thiên Phát Team.
            </div>
            <br>
        </div>
        """, unsafe_allow_html=True)
        if st.button("TÔI ĐỒNG Ý VÀ KHỞI CHẠY HỆ THỐNG", use_container_width=True):
            st.session_state.stage = "hub"
            st.rerun()

def show_hub():
    """Màn hình chính (Hub)"""
    apply_style()
    st.title("💠 NEXUS CENTRAL HUB")
    
    col_chat, col_set = st.columns([2, 1])
    
    with col_chat:
        st.markdown("""
        <div class='glass-panel'>
            <h3>🤖 Trò chuyện AI</h3>
            <p>Truy cập vào Neural Interface để bắt đầu phân tích.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("MỞ NEURAL INTERFACE (CHAT) 🚀", use_container_width=True):
            st.session_state.stage = "chat"
            st.rerun()

    with col_set:
        st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
        st.subheader("⚙️ Cài đặt & Thông tin")
        st.session_state.bg_url = st.text_input("🖼️ URL Hình nền:", st.session_state.bg_url)
        if st.button("Xem lại Điều khoản"):
            st.session_state.stage = "terms"
            st.rerun()
        st.write(f"**Core:** Hybrid Llama-3.3/Gemini")
        st.write(f"**Uptime:** Active")
        st.markdown("</div>", unsafe_allow_html=True)

def get_dynamic_suggestions(last_reply):
    """AI tự tạo ra 3 gợi ý câu hỏi dựa trên phản hồi cuối"""
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        prompt = f"Dựa trên nội dung này, hãy tạo ra 3 câu hỏi gợi ý ngắn gọn (dưới 10 chữ) để người dùng hỏi tiếp: {last_reply[:300]}"
        res = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        lines = res.choices[0].message.content.strip().split('\n')
        suggestions = [line.strip('123. -') for line in lines if len(line) > 5][:3]
        return suggestions if suggestions else st.session_state.dynamic_hints
    except:
        return st.session_state.dynamic_hints

def show_chat():
    """Giao diện Chat chuyên sâu"""
    apply_style()
    if st.button("⬅️ QUAY LẠI HUB"):
        st.session_state.stage = "hub"
        st.rerun()

    st.title("🧬 Neural Interface")
    
    # Hiển thị lịch sử
    for msg in st.session_state.chat_log:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # VÙNG GỢI Ý ĐỘNG (Dynamic Hints)
    st.markdown("💡 **Gợi ý thám tử:**")
    cols = st.columns(len(st.session_state.dynamic_hints))
    for i, hint in enumerate(st.session_state.dynamic_hints):
        if cols[i].button(f"✨ {hint}", key=f"hint_{i}"):
            process_message(hint)

    if prompt := st.chat_input("Nhập lệnh..."):
        process_message(prompt)

def process_message(prompt):
    st.session_state.chat_log.append({"role": "user", "content": prompt})
    
    # Giả lập gọi AI (Tôi rút gọn logic AI ở đây để tập trung vào UX)
    with st.chat_message("assistant"):
        full_res = "Hệ thống đang phân tích: " + prompt + "... (Đây là phản hồi giả lập, hãy kết nối API để chạy thật)."
        st.markdown(full_res)
        st.session_state.chat_log.append({"role": "assistant", "content": full_res})
        # Cập nhật gợi ý động từ phản hồi mới nhất
        st.session_state.dynamic_hints = get_dynamic_suggestions(full_res)
        st.rerun()

# --- 4. ĐIỀU PHỐI LUỒNG ---
if st.session_state.stage == "terms":
    show_terms()
elif st.session_state.stage == "hub":
    show_hub()
else:
    show_chat()
