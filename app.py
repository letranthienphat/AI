# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V4300 - DYNAMIC UI"
FILE_DATA = "data.json"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("Thiếu cấu hình Secrets!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. HỆ THỐNG BẢO MẬT & MÃ HÓA ---
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

def encrypt_msg(text):
    if not text: return text
    encoded = "".join([chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(text)])
    return base64.b64encode(encoded.encode()).decode()

def decrypt_msg(text):
    if not text: return text
    try:
        decoded = base64.b64decode(text.encode()).decode()
        return "".join([chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(decoded)])
    except: return text

# --- 3. ĐỒNG BỘ GITHUB ---
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
        "agreed_users": st.session_state.agreed_users,
        "friends": st.session_state.friends,
        "friend_requests": st.session_state.friend_requests,
        "groups": st.session_state.groups,
        "p2p_chats": st.session_state.p2p_chats
    }
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": "Nexus Sync", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- 4. KHỞI TẠO BIẾN ---
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123"})
    st.session_state.theme = db.get("theme", {
        "primary_color": "#00f2ff", 
        "bg_url": "", 
        "use_glass": True,
        "auto_wallpaper": False,
        "wp_interval": 1440, # Phút (24h)
        "last_wp_update": 0
    })
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.agreed_users = db.get("agreed_users", [])
    st.session_state.friends = db.get("friends", {})
    st.session_state.friend_requests = db.get("friend_requests", {})
    st.session_state.groups = db.get("groups", {})
    st.session_state.p2p_chats = db.get("p2p_chats", {})
    
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.confirm_delete = None
    st.session_state.initialized = True

# --- 5. LOGIC ĐỔI HÌNH NỀN TỰ ĐỘNG ---
def check_auto_wallpaper():
    t = st.session_state.theme
    if t.get('auto_wallpaper', False):
        now = time.time()
        interval_sec = t.get('wp_interval', 1440) * 60
        if now - t.get('last_wp_update', 0) > interval_sec:
            new_bg = f"https://picsum.photos/1920/1080?random={int(now)}"
            st.session_state.theme['bg_url'] = new_bg
            st.session_state.theme['last_wp_update'] = now
            save_github()

