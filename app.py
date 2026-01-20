import streamlit as st
import time
import json
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai

# --- 1. CẤU HÌNH & SESSION STATE ---
st.set_page_config(page_title="NEXUS V90.0 - ETERNAL", layout="wide", page_icon="📜")

# Khởi tạo các trạng thái
if 'stage' not in st.session_state: st.session_state.stage = "law"
if 'law_step' not in st.session_state: st.session_state.law_step = 1
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'bg_url' not in st.session_state: st.session_state.bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072"
if 'suggestions' not in st.session_state: st.session_state.suggestions = ["Bắt đầu nào!", "Bạn là ai?", "Làm bài thơ đi"]
if 'serial_clicks' not in st.session_state: st.session_state.serial_clicks = 0
if 'ok_count' not in st.session_state: st.session_state.ok_count = 0
if 'is_admin' not in st.session_state: st.session_state.is_admin = False

GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# --- 2. CSS SIÊU TƯƠNG PHẢN ---
def apply_ui_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;700&display=swap');
    * {{ font-family: 'Lexend', sans-serif; }}
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.9), rgba(0,0,0,0.95)), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}
    /* CHỮ TRẮNG TUYỆT ĐỐI */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, label, .stMarkdown li {{
        color: #FFFFFF !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }}
    .glass-card {{
        background: rgba(15, 18, 25, 0.98);
        border: 2px solid #00f2ff;
        border-radius: 20px; padding: 30px;
        box-shadow: 0 0 40px rgba(0, 242, 255, 0.2);
    }}
    .law-scroll {{
        height: 450px; overflow-y: scroll;
        background: rgba(0,0,0,0.7); padding: 25px;
        border: 1px solid #333; border-radius: 10px;
        color: #eee; line-height: 1.8;
    }}
    /* Tách nút gợi ý */
    .stButton>button {{
        border-radius: 12px; border: 1px solid #00f2ff55;
        background: rgba(0, 242, 255, 0.05); color: #00f2ff;
        font-weight: bold; transition: 0.3s; width: 100%;
    }}
    .stButton>button:hover {{
        background: #00f2ff; color: #000; box-shadow: 0 0 20px #00f2ff;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI AI & GỢI Ý ĐỘNG ---
def call_ai(prompt):
    messages = [{"role": "system", "content": f"Bạn là Nexus, trợ lý của {st.session_state.user_name}. Trả lời hài hước, dùng ngôn ngữ bình dân, 'khịa' nhẹ nhàng nếu cần."}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})

    for key in GROQ_KEYS:
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True), "Groq-Core"
        except: continue
    return None, None

def generate_hints(last_response):
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        prompt = f"Dựa trên câu trả lời này: '{last_response[:300]}', hãy gợi ý 3 câu hỏi ngắn (dưới 8 từ) để hỏi tiếp, phong cách hài hước. Trả về dạng: Câu 1, Câu 2, Câu 3"
        res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
        st.session_state.suggestions = [s.strip() for s in res.choices[0].message.content.split(',')]
    except:
        st.session_state.suggestions = ["Kể tiếp đi!", "Nói rõ hơn xem", "Chốt kèo này sao?"]

# --- 4. MÀN HÌNH BỘ LUẬT (MULTI-STAGE) ---
def screen_law():
    apply_ui_theme()
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    
    total_steps = 5
    st.title(f"⚖️ BỘ LUẬT NEXUS - PHẦN {st.session_state.law_step}/{total_steps}")
    
    # Nội dung giả lập dài (Bạn có thể copy thêm 5000 từ vào đây)
    law_content = {
        1: "<b>CHƯƠNG 1: QUYỀN LỢI CỦA 'THƯỢNG ĐẾ'</b><br>" + "Làm người ai làm thế... " * 300 + "<br>Bạn có quyền hỏi, Nexus có quyền trả lời hoặc đi ngủ.",
        2: "<b>CHƯƠNG 2: NGHĨA VỤ CỦA 'CON SEN'</b><br>" + "Hỏi thì phải hỏi cho hay... " * 300 + "<br>Cấm hỏi những câu như 'Người yêu cũ có còn yêu mình không?'.",
        3: "<b>CHƯƠNG 3: CHẾ TÀI HÌNH NỀN</b><br>" + "Hình nền phải sạch, đẹp, thơm... " * 300 + "<br>Dán link bậy bạ AI sẽ tự động phát nổ (trong tâm trí).",
        4: "<b>CHƯƠNG 4: THÔNG TIN PHIÊN BẢN (DÀI HÀNG KM)</b><br>" + "Fix lỗi từ năm 1900... " * 300 + "<br>Build V90.0: Nâng cấp AI gợi ý, vá lỗi chữ đen, thêm tính năng bắt người dùng đọc luật.",
        5: "<b>CHƯƠNG 5: LỜI THỀ HUYẾT TỘC</b><br>" + "Tôi thề sẽ không bao giờ bỏ cuộc... " * 300 + "<br>Kết thúc bộ luật dài 5000 từ. Bạn là người hùng nếu đọc đến đây!"
    }
    
    st.markdown(f"<div class='law-scroll'>{law_content[st.session_state.law_step]}</div>", unsafe_allow_html=True)
    
    st.write("")
    confirm = st.checkbox(f"Tôi xác nhận đã đọc và thấm nhuần kiến thức ở Phần {st.session_state.law_step}.", key=f"check_{st.session_state.law_step}")
    
    if confirm:
        if st.session_state.law_step < total_steps:
            if st.button("TIẾP TỤC TRANG KẾ ➡️"):
                st.session_state.law_step += 1
                st.rerun()
        else:
            if st.button("KÍCH HOẠT HỆ THỐNG (CHỐT KÈO) ✅"):
                st.session_state.stage = "ask_name"; st.rerun()
    else:
        st.info("💡 Bạn phải tick vào ô xác nhận ở trên để hiện nút đi tiếp. Đừng hòng cuộn xuống đáy mà thoát được!")
    st.markdown("</div>", unsafe_allow_html=True)

# --- 5. MÀN HÌNH NHẬP TÊN ---
def screen_name():
    apply_ui_theme()
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.header("👤 DANH TÍNH CỦA BẠN")
    name = st.text_input("Vui lòng cho biết quý danh trước khi vào phòng chat:", placeholder="Ví dụ: Anh Ba, Chị Bảy...")
    if st.button("XÁC NHẬN VÀO HUB"):
        if name:
            st.session_state.user_name = name; st.session_state.stage = "home"; st.rerun()
        else: st.warning("Đừng để Nexus gọi bạn là 'Người lạ ơi'!")
    st.markdown("</div>", unsafe_allow_html=True)

# --- 6. MÀN HÌNH CHÍNH (HUB) ---
def screen_home():
    apply_ui_theme()
    st.title(f"🌐 HUB ĐIỀU HÀNH - CHÀO {st.session_state.user_name.upper()}")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("<div class='glass-card'><h3>🤖 Neural Interface</h3><p>Mở cổng trò chuyện với Nexus.</p></div>", unsafe_allow_html=True)
        if st.button("VÀO PHÒNG CHAT 🚀", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()
    with c2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("⚙️ Cài đặt")
        st.session_state.bg_url = st.text_input("🖼️ Link hình nền:", st.session_state.bg_url)
        
        # EASTER EGG: ADMIN GATE
        with st.expander("ℹ️ THÔNG TIN HỆ THỐNG"):
            st.write("Phiên bản: V90.0.1 (Eternal White)")
            if st.button("SỐ SERI: NX-2026-BETA-09"):
                st.session_state.serial_clicks += 1
                if st.session_state.serial_clicks >= 10:
                    st.session_state.secret_gate = True
            
            if st.session_state.get('secret_gate'):
                st.warning("Xác nhận quyền sở hữu?")
                if st.button("OK"):
                    st.session_state.ok_count += 1
                    if st.session_state.ok_count >= 4:
                        st.session_state.is_admin = True
                        st.session_state.secret_gate = False
        
        if st.session_state.is_admin:
            st.success("🔓 QUYỀN ADMIN ĐÃ MỞ")
            st.write(f"User: {st.session_state.user_name}")
            import socket
            st.code(f"IP: {socket.gethostbyname(socket.gethostname())}\nStatus: GOD MODE", language="bash")

        if st.button("⚖️ Đọc lại Bộ Luật"): st.session_state.stage = "law"; st.session_state.law_step = 1; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. PHÒNG CHAT & GỢI Ý ĐỘNG ---
def screen_chat():
    apply_ui_theme()
    if st.button("⬅️ THOÁT"): st.session_state.stage = "home"; st.rerun()
    
    st.title("🧬 Nexus Neural Interface")
    
    chat_box = st.container()
    for m in st.session_state.chat_log:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    # HIỂN THỊ GỢI Ý ĐỘNG (TÁCH BIỆT)
    st.write("💡 **Gợi ý từ Nexus:**")
    h_cols = st.columns(3)
    for i, sug in enumerate(st.session_state.suggestions[:3]):
        if h_cols[i].button(f"✨ {sug}", key=f"sug_{i}"):
            process_msg(sug)

    if p := st.chat_input("Hỏi gì đi..."):
        process_msg(p)

def process_msg(p):
    st.session_state.chat_log.append({"role": "user", "content": p})
    with st.chat_message("user"): st.markdown(p)
    with st.chat_message("assistant"):
        holder = st.empty(); full = ""
        stream, node = call_ai(p)
        if stream:
            for chunk in stream:
                content = chunk.choices[0].delta.content if "Groq" in node else chunk.text
                if content:
                    full += content; holder.markdown(full + "█")
            holder.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            # TỰ ĐỘNG SINH GỢI Ý ĐỘNG CHO LƯỢT TIẾP THEO
            generate_hints(full)
            st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "law": screen_law()
elif st.session_state.stage == "ask_name": screen_name()
elif st.session_state.stage == "home": screen_home()
else: screen_chat()
