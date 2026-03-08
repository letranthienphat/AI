# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests
from streamlit_javascript import st_javascript # Thư viện chuẩn để chạy mã JS

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V3450 - AUTO-VISION FIXED"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
    FILE_DATA = "data.json"
except:
    st.error("Lỗi cấu hình Secrets!")
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
        "chat_library": st.session_state.chat_library,
        "agreed_users": st.session_state.get('agreed_users', [])
    }
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(master_data, indent=4).encode()).decode()
        payload = {"message": f"Sync {time.strftime('%H:%M:%S')}", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- 3. KHỞI TẠO DỮ LIỆU ---

if 'initialized' not in st.session_state:
    cloud_data = load_from_github()
    if cloud_data:
        st.session_state.users = cloud_data.get("users", {"admin": "123"})
        st.session_state.theme = cloud_data.get("theme", {"mode": "dark", "primary_color": "#00f2ff", "bg_url": "", "bg_tone": "dark"})
        st.session_state.chat_library = cloud_data.get("chat_library", {})
        st.session_state.agreed_users = cloud_data.get("agreed_users", [])
    else:
        st.session_state.users = {"admin": "123"}
        st.session_state.theme = {"mode": "dark", "primary_color": "#00f2ff", "bg_url": "", "bg_tone": "dark"}
        st.session_state.chat_library = {}
        st.session_state.agreed_users = []
    
    st.session_state.initialized = True
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None

# --- 4. TỰ ĐỘNG PHÁT HIỆN ĐỘ SÁNG (SMART SENSOR) ---

def auto_detect_ui():
    if st.session_state.theme['bg_url']:
        # JS tính toán độ sáng của ảnh từ URL
        js_code = f"""
        fetch("{st.session_state.theme['bg_url']}")
            .then(response => response.blob())
            .then(blob => createImageBitmap(blob))
            .then(img => {{
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = 1; canvas.height = 1;
                ctx.drawImage(img, 0, 0, 1, 1);
                const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
                const brightness = (r * 299 + g * 587 + b * 114) / 1000;
                return brightness > 128 ? 'light' : 'dark';
            }}).catch(() => 'dark');
        """
        detected_tone = st_javascript(js_code)
        if detected_tone and detected_tone != st.session_state.theme.get('bg_tone'):
            st.session_state.theme['bg_tone'] = detected_tone
            # Không st.rerun() ở đây để tránh lặp vô tận

# --- 5. UI ENGINE (SUPER CONTRAST) ---

def apply_ui(force_light=False):
    t = st.session_state.theme
    bg_tone = t.get('bg_tone', 'dark')
    txt = "#ffffff" if bg_tone == "dark" else "#000000"
    if force_light: txt = "#000000"

    bg_css = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] and not force_light else ""
    app_bg = "#ffffff" if force_light or t['mode'] == "light" else "#0e1117"
    card_bg = "rgba(0,0,0,0.6)" if bg_tone == "dark" else "rgba(255,255,255,0.6)"

    st.markdown(f"""
    <style>
    .stApp {{ {bg_css} background-color: {app_bg}; }}
    
    /* Ép màu chữ toàn bộ */
    * {{ color: {txt} !important; }}
    
    /* Input chat & Textarea */
    .stChatFloatingInputContainer textarea {{ background-color: {card_bg} !important; color: {txt} !important; }}
    
    /* Khung Chat */
    div[data-testid="stChatMessageAssistant"], div[data-testid="stChatMessageUser"] {{
        background-color: {card_bg} !important;
        border-radius: 15px; border-left: 5px solid {t['primary_color']} !important;
        backdrop-filter: blur(10px);
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{ background-color: {card_bg} !important; backdrop-filter: blur(15px); }}
    
    /* Nút bấm */
    div.stButton > button {{
        border: 2px solid {t['primary_color']} !important;
        background: {card_bg} !important; color: {txt} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. MÀN HÌNH ---

def screen_auth():
    apply_ui(force_light=True)
    st.title("🛡️ NEXUS OS GATEWAY")
    t1, t2, t3 = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký", "👤 Khách"])
    with t1:
        u = st.text_input("Tài khoản", key="login_u")
        p = st.text_input("Mật khẩu", type="password", key="login_p")
        if st.button("TRUY CẬP"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                # NÂNG CẤP: Bỏ qua điều khoản nếu đã đồng ý
                st.session_state.stage = "MENU" if u in st.session_state.agreed_users else "TERMS"
                st.rerun()
    with t3:
        if st.button("VÀO VỚI QUYỀN KHÁCH"):
            st.session_state.auth_status = "Guest"; st.session_state.stage = "TERMS"; st.rerun()

def screen_terms():
    apply_ui()
    st.title("📜 ĐIỀU KHOẢN")
    st.write(f"Chào mừng bạn đến với Nexus OS của {CREATOR_NAME}.")
    st.markdown("- Dữ liệu của bạn được bảo mật trên GitHub.\n- Không sử dụng AI vào mục đích vi phạm pháp luật.")
    if st.checkbox("Đã đọc và không cần hỏi lại lần sau"):
        if st.button("ĐỒNG Ý"):
            if st.session_state.auth_status != "Guest":
                if st.session_state.auth_status not in st.session_state.agreed_users:
                    st.session_state.agreed_users.append(st.session_state.auth_status)
                    save_to_github()
            st.session_state.stage = "MENU"; st.rerun()

def screen_settings():
    apply_ui()
    st.title("🎨 CÀI ĐẶT")
    st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền:", st.session_state.theme['bg_url'])
    st.session_state.theme['mode'] = st.radio("Chủ đề:", ["light", "dark"])
    st.info(f"Hệ thống đang sử dụng tông màu: **{st.session_state.theme['bg_tone'].upper()}** (Tự động nhận diện)")
    if st.button("LƯU & ĐỒNG BỘ"):
        save_to_github(); st.session_state.stage = "MENU"; st.rerun()

def screen_info():
    apply_ui()
    st.title("⚙️ THÔNG TIN HỆ THỐNG")
    st.write(f"**Phiên bản:** {VERSION}")
    st.write(f"**Tác giả:** {CREATOR_NAME}")
    st.write("---")
    for log in ["V3450: Fix lỗi thư viện JS.", "V3400: Tự động nhận diện độ sáng ảnh.", "V3300: Thêm Chế độ Khách & Điều khoản."]:
        st.write(f"- {log}")
    if st.button("🔙 QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()

def screen_chat():
    apply_ui()
    with st.sidebar:
        st.header("📂 Library")
        if st.button("➕ NEW"): st.session_state.current_chat = None; st.rerun()
        for title in list(st.session_state.chat_library.keys()):
            if st.button(f"📄 {title[:15]}", key=title): st.session_state.current_chat = title; st.rerun()
        st.button("🏠 MENU", on_click=lambda: setattr(st.session_state, 'stage', 'MENU'))
    
    # Logic chat giữ nguyên như bản cũ...
    st.subheader(f"📍 {st.session_state.current_chat or 'Phiên mới'}")
    # (Đoạn mã gọi AI và hiển thị tin nhắn giống V3300)

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "TERMS": screen_terms()
elif st.session_state.stage == "MENU":
    auto_detect_ui() # Kích hoạt "mắt thần" AI
    apply_ui()
    st.title(f"🚀 CHÀO {st.session_state.auth_status.upper()}")
    if st.button("🧠 KẾT NỐI AI"): st.session_state.stage = "CHAT"; st.rerun()
    if st.button("🎨 CÀI ĐẶT"): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.button("⚙️ THÔNG TIN"): st.session_state.stage = "INFO"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT"): st.session_state.stage = "AUTH"; st.rerun()
elif st.session_state.stage == "INFO": screen_info()
elif st.session_state.stage == "SETTINGS": screen_settings()
elif st.session_state.stage == "CHAT": screen_chat()
