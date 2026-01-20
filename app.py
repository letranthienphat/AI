import streamlit as st
import time
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="NEXUS V100.0", layout="wide", page_icon="🛡️")

# Trạng thái hệ thống
states = {
    'stage': "law", 'law_step': 1, 'user_name': "", 'chat_log': [], 
    'bg_url': "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072",
    'suggestions': ["Hướng dẫn sử dụng", "Tính năng chính", "Liên hệ hỗ trợ"],
    'admin_clicks': 0, 'ok_count': 0, 'is_admin': False, 'law_timer': 0
}
for key, val in states.items():
    if key not in st.session_state: st.session_state[key] = val

GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# --- 2. CSS TƯƠNG PHẢN CAO & CHỮ TRẮNG ---
def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.9), rgba(0,0,0,0.95)), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}
    /* ÉP CHỮ TRẮNG TUYỆT ĐỐI */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, label, span {{
        color: #FFFFFF !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,1);
    }}
    .glass-box {{
        background: rgba(20, 25, 30, 0.98);
        border: 1px solid #00f2ff;
        border-radius: 12px; padding: 30px;
    }}
    .law-area {{
        height: 450px; overflow-y: scroll; background: #000;
        padding: 25px; border: 1px solid #333; border-radius: 8px;
        color: #fff; line-height: 1.6; text-align: justify;
    }}
    /* Style nút gợi ý tách biệt */
    .suggestion-col button {{
        background: rgba(255, 255, 255, 0.1) !important;
        color: #00f2ff !important;
        border: 1px solid #00f2ff55 !important;
        margin-bottom: 10px; width: 100%;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI AI ---
def call_ai(prompt):
    messages = [{"role": "system", "content": f"Bạn là Nexus, trợ lý ảo thông minh của {st.session_state.user_name}. Hãy trả lời bằng ngôn ngữ chuẩn mực, lịch sự, dễ hiểu."}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})

    for key in GROQ_KEYS:
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True), "Groq"
        except: continue
    return None, None

def get_clean_hints(last_res):
    """Lấy gợi ý sạch, chỉ có nội dung tin nhắn"""
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        p = f"Dựa trên câu trả lời: '{last_res[:200]}', đưa ra 3 câu hỏi tiếp theo ngắn gọn. Chỉ trả về nội dung câu hỏi, cách nhau bằng dấu phẩy. Không đánh số, không ghi chú gì thêm."
        res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": p}])
        st.session_state.suggestions = [s.strip() for s in res.choices[0].message.content.split(',') if s.strip()]
    except: pass

# --- 4. MÀN HÌNH BỘ LUẬT (CÓ THỜI GIAN CHỜ) ---
def screen_law():
    apply_theme()
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    
    parts = {
        1: "<b>CHƯƠNG I: QUY ĐỊNH CHUNG</b><br><br>Điều 1: Nexus là nền tảng hỗ trợ thông tin dựa trên trí tuệ nhân tạo. Người dùng cần hiểu rằng mọi thông tin chỉ mang tính chất tham khảo... (Nội dung dài tiếp theo)",
        2: "<b>CHƯƠNG II: BẢO MẬT DỮ LIỆU</b><br><br>Điều 2: Thông tin cá nhân và nội dung hội thoại được bảo mật trong phạm vi phiên làm việc. Chúng tôi cam kết không chia sẻ dữ liệu cho bên thứ ba trái phép...",
        3: "<b>CHƯƠNG III: TRÁCH NHIỆM NGƯỜI DÙNG</b><br><br>Điều 3: Người dùng không được sử dụng hệ thống vào các mục đích vi phạm pháp luật, gây nhiễu loạn hoặc phá hoại hệ thống..."
    }
    
    st.title(f"⚖️ ĐIỀU KHOẢN SỬ DỤNG ({st.session_state.law_step}/3)")
    st.markdown(f"<div class='law-area'>{parts[st.session_state.law_step]}</div>", unsafe_allow_html=True)
    
    # Logic chờ đọc luật (Ví dụ 10 giây mỗi trang)
    if f"time_start_{st.session_state.law_step}" not in st.session_state:
        st.session_state[f"time_start_{st.session_state.law_step}"] = time.time()
    
    elapsed = time.time() - st.session_state[f"time_start_{st.session_state.law_step}"]
    remaining = max(0, 10 - int(elapsed))
    
    st.write("")
    if remaining > 0:
        st.warning(f"Vui lòng đọc kỹ nội dung. Bạn có thể xác nhận sau {remaining} giây nữa.")
        st.button("ĐANG KIỂM TRA NỘI DUNG...", disabled=True)
        time.sleep(1)
        st.rerun()
    else:
        if st.button("TÔI ĐÃ ĐỌC VÀ ĐỒNG Ý ✅"):
            if st.session_state.law_step < 3:
                st.session_state.law_step += 1
            else:
                st.session_state.stage = "ask_name"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 5. NHẬP TÊN ---
