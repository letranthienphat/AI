import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random

# --- V50.1.0: THE CLEAN START ---
st.set_page_config(page_title="Nexus OS V50.1.0")

# 1. Kiểm tra Secrets (Khớp 100% với ảnh bạn đã chụp)
try:
    # Lấy danh sách Keys
    GROQ_KEYS_LIST = st.secrets["GROQ_KEYS"]
    GEMINI_FINAL_KEY = st.secrets["GEMINI_KEY"]
    
    # Cấu hình Gemini
    genai.configure(api_key=GEMINI_FINAL_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Lỗi Secrets: {e}")
    st.stop()

# 2. Khởi tạo bộ nhớ
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Hàm xử lý AI
def run_ai(msgs):
    # Trộn Key Groq
    pool = list(GROQ_KEYS_LIST)
    random.shuffle(pool)
    
    # Thử Groq
    for k in pool:
        try:
            client = OpenAI(api_key=k, base_url="https://api.groq.com/openai/v1")
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in msgs[-6:]],
                stream=True
            )
            return res, "Groq"
        except:
            continue
            
    # Thử Gemini
    try:
        chat = gemini_model.start_chat(history=[])
        res = chat.send_message(msgs[-1]["content"], stream=True)
        return res, "Gemini"
    except:
        return None, None

# 4. Giao diện Chat
st.title("💠 Nexus OS V50.1.0")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Hỏi tôi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        box = st.empty()
        full = ""
        result, engine = run_ai(st.session_state.messages)
        
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
            st.error("Server bận, đợi xíu nhé!")
