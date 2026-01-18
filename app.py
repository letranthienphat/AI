import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import qrcode
from io import BytesIO

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="AI Super Hub - QR Export", layout="wide", page_icon="🛡️")

if "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
else:
    st.error("❌ Chưa cấu hình GROQ_API_KEY trong Secrets!")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "custom_keys" not in st.session_state:
    st.session_state.custom_keys = {"Gemini": "", "OpenAI": "", "DeepSeek": ""}

# --- HÀM TẠO MÃ QR CHIA NHỎ ---
def generate_qr_codes(text, chunk_size=1000):
    # Chia nhỏ văn bản thành các đoạn để nhét vừa QR
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    qr_images = []
    for i, chunk in enumerate(chunks):
        content = f"Part {i+1}/{len(chunks)}:\n{chunk}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Chuyển sang định dạng byte để Streamlit hiển thị
        buf = BytesIO()
        img.save(buf, format="PNG")
        qr_images.append(buf.getvalue())
    return qr_images

# --- 2. THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.title("🛡️ Quản lý & Xuất bản")
    mode = st.radio("Chế độ:", ["Dùng Groq (Mặc định)", "Dùng API cá nhân khác"])
    
    st.divider()
    st.subheader("📥 Xuất dữ liệu")
    if st.button("📄 Tạo mã QR Lịch sử"):
        if not st.session_state.messages:
            st.warning("Chưa có nội dung để tạo QR!")
        else:
            # Gộp toàn bộ chat thành văn bản
            full_chat_text = ""
            for m in st.session_state.messages:
                role = "Bạn" if m["role"] == "user" else "AI"
                full_chat_text += f"{role}: {m['content']}\n\n"
            
            qr_list = generate_qr_codes(full_chat_text)
            st.session_state.qr_results = qr_list
            st.success(f"Đã tạo {len(qr_list)} mã QR!")

    if st.button("🗑️ Xóa lịch sử"):
        st.session_state.messages = []
        if "qr_results" in st.session_state: del st.session_state.qr_results
        st.rerun()

# --- 3. GIAO DIỆN CHAT ---
st.title("🤖 Trợ lý AI")

# Hiển thị mã QR nếu có
if "qr_results" in st.session_state:
    st.subheader("📍 Mã QR Lịch sử Chat của bạn")
    cols = st.columns(3) # Hiển thị 3 QR mỗi hàng
    for idx, qr_data in enumerate(st.session_state.qr_results):
        with cols[idx % 3]:
            st.image(qr_data, caption=f"Phần {idx + 1}")
            st.download_button(f"Tải QR {idx+1}", data=qr_data, file_name=f"qr_part_{idx+1}.png")
    st.divider()

# Hiển thị lịch sử chat bình thường
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Nhập câu hỏi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        res_area = st.empty()
        full_res = ""
        try:
            client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
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
            st.error(f"⚠️ Lỗi: {str(e)}")
