import streamlit as st
import time
import psutil
import json
import random
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai
import streamlit.components.v1 as components

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="NEXUS V65.0 - SMOOTH", layout="wide", page_icon="🧬")

# Lấy Keys từ Secrets
GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# Khởi tạo Session State
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'session_id' not in st.session_state: st.session_state.session_id = f"SES_{int(time.time())}"
if 'auto_scroll' not in st.session_state: st.session_state.auto_scroll = True

# --- 2. JAVASCRIPT: TỰ ĐỘNG CUỘN THEO TỐC ĐỘ ĐỌC ---
def inject_auto_scroll():
    # JavaScript này tìm container chứa chat và cuộn dần dần
    components.html(
        """
        <script>
        var scrollInterval;
        function startAutoScroll() {
            scrollInterval = setInterval(function() {
                window.scrollTo({
                    top: document.body.scrollHeight,
                    behavior: 'smooth'
                });
            }, 500); // Mỗi 0.5 giây kiểm tra và cuộn nhẹ
        }
        startAutoScroll();
        </script>
        """,
        height=0,
    )

# --- 3. GIAO DIỆN CYBER TERMINAL (CSS FIX NHẢY KHUNG) ---
st.markdown(f"""
    <style>
    /* Chống nhảy khung chat khi AI đang stream */
    .stChatFloatingInputContainer {{
        background-color: rgba(10, 15, 20, 0.95) !important;
        border-top: 1px solid #00f2ff55 !important;
        padding-bottom: 20px !important;
    }}
    
    .stApp {{
        background: #05070a;
        color: #e0faff;
    }}

    /* Khung chat cố định */
    [data-testid="stChatMessage"] {{
        background: rgba(15, 25, 35, 0.8) !important;
        border-radius: 8px !important;
        border: 1px solid #1e293b !important;
        margin-bottom: 1rem;
    }}

    /* Widget thời gian thực */
    .stat-box {{
        padding: 15px;
        background: rgba(0, 242, 255, 0.05);
        border-left: 3px solid #00f2ff;
        border-radius: 4px;
        margin-bottom: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. HÀM XỬ LÝ DỮ LIỆU & AI ---
def get_hardware_status():
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "time": datetime.now().strftime("%H:%M:%S")
    }

def call_ai_engine(prompt, model_choice):
    # Đóng gói TOÀN BỘ lịch sử (Memory vĩnh cửu)
    full_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log]
    full_history.append({"role": "user", "content": prompt})

    # Logic Routing 1->2->3->4->Gemini
    key_pool = list(GROQ_KEYS)
    if "Groq" in model_choice:
        idx = int(model_choice.split(" ")[-1]) - 1
        key_pool.insert(0, key_pool.pop(idx))

    for i, key in enumerate(key_pool):
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=full_history,
                stream=True
            ), f"Groq Node {i+1}"
        except:
            continue

    # Backup Gemini
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        gem_hist = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in full_history[:-1]]
        chat = model.start_chat(history=gem_hist)
        return chat.send_message(prompt, stream=True), "Gemini Ultra"
    except:
        return None, None

# --- 5. GIAO DIỆN CHÍNH ---
def main():
    # SIDEBAR: MONITORING THỜI GIAN THỰC
    with st.sidebar:
        st.title("💠 NEXUS CORE")
        st.markdown("---")
        
        # Monitor Hardware Real-time
        stats = get_hardware_status()
        st.markdown(f"""
        <div class="stat-box">
            <b>SYSTEM MONITOR</b><br>
            CPU: <span style="color:#00f2ff">{stats['cpu']}%</span><br>
            RAM: <span style="color:#00f2ff">{stats['ram']}%</span><br>
            Update: {stats['time']}
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        # Bộ điều phối luồng
        st.subheader("🤖 AI Dispatcher")
        model_selection = st.selectbox("Chọn đích đến:", ["Auto-Route", "Groq 1", "Groq 2", "Groq 3", "Gemini"])
        
        if st.button("🔴 PURGE MEMORY"):
            st.session_state.chat_log = []
            st.rerun()

    # MAIN INTERFACE
    st.title("🧬 Neural Interface")
    st.caption(f"Session ID: `{st.session_state.session_id}` | Trí nhớ vĩnh cửu đang hoạt động.")

    # Container hiển thị chat
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.chat_log:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Xử lý nhập liệu (Được đặt ở đáy và cố định)
    if prompt := st.chat_input("Nhập lệnh điều khiển..."):
        # 1. Lưu tin nhắn người dùng
        st.session_state.chat_log.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # 2. Phản hồi AI
        with chat_container:
            with st.chat_message("assistant"):
                # Kích hoạt tự động cuộn
                if st.session_state.auto_scroll:
                    inject_auto_scroll()
                
                res_box = st.empty()
                full_res = ""
                stream, source = call_ai_engine(prompt, model_selection)
                
                if stream:
                    for chunk in stream:
                        content = chunk.choices[0].delta.content if "Groq" in source else chunk.text
                        if content:
                            full_res += content
                            # Hiển thị mượt mà không làm nhảy thanh chat
                            res_box.markdown(full_res + "█")
                    
                    res_box.markdown(full_res)
                    st.caption(f"⚡ Luồng dữ liệu: {source}")
                    st.session_state.chat_log.append({"role": "assistant", "content": full_res})
                    
                    # Lưu vào bộ nhớ giả lập máy chủ (JSON)
                    with open(f"{st.session_state.session_id}.json", "w") as f:
                        json.dump(st.session_state.chat_log, f)
                else:
                    st.error("Hệ thống mất kết nối hoàn toàn.")

if __name__ == "__main__":
    main()
