# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests
import random
import os
from datetime import datetime

# -------------------- CẤU HÌNH HỆ THỐNG --------------------
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V4900 - ULTIMATE EDITION"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

# Đọc secrets
try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]   # list
    UNSPLASH_ACCESS_KEY = st.secrets.get("UNSPLASH_ACCESS_KEY", "")  # không bắt buộc
except Exception as e:
    st.error(f"Thiếu secrets: {e}")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# -------------------- MÃ HÓA --------------------
def encrypt_msg(text):
    if not text: return text
    encoded = "".join([chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(text)])
    return base64.b64encode(encoded.encode()).decode()

def decrypt_msg(text):
    if not text: return text
    try:
        decoded = base64.b64decode(text.encode()).decode()
        return "".join([chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(decoded)])
    except:
        return text

# -------------------- ĐỒNG BỘ GITHUB --------------------
def load_github():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except Exception as e:
        st.warning(f"Không thể tải từ GitHub: {e}")
    return {}

def save_github():
    data = {
        "users": st.session_state.users,
        "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library,
        "friends": st.session_state.friends,
        "friend_requests": st.session_state.friend_requests,
        "groups": st.session_state.groups,
        "p2p_chats": st.session_state.p2p_chats,
        "agreed_users": st.session_state.agreed_users
    }
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode()).decode()
        payload = {"message": f"Nexus Sync {VERSION}", "content": content}
        if sha: payload["sha"] = sha
        requests.put(url, headers=headers, json=payload)
    except Exception as e:
        st.warning(f"Không thể lưu lên GitHub: {e}")

# -------------------- KHỞI TẠO SESSION STATE --------------------
if 'initialized' not in st.session_state:
    db = load_github()

    st.session_state.users = db.get("users", {"admin": "123"})

    default_theme = {
        "primary_color": "#00f2ff",
        "bg_url": "",
        "auto_wallpaper": False,
        "wp_interval": 1440,               # phút
        "last_wp_update": int(time.time()),
        "naming_threshold": 5,
        "use_unsplash": False,
        "unsplash_topic": "nature"          # chủ đề ảnh
    }
    theme_data = db.get("theme", {})
    for k, v in default_theme.items():
        if k not in theme_data:
            theme_data[k] = v
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
    st.session_state.current_p2p = None
    st.session_state.current_group = None
    st.session_state.confirm_delete = None
    st.session_state.initialized = True

# -------------------- TỰ ĐỘNG ĐỔI HÌNH NỀN --------------------
def update_wallpaper():
    """Cập nhật ảnh nền nếu đã đến thời gian và auto_wallpaper bật."""
    t = st.session_state.theme
    if not t["auto_wallpaper"]:
        return

    now = int(time.time())
    elapsed = now - t["last_wp_update"]
    if elapsed < t["wp_interval"] * 60:
        return

    # Lấy ảnh mới
    new_url = None
    if t["use_unsplash"] and UNSPLASH_ACCESS_KEY:
        # Dùng Unsplash API
        topic = t.get("unsplash_topic", "nature")
        url = f"https://api.unsplash.com/photos/random?query={topic}&orientation=landscape"
        headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                new_url = data["urls"]["regular"]
        except:
            pass
    else:
        # Ảnh mặc định từ nguồn công cộng (ví dụ: picsum)
        new_url = f"https://picsum.photos/1920/1080?random={random.randint(1,100000)}"

    if new_url:
        st.session_state.theme["bg_url"] = new_url
        st.session_state.theme["last_wp_update"] = now
        save_github()

# -------------------- GỬI FILE QUA FILE.IO --------------------
def upload_to_fileio(file_bytes, filename):
    """Upload file lên file.io, trả về link tải (str) hoặc None nếu lỗi."""
    try:
        files = {"file": (filename, file_bytes)}
        response = requests.post("https://file.io", files=files)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["link"]
    except Exception as e:
        st.error(f"Lỗi upload file: {e}")
    return None

