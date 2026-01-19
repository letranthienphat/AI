import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import time

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Nexus OS V55.5", layout="wide")

# Khởi tạo bộ nhớ và cấu hình
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'bg' not in st.session_state: st.session_state.bg = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1964"

# --- 2. GIAO DIỆN TƯƠNG PHẢN SIÊU CẤP ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), url("{st.session_state.bg}");
        background-size: cover;
    }}
    /* Khung chat Glassmorphism độ sáng cao */
    .stChatMessage {{
        background: rgba(25, 30, 40, 0.95) !important;
        border: 1px solid #00d2ff;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }}
    /* Chữ siêu rõ */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        color: #FFFFFF !important;
        font-weight: 500;
        text-shadow: 1px 1px 2px #000000;
    }}
    /* Thanh nhập liệu nổi bật */
    .stChatInputContainer {{ border-top: 2px solid #00d2ff !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI ĐIỀU PHỐI API (SMART-CHAINING) ---
def get_ai_response(prompt):
    """Cơ chế bậc thang: Groq 1 -> 2 -> 3 -> Gemini"""
    keys = st.secrets["GROQ_KEYS"] # Giả sử bạn có 3-4 keys trong danh sách này
    
    # Thử từng Key Groq theo thứ tự ưu tiên 1, 2, 3...
    for i, key in enumerate(keys):
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                timeout=10 # Nếu phản hồi quá chậm thì chuyển key
            )
            return response, f"Groq Key {i+1}"
        except Exception as e:
            continue # Thử key tiếp theo nếu lỗi hoặc hết lượt (Rate Limit)

    # Dự phòng cuối cùng: Gemini
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(prompt, stream=True), "Gemini (Backup)"
    except Exception as e:
        return None, f"Tất cả API đều lỗi: {str(e)}"

# --- 4. GIAO DIỆN CHÍNH ---
def main():
    with st.sidebar:
        st.title("💠 NEXUS CORE")
        st.write("Phiên bản: **V55.5 (Hyper)**")
        st.divider()
        if st.button("🗑️ Dọn sạch Terminal"):
            st.session_state.chat_log = []
            st.rerun()
        st.info("💡 Mẹo: Nhắn liên tục để kiểm tra khả năng chuyển tầng API.")

    st.title("🤖 Neural Terminal")

    # Hiển thị Chat
    for msg in st.session_state.chat_log:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Gợi ý câu trả lời chủ động
    if st.session_state.chat_log:
        c1, c2, c3 = st.columns(3)
        if c1.button("🔄 Giải thích thêm"): process_chat("Hãy giải thích chi tiết hơn về vấn đề này.")
        if c2.button("📝 Tóm tắt ý chính"): process_chat("Tóm tắt lại những gì chúng ta vừa thảo luận.")
        if c3.button("🎨 Vẽ minh họa"): process_chat("/draw một hình ảnh minh họa cho nội dung này.")

    # Input người dùng
    if p := st.chat_input("Nhập tin nhắn..."):
        process_chat(p)

def process_chat(user_input):
    st.session_state.chat_log.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        res_stream, source = get_ai_response(user_input)
        
        if res_stream:
            placeholder = st.empty()
            full_content = ""
            
            # Xử lý streaming tùy theo nguồn
            for chunk in res_stream:
                content = ""
                if "Groq" in source:
                    content = chunk.choices[0].delta.content or ""
                else:
                    content = chunk.text
                
                full_content += content
                placeholder.markdown(full_content + "▌")
            
            placeholder.markdown(full_content)
            st.caption(f"⚡ Nguồn: {source}")
            st.session_state.chat_log.append({"role": "assistant", "content": full_content})
        else:
            st.error("Cạn kiệt tài nguyên API. Vui lòng thử lại sau.")

if __name__ == "__main__":
    main()
