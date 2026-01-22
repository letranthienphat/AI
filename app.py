import streamlit as st
import time
import psutil
import json
from openai import OpenAI

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="NEXUS UNIVERSAL", layout="wide", page_icon="🌐")

ADMIN_NAME = "Lê Trần Thiên Phát"
ADMIN_EMAIL = "tranthienphatle@gmail.com"

# Khởi tạo dữ liệu
if 'stage' not in st.session_state: st.session_state.stage = "law"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'suggestions' not in st.session_state: 
    st.session_state.suggestions = ["Giới thiệu về Nexus", "Lợi ích của AI", "Kế hoạch làm việc", "Học ngoại ngữ", "Viết code mẫu", "Giải trí"]
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
if 'bg_url' not in st.session_state: st.session_state.bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072"

GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])

# --- 2. CSS CHUYÊN NGHIỆP (KHÔNG LỖI CHỮ) ---
def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.9)), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}

    /* Sửa lỗi chữ đen và mã HTML */
    .stMarkdown p, .stMarkdown li, div[data-testid="stChatMessage"] p {{
        color: #FFFFFF !important;
        font-size: 1.05rem;
        line-height: 1.6;
    }}

    /* Khung điều khoản chuyên nghiệp */
    .tos-box {{
        background: #000000;
        border: 1px solid #444;
        border-radius: 10px;
        padding: 25px;
        max-height: 450px;
        overflow-y: auto;
        margin-bottom: 20px;
        color: #ddd;
    }}
    .tos-box h2 {{ color: #00f2ff !important; }}
    .tos-box b {{ color: #00f2ff; }}

    /* Nút gợi ý */
    div.stButton > button {{
        background: rgba(255, 255, 255, 0.05);
        color: #00f2ff; border: 1px solid #00f2ff33;
        border-radius: 5px; height: 3rem; font-size: 0.85rem;
    }}
    div.stButton > button:hover {{ background: #00f2ff; color: #000; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIC GỢI Ý THÔNG MINH ---
def update_dynamic_suggestions(last_response):
    """Sử dụng AI để tạo ra 6 gợi ý dựa trên câu trả lời cuối cùng"""
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        prompt = f"Dựa trên nội dung này: '{last_response[:500]}', hãy đưa ra 6 hành động hoặc câu hỏi tiếp theo cực ngắn (dưới 4 từ). Trả về dưới dạng danh sách ngăn cách bởi dấu phẩy."
        res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
        new_hints = [h.strip() for h in res.choices[0].message.content.split(',') if h.strip()]
        if len(new_hints) >= 6:
            st.session_state.suggestions = new_hints[:6]
    except:
        pass # Giữ nguyên gợi ý cũ nếu lỗi

# --- 4. CÁC MÀN HÌNH ---

def screen_law():
    apply_theme()
    st.title("🌐 ĐIỀU KHOẢN SỬ DỤNG - NEXUS UNIVERSAL")
    st.write("Chào mừng mọi người đến với hệ điều hành tri thức được phát triển bởi **Lê Trần Thiên Phát**.")
    
    # Hiển thị điều khoản bằng HTML sạch không bị leak mã
    tos_html = f"""
    <div class="tos-box">
        <h2>1. CHÀO MỪNG ĐẾN VỚI NEXUS</h2>
        <p>Phần mềm này được thiết kế dành cho tất cả mọi người nhằm mục đích hỗ trợ học tập, làm việc và sáng tạo. Nexus OS được phát triển và vận hành bởi <b>{ADMIN_NAME}</b>.</p>
        
        <h2>2. QUYỀN HẠN CỦA NGƯỜI DÙNG</h2>
        <p>Người dùng có quyền tự do khám phá kiến thức, đặt câu hỏi cho AI và cá nhân hóa trải nghiệm của mình. Chúng tôi khuyến khích sự sáng tạo không giới hạn.</p>
        
        <h2>3. TRÁCH NHIỆM VÀ SỰ TÔN TRỌNG</h2>
        <p>Mặc dù hệ thống dành cho cộng đồng, chúng tôi yêu cầu người dùng tôn trọng công sức của nhà phát triển <b>{ADMIN_NAME}</b>. Không sử dụng hệ thống vào các mục đích phi pháp hoặc tấn công mạng.</p>
        
        <h2>4. TÍNH NĂNG ĐỘT PHÁ</h2>
        <p>Hệ thống hỗ trợ gợi ý động theo ngữ cảnh. Mỗi khi bạn trò chuyện, Nexus sẽ học hỏi và đưa ra các lựa chọn thông minh để bạn không phải suy nghĩ nhiều.</p>
        
        <h2>5. CAM KẾT BẢO MẬT</h2>
        <p>Mọi dữ liệu của bạn chỉ tồn tại trong phiên làm việc này. Email hỗ trợ: <b>{ADMIN_EMAIL}</b>. Admin luôn lắng nghe mọi góp ý từ các bạn.</p>
        
        <p><i>(Dùng chuột hoặc thanh cuộn bên phải để đọc toàn bộ văn bản này trên máy tính của bạn)</i></p>
    </div>
    """
    st.markdown(tos_html, unsafe_allow_html=True)
    
    if st.button("TÔI ĐÃ HIỂU VÀ ĐỒNG Ý ✅", use_container_width=True):
        st.session_state.stage = "home"
        st.rerun()

def screen_home():
    apply_theme()
    st.title("💠 NEXUS DASHBOARD")
    st.subheader(f"Giao thức vận hành bởi {ADMIN_NAME}")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.info("💡 Nexus hiện đã mở cửa cho tất cả mọi người. Hãy bắt đầu cuộc hội thoại trí tuệ ngay bây giờ.")
        if st.button("MỞ KÊNH TƯƠNG TÁC AI 🚀", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()
    with c2:
        with st.expander("📊 Thống kê hệ thống"):
            st.write(f"CPU: {psutil.cpu_percent()}%")
            st.write(f"Nhà phát triển: {ADMIN_NAME}")
            if st.button("Quản trị viên"): st.session_state.is_admin = True; st.rerun()
        if st.session_state.is_admin:
            st.success(f"Chào Admin Phát! Email: {ADMIN_EMAIL}")

def screen_chat():
    apply_theme()
    if st.button("⬅️ TRỞ VỀ"): st.session_state.stage = "home"; st.rerun()
    
    # Hiển thị lịch sử chat
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    st.markdown("---")
    
    # HIỂN THỊ GỢI Ý THÔNG MINH THEO NGỮ CẢNH
    st.caption("✨ Nexus gợi ý cho bạn:")
    cols = st.columns(3) # Hàng 1
    for i in range(3):
        if cols[i].button(st.session_state.suggestions[i], key=f"s_{i}", use_container_width=True):
            process_msg(st.session_state.suggestions[i])
            
    cols2 = st.columns(3) # Hàng 2
    for i in range(3, 6):
        if cols2[i-3].button(st.session_state.suggestions[i], key=f"s_{i}", use_container_width=True):
            process_msg(st.session_state.suggestions[i])

    if prompt := st.chat_input("Hỏi Nexus bất cứ điều gì..."):
        process_msg(prompt)

def process_msg(prompt):
    st.session_state.chat_log.append({"role": "user", "content": prompt})
    
    # Gọi AI
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        # System prompt sạch sẽ, không dùng thẻ HTML
        sys = f"Bạn là Nexus, một AI mạnh mẽ dành cho cộng đồng. Sáng tạo bởi {ADMIN_NAME}. Trả lời bằng Markdown rõ ràng, không sử dụng các thẻ HTML như <p> hay <font>."
        messages = [{"role": "system", "content": sys}]
        messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
        
        try:
            client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
            stream = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    full_res += content
                    placeholder.markdown(full_res + "█")
            placeholder.markdown(full_res)
            
            # Cập nhật state
            st.session_state.chat_log.append({"role": "assistant", "content": full_res})
            # CẬP NHẬT GỢI Ý MỚI DỰA TRÊN CÂU TRẢ LỜI
            update_dynamic_suggestions(full_res)
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi kết nối: {e}")

# ĐIỀU HƯỚNG
if st.session_state.stage == "law": screen_law()
elif st.session_state.stage == "home": screen_home()
else: screen_chat()