# --- 6. ENGINE GIAO DIỆN ---
def apply_ui():
    check_auto_wallpaper()
    t = st.session_state.theme
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] else "background-color: #0e1117;"
    glass_bg = "rgba(255, 255, 255, 0.45)" if t.get('use_glass', True) else "transparent"
    
    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} }}
    
    /* TIÊU ĐỀ PHÁT SÁNG */
    .glow-text {{
        color: {t['primary_color']} !important;
        text-shadow: 0px 0px 10px {t['primary_color']};
        font-weight: 900 !important;
        text-transform: uppercase;
    }}
    
    .main-title {{
        color: {t['primary_color']} !important;
        text-align: center; font-size: 3rem; font-weight: 900;
        text-shadow: 0px 0px 15px {t['primary_color']};
        margin-bottom: 25px;
    }}

    .stApp p, .stApp span, .stApp label, .stMarkdown p, .stMarkdown li, h1, h2, h3, h4 {{
        color: #000000 !important; font-weight: 600 !important;
    }}

    .glass-card, div[data-testid="stChatMessage"], [data-testid="stSidebar"], .stTabs {{
        background: {glass_bg} !important;
        backdrop-filter: blur(12px) !important;
        border-radius: 15px; padding: 20px;
    }}

    /* FIX NÚT BẤM DÀI TRONG SIDEBAR */
    [data-testid="stSidebar"] div.stButton > button {{
        white-space: normal !important;
        height: auto !important;
        text-align: left !important;
        padding: 10px !important;
        line-height: 1.4 !important;
    }}

    div.stButton > button {{
        width: 100%; border-radius: 10px; font-weight: 800;
        border: 2px solid {t['primary_color']} !important;
        background: rgba(255,255,255,0.8) !important; color: #000000 !important;
    }}
    div.stButton > button:hover {{ background: {t['primary_color']} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 7. MÀN HÌNH CHÍNH ---

def screen_auth():
    apply_ui()
    st.markdown('<h1 class="main-title">🛡️ NEXUS OS GATEWAY</h1>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔑 ĐĂNG NHẬP", "📝 ĐĂNG KÝ"])
        with t1:
            u = st.text_input("Tên tài khoản", key="l_u")
            p = st.text_input("Mật khẩu", type="password", key="l_p")
            if st.button("XÁC THỰC", use_container_width=True):
                if u in st.session_state.users and st.session_state.users[u] == p:
                    st.session_state.auth_status = u
                    st.session_state.stage = "MENU" if u in st.session_state.agreed_users else "TERMS"
                    st.rerun()
                else: st.error("Thông tin không chính xác!")
        with t2:
            nu = st.text_input("Tên mới", key="r_u")
            p1 = st.text_input("Mật khẩu", type="password", key="r_p1")
            if st.button("TẠO TÀI KHOẢN", use_container_width=True):
                if nu and p1: 
                    st.session_state.users[nu] = p1; save_github(); st.success("Đã tạo!")
        st.markdown('</div>', unsafe_allow_html=True)

def screen_chat():
    apply_ui()
    user = st.session_state.auth_status
    lib = st.session_state.chat_library.setdefault(user, {})

    with st.sidebar:
        st.markdown(f'<h2 class="glow-text">📂 THƯ VIỆN</h2>', unsafe_allow_html=True)
        if st.button("➕ CHAT MỚI"): st.session_state.current_chat = None; st.rerun()
        st.write("---")
        
        for title in list(lib.keys()):
            c_btn, c_del = st.columns([4, 1.2])
            with c_btn:
                if st.button(f"📄 {title}", key=f"btn_{title}"):
                    st.session_state.current_chat = title; st.rerun()
            with c_del:
                # Tính năng xác nhận xóa
                if st.session_state.confirm_delete == title:
                    if st.button("✔️", key=f"yes_{title}"):
                        del lib[title]; st.session_state.confirm_delete = None; save_github(); st.rerun()
                    if st.button("✖️", key=f"no_{title}"):
                        st.session_state.confirm_delete = None; st.rerun()
                else:
                    if st.button("🗑️", key=f"del_{title}"):
                        st.session_state.confirm_delete = title; st.rerun()
        
        st.write("---")
        if st.button("🏠 VỀ MENU"): st.session_state.stage = "MENU"; st.rerun()

    # (Phần hiển thị Chat AI giữ nguyên logic mã hóa của V4200)
    st.write(f"Đang chat: **{st.session_state.current_chat or 'Mới'}**")
    # ... code chat AI ...

def screen_settings():
    apply_ui()
    st.markdown('<h1 class="main-title">⚙️ CÀI ĐẶT HỆ THỐNG</h1>', unsafe_allow_html=True)
    user = st.session_state.auth_status
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="glow-text">👤 THAY ĐỔI TÊN</h3>', unsafe_allow_html=True)
        new_name = st.text_input("Tên hiển thị mới:", value=user)
        if st.button("CẬP NHẬT TÊN"):
            if new_name and new_name != user and new_name not in st.session_state.users:
                st.session_state.users[new_name] = st.session_state.users.pop(user)
                st.session_state.auth_status = new_name; save_github(); st.success("Đã đổi!"); st.rerun()
        
        st.write("---")
        st.markdown('<h3 class="glow-text">🔐 ĐỔI MẬT KHẨU</h3>', unsafe_allow_html=True)
        old_p = st.text_input("Mật khẩu hiện tại:", type="password")
        new_p = st.text_input("Mật khẩu mới:", type="password")
        if st.button("XÁC NHẬN ĐỔI MK"):
            if st.session_state.users[user] == old_p:
                st.session_state.users[user] = new_p; save_github(); st.success("Thành công!")
            else: st.error("Sai mật khẩu cũ!")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="glow-text">🖼️ GIAO DIỆN & HÌNH NỀN</h3>', unsafe_allow_html=True)
        st.session_state.theme['primary_color'] = st.color_picker("Màu chủ đạo (Neon):", st.session_state.theme['primary_color'])
        
        st.write("---")
        auto_wp = st.toggle("Bật đổi hình nền tự động mỗi ngày", st.session_state.theme.get('auto_wallpaper', False))
        st.session_state.theme['auto_wallpaper'] = auto_wp
        
        if auto_wp:
            st.session_state.theme['wp_interval'] = st.number_input("Khoảng thời gian đổi (Phút):", min_value=1, value=st.session_state.theme.get('wp_interval', 1440))
            if st.button("THỬ ĐỔI ẢNH NGAY"):
                st.session_state.theme['last_wp_update'] = 0; st.rerun()
        else:
            st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền thủ công:", st.session_state.theme['bg_url'])
            
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("<br>", unsafe_allow_html=True)
    if st.button("💾 LƯU TẤT CẢ & VỀ MENU", use_container_width=True): save_github(); st.session_state.stage = "MENU"; st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "MENU": 
    apply_ui()
    st.markdown('<h1 class="main-title">🚀 NEXUS MENU</h1>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("🧠 AI CHAT"): st.session_state.stage = "CHAT"; st.rerun()
    with c2: 
        if st.button("⚙️ CÀI ĐẶT"): st.session_state.stage = "SETTINGS"; st.rerun()
    with c3: 
        if st.button("🚪 ĐĂNG XUẤT"): st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "SETTINGS": screen_settings()
elif st.session_state.stage == "TERMS": screen_auth() # Đơn giản hóa cho bản mẫu
