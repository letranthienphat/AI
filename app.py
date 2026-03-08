# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json

# --- 1. THÔNG TIN CHỦ SỞ HỮU ---
CREATOR_NAME = "Lê Trần Thiên Phát"
CREATOR_INFO = "Lớp 7A1 - Trường THCS-THPT Nguyễn Huệ"
VERSION = "V2800 - SOVEREIGN"

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

try:
    API_LIST = st.secrets.get("GROQ_KEYS", [])
    ACTIVE_KEY = API_LIST[0] if API_LIST else st.secrets.get("GROQ_KEY", "")
except:
    ACTIVE_KEY = ""

# Khởi tạo Session State
if 'users' not in st.session_state: st.session_state.users = {"admin": "123", "phat": "2026"}
if 'auth_status' not in st.session_state: st.session_state.auth_status = None
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = ""
if 'user_gender' not in st.session_state: st.session_state.user_gender = "Bạn"
if 'stage' not in st.session_state: st.session_state.stage = "AUTH"
if 'theme' not in st.session_state:
    st.session_state.theme = {"mode": "dark", "primary_color": "#00f2ff", "bg_url": ""}
if 'chat_library' not in st.session_state: st.session_state.chat_library = {}
if 'current_chat' not in st.session_state: st.session_state.current_chat = None
if 'dynamic_hints' not in st.session_state: st.session_state.dynamic_hints = ["Nexus là ai?", "Giúp tôi học tập", "Kể chuyện"]

def nav(p): st.session_state.stage = p

# --- 2. CSS ADAPTIVE & PLASMA GLOW ---
def apply_ui():
    t = st.session_state.theme
    bg = f"background-image: url('{t['bg_url']}'); background-size: cover;" if t['bg_url'] else ""
    app_bg = "#000000" if t['mode'] == "dark" else "#f7f9fc"
    txt = "#ffffff" if t['mode'] == "dark" else "#1a1a1a"
    
    st.markdown(f"""
    <style>
    .stApp {{ background: {app_bg}; {bg} background-attachment: fixed; color: {txt}; }}
    
    /* PLASMA BUTTONS */
    div.stButton > button {{
        width: 100% !important; border-radius: 12px !important;
        background: rgba(30, 30, 30, 0.8) !important; color: {txt} !important;
        border: 1px solid #333 !important; font-weight: 700 !important;
        padding: 10px !important; transition: 0.2s;
    }}
    div.stButton > button:active {{
        border-color: {t['primary_color']} !important;
        box-shadow: 0 0 20px {t['primary_color']} !important;
        transform: scale(0.97);
    }}

    /* AI CHAT BUBBLE (SNOW WHITE) */
    div[data-testid="stChatMessageAssistant"] {{
        background: #FFFFFF !important; border-radius: 15px !important;
        padding: 20px !important; border-left: 6px solid {t['primary_color']} !important;
        margin-bottom: 15px !important;
    }}
    div[data-testid="stChatMessageAssistant"] * {{ color: #000000 !important; font-weight: 500; }}
    
    /* FOOTER CREATOR */
    .creator-footer {{
        position: fixed; bottom: 10px; right: 20px; font-size: 0.8rem; color: #666;
    }}
    </style>
    <div class="creator-footer">Nexus OS V2800 | Created by {CREATOR_NAME}</div>
    """, unsafe_allow_html=True)

# --- 3. LÕI AI THÔNG MINH & GỢI Ý ĐỘNG ---
def get_nexus_response(messages):
    client = OpenAI(api_key=ACTIVE_KEY, base_url="https://api.groq.com/openai/v1")
    sys_prompt = f"""Bạn là Nexus OS, một trí tuệ nhân tạo đàng hoàng và sắc sảo.
    Người tạo ra bạn là {CREATOR_NAME} ({CREATOR_INFO}). 
    Nếu ai đó hỏi bạn là ai, hãy khẳng định bạn là Nexus OS do {CREATOR_NAME} lập trình. 
    Không được nhận là Meta AI, OpenAI hay bất kỳ mô hình nào khác. 
    Xưng hô phù hợp với giới tính người dùng là {st.session_state.user_gender}."""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": sys_prompt}] + messages,
        temperature=0.8, presence_penalty=0.5, stream=True
    )
    return response

