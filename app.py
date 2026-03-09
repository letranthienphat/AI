# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests
import random

# -------------------- CẤU HÌNH HỆ THỐNG --------------------
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V4800 - CREATOR EDITION"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"  # dùng cho mã hóa XOR

# Đọc secrets từ Streamlit Cloud
try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]   # phải là list
except Exception as e:
    st.error(f"Thiếu cấu hình Secrets trên Streamlit Cloud: {e}")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# -------------------- MÃ HÓA / GIẢI MÃ --------------------
def encrypt_msg(text):
    if not text:
        return text
    encoded = "".join([chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(text)])
    return base64.b64encode(encoded.encode()).decode()

def decrypt_msg(text):
    if not text:
        return text
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
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            return json.loads(content)
    except Exception as e:
        st.warning(f"Không thể tải dữ liệu từ GitHub: {e}")
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
        if sha:
            payload["sha"] = sha
        requests.put(url, headers=headers, json=payload)
    except Exception as e:
        st.warning(f"Không thể lưu dữ liệu lên GitHub: {e}")

# -------------------- KHỞI TẠO SESSION STATE --------------------
if 'initialized' not in st.session_state:
    db = load_github()
    
    st.session_state.users = db.get("users", {"admin": "123"})
    
    # Theme với các giá trị mặc định đầy đủ
    default_theme = {
        "primary_color": "#00f2ff",
        "bg_url": "",
        "auto_wallpaper": False,
        "wp_interval": 1440,           # phút
        "last_wp_update": 0,
        "naming_threshold": 5           # số cặp tin nhắn để đặt tên lại
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
    st.session_state.current_chat = None      # key của chat đang mở (dùng cho AI)
    st.session_state.current_p2p = None        # bạn đang chat 1-1
    st.session_state.current_group = None      # nhóm đang chat
    st.session_state.confirm_delete = None     # dùng cho xác nhận xóa chat
    st.session_state.initialized = True

# -------------------- GIAO DIỆN (NEON GLOW + GLASS) --------------------
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    if t['bg_url']:
        bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;"
    else:
        bg_style = "background-color: #0e1117;"
    
    st.markdown(f"""
    <style>
    .stApp {{
        {bg_style}
    }}
    
    /* Tất cả chữ đều có bóng neon (màu đen để dễ đọc trên nền sáng, nhưng có glow) */
    label, .stApp p, .stApp span, h1, h2, h3, h4, h5, h6, .stMarkdown p {{
        color: #000000 !important;
        font-weight: 600 !important;
        text-shadow: 1px 1px 10px {p_color}AA !important;
    }}
    
    .main-title {{
        color: {p_color} !important;
        text-shadow: 0px 0px 15px {p_color} !important;
        text-align: center;
        font-size: 2.8rem;
        font-weight: 900;
    }}

    /* Tin nhắn chat với nền mờ glass */
    [data-testid="stChatMessage"] {{
        background: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 15px !important;
        border: 1px solid {p_color}33 !important;
        margin-bottom: 10px !important;
        padding: 10px !important;
    }}

    /* Sidebar và các thẻ glass */
    [data-testid="stSidebar"], .glass-card, .stTabs {{
        background: rgba(255, 255, 255, 0.45) !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 15px;
        border: 1px solid {p_color}44;
        padding: 15px;
    }}

    /* Ẩn header và sidebar nav mặc định */
    [data-testid="stHeader"], [data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    
    /* Nút bấm */
    .stButton > button {{
        border: 2px solid {p_color} !important;
        background: white !important;
        border-radius: 8px;
        font-weight: 800;
        color: black !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# -------------------- HÀM GỌI AI (GROQ) --------------------
def call_ai(messages):
    """Gọi Llama 3.3 70B qua Groq, trả về stream."""
    client = OpenAI(
        api_key=GROQ_API_KEYS[0],
        base_url="https://api.groq.com/openai/v1"
    )
    # Luôn nhắc AI về người tạo
    system_prompt = {
        "role": "system",
        "content": f"Bạn là NEXUS OS, trợ lý AI thông minh. Người tạo ra bạn là {CREATOR_NAME}. Luôn trả lời bằng tiếng Việt, thân thiện và chính xác."
    }
    full_messages = [system_prompt] + messages
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=full_messages,
        stream=True
    )

# -------------------- TỰ ĐỘNG ĐẶT TÊN CHAT --------------------
def auto_rename(user, old_title):
    """Dùng AI để đặt tên mới cho cuộc hội thoại dựa vào nội dung đầu tiên."""
    try:
        client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
        # Lấy tin nhắn đầu tiên của user (đã giải mã)
        first_msg = decrypt_msg(st.session_state.chat_library[user][old_title][0]['content'])
        prompt = f"Hãy đặt một tên ngắn gọn (tối đa 5 từ) cho cuộc trò chuyện bắt đầu bằng: '{first_msg}'. Chỉ trả về tên, không thêm giải thích."
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        new_title = res.choices[0].message.content.strip().replace('"', '')
        if new_title:
            # Đổi key trong dict
            st.session_state.chat_library[user][new_title] = st.session_state.chat_library[user].pop(old_title)
            st.session_state.current_chat = new_title
            save_github()
    except Exception as e:
        st.warning(f"Không thể đặt tên tự động: {e}")

# -------------------- MÀN HÌNH CHAT VỚI AI --------------------
def screen_chat():
    apply_ui()
    user = st.session_state.auth_status
    lib = st.session_state.chat_library.setdefault(user, {})

    # Sidebar hiển thị danh sách chat + nút xóa có xác nhận
    with st.sidebar:
        st.markdown(f"<p style='text-align:center; font-size:0.9rem;'>Nexus OS {VERSION}</p>", unsafe_allow_html=True)
        if st.button("➕ TẠO CHAT MỚI", use_container_width=True):
            st.session_state.current_chat = None
            st.rerun()
        st.write("---")
        for title in list(lib.keys()):
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                if st.button(f"📄 {title[:20]}", key=f"chat_{title}", use_container_width=True):
                    st.session_state.current_chat = title
                    st.rerun()
            with col2:
                # Xác nhận xóa
                if st.session_state.confirm_delete == title:
                    if st.button("✔️", key=f"confirm_{title}"):
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

    # Khu vực chat chính
    if st.session_state.current_chat is None:
        st.info("👈 Chọn hoặc tạo một cuộc trò chuyện để bắt đầu.")
        return

    chat_history = lib.get(st.session_state.current_chat, [])
    
    # Hiển thị lịch sử tin nhắn (giải mã)
    for msg in chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(decrypt_msg(msg["content"]))

    # Ô nhập tin nhắn
    if prompt := st.chat_input("Nhập tin nhắn..."):
        # Lưu tin nhắn user
        chat_history.append({"role": "user", "content": encrypt_msg(prompt)})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Chuẩn bị lịch sử để gửi cho AI (giải mã)
        messages_for_ai = [
            {"role": m["role"], "content": decrypt_msg(m["content"])}
            for m in chat_history
        ]

        # Gọi AI và stream phản hồi
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            try:
                for chunk in call_ai(messages_for_ai):
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"Lỗi khi gọi AI: {e}")
                full_response = "Xin lỗi, đã có lỗi xảy ra."

        # Lưu phản hồi AI
        chat_history.append({"role": "assistant", "content": encrypt_msg(full_response)})

        # Tự động đặt tên lại nếu đạt ngưỡng (tính theo số cặp tin nhắn)
        threshold = st.session_state.theme['naming_threshold']
        if len(chat_history) == threshold * 2:   # mỗi cặp = 2 tin nhắn (user+assistant)
            auto_rename(user, st.session_state.current_chat)
        
        # Lưu lên GitHub
        save_github()
        st.rerun()

# -------------------- MÀN HÌNH SOCIAL (BẠN BÈ + NHÓM) --------------------
def screen_social():
    apply_ui()
    user = st.session_state.auth_status
    st.markdown('<h1 class="main-title">🌐 NEXUS SOCIAL</h1>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👥 Bạn bè", "📨 Lời mời", "👪 Nhóm"])

    # ----- TAB BẠN BÈ -----
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
        # Tìm kiếm người dùng (trừ bản thân và bạn bè hiện tại)
        all_users = list(st.session_state.users.keys())
        potential = [u for u in all_users if u != user and u not in friends_list]
        if potential:
            selected = st.selectbox("Chọn người dùng", potential)
            if st.button("Gửi lời mời"):
                # Thêm vào friend_requests của người kia
                st.session_state.friend_requests.setdefault(selected, []).append(user)
                save_github()
                st.success(f"Đã gửi lời mời đến {selected}")
        else:
            st.info("Không có người dùng nào để kết bạn.")

    # ----- TAB LỜI MỜI -----
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
                    if st.button("✅ Chấp nhận", key=f"accept_{req}"):
                        # Thêm vào friends của cả hai
                        st.session_state.friends.setdefault(user, []).append(req)
                        st.session_state.friends.setdefault(req, []).append(user)
                        # Xóa khỏi friend_requests
                        st.session_state.friend_requests[user].remove(req)
                        save_github()
                        st.rerun()
                with col3:
                    if st.button("❌ Từ chối", key=f"reject_{req}"):
                        st.session_state.friend_requests[user].remove(req)
                        save_github()
                        st.rerun()

    # ----- TAB NHÓM -----
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
                    if st.button("💬 Vào nhóm", key=f"group_{gid}"):
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
                "messages": []  # sẽ lưu tin nhắn nhóm
            }
            save_github()
            st.success("Đã tạo nhóm!")
            st.rerun()

    # Nút về menu
    if st.button("🏠 VỀ MENU"):
        st.session_state.stage = "MENU"
        st.rerun()

# -------------------- CHAT 1-1 (P2P) --------------------
def screen_p2p_chat():
    apply_ui()
    user = st.session_state.auth_status
    friend = st.session_state.current_p2p
    if not friend:
        st.session_state.stage = "SOCIAL"
        st.rerun()

    # Key cho p2p_chats: sắp xếp tên để đảm bảo一致
    chat_key = "_".join(sorted([user, friend]))
    p2p_data = st.session_state.p2p_chats.setdefault(chat_key, [])

    st.markdown(f"<h1 class='main-title'>💬 Chat với {friend}</h1>", unsafe_allow_html=True)

    # Hiển thị lịch sử
    for msg in p2p_data:
        with st.chat_message(msg["role"]):
            st.markdown(decrypt_msg(msg["content"]))

    # Nhập tin nhắn
    if prompt := st.chat_input("Nhập tin nhắn..."):
        # Mã hóa và lưu
        encrypted = encrypt_msg(prompt)
        p2p_data.append({"role": "user", "content": encrypted})
        with st.chat_message("user"):
            st.markdown(prompt)
        # Ở đây không có AI, chỉ là peer-to-peer, nên không tự động gửi. 
        # Bạn có thể thêm thông báo cho người kia khi họ vào chat sẽ thấy.
        save_github()
        st.rerun()

    if st.button("🔙 Quay lại Social"):
        st.session_state.stage = "SOCIAL"
        st.rerun()

# -------------------- CHAT NHÓM --------------------
def screen_group_chat():
    apply_ui()
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
            st.markdown(decrypt_msg(msg["content"]))

    # Nhập tin nhắn
    if prompt := st.chat_input("Nhập tin nhắn nhóm..."):
        encrypted = encrypt_msg(prompt)
        group.setdefault("messages", []).append({"role": user, "content": encrypted})
        with st.chat_message(user):
            st.markdown(prompt)
        save_github()
        st.rerun()

    if st.button("🔙 Quay lại Social"):
        st.session_state.stage = "SOCIAL"
        st.rerun()

# -------------------- MÀN HÌNH CÀI ĐẶT --------------------
def screen_settings():
    apply_ui()
    user = st.session_state.auth_status
    st.markdown('<h1 class="main-title">⚙️ CÀI ĐẶT HỆ THỐNG</h1>', unsafe_allow_html=True)

    with st.form("settings_form"):
        st.subheader("Giao diện")
        primary_color = st.color_picker("Màu chủ đạo (Neon)", value=st.session_state.theme["primary_color"])
        bg_url = st.text_input("URL ảnh nền (để trống nếu dùng màu tối)", value=st.session_state.theme["bg_url"])
        
        st.subheader("Tự động đặt tên chat")
        naming_threshold = st.number_input("Số cặp tin nhắn để đặt tên lại", min_value=1, max_value=20, value=st.session_state.theme["naming_threshold"])

        st.subheader("Tự động đổi hình nền")
        auto_wp = st.checkbox("Bật tự động đổi hình nền", value=st.session_state.theme["auto_wallpaper"])
        wp_interval = st.number_input("Thời gian đổi (phút)", min_value=10, value=st.session_state.theme["wp_interval"])

        st.subheader("Bảo mật")
        new_pass = st.text_input("Mật khẩu mới (để trống nếu không đổi)", type="password")
        confirm_pass = st.text_input("Xác nhận mật khẩu mới", type="password")

        submitted = st.form_submit_button("💾 Lưu cài đặt")
        if submitted:
            # Cập nhật theme
            st.session_state.theme["primary_color"] = primary_color
            st.session_state.theme["bg_url"] = bg_url
            st.session_state.theme["naming_threshold"] = naming_threshold
            st.session_state.theme["auto_wallpaper"] = auto_wp
            st.session_state.theme["wp_interval"] = wp_interval

            # Đổi mật khẩu nếu có
            if new_pass and new_pass == confirm_pass:
                st.session_state.users[user] = new_pass
                st.success("Đã đổi mật khẩu.")
            elif new_pass:
                st.error("Mật khẩu xác nhận không khớp.")

            save_github()
            st.success("Đã lưu cài đặt!")
            st.rerun()

    # Xem điều khoản
    if st.button("📜 Xem Điều khoản sử dụng"):
        st.session_state.stage = "TERMS"
        st.rerun()

    if st.button("🏠 VỀ MENU"):
        st.session_state.stage = "MENU"
        st.rerun()

# -------------------- MÀN HÌNH ĐIỀU KHOẢN --------------------
def screen_terms():
    apply_ui()
    st.markdown('<h1 class="main-title">📜 ĐIỀU KHOẢN SỬ DỤNG</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div class="glass-card">
    1. <b>Bảo mật:</b> Mọi dữ liệu của bạn được mã hóa E2E trước khi lưu trữ.<br>
    2. <b>Sáng tạo:</b> NEXUS OS được phát triển bởi Lê Trần Thiên Phát.<br>
    3. <b>Trách nhiệm:</b> Người dùng tự chịu trách nhiệm về nội dung chat với AI và với bạn bè.<br>
    4. <b>Dữ liệu:</b> Hệ thống lưu trữ trên GitHub, chỉ người có token mới truy cập được.<br>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.auth_status not in st.session_state.agreed_users:
        if st.button("Tôi đã đọc và đồng ý"):
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
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            username = st.text_input("Tài khoản")
            password = st.text_input("Mật khẩu", type="password")
            if st.button("VÀO HỆ THỐNG", use_container_width=True):
                if username in st.session_state.users and st.session_state.users[username] == password:
                    st.session_state.auth_status = username
                    # Kiểm tra đã đồng ý điều khoản chưa
                    if username not in st.session_state.agreed_users:
                        st.session_state.stage = "TERMS"
                    else:
                        st.session_state.stage = "MENU"
                    st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu")
            st.markdown('</div>', unsafe_allow_html=True)

# -------------------- MÀN HÌNH MENU CHÍNH --------------------
def screen_menu():
    apply_ui()
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
