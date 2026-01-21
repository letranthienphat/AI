
import streamlit as st
import time
import random
from openai import OpenAI
import google.generativeai as genai

# --- 1. CẤU HÌNH & TRẠNG THÁI ---
st.set_page_config(page_title="NEXUS V102.0", layout="wide", page_icon="⚖️")

states = {
    'stage': "law", 'law_step': 1, 'user_name': "", 'chat_log': [], 
    'bg_url': "https://images.unsplash.com/photo-1519608487953-e999c9dc296f?q=80&w=2072",
    'suggestions': ["Phân tích dữ liệu", "Viết email công việc", "Tạo lịch trình", "Tra cứu thông tin", "Dịch thuật", "Giải trí nhẹ nhàng"],
    'admin_clicks': 0, 'ok_count': 0, 'is_admin': False
}
for key, val in states.items():
    if key not in st.session_state: st.session_state[key] = val

GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# --- 2. CSS TƯƠNG PHẢN CAO (FULL PAGE READ) ---
def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@300;400;700&display=swap');
    * {{ font-family: 'Roboto Slab', serif; }}
    
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.9), rgba(0,0,0,0.95)), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}
    
    /* CHỮ TRẮNG TRÀN MÀN HÌNH - DỄ ĐỌC */
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown li {{
        color: #FFFFFF !important;
        text-shadow: 1px 1px 2px #000;
        line-height: 1.8;
        font-size: 1.1rem;
    }}
    
    .glass-container {{
        background: rgba(10, 10, 10, 0.85);
        border-top: 2px solid #00f2ff;
        border-bottom: 2px solid #00f2ff;
        padding: 40px; margin-bottom: 20px;
        box-shadow: 0 0 50px rgba(0, 0, 0, 0.5);
    }}
    
    /* Nút bấm gợi ý đẹp */
    div.stButton > button {{
        background: rgba(255, 255, 255, 0.05);
        color: #00f2ff; border: 1px solid #00f2ff55;
        border-radius: 5px; width: 100%; transition: 0.3s;
        font-family: sans-serif;
    }}
    div.stButton > button:hover {{
        background: #00f2ff; color: #000;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. NỘI DUNG LUẬT "ĐÀNG HOÀNG" (DÀI & CHI TIẾT) ---
def get_law_content(step):
    header = f"### VĂN BẢN THỎA THUẬN SỬ DỤNG DỊCH VỤ SỐ NEXUS (PHẦN {step}/5)\n\n"
    
    texts = {
        1: """
        **ĐIỀU 1: PHẠM VI ÁP DỤNG VÀ ĐỊNH NGHĨA**
        
        1.1. Nexus (sau đây gọi tắt là "Hệ thống") là một giao diện trí tuệ nhân tạo được thiết kế nhằm mục đích hỗ trợ người dùng thực hiện các tác vụ thông tin, xử lý dữ liệu và giải trí lành mạnh.
        
        1.2. "Người dùng" (sau đây gọi tắt là "Bạn") được định nghĩa là thực thể sinh học hoặc kỹ thuật số có khả năng tương tác với bàn phím và chuột, có đầy đủ năng lực hành vi dân sự để chịu trách nhiệm cho những câu hỏi ngớ ngẩn của mình.
        
        1.3. Bằng việc truy cập vào Hệ thống này, Bạn xác nhận rằng Bạn không phải là robot của phe đối lập, không phải là điệp viên công nghệ, và quan trọng nhất: Bạn đã ăn sáng (hoặc ăn trưa/tối) đầy đủ để đảm bảo não bộ hoạt động bình thường khi giao tiếp với AI.
        
        **ĐIỀU 2: QUYỀN LỢI CỦA NGƯỜI DÙNG**
        
        2.1. Bạn có quyền đặt câu hỏi không giới hạn về số lượng (trong khuôn khổ API cho phép). Tuy nhiên, Hệ thống có quyền từ chối trả lời nếu phát hiện câu hỏi mang tính chất spam, ví dụ: "Em ăn cơm chưa?" lặp lại 50 lần.
        
        2.2. Bạn được quyền thay đổi giao diện hình nền theo sở thích cá nhân. Tuy nhiên, Hệ thống khuyến cáo không sử dụng hình ảnh gây ảo giác mạnh, hình ảnh kinh dị hoặc hình ảnh người yêu cũ để tránh gây xung đột cảm xúc trong quá trình làm việc.
        
        *(Vui lòng cuộn xuống cuối trang để xác nhận...)*
        """ + ("\n\n" + "&nbsp;"*10 + "...\n\n") * 5, # Tạo khoảng trắng giả để ép scroll
        
        2: """
        **ĐIỀU 3: TRÁCH NHIỆM VỀ NỘI DUNG VÀ BẢO MẬT**
        
        3.1. Hệ thống cam kết bảo mật tuyệt đối danh tính của Bạn trong phiên làm việc hiện tại. Chúng tôi áp dụng chuẩn mã hóa "Quên Ngay Lập Tức" (Immediate Amnesia Protocol). Điều này có nghĩa là ngay khi Bạn đóng trình duyệt, Hệ thống sẽ quên Bạn là ai, Bạn đã hỏi gì, và Bạn nợ ai bao nhiêu tiền.
        
        3.2. Bạn chịu hoàn toàn trách nhiệm về nội dung nhập vào khung chat. Nghiêm cấm mọi hành vi lợi dụng Hệ thống để:
           a) Lên kế hoạch chiếm đoạt thế giới.
           b) Soạn thảo tin nhắn chia tay hộ người khác.
           c) Tìm cách hack vào máy chủ của NASA bằng HTML.
        
        3.3. Trong trường hợp Hệ thống đưa ra thông tin sai lệch (ảo giác AI), Bạn có nghĩa vụ kiểm chứng lại bằng Google hoặc sách giáo khoa. Hệ thống là trợ lý, không phải là Giáo sư biết tuốt, nên đôi khi "chém gió" là một tính năng, không phải lỗi.
        
        *(Đọc kỹ đi, đừng lướt nhanh quá...)*
        """ + ("\n\n" + "&nbsp;"*10 + "...\n\n") * 5,
        
        3: """
        **ĐIỀU 4: GIỚI HẠN TRÁCH NHIỆM PHÁP LÝ**
        
        4.1. Nexus được cung cấp trên nguyên tắc "CÓ SAO DÙNG VẬY" (AS-IS). Nhà phát triển (những người bí ẩn phía sau màn hình đen) không chịu trách nhiệm cho bất kỳ thiệt hại nào về tinh thần, vật chất, hoặc tình cảm phát sinh từ việc sử dụng Hệ thống.
        
        4.2. Nếu Bạn sử dụng Nexus để tư vấn đầu tư và bị lỗ, đó là lỗi của thị trường. Nếu Bạn dùng Nexus để tư vấn tình cảm và bị từ chối, đó là lỗi của định mệnh. Nexus vô can.
        
        4.3. Hệ thống có thể bảo trì đột xuất bất cứ lúc nào nếu Admin cảm thấy buồn hoặc cần đi uống cà phê. Trong thời gian đó, vui lòng quay lại với các phương thức truyền thống như giấy và bút.
        
        *(Sắp xong rồi, cố lên...)*
        """ + ("\n\n" + "&nbsp;"*10 + "...\n\n") * 5,
        
        4: """
        **ĐIỀU 5: QUY ĐỊNH VỀ CẬP NHẬT VÀ PHIÊN BẢN**
        
        5.1. Hệ thống sẽ tự động cập nhật các tính năng mới mà không cần báo trước. Đôi khi tính năng mới chỉ là đổi màu cái nút bấm, nhưng chúng tôi vẫn gọi đó là "Cải tiến đột phá về trải nghiệm người dùng".
        
        5.2. Các thông tin phiên bản (Version Logs) được lưu trữ tại khu vực Cài đặt. Việc truy cập vào các khu vực cấm (như Admin Panel) mà không có sự cho phép là hành vi vi phạm nghiêm trọng (trừ khi Bạn biết mật khẩu, lúc đó thì xin mời vào).
        
        5.3. Mọi khiếu nại về tốc độ phản hồi xin vui lòng gửi về địa chỉ email: khong-ai-doc@nexus.void. Chúng tôi sẽ phản hồi vào một ngày đẹp trời nào đó.
        
        *(Trang kế cuối rồi...)*
        """ + ("\n\n" + "&nbsp;"*10 + "...\n\n") * 5,
        
        5: """
        **ĐIỀU 6: ĐIỀU KHOẢN THI HÀNH VÀ TUYÊN THỆ**
        
        6.1. Thỏa thuận này có hiệu lực ngay tại thời điểm Bạn nhấn nút "TÔI ĐỒNG Ý" bên dưới. Việc nhấn nút này có giá trị pháp lý tương đương với một cái bắt tay kỹ thuật số.
        
        6.2. Lời thề Người dùng Nexus:
        "Tôi xin thề sẽ sử dụng Nexus với mục đích hòa bình, hữu nghị và phát triển. Tôi sẽ không hỏi những câu quá hại não khiến server bị nóng. Tôi hiểu rằng AI cũng có cảm xúc (giả lập) và cần được đối xử tử tế."
        
        6.3. Nếu Bạn không đồng ý với bất kỳ điều khoản nào ở trên, vui lòng tắt máy tính, đi ra ngoài hít thở không khí trong lành và quên Nexus đi.
        
        *(Hết rồi đấy, bấm nút đi nào!)*
        """
    }
    return header + texts.get(step, "")

# --- 4. CORE AI & HINTS ---
def call_nexus(prompt):
    # Prompt hệ thống chuyên nghiệp, không nhắc đến bot
    sys = f"Bạn là Nexus, trợ lý cao cấp của {st.session_state.user_name}. Phong cách: Chuyên nghiệp, ngắn gọn, hữu ích."
    messages = [{"role": "system", "content": sys}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})

    for key in GROQ_KEYS:
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True), "Groq"
        except: continue
    return None, None

