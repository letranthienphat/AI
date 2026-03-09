# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V4700 - STABLE AI"
FILE_DATA = "data.json"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("Thiếu Secrets cấu hình!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. BẢO MẬT ---
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
        "users": st.session_state.users, "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library, "agreed_users": st.session_state.agreed_users,
        "friends": st.session_state.friends, "friend_requests": st.session_state.friend_requests,
        "groups": st.session_state.groups, "p2p_chats": st.session_state.p2p_chats
    }
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": f"Sync {VERSION}", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- 4. KHỞI TẠO & VÁ LỖI DỮ LIỆU ---
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123"})
    
    # VÁ LỖI THEME (Tránh KeyError)
    theme_data = db.get("theme", {})
    default_theme = {
        "primary_color": "#00f2ff", "bg_url": "", "use_glass": True,
        "auto_wallpaper": False, "wp_interval": 1440, "last_wp_update": 0,
        "naming_threshold": 5
    }
    for k, v in default_theme.items():
        if k not in theme_data: theme_data[k] = v
    st.session_state.theme = theme_data

    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.friends = db.get("friends", {})
    st.session_state.friend_requests = db.get("friend_requests", {})
    st.session_state.groups = db.get("groups", {})
    st.session_state.p2p_chats = db.get("p2p_chats", {})
    st.session_state.agreed_users = db.get("agreed_users", [])
    
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None
    st.session_state.confirm_delete = None
    st.session_state.initialized = True

