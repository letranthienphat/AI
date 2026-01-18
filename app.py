import streamlit as st
from openai import OpenAI
import google.generativeai as genai

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="AI Multi-Hub Pro", layout="wide")

# --- KHỞI TẠO BỘ NHỚ (SESSION STATE) ---
if "api_keys" not in st.session_state:
    st.session_state.api_keys = {"Gemini": "", "OpenAI": "", "DeepSeek": ""}
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR: QUẢN LÝ API KEY ---
with st.sidebar:
    st.title("⚙️ Cấu hình hệ thống")
    
    # Chọn hãng AI
    provider = st.selectbox("Chọn nhà cung cấp:", ["Gemini", "OpenAI", "DeepSeek"])
    
    # Hiển thị trạng thái Key hiện tại
    current_stored_key = st.session_state.api_keys.get(provider, "")
    
    if current_stored_key:
        st.success(f"✅ Đã có Key cho {provider}")
        if st.button(f"🗑️ Xóa/Sửa Key {provider}"):
            st.session_state.api_keys[provider] = ""
            st.rerun()
    else:
        new_key = st.text_input(f"Nhập API Key {provider}:", type="password")
        remember = st.checkbox("Ghi nhớ Key này vĩnh viễn (trong phiên này)", value=True)
        if st.button(f"💾 Lưu Key {provider}"):
            if new_key:
                st.session_state.api_keys[provider] = new_key
                st.success("Đã lưu!")
                st.rerun()
            else:
                st.error("Vui lòng không để trống!")

    st.divider()
    if st.button("🗑️ Xóa lịch sử chat"):
        st.session_state.messages = []
        st.rerun()

# --- GIAO DIỆN CHAT ---
st.title(f"🤖 Chat với {provider}")

# Kiểm tra xem đã có Key cho hãng đang chọn chưa
active_key = st.session_state.api_keys.get(provider)

if not active_key:
    st.warning(f"⚠️ Vui lòng nhập và lưu API Key của {provider} ở thanh bên trái để bắt đầu!")
    st.stop()

# Hiển thị tin nhắn
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Xử lý nhập liệu
if prompt := st.chat_input("Hỏi tôi bất cứ điều gì..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # 🔵 XỬ LÝ GEMINI (Sửa lỗi 404)
            if provider == "Gemini":
                genai.configure(api_key=active_key)
                # Dùng tên model ổn định nhất
                model = genai.GenerativeModel('gemini-1.5-flash') 
                response = model.generate_content(prompt)
                full_response = response.text
                response_placeholder.markdown(full_response)

            # 🟢 XỬ LÝ OPENAI / DEEPSEEK
            else:
                base_url = "https://api.openai.com/v1"
                model_name = "gpt-3.5-turbo"
                
                if provider == "DeepSeek":
                    base_url = "https://api.deepseek.com"
                    model_name = "deepseek-chat"
                
                client = OpenAI(api_key=active_key, base_url=base_url)
                stream = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            if "402" in str(e):
                st.error("❌ DeepSeek báo lỗi 402: Tài khoản của bạn hết tiền. Vui lòng nạp thêm credit tại trang chủ DeepSeek.")
            elif "404" in str(e):
                st.error("❌ Lỗi 404: Không tìm thấy Model. Hãy đảm bảo bạn đã dùng đúng loại Key cho hãng tương ứng.")
            else:
                st.error(f"❌ Lỗi hệ thống: {str(e)}")
