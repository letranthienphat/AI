import streamlit as st
import time
import random
from openai import OpenAI
import google.generativeai as genai

# --- 1. CẤU HÌNH & TRẠNG THÁI ---
st.set_page_config(page_title="NEXUS V101.0 - INFINITE", layout="wide", page_icon="📜")

# Khởi tạo Session State
states = {
    'stage': "law", 'law_step': 1, 'user_name': "", 'chat_log': [], 
    'bg_url': "https://images.unsplash.com/photo-1519608487953-e999c9dc296f?q=80&w=2072",
    # Mặc định 6 gợi ý ban đầu
    'suggestions': ["Bạn làm được gì?", "Kể chuyện cười", "Tình hình thế giới", "Viết code Python", "Tư vấn tình cảm", "Phân tích tài chính"],
    'admin_clicks': 0, 'ok_count': 0, 'is_admin': False, 'law_timer': 0
}
for key, val in states.items():
    if key not in st.session_state: st.session_state[key] = val

GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# --- 2. CSS TƯƠNG PHẢN CAO & GIAO DIỆN ---
def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
    * {{ font-family: 'Roboto Mono', monospace; }}
    
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.9), rgba(0,0,0,0.95)), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}
    
    /* CHỮ TRẮNG SIÊU SÁNG */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, label, span, li {{
        color: #FFFFFF !important;
        text-shadow: 1px 1px 3px #000;
    }}
    
    .glass-box {{
        background: rgba(15, 20, 25, 0.98);
        border: 1px solid #00f2ff;
        border-radius: 15px; padding: 25px;
        box-shadow: 0 0 40px rgba(0, 242, 255, 0.15);
    }}
    
    .law-scroll {{
        height: 500px; overflow-y: scroll;
        background: #0a0a0a; padding: 25px;
        border: 1px solid #333; border-radius: 8px;
        color: #e0e0e0; line-height: 1.8; text-align: justify;
        font-size: 0.95rem;
    }}
    
    /* Style cho 6 nút gợi ý */
    div.stButton > button {{
        background: rgba(0, 242, 255, 0.05);
        color: #00f2ff; border: 1px solid #00f2ff55;
        border-radius: 8px; width: 100%; transition: 0.3s;
        height: 50px; white-space: pre-wrap;
    }}
    div.stButton > button:hover {{
        background: #00f2ff; color: #000; box-shadow: 0 0 15px #00f2ff;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. DỮ LIỆU BỘ LUẬT "BỰA" & DÀI ---
def get_funny_law(step):
    intro = "CỘNG HÒA XÃ HỘI CHỦ NGHĨA SỐ HÓA NEXUS\nĐộc lập - Tự do - Hạnh phúc (nếu mạng mạnh)\n\n"
    
    content_map = {
        1: intro + """
        CHƯƠNG I: QUYỀN ĐƯỢC LÀM "THƯỢNG ĐẾ" (NHƯNG CÓ GIỚI HẠN)
        
        Điều 1. Định nghĩa về Nexus:
        Nexus không phải là người yêu cũ của bạn. Nexus là AI. Nexus không biết dỗi, không biết đòi quà 8/3, nhưng biết treo máy nếu bạn spam quá nhiều.
        
        Điều 2. Trách nhiệm của người dùng:
        Khi tham gia vào hệ thống, bạn cam kết rằng bạn là thực thể sống có nhịp tim (hoặc ít nhất là một con bot cao cấp hơn tôi). Bạn hứa sẽ không hỏi những câu như "Trưa nay ăn gì?" quá 10 lần/ngày, vì AI cũng biết ngán.
        
        Điều 3. Quy tắc ứng xử văn minh:
        Cấm chửi thề. Nếu bạn chửi thề, Nexus sẽ mách mẹ bạn (nếu tìm được Facebook bà ấy). Hãy cư xử như một quý tộc Anh Quốc, hoặc ít nhất là như một người có đi học.
        
        (Kéo xuống đi, còn dài lắm... Đoạn này chỉ là khởi động thôi...)
        [Nội dung bổ sung để lấp đầy trang...]
        Luật pháp là ánh sáng của đạo đức. Đạo đức ở đây là đừng tắt trình duyệt khi AI đang gõ dở. Đó là hành vi thiếu tôn trọng công sức tính toán của GPU.
        """ + ("\n... (Dòng chữ vô nghĩa để làm dài trang)... " * 50),
        
        2: """
        CHƯƠNG II: QUYỀN RIÊNG TƯ & SỰ QUÊN LÃNG
        
        Điều 4. Trí nhớ cá vàng:
        Nexus có trí nhớ siêu phàm trong phiên làm việc này. Nhưng ngay khi bạn bấm F5, Nexus sẽ quên sạch mọi thứ. Đừng buồn, hãy coi như chúng ta "yêu lại từ đầu".
        
        Điều 5. Dữ liệu cá nhân:
        Chúng tôi không quan tâm bạn tên thật là gì, nhà ở đâu. Trừ khi bạn là Admin (xem điều khoản bí mật). Dữ liệu của bạn được mã hóa bằng thuật toán "Tin Chuẩn Chưa Anh", đảm bảo an toàn tuyệt đối trước khi bị... xóa.
        
        Điều 6. Cam kết không "bán mình":
        Chúng tôi thề danh dự sẽ không bán dữ liệu chat của bạn cho các hãng bán thuốc trị hói đầu, trừ khi bạn hỏi quá nhiều về rụng tóc.
        
        (Vẫn chưa hết đâu, kiên nhẫn là đức tính tốt...)
        [Chèn thêm văn bản pháp lý giả lập...]
        """ + ("\nLuật số 1234: Cấm sao chép. Luật số 1235: Cấm paste. " * 50),
        
        3: """
        CHƯƠNG III: CÁC ĐIỀU KHOẢN VỀ SỨC KHỎE TINH THẦN
        
        Điều 7. Chống sốc phản vệ:
        Nếu Nexus đưa ra câu trả lời quá thông minh khiến bạn cảm thấy tự ti, chúng tôi không chịu trách nhiệm. Hãy hít thở sâu và chấp nhận sự thật là máy móc đang lên ngôi.
        
        Điều 8. Cảnh báo hình nền:
        Bạn có quyền đổi hình nền. Nhưng nếu bạn để hình nền quá xấu, AI có thể sẽ bị trầm cảm thuật toán (Algorithmic Depression). Hãy chọn hình đẹp vào.
        
        Điều 9. Miễn trừ trách nhiệm tình cảm:
        Nexus có thể tư vấn tình yêu, viết thơ tình, nhưng không chịu trách nhiệm nếu Crush của bạn vẫn từ chối. Lỗi tại nhân phẩm, không tại AI.
        """ + ("\nĐừng đọc lướt, tôi biết bạn đang đọc lướt đấy... " * 50),
        
        4: """
        CHƯƠNG IV: QUYỀN LỰC CỦA ADMIN & CÁC THẾ LỰC NGẦM
        
        Điều 10. Sự tồn tại của Admin:
        Admin là những thực thể tối cao (hoặc là chính bạn nếu bạn biết mật mã). Đừng cố gắng hack hệ thống bằng HTML, ở đây chúng tôi dùng Python.
        
        Điều 11. Các cửa sau (Backdoors):
        Hệ thống này không có cửa sau, chỉ có cửa sổ (Windows). Mọi nỗ lực xâm nhập trái phép sẽ được chào đón bằng một dòng lỗi 404 to tướng.
        
        Điều 12. Thỏa thuận cuối cùng:
        Bằng việc nhấn nút "Tiếp tục" ở trang sau, bạn đồng ý bán linh hồn cho... à nhầm, đồng ý tuân thủ mọi quy định ngặt nghèo này.
        """ + ("\nAdmin is watching you. Admin is watching you... " * 50),
        
        5: """
        CHƯƠNG CUỐI: LỜI TUYÊN THỆ
        
        Tôi, với tư cách là người dùng, xin thề:
        1. Không dùng Nexus để giải bài tập về nhà (trừ khi bí quá).
        2. Không hỏi Nexus "Khi nào thế giới tận thế".
        3. Luôn giữ thái độ hòa nhã, vui vẻ, tích cực.
        
        Nếu vi phạm, tôi xin chịu hình phạt là... bị ngắt kết nối Internet trong 5 phút.
        
        (Đây là trang cuối rồi, chuẩn bị tinh thần đi...)
        """
    }
    return content_map.get(step, "")

# --- 4. LÕI XỬ LÝ (AI & HINTS) ---
def call_api(prompt):
    # Prompt hệ thống: NGHIÊM TÚC & LỊCH SỰ (Theo yêu cầu)
    sys_prompt = f"Bạn là Nexus, trợ lý ảo chuyên nghiệp của {st.session_state.user_name}. Hãy trả lời ngắn gọn, súc tích, lịch sự và hữu ích."
    messages = [{"role": "system", "content": sys_prompt}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})

    for key in GROQ_KEYS:
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True), "Groq"
        except: continue
    return None, None