def screen_name():
    apply_theme()
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    st.header("👤 THIẾT LẬP TÊN NGƯỜI DÙNG")
    name = st.text_input("Vui lòng nhập tên để bắt đầu:")
    if st.button("XÁC NHẬN"):
        if name:
            st.session_state.user_name = name; st.session_state.stage = "home"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 6. HUB & ADMIN ---
def screen_home():
    apply_theme()
    st.title(f"🏠 TRUNG TÂM ĐIỀU HÀNH - {st.session_state.user_name}")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<div class='glass-box'><h3>🌐 Chatbot Interface</h3><p>Truy cập vào hệ thống hỗ trợ trực tuyến.</p></div>", unsafe_allow_html=True)
        if st.button("MỞ PHÒNG CHAT", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()

    with col2:
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        st.subheader("⚙️ Hệ thống")
        st.session_state.bg_url = st.text_input("Link ảnh nền:", st.session_state.bg_url)
        
        with st.expander("Thông tin phiên bản"):
            st.write("Phiên bản: 100.0.1 (Stable)")
            if st.button("S/N: NX-2026-FINAL-V1"):
                st.session_state.admin_clicks += 1
                if st.session_state.admin_clicks >= 10: st.session_state.secret = True
            
            if st.session_state.get('secret'):
                if st.button("Xác nhận quyền"):
                    st.session_state.ok_count += 1
                    if st.session_state.ok_count >= 4:
                        st.session_state.is_admin = True; st.session_state.secret = False

        if st.session_state.is_admin:
            st.success("🔓 Chế độ Admin")
            import socket
            st.write(f"Tên: {st.session_state.user_name} | IP: {socket.gethostbyname(socket.gethostname())}")

        if st.button("Đọc lại Điều khoản"):
            st.session_state.stage = "law"; st.session_state.law_step = 1; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. CHAT & GỢI Ý TÁCH BIỆT ---
def screen_chat():
    apply_theme()
    if st.button("⬅️ QUAY LẠI"): st.session_state.stage = "home"; st.rerun()
    
    st.title("🧬 Nexus Neural Interface")
    box = st.container()
    for m in st.session_state.chat_log:
        with box.chat_message(m["role"]): st.markdown(m["content"])

    # Gợi ý tách biệt thành từng nút trong cột
    st.write("💡 **Gợi ý:**")
    h_cols = st.columns(3)
    for i, s in enumerate(st.session_state.suggestions[:3]):
        with h_cols[i]:
            if st.button(s, key=f"h_{i}"):
                process_msg(s)

    if p := st.chat_input("Nhập nội dung..."):
        process_msg(p)

def process_msg(p):
    st.session_state.chat_log.append({"role": "user", "content": p})
    with st.chat_message("user"): st.markdown(p)
    with st.chat_message("assistant"):
        h = st.empty(); full = ""
        stream, _ = call_ai(p)
        if stream:
            for chunk in stream:
                content = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                if content:
                    full += content; h.markdown(full + "█")
            h.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            get_clean_hints(full)
            st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "law": screen_law()
elif st.session_state.stage == "ask_name": screen_name()
elif st.session_state.stage == "home": screen_home()
else: screen_chat()