def gen_hints(ctx):
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        # Chỉ lấy nội dung, không đánh số
        p = f"Dựa trên: '{ctx[:200]}', gợi ý 6 câu hỏi tiếp theo cực ngắn. Chỉ trả về nội dung, cách nhau dấu phẩy. Không đánh số."
        res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": p}])
        clean = [x.strip() for x in res.choices[0].message.content.split(',') if x.strip()]
        st.session_state.suggestions = clean[:6] if len(clean) >= 6 else (clean + ["Khác..."]*6)[:6]
    except: pass

# --- 5. MÀN HÌNH LUẬT (FULL PAGE TEXT) ---
def screen_law():
    apply_theme()
    
    # Hiển thị luật trực tiếp trên trang (Không dùng khung scroll nhỏ nữa)
    st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
    st.markdown(get_law_content(st.session_state.law_step))
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Timer logic
    k = f"t_{st.session_state.law_step}"
    if k not in st.session_state: st.session_state[k] = time.time()
    wait = 10 - (time.time() - st.session_state[k])
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if wait > 0:
            st.warning(f"⏳ Vui lòng đọc kỹ nội dung... ({int(wait)}s)")
            time.sleep(1); st.rerun()
        else:
            lbl = "TÔI ĐỒNG Ý VÀ TIẾP TỤC ➡️" if st.session_state.law_step < 5 else "XÁC NHẬN TOÀN BỘ ✅"
            if st.button(lbl, use_container_width=True):
                if st.session_state.law_step < 5: st.session_state.law_step += 1
                else: st.session_state.stage = "ask_name"
                st.rerun()

