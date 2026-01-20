import streamlit as st
import time
import socket
import psutil
import json
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="NEXUS V88.0", layout="wide", page_icon="🛡️")

# Khởi tạo bộ nhớ logic
initial_states = {
    'stage': "law", 'user_name': "", 'chat_log': [], 
    'bg_url': "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072",
    'suggestions': ["Chào Nexus!", "Hôm nay có gì mới?", "Phân tích dữ liệu"],
    'serial_clicks': 0, 'ok_counter': 0, 'is_admin': False, 'secret_gate_open': False
}
for key, val in initial_states.items():
    if key not in st.session_state: st.session_state[key] = val

GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# --- 2. GIAO DIỆN SIÊU TƯƠNG PHẢN (CSS FIX CHỮ ĐEN) ---
def apply_ultra_contrast():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&family=Fira+Code&display=swap');
    
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.9), rgba(0,0,0,0.95)), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}

    /* FIX CHỮ TRẮNG TINH TRÊN NỀN TỐI */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown span, label {{
        color: #FFFFFF !important;
        text-shadow: 1px 1px 2px #000;
    }}
    
    /* Panel kính cường lực */
    .glass-box {{
        background: rgba(20, 25, 30, 0.98);
        border: 2px solid #00f2ff;
        border-radius: 15px; padding: 25px;
        box-shadow: 0 0 30px rgba(0, 242, 255, 0.2);
    }}

    /* Khung chat tương phản cao */
    div[data-testid="stChatMessage"] {{
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid #00f2ff55 !important;
        border-radius: 10px !important;
    }}

    .law-text {{
        height: 500px; overflow-y: scroll; 
        background: #050505; color: #fff; padding: 20px;
        border: 1px solid #333; font-family: 'Fira Code', monospace;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI XỬ LÝ AI ---
def call_nexus_core(prompt):
    messages = [{"role": "system", "content": f"Bạn là Nexus, trợ lý cao cấp của {st.session_state.user_name}. Trả lời hài hước, bình dân nhưng cực thông minh."}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})

    for i, key in enumerate(GROQ_KEYS):
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True), f"Node-{i+1}"
        except: continue
    return None, None

# --- 4. MÀN HÌNH 1: BỘ LUẬT HÌNH SỰ NEXUS ---
def screen_law():
    apply_ultra_contrast()
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    st.title("⚖️ BỘ LUẬT DÂN SỰ & HÌNH SỰ NEXUS V88.0")
    
    st.markdown("""<div class='law-text'>
    <b>CHƯƠNG 1: QUYỀN ĐƯỢC THỞ VÀ SỬ DỤNG AI</b><br>
    Điều 1: Người dùng có quyền hỏi mọi câu hỏi từ thông minh đến ngây ngô. Hệ thống không có quyền phán xét nhưng có quyền trả lời khịa lại.<br>
    Điều 2: Mọi câu trả lời của hệ thống chỉ mang tính chất tham khảo. Nếu bạn làm theo và bị bồ đá, hệ thống không chịu trách nhiệm.<br><br>
    <b>CHƯƠNG 2: TRÁCH NHIỆM HÌNH NỀN</b><br>
    Điều 3: Việc sử dụng hình nền quá chói mắt gây mù tạm thời cho người khác có thể bị khép vào tội "Gây rối trật tự ảo".<br>
    Điều 4: Cấm dán link hình nền "nhạy cảm". AI có mắt và nó sẽ cảm thấy bị tổn thương.<br><br>
    <b>CHƯƠNG 3: BẢO MẬT VÀ TRÍ NHỚ</b><br>
    Điều 5: Nexus nhớ mọi thứ bạn nói trong phiên này. Nếu bạn nói xấu sếp, hãy nhớ xóa lịch sử trước khi sếp đi ngang qua.<br>
    Điều 6: Dữ liệu của bạn nằm ở đây, nhưng nếu bạn F5 thì nó bay màu. Đừng khóc, đó là tính năng, không phải lỗi.<br><br>
    <b>CHƯƠNG 4: THÔNG TIN PHIÊN BẢN (SIÊU CHI TIẾT)</b><br>
    - Version: V88.0.2026 (Eternal White Edition)<br>
    - Build: 0928374-X<br>
    - Cập nhật cơ chế hiển thị Trắng Sáng (Anti-Dark Mode).<br>
    - Tích hợp cổng Admin ẩn cấp độ 7.<br>
    - Cải thiện tốc độ phản hồi từ 0.5s xuống còn "nhanh như chớp".<br>
    - Vá lỗi "Chatbot hay dỗi" ở bản V84.<br>
    - Thêm 1,500 dòng code chỉ để chạy hiệu ứng cuộn trang.<br><br>
    <i>(Cuộn tiếp đi, vẫn còn 400 trang luật về việc cấm spam nút gửi tin nhắn...)</i>
    </div>""", unsafe_allow_html=True)
    
    if st.checkbox("Tôi xác nhận đã đọc sạch sành sanh và đồng ý làm nô lệ... à nhầm, làm người dùng của Nexus."):
        st.session_state.stage = "ask_name"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 5. MÀN HÌNH 2: XÁC MINH DANH TÍNH ---
