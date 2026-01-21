import streamlit as st
import time
import random
import pandas as pd
import numpy as np
import psutil
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai

# --- 1. CẤU HÌNH & DỮ LIỆU GIẢ LẬP ---
st.set_page_config(page_title="NEXUS OMNI", layout="wide", page_icon="💠", initial_sidebar_state="collapsed")

# Khởi tạo Session State
defaults = {
    'stage': "law", 'law_step': 1, 'user_name': "", 'chat_log': [],
    'bg_url': "https://images.unsplash.com/photo-1519608487953-e999c9dc296f?q=80&w=2072",
    'suggestions': ["Phân tích thị trường", "Viết code Python", "Tạo kế hoạch ngày", "Tóm tắt văn bản", "Dịch sang tiếng Anh", "Giải thích khái niệm"],
    'admin_clicks': 0, 'ok_count': 0, 'is_admin': False,
    # Fake Stats
    'total_visits': 14205, 'active_users': 312, 'server_uptime': "99.98%"
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])

# --- 2. CSS RESPONSIVE (MẤU CHỐT CỦA GIAO DIỆN) ---
def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    /* Cấu trúc nền tảng */
    .stApp {{
        background: linear-gradient(180deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.95) 100%), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed; background-position: center;
    }}
    
    /* Typography Responsive */
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    h1, h2, h3 {{ font-family: 'JetBrains Mono', monospace; letter-spacing: -1px; }}
    
    /* CHỮ TRẮNG TUYỆT ĐỐI & SHADOW */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown li, label, span, div {{
        color: #FFFFFF !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.8);
    }}

    /* GLASS CONTAINER - TỰ ĐỘNG CO GIÃN */
    .glass-box {{
        background: rgba(10, 15, 20, 0.85);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 242, 255, 0.3);
        border-radius: 16px;
        padding: 5vw; /* Padding theo chiều rộng màn hình */
        margin-bottom: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    }}
    
    /* HIỂN THỊ LUẬT RESPONSIVE */
    .law-text {{
        font-size: clamp(14px, 1.2vw, 18px); /* Chữ tự to nhỏ theo màn hình */
        line-height: 1.8;
        text-align: justify;
        padding: 20px;
        border-left: 2px solid #00f2ff;
        background: rgba(0,0,0,0.6);
        margin-bottom: 20px;
    }}

    /* NÚT BẤM CAO CẤP */
    div.stButton > button {{
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 242, 255, 0.4);
        color: #00f2ff;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        width: 100%;
    }}
    div.stButton > button:hover {{
        background: #00f2ff;
        color: #000;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 242, 255, 0.4);
    }}
    
    /* Ẩn Header mặc định của Streamlit */
    header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIC HỆ THỐNG ---

