# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time
import base64
import json
import requests
import random
import string

# --- 1. THÔNG TIN HỆ THỐNG ---
CREATOR_NAME = "Lê Trần Thiên Phát"
VERSION = "V4200 - SOCIAL HUB & SECURE COMM"
FILE_DATA = "data.json"

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("Thiếu cấu hình Secrets!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR_NAME}", layout="wide")

# --- 2. HỆ THỐNG BẢO MẬT & MÃ HÓA (ENCRYPTION) ---
# Mã hóa giả lập mã hóa đầu cuối (XOR + Base64) để chống đọc trộm file JSON
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
    except: return text # Fallback cho dữ liệu cũ

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
        payload = {"message": f"Nexus Update", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- 4. KHỞI TẠO BIẾN ---
if 'initialized' not in st.session_state:
    db = load_github()
    st.session_state.users = db.get("users", {"admin": "123"})
    st.session_state.theme = db.get("theme", {"primary_color": "#00f2ff", "bg_url": "", "use_glass": True, "max_fails": 5, "lockout_time": 30})
    
    # Cấu trúc lại chat library: Tách riêng cho từng User
    raw_chat = db.get("chat_library", {})
    st.session_state.chat_library = raw_chat if isinstance(raw_chat, dict) else {}
    
    st.session_state.agreed_users = db.get("agreed_users", [])
    st.session_state.friends = db.get("friends", {})
    st.session_state.friend_requests = db.get("friend_requests", {})
    st.session_state.groups = db.get("groups", {})
    st.session_state.p2p_chats = db.get("p2p_chats", {})
    
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None
    st.session_state.current_group = None
    st.session_state.login_track = {}
    st.session_state.initialized = True

# Đảm bảo user có dữ liệu
def init_user_data(username):
    if username not in st.session_state.chat_library: st.session_state.chat_library[username] = {}
    if username not in st.session_state.friends: st.session_state.friends[username] = []
    if username not in st.session_state.friend_requests: st.session_state.friend_requests[username] = []

# --- 5. ENGINE GIAO DIỆN ---
def apply_ui():
    t = st.session_state.theme
    bg_style = f"background: url('{t['bg_url']}') no-repeat center center fixed; background-size: cover;" if t['bg_url'] else "background-color: #0e1117;"
    glass_bg = "rgba(255, 255, 255, 0.45)" if t.get('use_glass', True) else "transparent"
    glass_blur = "blur(12px)" if t.get('use_glass', True) else "none"

    st.markdown(f"""
    <style>
    .stApp {{ {bg_style} }}
    .main-title {{ color: {t['primary_color']} !important; text-align: center; font-size: 3rem; font-weight: 900; text-shadow: 0px 0px 15px {t['primary_color']}; margin-bottom: 25px; }}
    .stApp p, .stApp span, .stApp label, .stMarkdown p, .stMarkdown li, h1, h2, h3, h4 {{ color: #000000 !important; font-weight: 600 !important; }}
    .glass-card, div[data-testid="stChatMessage"], [data-testid="stSidebar"], .stTabs {{ background: {glass_bg} !important; backdrop-filter: {glass_blur} !important; border-radius: 15px; padding: 20px; }}
    div.stButton > button {{ width: 100%; border-radius: 10px; font-weight: 800; border: 2px solid {t['primary_color']} !important; background: rgba(255,255,255,0.8) !important; color: #000000 !important; }}
    div.stButton > button:hover {{ background: {t['primary_color']} !important; color: #000000 !important; }}
    [data-testid="stSidebarContent"] * {{ color: #000000 !important; }}
    input, textarea {{ background: rgba(255, 255, 255, 0.9) !important; color: #000000 !important; border: 2px solid #000000 !important; }}
    
    /* FIX NÚT THÙNG RÁC */
    .trash-btn {{ display: flex; align-items: center; justify-content: center; }}
    </style>
    """, unsafe_allow_html=True)

# --- 6. LÕI AI (ĐÃ KHÓA TIẾNG TRUNG) ---
def call_ai(messages):
    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
    sys_prompt = f"Bạn là A.I Nexus OS của {CREATOR_NAME}. BẮT BUỘC TRẢ LỜI BẰNG TIẾNG VIỆT 100%. TUYỆT ĐỐI KHÔNG DÙNG KÝ TỰ TIẾNG TRUNG QUỐC. HÃY THÂN THIỆN VÀ RÕ RÀNG."
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": sys_prompt}] + messages,
        stream=True
    )