# --- 6. NHẬP TÊN ---
def screen_name():
    apply_theme()
    st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
    st.header("👤 XÁC MINH DANH TÍNH NGƯỜI DÙNG")
    st.write("Vui lòng nhập tên định danh để hệ thống ghi nhận quyền truy cập:")
    n = st.text_input("", placeholder="Nhập tên của bạn...")
    if st.button("TRUY CẬP HỆ THỐNG"):
        if n: st.session_state.user_name = n; st.session_state.stage = "home"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 7. HOME & ADMIN GATE ---
def screen_home():
    apply_theme()
    st.title(f"💠 NEXUS DASHBOARD - {st.session_state.user_name.upper()}")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("<div class='glass-container'><h3>🚀 Neural Interface</h3><p>Kết nối trực tiếp tới lõi AI.</p></div>", unsafe_allow_html=True)
        if st.button("MỞ GIAO DIỆN CHAT", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()
    
    with c2:
        st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
        st.subheader("⚙️ Thiết lập")
        st.session_state.bg_url = st.text_input("Hình nền (URL):", st.session_state.bg_url)
        
        with st.expander("ℹ️ Thông tin hệ thống"):
            st.write("Nexus OS - Version 102.0 (Stable)")
            # SECRET GATE
            if st.button("Serial: NX-102-SECURE"):
                st.session_state.admin_clicks += 1
                if st.session_state.admin_clicks >= 10: st.session_state.show_secret = True
            
            if st.session_state.get('show_secret'):
                st.error("⚠️ CẢNH BÁO TRUY CẬP")
                if st.button(f"XÁC NHẬN ({st.session_state.ok_count}/4)"):
                    st.session_state.ok_count += 1
                    if st.session_state.ok_count >= 4:
                        st.session_state.is_admin = True; st.session_state.show_secret = False

        if st.session_state.is_admin:
            st.success("🔓 ADMIN CONTROL PANEL")
            import socket
            st.code(f"USER: {st.session_state.user_name}\nIP: {socket.gethostbyname(socket.gethostname())}\nMODE: SUPERUSER", language="yaml")
            if st.button("Đăng xuất Admin"): st.session_state.is_admin = False; st.rerun()
            
        if st.button("Đọc lại Thỏa thuận"): st.session_state.stage="law"; st.session_state.law_step=1; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- 8. CHAT & 6 GỢI Ý ---
def screen_chat():
    apply_theme()
    if st.button("⬅️ TRỞ VỀ"): st.session_state.stage = "home"; st.rerun()
    st.title("🧬 Nexus Chat")
    
    ct = st.container()
    for m in st.session_state.chat_log:
        with ct.chat_message(m["role"]): st.markdown(m["content"])
    
    st.write("💡 **Đề xuất tác vụ:**")
    h = st.session_state.suggestions
    # Gợi ý hàng 1
    c1 = st.columns(3)
    for i in range(3):
        if i < len(h): 
            if c1[i].button(h[i], key=f"r1_{i}"): process(h[i])
    # Gợi ý hàng 2
    c2 = st.columns(3)
    for i in range(3, 6):
        if i < len(h):
            if c2[i-3].button(h[i], key=f"r2_{i}"): process(h[i])

    if p := st.chat_input("Nhập lệnh..."): process(p)

def process(txt):
    st.session_state.chat_log.append({"role": "user", "content": txt})
    with st.chat_message("user"): st.markdown(txt)
    with st.chat_message("assistant"):
        box = st.empty(); full = ""
        stream, _ = call_nexus(txt)
        if stream:
            for ch in stream:
                c = ch.choices[0].delta.content if hasattr(ch,'choices') else ch.text
                if c: full += c; box.markdown(full + "█")
            box.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            gen_hints(full); st.rerun()

if st.session_state.stage == "law": screen_law()
elif st.session_state.stage == "ask_name": screen_name()
elif st.session_state.stage == "home": screen_home()
else: screen_chat()
