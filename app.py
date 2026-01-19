import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random
import requests
import io
from PIL import Image

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Nexus OS V55.0", layout="wide", page_icon="💠")

# LẤY API TỪ SECRET (Không dán Key trực tiếp vào code để tránh bị hack/khóa key)
try:
    GROQ_KEYS = st.secrets["GROQ_KEYS"] # Phải đặt trong mục Secrets là một danh sách
    GEMINI_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("⚠️ Thiếu cấu hình API trong Secrets! Vui lòng kiểm tra lại.")
    st.stop()

# Khởi tạo dữ liệu
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'bg' not in st.session_state: st.session_state.bg = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"

# --- 2. GIAO DIỆN TITAN DARK GLASSMORPHISM ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("{st.session_state.bg}");
        background-size: cover; background-attachment: fixed;
    }}
    /* Sidebar mờ ảo */
    [data-testid="stSidebar"] {{
        background: rgba(10, 12, 16, 0.8) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(0, 210, 255, 0.2);
    }}
    /* Khung chat hiện đại */
    .stChatMessage {{
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(10px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 15px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI XỬ LÝ AI SIÊU CẤP ---
def get_ai_response(prompt):
    """Cơ chế xoay vòng Key thông minh & Fail-safe"""
    # 1. Thử nghiệm với Groq (Llama 3.3)
    available_keys = list(GROQ_KEYS)
    random.shuffle(available_keys)
    
    for key in available_keys:
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            ), "Groq (Llama 3.3)"
        except Exception:
            continue 

    # 2. Dự phòng cuối cùng với Gemini
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(prompt, stream=True), "Gemini Flash"
    except Exception as e:
        return None, f"Lỗi: {str(e)}"

# --- 4. TÍNH NĂNG VẼ ẢNH AI (Hugging Face) ---
def generate_nexus_art(prompt):
    """Tạo ảnh nghệ thuật từ văn bản"""
    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    # Gợi ý: Thêm HF_TOKEN vào secret để không bị giới hạn tốc độ
    headers = {"Authorization": f"Bearer {st.secrets.get('HF_TOKEN', '')}"}
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=30)
        return response.content
    except: return None

# --- 5. GIAO DIỆN CHÍNH ---
def main():
    with st.sidebar:
        st.title("💠 NEXUS OS")
        st.subheader("V55.0 Professional")
        st.divider()
        menu = st.radio("Tính năng", ["🤖 Neural Chat", "🎨 Art Studio", "⚙️ Hệ thống"])
        
        if st.button("🗑️ Reset Terminal"):
            st.session_state.chat_log = []
            st.rerun()

    if menu == "🤖 Neural Chat":
        st.title("🤖 Neural Terminal")
        
        # Hiển thị lịch sử
        for msg in st.session_state.chat_log:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat input
        if p := st.chat_input("Gõ lệnh hoặc tin nhắn..."):
            st.session_state.chat_log.append({"role": "user", "content": p})
            with st.chat_message("user"): st.markdown(p)

            with st.chat_message("assistant"):
                res, provider = get_ai_response(p)
                if res:
                    box = st.empty(); full = ""
                    for chunk in res:
                        # Xử lý khác biệt giữa OpenAI Stream và Gemini Stream
                        content = chunk.choices[0].delta.content if "Groq" in provider else chunk.text
                        if content:
                            full += content
                            box.markdown(full + "▌")
                    box.markdown(full)
                    st.caption(f"⚡ Đã xử lý bởi: {provider}")
                    st.session_state.chat_log.append({"role": "assistant", "content": full})
                else:
                    st.error("Tất cả lõi AI đang quá tải.")

    elif menu == "🎨 Art Studio":
        st.title("🎨 Nexus Art Studio")
        art_prompt = st.text_area("Mô tả bức ảnh bạn muốn tạo:", placeholder="Ví dụ: Một phi hành gia cưỡi ngựa trên sao Hỏa, phong cách cyberpunk...")
        if st.button("Bắt đầu vẽ"):
            if art_prompt:
                with st.spinner("Đang sử dụng lõi FLUX để phác họa..."):
                    img_data = generate_nexus_art(art_prompt)
                    if img_data:
                        st.image(img_data, caption="Kết quả sáng tạo từ Nexus OS")
                    else:
                        st.error("Lõi vẽ ảnh đang bận, thử lại sau nhé!")

    elif menu == "⚙️ Hệ thống":
        st.title("⚙️ Cài đặt hệ thống")
        st.session_state.bg = st.text_input("Link hình nền mới (URL):", st.session_state.bg)
        st.success("Cấu hình hệ thống đã sẵn sàng.")

if __name__ == "__main__":
    main()
