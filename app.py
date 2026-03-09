# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests
from datetime import datetime

# --- [1] CẤU HÌNH HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V4800 - SOCIAL EDITION"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("❌ Thiếu cấu hình Secrets!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- [2] CÔNG CỤ MÃ HÓA & DỮ LIỆU ---
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
        "p2p_chats": st.session_state.p2p_chats
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

# --- [3] KHỞI TẠO SESSION ---
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123", "phat": "2002"})
    st.session_state.theme = db.get("theme", {"primary_color": "#00f2ff", "bg_url": ""})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.friends = db.get("friends", {}) # {user: [friend1, friend2]}
    st.session_state.friend_requests = db.get("friend_requests", {}) # {to_user: [from_user]}
    st.session_state.groups = db.get("groups", {"Chung": []}) # {group_name: [messages]}
    st.session_state.p2p_chats = db.get("p2p_chats", {}) # {"user1-user2": [messages]}
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.initialized = True

def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg = f"url('{t['bg_url']}')" if t['bg_url'] else "#0e1117"
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg} no-repeat center fixed; background-size: cover; }}
    [data-testid="stSidebar"] {{ background: rgba(0,0,0,0.7) !important; backdrop-filter: blur(10px); }}
    h1, h2, h3, p, label {{ color: white !important; text-shadow: 1px 1px 10px {p_color}; }}
    .stButton > button {{ border: 1px solid {p_color}; background: rgba(0,0,0,0.5); color: white; border-radius: 8px; }}
    </style>
    """, unsafe_allow_html=True)

# --- [4] MÀN HÌNH SOCIAL (CỘNG ĐỒNG) ---
def screen_social():
    apply_ui()
    me = st.session_state.auth_status
    st.title("🌐 NEXUS SOCIAL NETWORK")
    
    tab1, tab2, tab3 = st.tabs(["👥 Bạn bè", "💬 Tin nhắn nhóm", "➕ Tìm kiếm"])
    
    with tab1:
        st.subheader("Danh sách bạn bè")
        my_friends = st.session_state.friends.get(me, [])
        if not my_friends:
            st.info("Bạn chưa có bạn bè nào. Hãy kết nối thêm!")
        else:
            for f in my_friends:
                c1, c2 = st.columns([0.8, 0.2])
                c1.write(f"👤 **{f}**")
                if c2.button("Chat", key=f"chat_{f}"):
                    # Tạo key chat 1-1 duy nhất (sắp xếp tên để đồng nhất)
                    chat_id = "-".join(sorted([me, f]))
                    st.session_state.current_p2p = chat_id
                    st.session_state.stage = "P2P_CHAT"
                    st.rerun()

    with tab2:
        st.subheader("Phòng chat cộng đồng")
        for g_name in st.session_state.groups.keys():
            if st.button(f"🚪 Tham gia {g_name}", use_container_width=True):
                st.session_state.current_group = g_name
                st.session_state.stage = "GROUP_CHAT"
                st.rerun()

    with tab3:
        st.subheader("Gửi lời mời kết bạn")
        other_user = st.text_input("Nhập tên tài khoản muốn kết bạn")
        if st.button("Gửi lời mời"):
            if other_user in st.session_state.users and other_user != me:
                reqs = st.session_state.friend_requests.setdefault(other_user, [])
                if me not in reqs:
                    reqs.append(me)
                    save_github()
                    st.success(f"Đã gửi lời mời tới {other_user}!")
                else: st.warning("Đã gửi lời mời trước đó rồi.")
            else: st.error("Người dùng không tồn tại.")
        
        st.divider()
        st.subheader("Lời mời đã nhận")
        my_reqs = st.session_state.friend_requests.get(me, [])
        for r in my_reqs:
            col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
            col1.write(f"📩 **{r}** muốn kết bạn.")
            if col2.button("Đồng ý", key=f"acc_{r}"):
                st.session_state.friends.setdefault(me, []).append(r)
                st.session_state.friends.setdefault(r, []).append(me)
                st.session_state.friend_requests[me].remove(r)
                save_github()
                st.rerun()
            if col3.button("Từ chối", key=f"rej_{r}"):
                st.session_state.friend_requests[me].remove(r)
                save_github()
                st.rerun()

    if st.button("🏠 QUAY LẠI MENU"):
        st.session_state.stage = "MENU"
        st.rerun()

# --- [5] MÀN HÌNH CHAT NHÓM ---
def screen_group_chat():
    apply_ui()
    g_name = st.session_state.current_group
    st.title(f"👥 Nhóm: {g_name}")
    
    messages = st.session_state.groups.get(g_name, [])
    
    # Hiển thị tin nhắn
    chat_container = st.container(height=400)
    with chat_container:
        for m in messages:
            with st.chat_message("user" if m['user'] == st.session_state.auth_status else "assistant"):
                st.write(f"**{m['user']}**: {decrypt_msg(m['text'])}")

    if p := st.chat_input("Nhập tin nhắn nhóm..."):
        new_msg = {"user": st.session_state.auth_status, "text": encrypt_msg(p), "time": str(datetime.now())}
        st.session_state.groups[g_name].append(new_msg)
        save_github()
        st.rerun()

    if st.button("⬅️ RỜI PHÒNG"):
        st.session_state.stage = "SOCIAL"
        st.rerun()

# --- [6] MAIN ROUTER (Đã bổ sung các Case) ---
if st.session_state.stage == "AUTH":
    apply_ui()
    st.title("🔐 NEXUS LOGIN")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        if u in st.session_state.users and st.session_state.users[u] == p:
            st.session_state.auth_status = u
            st.session_state.stage = "MENU"
            st.rerun()

elif st.session_state.stage == "MENU":
    apply_ui()
    st.title(f"🚀 NEXUS OS - Chào {st.session_state.auth_status}")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🧠 AI CHAT"): st.session_state.stage = "CHAT"; st.rerun()
    if c2.button("🌐 SOCIAL"): st.session_state.stage = "SOCIAL"; st.rerun()
    if c3.button("⚙️ SETTINGS"): st.session_state.stage = "SETTINGS"; st.rerun()
    if c4.button("🚪 LOGOUT"): 
        st.session_state.auth_status = None
        st.session_state.stage = "AUTH"
        st.rerun()

elif st.session_state.stage == "SOCIAL":
    screen_social()

elif st.session_state.stage == "GROUP_CHAT":
    screen_group_chat()

elif st.session_state.stage == "CHAT":
    # (Giữ nguyên hàm screen_chat từ bản trước của bạn)
    import app_chat # Giả sử bạn tách hoặc lồng code chat vào đây
    # Để đơn giản, tôi tạm thời gọi quay lại menu nếu chưa copy hàm chat vào
    if st.button("Quay lại"): st.session_state.stage = "MENU"; st.rerun()

elif st.session_state.stage == "SETTINGS":
    apply_ui()
    st.subheader("Cài đặt hệ thống")
    t = st.session_state.theme
    new_color = st.color_picker("Màu Neon", t['primary_color'])
    new_bg = st.text_input("Link ảnh nền", t['bg_url'])
    if st.button("Lưu cấu hình"):
        st.session_state.theme = {"primary_color": new_color, "bg_url": new_bg}
        save_github()
        st.success("Đã lưu!")
    if st.button("Quay lại"): st.session_state.stage = "MENU"; st.rerun()
