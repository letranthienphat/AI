
import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random

# --- V50.1.1: BẢN VÁ LỖI ĐỒNG BỘ ---
st.set_page_config(page_title="Nexus OS V50.1.1")

# 1. Kết nối Secrets (Khớp 100% với mã Secret tôi vừa gửi)
try:
    # Lấy danh sách Keys từ tên mới: GROQ_KEYS
    ALL_KEYS = st.secrets["GROQ_KEYS"]
    G_KEY = st.secrets["GEMINI_KEY"]
    
    # Cấu hình Gemini
    genai.configure(api_key=G_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Hệ thống chưa nhận được Secret: {e}")
    st.stop()

# 2. Khởi tạo bộ nhớ
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Hàm xử lý AI
def call_ai(msgs):
    pool = list(ALL_KEYS)
    random.shuffle(pool)
    
    for k in pool:
        try:
            # DÙNG BIẾN k (LẤY TỪ ALL_KEYS), KHÔNG DÙNG "GROQ_API_KEY"
            client = OpenAI(api_key=k, base_url="https://api.groq.com/openai/v1")
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in msgs[-6:]],
                stream=True
            )
            return res, "Groq"
        except:
            continue
            
    try:
        chat = gemini_model.start_chat(history=[])
        res = chat.send_message(msgs[-1]["content"], stream=True)
        return res, "Gemini"
    except:
        return None, None

# 4. Giao diện Chat
st.title("💠 Nexus OS V50.1.1")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Nhập tin nhắn..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        box = st.empty()
        full = ""
        result, engine = call_ai(st.session_state.messages)
        
        if result:
            if engine == "Groq":
                for chunk in result:
                    if chunk.choices[0].delta.content:
                        full += chunk.choices[0].delta.content
                        box.markdown(full + "▌")
            else:
                for chunk in result:
                    full += chunk.text
                    box.markdown(full + "▌")
            box.markdown(full)
            st.session_state.messages.append({"role": "assistant", "content": full})
        else:
            st.error("Server đang bận, bạn thử lại nhé!")
