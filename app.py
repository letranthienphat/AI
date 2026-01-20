import streamlit as st
import time
import json
import random
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai
import streamlit.components.v1 as components

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="NEXUS V80.0 - SIÊU TRỢ LÝ", layout="wide", page_icon="🌐")

# Lấy API Keys từ Secrets (Phải cài trong Streamlit Cloud)
GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# Khởi tạo bộ nhớ (Session State)
if 'stage' not in st.session_state: st.session_state.stage = "law"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'bg_url' not in st.session_state: st.session_state.bg_url = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=2070"
if 'suggestions' not in st.session_state: st.session_state.suggestions = ["Chào Nexus!", "Bạn làm được gì?", "Kể chuyện cười đi"]

# --- 2. GIAO DIỆN SIÊU TƯƠNG PHẢN (CSS) ---
def apply_ui_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;500;800&display=swap');
    * {{ font-family: 'Lexend', sans-serif; }}
    
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.9)), url("{st.session_state.bg_url}");
        background-size: cover; background-attachment: fixed;
    }}

    /* Card Kính mờ siêu đặc */
    .glass-card {{
        background: rgba(13, 17, 23, 0.98);
        border: 2px solid #00f2ff;
        border-radius: 20px; padding: 30px;
        box-shadow: 0 0 50px rgba(0,242,255,0.2);
        color: white;
    }}

    /* Khung Chat Trắng Sáng trên nền tối */
    div[data-testid="stChatMessage"] {{
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid #00f2ff33 !important;
        border-radius: 15px !important;
        margin-bottom: 15px;
    }}
    .stMarkdown p {{ color: #ffffff !important; font-size: 1.1rem; }}

    /* Nút gợi ý động */
    .hint-btn {{
        background: #00f2ff; color: #000 !important;
        border-radius: 50px; padding: 8px 20px;
        font-weight: bold; border: none; cursor: pointer;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. KẾT NỐI API THẬT (THE BRAIN) ---
def call_ai_api(user_input):
    # Gửi TOÀN BỘ lịch sử để có trí nhớ vĩnh cửu
    messages = [{"role": "system", "content": "Bạn là Nexus, một siêu trợ lý ảo thân thiện, dùng ngôn ngữ bình dân, thông minh và hài hước."}]
    for m in st.session_state.chat_log:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_input})

    # Lần lượt thử các Node Groq
    for i, key in enumerate(GROQ_KEYS):
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(
                model="llama-3.3-70b-versatile", messages=messages, stream=True
            ), f"Groq Node {i+1}"
        except: continue

    # Nếu Groq chết, dùng Gemini
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        gem_hist = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in messages[1:-1]]
        chat = model.start_chat(history=gem_hist)
        return chat.send_message(user_input, stream=True), "Gemini Ultra"
    except: return None, None

def generate_dynamic_suggestions(text):
    """AI tự đẻ ra 3 câu hỏi gợi ý"""
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        prompt = f"Dựa vào câu này: '{text[:200]}', gợi ý 3 câu hỏi ngắn (dưới 7 từ) để người dùng hỏi tiếp. Chỉ trả về các câu hỏi cách nhau bởi dấu phẩy."
        res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
        return [s.strip() for s in res.choices[0].message.content.split(',')]
    except: return ["Kể tiếp đi", "Giải thích rõ hơn", "Chốt vấn đề nào"]

# --- 4. CÁC MÀN HÌNH CHÍNH ---

def show_law_screen():
    apply_ui_theme()
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container():
        st.markdown(f"""
        <div class='glass-card'>
            <h1 style='color:#00f2ff; text-align:center;'>⚖️ BỘ LUẬT NGƯỜI DÙNG NEXUS OS</h1>
            <p style='text-align:center;'>Phiên bản 80.0 | Ngày hiệu lực: {datetime.now().strftime('%d/%m/%Y')}</p>
            <hr>
            <h4>ĐIỀU 1: CHẤP THUẬN QUYỀN LỢI</h4>
            <p>Người dùng khi nhấn nút "Chấp nhận" sẽ được cấp quyền truy cập vào lõi AI mạnh nhất thế giới hiện nay.</p>
            <h4>ĐIỀU 2: TRÍ NHỚ VĨNH CỬU</h4>
            <p>Hệ thống có quyền ghi nhớ mọi lời bạn nói để phục vụ bạn tốt hơn. Chúng tôi gọi đó là "Trí nhớ vĩnh cửu".</p>
            <h4>ĐIỀU 3: CẤM HÀNH VI "TROLL" AI</h4>
            <p>Mọi hành vi hỏi xoáy đáp xoay quá mức sẽ khiến AI trả lời một cách cực kỳ lầy lội.</p>
            <h4>ĐIỀU 4: HÌNH NỀN TỰ CHỌN</h4>
            <p>Bạn có quyền đổi hình nền bằng URL. Nếu hình nền quá xấu, đó là lỗi của bạn, không phải lỗi hệ thống.</p>
            <p style='color:#888;'><i>Bằng việc tiếp tục, bạn đồng ý với mọi điều khoản trên mà không có quyền khiếu nại.</i></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("TÔI ĐÃ ĐỌC VÀ CHỐT LUÔN!", use_container_width=True):
            st.session_state.stage = "home"; st.rerun()

def show_home_screen():
    apply_ui_theme()
    st.title("🌐 NEXUS CENTRAL HUB")
    st.write("Chào mừng bạn đã gia nhập hàng ngũ người dùng đẳng cấp!")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("<div class='glass-card'><h3>🤖 Trò chuyện cùng Siêu AI</h3><p>Hỏi bất cứ thứ gì trên đời, từ việc đại sự đến việc nấu ăn.</p></div>", unsafe_allow_html=True)
        if st.button("MỞ PHÒNG CHAT NGAY 🚀", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()

    with c2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("⚙️ Cài đặt nhanh")
        st.session_state.bg_url = st.text_input("🖼️ Link hình nền mới:", st.session_state.bg_url)
        if st.button("Đọc lại Bộ luật"): st.session_state.stage = "law"; st.rerun()
        st.info("Trạng thái: Đã kết nối API thật ✅")
        st.markdown("</div>", unsafe_allow_html=True)

def show_chat_screen():
    apply_ui_theme()
    if st.button("⬅️ VỀ TRANG CHỦ"): st.session_state.stage = "home"; st.rerun()
    
    st.title("🧬 Nexus Neural Interface")
    
    # Hiển thị lịch sử
    chat_box = st.container()
    for m in st.session_state.chat_log:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    # GỢI Ý ĐỘNG (Dạng Icon Clickable)
    st.write("💡 **Gợi ý cho bạn:**")
    cols = st.columns(len(st.session_state.suggestions))
    for i, s in enumerate(st.session_state.suggestions):
        if cols[i].button(f"✨ {s}", key=f"sug_{i}"):
            process_input(s)

    # Nhập liệu
    if prompt := st.chat_input("Hỏi gì cũng được nè..."):
        process_input(prompt)

def process_input(prompt):
    st.session_state.chat_log.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        stream, node = call_ai_api(prompt)
        
        if stream:
            # JavaScript Tự động cuộn mượt mà
            components.html("<script>window.parent.document.querySelector('.main').scrollTo(0,1000000);</script>", height=0)
            
            for chunk in stream:
                content = chunk.choices[0].delta.content if "Groq" in node else chunk.text
                if content:
                    full_res += content
                    placeholder.markdown(full_res + "█")
            
            placeholder.markdown(full_res)
            st.caption(f"✅ Đã xử lý bởi: {node}")
            st.session_state.chat_log.append({"role": "assistant", "content": full_res})
            
            # Cập nhật gợi ý động mới
            st.session_state.suggestions = generate_dynamic_suggestions(full_res)
            st.rerun()
        else:
            st.error("Lỗi API rồi anh em ơi! Kiểm tra lại Key nhé.")

# --- 5. ĐIỀU HƯỚNG ---
if st.session_state.stage == "law": show_law_screen()
elif st.session_state.stage == "home": show_home_screen()
else: show_chat_screen()
