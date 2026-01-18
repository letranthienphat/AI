import streamlit as st
import google.generativeai as genai
from openai import OpenAI

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="AI Multi-Hub Ultimate", layout="wide")

# Khởi tạo bộ nhớ Session
if "api_keys" not in st.session_state:
    st.session_state.api_keys = {"Gemini": "", "OpenAI": "", "DeepSeek": "", "Groq (Llama 3)": ""}
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. THANH BÊN (QUẢN LÝ API) ---
with st.sidebar:
    st.title("⚙️ Cài đặt Hệ thống")
    provider = st.selectbox("Chọn hãng AI:", list(st.session_state.api_keys.keys()))
    
    # Hiển thị trạng thái và tính năng Sửa/Xóa
    current_k = st.session_state.api_keys[provider]
    if current_k:
        st.success(f"✅ Đã kết nối {provider}")
        if st.button(f"🗑️ Xóa/Sửa Key {provider}"):
            st.session_state.api_keys[provider] = ""
            st.rerun()
    else:
        new_k = st.text_input(f"Nhập API Key cho {provider}:", type="password")
        if st.button(f"🚀 Kích hoạt {provider}"):
            st.session_state.api_keys[provider] = new_k
            st.rerun()

    st.divider()
    if st.button("🧹 Xóa lịch sử chat"):
        st.session_state.messages = []
        st.rerun()

# --- 3. LOGIC XỬ LÝ AI ---
st.title(f"🤖 Trợ lý {provider}")
active_key = st.session_state.api_keys[provider]

if not active_key:
    st.info(f"Vui lòng nhập API Key của {provider} để bắt đầu.")
    st.stop()

# Hiển thị chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Hỏi tôi bất cứ điều gì..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        
        try:
            # --- XỬ LÝ GEMINI (Sửa lỗi 404 & Gemini 1.5/2.0/3.0) ---
            if provider == "Gemini":
                genai.configure(api_key=active_key)
                # Kỹ thuật dùng 'gemini-1.5-flash' là ổn định nhất trên API hiện tại
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                full_res = response.text
                res_area.markdown(full_res)

            # --- XỬ LÝ GROQ (MIỄN PHÍ TỐC ĐỘ CAO) ---
            elif provider == "Groq (Llama 3)":
                client = OpenAI(api_key=active_key, base_url="https://api.groq.com/openai/v1")
                completion = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
                full_res = completion.choices[0].message.content
                res_area.markdown(full_res)

            # --- XỬ LÝ OPENAI / DEEPSEEK ---
            else:
                b_url = "https://api.openai.com/v1" if provider == "OpenAI" else "https://api.deepseek.com"
                m_name = "gpt-3.5-turbo" if provider == "OpenAI" else "deepseek-chat"
                client = OpenAI(api_key=active_key, base_url=b_url)
                # Stream cho trải nghiệm mượt mà
                stream = client.chat.completions.create(
                    model=m_name,
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(full_res + "▌")
                res_area.markdown(full_res)

            st.session_state.messages.append({"role": "assistant", "content": full_res})

        except Exception as e:
            if "402" in str(e):
                st.error("💳 DeepSeek báo: Tài khoản hết tiền (Insufficient Balance)!")
            elif "404" in str(e):
                st.error("❌ Lỗi 404: Google API chưa cập nhật model này. Hãy thử lại sau vài phút hoặc đổi model.")
            else:
                st.error(f"⚠️ Lỗi: {str(e)}")
