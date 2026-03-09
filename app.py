# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V4800 - ULTIMATE"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("❌ Thiếu Secrets trên Streamlit Cloud!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- [2] CÔNG CỤ MÃ HÓA & LOGIC ---
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
    data = {
        "users": st.session_state.users, "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library, "friends": st.session_state.friends,
        "friend_requests": st.session_state.friend_requests, "groups": st.session_state.groups,
        "access_logs": st.session_state.get("access_logs", [])
    }
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": f"Nexus Update {datetime.now()}", "content": content}
        if sha: payload["sha"] = sha
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- [3] KHỞI TẠO DỮ LIỆU ---
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123", "Thiên Phát": "2002"})
    st.session_state.theme = db.get("theme", {"primary_color": "#00f2ff", "bg_url": "", "ai_temp": 0.7})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.friends = db.get("friends", {})
    st.session_state.friend_requests = db.get("friend_requests", {})
    st.session_state.groups = db.get("groups", {"Chung": []})
    st.session_state.access_logs = db.get("access_logs", [])
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None
    st.session_state.initialized = True

def log_access(user):
    # Lấy thông tin thiết bị từ headers của Streamlit
    headers = st.context.headers
    user_agent = headers.get("User-Agent", "Unknown Device")
    log_entry = {
        "user": user,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "device": user_agent
    }
    # Chỉ giữ log trong 14 ngày
    st.session_state.access_logs.append(log_entry)
    cutoff = datetime.now() - timedelta(days=14)
    st.session_state.access_logs = [l for l in st.session_state.access_logs 
                                   if datetime.strptime(l['time'], "%Y-%m-%d %H:%M:%S") > cutoff]
    save_github()

def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg = f"url('{t['bg_url']}')" if t['bg_url'] else "#0e1117"
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg} no-repeat center fixed; background-size: cover; }}
    .stChatFloatingInputContainer {{ background: rgba(0,0,0,0) !important; }}
    h1, h2, h3, p, label {{ color: white !important; text-shadow: 1px 1px 10px {p_color}; }}
    .stButton > button {{ border: 1px solid {p_color}; background: rgba(0,0,0,0.5); color: white; border-radius: 8px; }}
    [data-testid="stSidebar"] {{ background: rgba(0,0,0,0.8) !important; backdrop-filter: blur(10px); }}
    </style>
    """, unsafe_allow_html=True)

# --- [4] MÀN HÌNH CHỨC NĂNG ---

def screen_chat():
    apply_ui()
    user = st.session_state.auth_status
    lib = st.session_state.chat_library.setdefault(user, {})
    
    with st.sidebar:
        st.header("🧠 AI CHAT")
        if st.button("➕ PHIÊN MỚI", use_container_width=True):
            st.session_state.current_chat = None
            st.rerun()
        
        st.divider()
        for t in list(lib.keys()):
            col_t, col_d = st.columns([0.8, 0.2])
            if col_t.button(f"💬 {t[:15]}", key=f"sel_{t}", use_container_width=True):
                st.session_state.current_chat = t
                st.rerun()
            if col_d.button("🗑️", key=f"del_{t}"):
                del lib[t]
                save_github()
                st.rerun()
        
        if st.button("🏠 MENU CHÍNH", use_container_width=True):
            st.session_state.stage = "MENU"; st.rerun()

    chat_id = st.session_state.current_chat
    if chat_id:
        for m in lib[chat_id]:
            with st.chat_message(m["role"]): st.write(decrypt_msg(m["content"]))

    if p := st.chat_input("Hỏi AI Nexus..."):
        if not chat_id:
            chat_id = f"Hội thoại {datetime.now().strftime('%H:%M')}"
            st.session_state.current_chat = chat_id
            lib[chat_id] = []
        
        lib[chat_id].append({"role": "user", "content": encrypt_msg(p)})
        st.rerun() # Refresh để AI trả lời

def screen_admin():
    apply_ui()
    st.title("🛡️ QUẢN TRỊ HỆ THỐNG")
    st.write("### Lịch sử truy cập (14 ngày qua)")
    
    if not st.session_state.access_logs:
        st.info("Chưa có dữ liệu truy cập.")
    else:
        for log in reversed(st.session_state.access_logs):
            with st.expander(f"👤 {log['user']} - 🕒 {log['time']}"):
                st.code(log['device'], language="text")
    
    if st.button("🏠 QUAY LẠI"):
        st.session_state.stage = "MENU"; st.rerun()

def screen_settings():
    apply_ui()
    st.title("⚙️ CÀI ĐẶT NÂNG CAO")
    t = st.session_state.theme
    
    new_bg = st.text_input("Link ảnh nền (URL)", t['bg_url'])
    new_color = st.color_picker("Màu chủ đạo Neon", t['primary_color'])
    new_temp = st.slider("Độ sáng tạo của AI (Temperature)", 0.0, 1.0, t.get('ai_temp', 0.7))
    
    if st.button("LƯU CẤU HÌNH"):
        st.session_state.theme.update({"bg_url": new_bg, "primary_color": new_color, "ai_temp": new_temp})
        save_github()
        st.success("Hệ thống đã cập nhật!")
        
    if st.button("🧹 XÓA LỊCH SỬ CHAT CỦA TÔI"):
        st.session_state.chat_library[st.session_state.auth_status] = {}
        save_github()
        st.warning("Đã xóa sạch lịch sử chat!")

    if st.button("🏠 QUAY LẠI"):
        st.session_state.stage = "MENU"; st.rerun()

# --- [5] ĐIỀU HƯỚNG CHÍNH ---
if st.session_state.stage == "AUTH":
    apply_ui()
    st.title("🔐 NEXUS OS LOGIN")
    u = st.text_input("Tên chủ nhân")
    p = st.text_input("Mật khẩu", type="password")
    if st.button("KHỞI CHẠY"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.auth_status = u
            st.session_state.stage = "MENU"
            log_access(u)
            st.rerun()
        else: st.error("Sai thông tin định danh!")

elif st.session_state.stage == "MENU":
    apply_ui()
    st.title(f"🚀 NEXUS CENTER - CHÀO {st.session_state.auth_status.upper()}")
    
    # Nút Admin đặc biệt
    if st.session_state.auth_status.lower() == "thiên phát":
        if st.button("🛡️ ADMIN PANEL", use_container_width=True):
            st.session_state.stage = "ADMIN"; st.rerun()
            
    cols = st.columns(2)
    if cols[0].button("🧠 TRÍ TUỆ NHÂN TẠO", use_container_width=True):
        st.session_state.stage = "CHAT"; st.rerun()
    if cols[1].button("⚙️ CÀI ĐẶT HỆ THỐNG", use_container_width=True):
        st.session_state.stage = "SETTINGS"; st.rerun()
    
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True):
        st.session_state.auth_status = None
        st.session_state.stage = "AUTH"; st.rerun()

elif st.session_state.stage == "CHAT":
    screen_chat()
elif st.session_state.stage == "ADMIN":
    screen_admin()
elif st.session_state.stage == "SETTINGS":
    screen_settings()