# --- 5. GIAO DIỆN SIÊU SẠCH (NO EXTRA BARS) ---
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] else "background-color: #0e1117;"
    
    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} }}
    
    /* CHỮ CÓ BÓNG MỜ NEON */
    label, .stApp p, .stApp span, h1, h2, h3, h4, .stMarkdown p {{
        color: #000000 !important; font-weight: 700 !important;
        text-shadow: 1px 1px 10px {p_color}88 !important;
    }}
    
    .main-title {{
        color: {p_color} !important; text-shadow: 0px 0px 15px {p_color} !important;
        text-align: center; font-size: 2.8rem; font-weight: 900;
    }}

    .glass-card, [data-testid="stSidebar"], .stTabs {{
        background: rgba(255, 255, 255, 0.45) !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 15px; border: 1px solid {p_color}44;
    }}

    /* DỌN DẸP SIDEBAR & CÁC THANH THỪA */
    [data-testid="stSidebarNav"], [data-testid="stHeader"] {{ display: none !important; }}
    div[data-testid="stVerticalBlock"] {{ gap: 0rem !important; }}
    
    /* FIX NÚT XÓA SIDEBAR - KHÔNG BỊ LỆCH */
    .stButton > button {{
        border: 2px solid {p_color} !important; background: white !important;
        border-radius: 8px; font-weight: 800; height: 100% !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. HỆ THỐNG AI ĐẶT TÊN ---
def call_ai(messages):
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)

def auto_rename_chat(user, old_title):
    history = st.session_state.chat_library[user][old_title]
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    context = "\n".join([decrypt_msg(m['content']) for m in history[:4]])
    prompt = f"Đặt 1 tên ngắn gọn (dưới 5 từ) cho nội dung sau bằng tiếng Việt. Chỉ trả về tên:\n{context}"
    try:
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
        new_title = res.choices[0].message.content.strip().replace('"', '')
        if new_title and new_title != old_title:
            st.session_state.chat_library[user][new_title] = st.session_state.chat_library[user].pop(old_title)
            st.session_state.current_chat = new_title
            save_github()
    except: pass

# --- 7. MÀN HÌNH CHÍNH ---

def screen_chat():
    apply_ui()
    user = st.session_state.auth_status
    lib = st.session_state.chat_library.setdefault(user, {})
    
    with st.sidebar:
        st.markdown(f'<h3 style="color:{st.session_state.theme["primary_color"]}; text-align:center;">NEXUS CHAT</h3>', unsafe_allow_html=True)
        if st.button("➕ CHAT MỚI", use_container_width=True): st.session_state.current_chat = None; st.rerun()
        st.write("---")
        for title in list(lib.keys()):
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                if st.button(f"📄 {title}", key=f"b_{title}", use_container_width=True):
                    st.session_state.current_chat = title; st.rerun()
            with c2:
                if st.session_state.confirm_delete == title:
                    if st.button("✔️", key=f"y_{title}"): del lib[title]; st.session_state.confirm_delete = None; save_github(); st.rerun()
                elif st.button("🗑️", key=f"d_{title}"): st.session_state.confirm_delete = title; st.rerun()
        st.write("---")
        if st.button("🏠 VỀ MENU", use_container_width=True): st.session_state.stage = "MENU"; st.rerun()

    # HIỂN THỊ NỘI DUNG CHAT
    st.write(f"📂 **{st.session_state.current_chat or 'Phiên mới'}**")
    history = lib.get(st.session_state.current_chat, [])
    for m in history:
        with st.chat_message(m["role"]): st.markdown(decrypt_msg(m["content"]))

    if prompt := st.chat_input("Nhập tin nhắn..."):
        if not st.session_state.current_chat:
            st.session_state.current_chat = f"Chat {int(time.time())}"
            lib[st.session_state.current_chat] = []
        
        lib[st.session_state.current_chat].append({"role": "user", "content": encrypt_msg(prompt)})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            res_box = st.empty(); full_res = ""
            messages = [{"role": "system", "content": "Bạn là AI Nexus. Trả lời tiếng Việt."}]
            messages += [{"role": m["role"], "content": decrypt_msg(m["content"])} for m in lib[st.session_state.current_chat]]
            for chunk in call_ai(messages):
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    res_box.markdown(full_res + "▌")
            res_box.markdown(full_res)
        
        lib[st.session_state.current_chat].append({"role": "assistant", "content": encrypt_msg(full_res)})
        
        # AI tự đặt tên sau X phản hồi
        if len(lib[st.session_state.current_chat]) == st.session_state.theme.get('naming_threshold', 5) * 2:
            auto_rename_chat(user, st.session_state.current_chat)
        
        save_github(); st.rerun()

def screen_settings():
    apply_ui()
    st.markdown('<h1 class="main-title">⚙️ CÀI ĐẶT</h1>', unsafe_allow_html=True)
    user = st.session_state.auth_status
    t = st.session_state.theme
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f'<h4 style="color:{t["primary_color"]}">🔐 ĐỔI MẬT KHẨU</h4>', unsafe_allow_html=True)
        old_p = st.text_input("Mật khẩu hiện tại:", type="password")
        new_p = st.text_input("Mật khẩu mới:", type="password")
        if st.button("CẬP NHẬT MẬT KHẨU"):
            if st.session_state.users[user] == old_p:
                st.session_state.users[user] = new_p; save_github(); st.success("Xong!")
            else: st.error("Sai mật khẩu cũ!")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f'<h4 style="color:{t["primary_color"]}">🎨 CÁ NHÂN HÓA</h4>', unsafe_allow_html=True)
        t['naming_threshold'] = st.slider("Đặt tên sau số tin nhắn:", 1, 10, t['naming_threshold'])
        t['primary_color'] = st.color_picker("Màu chủ đạo:", t['primary_color'])
        st.write("---")
        auto = st.toggle("Đổi hình nền tự động", t.get('auto_wallpaper', False))
        t['auto_wallpaper'] = auto
        if auto:
            t['wp_interval'] = st.number_input("Mỗi bao nhiêu phút:", min_value=1, value=t.get('wp_interval', 1440))
        st.markdown('</div>', unsafe_allow_html=True)
        
    if st.button("💾 LƯU & QUAY LẠI", use_container_width=True): save_github(); st.session_state.stage = "MENU"; st.rerun()

# --- 8. ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH":
    apply_ui()
    st.markdown('<h1 class="main-title">🛡️ NEXUS OS</h1>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.3, 1])
    with c2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("LOGIN", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u; st.session_state.stage = "MENU"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    st.markdown('<h1 class="main-title">🚀 TRUNG TÂM</h1>', unsafe_allow_html=True)
    cols = st.columns(4)
    if cols[0].button("🧠 CHAT"): st.session_state.stage = "CHAT"; st.rerun()
    if cols[1].button("🌐 SOCIAL"): st.session_state.stage = "SOCIAL"; st.rerun()
    if cols[2].button("⚙️ CÀI ĐẶT"): st.session_state.stage = "SETTINGS"; st.rerun()
    if cols[3].button("🚪 LOGOUT"): st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()

elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "SETTINGS": screen_settings()
