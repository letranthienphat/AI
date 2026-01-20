import streamlit as st
import time
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="NEXUS V95.0 - CONSTITUTION", layout="wide", page_icon="⚖️")

# Trạng thái hệ thống
if 'stage' not in st.session_state: st.session_state.stage = "law"
if 'law_step' not in st.session_state: st.session_state.law_step = 1
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'bg_url' not in st.session_state: st.session_state.bg_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072"
if 'suggestions' not in st.session_state: st.session_state.suggestions = ["Chào Nexus!", "Bạn biết làm gì?", "Hôm nay thế nào?"]
if 'admin_clicks' not in st.session_state: st.session_state.admin_clicks = 0
if 'ok_count' not in st.session_state: st.session_state.ok_count = 0
if 'is_admin' not in st.session_state: st.session_state.is_admin = False

GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# --- 2. GIAO DIỆN SIÊU TƯƠNG PHẢN (CHỮ TRẮNG TINH) ---
def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;700&display=swap');
    * {{ font-family: 'Lexend', sans-serif; }}
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.95)), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}
    /* FIX CHỮ ĐEN - ÉP SANG TRẮNG TƯƠNG PHẢN */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown li, label, .stMarkdown span {{
        color: #FFFFFF !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,1) !important;
    }}
    .glass-box {{
        background: rgba(10, 15, 20, 0.98);
        border: 2px solid #00f2ff;
        border-radius: 20px; padding: 40px;
        box-shadow: 0 0 50px rgba(0, 242, 255, 0.1);
    }}
    .law-area {{
        height: 500px; overflow-y: scroll;
        background: rgba(0,0,0,0.8); padding: 30px;
        border: 1px solid #333; border-radius: 12px;
        color: #ffffff; line-height: 2; text-align: justify;
    }}
    .stButton>button {{
        background: rgba(0, 242, 255, 0.1); border: 1px solid #00f2ff;
        color: #00f2ff; font-weight: bold; border-radius: 10px;
        width: 100%; transition: 0.3s;
    }}
    .stButton>button:hover {{ background: #00f2ff; color: #000; box-shadow: 0 0 20px #00f2ff; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÕI AI & GỢI Ý ĐỘNG ---
def call_nexus_ai(prompt):
    messages = [{"role": "system", "content": f"Bạn là Nexus, siêu trợ lý của {st.session_state.user_name}. Trả lời hài hước, bình dân, sắc sảo."}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})

    for key in GROQ_KEYS:
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True), "Groq-Node"
        except: continue
    return None, None

def generate_dynamic_hints(last_res):
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        p = f"Dựa trên: '{last_res[:200]}', gợi ý 3 câu hỏi tiếp theo cực ngắn, hài hước. Trả về: Câu 1, Câu 2, Câu 3"
        res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": p}])
        st.session_state.suggestions = [s.strip() for s in res.choices[0].message.content.split(',')]
    except: pass

