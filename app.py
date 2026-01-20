import streamlit as st
import os
import json
import time
import psutil
import random
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai

# --- 1. HỆ THỐNG QUẢN LÝ CẤU HÌNH & BẢO MẬT ---
st.set_page_config(page_title="NEXUS V62.0 ARCHIVE", layout="wide", page_icon="💾")

# Kiểm tra API Keys từ Secrets
try:
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    GEMINI_KEY = st.secrets["GEMINI_KEY"]
except Exception as e:
    st.error("❌ CẤU HÌNH THIẾU: Vui lòng kiểm tra mục Secrets trên Streamlit Cloud.")
    st.stop()

# --- 2. KHỞI TẠO BỘ NHỚ VĨNH CỬU (SESSION STATE) ---
if 'chat_sessions' not in st.session_state: st.session_state.chat_sessions = {}
if 'current_session_id' not in st.session_state: st.session_state.current_session_id = "Default_Node"
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'session_name' not in st.session_state: st.session_state.session_name = "Cuộc hội thoại mới"
if 'terminal_logs' not in st.session_state: st.session_state.terminal_logs = []

# --- 3. GIAO DIỆN TERMINAL ĐỘC QUYỀN (CSS) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Source+Code+Pro:wght@300;500&display=swap');
    
    body {{ background-color: #050505; color: #00f2ff; }}
    .stApp {{
        background: radial-gradient(circle at 50% 50%, #0a1118 0%, #000000 100%);
    }}
    
    /* Khung Chat High-Contrast */
    [data-testid="stChatMessage"] {{
        background: rgba(0, 20, 30, 0.8) !important;
        border: 1px solid #00f2ff33;
        border-radius: 10px !important;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.1);
        color: white !important;
    }}
    
    /* Chữ Neon */
    h1, h2, h3 {{
        font-family: 'Orbitron', sans-serif;
        color: #00f2ff !important;
        text-shadow: 0 0 10px #00f2ff;
    }}
    
    .stMarkdown p {{
        font-family: 'Source Code Pro', monospace;
        color: #e0faff !important;
        font-size: 1.05rem;
    }}

    /* Sidebar Matrix Effect */
    [data-testid="stSidebar"] {{
        background: rgba(0, 10, 15, 0.95) !important;
        border-right: 1px solid #00f2ff55;
    }}

    /* Custom Scrollbar */
    ::-webkit-scrollbar {{ width: 5px; }}
    ::-webkit-scrollbar-thumb {{ background: #00f2ff; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. LÕI XỬ LÝ AI & QUẢN LÝ LUỒNG (ROUTING) ---
def log_sys(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.terminal_logs.append(f"> [{ts}] {msg}")

def auto_generate_name(history):
    """AI tự động đặt tên cuộc hội thoại dựa trên bối cảnh"""
    if len(history) == 2: # Sau câu hỏi và trả lời đầu tiên
        try:
            client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
            prompt = f"Đặt 1 tiêu đề ngắn gọn (dưới 5 từ) cho nội dung này: {history[0]['content']}"
            res = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}]
            )
            st.session_state.session_name = res.choices[0].message.content.replace('"', '')
            log_sys(f"Session renamed to: {st.session_state.session_name}")
        except: pass

def get_neural_response(user_input, model_selection):
    # ĐÓNG GÓI TOÀN BỘ LUỒNG HỘI THOẠI (Trí nhớ vĩnh cửu)
    messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log]
    messages.append({"role": "user", "content": user_input})
    
    # 1. CHIẾN THUẬT QUÉT GROQ (1->2->3->4)
    key_pool = list(GROQ_KEYS)
    if "Groq" in model_selection:
        target_idx = int(model_selection.split(" ")[-1]) - 1
        key_pool.insert(0, key_pool.pop(target_idx)) # Ưu tiên key được chọn

    for i, key in enumerate(key_pool):
        try:
            log_sys(f"Đang gọi Neural Node: Groq-{i+1}...")
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages, # Gửi toàn bộ context
                stream=True
            ), f"Groq Node {i+1}"
        except:
            log_sys(f"Node-{i+1} quá tải, đang nhảy tầng...")
            continue

    # 2. DỰ PHÒNG GEMINI
    try:
        log_sys("Kích hoạt vệ tinh dự phòng Gemini...")
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Chuyển đổi context cho Gemini
        gem_hist = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in messages[:-1]]
        chat = model.start_chat(history=gem_hist)
        return chat.send_message(user_input, stream=True), "Gemini Ultra"
    except Exception as e:
        log_sys(f"Lỗi nghiêm trọng: {str(e)}")
        return None, None

