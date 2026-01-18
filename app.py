import streamlit as st
import google.generativeai as genai
from openai import OpenAI

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="AI Super Hub", layout="wide")

if "api_keys" not in st.session_state:
    st.session_state.api_keys = {"Gemini": "", "Groq (Free)": "", "DeepSeek": "", "OpenAI": ""}
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- THANH BÊN: QUẢN LÝ API ---
with st.sidebar:
    st.header("⚙️ Quản lý API")
    provider = st.selectbox("Chọn hãng AI:", list(st.session_state.api_keys.keys()))
    
    # Tính năng Sửa/Xóa API Key
    if st.session_state.api_keys[provider]:
        st.success(f"✅ Đã lưu Key {provider}")
        if st.button(f"🗑️ Xóa/Sửa Key {provider}"):
            st.session_state.api_keys[provider] = ""
            st.rerun()
    else:
        new_k = st.text_input(f"Nhập Key {provider}:", type="password")
        if st.button(f"💾 Lưu & Kích hoạt"):
            st.session_state.api_keys[provider] = new_k
            st.rerun()

    st.divider()
    if st.button("🗑️ Xóa lịch sử chat"):
        st.session_state.messages = []
        st.rerun()

# --- GIAO DIỆN CHAT ---
st.title(f"🤖 Trợ lý {provider}")
active_key = st.session_state.api_keys[provider]

if not active_key:
    st.info(f"Vui lòng nhập Key cho {provider} ở Sidebar bên trái.")
    st.stop()

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Nhập câu hỏi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        
        try:
            # --- LOGIC CHO GEMINI (TỰ DÒ MODEL) ---
            if provider == "Gemini":
                genai.configure(api_key=active_key)
                # Kỹ thuật dò tìm model khả dụng để tránh 404
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(prompt)
                except:
                    # Nếu flash lỗi, thử dùng bản pro hoặc bản có sẵn trong list
                    available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model = genai.GenerativeModel(available[0]) # Lấy cái đầu tiên khả dụng
                    response = model.generate_content(prompt)
                full_res = response.text
                res_area.markdown(full_res)

            # --- LOGIC CHO GROQ (MIỄN PHÍ - LLAMA 3) ---
            elif provider == "Groq (Free)":
                client = OpenAI(api_key=active_key, base_url="https://api.groq.com/openai/v1")
                stream = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(full_res + "▌")

            # --- LOGIC CHO DEEPSEEK / OPENAI ---
            else:
                base = "https://api.openai.com/v1" if provider == "OpenAI" else "https://api.deepseek.com"
                name = "gpt-3.5-turbo" if provider == "OpenAI" else "deepseek-chat"
                client = OpenAI(api_key=active_key, base_url=base)
                stream = client.chat.completions.create(model=name, messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages], stream=True)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_area.markdown(full_res + "▌")

            res_area.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})

        except Exception as e:
            st.error(f"❌ Lỗi: {str(e)}")
            if "402" in str(e): st.warning("DeepSeek hết tiền rồi bạn ơi!")