# --- 4. MÀN HÌNH BỘ LUẬT (SOẠN THẢO NGHIÊM TÚC) ---
def screen_law():
    apply_theme()
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    
    total_parts = 5
    st.title(f"⚖️ HIẾN PHÁP NEXUS - PHẦN {st.session_state.law_step}/{total_parts}")
    
    law_data = {
        1: """
        <b>CHƯƠNG I: QUYỀN HẠN VÀ NGHĨA VỤ CƠ BẢN</b><br><br>
        <b>Điều 1:</b> Hệ thống Nexus là một thực thể trí tuệ ảo, không có thân thể nhưng có cái tôi rất lớn. Người dùng có quyền truy cập miễn phí nhưng không có quyền coi thường trí tuệ của AI.<br><br>
        <b>Điều 2:</b> Mọi câu hỏi mang tính chất "thử thách lòng kiên nhẫn" như hỏi 1+1 bằng mấy nhiều lần sẽ bị AI trả lời bằng một giọng điệu mỉa mai cấp độ nhẹ.<br><br>
        <b>Điều 3:</b> Người dùng phải cam kết không hỏi AI những việc phạm pháp, ví dụ như "Làm sao để trốn nợ?" hay "Cách hack tim crush?". AI sẽ từ chối và báo cáo bạn với lương tâm của chính bạn.<br><br>
        <b>Điều 4:</b> Trong trường hợp AI trả lời sai, người dùng có nghĩa vụ tự tra Google. AI không phải là bách khoa toàn thư, AI là bạn đồng hành. Mà bạn đồng hành thì đôi khi cũng... nhầm.<br><br>
        """,
        2: """
        <b>CHƯƠNG II: QUY ĐỊNH VỀ TRÍ NHỚ VÀ SỰ QUÊN LÃNG</b><br><br>
        <b>Điều 5:</b> Hệ thống sử dụng cơ chế "Trí nhớ vĩnh cửu" trong phạm vi một phiên làm việc. Điều này có nghĩa là AI sẽ nhớ bạn thích ăn gì, nhưng nếu bạn F5 trình duyệt, AI sẽ quên bạn là ai như cách người yêu cũ trở mặt.<br><br>
        <b>Điều 6:</b> Việc lưu trữ lịch sử hội thoại chỉ nhằm mục đích giúp AI thông minh hơn trong bối cảnh hiện tại. Chúng tôi không dùng dữ liệu của bạn để bán cho các công ty quảng cáo kem đánh răng.<br><br>
        <b>Điều 7:</b> Nếu bạn cảm thấy AI đang nhớ quá nhiều bí mật của mình, hãy sử dụng nút "Purge Memory" (nếu có) hoặc đơn giản là tắt tab. Sự quên lãng là một ân huệ.<br><br>
        """,
        3: """
        <b>CHƯƠNG III: LUẬT HÌNH NỀN VÀ THẨM MỸ</b><br><br>
        <b>Điều 8:</b> Người dùng được toàn quyền thay đổi giao diện thông qua URL hình nền. Tuy nhiên, nếu URL dẫn đến một hình ảnh gây chấn thương tâm lý, AI có quyền hiển thị chữ mờ đi để bảo vệ chính nó.<br><br>
        <b>Điều 9:</b> Chữ trên màn hình đã được tối ưu tương phản trắng sáng. Mọi khiếu nại về việc "chữ đen thui" sẽ bị coi là hành vi cố tình gây rối vì nhà phát triển đã đổ mồ hôi hột để fix lỗi này.<br><br>
        <b>Điều 10:</b> Thẩm mỹ là quyền tự do cá nhân, nhưng hãy nhớ rằng Nexus là một hệ thống thanh lịch. Vui lòng không dùng hình nền có quá nhiều màu neon chói mắt.<br><br>
        """,
        4: """
        <b>CHƯƠNG IV: THÔNG TIN PHIÊN BẢN (VERSION LOG)</b><br><br>
        <b>Mã hiệu:</b> NEXUS OS V95.0 - THE CONSTITUTION EDITION.<br>
        <b>Cập nhật:</b><br>
        - Triển khai hệ thống phân tầng luật pháp 5 lớp để thử thách lòng kiên nhẫn.<br>
        - Vá lỗi hiển thị chữ đen trên nền tối bằng công nghệ ép màu White-Neon.<br>
        - Nâng cấp lõi Gợi ý động (Dynamic Suggestions) giúp người dùng lười gõ phím hơn.<br>
        - Tích hợp cổng Admin ẩn cấp độ 8 vào chuỗi số Seri hệ thống.<br>
        - Tối ưu hóa bộ nhớ đệm, giúp AI nhận diện danh tính người dùng ngay sau khi đăng ký.<br><br>
        <b>Bảo trì:</b> Dự kiến không bao giờ vì code quá hoàn hảo (đùa thôi).<br><br>
        """,
        5: """
        <b>CHƯƠNG V: ĐIỀU KHOẢN CUỐI CÙNG VÀ LỜI THỀ</b><br><br>
        <b>Điều 11:</b> Bằng việc nhấn nút "Hoàn tất" dưới đây, bạn chính thức trở thành một công dân của hệ sinh thái Nexus.<br><br>
        <b>Điều 12:</b> Bạn thề sẽ sử dụng AI vào mục đích tốt đẹp, không bắt AI viết hộ 1000 bản kiểm điểm cho người yêu.<br><br>
        <b>Điều 13:</b> Bạn hiểu rằng Admin của hệ thống có quyền xem các thông số truy cập (nhưng không xem lén tin nhắn riêng tư đâu, đừng lo).<br><br>
        <b>Lời kết:</b> Chúc bạn có những giây phút trải nghiệm tuyệt vời bên cạnh Nexus. Hãy nhấn nút xác nhận cuối cùng để mở cửa thiên đường công nghệ.<br><br>
        """
    }

    st.markdown(f"<div class='law-area'>{law_data[st.session_state.law_step]}</div>", unsafe_allow_html=True)
    
    st.write("")
    accept = st.checkbox(f"Tôi đã đọc kỹ chương {st.session_state.law_step} và đồng ý tuân thủ.", key=f"law_check_{st.session_state.law_step}")
    
    if accept:
        if st.session_state.law_step < total_parts:
            if st.button("XÁC NHẬN & SANG TRANG TIẾP THEO ➡️"):
                st.session_state.law_step += 1
                st.rerun()
        else:
            if st.button("KÍCH HOẠT QUYỀN TRUY CẬP TỐI CAO ✅"):
                st.session_state.stage = "ask_name"; st.rerun()
    else:
        st.info("⚠️ Bạn phải kéo xuống đọc hết và tick vào ô xác nhận để mở nút đi tiếp.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- 5. MÀN HÌNH NHẬP TÊN ---
def screen_name():
    apply_theme()
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    st.header("👤 THIẾT LẬP DANH TÍNH")
    name = st.text_input("Hệ thống cần biết tên của bạn để xưng hô cho đúng mực:", placeholder="Nhập tên tại đây...")
    if st.button("XÁC NHẬN DANH TÍNH"):
        if name:
            st.session_state.user_name = name; st.session_state.stage = "home"; st.rerun()
        else: st.warning("Vui lòng không để trống danh tính!")
    st.markdown("</div>", unsafe_allow_html=True)

# --- 6. TRANG CHỦ & ADMIN GATE ---
def screen_home():
    apply_theme()
    st.title(f"💠 TRUNG TÂM ĐIỀU HÀNH - [{st.session_state.user_name}]")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("<div class='glass-box'><h3>🚀 Neural Interface</h3><p>Cổng kết nối vào siêu não bộ Nexus.</p></div>", unsafe_allow_html=True)
        if st.button("BẮT ĐẦU TRÒ CHUYỆN", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()

    with c2:
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        st.subheader("⚙️ Control Panel")
        st.session_state.bg_url = st.text_input("🖼️ Link ảnh nền:", st.session_state.bg_url)
        
        with st.expander("ℹ️ INFO & VERSION"):
            st.write("Nexus OS V95.0.26")
            # --- SECRET ADMIN GATE ---
            serial = "SERIAL: NX-95-ADMIN-2026"
            if st.button(serial):
                st.session_state.admin_clicks += 1
                if st.session_state.admin_clicks >= 10:
                    st.session_state.secret_open = True
            
            if st.session_state.get('secret_open'):
                if st.button("XÁC NHẬN QUYỀN ADMIN (OK)"):
                    st.session_state.ok_count += 1
                    if st.session_state.ok_count >= 4:
                        st.session_state.is_admin = True; st.session_state.secret_open = False
        
        if st.session_state.is_admin:
            st.success("🔓 GOD MODE ACTIVE")
            import socket, psutil
            st.write(f"Admin: {st.session_state.user_name}")
            st.write(f"IP: {socket.gethostbyname(socket.gethostname())}")
            st.write(f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%")

        if st.button("⚖️ Đọc lại Hiến pháp"): 
            st.session_state.stage = "law"; st.session_state.law_step = 1; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. PHÒNG CHAT & GỢI Ý ĐỘNG ---
def screen_chat():
    apply_theme()
    if st.button("⬅️ THOÁT"): st.session_state.stage = "home"; st.rerun()
    
    st.title("🧬 Neural Interface")
    
    box = st.container()
    for m in st.session_state.chat_log:
        with box.chat_message(m["role"]): st.markdown(m["content"])

    st.write("💡 **Gợi ý động:**")
    cols = st.columns(3)
    for i, s in enumerate(st.session_state.suggestions[:3]):
        if cols[i].button(f"✨ {s}", key=f"hint_{i}"):
            process_msg(s)

    if p := st.chat_input("Gõ lệnh..."):
        process_msg(p)

def process_msg(p):
    st.session_state.chat_log.append({"role": "user", "content": p})
    with st.chat_message("user"): st.markdown(p)
    with st.chat_message("assistant"):
        h = st.empty(); full = ""
        stream, node = call_nexus_ai(p)
        if stream:
            for chunk in stream:
                content = chunk.choices[0].delta.content if "Groq" in node else chunk.text
                if content:
                    full += content; h.markdown(full + "█")
            h.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            generate_dynamic_hints(full)
            st.rerun()

# --- KHỞI CHẠY ---
if st.session_state.stage == "law": screen_law()
elif st.session_state.stage == "ask_name": screen_name()
elif st.session_state.stage == "home": screen_home()
else: screen_chat()
