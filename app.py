import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Gemini AI Pro", layout="centered")

# --- PHẦN XÁC THỰC API KEY ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔑 Nhập khóa Gemini")
    user_key = st.text_input("Dán Gemini API Key của bạn:", type="password")
    if st.button("Bắt đầu trò chuyện"):
        if user_key.startswith("AIza"): # Kiểm tra định dạng cơ bản của Google Key
            st.session_state.api_key = user_key
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("API Key của Gemini thường bắt đầu bằng 'AIza'. Vui lòng kiểm tra lại!")
    st.stop()

# --- CẤU HÌNH GEMINI ---
genai.configure(api_key=st.session_state.api_key)
model = genai.GenerativeModel('gemini-1.5-flash') # Dùng bản flash cho tốc độ cực nhanh

if "chat_history" not in st.session_state:
    # Gemini cần lịch sử theo định dạng riêng: role 'user' và 'model'
    st.session_state.chat_history = []

st.title("🤖 Trợ lý Gemini")

# Hiển thị lịch sử chat
for message in st.session_state.chat_history:
    with st.chat_message("user" if message["role"] == "user" else "assistant"):
        st.markdown(message["parts"][0])

# Xử lý nhập liệu
if prompt := st.chat_input("Hỏi Gemini điều gì đó..."):
    # Hiển thị tin nhắn người dùng ngay lập tức
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Lưu vào lịch sử
    st.session_state.chat_history.append({"role": "user", "parts": [prompt]})

    with st.chat_message("assistant"):
        status_placeholder = st.status("⏳ Đang kết nối với Google AI...")
        try:
            # Gửi toàn bộ lịch sử để Gemini hiểu ngữ cảnh
            chat = model.start_chat(history=st.session_state.chat_history[:-1])
            response = chat.send_message(prompt)
            
            answer = response.text
            st.markdown(answer)
            
            # Lưu phản hồi vào lịch sử
            st.session_state.chat_history.append({"role": "model", "parts": [answer]})
            status_placeholder.update(label="✅ Đã trả lời!", state="complete")
            
        except Exception as e:
            status_placeholder.update(label="❌ Lỗi phản hồi", state="error")
            st.error(f"Chi tiết lỗi: {str(e)}")
            if "API_KEY_INVALID" in str(e):
                st.warning("API Key bạn nhập có vẻ không đúng hoặc đã bị vô hiệu hóa.")
