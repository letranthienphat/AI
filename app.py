import streamlit as st
import google.generativeai as genai
from openai import OpenAI

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="AI Multi-Tool v2", layout="wide")

# Khởi tạo kho lưu trữ trong Session State
if "api_storage" not in st.session_state:
    st.session_state.api_storage = {"Gemini": "", "OpenAI": "", "DeepSeek": ""}
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. THANH BÊN (SIDEBAR) - NƠI QUẢN TRỊ API ---
with st.sidebar:
    st.title("🛡️ Trung tâm Điều khiển")
    
    # Chọn hãng AI để làm việc
    provider = st.selectbox("Chọn hãng AI:", ["Gemini", "OpenAI", "DeepSeek"])
    
    st.divider()
    st.subheader("🔑 Quản lý Key")
    
    # Kiểm tra xem hãng hiện tại đã có Key chưa
    current_key = st.session_state.api_storage[provider]
    
    if current_key:
        st.success(f"Đã lưu Key {provider}")
        if st.button(f"Sửa / Xóa Key {provider}"):
            st.session_state.api_storage[provider] = ""
            st.rerun()
    else:
        new_key = st.text_input(f"Nhập Key {provider} mới:", type="password")
        if st.button(f"Lưu & Kích hoạt {provider}"):
            if new_key:
                st.session_state.api_storage[provider] = new_key
                st.rerun()
            else:
                st.warning("Vui lòng nhập Key!")

    st.divider()
    if st.button("🧹 Xóa lịch sử hội thoại"):
        st.session_state.messages = []
        st.rerun()

# --- 3. GIAO DIỆN CHAT ---
st.title(f"🤖 Trợ lý {provider}")

# Kiểm tra nếu chưa có Key thì chặn không cho chat
active_key = st.session_state.api_storage[provider]
if not active_key:
    st.info(f"💡 Vui lòng nhập API Key cho **{provider}** ở thanh bên trái để bắt đầu.")
    st.stop()

# Hiển thị lịch sử
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Xử lý nhập liệu
if prompt := st.chat_input("Gõ câu hỏi tại đây..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        
        try:
            if provider == "Gemini":
                # SỬA LỖI 404: Cấu hình chuẩn cho Gemini 1.5
                genai.configure(api_key=active_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                full_res = response.text
                res_area.markdown(full_res)
            
            else:
                # Cấu hình cho OpenAI hoặc DeepSeek
                b_url = "https://api.openai.com/v1" if provider == "OpenAI" else "https://api.deepseek.com"
                m_name = "gpt-3.5-turbo" if provider == "OpenAI" else "deepseek-chat"
                
                client = OpenAI(api_key=active_key, base_url=b_url)
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
            # Bắt lỗi 402 cụ thể cho DeepSeek
            if "402" in str(e):
                st.error("💳 Tài khoản DeepSeek hết tiền! Hãy nạp thêm hoặc đổi sang Gemini.")
            else:
                st.error(f"⚠️ Lỗi: {str(e)}")
