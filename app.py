import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import time

# --- 1. CẤU HÌNH HỆ THỐNG CỰC MẠNH ---
st.set_page_config(page_title="NEXUS ULTIMATE", layout="wide", page_icon="☢️")

# Lấy API Keys
GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# Khởi tạo bộ nhớ (SESSION STATE)
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'selected_model' not in st.session_state: st.session_state.selected_model = "Groq 1 (Llama 3.3)"

# --- 2. GIAO DIỆN CYBERPUNK (CSS NÂNG CAO) ---
st.markdown("""
    <style>
    /* Hình nền động dạng lưới */
    .stApp {
        background-color: #000000;
        background-image: 
            linear-gradient(rgba(0, 255, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 255, 0.03) 1px, transparent 1px);
        background-size: 30px 30px;
    }
    
    /* Hiệu ứng chữ phát sáng */
    h1 {
        color: #00e5ff !important;
        text-shadow: 0 0 10px #00e5ff, 0 0 20px #00e5ff;
        font-family: 'Courier New', monospace;
        font-weight: bold;
    }
    
    /* Khung chat người dùng */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background: rgba(0, 229, 255, 0.1) !important;
        border-right: 3px solid #00e5ff;
        border-radius: 10px 0 0 10px;
        color: white !important;
    }

    /* Khung chat AI */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background: rgba(255, 0, 85, 0.1) !important;
        border-left: 3px solid #ff0055;
        border-radius: 0 10px 10px 0;
        color: white !important;
    }

    /* Sidebar kính cường lực */
    [data-testid="stSidebar"] {
        background: rgba(10, 10, 10, 0.95) !important;
        border-right: 1px solid #333;
    }
    
    /* Nút bấm Neon */
    .stButton button {
        border: 1px solid #00e5ff;
        background: transparent;
        color: #00e5ff;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background: #00e5ff;
        color: black;
        box-shadow: 0 0 15px #00e5ff;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. BỘ NÃO XỬ LÝ (THE BRAIN) ---
def get_groq_response(messages, key_index):
    """Gọi Groq và gửi TOÀN BỘ lịch sử"""
    try:
        client = OpenAI(api_key=GROQ_KEYS[key_index], base_url="https://api.groq.com/openai/v1")
        return client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages, # Gửi toàn bộ list messages để AI nhớ
            stream=True
        )
    except Exception as e:
        return None

def get_gemini_response(messages):
    """Gọi Gemini và gửi TOÀN BỘ lịch sử"""
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Chuyển đổi định dạng lịch sử cho Gemini
        gemini_hist = []
        for msg in messages[:-1]: # Lấy quá khứ
            role = "user" if msg["role"] == "user" else "model"
            gemini_hist.append({"role": role, "parts": [msg["content"]]})
        
        chat = model.start_chat(history=gemini_hist)
        return chat.send_message(messages[-1]["content"], stream=True)
    except Exception as e:
        return None

def ai_engine(user_input, preferred_model):
    # 1. Cập nhật vào bộ nhớ tạm để gửi đi (nhưng chưa lưu vào session state vội)
    temp_memory = st.session_state.chat_log.copy()
    temp_memory.append({"role": "user", "content": user_input})

    stream = None
    used_model = ""

    # 2. Xử lý theo lựa chọn của người dùng
    if "Groq" in preferred_model:
        idx = int(preferred_model.split(" ")[1]) - 1 # Lấy số 1, 2, 3...
        stream = get_groq_response(temp_memory, idx)
        used_model = preferred_model
        
        # Nếu Groq này lỗi, TỰ ĐỘNG nhảy sang Groq khác (Fail-over)
        if not stream:
            for i in range(len(GROQ_KEYS)):
                if i != idx:
                    stream = get_groq_response(temp_memory, i)
                    if stream: 
                        used_model = f"Groq {i+1} (Auto-Switch)"
                        break
    
    # 3. Nếu vẫn chưa có (hoặc chọn Gemini), dùng Gemini
    if not stream or "Gemini" in preferred_model:
        stream = get_gemini_response(temp_memory)
        used_model = "Gemini" if stream else "SYSTEM FAILURE"

    return stream, used_model

# --- 4. GIAO DIỆN CHÍNH ---
def main():
    # SIDEBAR: Trung tâm chỉ huy
    with st.sidebar:
        st.title("🎛️ SYSTEM CONTROL")
        st.markdown("---")
        
        # Model Selector
        model_options = [f"Groq {i+1} (Llama 3.3)" for i in range(len(GROQ_KEYS))] + ["Gemini (Google)"]
        st.session_state.selected_model = st.radio(
            "📡 Chọn Kênh Kết Nối:", 
            model_options,
            index=model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0
        )
        
        st.markdown("---")
        st.write(f"🧠 Bộ nhớ đệm: **{len(st.session_state.chat_log)} dòng**")
        if st.button("🔴 KHỞI ĐỘNG LẠI (RESET)"):
            st.session_state.chat_log = []
            st.rerun()

    # MAIN SCREEN
    st.title("NEXUS /// ULTIMATE")
    
    # Hiển thị lịch sử chat (Memory Playback)
    for msg in st.session_state.chat_log:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Ô nhập liệu
    if prompt := st.chat_input("Nhập lệnh kích hoạt..."):
        # Hiển thị tin nhắn người dùng ngay lập tức
        st.session_state.chat_log.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Xử lý AI
        with st.chat_message("assistant"):
            status_box = st.empty()
            status_box.caption("🔄 Đang kết nối neural network...")
            
            stream, source = ai_engine(prompt, st.session_state.selected_model)
            
            if stream:
                status_box.caption(f"⚡ Đã kết nối: **{source}**")
                response_container = st.empty()
                full_response = ""
                
                # Streaming effect
                for chunk in stream:
                    content = ""
                    if "Groq" in source:
                        content = chunk.choices[0].delta.content or ""
                    else:
                        content = chunk.text
                    
                    full_response += content
                    response_container.markdown(full_response + "█") # Con trỏ nhấp nháy
                
                response_container.markdown(full_response)
                # LƯU VÀO BỘ NHỚ VĨNH CỬU
                st.session_state.chat_log.append({"role": "assistant", "content": full_response})
            else:
                st.error("❌ MẤT KẾT NỐI TOÀN BỘ SERVER!")

if __name__ == "__main__":
    main()
