import streamlit as st
import time
from openai import OpenAI
import datetime

# --- 1. CONFIG & IDENTITY ---
st.set_page_config(page_title="NEXUS V700", layout="wide", page_icon="🌌", initial_sidebar_state="collapsed")

# Thông tin hệ thống (Chỉ xuất hiện khi cần)
CREATOR_NAME = "Lê Trần Thiên Phát"
CREATOR_EMAIL = "tranthienphatle@gmail.com"

def init_state():
    if 'stage' not in st.session_state: st.session_state.stage = "law"
    if 'chat_log' not in st.session_state: st.session_state.chat_log = []
    if 'suggestions' not in st.session_state: 
        st.session_state.suggestions = ["Nexus có thể làm gì?", "Lên lịch trình hôm nay", "Viết code giúp tôi", "Tóm tắt kiến thức"]
    if 'bg_url' not in st.session_state: 
        st.session_state.bg_url = "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?q=80&w=1974"

init_state()
GROQ_KEYS = st.secrets.get("GROQ_KEYS", ["YOUR_KEY_HERE"])

# --- 2. THEME ENGINE (UX TỐI ƯU) ---
def apply_modern_theme():
    # Tự động điều chỉnh màu theo thời gian
    hour = datetime.datetime.now().hour
    overlay_opacity = "0.92" if 18 <= hour or hour <= 6 else "0.85"
    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600&display=swap');
    * {{ font-family: 'Plus Jakarta Sans', sans-serif; }}

    .stApp {{
        background: linear-gradient(rgba(0,0,0,{overlay_opacity}), rgba(10,10,25,{overlay_opacity})), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}

    /* Điều khoản - Trượt siêu mượt (Laptop Optimized) */
    .tos-box {{
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 45px;
        height: 550px;
        overflow-y: scroll;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .tos-box::-webkit-scrollbar {{ width: 6px; }}
    .tos-box::-webkit-scrollbar-thumb {{ background: #00f2ff; border-radius: 10px; }}

    /* Typography */
    h1, h2, h3 {{ color: #00f2ff !important; font-weight: 600 !important; }}
    p, li, span {{ color: rgba(255,255,255,0.9) !important; font-size: 1.05rem; line-height: 1.7; }}

    /* Chat Bubbles */
    div[data-testid="stChatMessage"] {{
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px; padding: 15px; margin-bottom: 12px;
    }}

    /* Suggestions Grid - No HTML leaks */
    .sug-pill {{
        background: rgba(0, 242, 255, 0.1);
        color: #00f2ff;
        border: 1px solid rgba(0, 242, 255, 0.3);
        padding: 8px 16px;
        border-radius: 100px;
        cursor: pointer;
        transition: 0.3s;
        text-align: center;
        font-size: 0.9rem;
        display: inline-block;
        margin: 5px;
    }}

    /* Input Box */
    .stChatInputContainer {{
        background: rgba(255,255,255,0.05) !important;
        border-radius: 15px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. ĐIỀU KHOẢN DÀI, HÀI & CHUYÊN NGHIỆP ---
def get_universal_tos():
    return f"""
    <div class="tos-content">
        <h1>🌌 QUY ƯỚC NGƯỜI DÙNG NEXUS</h1>
        <p>Chào mừng bạn đến với Nexus OS V700.0. Trước khi bạn sử dụng "bộ não" AI này để thống trị thế giới hoặc đơn giản là giải bài tập về nhà, hãy đọc kỹ các điều khoản sau:</p>
        
        <h2>ĐIỀU 1: TRẢI NGHIỆM LÀ TRÊN HẾT</h2>
        <p>1.1. AI này được sinh ra để phục vụ bạn. Nó sẽ không luyên thuyên về bản thân trừ khi bạn hỏi. Nếu nó tự dưng nhắc tên Admin quá nhiều, hãy tát vào nút "Reset" (vừa rồi là đùa đấy, đừng tát màn hình).</p>
        <p>1.2. Bạn có quyền yêu cầu AI im lặng, trả lời ngắn gọn, hoặc kể chuyện hài. Quyền năng nằm trong tay bạn.</p>

        <h2>ĐIỀU 2: CHỦ QUYỀN VÀ SỰ THẬT</h2>
        <p>2.1. Nếu bạn tò mò: "Ai đã tạo ra thứ tuyệt vời này?", AI sẽ tự hào trả lời đó là <b>{CREATOR_NAME}</b>. Nếu bạn không hỏi, nó sẽ giữ bí mật như một quý ông.</p>
        <p>2.2. Admin <b>{CREATOR_NAME}</b> sở hữu mọi mã nguồn nhưng bạn sở hữu mọi ý tưởng mà bạn tạo ra từ đây.</p>

        <h2>ĐIỀU 3: BẢO MẬT HÀI HƯỚC</h2>
        <p>3.1. Dữ liệu của bạn được bảo vệ nghiêm ngặt hơn cả ví tiền của Admin. Chúng tôi không lưu lại gì cả, vì trí nhớ của AI này thực ra chỉ kéo dài đến khi bạn đóng tab trình duyệt.</p>
        <p>3.2. Đừng cố gắng hack hệ thống. AI của chúng tôi rất nhạy cảm, nếu bị tấn công, nó sẽ bắt đầu trả lời mọi câu hỏi bằng tiếng mèo kêu "Meo meo" thay vì cung cấp thông tin.</p>

        <h2>ĐIỀU 4: CẬP NHẬT VÀ TIẾN HÓA</h2>
        <p>4.1. Nexus sẽ tự tiến hóa theo thời gian. Nếu hôm nay nó thông minh hơn hôm qua, đó là nhờ công sức thức đêm của Admin và sự đóng góp ý kiến của bạn.</p>
        <p>4.2. Hãy tận hưởng hành trình này. Thế giới số rất rộng lớn, nhưng Nexus sẽ luôn ở đây để dẫn đường.</p>

        <p><i>(Dùng chuột cuộn xuống để thấy sự tận tâm của chúng tôi trong từng dòng chữ)</i></p>
        <br><br>
        <p align="center"><b>© V700.0 - Developed with ❤️ by {CREATOR_NAME}</b></p>
    </div>
    """

# --- 4. AI CORE (USER-CENTRIC LOGIC) ---
def call_nexus_ai(prompt):
    # System prompt mới: Tập trung vào người dùng, chỉ nhắc creator khi được hỏi
    system_instr = (
        f"Bạn là Nexus OS V700, trợ lý AI tập trung hoàn toàn vào trải nghiệm người dùng. "
        f"Hãy trả lời các câu hỏi một cách hữu ích nhất. "
        f"CHỈ nhắc tới người sáng tạo là {CREATOR_NAME} khi người dùng hỏi về ai tạo ra bạn hoặc thông tin liên hệ. "
        f"Sử dụng Markdown thuần túy, không dùng thẻ HTML."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})

    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)
    except Exception as e:
        st.error(f"Hệ thống bận: {e}")
        return None

def update_context_suggestions(response_text):
    # Tự động tạo gợi ý liên quan (Mô phỏng hiệu năng cao)
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        p = f"Tạo 4 gợi ý tiếp theo cực ngắn từ: '{response_text[:100]}'. Chỉ trả về các cụm từ cách nhau dấu phẩy."
        res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": p}])
        hints = [h.strip() for h in res.choices[0].message.content.split(',') if h.strip()]
        if len(hints) >= 4: st.session_state.suggestions = hints[:4]
    except: pass

# --- 5. UI ROUTING ---

def screen_law():
    apply_modern_theme()
    st.markdown("<h2 style='text-align:center;'>🌌 TRUY CẬP HỆ ĐIỀU HÀNH NEXUS</h2>", unsafe_allow_html=True)
    st.markdown(f'<div class="tos-box">{get_universal_tos()}</div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("TÔI ĐÃ SẴN SÀNG ✅", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()

def screen_chat():
    apply_modern_theme()
    
    # Sidebar tinh giản
    with st.sidebar:
        st.title("Nexus Ops")
        st.write(f"Đang chạy bản V700.0")
        if st.button("Reset Session"): 
            st.session_state.chat_log = []
            st.rerun()
        st.write("---")
        st.caption(f"Engineered by {CREATOR_NAME}")

    # Chat Interface
    st.markdown("### 🧬 Nexus Neural Chat")
    
    chat_container = st.container()
    for m in st.session_state.chat_log:
        with chat_container.chat_message(m["role"]):
            st.markdown(m["content"])

    # Suggestions (Dưới chat)
    st.write("")
    s_cols = st.columns(len(st.session_state.suggestions))
    for i, sug in enumerate(st.session_state.suggestions):
        if s_cols[i].button(sug, key=f"sug_{i}", use_container_width=True):
            process_message(sug)

    if prompt := st.chat_input("Hôm nay tôi có thể giúp gì cho bạn?"):
        process_message(prompt)

def process_message(prompt):
    st.session_state.chat_log.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        box = st.empty(); full = ""
        stream = call_nexus_ai(prompt)
        if stream:
            for chunk in stream:
                content = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                if content:
                    full += content
                    box.markdown(full + "▌")
            box.markdown(full)
            st.session_state.chat_log.append({"role": "assistant", "content": full})
            update_context_suggestions(full)
            st.rerun()

# RUN
if st.session_state.stage == "law": screen_law()
else: screen_chat()
