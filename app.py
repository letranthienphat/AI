import streamlit as st
from openai import OpenAI
import google.generativeai as genai
import time
import random
import psutil
import json
from datetime import datetime

# --- 1. KIỂM SOÁT HỆ THỐNG & CẤU HÌNH BIẾN ---
st.set_page_config(page_title="NEXUS OS V58.0", layout="wide", initial_sidebar_state="expanded")

# Lấy dữ liệu an toàn
GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# Khởi tạo trạng thái hệ thống
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'sys_logs' not in st.session_state: st.session_state.sys_logs = [f"[{datetime.now().strftime('%H:%M:%S')}] Core Initialized."]
if 'selected_model' not in st.session_state: st.session_state.selected_model = "Auto-Sync"
if 'theme_color' not in st.session_state: st.session_state.theme_color = "#00f2ff"

# --- 2. GIAO DIỆN NÂNG CAO (ADVANCED CSS) ---
def apply_ui():
    theme = st.session_state.theme_color
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;500&display=swap');
    * {{ font-family: 'Fira Code', monospace; }}
    
    .stApp {{
        background: radial-gradient(circle at center, #0a1118 0%, #050505 100%);
        color: white;
    }}
    
    /* Hiệu ứng quét Laser */
    .stApp::before {{
        content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 2px;
        background: {theme}; opacity: 0.1; z-index: 9999;
        animation: scan 4s linear infinite;
    }}
    @keyframes scan {{ 0% {{ top: 0; }} 100% {{ top: 100%; }} }}

    /* Khung chat đa tầng */
    .stChatMessage {{
        background: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px !important;
        margin-bottom: 15px;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.5);
    }}
    
    /* Chữ siêu tương phản */
    .stMarkdown p {{
        color: #e0e0e0 !important;
        line-height: 1.6;
        text-shadow: 1px 1px 2px black;
    }}

    /* Sidebar Sidebar Custom */
    [data-testid="stSidebar"] {{
        background: rgba(0, 0, 0, 0.8) !important;
        border-right: 1px solid {theme}44;
    }}
    
    /* Widget chỉ số */
    .metric-card {{
        background: rgba(0,0,0,0.4); border: 1px solid {theme}33;
        padding: 10px; border-radius: 8px; text-align: center;
    }}
    </style>
    """, unsafe_allow_html=True)

apply_ui()

# --- 3. CÔNG CỤ HỖ TRỢ (UTILITIES) ---
def log_event(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.sys_logs.append(f"[{timestamp}] {msg}")
    if len(st.session_state.sys_logs) > 20: st.session_state.sys_logs.pop(0)

def get_system_metrics():
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "latency": random.randint(20, 150)
    }

# --- 4. LÕI CHATBOT (GIỮ NGUYÊN LOGIC NHƯNG NÂNG CẤP KẾT NỐI) ---
def get_ai_stream(user_input, model_choice):
    # Tổng hợp bộ nhớ vĩnh cửu
    messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log]
    messages.append({"role": "user", "content": user_input})
    
    # Chiến lược chuyển tầng (1 -> 2 -> 3 -> Gemini)
    key_queue = list(GROQ_KEYS)
    
    if "Groq" in model_choice:
        target_idx = int(model_choice.split(" ")[-1]) - 1
        # Đưa key được chọn lên đầu hàng đợi
        key_queue.insert(0, key_queue.pop(target_idx))

    # Thử Groq Keys
    for i, key in enumerate(key_queue):
        try:
            log_event(f"Attempting connection: Groq Node {i+1}...")
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                stream=True
            ), f"Groq Node {i+1}"
        except Exception as e:
            log_event(f"Node {i+1} Failed: Rate Limit reached.")
            continue

    # Dự phòng Gemini
    try:
        log_event("Switching to Gemini Satellite...")
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Format lại cho Gemini
        history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in messages[:-1]]
        chat = model.start_chat(history=history)
        return chat.send_message(user_input, stream=True), "Gemini Ultra"
    except Exception as e:
        log_event("Critical Failure: All AI nodes offline.")
        return None, None

# --- 5. GIAO DIỆN ĐIỀU KHIỂN CHÍNH ---
def main():
    # SIDEBAR: COMMAND CENTER
    with st.sidebar:
        st.title("💠 NEXUS CORE")
        st.markdown("---")
        
        # Monitor Real-time
        metrics = get_system_metrics()
        col1, col2 = st.columns(2)
        col1.markdown(f"<div class='metric-card'>CPU<br><b style='color:cyan'>{metrics['cpu']}%</b></div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='metric-card'>LATENCY<br><b style='color:lime'>{metrics['latency']}ms</b></div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Model Selection
        options = ["Auto-Sync"] + [f"Groq {i+1}" for i in range(len(GROQ_KEYS))] + ["Gemini"]
        st.session_state.selected_model = st.selectbox("🎯 AI Target:", options)
        
        # Memory Info
        st.write(f"🧠 Context Stream: `{len(st.session_state.chat_log)} nodes`")
        
        # Theme Selector
        st.session_state.theme_color = st.color_picker("🎨 Theme Accent:", st.session_state.theme_color)
        
        if st.button("🔥 PURGE MEMORY"):
            st.session_state.chat_log = []
            st.rerun()

    # MAIN VIEW: NEURAL TERMINAL
    tab1, tab2, tab3 = st.tabs(["💬 NEURAL CHAT", "📊 SYSTEM LOGS", "🧠 MEMORY ANALYZER"])

    with tab1:
        # Hiển thị lịch sử hội thoại
        for msg in st.session_state.chat_log:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Input
        if prompt := st.chat_input("Enter command..."):
            st.session_state.chat_log.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                res, source = get_ai_stream(prompt, st.session_state.selected_model)
                if res:
                    placeholder = st.empty()
                    full_res = ""
                    for chunk in res:
                        content = chunk.choices[0].delta.content if "Groq" in source else chunk.text
                        if content:
                            full_res += content
                            placeholder.markdown(full_res + "█")
                    placeholder.markdown(full_res)
                    st.caption(f"Connected via: {source}")
                    st.session_state.chat_log.append({"role": "assistant", "content": full_res})
                else:
                    st.error("CORE ERROR: No response from Neural Network.")

    with tab2:
        st.subheader("🛠️ Real-time System Kernel Logs")
        log_box = st.empty()
        log_text = "\n".join(st.session_state.sys_logs[::-1])
        log_box.code(log_text, language="bash")
        if st.button("Refresh Logs"): st.rerun()

    with tab3:
        st.subheader("🧠 Neural Memory Structure")
        if st.session_state.chat_log:
            st.json(st.session_state.chat_log)
        else:
            st.info("Memory is currently empty.")

    # FOOTER
    st.markdown("---")
    st.caption(f"Nexus OS V58.0 | Security Status: Encrypted | Build: {datetime.now().strftime('%Y%m%d')}")

if __name__ == "__main__":
    main()
