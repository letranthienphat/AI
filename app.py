import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random
import requests
import io
from PIL import Image

# --- 1. Cấu hình hệ thống & Trí nhớ ---
st.set_page_config(page_title="Nexus OS V55.2", layout="wide")

# Khởi tạo bộ nhớ tóm tắt nếu chưa có
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'summary' not in st.session_state: st.session_state.summary = ""
if 'bg' not in st.session_state: st.session_state.bg = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072"

# --- 2. Giao diện Tương phản cao ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)), url("{st.session_state.bg}");
        background-size: cover; background-attachment: fixed;
    }}
    .stChatMessage {{
        background: rgba(20, 25, 35, 0.9) !important; /* Độ đậm cao để rõ chữ */
        border: 1px solid #00d2ff;
        border-radius: 15px !important;
        color: white !important;
        margin-bottom: 10px;
    }}
    /* Nút gợi ý xịn */
    .stButton button {{
        background: rgba(0, 210, 255, 0.1);
        border: 1px solid #00d2ff;
        color: #00d2ff;
        border-radius: 20px;
        transition: 0.3s;
    }}
    .stButton button:hover {{
        background: #00d2ff;
        color: black;
    }}
    h1, h2, h3, p, b {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,1);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. Lõi xử lý AI (Tóm tắt & Phản hồi) ---
def get_ai_response(prompt, context_summary=""):
    """Gửi kèm tóm tắt để AI luôn nhớ mình đang nói về gì"""
    full_prompt = f"Bối cảnh trước đó: {context_summary}\n\nNgười dùng: {prompt}"
    
    keys = list(st.secrets["GROQ_KEYS"])
    random.shuffle(keys)
    for key in keys:
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": full_prompt}],
                stream=True
            ), "Groq"
        except: continue
    
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash').generate_content(full_prompt, stream=True), "Gemini"

def update_summary():
    """Tự động tóm tắt khi chat đạt trên 5 câu để tiết kiệm bộ nhớ"""
    if len(st.session_state.chat_log) > 5:
        history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_log[-4:]])
        summary_prompt = f"Hãy tóm tắt ngắn gọn cuộc trò chuyện này trong 2 câu để tôi ghi nhớ: {history}"
        # Gọi Gemini để tóm tắt nhanh
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        res = genai.GenerativeModel('gemini-1.5-flash').generate_content(summary_prompt)
        st.session_state.summary = res.text

# --- 4. Giao diện chính ---
def main():
    with st.sidebar:
        st.title("💠 NEXUS OS V55.2")
        st.write(f"🧠 Trí nhớ hiện tại: {st.session_state.summary[:50]}...")
        if st.button("🗑️ Xóa trí nhớ"):
            st.session_state.chat_log = []
            st.session_state.summary = ""
            st.rerun()
        st.divider()
        st.session_state.bg = st.text_input("Đổi hình nền:", st.session_state.bg)

    st.title("🤖 Neural Terminal")

    # Hiển thị Chat
    for msg in st.session_state.chat_log:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Nút gợi ý chủ động
    if st.session_state.chat_log:
        cols = st.columns(3)
        suggestions = ["Giải thích rõ hơn", "Ví dụ cụ thể", "Viết code tính năng này"]
        for i, sug in enumerate(suggestions):
            if cols[i].button(f"💡 {sug}"):
                process_chat(sug)

    # Input người dùng
    if p := st.chat_input("Hỏi Nexus bất cứ điều gì..."):
        process_chat(p)

def process_chat(user_input):
    st.session_state.chat_log.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        res, provider = get_ai_response(user_input, st.session_state.summary)
        box = st.empty(); full = ""
        if res:
            for chunk in res:
                content = chunk.choices[0].delta.content if provider == "Groq" else chunk.text
                if content:
                    full += content
                    box.markdown(full + "▌")
            box.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            update_summary() # Cập nhật trí nhớ sau mỗi lần chat
            st.rerun()

if __name__ == "__main__":
    main()