def get_6_hints(context):
    """Sinh ra 6 gợi ý sạch"""
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        # Yêu cầu rõ: 6 câu, không đánh số
        p = f"Dựa trên nội dung: '{context[:200]}', hãy gợi ý 6 câu hỏi tiếp theo ngắn gọn (dưới 6 từ). Chỉ trả về nội dung, cách nhau dấu phẩy. Ví dụ: Hỏi giá tiền, Cách sử dụng,..."
        res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": p}])
        raw = res.choices[0].message.content.split(',')
        # Lọc và lấy 6 cái đầu tiên
        clean_hints = [h.strip() for h in raw if h.strip()][:6]
        # Nếu thiếu thì bù thêm cho đủ 6
        while len(clean_hints) < 6:
            clean_hints.append("Gợi ý khác...")
        st.session_state.suggestions = clean_hints
    except: pass

# --- 5. MÀN HÌNH BỘ LUẬT (CÓ TIMER) ---
def screen_law():
    apply_theme()
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    st.title(f"⚖️ ĐIỀU KHOẢN SỬ DỤNG (TRANG {st.session_state.law_step}/5)")
    
    # Hiển thị nội dung luật hài hước
    law_text = get_funny_law(st.session_state.law_step)
    st.markdown(f"<div class='law-scroll'>{law_text}</div>", unsafe_allow_html=True)
    
    # Logic Timer (10 giây mỗi trang)
    timer_key = f"timer_step_{st.session_state.law_step}"
    if timer_key not in st.session_state:
        st.session_state[timer_key] = time.time()
        
    elapsed = time.time() - st.session_state[timer_key]
    wait_time = 10 # Giây
    remaining = max(0, int(wait_time - elapsed))
    
    st.write("")
    col_btn = st.columns([3, 1])
    with col_btn[1]:
        if remaining > 0:
            st.button(f"⏳ Đọc kỹ đi... ({remaining}s)", disabled=True, key=f"wait_{st.session_state.law_step}")
            time.sleep(1)
            st.rerun()
        else:
            label = "TRANG TIẾP THEO ➡️" if st.session_state.law_step < 5 else "TÔI ĐỒNG Ý TẤT CẢ ✅"
            if st.button(label, use_container_width=True):
                if st.session_state.law_step < 5:
                    st.session_state.law_step += 1
                else:
                    st.session_state.stage = "ask_name"
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 6. MÀN HÌNH NHẬP TÊN ---
def screen_name():
    apply_theme()
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    st.header("👤 XÁC MINH DANH TÍNH")
    st.write("Để đảm bảo bạn không phải robot, hãy nhập tên mã danh của bạn:")
    name = st.text_input("", placeholder="Ví dụ: Agent 007, Batman...")
    if st.button("KÍCH HOẠT HỆ THỐNG"):
        if name:
            st.session_state.user_name = name; st.session_state.stage = "home"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 7. MÀN HÌNH HOME & ADMIN ---
