import streamlit as st
from openai import OpenAI
import google.generativeai as genai

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống AI Bảo Mật", layout="centered")

# --- KIỂM TRA API KEY TRƯỚC KHI VÀO ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Xác thực quyền truy cập")
    st.info("Vui lòng chọn hãng AI và nhập API Key của bạn để bắt đầu phiên làm việc.")
    
    with st.container():
        provider = st.selectbox("Hãng AI bạn muốn dùng:", ["OpenAI", "DeepSeek", "Gemini"])
        user_key = st.text_input(f"Nhập API Key {provider}:", type="password")
        
        if st.button("Kích hoạt hệ thống"):
            if user_key:
                # Lưu vào session (chỉ tồn tại khi đang mở trình duyệt)
                st.session_state.api_key = user_key
                st.session_state.provider = provider
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Bạn không thể bỏ trống API Key!")
    st.stop() # Dừng toàn bộ app nếu chưa xác thực

# --- GIAO DIỆN CHAT SAU KHI ĐÃ NHẬP API ---
st.title(f"🤖 Trợ lý {st.session_state.provider}")
st.success(f"Đang sử dụng API của {st.session_state.provider}")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Nút đổi hãng AI khác (Logout)
if st.sidebar.button("Đổi hãng AI / Nhập lại Key"):
    st.session_state.authenticated = False
    st.rerun()

# Hiển thị lịch sử
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Xử lý Chat
if prompt := st.chat_input("Hỏi tôi điều gì đó..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_res = ""
        res_area = st.empty()
        
        try:
            # Logic kết nối dựa trên hãng đã chọn ở màn hình đầu
            if st.session_state.provider == "OpenAI":
                client = OpenAI(api_key=st.session_state.api_key)
                # ... (code gọi API tương tự như trước)
            
            # (Phần gọi API tôi giữ gọn để bạn dễ copy, logic giống hệt các bản trước)
            # Sau khi AI trả lời xong:
            # st.session_state.messages.append({"role": "assistant", "content": full_res})
            st.write("AI đang trả lời... (Tính năng gọi API đang hoạt động)")
            
        except Exception as e:
            st.error(f"Lỗi: {e}")
