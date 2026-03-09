# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests
from datetime import datetime

# --- [1] CẤU HÌNH & THÔNG TIN ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V4800 - STABLE"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

# Kiểm tra Secrets để tránh crash
try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except Exception:
    st.error("❌ Thiếu cấu hình Secrets trên Streamlit Cloud (GH_TOKEN, GH_REPO, GROQ_KEYS)!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- [2] CÔNG CỤ MÃ HÓA ---
def encrypt_msg(text):
    if not text: return ""
    encoded = "".join([chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(text)])
    return base64.b64encode(encoded.encode()).decode()

def decrypt_msg(text):
    if not text: return ""
    try:
        decoded = base64.b64decode(text.encode()).decode()
        return "".join([chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(decoded)])
    except: return text

# --- [3] ĐỒNG BỘ GITHUB ---
def load_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            return json.loads(content)
    except: pass
    return {}

def save_github():
    data = {
        "users": st.session_state.users, "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library, "friends": st.session_state.friends,
        "friend_requests": st.session_state.friend_requests, "groups": st.session_state.groups,
        "p2p_chats": st.session_state.p2p_chats, "agreed_users": st.session_state.agreed_users
    }
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": f"Nexus Sync {VERSION}", "content": content}
        if sha: payload["sha"] = sha
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- [4] KHỞI TẠO HỆ THỐNG (SESSION STATE) ---
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123", "phat": "2002"})
    t_db = db.get("theme", {})
    st.session_state.theme = {
        "primary_color": t_db.get("primary_color", "#00f2ff"),
        "bg_url": t_db.get("bg_url", "https://wallpaperaccess.com/full/1567831.jpg"),
        "naming_threshold": t_db.get("naming_threshold", 3)
    }
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.friends = db.get("friends", {})
    st.session_state.friend_requests = db.get("friend_requests", {})
    st.session_state.groups = db.get("groups", {})
    st.session_state.p2p_chats = db.get("p2p_chats", {})
    st.session_state.agreed_users = db.get("agreed_users", [])
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None
    st.session_state.initialized = True

# --- [5] UI ENGINE ---
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg = f"url('{t['bg_url']}')" if t['bg_url'] else "#0e1117"
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg} no-repeat center fixed; background-size: cover; }}
    /* Glassmorphism cho Card */
    .glass {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.2);
        padding: 20px;
        color: white !important;
    }}
    h1, h2, h3, p, label, span {{
        color: white !important;
        text-shadow: 2px 2px 10px {p_color};
        font-weight: 800 !important;
    }}
    .stButton > button {{
        background: rgba(255,255,255,0.2) !important;
        color: white !important;
        border: 2px solid {p_color} !important;
        border-radius: 10px;
        transition: 0.3s;
    }}
    .stButton > button:hover {{ transform: scale(1.05); background: {p_color} !important; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [6] AI CORE ---
def call_ai(msgs):
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    sys_prompt = {"role": "system", "content": f"Bạn là NEXUS OS. Chủ nhân là {CREATOR_NAME}. Trả lời ngắn gọn, ngầu."}
    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[sys_prompt]+msgs, stream=True)

# --- [7] CÁC MÀN HÌNH (SCREENS) ---

def screen_auth():
    apply_ui()
    st.markdown("<center><h1>🛡️ NEXUS LOGIN</h1></center>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        u = st.text_input("Tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("XÁC THỰC", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU"
                st.rerun()
            else: st.error("Sai thông tin!")

def screen_menu():
    apply_ui()
    st.markdown(f"<h1>🚀 CHÀO {st.session_state.auth_status.upper()}</h1>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🧠 AI CHAT", use_container_width=True): st.session_state.stage = "CHAT"; st.rerun()
    if c2.button("🌐 SOCIAL", use_container_width=True): st.session_state.stage = "SOCIAL"; st.rerun()
    if c3.button("⚙️ SETTINGS", use_container_width=True): st.session_state.stage = "SETTINGS"; st.rerun()
    if c4.button("🚪 EXIT", use_container_width=True): 
        st.session_state.auth_status = None
        st.session_state.stage = "AUTH"
        st.rerun()

def screen_chat():
    apply_ui()
    user = st.session_state.auth_status
    lib = st.session_state.chat_library.setdefault(user, {})
    
    with st.sidebar:
        st.write("### 📄 LỊCH SỬ CHAT")
        if st.button("➕ CHAT MỚI", use_container_width=True): 
            st.session_state.current_chat = None
            st.rerun()
        for t in list(lib.keys()):
            if st.button(f"▪️ {t[:20]}", key=f"btn_{t}", use_container_width=True):
                st.session_state.current_chat = t
                st.rerun()
        if st.button("🏠 VỀ MENU", use_container_width=True): 
            st.session_state.stage = "MENU"
            st.rerun()

    st.subheader(f"💬 {st.session_state.current_chat or 'Phiên hội thoại mới'}")
    
    # Hiển thị chat
    chat_key = st.session_state.current_chat
    if chat_key and chat_key in lib:
        for m in lib[chat_key]:
            with st.chat_message(m["role"]): st.write(decrypt_msg(m["content"]))

    if p := st.chat_input("Nhập lệnh cho NEXUS..."):
        if not chat_key:
            chat_key = f"Chat {datetime.now().strftime('%H:%M:%S')}"
            st.session_state.current_chat = chat_key
            lib[chat_key] = []
        
        # User side
        lib[chat_key].append({"role": "user", "content": encrypt_msg(p)})
        with st.chat_message("user"): st.write(p)
        
        # AI side
        with st.chat_message("assistant"):
            res_box = st.empty(); full_res = ""
            msgs = [{"role": m["role"], "content": decrypt_msg(m["content"])} for m in lib[chat_key]]
            for chunk in call_ai(msgs):
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    res_box.markdown(full_res + "▌")
            res_box.markdown(full_res)
        
        lib[chat_key].append({"role": "assistant", "content": encrypt_msg(full_res)})
        save_github()
        st.rerun()

def screen_settings():
    apply_ui()
    st.write("## ⚙️ CÀI ĐẶT HỆ THỐNG")
    t = st.session_state.theme
    new_bg = st.text_input("Link ảnh nền (URL)", value=t['bg_url'])
    new_color = st.color_picker("Màu chủ đạo Neon", value=t['primary_color'])
    
    if st.button("LƯU THAY ĐỔI"):
        st.session_state.theme['bg_url'] = new_bg
        st.session_state.theme['primary_color'] = new_color
        save_github()
        st.success("Đã cập nhật!")
        time.sleep(1)
        st.rerun()
    
    if st.button("🏠 QUAY LẠI"):
        st.session_state.stage = "MENU"
        st.rerun()

def screen_social():
    apply_ui()
    st.write("## 🌐 NEXUS SOCIAL (BETA)")
    st.info("Tính năng kết nối đang được bảo trì cho phiên bản V4800.")
    if st.button("🏠 QUAY LẠI"):
        st.session_state.stage = "MENU"
        st.rerun()

# --- [8] MAIN ROUTER (BỘ ĐIỀU HƯỚNG CHÍNH) ---
# Quan trọng: Không để trống bất kỳ trường hợp nào để tránh màn hình trắng
if st.session_state.stage == "AUTH":
    screen_auth()
elif st.session_state.stage == "MENU":
    screen_menu()
elif st.session_state.stage == "CHAT":
    screen_chat()
elif st.session_state.stage == "SETTINGS":
    screen_settings()
elif st.session_state.stage == "SOCIAL":
    screen_social()
else:
    # Trường hợp dự phòng nếu stage bị lỗi
    st.session_state.stage = "AUTH"
    st.rerun()