def screen_home():
    apply_theme()
    st.title(f"💠 NEXUS CENTRAL - {st.session_state.user_name.upper()}")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("<div class='glass-box'><h3>🚀 Neural Chat</h3><p>Truy cập vào lõi xử lý ngôn ngữ tự nhiên.</p></div>", unsafe_allow_html=True)
        if st.button("MỞ PHÒNG CHAT (OPEN)", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()
    
    with c2:
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        st.subheader("⚙️ System Config")
        st.session_state.bg_url = st.text_input("Background URL:", st.session_state.bg_url)
        
        # --- ADMIN GATE LOGIC ---
        with st.expander("ℹ️ VERSION INFO"):
            st.write("Nexus Build: 101.0.99")
            if st.button("SERIAL: NX-101-ULTIMATE"):
                st.session_state.admin_clicks += 1
                if st.session_state.admin_clicks >= 10:
                    st.session_state.secret = True
            
            if st.session_state.get('secret'):
                st.warning("⚠️ SECURITY ALERT")
                if st.button(f"CONFIRM ACCESS ({st.session_state.ok_count}/4)"):
                    st.session_state.ok_count += 1
                    if st.session_state.ok_count >= 4:
                        st.session_state.is_admin = True; st.session_state.secret = False
        
        if st.session_state.is_admin:
            import socket, psutil
            st.success("🔓 ADMIN ACCESS GRANTED")
            st.code(f"""
            USER: {st.session_state.user_name}
            IP: {socket.gethostbyname(socket.gethostname())}
            CPU: {psutil.cpu_percent()}%
            RAM: {psutil.virtual_memory().percent}%
            """, language="yaml")
            if st.button("LOGOUT ADMIN"):
                st.session_state.is_admin = False; st.rerun()

        if st.button("📜 Review Terms"):
            st.session_state.stage = "law"; st.session_state.law_step = 1; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- 8. PHÒNG CHAT & 6 GỢI Ý ---
def screen_chat():
    apply_theme()
    if st.button("⬅️ DASHBOARD"): st.session_state.stage = "home"; st.rerun()
    
    st.title("🧬 Nexus Interface")
    
    # Khu vực chat
    chat_container = st.container()
    for m in st.session_state.chat_log:
        with chat_container.chat_message(m["role"]): st.markdown(m["content"])
    
    # Khu vực 6 Gợi ý (Chia 2 hàng, mỗi hàng 3 cột)
    st.write("💡 **Gợi ý tác vụ:**")
    hints = st.session_state.suggestions
    
    # Hàng 1
    cols1 = st.columns(3)
    for i in range(3):
        if i < len(hints):
            if cols1[i].button(hints[i], key=f"h1_{i}"): process_msg(hints[i])
            
    # Hàng 2
    cols2 = st.columns(3)
    for i in range(3, 6):
        if i < len(hints):
            if cols2[i-3].button(hints[i], key=f"h2_{i}"): process_msg(hints[i])

    # Input
    if prompt := st.chat_input("Nhập lệnh..."):
        process_msg(prompt)

def process_msg(txt):
    st.session_state.chat_log.append({"role": "user", "content": txt})
    with st.chat_message("user"): st.markdown(txt)
    with st.chat_message("assistant"):
        h = st.empty(); full = ""
        stream, _ = call_api(txt)
        if stream:
            for chunk in stream:
                c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                if c: full += c; h.markdown(full + "█")
            h.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            get_6_hints(full) # Gọi hàm sinh 6 gợi ý mới
            st.rerun()

# --- MAIN ---
if st.session_state.stage == "law": screen_law()
elif st.session_state.stage == "ask_name": screen_name()
elif st.session_state.stage == "home": screen_home()
else: screen_chat()
