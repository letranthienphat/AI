import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random

# --- 1. CẤU HÌNH GIAO DIỆN TITAN DARK ---
st.set_page_config(page_title="Nexus OS V50.0.1.2", layout="wide", page_icon="💠")

st.markdown("""
    <style>
    .stApp { background-color: #05070a !important; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #0a0c10 !important; border-right: 1px solid #1e2630; }
    .stChatMessage { background-color: #11141a !important; border-radius: 10px; border: 1px solid #1e2630; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KẾT NỐI SECRETS (KHỚP VỚI HÌNH BẠN CHỤP) ---
try:
    # Lấy danh sách từ mục GROQ_KEYS (có chữ S)
    GROQ_POOL = st.secrets["GROQ_KEYS"] 
    # Lấy key đơn từ GEMINI_KEY
    G_KEY = st.secrets["GEMINI_KEY"]
    
    # Khởi tạo Gemini
    genai.configure(api_key=G_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("❌ LỖI KẾT NỐI SECRETS: Vui lòng kiểm tra lại bảng tên trong mục Settings -> Secrets.")
    st.stop()

# --- 3. QUẢN LÝ TRẠNG THÁI ---
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'user' not in st.session_state:
    st.session_state.user = None

# --- 4. HÀM GỌI AI FAILOVER (VÒNG LẶP KHÔNG LỖI) ---
def call_nexus_core(msgs):
    # Trộn danh sách Key để chia đều tải
    keys = list(GROQ_POOL)
    random.shuffle(keys)
    
    # Chỉ gửi 6 câu gần nhất để tránh quá tải token
    safe_history = msgs[-7:]

    # LỚP 1: THỬ CÁC KEY GROQ
    for current_key in keys:
        try:
            # SỬ DỤNG current_key THAY VÌ st.secrets["GROQ_API_KEY"] CŨ
            temp_client = OpenAI(api_key=current_key, base_url="https://api.groq.com/openai/v1")
            response = temp_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in safe_history],
                stream=True
            )
            return response, "Groq-Engine"
        except Exception:
            continue # Nếu key này lỗi (hết hạn mức), tự động nhảy sang key tiếp theo
            
    # LỚP 2: DỰ PHÒNG GEMINI (CHỐT CHẶN CUỐI)
    try:
        st.toast("⚡ Đang dùng băng tần Gemini...", icon="🛡️")
        chat = gemini_model.start_chat(history=[])
        response = chat.send_message(msgs[-1]["content"], stream=True)
        return response, "Gemini-Engine"
    except:
        return None, None

# --- 5. GIAO DIỆN ĐIỀU HÀNH ---
with st.sidebar:
    st.title("💠 NEXUS V50")
    st.caption("Status: Secure Connection")
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

if not st.session_state.user:
    st.title("🔐 Login to Nexus")
    name = st.text_input("Tên định danh:")
    if st.button("Truy cập"):
        if name:
            st.session_state.user = name
            st.rerun()
else:
    st.title(f"🤖 Terminal: {st.session_state.user}")
    
    # Hiển thị lịch sử chat
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Nhập liệu
    if prompt := st.chat_input("Gõ lệnh tại đây..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            res_area = st.empty()
            full_ans = ""
            
            # Gọi hàm AI mới
            resp, engine_name = call_nexus_core(st.session_state.messages)
            
            if resp:
                if engine_name == "Groq-Engine":
                    for chunk in resp:
                        if chunk.choices[0].delta.content:
                            full_ans += chunk.choices[0].delta.content
                            res_area.markdown(full_ans + "▌")
                else: # Gemini
                    for chunk in resp:
                        full_ans += chunk.text
                        res_area.markdown(full_ans + "▌")
                
                res_area.markdown(full_ans)
                st.session_state.messages.append({"role": "assistant", "content": full_ans})
                st.caption(f"✓ Phản hồi bởi {engine_name}")
            else:
                st.error("🆘 Toàn bộ 4 cổng API đều đang kẹt. Vui lòng đợi 30 giây.")
