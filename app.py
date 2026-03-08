# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN HỆ THỐNG CHI TIẾT ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V3300 - SUPREME CONTROL"
UPDATE_LOG = [
    "V3300: Thêm màn hình Điều khoản, Chế độ Khách, Fix triệt để màu chữ.",
    "V3200: Đồng bộ GitHub vĩnh viễn, sửa lỗi KeyError.",
    "V3100: Tùy chỉnh tông màu ảnh nền Adaptive UI.",
    "V3000: Tích hợp Groq API đa khóa."
]

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
    FILE_DATA = "data.json"
except:
    st.error("Thiếu cấu hình Secrets!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. HỆ THỐNG ĐỒNG BỘ GITHUB ---

def load_from_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            return json.loads(content)
    except: return None
    return None

def save_to_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    master_data = {
        "users": st.session_state.users,
        "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library
    }
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(master_data, indent=4).encode()).decode()
        payload = {"message": f"Nexus Sync {time.strftime('%H:%M:%S')}", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- 3. KHỞI TẠO DỮ LIỆU ---

if 'initialized' not in st.session_state:
    cloud_data = load_from_github()
    if cloud_data:
        st.session_state.users = cloud_data.get("users", {"admin": "123"})
        st.session_state.theme = cloud_data.get("theme", {"mode": "light", "primary_color": "#00f2ff", "bg_url": "", "bg_tone": "light"})
        st.session_state.chat_library = cloud_data.get("chat_library", {})
    else:
        st.session_state.users = {"admin": "123"}
        st.session_state.theme = {"mode": "light", "primary_color": "#00f2ff", "bg_url": "", "bg_tone": "light"}
        st.session_state.chat_library = {}
    st.session_state.initialized = True
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None
    st.session_state.agreed_terms = False

# --- 4. SIÊU CẤU TRÚC UI (TRIỆT TIÊU CHỮ ĐEN) ---

def apply_ui(force_light=False):
    t = st.session_state.theme
    bg_tone = t.get('bg_tone', 'light')
    txt = "#ffffff" if bg_tone == "dark" else "#000000"
    if force_light: txt = "#000000"

    bg_css = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] and not force_light else ""
    app_bg = "#ffffff" if force_light or t['mode'] == "light" else "#0e1117"
    card_bg = "rgba(0,0,0,0.7)" if bg_tone == "dark" else "rgba(255,255,255,0.7)"

    st.markdown(f"""
    <style>
    /* Tổng thể */
    .stApp {{ {bg_css} background-color: {app_bg}; }}
    
    /* FIX MÀU CHỮ CỰC ĐOAN: Áp dụng cho mọi thành phần có thể chứa text */
    .stApp, .stApp p, .stApp div, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, 
    .stMarkdown, .stMarkdownContainer p, .stTextArea label, .stTextInput label {{
        color: {txt} !important;
    }}

    /* Khung nhập liệu (Chat Input) */
    .stChatFloatingInputContainer textarea {{
        color: {txt} !important;
        background-color: {card_bg} !important;
    }}

    /* Nút bấm */
    div.stButton > button {{
        width: 100%; border-radius: 12px; font-weight: 700;
        border: 2px solid {t['primary_color']} !important;
        background: {card_bg} !important; color: {txt} !important;
        backdrop-filter: blur(10px);
    }}

    /* Khung Chat Assistant & User */
    div[data-testid="stChatMessageAssistant"], div[data-testid="stChatMessageUser"] {{
        background-color: {card_bg} !important;
        border-radius: 15px;
        border-left: 6px solid {t['primary_color']} !important;
        backdrop-filter: blur(10px);
    }}
    div[data-testid="stChatMessageAssistant"] .stMarkdown p, 
    div[data-testid="stChatMessageUser"] .stMarkdown p {{
        color: {txt} !important;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{ background-color: {card_bg} !important; backdrop-filter: blur(15px); }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÕI AI ---
def call_ai(messages):
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    sys = f"Bạn là Nexus OS của {CREATOR_NAME}."
    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":sys}]+messages, stream=True)

# --- 6. CÁC MÀN HÌNH ---

def screen_auth():
    apply_ui(force_light=True)
    st.title("🛡️ NEXUS OS GATEWAY")
    t1, t2, t3 = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký", "👤 Khách"])
    with t1:
        u = st.text_input("Tài khoản", key="u_login")
        p = st.text_input("Mật khẩu", type="password", key="p_login")
        if st.button("TRUY CẬP"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u; st.session_state.stage = "TERMS"; st.rerun()
            else: st.error("Sai tài khoản!")
    with t2:
        nu = st.text_input("Tên đăng ký", key="u_reg")
        np = st.text_input("Mật khẩu", type="password", key="p_reg")
        if st.button("TẠO TÀI KHOẢN"):
            if nu: st.session_state.users[nu] = np; save_to_github(); st.success("Đã lưu Cloud!")
    with t3:
        st.write("Bạn sẽ vào với quyền Khách. Dữ liệu chat sẽ không được lưu vĩnh viễn.")
        if st.button("TRẢI NGHIỆM KHÁCH"):
            st.session_state.auth_status = "Guest"; st.session_state.stage = "TERMS"; st.rerun()

def screen_terms():
    apply_ui()
    st.title("📜 ĐIỀU KHOẢN SỬ DỤNG")
    st.write(f"Chào mừng bạn đến với Nexus OS được phát triển bởi **{CREATOR_NAME}**.")
    st.markdown("""
    1. **Bảo mật**: Thông tin của bạn được đồng bộ qua hệ thống GitHub bảo mật.
    2. **Trách nhiệm**: Không sử dụng AI cho mục đích xấu hoặc vi phạm pháp luật.
    3. **Dữ liệu**: Nếu là Khách, dữ liệu sẽ bị xóa khi phiên làm việc kết thúc.
    """)
    if st.checkbox("Tôi đã đọc và đồng ý với các điều khoản trên"):
        if st.button("BẮT ĐẦU"): st.session_state.stage = "MENU"; st.rerun()

def screen_chat():
    apply_ui()
    with st.sidebar:
        st.header("📂 Library")
        if st.button("➕ NEW CHAT"): st.session_state.current_chat = None; st.rerun()
        for title in list(st.session_state.chat_library.keys()):
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                if st.button(f"📄 {title[:12]}", key=title): st.session_state.current_chat = title; st.rerun()
            with c2:
                if st.button("❌", key=f"d_{title}"): del st.session_state.chat_library[title]; save_to_github(); st.rerun()
        st.button("🏠 MENU", on_click=lambda: setattr(st.session_state, 'stage', 'MENU'))

    if st.session_state.current_chat and st.session_state.current_chat in st.session_state.chat_library:
        history = st.session_state.chat_library[st.session_state.current_chat]
    else: history = []

    for m in history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if pr := st.chat_input("Nhập lệnh..."):
        if not st.session_state.current_chat:
            st.session_state.current_chat = pr[:20]
            st.session_state.chat_library[st.session_state.current_chat] = []
            history = st.session_state.chat_library[st.session_state.current_chat]
        history.append({"role": "user", "content": pr})
        with st.chat_message("user"): st.markdown(pr)
        with st.chat_message("assistant"):
            box = st.empty(); full = ""
            for chunk in call_ai(history):
                c = chunk.choices[0].delta.content
                if c: full += c; box.markdown(full + "▌")
            box.markdown(full)
            history.append({"role": "assistant", "content": full})
            st.session_state.chat_library[st.session_state.current_chat] = history
            if st.session_state.auth_status != "Guest": save_to_github()
            st.rerun()

def screen_info():
    apply_ui()
    st.title("⚙️ CHI TIẾT PHIÊN BẢN")
    st.write(f"**Tên phần mềm:** Nexus OS")
    st.write(f"**Phiên bản hiện tại:** {VERSION}")
    st.write(f"**Chủ sở hữu:** {CREATOR_NAME}")
    st.write("---")
    st.subheader("Lịch sử cập nhật:")
    for log in UPDATE_LOG: st.write(f"- {log}")
    if st.button("🔙 QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "TERMS": screen_terms()
elif st.session_state.stage == "MENU":
    apply_ui(); st.title(f"🚀 CHÀO {st.session_state.auth_status.upper()}")
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("🧠 KẾT NỐI AI"): st.session_state.stage = "CHAT"; st.rerun()
    with c2: 
        if st.button("🎨 THIẾT KẾ UI"): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.button("⚙️ THÔNG TIN PHIÊN BẢN"): st.session_state.stage = "INFO"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT"): st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "INFO": screen_info()
elif st.session_state.stage == "SETTINGS": 
    apply_ui()
    st.title("🎨 CÀI ĐẶT")
    st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền:", st.session_state.theme['bg_url'])
    st.session_state.theme['bg_tone'] = st.radio("Tông màu nền:", ["light", "dark"])
    if st.button("LƯU"): save_to_github(); st.session_state.stage = "MENU"; st.rerun()
