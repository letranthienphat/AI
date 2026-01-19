import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import random

# --- CÀI ĐẶT GIAO DIỆN ---
st.set_page_config(page_title="Hệ điều hành Nexus", layout="wide")

# Thiết lập hình nền và phong cách "kính mờ"
if 'hinh_nen' not in st.session_state:
    st.session_state.hinh_nen = "https://wallpaperaccess.com/full/1155013.jpg"

st.markdown(f"""
    <style>
    .stApp {{
        background: url("{st.session_state.hinh_nen}");
        background-size: cover;
    }}
    .stMarkdown, .stButton, [data-testid="stSidebar"] {{
        background: rgba(0, 0, 0, 0.7) !important;
        color: white !important;
        border-radius: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- QUẢN LÝ TÀI KHOẢN ---
if 'danh_sach_user' not in st.session_state:
    st.session_state.danh_sach_user = {"admin": "8888"} # Tài khoản chủ lực

if 'dang_nhap_chua' not in st.session_state:
    st.session_state.dang_nhap_chua = False
    st.session_state.ten_user = ""
    st.session_state.quyen = "Khách"
    st.session_state.tin_nhan = []

# --- HÀM CHAT AI ---
def goi_ai_tra_loi(cau_hoi):
    try:
        keys = st.secrets["GROQ_KEYS"]
        client = OpenAI(api_key=random.choice(keys), base_url="https://api.groq.com/openai/v1")
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": cau_hoi}], stream=True), "Groq"
    except:
        try:
            genai.configure(api_key=st.secrets["GEMINI_KEY"])
            return genai.GenerativeModel('gemini-1.5-flash').generate_content(cau_hoi, stream=True), "Gemini"
        except: return None, None

# --- GIAO DIỆN ĐĂNG NHẬP / ĐĂNG KÝ ---
if not st.session_state.dang_nhap_chua:
    st.title("🛡️ CỔNG VÀO NEXUS")
    lua_chon = st.radio("Bạn muốn làm gì?", ["Đăng nhập", "Đăng ký tài khoản mới", "Dùng thử (Khách)"], horizontal=True)
    
    if lua_chon == "Đăng nhập":
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("Vào hệ thống"):
            if u in st.session_state.danh_sach_user and st.session_state.danh_sach_user[u] == p:
                st.session_state.dang_nhap_chua = True
                st.session_state.ten_user = u
                st.session_state.quyen = "Chủ phòng" if u == "admin" else "Thành viên"
                st.rerun()
            else: st.error("Sai tên hoặc mật khẩu rồi bạn ơi!")
            
    elif lua_chon == "Đăng ký tài khoản mới":
        new_u = st.text_input("Chọn tên muốn đặt")
        new_p = st.text_input("Chọn mật khẩu", type="password")
        if st.button("Tạo tài khoản ngay"):
            if new_u in st.session_state.danh_sach_user: st.error("Tên này có người dùng rồi!")
            elif new_u and new_p:
                st.session_state.danh_sach_user[new_u] = new_p
                st.success("Đã tạo xong! Giờ qua tab Đăng nhập để vào nhé.")
            else: st.warning("Đừng để trống ô nào cả.")
            
    else:
        if st.button("Vào xem chơi (Khách)"):
            st.session_state.dang_nhap_chua = True
            st.session_state.ten_user = "Khách vãng lai"
            st.session_state.quyen = "Khách"
            st.rerun()

# --- GIAO DIỆN SAU KHI VÀO TRONG ---
else:
    with st.sidebar:
        st.title(f"Chào, {st.session_state.ten_user}")
        st.write(f"Cấp bậc: {st.session_state.quyen}")
        st.divider()
        menu = st.selectbox("Chọn chức năng", ["Màn hình chính", "Chat với AI", "Khu vực bí mật 🔐", "Cài đặt"])
        if st.button("Thoát hệ thống"):
            st.session_state.dang_nhap_chua = False
            st.rerun()

    if menu == "Màn hình chính":
        st.title("🏠 BẢNG ĐIỀU KHIỂN")
        st.write(f"Hôm nay bạn thế nào, {st.session_state.ten_user}?")
        col1, col2 = st.columns(2)
        col1.metric("Số người đang online", random.randint(1, 100))
        col2.metric("Trạng thái API", "Đang chạy tốt ✅")

    elif menu == "Chat với AI":
        st.title("🤖 TRỢ LÝ THÔNG MINH")
        for m in st.session_state.tin_nhan:
            with st.chat_message(m["role"]): st.write(m["content"])
        
        if cau_hoi := st.chat_input("Hỏi AI bất cứ điều gì..."):
            st.session_state.tin_nhan.append({"role": "user", "content": cau_hoi})
            with st.chat_message("user"): st.write(cau_hoi)
            with st.chat_message("assistant"):
                box = st.empty(); full = ""
                tra_loi, kieu = goi_ai_tra_loi(cau_hoi)
                if tra_loi:
                    for chunk in tra_loi:
                        text = chunk.choices[0].delta.content if kieu == "Groq" else chunk.text
                        if text: full += text; box.markdown(full + "▌")
                    box.markdown(full)
                    st.session_state.tin_nhan.append({"role": "assistant", "content": full})

    elif menu == "Khu vực bí mật 🔐":
        if st.session_state.quyen != "Chủ phòng":
            st.error("⚠️ Lỗiii! Chỗ này chỉ dành cho Chủ phòng (Admin). Bạn không đủ tuổi!")
        else:
            st.title("🕵️ PHÒNG BÍ MẬT")
            st.write("Đây là nơi chứa các bí mật của bạn...")
            st.text_area("Ghi chú bí mật của bạn:", "Dán thông tin nhạy cảm vào đây...")
            st.write("Danh sách mật khẩu lưu trữ: 123456, abcdef, ...")

    elif menu == "Cài đặt":
        st.title("⚙️ CÀI ĐẶT HỆ THỐNG")
        st.subheader("Đổi hình nền")
        link = st.text_input("Dán link ảnh bạn thích vào đây:", st.session_state.hinh_nen)
        if st.button("Đổi ngay và luôn"):
            st.session_state.hinh_nen = link
            st.rerun()