# Soạn thảo Luật (Phiên bản chuyên nghiệp & hài hước)
def get_law(step):
    headers = ["KHỞI TẠO GIAO THỨC", "BẢO MẬT & QUYỀN RIÊNG TƯ", "TRÁCH NHIỆM PHÁP LÝ", "HỆ THỐNG VẬN HÀNH", "TUYÊN THỆ CUỐI CÙNG"]
    
    texts = {
        1: """
        **ĐIỀU 1.1: ĐỊNH DANH HỆ THỐNG**
        Nexus OS không phải là một công cụ tìm kiếm thông thường. Đây là một giao diện trí tuệ nhân tạo bậc cao được thiết kế để tối ưu hóa hiệu suất làm việc của con người.
        
        **ĐIỀU 1.2: ĐỐI TƯỢNG SỬ DỤNG**
        Dịch vụ này chỉ dành cho các thực thể sinh học (con người) có khả năng đọc hiểu văn bản và có chỉ số kiên nhẫn trên mức trung bình. Nếu bạn là robot, vui lòng nhập mã xác thực nhị phân 010101 rồi tự tắt máy.
        
        **ĐIỀU 1.3: QUY TẮC HIỂN THỊ**
        Hệ thống này được tối ưu hóa hiển thị trên mọi thiết bị. Nếu bạn đang đọc dòng này trên điện thoại dọc, chúc mừng bạn, CSS của tôi hoạt động tốt. Nếu bạn đọc trên máy tính, nó vẫn hoạt động tốt. Đó là sự hoàn hảo.
        """ + ("\n\n(Cuộn xuống tiếp đi, chưa hết đâu...)\n" * 5),
        
        2: """
        **ĐIỀU 2.1: DỮ LIỆU NGƯỜI DÙNG**
        Mọi dữ liệu bạn nhập vào phiên làm việc này sẽ biến mất ngay khi bạn đóng tab trình duyệt, giống như tiền lương biến mất vào cuối tháng vậy. Chúng tôi tôn trọng quyền "được quên" của bạn.
        
        **ĐIỀU 2.2: QUYỀN CHỦ SỞ HỮU**
        Hệ thống này thuộc quyền quản lý tối cao của **Trần Thiện Phát Lê** (tranthienphatle@gmail.com). Mọi nỗ lực sao chép, đảo ngược mã nguồn đều sẽ bị... admin cười nhạo vì code này quá phức tạp để copy.
        """ + ("\n\n(Tiếp tục nào, kiên nhẫn là vàng...)\n" * 5),
        
        3: """
        **ĐIỀU 3.1: MIỄN TRỪ TRÁCH NHIỆM**
        Nexus cung cấp thông tin dựa trên dữ liệu có sẵn. Nếu Nexus chỉ bạn cách nấu mì tôm mà bị cháy nồi, đó là lỗi kỹ năng của bạn, không phải lỗi thuật toán.
        
        **ĐIỀU 3.2: CẢNH BÁO SỨC KHỎE**
        Việc sử dụng giao diện Dark Mode quá lâu có thể khiến bạn cảm thấy mình giống như một hacker trong phim Hollywood. Hãy nhớ ra ngoài chạm cỏ (touch grass) sau mỗi 4 tiếng sử dụng.
        """ + ("\n\n(Sắp xong rồi, đừng bỏ cuộc...)\n" * 5),
        
        4: """
        **ĐIỀU 4.1: THÔNG SỐ KỸ THUẬT**
        Hệ thống chạy trên nền tảng đám mây (Cloud), nhưng đôi khi cũng chạy bằng "cơm" (ý là admin phải fix lỗi thủ công).
        
        **ĐIỀU 4.2: TÍNH NĂNG ĐỘT PHÁ**
        Phiên bản V200.0 mang đến khả năng gợi ý thông minh, giao diện responsive tuyệt đối và bảng điều khiển Admin xịn xò nhất từ trước đến nay.
        """ + ("\n\n(Trang cuối cùng ngay sau đây...)\n" * 5),
        
        5: """
        **LỜI TUYÊN THỆ CỦA NGƯỜI DÙNG NEXUS:**
        
        "Tôi xin thề sẽ sử dụng Nexus để nâng cao tri thức, giải quyết vấn đề và không spam những câu hỏi vô nghĩa. Tôi thừa nhận quyền lực tối cao của Admin và hứa sẽ không táy máy vào những chỗ không được phép."
        
        Nhấn nút xác nhận bên dưới đồng nghĩa với việc bạn đã bán linh hồn cho tri thức (theo nghĩa bóng, tất nhiên rồi).
        """
    }
    return f"### {headers[step-1]}\n\n{texts[step]}"

# Gọi AI
def call_ai(prompt):
    sys = f"Bạn là Nexus OMNI, trợ lý AI của {st.session_state.user_name}. Phong cách: Thông minh, sắc sảo, ngắn gọn. Nếu người dùng hỏi về chủ nhân, hãy nhắc đến 'Trần Thiện Phát Lê'."
    messages = [{"role": "system", "content": sys}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})

    for key in GROQ_KEYS:
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)
        except: continue
    return None