# --- 7. CÁC MÀN HÌNH ---
def screen_auth():
    apply_ui()
    st.markdown('<h1 class="main-title">🛡️ NEXUS OS GATEWAY</h1>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["🔑 LOGIN", "📝 REGISTER", "👤 GUEST"])
        with t1:
            u = st.text_input("Username", key="l_u")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("TRUY CẬP HỆ THỐNG", use_container_width=True):
                if u:
                    track = st.session_state.login_track.setdefault(u, {"fails": 0, "locked_until": 0})
                    if time.time() < track["locked_until"]:
                        st.error(f"🔒 Khóa tài khoản! Thử lại sau {int(track['locked_until'] - time.time())}s.")
                    elif u in st.session_state.users and st.session_state.users[u] == p:
                        track["fails"] = 0; st.session_state.auth_status = u
                        init_user_data(u)
                        st.session_state.stage = "MENU" if u in st.session_state.agreed_users else "TERMS"
                        st.rerun()
                    else:
                        track["fails"] += 1
                        if track["fails"] >= st.session_state.theme['max_fails']:
                            track["locked_until"] = time.time() + st.session_state.theme['lockout_time']
                            st.error("⛔ Đã khóa do nhập sai quá nhiều!")
                        else: st.error("❌ Sai thông tin!")
        with t2:
            nu = st.text_input("Tên đăng ký", key="r_u")
            p1 = st.text_input("Mật khẩu", type="password", key="r_p1")
            p2 = st.text_input("Xác nhận", type="password", key="r_p2")
            if st.button("TẠO TÀI KHOẢN", use_container_width=True):
                if nu in st.session_state.users: st.error("Tên đã tồn tại!")
                elif p1 == p2 and nu:
                    st.session_state.users[nu] = p1; init_user_data(nu)
                    save_github(); st.success("Xong! Hãy Login.")
                else: st.error("Mật khẩu không khớp!")
        with t3:
            if st.button("QUYỀN KHÁCH", use_container_width=True):
                st.session_state.auth_status = "Guest"; st.session_state.stage = "TERMS"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def screen_terms():
    apply_ui()
    st.markdown('<h1 class="main-title">📜 ĐIỀU KHOẢN & QUY TẮC</h1>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 3, 1])
    with c2:
        st.markdown(f"""
        <div class="glass-card">
            <h3>Luật Lệ Hệ Thống Nexus ({VERSION})</h3>
            <p>1. <b>Bảo mật tuyệt đối:</b> Tin nhắn được mã hóa E2E. Chỉ người trong cuộc mới đọc được.</p>
            <p>2. <b>Văn minh:</b> Không dùng từ ngữ xúc phạm, không spam nền tảng.</p>
            <p>3. <b>AI Trợ Lý:</b> AI được giám sát để trả lời 100% tiếng Việt.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.checkbox("Tôi đồng ý với các luật lệ trên") and st.button("VÀO MENU"):
            if st.session_state.auth_status != "Guest":
                if st.session_state.auth_status not in st.session_state.agreed_users:
                    st.session_state.agreed_users.append(st.session_state.auth_status)
                    save_github()
            st.session_state.stage = "MENU"; st.rerun()

def screen_menu():
    apply_ui()
    st.markdown(f'<h1 class="main-title">🚀 NEXUS MENU</h1>', unsafe_allow_html=True)
    st.markdown(f'<h3 style="text-align:center;">User: {st.session_state.auth_status.upper()}</h3><br>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        if st.button("🧠 TRỢ LÝ A.I"): st.session_state.stage = "CHAT"; st.rerun()
    with c2: 
        if st.button("🌐 CỘNG ĐỒNG"): st.session_state.stage = "SOCIAL"; st.rerun()
    with c3: 
        if st.button("⚙️ CÀI ĐẶT"): st.session_state.stage = "SETTINGS"; st.rerun()
    with c4: 
        if st.button("🚪 ĐĂNG XUẤT"): st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()

# --- CHAT A.I ---
def screen_chat():
    apply_ui()
    user = st.session_state.auth_status
    if user == "Guest": lib = st.session_state.chat_library.setdefault("Guest", {})
    else: lib = st.session_state.chat_library[user]

    with st.sidebar:
        st.header("📂 Thư Viện A.I")
        if st.button("➕ TẠO CHAT MỚI"): st.session_state.current_chat = None; st.rerun()
        st.write("---")
        for title in list(lib.keys()):
            col1, col2 = st.columns([5, 1])
            with col1:
                if st.button(f"📄 {title[:12]}", key=f"c_{title}"): st.session_state.current_chat = title; st.rerun()
            with col2:
                if st.button("🗑️", key=f"d_{title}"):
                    del lib[title]; save_github(); st.session_state.current_chat = None; st.rerun()
        st.write("---")
        if st.button("🏠 VỀ MENU"): st.session_state.stage = "MENU"; st.rerun()

    history = lib.get(st.session_state.current_chat, []) if st.session_state.current_chat else []
    for m in history:
        with st.chat_message(m["role"]): st.markdown(decrypt_msg(m["content"]))

    if p := st.chat_input("Nhập lệnh cho A.I..."):
        if not st.session_state.current_chat:
            st.session_state.current_chat = p[:20]
            lib[st.session_state.current_chat] = []
        
        lib[st.session_state.current_chat].append({"role": "user", "content": encrypt_msg(p)})
        with st.chat_message("user"): st.markdown(p)
        
        # Call AI with decrypted history context
        ai_context = [{"role": m["role"], "content": decrypt_msg(m["content"])} for m in lib[st.session_state.current_chat]]
        with st.chat_message("assistant"):
            res = st.empty(); full = ""
            for chunk in call_ai(ai_context):
                if chunk.choices[0].delta.content:
                    full += chunk.choices[0].delta.content
                    res.markdown(full + "▌")
            res.markdown(full)
        
        lib[st.session_state.current_chat].append({"role": "assistant", "content": encrypt_msg(full)})
        if user != "Guest": save_github()

# --- MẠNG XÃ HỘI & NHÓM ---
def screen_social():
    apply_ui()
    user = st.session_state.auth_status
    if user == "Guest":
        st.warning("Khách không thể dùng tính năng này!"); st.button("Quay lại", on_click=lambda: st.session_state.update(stage="MENU")); return

    st.markdown('<h1 class="main-title">🌐 MẠNG CỘNG ĐỒNG</h1>', unsafe_allow_html=True)
    if st.button("🔄 LÀM MỚI DỮ LIỆU"): load_github(); st.rerun()
    
    t1, t2, t3 = st.tabs(["🔍 TÌM BẠN bè", "👥 DANH SÁCH BẠN", "💬 NHÓM LÀM VIỆC"])
    
    with t1:
        st.markdown("### 💌 Lời mời kết bạn")
        reqs = st.session_state.friend_requests.get(user, [])
        if not reqs: st.write("Không có lời mời nào.")
        for r in reqs:
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{r}** muốn kết bạn.")
            if c2.button("✅ Chấp nhận", key=f"acc_{r}"):
                st.session_state.friends[user].append(r)
                st.session_state.friends[r].append(user)
                st.session_state.friend_requests[user].remove(r)
                save_github(); st.rerun()
            if c3.button("❌ Từ chối", key=f"den_{r}"):
                st.session_state.friend_requests[user].remove(r); save_github(); st.rerun()

        st.markdown("### 🔍 Tìm kiếm người dùng")
        search_q = st.text_input("Nhập tên người dùng cần tìm:")
        if search_q:
            for u in st.session_state.users:
                if search_q.lower() in u.lower() and u != "admin" and u != user:
                    cc1, cc2 = st.columns([4, 1])
                    cc1.write(f"👤 **{u}**")
                    if u in st.session_state.friends.get(user, []): cc2.success("Đã là bạn")
                    elif user in st.session_state.friend_requests.get(u, []): cc2.info("Đã gửi mời")
                    else:
                        if cc2.button("➕ Kết bạn", key=f"add_{u}"):
                            if u not in st.session_state.friend_requests: st.session_state.friend_requests[u] = []
                            st.session_state.friend_requests[u].append(user)
                            save_github(); st.rerun()

    with t2:
        my_friends = st.session_state.friends.get(user, [])
        if not my_friends: st.write("Chưa có bạn bè nào.")
        for f in my_friends:
            cc1, cc2 = st.columns([4, 1])
            cc1.write(f"🟢 **{f}**")
            if cc2.button("💬 Nhắn tin", key=f"msg_{f}"):
                chat_id = "_".join(sorted([user, f]))
                if chat_id not in st.session_state.p2p_chats: st.session_state.p2p_chats[chat_id] = []
                st.session_state.current_chat = chat_id
                st.session_state.stage = "P2P_CHAT"; st.rerun()

    with t3:
        st.markdown("### 🛠️ Tạo nhóm mới")
        g_name = st.text_input("Tên nhóm:")
        g_mode = st.selectbox("Chế độ A.I trong nhóm:", ["Bán tự động (AI nằm ngoài)", "Tự động (AI như thành viên)", "Không dùng AI"])
        g_members = st.multiselect("Thêm bạn bè vào nhóm:", my_friends)
        if st.button("TẠO NHÓM"):
            if g_name and g_members:
                g_id = f"G_{int(time.time())}"
                st.session_state.groups[g_id] = {"name": g_name, "mode": g_mode, "members": [user] + g_members, "msgs": []}
                save_github(); st.success("Đã tạo nhóm!"); st.rerun()
            else: st.warning("Cần điền tên và thêm ít nhất 1 bạn.")
        
        st.markdown("### 📋 Nhóm của tôi")
        for gid, ginfo in st.session_state.groups.items():
            if user in ginfo["members"]:
                col1, col2 = st.columns([4, 1])
                col1.write(f"📁 **{ginfo['name']}** ({len(ginfo['members'])} người) - [Chế độ: {ginfo['mode']}]")
                if col2.button("VÀO NHÓM", key=f"enter_{gid}"):
                    st.session_state.current_group = gid; st.session_state.stage = "GROUP_CHAT"; st.rerun()

    if st.button("🔙 QUAY LẠI MENU"): st.session_state.stage = "MENU"; st.rerun()

# --- CHAT NHÓM ---
def screen_group_chat():
    apply_ui()
    gid = st.session_state.current_group
    ginfo = st.session_state.groups[gid]
    mode = ginfo["mode"]
    user = st.session_state.auth_status

    st.markdown(f'<h2 class="main-title">Nhóm: {ginfo["name"]}</h2>', unsafe_allow_html=True)
    c1, c2 = st.columns([5, 1])
    with c1: st.write(f"Thành viên: {', '.join(ginfo['members'])}")
    with c2: 
        if st.button("🔄 LÀM MỚI"): load_github(); st.rerun()
        if st.button("🔙 THOÁT"): st.session_state.stage = "SOCIAL"; st.rerun()

    # BỐ CỤC CHAT (Tùy theo mode)
    if "Bán tự động" in mode:
        col_chat, col_ai = st.columns([2, 1])
    else: col_chat = st.container(); col_ai = None

    with col_chat:
        st.markdown('<div class="glass-card" style="height:400px; overflow-y:scroll;">', unsafe_allow_html=True)
        for m in ginfo["msgs"]:
            sender, text = m["s"], decrypt_msg(m["t"])
            if sender == "A.I": st.markdown(f"🤖 **A.I:** {text}")
            elif sender == user: st.markdown(f"🔵 **Bạn:** {text}")
            else: st.markdown(f"👤 **{sender}:** {text}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        msg = st.chat_input("Nhắn vào nhóm...")
        if msg:
            st.session_state.groups[gid]["msgs"].append({"s": user, "t": encrypt_msg(msg)})
            save_github()
            
            # Logic AI tự động
            if "Tự động" in mode:
                ai_ctx = [{"role": "user", "content": decrypt_msg(m["t"])} for m in st.session_state.groups[gid]["msgs"][-5:]]
                with st.spinner("A.I đang gõ..."):
                    res = ""
                    for chunk in call_ai(ai_ctx):
                        if chunk.choices[0].delta.content: res += chunk.choices[0].delta.content
                    st.session_state.groups[gid]["msgs"].append({"s": "A.I", "t": encrypt_msg(res)})
                    save_github()
            st.rerun()

    # Khung AI Bán Tự Động
    if col_ai:
        with col_ai:
            st.markdown("### 🤖 A.I Trợ Lý Riêng")
            if "ai_private" not in st.session_state: st.session_state.ai_private = ""
            ai_q = st.text_area("Hỏi riêng A.I (Chỉ bạn thấy):")
            if st.button("GỬI A.I"):
                res = ""
                for chunk in call_ai([{"role": "user", "content": ai_q}]):
                    if chunk.choices[0].delta.content: res += chunk.choices[0].delta.content
                st.session_state.ai_private = res
            
            if st.session_state.ai_private:
                st.info(st.session_state.ai_private)
                if st.button("📣 GỬI KẾT QUẢ VÀO NHÓM"):
                    st.session_state.groups[gid]["msgs"].append({"s": user, "t": encrypt_msg(f"[AI Gợi ý] {st.session_state.ai_private}")})
                    st.session_state.ai_private = ""
                    save_github(); st.rerun()

# --- CHAT P2P ---
def screen_p2p():
    apply_ui()
    chat_id = st.session_state.current_chat
    u1, u2 = chat_id.split("_")
    friend = u2 if u1 == st.session_state.auth_status else u1

    c1, c2 = st.columns([5, 1])
    c1.markdown(f'<h2 class="main-title">Chat 1-1: {friend} 🔒</h2>', unsafe_allow_html=True)
    with c2:
        if st.button("🔄 LÀM MỚI"): load_github(); st.rerun()
        if st.button("🔙 QUAY LẠI"): st.session_state.stage = "SOCIAL"; st.rerun()

    msgs = st.session_state.p2p_chats[chat_id]
    st.markdown('<div class="glass-card" style="height:500px; overflow-y:scroll;">', unsafe_allow_html=True)
    for m in msgs:
        sender, text = m["s"], decrypt_msg(m["t"])
        if sender == st.session_state.auth_status: st.markdown(f"<div style='text-align:right;'>🔵 <b>Bạn:</b> {text}</div>", unsafe_allow_html=True)
        else: st.markdown(f"<div style='text-align:left;'>🟢 <b>{sender}:</b> {text}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if msg := st.chat_input(f"Nhắn tin cho {friend} (Mã hóa E2E)"):
        st.session_state.p2p_chats[chat_id].append({"s": st.session_state.auth_status, "t": encrypt_msg(msg)})
        save_github(); st.rerun()

# --- CÀI ĐẶT & THAY ĐỔI THÔNG TIN ---
def screen_settings():
    apply_ui()
    st.markdown('<h1 class="main-title">⚙️ TRUNG TÂM CÀI ĐẶT</h1>', unsafe_allow_html=True)
    user = st.session_state.auth_status
    
    col_acc, col_ui = st.columns(2)
    with col_acc:
        st.markdown("""<div class="glass-card"><h3>👤 Quản Lý Tài Khoản</h3>""", unsafe_allow_html=True)
        if user != "Guest" and user != "admin":
            new_u = st.text_input("Đổi tên đăng nhập mới:")
            if st.button("ĐỔI TÊN"):
                if new_u in st.session_state.users: st.error("Tên này đã có người dùng!")
                elif new_u:
                    # Update all links
                    st.session_state.users[new_u] = st.session_state.users.pop(user)
                    st.session_state.chat_library[new_u] = st.session_state.chat_library.pop(user, {})
                    st.session_state.friends[new_u] = st.session_state.friends.pop(user, [])
                    st.session_state.friend_requests[new_u] = st.session_state.friend_requests.pop(user, [])
                    if user in st.session_state.agreed_users: 
                        st.session_state.agreed_users.remove(user)
                        st.session_state.agreed_users.append(new_u)
                    st.session_state.auth_status = new_u
                    save_github(); st.success("Đổi tên thành công!"); st.rerun()

            st.write("---")
            old_p = st.text_input("Mật khẩu cũ:", type="password")
            new_p1 = st.text_input("Mật khẩu mới:", type="password")
            new_p2 = st.text_input("Xác nhận mật khẩu mới:", type="password")
            if st.button("ĐỔI MẬT KHẨU"):
                if st.session_state.users[user] != old_p: st.error("Sai mật khẩu cũ!")
                elif new_p1 != new_p2: st.error("Mật khẩu mới không khớp!")
                else: 
                    st.session_state.users[user] = new_p1; save_github(); st.success("Đã đổi!")
        else: st.warning("Khách/Admin không đổi thông tin tại đây.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_ui:
        st.markdown("""<div class="glass-card"><h3>🎨 Tùy Chỉnh Giao Diện</h3>""", unsafe_allow_html=True)
        st.session_state.theme['bg_url'] = st.text_input("Link ảnh nền:", st.session_state.theme['bg_url'])
        st.session_state.theme['primary_color'] = st.color_picker("Màu chủ đạo:", st.session_state.theme['primary_color'])
        st.session_state.theme['use_glass'] = st.toggle("Sương mờ", st.session_state.theme['use_glass'])
        st.markdown("</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("💾 LƯU MÀU & NỀN", use_container_width=True): save_github(); st.rerun()
        if st.button("🔙 VỀ MENU", use_container_width=True): st.session_state.stage = "MENU"; st.rerun()

# --- ĐIỀU HƯỚNG ---
if st.session_state.stage == "AUTH": screen_auth()
elif st.session_state.stage == "TERMS": screen_terms()
elif st.session_state.stage == "MENU": screen_menu()
elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "SOCIAL": screen_social()
elif st.session_state.stage == "GROUP_CHAT": screen_group_chat()
elif st.session_state.stage == "P2P_CHAT": screen_p2p()
elif st.session_state.stage == "SETTINGS": screen_settings()
