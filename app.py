import streamlit as st
from openai import OpenAI
import google.generativeai as genai

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hệ Thống AI Đa Năng", page_icon="🤖", layout="centered")

# --- KHỞI TẠO BỘ NHỚ LƯU TRỮ ---
if "api_storage" not in st.session_state:
    st.session_state.api_storage = {"OpenAI": "", "DeepSeek": "", "Gemini": ""}
if "messages" not in st.session_state:
    st.session_state.messages = []
if "auth_success" not in st.session_state:
    st.session_state.auth_success = False

# --- MÀN HÌNH ĐĂNG NHẬP / CẤU HÌNH API ---
if not st.session_state.auth_success:
    st.title("🔐 Cấu hình API AI")
    st.write("Vui lòng thiết lập khóa kết nối để bắt đầu.")
    
    provider = st.selectbox("Chọn hãng AI muốn dùng:", ["Gemini", "OpenAI", "DeepSeek"])
    
    # Lấy key cũ nếu đã lỡ nhập trước đó
    saved_key = st.session_state.api_storage.get(provider, "")
    input_key = st.text_input(f"Nhập API Key cho {provider}:", value=saved_key, type="password")
    
    remember_me = st.checkbox("Ghi nhớ API Key cho phiên làm việc này", value=True)
    
    if st.button("Kết nối hệ thống"):
        if input_key:
            if remember_me:
                st.session_state.api_storage[provider] = input_key
            
            st.session_state.current_provider = provider
            st.session_state.current_key = input_key
            st.session_state.auth_success = True
            st.rerun()
        else:
            st.error("Vui lòng không để trống API Key!")
    st.stop()

# --- GIAO DIỆN CHAT CHÍNH ---
st.title(f"🤖 Trợ lý {st.session_state.current_provider}")

# Sidebar cho phép chỉnh sửa API bất cứ lúc nào
with st.sidebar:
    st.header("⚙️ Tùy chỉnh")
    st.write(f"Đang dùng: **{st.session_state.current_provider}**")
    if st.button("🔄 Thay đổi API / Đổi hãng"):
        st.session_state.auth_success = False
        st.rerun()
    
    st.divider()
    if st.button("🗑️ Xóa lịch sử chat"):
        st.session_state.messages = []
        st.rerun()

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# XỬ LÝ PHẢN HỒI AI
if prompt := st.chat_input("Nhập câu hỏi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # 1. XỬ LÝ CHO GEMINI (Sửa lỗi 404)
            if st.session_state.current_provider == "Gemini":
                genai.configure(api_key=st.session_state.current_key)
                # Sử dụng gemini-1.5-flash-latest để đảm bảo tương thích API mới nhất
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                response = model.generate_content(prompt)
                full_response = response.text
                response_placeholder.markdown(full_response)

            # 2. XỬ LÝ CHO OPENAI
            elif st.session_state.current_provider == "OpenAI":
                client = OpenAI(api_key=st.session_state.current_key)
                stream = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    stream=True,
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)

            # 3. XỬ LÝ CHO DEEPSEEK
            elif st.session_state.current_provider == "DeepSeek":
                client = OpenAI(api_key=st.session_state.current_key, base_url="https://api.deepseek.com")
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    stream=False
                )
                full_response = response.choices[0].message.content
                response_placeholder.markdown(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"❌ Lỗi: {str(e)}")
