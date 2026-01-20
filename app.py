import streamlit as st
from openai import OpenAI
import google.generativeai as genai

# --- 1. CẤU HÌNH HỆ THỐNG & GIAO DIỆN ---
st.set_page_config(page_title="Nexus OS V56.0 - Hyper Memory", layout="wide")

# Lấy Keys từ Secrets
GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# Khởi tạo Session State
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'bg' not in st.session_state: st.session_state.bg = "https://images.unsplash.com/photo-1614850523296-d8c1af93d400?q=80&w=2070"
if 'current_model' not in st.session_state: st.session_state.current_model = "Auto-Sync"

# CSS Tương phản cao - Chống mỏi mắt và nhìn rõ chữ
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("{st.session_state.bg}");
        background-size: cover;
    }}
    /* Khung chat tối đặc để chữ trắng nổi bật */
    .stChatMessage {{
        background: rgba(10, 15, 25, 0.98) !important;
        border: 1px solid #00d2ff;
        color: #ffffff !important;
        border-radius: 15px !important;
    }}
    .stMarkdown p {{ color: #ffffff !important; font-size: 1.1rem; }}
    /* Sidebar chuyên nghiệp */
    [data-testid="stSidebar"] {{
        background: rgba(5, 10, 20, 0.95) !important;
        border-right: 2px solid #00d2ff;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LÕI QUẢN LÝ BỘ NHỚ & PHẢN HỒI ---
def get_ai_response(user_input, model_mode):
    # Chuẩn bị lịch sử hội thoại (Trí nhớ dài hạn)
    # Lấy 10 câu gần nhất để AI không bị quá tải nhưng vẫn hiểu bối cảnh
    history = []
    for m in st.session_state.chat_log[-10:]:
        history.append({"role": m["role"], "content": m["content"]})
    history.append({"role": "user", "content": user_input})

    # DANH SÁCH KEY ĐỂ THỬ
    target_keys = []
    if model_mode == "Auto-Sync":
        target_keys = GROQ_KEYS
    elif "Groq" in model_mode:
        idx = int(model_mode.split(" ")[-1]) - 1
        target_keys = [GROQ_KEYS[idx]]
    
    # 1. THỬ VỚI GROQ
    for i, key in enumerate(target_keys):
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=history, # Gửi toàn bộ lịch sử thay vì chỉ 1 câu
                stream=True
            ), f"Groq {i+1 if model_mode == 'Auto-Sync' else model_mode}"
        except Exception:
            if model_mode != "Auto-Sync": break # Nếu chọn Manual mà lỗi thì dừng luôn
            continue

    # 2. DỰ PHÒNG GEMINI (Nếu Auto hoặc Manual Gemini được chọn)
    if model_mode == "Auto-Sync" or model_mode == "Gemini":
        try:
            genai.configure(api_key=GEMINI_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Chuyển đổi format history sang format của Gemini
            gemini_history = []
            for m in history[:-1]:
                role = "user" if m["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [m["content"]]})
            
            chat = model.start_chat(history=gemini_history)
            return chat.send_message(user_input, stream=True), "Gemini Flash"
        except Exception as e:
            return None, str(e)
    
    return None, "Lỗi kết nối API"

# --- 3. GIAO DIỆN ĐIỀU KHIỂN ---
def main():
    with st.sidebar:
        st.title("💠 NEXUS CORE V56")
        
        # BỘ CHỌN CHATBOT REAL-TIME
        st.subheader("🤖 Cấu hình AI")
        options = ["Auto-Sync"] + [f"Groq {i+1}" for i in range(len(GROQ_KEYS))] + ["Gemini"]
        st.session_state.current_model = st.selectbox(
            "Chọn luồng xử lý:", 
            options, 
            index=options.index(st.session_state.current_model)
        )
        
        st.divider()
        st.write(f"🧠 Trí nhớ: **{len(st.session_state.chat_log)} tin nhắn**")
        if st.button("🗑️ Xóa sạch bộ nhớ"):
            st.session_state.chat_log = []
            st.rerun()

    st.title("🤖 Neural Terminal")
    st.caption(f"Đang sử dụng chế độ: **{st.session_state.current_model}** | Chữ đã được tối ưu độ tương phản.")

    # Hiển thị lịch sử chat
    for msg in st.session_state.chat_log:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Xử lý nhập liệu
    if p := st.chat_input("Nhập tin nhắn để tiếp tục cuộc trò chuyện..."):
        st.session_state.chat_log.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)

        with st.chat_message("assistant"):
            res, source = get_ai_response(p, st.session_state.current_model)
            
            if res:
                box = st.empty(); full = ""
                for chunk in res:
                    # Kiểm tra xem là Groq (OpenAI style) hay Gemini
                    if "Groq" in source:
                        content = chunk.choices[0].delta.content or ""
                    else:
                        content = chunk.text
                    
                    full += content
                    box.markdown(full + "▌")
                
                box.markdown(full)
                st.caption(f"⚡ Phản hồi qua: {source}")
                st.session_state.chat_log.append({"role": "assistant", "content": full})
            else:
                st.error(f"⚠️ Model {st.session_state.current_model} đang bận hoặc sai cấu hình.")

if __name__ == "__main__":
    main()