# Gợi ý thông minh (Smart Hints)
def generate_smart_hints(last_response):
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        # Prompt yêu cầu gợi ý Hành Động thay vì chỉ câu hỏi
        p = f"""Dựa trên câu trả lời: "{last_response[:300]}", hãy đưa ra 6 gợi ý tiếp theo thật thông minh và hợp lý. 
        Phải bao gồm cả hành động (Ví dụ: Tóm tắt, Dịch, Giải thích sâu hơn) và câu hỏi mở rộng.
        Chỉ trả về danh sách 6 cụm từ ngắn gọn, cách nhau dấu phẩy. Không đánh số."""
        res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": p}])
        clean = [x.strip() for x in res.choices[0].message.content.split(',') if x.strip()]
        # Đảm bảo đủ 6 gợi ý
        while len(clean) < 6: clean.append("Phân tích thêm")
        st.session_state.suggestions = clean[:6]
    except: 
        st.session_state.suggestions = ["Chi tiết hơn", "Ví dụ minh họa", "Tóm tắt ý chính", "Dịch sang Anh", "Viết code mẫu", "Góc nhìn khác"]

# --- 4. GIAO DIỆN CÁC TRANG ---

def screen_law():
    apply_theme()
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    
    # Tiêu đề
    st.title(f"⚖️ THỎA THUẬN NGƯỜI DÙNG (BƯỚC {st.session_state.law_step}/5)")
    
    # Nội dung luật Responsive
    st.markdown(f"<div class='law-text'>{get_law(st.session_state.law_step)}</div>", unsafe_allow_html=True)
    
    # Timer logic
    t_key = f"timer_{st.session_state.law_step}"
    if t_key not in st.session_state: st.session_state[t_key] = time.time()
    wait = 8 - (time.time() - st.session_state[t_key]) # 8 giây chờ
    
    # Nút bấm Responsive
    col1, col2 = st.columns([1, 1])
    with col2:
        if wait > 0:
            st.warning(f"⏳ Vui lòng đọc kỹ... ({int(wait)}s)")
            time.sleep(1); st.rerun()
        else:
            label = "ĐỒNG Ý & TIẾP TỤC ➡️" if st.session_state.law_step < 5 else "CHẤP NHẬN TOÀN BỘ ✅"
            if st.button(label, use_container_width=True):
                if st.session_state.law_step < 5: st.session_state.law_step += 1
                else: st.session_state.stage = "ask_name"
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def screen_name():
    apply_theme()
    st.markdown("<div class='glass-box' style='text-align: center;'>", unsafe_allow_html=True)
    st.markdown("## 🔐 XÁC THỰC DANH TÍNH")
    st.write("Hệ thống cần biết bạn là ai để cấp quyền truy cập.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name = st.text_input("Nhập Codename của bạn:", placeholder="Ví dụ: Alpha, User 01...")
        if st.button("KẾT NỐI VÀO NEXUS", use_container_width=True):
            if name: 
                st.session_state.user_name = name
                # Tăng stats giả lập
                st.session_state.total_visits += 1
                st.session_state.active_users += 1
                st.session_state.stage = "home"
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def screen_home():
    apply_theme()
    st.markdown(f"# 💠 NEXUS COMMAND CENTER")
    st.markdown(f"Chào mừng đặc vụ **{st.session_state.user_name}**")

    # Layout Dashboard Responsive
    # Hàng 1: Chat & Config
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("<div class='glass-box'><h3>🧠 Neural Core</h3><p>Truy cập vào lõi xử lý ngôn ngữ tự nhiên.</p></div>", unsafe_allow_html=True)
        if st.button("🚀 KHỞI CHẠY GIAO DIỆN CHAT", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()
            
    with c2:
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        st.markdown("### ⚙️ Hệ thống")
        st.session_state.bg_url = st.text_input("Đổi hình nền (URL):", st.session_state.bg_url)
        
        # EASTER EGG KÍCH HOẠT ADMIN
        if st.button(f"Phiên bản: V200.0 (OMNI)"):
            st.session_state.admin_clicks += 1
            if st.session_state.admin_clicks >= 7: st.session_state.show_pass = True
        
        if st.session_state.get('show_pass'):
            if st.button("XÁC NHẬN QUYỀN CHỦ SỞ HỮU"):
                 st.session_state.ok_count += 1
                 if st.session_state.ok_count >= 3:
                     st.session_state.is_admin = True
                     st.session_state.show_pass = False
        st.markdown("</div>", unsafe_allow_html=True)

    # KHU VỰC ADMIN (NẾU ĐƯỢC KÍCH HOẠT)
    if st.session_state.is_admin:
        st.markdown("---")
        st.markdown("## 🛡️ SUPER ADMIN DASHBOARD")
        
        # Thống kê đột phá (Charts)
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Tổng truy cập", f"{st.session_state.total_visits:,}")
        a2.metric("Người dùng Active", st.session_state.active_users)
        a3.metric("Server Uptime", st.session_state.server_uptime)
        a4.metric("CPU Load", f"{psutil.cpu_percent()}%")
        
        # Thông tin chủ sở hữu
        st.info(f"👑 **OWNER:** Trần Thiện Phát Lê | 📧 **EMAIL:** tranthienphatle@gmail.com")
        
        # Biểu đồ giả lập (Analytics)
        chart_data = pd.DataFrame(
            np.random.randn(20, 3),
            columns=['Truy cập', 'Tương tác', 'Tải hệ thống'])
        st.line_chart(chart_data)
        
        if st.button("Đăng xuất Admin"): st.session_state.is_admin = False; st.rerun()

    # Nút đọc lại luật
    if st.button("📜 Xem lại Điều khoản"): st.session_state.stage="law"; st.session_state.law_step=1; st.rerun()

def screen_chat():
    apply_theme()
    if st.button("⬅️ DASHBOARD", use_container_width=True): st.session_state.stage = "home"; st.rerun()
    
    st.markdown("### 🧬 NEXUS OMNI-CHAT")
    
    # Container Chat
    chat_container = st.container()
    for m in st.session_state.chat_log:
        with chat_container.chat_message(m["role"]): st.markdown(m["content"])
    
    # 6 GỢI Ý THÔNG MINH (Responsive Layout)
    st.write("✨ **Đề xuất hành động:**")
    hints = st.session_state.suggestions
    
    # Dùng columns để chia đều gợi ý
    c1, c2, c3 = st.columns(3)
    for i, hint in enumerate(hints):
        if i < 2: col = c1
        elif i < 4: col = c2
        else: col = c3
        
        with col:
            if st.button(hint, key=f"h_{i}", use_container_width=True):
                process_chat(hint)

    # Input Box
    if prompt := st.chat_input("Nhập yêu cầu của bạn..."):
        process_chat(prompt)

def process_chat(txt):
    st.session_state.chat_log.append({"role": "user", "content": txt})
    with st.chat_message("user"): st.markdown(txt)
    
    with st.chat_message("assistant"):
        box = st.empty(); full_res = ""
        stream = call_ai(txt)
        if stream:
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    full_res += content
                    # Hiệu ứng gõ máy
                    box.markdown(full_res + "▌")
            box.markdown(full_res)
            st.session_state.chat_log.append({"role": "assistant", "content": full_res})
            # Tạo gợi ý mới ngay lập tức
            generate_smart_hints(full_res)
            st.rerun()

# --- MAIN CONTROLLER ---
if st.session_state.stage == "law": screen_law()
elif st.session_state.stage == "ask_name": screen_name()
elif st.session_state.stage == "home": screen_home()
else: screen_chat()
