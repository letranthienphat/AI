import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Nexus OS V50.0.1.3", layout="wide")

# --- 2. LẤY DỮ LIỆU TỪ SECRETS ---
# Lưu ý: Phải khớp 100% với mục Secrets bạn đã dán
try:
    # Chúng ta dùng get() để nếu thiếu key nó sẽ báo lỗi rõ ràng hơn thay vì sập App
    GROQ_LIST = st.secrets.get("GROQ_KEYS", [])
    GEMINI_CORE_KEY = st.secrets.get("GEMINI_KEY", "")

    if not GROQ_LIST or not GEMINI_CORE_KEY:
        st.error("🆘 Lỗi: Không tìm thấy GROQ_KEYS hoặc GEMINI_KEY trong mục Secrets.")
        st.stop()

    # Cấu hình Gemini
    genai.configure(api_key=GEMINI_CORE_KEY)
    gemini_engine = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"❌ Lỗi cấu hình: {e}")
    st.stop()

# --- 3. KHỞI TẠO BỘ NHỚ ---
if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- 4. HÀM XỬ LÝ AI (HỆ THỐNG XOAY VÒNG MỚI) ---
def nexus_ai_logic(chat_history):
    # Trộn danh sách key
    pool = list(GROQ_LIST)
    random.shuffle(pool)
    
    # Lấy 5 câu gần nhất
    recent_context = chat_history[-6:]
    
    # THỬ LẦN LƯỢT CÁC KEY TRONG POOL
    for current_key in pool:
        try:
            # KHÔNG DÙNG BIẾN "GROQ_API_KEY" CŨ NỮA
            client = OpenAI(api_key=current_key, base_url="https://api.groq.com/openai/v1")
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in recent_context],
                stream=True
            )
            return stream, "Groq-Node"
        except Exception:
            continue # Thử key tiếp theo nếu lỗi
            
    # NẾU TẤT CẢ THẤT BẠI -> GEMINI
    try:
        chat = gemini_engine.start_chat(history=[])
        response = chat.send_message(chat_history[-1]["content"], stream=True)
        return response, "Gemini-Node"
    except:
        return None, None

# --- 5. GIAO DIỆN CHAT ---
st.title("💠 Nexus Terminal V50.0.1.3")

# Hiển thị lịch sử
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Ô nhập liệu
if prompt := st.chat_input("Nhập tin nhắn..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        result, node_type = nexus_ai_logic(st.session_state.messages)
        
        if result:
            if node_type == "Groq-Node":
                for chunk in result:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        placeholder.markdown(full_response + "▌")
            else: # Gemini
                for chunk in result:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
            
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.caption(f"✓ Kết nối ổn định qua {node_type}")
        else:
            st.error("🆘 Hệ thống quá tải. Vui lòng kiểm tra lại Keys hoặc đợi 1 phút.")