def screen_name():
    apply_ultra_contrast()
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    st.header("👤 XÁC MINH DANH TÍNH")
    name = st.text_input("Trước khi vào, vui lòng cho hệ thống biết danh tính của bạn là gì?")
    if st.button("XÁC NHẬN"):
        if name:
            st.session_state.user_name = name
            st.session_state.stage = "home"; st.rerun()
        else: st.warning("Vui lòng nhập tên, đừng để hệ thống gọi bạn là Vô Danh!")
    st.markdown("</div>", unsafe_allow_html=True)

# --- 6. MÀN HÌNH CHÍNH & ADMIN BÍ MẬT ---
def screen_home():
    apply_ultra_contrast()
    st.title(f"🏠 TRUNG TÂM ĐIỀU HÀNH - CHÀO {st.session_state.user_name.upper()}")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("<div class='glass-box'><h3>🚀 Neural Gate</h3><p>Kết nối trực tiếp tới lõi xử lý trung tâm.</p></div>", unsafe_allow_html=True)
        if st.button("MỞ PHÒNG CHAT TƯƠNG TÁC", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()

    with col2:
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        st.subheader("⚙️ CÀI ĐẶT TỐI CAO")
        st.session_state.bg_url = st.text_input("🔗 URL Hình nền:", st.session_state.bg_url)
        
        # --- THÔNG TIN PHIÊN BẢN (DÀI CỰC KỲ KHI NHẤN) ---
        with st.expander("ℹ️ THÔNG TIN PHIÊN BẢN (NHẤN ĐỂ XEM)"):
            st.write("📌 Nexus OS V88.0 - Code name: 'The Bright Knight'")
            st.write("📍 Kernel: Hybrid 9.4.1 | Architecture: Neural-X")
            st.write("Dữ liệu cập nhật dài 10,000 dòng: Fix lỗi hiển thị chữ đen, tối ưu hóa bộ nhớ đệm, thêm AI gợi ý hành vi, nâng cấp lớp bảo mật Admin Gate, cải tiến tốc độ stream dữ liệu, sửa lỗi người dùng quá đẹp trai/xinh gái khiến AI bối rối...")
            
            # --- SECRET ADMIN GATE ---
            serial_num = "SN: NX-888-2026-SECURE"
            if st.button(serial_num):
                st.session_state.serial_clicks += 1
                if st.session_state.serial_clicks >= 10:
                    st.session_state.secret_gate_open = True
            
            if st.session_state.secret_gate_open:
                st.markdown("---")
                st.error("❗ PHÁT HIỆN TRUY CẬP TRÁI PHÉP. XÁC NHẬN OK?")
                if st.button(f"XÁC NHẬN OK ({st.session_state.ok_counter}/4)"):
                    st.session_state.ok_counter += 1
                    if st.session_state.ok_counter >= 4:
                        st.session_state.is_admin = True
                        st.session_state.secret_gate_open = False
        
        if st.session_state.is_admin:
            st.success("🔓 QUYỀN ADMIN ĐÃ KÍCH HOẠT")
            st.write(f"**Admin hiện tại:** {st.session_state.user_name}")
            st.write(f"**Máy chủ:** {socket.gethostname()}")
            st.write(f"**Địa chỉ IP:** {socket.gethostbyname(socket.gethostname())}")
            st.write(f"**Thiết bị:** {psutil.cpu_count()} Cores | {round(psutil.virtual_memory().total / (1024**3), 2)} GB RAM")
            if st.button("ĐÓNG QUYỀN ADMIN"):
                st.session_state.is_admin = False; st.session_state.serial_clicks = 0; st.session_state.ok_counter = 0; st.rerun()

        if st.button("⚖️ Xem lại Bộ Luật"): st.session_state.stage = "law"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. PHÒNG CHAT ---
def screen_chat():
    apply_ultra_contrast()
    if st.button("⬅️ THOÁT RA NGOÀI"): st.session_state.stage = "home"; st.rerun()
    st.title("🧬 Nexus Neural Interface")
    
    chat_box = st.container()
    for m in st.session_state.chat_log:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    # TÁCH CÁC NÚT GỢI Ý ĐỘNG (CHỈ HIỆN KHI KHÔNG TRONG CHẾ ĐỘ NHẬP ADMIN)
    if not st.session_state.secret_gate_open:
        st.write("💡 **Nexus gợi ý:**")
        cols = st.columns(3)
        for i, sug in enumerate(st.session_state.suggestions[:3]):
            if cols[i].button(f"✨ {sug}", key=f"sug_{i}"):
                process_msg(sug)

    if p := st.chat_input("Nhập lệnh tại đây..."):
        process_msg(p)

def process_msg(p):
    st.session_state.chat_log.append({"role": "user", "content": p})
    with st.chat_message("user"): st.markdown(p)
    with st.chat_message("assistant"):
        holder = st.empty(); full = ""
        stream, node = call_nexus_core(p)
        if stream:
            for chunk in stream:
                content = chunk.choices[0].delta.content if "Node" in node else chunk.text
                if content:
                    full += content; holder.markdown(full + "█")
            holder.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "law": screen_law()
elif st.session_state.stage == "ask_name": screen_name()
elif st.session_state.stage == "home": screen_home()
else: screen_chat()
