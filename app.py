# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests
from streamlit_components_lowlevel import st_javascript # Cần thiết để chạy mã JS phát hiện màu

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V3400 - AUTO-VISION"
UPDATE_LOG = [
    "V3400: Tự động nhận diện độ sáng ảnh nền & Ghi nhớ đồng ý điều khoản.",
    "V3300: Thêm màn hình Điều khoản, Chế độ Khách, Fix chữ đen.",
]

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

def save_to_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    master_data = {
        "users": st.session_state.users,
        "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library,
        "agreed_users": st.session_state.get('agreed_users', []) # Lưu danh sách người đã đồng ý
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
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    cloud_data = json.loads(base64.b64decode(res.json()['content']).decode('utf-8')) if res.status_code == 200 else {}
    
    st.session_state.users = cloud_data.get("users", {"admin": "123"})
    st.session_state.theme = cloud_data.get("theme", {"mode": "dark", "primary_color": "#00f2ff", "bg_url": "", "bg_tone": "dark"})
    st.session_state.chat_library = cloud_data.get("chat_library", {})
    st.session_state.agreed_users = cloud_data.get("agreed_users", [])
    
    st.session_state.initialized = True
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None

# --- 4. TÍNH NĂNG TỰ ĐỘNG PHÁT HIỆN ĐỘ SÁNG (AUTO-VISION) ---

def detect_brightness():
    if st.session_state.theme['bg_url']:
        # Đoạn mã JS này sẽ tải ảnh lên canvas ngầm và tính toán độ sáng trung bình
        js_code = f"""
        (async function() {{
            const img = new Image();
            img.crossOrigin = "Anonymous";
            img.src = "{st.session_state.theme['bg_url']}";
            return new Promise(resolve => {{
                img.onload = function() {{
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    canvas.width = img.width; canvas.height = img.height;
                    ctx.drawImage(img, 0, 0);
                    const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
                    let r, g, b, avg;
                    let colorSum = 0;
                    for(let x = 0, len = data.length; x < len; x += 4) {{
                        r = data[x]; g = data[x+1]; b = data[x+2];
                        avg = Math.floor((r+g+b)/3);
                        colorSum += avg;
                    }}
                    const brightness = Math.floor(colorSum / (img.width * img.height));
                    resolve(brightness > 128 ? 'light' : 'dark');
                }};
                img.onerror = () => resolve('dark');
            }});
        }})();
        """
        try:
            result = st_javascript(js_code)
            if result and result != st.session_state.theme['bg_tone']:
                st.session_state.theme['bg_tone'] = result
                st.rerun()
        except: pass

# --- 5. UI ENGINE (MAX CONTRAST) ---

def apply_ui(force_light=False):
    t = st.session_state.theme
    bg_tone = t.get('bg_tone', 'dark')
    txt = "#ffffff" if bg_tone == "dark" else "#000000"
    if force_light: txt = "#000000"

    bg_css = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] and not force_light else ""
    app_bg = "#ffffff" if force_light or t['mode'] == "light" else "#0e1117"
    card_bg = "rgba(0,0,0,0.7)" if bg_tone == "dark" else "rgba(255,255,255,0.7)"

    st.markdown(f"""
    <style>
    .stApp {{ {bg_css} background-color: {app_bg}; }}
    * {{ color: {txt} !important; font-family: 'Segoe UI', sans-serif; }}
    div.stButton > button {{
        border: 2px solid {t['primary_color']} !important;
        background: {card_bg} !important; backdrop-filter: blur(10px);
    }}
    div[data-testid="stChatMessageAssistant"], div[data-testid="stChatMessageUser"] {{
        background-color: {card_bg} !important; border-left: 5px solid {t['primary_color']} !important;
    }}
    [data-testid="stSidebar"] {{ background-color: {card_bg} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. ĐIỀU HƯỚNG MÀN HÌNH ---

def screen_auth():
    apply_ui(force_light=True)
    st.title("🛡️ NEXUS OS GATEWAY")
    t1, t2, t3 = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký", "👤 Khách"])
    with t1:
        u = st.text_input("Tài khoản", key="login_u")
        p = st.text_input("Mật khẩu", type="password", key="login_p")
        if st.button("XÁC THỰC"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                # KIỂM TRA ĐÃ ĐỒNG Ý CHƯA
                if u in st.session_state.agreed_users:
                    st.session_state.stage = "MENU"
                else:
                    st.session_state.stage = "TERMS"
                st.rerun()
    with t3:
        if st.button("VÀO QUYỀN KHÁCH"):
            st.session_state.auth_status = "Guest"; st.session_state.stage = "TERMS"; st.rerun()

def screen_terms():
    apply_ui()
    st.title("📜 ĐIỀU KHOẢN")
    st.write("Chào mừng đến với hệ thống của Lê Trần Thiên Phát...")
    if st.checkbox("Tôi đồng ý và không cần hỏi lại lần sau"):
        if st.button("XÁC NHẬN"):
            if st.session_state.auth_status != "Guest":
                st.session_state.agreed_users.append(st.session_state.auth_status)
                save_to_github()
            st.session_state.stage = "MENU"; st.rerun()

def screen_settings():
    apply_ui()
    st.title("🎨 CÀI ĐẶT")
    new_url = st.text_input("Link ảnh nền:", st.session_state.theme['bg_url'])
    if new_url != st.session_state.theme['bg_url']:
        st.session_state.theme['bg_url'] = new_url
        # Gọi hàm tự động phát hiện màu khi link thay đổi
        detect_brightness() 
    
    st.write(f"Độ sáng ảnh hiện tại: **{st.session_state.theme['bg_tone'].upper()}** (Tự động)")
    if st.button("LƯU CẤU HÌNH"):
        save_to_github(); st.session_state.stage = "MENU"; st.rerun()

# (Các hàm screen_chat, screen_info giữ nguyên cấu trúc cũ nhưng dùng apply_ui mới)

# --- ĐIỀU HƯỚNG CHÍNH ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "TERMS": screen_terms()
elif st.session_state.stage == "MENU":
    detect_brightness() # Luôn kiểm tra màu nền
    apply_ui()
    st.title(f"🚀 WELCOME {st.session_state.auth_status.upper()}")
    if st.button("🧠 KẾT NỐI AI"): st.session_state.stage = "CHAT"; st.rerun()
    if st.button("🎨 THIẾT KẾ UI"): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.button("🚪 ĐĂNG XUẤT"): st.session_state.stage = "AUTH"; st.rerun()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "SETTINGS": screen_settings()
