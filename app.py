import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random

# --- 1. CẤU HÌNH HỆ THỐNG & VAI DIỄN ---
st.set_page_config(page_title="Nexus OS V55.3 - Case File", layout="wide")

# Hệ thống vai diễn mặc định (System Message)
DETECTIVE_ROLE = "Bạn là một Cảnh sát chuyên nghiệp đang hỗ trợ Thám tử (người dùng). Nhiệm vụ của bạn là cung cấp báo cáo, hồ sơ và trả lời mọi câu hỏi điều tra một cách nghiêm túc, chi tiết."

if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'summary' not in st.session_state: st.session_state.summary = "Chưa có tóm tắt vụ án."
if 'case_status' not in st.session_state: st.session_state.case_status = "Đang mở rộng điều tra"

# --- 2. GIAO DIỆN TƯƠNG PHẢN CAO ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("https://images.unsplash.com/photo-1505816014357-96b5ff457e9a?q=80&w=2070");
        background-size: cover;
    }}
    .stChatMessage {{
        background: rgba(15, 20, 30, 0.95) !important;
        border-left: 5px solid #00d2ff !important;
        border-radius: 10px !important;
    }}
    .stButton button {{
        width: 100%;
        background: rgba(0, 210, 255, 0.1);
        border: 1px solid #00d2ff;
        color: #00d2ff;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI XỬ LÝ AI ---
def get_ai_response(prompt, history_summary):
    # Kết hợp Vai diễn + Tóm tắt + Câu hỏi mới
    context = f"{DETECTIVE_ROLE}\n\nTóm tắt hồ sơ trước đó: {history_summary}\n\nThám tử hỏi: {prompt}"
    
    try:
        keys = list(st.secrets["GROQ_KEYS"])
        random.shuffle(keys)
        client = OpenAI(api_key=keys[0], base_url="https://api.groq.com/openai/v1")
        return client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": context}],
            stream=True
        ), "Groq"
    except:
        try:
            genai.configure(api_key=st.secrets["GEMINI_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            return model.generate_content(context, stream=True), "Gemini"
        except Exception as e:
            return None, str(e)

def update_summary():
    """Tóm tắt vụ án để ghi nhớ vĩnh viễn - Có bẫy lỗi NotFound"""
    if len(st.session_state.chat_log) > 4:
        try:
            history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_log[-4:]])
            sum_p = f"Tóm tắt các tình tiết chính của vụ án từ đối thoại này (ngắn gọn): {history}"
            genai.configure(api_key=st.secrets["GEMINI_KEY"])
            res = genai.GenerativeModel('gemini-1.5-flash').generate_content(sum_p)
            st.session_state.summary = res.text
        except:
            pass # Nếu lỗi tóm tắt thì bỏ qua để không sập app

# --- 4. GIAO DIỆN ĐIỀU TRA ---
def main():
    with st.sidebar:
        st.title("🚓 CƠ QUAN ĐIỀU TRA")
        st.info(f"📁 Trạng thái: {st.session_state.case_status}")
        st.markdown(f"**Hồ sơ ghi nhớ:**\n{st.session_state.summary}")
        if st.button("🚨 Đóng hồ sơ (Reset)"):
            st.session_state.chat_log = []
            st.session_state.summary = "Chưa có tóm tắt vụ án."
            st.rerun()

    st.title("🕵️ Kho lưu trữ bằng chứng")

    # Hiển thị hội thoại
    for msg in st.session_state.chat_log:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Nút gợi ý nghiệp vụ
    if st.session_state.chat_log:
        c1, c2, c3 = st.columns(3)
        if c1.button("🔍 Khám nghiệm hiện trường"): process_chat("Cảnh sát cho tôi xem danh sách vật chứng tại hiện trường.")
        if c2.button("👥 Thẩm vấn nghi phạm"): process_chat("Hãy triệu tập nghi phạm chính để tôi thẩm vấn.")
        if c3.button("🧪 Giám định pháp y"): process_chat("Kết quả giám định mảnh vải/dấu tay thế nào rồi?")

    # Input
    if p := st.chat_input("Nhập lệnh điều tra..."):
        process_chat(p)

def process_chat(user_input):
    st.session_state.chat_log.append({"role": "user", "content": user_input})
    with st.chat_message("assistant"):
        res, provider = get_ai_response(user_input, st.session_state.summary)
        if res:
            box = st.empty(); full = ""
            for chunk in res:
                t = chunk.choices[0].delta.content if provider == "Groq" else chunk.text
                if t: full += t; box.markdown(full + "▌")
            box.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            update_summary()
            st.rerun()
        else:
            st.error("⚠️ Mất liên lạc với trung tâm chỉ huy (API Error).")

if __name__ == "__main__":
    main()
