import streamlit as st
import time
import json
import psutil
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai
import streamlit.components.v1 as components

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="NEXUS V68.0", layout="wide", page_icon="🎨")

# Lấy Keys từ Secrets
GROQ_KEYS = st.secrets.get("GROQ_KEYS", [])
GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")

# Khởi tạo Session State
if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'bg_url' not in st.session_state: st.session_state.bg_url = "https://images.unsplash.com/photo-1614850523296-d8c1af93d400?q=80&w=2070"
if 'auto_scroll' not in st.session_state: st.session_state.auto_scroll = True

# --- 2. GIAO DIỆN SIÊU TƯƠNG PHẢN (ULTRA CONTRAST CSS) ---
def apply_advanced_ui():
    bg = st.session_state.bg_url
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=Fira+Code&display=swap');
    
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("{bg}");
        background-size: cover;
        background-attachment: fixed;
    }}

    /* Khung chat siêu tương phản - Chữ trắng tinh trên nền đặc */
    div[data-testid="stChatMessage"] {{
        background: rgba(10, 15, 25, 0.98) !important;
        border: 2px solid #00f2ff;
        border-radius: 12px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.8);
        padding: 20px !important;
    }}
    
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2 {{
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        text-shadow: 2px 2px 4px #000000;
    }}

    /* Thanh Input cố định không nhảy */
    .stChatFloatingInputContainer {{
        background: rgba(0,0,0,0.9) !important;
        border-top: 2px solid #00f2ff !important;
        padding: 15px !important;
    }}

    /* Icon Clickable Style */
    .icon-btn {{
        display: inline-block;
        padding: 10px 20px;
        margin: 5px;
        background: rgba(0, 242, 255, 0.1);
        border: 1px solid #00f2ff;
        border-radius: 8px;
        color: #00f2ff;
        cursor: pointer;
        transition: 0.3s;
        text-decoration: none;
        font-weight: bold;
    }}
    .icon-btn:hover {{
        background: #00f2ff;
        color: #000;
        box-shadow: 0 0 20px #00f2ff;
    }}

    /* Settings Box */
    .settings-panel {{
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 20px;
        border-radius: 15px;
        backdrop-filter: blur(10px);
    }}
    </style>
    """, unsafe_allow_html=True)

apply_advanced_ui()

# --- 3. JAVASCRIPT: AUTO-SCROLL ---
def inject_auto_scroll():
    components.html(
        """<script>
        window.parent.document.querySelector(".main").scrollTo({
            top: window.parent.document.querySelector(".main").scrollHeight,
            behavior: 'smooth'
        });
        </script>""", height=0
    )

# --- 4. HÀM AI & LOGIC ---
def get_ai_response(prompt):
    # Gửi TOÀN BỘ lịch sử vĩnh cửu
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_log]
    history.append({"role": "user", "content": prompt})
    
    # Routing Groq 1-4 -> Gemini
    for i, key in enumerate(GROQ_KEYS):
        try:
            client = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
            return client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=history,
                stream=True
            ), f"Groq Node {i+1}"
        except: continue
        
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        gem_hist = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in history[:-1]]
        chat = model.start_chat(history=gem_hist)
        return chat.send_message(prompt, stream=True), "Gemini Ultra"
    except: return None, None

# --- 5. GIAO DIỆN ĐIỀU KHIỂN ---
def main():
    # SIDEBAR: DANH SÁCH PHIÊN & TRẠNG THÁI
    with st.sidebar:
        st.title("🗂️ CHỈ HUY NEXUS")
        st.info("Hệ thống đã loại bỏ Monitor RAM/CPU để tối ưu tốc độ.")
        if st.button("🗑️ XÓA BỘ NHỚ TẠM"):
            st.session_state.chat_log = []
            st.rerun()

    # MÀN HÌNH CHÍNH
    col_main, col_set = st.columns([3, 1])

    with col_set:
        st.markdown("### ⚙️ CÀI ĐẶT HỆ THỐNG")
        with st.container():
            st.markdown("<div class='settings-panel'>", unsafe_allow_html=True)
            # Tính năng đổi hình nền qua URL
            new_bg = st.text_input("🖼️ Dán URL hình nền mới:", value=st.session_state.bg_url)
            if st.button("CẬP NHẬT HÌNH NỀN"):
                st.session_state.bg_url = new_bg
                st.rerun()
            
            st.divider()
            st.markdown("**Lệnh nhanh (Click Icon):**")
            # Icon Clickable
            if st.button("🔍 Tóm tắt vụ án", use_container_width=True):
                process_chat("Hãy tóm tắt lại toàn bộ thông tin quan trọng từ đầu đến giờ.")
            if st.button("🧪 Phân tích bằng chứng", use_container_width=True):
                process_chat("Dựa trên lịch sử hội thoại, hãy phân tích các bằng chứng hiện có.")
            if st.button("🚨 Xuất báo cáo", use_container_width=True):
                process_chat("Viết một bản báo cáo tổng kết vụ án chuyên nghiệp.")
            st.markdown("</div>", unsafe_allow_html=True)

    with col_main:
        st.title("🤖 NEURAL TERMINAL")
        
        # Vùng Chat
        chat_area = st.container()
        with chat_area:
            for msg in st.session_state.chat_log:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Nhập liệu (Cố định ở đáy)
        if prompt := st.chat_input("Nhập lệnh điều khiển..."):
            process_chat(prompt)

def process_chat(prompt):
    st.session_state.chat_log.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        res_box = st.empty()
        full_res = ""
        stream, source = get_ai_response(prompt)
        
        if stream:
            if st.session_state.auto_scroll: inject_auto_scroll()
            
            for chunk in stream:
                content = chunk.choices[0].delta.content if "Groq" in source else chunk.text
                if content:
                    full_res += content
                    res_box.markdown(full_res + "█")
            
            res_box.markdown(full_res)
            st.caption(f"⚡ Node: {source} | Trí nhớ: Toàn diện")
            st.session_state.chat_log.append({"role": "assistant", "content": full_res})
            st.rerun()
        else:
            st.error("🆘 Server AI không phản hồi.")

if __name__ == "__main__":
    main()
