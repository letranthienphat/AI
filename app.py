import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random
import requests
import io
from PIL import Image

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Nexus OS V55.1", layout="wide", page_icon="💠")

# Lấy Key an toàn từ Secrets
try:
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    GEMINI_KEY = st.secrets["GEMINI_KEY"]
except Exception as e:
    st.error("❌ Không tìm thấy API Keys trong mục Secrets!")
    st.stop()

if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'bg' not in st.session_state: st.session_state.bg = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072"

# --- 2. GIAO DIỆN TƯƠNG PHẢN CAO (HIGH CONTRAST GLASSMORPHISM) ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("{st.session_state.bg}");
        background-size: cover; background-attachment: fixed;
    }}
    /* Làm Sidebar sáng và rõ hơn */
    [data-testid="stSidebar"] {{
        background: rgba(15, 18, 25, 0.9) !important;
        backdrop-filter: blur(25px);
        border-right: 2px solid #00d2ff;
    }}
    /* Cải thiện độ hiển thị tin nhắn */
    .stChatMessage {{
        background: rgba(30, 35, 45, 0.85) !important; /* Tăng độ đục để rõ chữ */
        border: 1px solid rgba(0, 210, 255, 0.3);
        border-radius: 15px !important;
        color: #ffffff !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        margin-bottom: 15px;
    }}
    /* Đảm bảo chữ trong ô nhập liệu luôn trắng rõ */
    .stChatInput input {{
        color: white !important;
        background: rgba(40, 45, 55, 1) !important;
    }}
    h1, h2, h3, p, span {{
        color: white !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8); /* Thêm bóng cho chữ để dễ đọc */
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI XỬ LÝ AI ---
def get_ai_response(prompt):
    keys = list(GROQ_KEYS)
    random.shuffle(keys)
    for key in keys:
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                stream=True
            ), "Groq (Llama 3.3)"
        except: continue
    try:
        genai.configure(api_key=GEMINI_KEY)
        return genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt, stream=True), "Gemini"
    except: return None, None

def generate_nexus_art(prompt):
    """Xử lý lỗi UnidentifiedImageError bằng cách kiểm tra phản hồi"""
    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    # Bạn nên để HF_TOKEN vào secret để tránh bị từ chối yêu cầu
    headers = {"Authorization": f"Bearer {st.secrets.get('HF_TOKEN', '')}"}
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=40)
        # Kiểm tra nếu kết quả trả về không phải là ảnh (thường là JSON báo lỗi)
        if response.status_code == 200 and b"PNG" in response.content[:10] or b"JFIF" in response.content[:10]:
            return response.content
        else:
            return None
    except: return None

# --- 4. GIAO DIỆN CHÍNH ---
def main():
    with st.sidebar:
        st.title("💠 NEXUS TERMINAL")
        menu = st.radio("Menu", ["🤖 Neural Chat", "🎨 Art Studio", "⚙️ Cài đặt"])
        st.divider()
        if st.button("🗑️ Dọn dẹp nhật ký"):
            st.session_state.chat_log = []
            st.rerun()

    if menu == "🤖 Neural Chat":
        st.title("🤖 Neural Terminal")
        for msg in st.session_state.chat_log:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if p := st.chat_input("Nhập lệnh..."):
            st.session_state.chat_log.append({"role": "user", "content": p})
            with st.chat_message("user"): st.markdown(p)

            with st.chat_message("assistant"):
                res, provider = get_ai_response(p)
                if res:
                    box = st.empty(); full = ""
                    for chunk in res:
                        content = chunk.choices[0].delta.content if provider == "Groq (Llama 3.3)" else chunk.text
                        if content:
                            full += content
                            box.markdown(full + "▌")
                    box.markdown(full)
                    st.session_state.chat_log.append({"role": "assistant", "content": full})
                else:
                    st.error("Lõi AI không phản hồi.")

    elif menu == "🎨 Art Studio":
        st.title("🎨 Nexus Art Studio")
        p = st.text_input("Mô tả ảnh:")
        if st.button("Sáng tạo"):
            with st.spinner("Đang xử lý dữ liệu ảnh..."):
                img_data = generate_nexus_art(p)
                if img_data:
                    # Chống lỗi PIL bằng cách kiểm tra dữ liệu trước khi mở
                    try:
                        image = Image.open(io.BytesIO(img_data))
                        st.image(image, caption="AI Generated Image")
                    except Exception:
                        st.error("Dữ liệu ảnh bị lỗi cấu trúc.")
                else:
                    st.warning("⚠️ API Vẽ ảnh đang bận hoặc hết hạn mức miễn phí. Hãy thử lại sau 1 phút.")

    elif menu == "⚙️ Cài đặt":
        st.title("⚙️ Tùy chỉnh hệ thống")
        st.session_state.bg = st.text_input("Thay đổi URL hình nền:", st.session_state.bg)
        if st.button("Cập nhật"): st.rerun()

if __name__ == "__main__":
    main()