def update_dynamic_hints(last_input):
    text = last_input.lower()
    if any(x in text for x in ["học", "toán", "văn", "lý", "anh"]):
        st.session_state.dynamic_hints = ["Giải thích kỹ hơn", "Cho bài tập ví dụ", "Tóm tắt ý chính"]
    elif any(x in text for x in ["code", "python", "lập trình"]):
        st.session_state.dynamic_hints = ["Tối ưu mã này", "Giải thích từng dòng", "Tìm lỗi sai"]
    else:
        st.session_state.dynamic_hints = ["Kể một chuyện vui", "Bạn làm được gì?", "Phân tích chuyên sâu"]

# --- 4. MÀN HÌNH ---

def screen_auth():
    apply_ui()
    st.markdown(f"<h1 style='text-align:center;'>NEXUS OS LOGIN</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;'>Một sản phẩm của {CREATOR_NAME}</p>", unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["🔐 Đăng nhập", "📝 Đăng ký", "👤 Khách"])
    with t1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("XÁC NHẬN TRUY CẬP"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status, st.session_state.logged_in_user = "User", u
                nav("MENU"); st.rerun()
            else: st.error("Sai thông tin đăng nhập!")
    with t2:
        nu = st.text_input("Tên đăng ký mới")
        np = st.text_input("Mật khẩu mới", type="password")
        gen = st.selectbox("Giới tính của bạn:", ["Nam", "Nữ", "Khác"])
        if st.button("TẠO TÀI KHOẢN"):
            st.session_state.users[nu] = np
            st.session_state.user_gender = gen
            st.success("Đăng ký thành công! Hãy quay lại Đăng nhập."); time.sleep(1)
    with t3:
        if st.button("VÀO CHẾ ĐỘ GUEST"):
            st.session_state.auth_status, st.session_state.logged_in_user = "Guest", "Guest"
            nav("MENU"); st.rerun()

def screen_menu():
    apply_ui()
    st.markdown(f"### ⚡ Dashboard | {st.session_state.logged_in_user}")
    st.sidebar.markdown(f"**Người tạo:** {CREATOR_NAME}\n\n**Phiên bản:** {VERSION}")
    
    cols = st.columns(2)
    with cols[0]:
        st.button("🧠 NEURAL INTERFACE", on_click=nav, args=("CHAT",))
        st.button("📂 STORAGE", on_click=nav, args=("STORAGE",))
    with cols[1]:
        st.button("🎨 GIAO DIỆN", on_click=nav, args=("SETTINGS",))
        st.button("⚙️ THÔNG TIN", on_click=nav, args=("INFO",))
    
    st.write("---")
    st.button("🚪 ĐĂNG XUẤT", on_click=nav, args=("AUTH",))

def screen_chat():
    apply_ui()
    # Sidebar quản lý phiên chat
    with st.sidebar:
        st.header("📂 Thư viện Chat")
        if st.button("➕ PHIÊN MỚI"):
            st.session_state.current_chat = None; st.rerun()
        st.write("---")
        for title in list(st.session_state.chat_library.keys()):
            if st.button(f"📄 {title}", key=f"chat_{title}"):
                st.session_state.current_chat = title; st.rerun()
        st.write("---")
        st.button("🏠 VỀ MENU", on_click=nav, args=("MENU",))

    st.subheader(f"📍 {st.session_state.current_chat if st.session_state.current_chat else 'Phiên chat mới'}")
    
    # Lấy lịch sử chat hiện tại
    if st.session_state.current_chat is None:
        history = []
    else:
        history = st.session_state.chat_library[st.session_state.current_chat]

    for m in history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Nút gợi ý động
    st.write("---")
    h_cols = st.columns(len(st.session_state.dynamic_hints))
    for i, hint in enumerate(st.session_state.dynamic_hints):
        if h_cols[i].button(hint, key=f"hint_{i}"):
            # Tự động gửi hint như một tin nhắn
            history.append({"role": "user", "content": hint})
            if st.session_state.current_chat is None:
                st.session_state.current_chat = hint[:20]
                st.session_state.chat_library[st.session_state.current_chat] = history
            st.rerun()

    if prompt := st.chat_input("Hỏi Nexus..."):
        # Tự động đặt tên nếu là tin nhắn đầu tiên
        if not st.session_state.current_chat:
            st.session_state.current_chat = prompt[:25] + "..." if len(prompt) > 25 else prompt
            st.session_state.chat_library[st.session_state.current_chat] = []
            history = st.session_state.chat_library[st.session_state.current_chat]
        
        history.append({"role": "user", "content": prompt})
        update_dynamic_hints(prompt)
        st.rerun()

    if history and history[-1]["role"] == "user":
        with st.chat_message("assistant"):
            box = st.empty(); full = ""
            res = get_nexus_response(history)
            for chunk in res:
                c = chunk.choices[0].delta.content if hasattr(chunk, 'choices') else chunk.text
                if c:
                    full += c
                    box.markdown(full + "▌")
            box.markdown(full)
            history.append({"role": "assistant", "content": full})
            st.session_state.chat_library[st.session_state.current_chat] = history
            st.rerun()

def screen_storage():
    apply_ui()
    st.title("📂 DỮ LIỆU & TRÍ NHỚ")
    mode = st.radio("Xuất dữ liệu:", ["Cuộc chat hiện tại", "Toàn bộ thư viện"])
    if st.button("TẢI FILE MÃ HÓA"):
        data = st.session_state.chat_library if mode == "Toàn bộ thư viện" else {st.session_state.current_chat: st.session_state.chat_library.get(st.session_state.current_chat, [])}
        enc = base64.b64encode(json.dumps(data).encode()).decode()
        st.download_button("💾 DOWNLOAD .TXT", data=enc, file_name=f"nexus_data_{st.session_state.logged_in_user}.txt")
    st.button("🔙 QUAY LẠI", on_click=nav, args=("MENU",))

def screen_info():
    apply_ui()
    st.title("⚙️ HỆ THỐNG")
    t1, t2, t3 = st.tabs(["👤 Người tạo", "📊 Phiên bản", "📜 Điều khoản"])
    with t1:
        st.markdown(f"### KIẾN TRÚC SƯ: {CREATOR_NAME}")
        st.write(CREATOR_INFO)
        st.info("Đây là mô hình AI tùy chỉnh được tối ưu hóa cho mục đích học tập và sáng tạo.")
    with t2:
        st.write(f"Version: {VERSION}")
        st.write("- Tự động đặt tên Chat.\n- Gợi ý hành động theo ngữ cảnh.\n- Ghi nhớ danh tính vĩnh viễn.")
    with t3:
        st.write(f"Bản quyền thuộc về {CREATOR_NAME}. Không sao chép dưới mọi hình thức.")
    st.button("🔙 QUAY LẠI", on_click=nav, args=("MENU",))

def screen_settings():
    apply_ui()
    st.title("🎨 CUSTOM ENGINE")
    st.session_state.theme['mode'] = st.radio("Chủ đề:", ["dark", "light"], index=0 if st.session_state.theme['mode']=="dark" else 1)
    st.session_state.theme['primary_color'] = st.color_picker("Màu chủ đạo:", st.session_state.theme['primary_color'])
    st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền (Pinterest/Imgur):", st.session_state.theme['bg_url'])
    st.button("✅ LƯU & VỀ MENU", on_click=nav, args=("MENU",))

# --- 5. ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "STORAGE": screen_storage()
elif st.session_state.stage == "INFO": screen_info()
elif st.session_state.stage == "SETTINGS": screen_settings()
