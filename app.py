# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V4500 - FULL SOCIAL & AUTO-WP"
FILE_DATA = "data.json"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("Thiếu cấu hình Secrets!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. HỆ THỐNG BẢO MẬT & MÃ HÓA E2E ---
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
        payload = {"message": "Nexus Sync Full", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- 4. KHỞI TẠO BIẾN TỔNG THỂ ---
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123"})
    st.session_state.theme = db.get("theme", {
        "primary_color": "#00f2ff", "bg_url": "", "use_glass": True,
        "auto_wallpaper": False, "wp_interval": 1440, "last_wp_update": 0
    })
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.agreed_users = db.get("agreed_users", [])
    st.session_state.friends = db.get("friends", {})
    st.session_state.friend_requests = db.get("friend_requests", {})
    st.session_state.groups = db.get("groups", {})
    st.session_state.p2p_chats = db.get("p2p_chats", {})
    
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None
    st.session_state.current_group = None
    st.session_state.confirm_delete = None
    st.session_state.initialized = True

def init_user_data(u):
    if u not in st.session_state.friends: st.session_state.friends[u] = []
    if u not in st.session_state.friend_requests: st.session_state.friend_requests[u] = []

# --- 5. LOGIC ĐỔI HÌNH NỀN ---
def run_wallpaper_engine():
    t = st.session_state.theme
    if t.get('auto_wallpaper', False):
        now = time.time()
        interval_sec = t.get('wp_interval', 1440) * 60
        if now - t.get('last_wp_update', 0) > interval_sec:
            st.session_state.theme['bg_url'] = f"https://picsum.photos/1920/1080?random={int(now)}"
            st.session_state.theme['last_wp_update'] = now
            save_github()

# --- 6. ENGINE GIAO DIỆN (NEON GLOW & ALIGNMENT) ---
def apply_ui():
    run_wallpaper_engine()
    t = st.session_state.theme
    p_color = t['primary_color']
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] else "background-color: #0e1117;"
    
    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} }}
    
    /* GLOW CHO NHÃN VÀ CHỮ */
    .stApp p, .stApp span, .stApp label, .stMarkdown p, h1, h2, h3, h4 {{
        color: #000000 !important; font-weight: 700 !important;
        text-shadow: 0px 0px 8px {p_color}88 !important;
    }}
    
    .main-title, .glow-header {{
        color: {p_color} !important;
        text-shadow: 0px 0px 15px {p_color} !important;
        text-align: center; font-weight: 900;
    }}

    .glass-card, [data-testid="stSidebar"], .stTabs {{
        background: rgba(255, 255, 255, 0.45) !important;
        backdrop-filter: blur(12px) !important;
        border-radius: 15px; padding: 20px; border: 1px solid {p_color}33;
    }}

    /* SIDEBAR NÚT THÙNG RÁC NGAY NGẮN */
    [data-testid="stSidebar"] .stButton > button {{
        white-space: normal !important; height: auto !important;
        text-align: left !important; display: flex; align-items: center;
        border: 2px solid {p_color} !important; background: white !important;
    }}
    
    /* INPUT BOX */
    input, textarea {{
        background: rgba(255, 255, 255, 0.8) !important;
        border: 2px solid {p_color} !important; font-weight: 700 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 7. LÕI AI ---
def call_ai(messages):
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    sys_msg = {"role": "system", "content": f"Bạn là A.I Nexus OS của {CREATOR_NAME}. BẮT BUỘC TRẢ LỜI TIẾNG VIỆT 100%, KHÔNG TIẾNG TRUNG."}
    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[sys_msg] + messages, stream=True)

# --- 8. MÀN HÌNH CHỨC NĂNG ---

def screen_auth():
    apply_ui()
    st.markdown('<h1 class="main-title">🛡️ NEXUS OS GATEWAY</h1>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("TRUY CẬP"):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u; init_user_data(u)
                st.session_state.stage = "MENU"; st.rerun()
            else: st.error("Sai thông tin!")
        st.markdown('</div>', unsafe_allow_html=True)

def screen_social():
    apply_ui()
    user = st.session_state.auth_status
    st.markdown('<h1 class="main-title">🌐 CỘNG ĐỒNG NEXUS</h1>', unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["🔍 TÌM BẠN", "👥 BẠN BÈ", "💬 NHÓM LÀM VIỆC"])
    
    with t1:
        st.markdown("### 💌 Lời mời kết bạn")
        for r in st.session_state.friend_requests.get(user, []):
            col_u, col_a, col_d = st.columns([3, 1, 1])
            col_u.write(f"**{r}** gửi lời mời")
            if col_a.button("✅", key=f"a_{r}"):
                st.session_state.friends[user].append(r)
                st.session_state.friends.setdefault(r, []).append(user)
                st.session_state.friend_requests[user].remove(r); save_github(); st.rerun()
            if col_d.button("❌", key=f"d_{r}"):
                st.session_state.friend_requests[user].remove(r); save_github(); st.rerun()
        
        st.write("---")
        search = st.text_input("Tìm tên người dùng:")
        if search:
            for u in st.session_state.users:
                if search.lower() in u.lower() and u != user:
                    c_n, c_b = st.columns([4, 1])
                    c_n.write(f"👤 **{u}**")
                    if c_b.button("Kết bạn", key=f"add_{u}"):
                        st.session_state.friend_requests.setdefault(u, []).append(user)
                        save_github(); st.success("Đã gửi!"); st.rerun()

    with t2:
        for f in st.session_state.friends.get(user, []):
            c_f, c_m = st.columns([4, 1])
            c_f.write(f"🟢 **{f}**")
            if c_m.button("Nhắn tin", key=f"chat_{f}"):
                st.session_state.current_chat = "_".join(sorted([user, f]))
                st.session_state.p2p_chats.setdefault(st.session_state.current_chat, [])
                st.session_state.stage = "P2P_CHAT"; st.rerun()

    with t3:
        st.markdown("### 🛠️ Tạo nhóm mới")
        g_name = st.text_input("Tên nhóm:")
        g_mode = st.selectbox("Chế độ AI:", ["Bán tự động", "Tự động", "Không AI"])
        if st.button("TẠO NHÓM"):
            gid = f"G_{int(time.time())}"
            st.session_state.groups[gid] = {"name": g_name, "mode": g_mode, "members": [user], "msgs": []}
            save_github(); st.rerun()
        
        st.write("---")
        for gid, ginfo in st.session_state.groups.items():
            if user in ginfo["members"]:
                if st.button(f"📁 {ginfo['name']} ({ginfo['mode']})", key=f"g_{gid}"):
                    st.session_state.current_group = gid; st.session_state.stage = "GROUP_CHAT"; st.rerun()

    if st.button("🔙 VỀ MENU"): st.session_state.stage = "MENU"; st.rerun()

def screen_p2p():
    apply_ui()
    chat_id = st.session_state.current_chat
    msgs = st.session_state.p2p_chats[chat_id]
    st.markdown(f'<h2 class="main-title">🔒 CHAT MÃ HÓA</h2>', unsafe_allow_html=True)
    
    for m in msgs:
        with st.chat_message("user" if m['s'] == st.session_state.auth_status else "assistant"):
            st.write(f"**{m['s']}:** {decrypt_msg(m['t'])}")
    
    if p := st.chat_input("Nhập tin nhắn..."):
        st.session_state.p2p_chats[chat_id].append({"s": st.session_state.auth_status, "t": encrypt_msg(p)})
        save_github(); st.rerun()
    if st.button("🔙 THOÁT"): st.session_state.stage = "SOCIAL"; st.rerun()

def screen_chat():
    apply_ui()
    user = st.session_state.auth_status
    lib = st.session_state.chat_library.setdefault(user, {})
    
    with st.sidebar:
        st.markdown('<h2 class="glow-header">📂 THƯ VIỆN AI</h2>', unsafe_allow_html=True)
        if st.button("➕ CHAT MỚI"): st.session_state.current_chat = None; st.rerun()
        st.write("---")
        for title in list(lib.keys()):
            c_b, c_d = st.columns([0.8, 0.2])
            with c_b:
                if st.button(f"📄 {title}", key=f"b_{title}"): st.session_state.current_chat = title; st.rerun()
            with c_d:
                if st.session_state.confirm_delete == title:
                    if st.button("✔️", key=f"y_{title}"): del lib[title]; st.session_state.confirm_delete = None; save_github(); st.rerun()
                elif st.button("🗑️", key=f"d_{title}"): st.session_state.confirm_delete = title; st.rerun()
        st.write("---")
        if st.button("🏠 MENU"): st.session_state.stage = "MENU"; st.rerun()

    history = lib.get(st.session_state.current_chat, []) if st.session_state.current_chat else []
    for m in history:
        with st.chat_message(m["role"]): st.markdown(decrypt_msg(m["content"]))
    
    if p := st.chat_input("Hỏi AI..."):
        if not st.session_state.current_chat:
            st.session_state.current_chat = p[:20]
            lib[st.session_state.current_chat] = []
        lib[st.session_state.current_chat].append({"role": "user", "content": encrypt_msg(p)})
        st.rerun()

def screen_settings():
    apply_ui()
    st.markdown('<h1 class="main-title">⚙️ CÀI ĐẶT HỆ THỐNG</h1>', unsafe_allow_html=True)
    user = st.session_state.auth_status
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="glow-header">🔐 ĐỔI MẬT KHẨU</h3>', unsafe_allow_html=True)
        old_p = st.text_input("Nhập mật khẩu cũ:", type="password")
        new_p = st.text_input("Nhập mật khẩu mới:", type="password")
        if st.button("XÁC NHẬN ĐỔI"):
            if st.session_state.users[user] == old_p:
                st.session_state.users[user] = new_p; save_github(); st.success("Đã đổi!")
            else: st.error("Sai mật khẩu cũ!")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="glow-header">🖼️ HÌNH NỀN TỰ ĐỘNG</h3>', unsafe_allow_html=True)
        auto = st.toggle("Kích hoạt tự động đổi", st.session_state.theme.get('auto_wallpaper', False))
        st.session_state.theme['auto_wallpaper'] = auto
        if auto:
            st.session_state.theme['wp_interval'] = st.number_input("Thời gian đổi (Phút):", min_value=1, value=st.session_state.theme.get('wp_interval', 1440))
        st.session_state.theme['primary_color'] = st.color_picker("Màu Neon chủ đạo:", st.session_state.theme['primary_color'])
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("💾 LƯU & VỀ MENU", use_container_width=True): save_github(); st.session_state.stage = "MENU"; st.rerun()

# --- 9. ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "MENU":
    apply_ui()
    st.markdown('<h1 class="main-title">🚀 NEXUS CONTROL</h1>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        if st.button("🧠 AI CHAT"): st.session_state.stage = "CHAT"; st.rerun()
    with c2: 
        if st.button("🌐 CỘNG ĐỒNG"): st.session_state.stage = "SOCIAL"; st.rerun()
    with c3: 
        if st.button("⚙️ CÀI ĐẶT"): st.session_state.stage = "SETTINGS"; st.rerun()
    with c4: 
        if st.button("🚪 ĐĂNG XUẤT"): st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()
elif st.session_state.stage == "SOCIAL": screen_social()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "SETTINGS": screen_settings()
elif st.session_state.stage == "P2P_CHAT": screen_p2p()
