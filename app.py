import streamlit as st
import time
from openai import OpenAI
import random

# --- 1. CẤU HÌNH HỆ THỐNG TỐI ƯU ---
st.set_page_config(page_title="NEXUS V600", layout="wide", page_icon="🧠", initial_sidebar_state="collapsed")

ADMIN_NAME = "Lê Trần Thiên Phát"
ADMIN_EMAIL = "tranthienphatle@gmail.com"

# Khởi tạo Session State
def init_state():
    defaults = {
        'stage': "law", 'chat_log': [], 'is_admin': False,
        'suggestions': ["Khám phá Nexus", "Tạo ý tưởng kinh doanh", "Viết thơ tình AI", "Giải mã giấc mơ", "Lập trình Web", "Kể chuyện cười"],
        'bg_url': "https://images.unsplash.com/photo-1614850523296-d8c1af93d400?q=80&w=2070",
        'ai_mode': "Thông thái", 'thinking': False
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

init_state()
GROQ_KEYS = st.secrets.get("GROQ_KEYS", ["gsk_vM6MhIq9hY8N1D0b2k5bWGdyb3FYM3J8S9k9q9q9q9q9q9q9q9q"]) # Thay key của bạn vào đây

# --- 2. GIAO DIỆN CYBER-GLASS ---
def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;600&display=swap');
    * {{ font-family: 'Lexend', sans-serif; }}

    .stApp {{
        background: linear-gradient(135deg, rgba(10,10,15,0.95), rgba(20,20,35,0.9)), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}

    /* Khung Điều khoản - Hiệu ứng trượt Laptop cực mượt */
    .tos-container {{
        background: rgba(0, 0, 0, 0.8);
        border: 1px solid rgba(0, 242, 255, 0.3);
        border-radius: 20px;
        padding: 40px;
        height: 500px;
        overflow-y: auto;
        margin: 20px 0;
        scrollbar-width: thin;
        scrollbar-color: #00f2ff #000;
    }}
    .tos-container::-webkit-scrollbar {{ width: 8px; }}
    .tos-container::-webkit-scrollbar-thumb {{ background: #00f2ff; border-radius: 10px; }}

    .tos-text h1, .tos-text h2 {{ color: #00f2ff !important; font-weight: 600; }}
    .tos-text p, .tos-text li {{ color: #ffffff !important; line-height: 1.8; font-size: 1.1rem; }}

    /* Chat Styling */
    div[data-testid="stChatMessage"] {{
        background: rgba(255, 255, 255, 0.03);
        border-radius: 15px; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.1);
    }}
    .stMarkdown p {{ color: white !important; }}

    /* Suggestion Buttons - Fix Layout */
    .suggestion-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 10px; margin-top: 15px;
    }}
    
    div.stButton > button {{
        background: rgba(0, 242, 255, 0.1);
        color: #00f2ff; border: 1px solid rgba(0, 242, 255, 0.4);
        border-radius: 12px; height: auto; transition: 0.3s;
        padding: 10px; width: 100%;
    }}
    div.stButton > button:hover {{
        background: #00f2ff; color: #000; transform: translateY(-2px);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. ĐIỀU KHOẢN "DÀI & HÀI" ---
def get_funny_tos():
    return f"""
    <div class="tos-text">
        <h1>📜 HIẾP ƯỚC NEXUS - BẢN FULL KHÔNG CHE</h1>
        <p>Chào mừng bạn đã gia nhập hệ sinh thái của <b>{ADMIN_NAME}</b>. Trước khi bắt đầu, hãy hít một hơi thật sâu và đọc đống chữ này.</p>
        
        <h2>CHƯƠNG 1: QUYỀN LỢI VÀ SỰ ĐẸP TRAI</h2>
        <p>1.1. Bạn có quyền sử dụng AI này để làm bài tập, viết mail cho sếp, hoặc thậm chí là nhờ nó tư vấn cách tỏ tình. Nhưng nếu bị từ chối, Admin <b>{ADMIN_NAME}</b> không chịu trách nhiệm.</p>
        <p>1.2. Mọi câu trả lời của AI đều mang tính tham khảo. Nếu AI bảo bạn đi cầu hôn một cái cột điện, vui lòng dùng não để lọc thông tin.</p>
        <p>1.3. Bạn thừa nhận rằng giao diện này trông rất ngầu, và người tạo ra nó (là Phát đấy) xứng đáng được nhận một lời khen thầm lặng trong lòng bạn.</p>
        
        <h2>CHƯƠNG 2: BẢO MẬT VÀ LINH HỒN</h2>
        <p>2.1. Chúng tôi không lưu trữ dữ liệu của bạn, đơn giản vì server của Admin không đủ tiền mua thêm ổ cứng. Mọi bí mật của bạn sẽ tan biến khi bạn F5.</p>
        <p>2.2. Email liên hệ <b>{ADMIN_EMAIL}</b> chỉ dùng để hỗ trợ kỹ thuật. Vui lòng không gửi mail hỏi "Tối nay ăn gì?".</p>
        
        <h2>CHƯƠNG 3: CẤM ĐOÁN VÀ TRỪNG PHẠT</h2>
        <p>3.1. Nghiêm cấm hỏi AI các câu hỏi như: "Ai là người đẹp trai nhất thế giới?". Câu trả lời luôn là <b>{ADMIN_NAME}</b>, hỏi chi cho tốn token.</p>
        <p>3.2. Nếu bạn cố tình tìm cách hack hệ thống này, AI sẽ tự động chuyển sang chế độ "Nghiệp quật" và trả lời mọi câu hỏi của bạn bằng ngôn ngữ của người ngoài hành tinh.</p>
        
        <h2>CHƯƠNG 4: HIỆU NĂNG VÀ CÀ PHÊ</h2>
        <p>4.1. Hệ thống chạy bằng thuật toán và sự tâm huyết. Đôi khi nó chạy chậm là vì Admin đang bận đi uống trà sữa, hãy kiên nhẫn.</p>
        <p>4.2. Bạn cam kết không cảm thấy buồn ngủ khi đọc đến dòng này. Nếu đã đọc đến đây, bạn chính là người dùng ưu tú nhất của Nexus.</p>
        
        <h2>CHƯƠNG 5: CHẤP THUẬN CƯỚNG ÉP</h2>
        <p>5.1. Bằng việc bấm nút "Xác nhận", bạn chính thức trở thành một phần của cộng đồng Nexus. Chúc bạn một ngày tốt lành và không bị AI cà khịa.</p>
        <p>--- KÝ TÊN: {ADMIN_NAME} ---</p>
    </div>
    """

# --- 4. HÀM XỬ LÝ AI TIẾN TIẾN ---
def get_ai_response(prompt):
    modes = {
        "Thông thái": "Bạn là Nexus, một bậc thầy kiến thức súc tích.",
        "Hài hước": "Bạn là Nexus, trợ lý AI vui tính, hay pha trò và hơi lầy lội.",
        "Chuyên gia": "Bạn là Nexus, chuyên gia tư vấn kỹ thuật và logic cao cấp."
    }
    system_msg = f"{modes[st.session_state.ai_mode]} Chủ nhân của bạn là {ADMIN_NAME}. Trả lời bằng Markdown sạch sẽ."
    
    messages = [{"role": "system", "content": system_msg}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})

    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)
    except:
        return None

def update_suggestions_dynamic(last_reply):
    # Tạo gợi ý thông minh dựa trên context
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        p = f"Dựa trên câu trả lời: '{last_reply[:200]}', hãy đưa ra 6 gợi ý tiếp theo cực hay và ngắn (2-3 từ). Ngăn cách bằng dấu phẩy."
        res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": p}])
        hints = [h.strip() for h in res.choices[0].message.content.split(',') if h.strip()]
        if len(hints) >= 6: st.session_state.suggestions = hints[:6]
    except:
        pass

# --- 5. GIAO DIỆN CHÍNH ---

def screen_law():
    apply_theme()
    st.title("🛡️ NEXUS CORE PROTOCOL")
    st.markdown(f'<div class="tos-container">{get_funny_tos()}</div>', unsafe_allow_html=True)
    if st.button("XÁC NHẬN VÀ TRUY CẬP VŨ TRỤ SỐ 🚀", use_container_width=True):
        st.session_state.stage = "home"; st.rerun()

def screen_home():
    apply_theme()
    st.title(f"💠 NEXUS COMMAND")
    st.write(f"Nhà phát triển: **{ADMIN_NAME}** | Phiên bản: **V600.0**")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""
        <div style='background:rgba(0,242,255,0.05); padding:30px; border-radius:20px; border:1px solid #00f2ff;'>
            <h2>Hệ thống đã sẵn sàng</h2>
            <p>Chào mừng {ADMIN_NAME}, hôm nay bạn muốn AI làm gì?</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("BẮT ĐẦU TRÒ CHUYỆN 🧠", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()
            
    with col2:
        st.session_state.ai_mode = st.selectbox("🎯 Chế độ AI:", ["Thông thái", "Hài hước", "Chuyên gia"])
        st.session_state.bg_url = st.text_input("🖼️ Đổi hình nền (URL):", st.session_state.bg_url)
        if st.button("Xóa lịch sử Chat"): st.session_state.chat_log = []; st.success("Đã dọn dẹp!")

def screen_chat():
    apply_theme()
    if st.button("⬅️ DASHBOARD"): st.session_state.stage = "home"; st.rerun()
    
    # Khu vực chat hiển thị mượt mà
    chat_container = st.container()
    for m in st.session_state.chat_log:
        with chat_container.chat_message(m["role"]):
            st.markdown(m["content"])

    # Phân tách gợi ý và Input
    st.markdown("---")
    
    # FIX: Hiển thị gợi ý dạng Grid để không bị lỗi layout
    st.caption(f"✨ Gợi ý từ Nexus ({st.session_state.ai_mode} mode):")
    cols = st.columns(3)
    for i in range(6):
        with cols[i % 3]:
            if st.button(st.session_state.suggestions[i], key=f"sug_{i}", use_container_width=True):
                process_msg(st.session_state.suggestions[i])

    if prompt := st.chat_input("Gửi thông điệp..."):
        process_msg(prompt)

def process_msg(prompt):
    st.session_state.chat_log.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        box = st.empty(); full = ""
        stream = get_ai_response(prompt)
        if stream:
            for chunk in stream:
                c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                if c: 
                    full += c
                    box.markdown(full + "█")
            box.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            update_suggestions_dynamic(full)
            st.rerun()

# --- MAIN ROUTER ---
if st.session_state.stage == "law": screen_law()
elif st.session_state.stage == "home": screen_home()
else: screen_chat()
