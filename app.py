import streamlit as st
import time
import json
import random
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai

# --- 1. CẤU HÌNH & TRẠNG THÁI BÍ MẬT ---
st.set_page_config(page_title="NEXUS V85.0 - PRESTIGE", layout="wide", page_icon="🗝️")

# Khởi tạo bộ não
states = {
    'stage': "law", 'chat_log': [], 'bg_url': "https://images.unsplash.com/photo-1510511459019-5dee997dd1db?q=80&w=2070",
    'suggestions': ["Chào đại ca!", "Có gì hot không?", "Giải trí chút đi"],
    'admin_clicks': 0, 'admin_ok_count': 0, 'is_admin': False, 'show_secret_popup': False
}
for key, val in states.items():
    if key not in st.session_state: st.session_state[key] = val

GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# --- 2. GIAO DIỆN SIÊU TƯƠNG PHẢN ---
def apply_ui():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;700&display=swap');
    * {{ font-family: 'Lexend', sans-serif; }}
    .stApp {{ background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.9)), url("{st.session_state.bg_url}"); background-size: cover; }}
    .glass {{ background: rgba(13, 17, 23, 0.98); border: 2px solid #00f2ff; border-radius: 20px; padding: 25px; color: white; }}
    .law-box {{ height: 400px; overflow-y: scroll; background: rgba(0,0,0,0.5); padding: 20px; border: 1px solid #333; border-radius: 10px; line-height: 1.8; }}
    /* Tách biệt các nút gợi ý */
    .stButton>button {{ width: 100%; border-radius: 10px; border: 1px solid #00f2ff33; transition: 0.3s; }}
    .stButton>button:hover {{ border-color: #00f2ff; box-shadow: 0 0 10px #00f2ff; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. KẾT NỐI API THẬT ---
def call_nexus_ai(prompt):
    messages = [{"role": "system", "content": "Bạn là Nexus, siêu trợ lý bình dân, hài hước, xưng mình và gọi người dùng là bạn hoặc đại ca."}]
    messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log])
    messages.append({"role": "user", "content": prompt})

    for i, key in enumerate(GROQ_KEYS):
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True), f"Core-{i+1}"
        except: continue
    try:
        genai.configure(api_key=GEMINI_KEY); model = genai.GenerativeModel('gemini-1.5-flash')
        chat = model.start_chat(history=[{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in messages[1:-1]])
        return chat.send_message(prompt, stream=True), "Core-Gemini"
    except: return None, None

def update_hints(text):
    try:
        client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role":"user","content":f"Gợi ý 3 câu hỏi ngắn từ: {text[:100]}. Chỉ trả về 3 câu cách nhau dấu phẩy."}])
        st.session_state.suggestions = [s.strip() for s in res.choices[0].message.content.split(',')]
    except: pass

# --- 4. MÀN HÌNH ĐIỀU KHOẢN (BỘ LUẬT "HÌNH SỰ") ---
def show_law():
    apply_ui()
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.header("📜 BỘ LUẬT SỬ DỤNG NEXUS OS - V85.0")
    st.write(f"Cập nhật: {datetime.now().strftime('%d/%m/%Y')} | Mã lưu trữ: NX-999")
    
    st.markdown("""<div class='law-box'>
    <b>ĐIỀU 1: KHỔ TẬN CAM LAI</b><br>Chào mừng bạn đến với Nexus. Việc bạn đang đọc dòng này chứng tỏ bạn là người kiên nhẫn hoặc đang rất rảnh. Nexus là AI, không phải người yêu cũ, nên sẽ không bao giờ phản bội bạn (trừ khi mất mạng).<br><br>
    <b>ĐIỀU 2: QUYỀN HẠN CỦA "NÓC"</b><br>Bạn có quyền hỏi mọi thứ. Nexus có quyền trả lời hoặc giả vờ lag nếu câu hỏi quá khó. Nếu bạn hỏi "Trưa nay ăn gì?", Nexus sẽ gợi ý món bạn thích nhất, nhưng không bao giờ trả tiền giùm.<br><br>
    <b>ĐIỀU 3: CHẾ TÀI HÌNH NỀN</b><br>Bạn được phép đổi hình nền qua URL. Tuy nhiên, nếu bạn cài hình nền làm đau mắt người nhìn, hệ thống sẽ tự động gửi một lời phê bình nhẹ nhàng vào bộ nhớ đệm.<br><br>
    <b>ĐIỀU 4: TRÍ NHỚ VÀ SỰ QUÊN LÃNG</b><br>Nexus nhớ hết những gì bạn nói trong phiên này. Nhưng nếu bạn F5 (Refresh), Nexus sẽ bị "mất trí nhớ tạm thời". Hãy coi đó là một khởi đầu mới.<br><br>
    <b>ĐIỀU 5: AN NINH QUỐC GIA</b><br>Mọi hành vi cố gắng hack vào hệ thống này sẽ được chúng tôi ghi nhận và... cười vào mặt vì code này được viết bởi một con AI khác cực kỳ bảo mật.<br><br>
    <b>ĐIỀU 6: THÔNG TIN PHIÊN BẢN</b><br>Nexus V85.0 - The Secret Gate. Tích hợp AI Routing, Dynamic Sugesstion, và một vài "trứng phục sinh" mà bạn sẽ không bao giờ tìm thấy nếu không phải là dân chuyên.<br><br>
    <i>Bạn đã cuộn hết chưa? Cuộn đi, luật còn dài lắm... (Thêm 100 dòng giả định ở đây)</i>
    </div>""", unsafe_allow_html=True)
    
    confirm = st.checkbox("Tôi thề đã đọc hết đống chữ trên và cam kết không gây gổ với AI.")
    if st.button("KÍCH HOẠT HỆ THỐNG", disabled=not confirm, use_container_width=True):
        st.session_state.stage = "home"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 5. TRANG CHỦ & CÀI ĐẶT ---
def show_home():
    apply_ui()
    st.title("🌐 TRUNG TÂM ĐIỀU HÀNH")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<div class='glass'><h3>🤖 Neural Interface</h3><p>Mở cổng giao tiếp với trợ lý Nexus.</p></div>", unsafe_allow_html=True)
        if st.button("VÀO PHÒNG CHAT 🚀", use_container_width=True):
            st.session_state.stage = "chat"; st.rerun()

    with col2:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.subheader("⚙️ Cài đặt")
        st.session_state.bg_url = st.text_input("🔗 Link hình nền:", st.session_state.bg_url)
        
        # --- EASTER EGG: ADMIN GATE ---
        version_text = f"Phiên bản: V85.0.26"
        if st.button(version_text, key="ver_btn", help="Nhấn vào đây để xem thông tin"):
            st.session_state.admin_clicks += 1
            if st.session_state.admin_clicks == 10:
                st.session_state.show_secret_popup = True
        
        if st.session_state.show_secret_popup:
            st.warning(f"Cảnh báo: Hệ thống gặp sự cố nhẹ. Nhấn OK để xác nhận ({st.session_state.admin_ok_count}/4)")
            if st.button("OK"):
                st.session_state.admin_ok_count += 1
                if st.session_state.admin_ok_count >= 4:
                    st.session_state.is_admin = True
                    st.session_state.show_secret_popup = False
                    st.balloons()
        
        if st.session_state.is_admin:
            st.success("🔓 QUYỀN ADMIN ĐÃ MỞ")
            st.code("DEBUG_MODE: ON\nTOKEN_LIMIT: UNLIMITED\nGOD_MODE: ACTIVE", language="bash")
        
        if st.button("Đọc lại Bộ luật"): st.session_state.stage = "law"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- 6. PHÒNG CHAT ---
def show_chat():
    apply_ui()
    if st.button("⬅️ THOÁT"): st.session_state.stage = "home"; st.rerun()
    
    st.title("🧬 Nexus Neural Interface")
    
    chat_box = st.container()
    for m in st.session_state.chat_log:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    # TÁCH CÁC NÚT GỢI Ý ĐỘNG
    st.write("💡 **Gợi ý nhanh:**")
    h_cols = st.columns(3)
    for i, s in enumerate(st.session_state.suggestions[:3]):
        if h_cols[i].button(f"✨ {s}", key=f"h_{i}"):
            process_msg(s)

    if p := st.chat_input("Nói gì đó với Nexus đi..."):
        process_msg(p)

def process_msg(p):
    st.session_state.chat_log.append({"role": "user", "content": p})
    with st.chat_message("user"): st.markdown(p)
    with st.chat_message("assistant"):
        placeholder = st.empty(); full_res = ""
        stream, node = call_nexus_ai(p)
        if stream:
            for chunk in stream:
                content = chunk.choices[0].delta.content if "Core" in node and "Gemini" not in node else chunk.text
                if content:
                    full_res += content; placeholder.markdown(full_res + "█")
            placeholder.markdown(full_res)
            st.session_state.chat_log.append({"role": "assistant", "content": full_res})
            update_hints(full_res)
            st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "law": show_law()
elif st.session_state.stage == "home": show_home()
else: show_chat()
