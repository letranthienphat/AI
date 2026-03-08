# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests
from streamlit_javascript import st_javascript

# --- 1. CẤU HÌNH ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V3600 - SECURE AUTH"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
    FILE_DATA = "data.json"
except:
    st.error("Thiếu Secrets! Hãy kiểm tra GH_TOKEN, GH_REPO và GROQ_KEYS.")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. HÀM ĐỒNG BỘ ---
def load_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except: pass
    return {}

def save_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    data = {
        "users": st.session_state.users,
        "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library,
        "agreed_users": st.session_state.get('agreed_users', [])
    }
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": f"Sync {time.strftime('%H:%M:%S')}", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- 3. KHỞI TẠO ---
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123"})
    st.session_state.theme = db.get("theme", {"mode": "dark", "primary_color": "#00f2ff", "bg_url": "", "bg_tone": "dark"})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.agreed_users = db.get("agreed_users", [])
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.initialized = True

# --- 4. TƯƠNG PHẢN TỰ ĐỘNG ---
def detect_ui_tone():
    if st.session_state.theme.get('bg_url'):
        js_code = f"""
        fetch("{st.session_state.theme['bg_url']}")
            .then(res => res.blob()).then(createImageBitmap)
            .then(img => {{
                const cvs = document.createElement('canvas'); const ctx = cvs.getContext('2d');
                cvs.width = 1; cvs.height = 1; ctx.drawImage(img, 0, 0, 1, 1);
                const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
                return (r*0.299 + g*0.587 + b*0.114) > 128 ? 'light' : 'dark';
            }}).catch(() => 'dark');
        """
        result = st_javascript(js_code)
        if result and result in ['light', 'dark']:
            if result != st.session_state.theme.get('bg_tone'):
                st.session_state.theme['bg_tone'] = result

def apply_ui(force_light=False):
    t = st.session_state.theme
    tone = 'light' if force_light else t.get('bg_tone', 'dark')
    txt = "#000000" if tone == 'light' else "#ffffff"
    app_bg = "#ffffff" if (force_light or t['mode'] == 'light') else "#0e1117"
    card_bg = "rgba(255,255,255,0.8)" if tone == 'light' else "rgba(0,0,0,0.8)"
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if (t['bg_url'] and not force_light) else ""

    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} background-color: {app_bg}; }}
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, .stMarkdown p, .stMarkdown li {{
        color: {txt} !important;
    }}
    .overlay-box {{
        background-color: {card_bg} !important; border-radius: 15px; padding: 25px;
        border: 1px solid {t['primary_color']}; backdrop-filter: blur(10px);
    }}
    div.stButton > button {{
        border: 2px solid {t['primary_color']} !important;
        background: {card_bg} !important; color: {txt} !important; font-weight: bold;
    }}
    [data-testid="stSidebar"] {{ background-color: {card_bg} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. MÀN HÌNH XÁC THỰC ---
def screen_auth():
    apply_ui(force_light=True)
    st.title("🛡️ NEXUS OS GATEWAY")
    tab1, tab2, tab3 = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký", "👤 Khách"])
    
    with tab1:
        u = st.text_input("Tài khoản", key="u_login")
        p = st.text_input("Mật khẩu", type="password", key="p_login")
        if st.button("TRUY CẬP HỆ THỐNG"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU" if u in st.session_state.agreed_users else "TERMS"
                st.rerun()
            else: st.error("Sai thông tin đăng nhập!")

    with tab2:
        nu = st.text_input("Tên đăng ký", key="u_reg")
        np1 = st.text_input("Mật khẩu", type="password", key="p_reg1")
        np2 = st.text_input("Xác nhận mật khẩu", type="password", key="p_reg2")
        if st.button("TẠO TÀI KHOẢN MỚI"):
            if not nu: st.warning("Vui lòng nhập tên!")
            elif np1 != np2: st.error("Mật khẩu xác nhận không khớp!")
            elif len(np1) < 3: st.warning("Mật khẩu quá ngắn!")
            else:
                st.session_state.users[nu] = np1
                save_github()
                st.success("Đăng ký thành công! Hãy quay lại tab Đăng nhập.")

    with tab3:
        st.info("Chế độ khách: Bạn có thể trải nghiệm AI nhưng lịch sử chat sẽ không được lưu vĩnh viễn.")
        if st.button("TIẾP TỤC VỚI QUYỀN KHÁCH"):
            st.session_state.auth_status = "Guest"
            st.session_state.stage = "TERMS"
            st.rerun()

def screen_terms():
    detect_ui_tone()
    apply_ui()
    st.title("📜 ĐIỀU KHOẢN")
    st.markdown(f"""
    <div class="overlay-box">
        <h3>Chào mừng {st.session_state.auth_status.upper()}</h3>
        <p>1. Mọi dữ liệu chat sẽ được bảo mật qua mã hóa GitHub.</p>
        <p>2. Không sử dụng Nexus OS cho mục đích trái pháp luật.</p>
        <p>3. Tài khoản khách sẽ bị xóa lịch sử khi trình duyệt đóng.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.checkbox("Tôi đồng ý và không cần hỏi lại") and st.button("VÀO MENU"):
        if st.session_state.auth_status != "Guest":
            st.session_state.agreed_users.append(st.session_state.auth_status)
            save_github()
        st.session_state.stage = "MENU"; st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "TERMS": screen_terms()
elif st.session_state.stage == "MENU":
    detect_ui_tone()
    apply_ui()
    st.title(f"🚀 CHÀO {st.session_state.auth_status.upper()}")
    # ... (Các nút chức năng khác của Menu)
    if st.button("🚪 ĐĂNG XUẤT"): 
        st.session_state.stage = "AUTH"
        st.session_state.auth_status = None
        st.rerun()