# --- 5. HỆ THỐNG LƯU TRỮ VÀ QUẢN LÝ PHIÊN ---
def save_chat_to_server():
    """Ghi dữ liệu vào session_state (Mô phỏng server trên Cloud)"""
    session_id = st.session_state.current_session_id
    st.session_state.chat_sessions[session_id] = {
        "name": st.session_state.session_name,
        "log": st.session_state.chat_log,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    # Gợi ý: Để lưu vĩnh viễn trên máy chủ thật, bạn có thể dùng requests gửi đến một Webhook/DB ở đây.
    log_sys("Dữ liệu đã được đồng bộ vào Database.")

# --- 6. GIAO DIỆN ĐIỀU KHIỂN CHÍNH (OMNI DASHBOARD) ---
def main():
    # SIDEBAR: CƠ QUAN LƯU TRỮ
    with st.sidebar:
        st.title("💠 NEXUS ARCHIVE")
        st.write(f"📡 Status: **Active**")
        
        st.divider()
        st.subheader("📁 Danh sách hội thoại")
        # Quản lý phiên làm việc
        if st.button("+ Tạo hội thoại mới"):
            st.session_state.current_session_id = f"Node_{random.randint(100,999)}"
            st.session_state.chat_log = []
            st.session_state.session_name = "Cuộc hội thoại mới"
            st.rerun()

        for sid, data in st.session_state.chat_sessions.items():
            if st.sidebar.button(f"📄 {data['name']}", key=sid):
                st.session_state.current_session_id = sid
                st.session_state.chat_log = data['log']
                st.session_state.session_name = data['name']
                st.rerun()

        st.divider()
        # Monitor
        st.write("📊 Tài nguyên Node")
        st.caption(f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%")
        
        # Chọn Bot
        st.session_state.target_ai = st.selectbox("🎯 AI Target:", ["Auto-Route", "Groq 1", "Groq 2", "Groq 3", "Gemini"])

    # MÀN HÌNH CHÍNH
    st.title(f"🚀 {st.session_state.session_name}")
    st.caption(f"ID Phiên: `{st.session_state.current_session_id}` | Trí nhớ: `{len(st.session_state.chat_log)} nodes`")

    tab_chat, tab_log, tab_raw = st.tabs(["💬 Giao diện Neural", "📜 Nhật ký Kernel", "💾 Dữ liệu thô"])

    with tab_chat:
        # Hiển thị lịch sử
        for msg in st.session_state.chat_log:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Input điều khiển
        if prompt := st.chat_input("Gõ lệnh điều khiển Nexus..."):
            st.session_state.chat_log.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                res, source = get_neural_response(prompt, st.session_state.target_ai)
                if res:
                    full_res = ""
                    placeholder = st.empty()
                    for chunk in res:
                        content = chunk.choices[0].delta.content if "Groq" in source else chunk.text
                        if content:
                            full_res += content
                            placeholder.markdown(full_res + "█")
                    placeholder.markdown(full_res)
                    st.session_state.chat_log.append({"role": "assistant", "content": full_res})
                    
                    # Tự động hóa sau khi phản hồi
                    auto_generate_name(st.session_state.chat_log)
                    save_chat_to_server()
                    st.rerun()

    with tab_log:
        st.code("\n".join(st.session_state.terminal_logs[::-1]), language="bash")

    with tab_raw:
        st.subheader("📦 Xuất dữ liệu hội thoại")
        json_data = json.dumps(st.session_state.chat_log, indent=2, ensure_ascii=False)
        st.download_button("Tải xuống JSON lịch sử", json_data, file_name=f"{st.session_state.session_name}.json")
        st.json(st.session_state.chat_log)

if __name__ == "__main__":
    main()