# -------------------- GIAO DIỆN NÂNG CAO --------------------
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg_url = t['bg_url'] if t['bg_url'] else ""

    # Xây dựng style nền
    if bg_url:
        bg_style = f"""
            background: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('{bg_url}');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        """
    else:
        bg_style = "background: #0e1117;"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    .stApp {{
        {bg_style}
        font-family: 'Inter', sans-serif;
    }}

    /* Lớp phủ glass động */
    .glass-panel {{
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        border: 1px solid {p_color}66;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        padding: 20px;
    }}

    /* Sidebar và các khung chính */
    [data-testid="stSidebar"], .stTabs {{
        background: rgba(255, 255, 255, 0.25) !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 20px !important;
        border: 1px solid {p_color}66 !important;
        padding: 15px !important;
    }}

    /* Text hiển thị */
    label, .stApp p, .stApp span, h1, h2, h3, h4, h5, h6, .stMarkdown p {{
        color: #ffffff !important;
        font-weight: 600 !important;
        text-shadow: 2px 2px 8px {p_color}AA, 0px 0px 20px {p_color} !important;
    }}

    h1 {{
        font-size: 3rem !important;
        font-weight: 800 !important;
        letter-spacing: 2px;
    }}

    /* Tin nhắn chat */
    [data-testid="stChatMessage"] {{
        background: rgba(255, 255, 255, 0.2) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 20px !important;
        border: 1px solid {p_color}80 !important;
        margin-bottom: 10px !important;
        padding: 10px 15px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }}

    /* Nút bấm */
    .stButton > button {{
        border: 2px solid {p_color} !important;
        background: rgba(255,255,255,0.2) !important;
        backdrop-filter: blur(5px);
        border-radius: 12px !important;
        font-weight: 700 !important;
        color: white !important;
        text-shadow: 1px 1px 2px black;
        transition: 0.3s;
    }}
    .stButton > button:hover {{
        background: {p_color} !important;
        color: black !important;
        border-color: white !important;
    }}

    /* Ẩn header */
    [data-testid="stHeader"] {{ display: none !important; }}
    </style>
    """, unsafe_allow_html=True)

# -------------------- AI CHAT --------------------
def call_ai(messages):
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    system_prompt = {
        "role": "system",
        "content": f"Bạn là NEXUS OS AI, được tạo bởi {CREATOR_NAME}. Luôn trả lời bằng tiếng Việt, thân thiện, chính xác."
    }
    full_messages = [system_prompt] + messages
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=full_messages,
        stream=True
    )

def auto_rename(user, old_title):
    try:
        client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
        first_msg = decrypt_msg(st.session_state.chat_library[user][old_title][0]['content'])
        prompt = f"Đặt tên ngắn gọn (≤5 từ) cho cuộc trò chuyện bắt đầu bằng: '{first_msg}'. Chỉ trả về tên."
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        new_title = res.choices[0].message.content.strip().replace('"', '')
        if new_title:
            st.session_state.chat_library[user][new_title] = st.session_state.chat_library[user].pop(old_title)
            st.session_state.current_chat = new_title
            save_github()
    except Exception as e:
        st.warning(f"Lỗi đặt tên: {e}")

# -------------------- MÀN HÌNH CHAT AI --------------------
def screen_chat():
    apply_ui()
    update_wallpaper()
    user = st.session_state.auth_status
    lib = st.session_state.chat_library.setdefault(user, {})

    with st.sidebar:
        st.markdown(f"<p style='text-align:center;'>✨ NEXUS {VERSION}</p>", unsafe_allow_html=True)
        if st.button("➕ TẠO CHAT MỚI", use_container_width=True):
            st.session_state.current_chat = None
            st.rerun()
        st.write("---")
        for title in list(lib.keys()):
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                if st.button(f"💬 {title[:20]}", key=f"chat_{title}", use_container_width=True):
                    st.session_state.current_chat = title
                    st.rerun()
            with col2:
                if st.session_state.confirm_delete == title:
                    if st.button("✔️", key=f"conf_{title}"):
                        del lib[title]
                        st.session_state.confirm_delete = None
                        if st.session_state.current_chat == title:
                            st.session_state.current_chat = None
                        save_github()
                        st.rerun()
                else:
                    if st.button("🗑️", key=f"del_{title}"):
                        st.session_state.confirm_delete = title
                        st.rerun()
        st.write("---")
        if st.button("🏠 VỀ MENU", use_container_width=True):
            st.session_state.stage = "MENU"
            st.rerun()

    if st.session_state.current_chat is None:
        st.info("👈 Chọn hoặc tạo cuộc trò chuyện để bắt đầu.")
        return

    chat_history = lib.get(st.session_state.current_chat, [])
    for msg in chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(decrypt_msg(msg["content"]))

    if prompt := st.chat_input("Nhập tin nhắn..."):
        chat_history.append({"role": "user", "content": encrypt_msg(prompt)})
        with st.chat_message("user"):
            st.markdown(prompt)

        messages_for_ai = [{"role": m["role"], "content": decrypt_msg(m["content"])} for m in chat_history]

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_res = ""
            try:
                for chunk in call_ai(messages_for_ai):
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        placeholder.markdown(full_res + "▌")
                placeholder.markdown(full_res)
            except Exception as e:
                st.error(f"Lỗi AI: {e}")
                full_res = "Xin lỗi, đã có lỗi."

        chat_history.append({"role": "assistant", "content": encrypt_msg(full_res)})

        if len(chat_history) == st.session_state.theme["naming_threshold"] * 2:
            auto_rename(user, st.session_state.current_chat)

        save_github()
        st.rerun()

# -------------------- CHAT 1-1 (P2P) CÓ GỬI FILE --------------------
def screen_p2p_chat():
    apply_ui()
    update_wallpaper()
    user = st.session_state.auth_status
    friend = st.session_state.current_p2p
    if not friend:
        st.session_state.stage = "SOCIAL"
        st.rerun()

    chat_key = "_".join(sorted([user, friend]))
    p2p_data = st.session_state.p2p_chats.setdefault(chat_key, [])

    st.markdown(f"<h1 class='main-title'>💬 Chat với {friend}</h1>", unsafe_allow_html=True)

    # Hiển thị tin nhắn
    for msg in p2p_data:
        with st.chat_message(msg["role"]):
            content = decrypt_msg(msg["content"])
            # Nếu là tin nhắn file, hiển thị đặc biệt
            if content.startswith("📎 FILE:"):
                st.markdown(content, unsafe_allow_html=True)
            else:
                st.markdown(content)

    # Khu vực nhập tin nhắn và gửi file
    with st.container():
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            text_input = st.chat_input("Nhập tin nhắn...")
        with col2:
            # Nút gửi file (mở rộng)
            with st.popover("📎 Gửi file"):
                uploaded_file = st.file_uploader("Chọn file", type=None, key=f"upload_{chat_key}")
                if uploaded_file and st.button("Gửi file", key=f"sendfile_{chat_key}"):
                    file_bytes = uploaded_file.getvalue()
                    filename = uploaded_file.name
                    size_kb = len(file_bytes) // 1024
                    with st.spinner("Đang tải lên file.io..."):
                        link = upload_to_fileio(file_bytes, filename)
                    if link:
                        msg_content = f"📎 FILE: **{filename}** ({size_kb} KB) - [Tải về]({link}) (tự huỷ sau 1 lần tải)"
                        encrypted = encrypt_msg(msg_content)
                        p2p_data.append({"role": user, "content": encrypted})
                        save_github()
                        st.rerun()
                    else:
                        st.error("Không thể tải file lên, thử lại sau.")

    if text_input:
        encrypted = encrypt_msg(text_input)
        p2p_data.append({"role": user, "content": encrypted})
        save_github()
        st.rerun()

    if st.button("🔙 Quay lại Social"):
        st.session_state.stage = "SOCIAL"
        st.rerun()

# -------------------- CHAT NHÓM CÓ GỬI FILE --------------------
def screen_group_chat():
    apply_ui()
    update_wallpaper()
    user = st.session_state.auth_status
    gid = st.session_state.current_group
    group = st.session_state.groups.get(gid)
    if not group or user not in group["members"]:
        st.error("Không thể truy cập nhóm này.")
        st.session_state.stage = "SOCIAL"
        st.rerun()

    st.markdown(f"<h1 class='main-title'>👪 {group['name']}</h1>", unsafe_allow_html=True)

    # Hiển thị tin nhắn
    for msg in group.get("messages", []):
        with st.chat_message(msg["role"]):
            content = decrypt_msg(msg["content"])
            if content.startswith("📎 FILE:"):
                st.markdown(content, unsafe_allow_html=True)
            else:
                st.markdown(content)

    # Khu vực nhập tin nhắn và gửi file
    with st.container():
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            text_input = st.chat_input("Nhập tin nhắn nhóm...")
        with col2:
            with st.popover("📎 Gửi file"):
                uploaded_file = st.file_uploader("Chọn file", type=None, key=f"upload_group_{gid}")
                if uploaded_file and st.button("Gửi file", key=f"sendfile_group_{gid}"):
                    file_bytes = uploaded_file.getvalue()
                    filename = uploaded_file.name
                    size_kb = len(file_bytes) // 1024
                    with st.spinner("Đang tải lên file.io..."):
                        link = upload_to_fileio(file_bytes, filename)
                    if link:
                        msg_content = f"📎 FILE: **{filename}** ({size_kb} KB) - [Tải về]({link})"
                        encrypted = encrypt_msg(msg_content)
                        group.setdefault("messages", []).append({"role": user, "content": encrypted})
                        save_github()
                        st.rerun()
                    else:
                        st.error("Không thể tải file lên, thử lại sau.")

    if text_input:
        encrypted = encrypt_msg(text_input)
        group.setdefault("messages", []).append({"role": user, "content": encrypted})
        save_github()
        st.rerun()

    if st.button("🔙 Quay lại Social"):
        st.session_state.stage = "SOCIAL"
        st.rerun()

# -------------------- MÀN HÌNH SOCIAL --------------------
def screen_social():
    apply_ui()
    update_wallpaper()
    user = st.session_state.auth_status
    st.markdown('<h1 class="main-title">🌐 NEXUS SOCIAL</h1>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👥 Bạn bè", "📨 Lời mời", "👪 Nhóm"])

    with tab1:
        st.subheader("Danh sách bạn bè")
        friends_list = st.session_state.friends.get(user, [])
        if not friends_list:
            st.info("Bạn chưa có bạn bè nào.")
        else:
            for friend in friends_list:
                col1, col2 = st.columns([3,1])
                with col1:
                    st.write(f"• {friend}")
                with col2:
                    if st.button("💬 Chat", key=f"chat_{friend}"):
                        st.session_state.current_p2p = friend
                        st.session_state.stage = "P2P_CHAT"
                        st.rerun()

        st.markdown("---")
        st.subheader("Gửi lời mời kết bạn")
        all_users = list(st.session_state.users.keys())
        potential = [u for u in all_users if u != user and u not in friends_list]
        if potential:
            selected = st.selectbox("Chọn người dùng", potential)
            if st.button("Gửi lời mời"):
                st.session_state.friend_requests.setdefault(selected, []).append(user)
                save_github()
                st.success(f"Đã gửi lời mời đến {selected}")
        else:
            st.info("Không có ai để kết bạn.")

    with tab2:
        st.subheader("Lời mời kết bạn")
        requests_list = st.session_state.friend_requests.get(user, [])
        if not requests_list:
            st.info("Không có lời mời nào.")
        else:
            for req in requests_list:
                col1, col2, col3 = st.columns([3,1,1])
                with col1:
                    st.write(f"📩 {req}")
                with col2:
                    if st.button("✅ Chấp nhận", key=f"acc_{req}"):
                        st.session_state.friends.setdefault(user, []).append(req)
                        st.session_state.friends.setdefault(req, []).append(user)
                        st.session_state.friend_requests[user].remove(req)
                        save_github()
                        st.rerun()
                with col3:
                    if st.button("❌ Từ chối", key=f"rej_{req}"):
                        st.session_state.friend_requests[user].remove(req)
                        save_github()
                        st.rerun()

    with tab3:
        st.subheader("Nhóm của tôi")
        my_groups = []
        for gid, ginfo in st.session_state.groups.items():
            if user in ginfo.get("members", []):
                my_groups.append((gid, ginfo["name"]))
        if not my_groups:
            st.info("Bạn chưa tham gia nhóm nào.")
        else:
            for gid, gname in my_groups:
                col1, col2 = st.columns([3,1])
                with col1:
                    st.write(f"• {gname}")
                with col2:
                    if st.button("💬 Vào nhóm", key=f"grp_{gid}"):
                        st.session_state.current_group = gid
                        st.session_state.stage = "GROUP_CHAT"
                        st.rerun()

        st.markdown("---")
        st.subheader("Tạo nhóm mới")
        new_group_name = st.text_input("Tên nhóm")
        if st.button("Tạo nhóm") and new_group_name:
            gid = f"group_{int(time.time())}"
            st.session_state.groups[gid] = {
                "name": new_group_name,
                "members": [user],
                "messages": []
            }
            save_github()
            st.success("Đã tạo nhóm!")
            st.rerun()

    if st.button("🏠 VỀ MENU"):
        st.session_state.stage = "MENU"
        st.rerun()

# -------------------- MÀN HÌNH CÀI ĐẶT --------------------
def screen_settings():
    apply_ui()
    update_wallpaper()
    user = st.session_state.auth_status
    st.markdown('<h1 class="main-title">⚙️ CÀI ĐẶT</h1>', unsafe_allow_html=True)

    # Đảm bảo giá trị hợp lệ trước khi hiển thị form
    current_interval = st.session_state.theme["wp_interval"]
    if current_interval < 10:
        current_interval = 10

    with st.form("settings_form"):
        st.subheader("Giao diện")
        primary_color = st.color_picker("Màu chủ đạo", value=st.session_state.theme["primary_color"])
        bg_url = st.text_input("URL ảnh nền (bỏ trống nếu dùng tự động)", value=st.session_state.theme["bg_url"])

        st.subheader("Tự động đổi hình nền")
        auto_wp = st.checkbox("Bật tự động đổi ảnh nền", value=st.session_state.theme["auto_wallpaper"])
        use_unsplash = st.checkbox("Dùng Unsplash (cần access key)", value=st.session_state.theme.get("use_unsplash", False))
        unsplash_topic = st.text_input("Chủ đề ảnh (ví dụ: nature, city)", value=st.session_state.theme.get("unsplash_topic", "nature"))
        wp_interval = st.number_input("Thời gian đổi (phút)", min_value=10, value=current_interval, step=5)

        st.subheader("Tự động đặt tên chat")
        naming_threshold = st.number_input("Số cặp tin nhắn để đặt tên lại", min_value=1, max_value=20, value=st.session_state.theme["naming_threshold"])

        st.subheader("Bảo mật")
        new_pass = st.text_input("Mật khẩu mới (để trống nếu không đổi)", type="password")
        confirm_pass = st.text_input("Xác nhận mật khẩu mới", type="password")

        submitted = st.form_submit_button("💾 LƯU CÀI ĐẶT")
        if submitted:
            st.session_state.theme["primary_color"] = primary_color
            st.session_state.theme["bg_url"] = bg_url
            st.session_state.theme["auto_wallpaper"] = auto_wp
            st.session_state.theme["use_unsplash"] = use_unsplash
            st.session_state.theme["unsplash_topic"] = unsplash_topic
            st.session_state.theme["wp_interval"] = wp_interval
            st.session_state.theme["naming_threshold"] = naming_threshold

            if new_pass and new_pass == confirm_pass:
                st.session_state.users[user] = new_pass
                st.success("Đã đổi mật khẩu.")
            elif new_pass:
                st.error("Mật khẩu xác nhận không khớp.")

            save_github()
            st.success("Đã lưu cài đặt!")
            st.rerun()

    if st.button("📜 Xem Điều khoản"):
        st.session_state.stage = "TERMS"
        st.rerun()

    if st.button("🏠 VỀ MENU"):
        st.session_state.stage = "MENU"
        st.rerun()

# -------------------- MÀN HÌNH ĐIỀU KHOẢN --------------------
def screen_terms():
    apply_ui()
    st.markdown('<h1 class="main-title">📜 ĐIỀU KHOẢN</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div class="glass-panel">
    1. <b>Bảo mật:</b> Dữ liệu được mã hóa E2E trước khi lưu.<br>
    2. <b>Sáng tạo:</b> NEXUS OS được phát triển bởi Lê Trần Thiên Phát.<br>
    3. <b>Trách nhiệm:</b> Người dùng tự chịu trách nhiệm nội dung.<br>
    4. <b>File:</b> File được upload qua file.io, tự động xoá sau khi tải.<br>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.auth_status not in st.session_state.agreed_users:
        if st.button("Tôi đồng ý"):
            st.session_state.agreed_users.append(st.session_state.auth_status)
            save_github()
            st.session_state.stage = "MENU"
            st.rerun()
    else:
        if st.button("VỀ MENU"):
            st.session_state.stage = "MENU"
            st.rerun()

# -------------------- MÀN HÌNH ĐĂNG NHẬP --------------------
def screen_auth():
    apply_ui()
    st.markdown('<h1 class="main-title">🛡️ NEXUS OS</h1>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container():
            st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
            username = st.text_input("Tài khoản")
            password = st.text_input("Mật khẩu", type="password")
            if st.button("VÀO HỆ THỐNG", use_container_width=True):
                if username in st.session_state.users and st.session_state.users[username] == password:
                    st.session_state.auth_status = username
                    if username not in st.session_state.agreed_users:
                        st.session_state.stage = "TERMS"
                    else:
                        st.session_state.stage = "MENU"
                    st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu")
            st.markdown('</div>', unsafe_allow_html=True)

# -------------------- MÀN HÌNH MENU --------------------
def screen_menu():
    apply_ui()
    update_wallpaper()
    st.markdown(f'<h1 class="main-title">🚀 NEXUS CENTER</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center;">Xin chào, <b>{st.session_state.auth_status}</b> | {VERSION}</p>', unsafe_allow_html=True)

    cols = st.columns(5)
    if cols[0].button("🧠 AI CHAT"): st.session_state.stage = "CHAT"; st.rerun()
    if cols[1].button("🌐 SOCIAL"): st.session_state.stage = "SOCIAL"; st.rerun()
    if cols[2].button("⚙️ CÀI ĐẶT"): st.session_state.stage = "SETTINGS"; st.rerun()
    if cols[3].button("📜 TERMS"): st.session_state.stage = "TERMS"; st.rerun()
    if cols[4].button("🚪 THOÁT"):
        st.session_state.auth_status = None
        st.session_state.stage = "AUTH"
        st.rerun()

# -------------------- ĐIỀU HƯỚNG CHÍNH --------------------
def main():
    if st.session_state.stage == "AUTH":
        screen_auth()
    elif st.session_state.stage == "MENU":
        screen_menu()
    elif st.session_state.stage == "CHAT":
        screen_chat()
    elif st.session_state.stage == "SOCIAL":
        screen_social()
    elif st.session_state.stage == "P2P_CHAT":
        screen_p2p_chat()
    elif st.session_state.stage == "GROUP_CHAT":
        screen_group_chat()
    elif st.session_state.stage == "SETTINGS":
        screen_settings()
    elif st.session_state.stage == "TERMS":
        screen_terms()

if __name__ == "__main__":
    main()
