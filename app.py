# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH ---
CREATOR = "Lê Trần Thiên Phát"
VERSION = "V4900 - JUSTICE & STABLE"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("Cấu hình Secrets bị thiếu!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR}", layout="wide")

# --- [2] HÀM NỀN TẢNG ---
def ma_hoa(text):
    if not text: return ""
    encoded = "".join([chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(text)])
    return base64.b64encode(encoded.encode()).decode()

def giai_ma(text):
    if not text: return ""
    try:
        decoded = base64.b64decode(text.encode()).decode()
        return "".join([chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(decoded)])
    except: return text

def tai_du_lieu():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
    except: pass
    return {}

def luu_du_lieu():
    data = {
        "users": st.session_state.users, 
        "profiles": st.session_state.profiles,
        "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library, 
        "groups": st.session_state.groups,
        "access_logs": st.session_state.get("access_logs", []),
        "punishments": st.session_state.punishments
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": f"Nexus Update {datetime.now()}", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- [3] KHỞI TẠO ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"Thiên Phát": "2002"})
    st.session_state.profiles = db.get("profiles", {}) # {user: {avatar, bio, nickname}}
    st.session_state.theme = db.get("theme", {"primary_color": "#00f2ff", "bg_url": ""})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {"Chung": {"type": "NONE", "msgs": []}})
    st.session_state.access_logs = db.get("access_logs", [])
    st.session_state.punishments = db.get("punishments", {}) # {user: {banned_until, reason}}
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.initialized = True

# --- [4] GIAO DIỆN & LOGO ---
def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg = f"url('{t['bg_url']}')" if t['bg_url'] else "#0f172a"
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg} no-repeat center fixed; background-size: cover; color: #F8F9FA; }}
    .glass-box {{ background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(10px); border-radius: 12px; padding: 20px; border: 1px solid {p_color}33; }}
    h1, h2, h3 {{ color: #F8F9FA !important; text-shadow: 0 0 10px {p_color}; }}
    p, label, span {{ color: #cbd5e1 !important; }}
    </style>
    """, unsafe_allow_html=True)

def draw_logo():
    color = st.session_state.theme.get('primary_color', '#00f2ff')
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; margin: 20px 0;">
        <div style="width: 70px; height: 70px; border: 4px solid {color}; border-radius: 20% 50%; animation: orbit 4s linear infinite; box-shadow: 0 0 15px {color};"></div>
        <div style="color: #F8F9FA; font-weight: bold; margin-top: 10px; letter-spacing: 2px;">NEXUS GATEWAY</div>
    </div>
    <style> @keyframes orbit {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }} </style>
    """, unsafe_allow_html=True)

# --- [5] CÁC MÀN HÌNH CHỨC NĂNG ---

def check_ban(user):
    if user in st.session_state.punishments:
        ban_info = st.session_state.punishments[user]
        until = datetime.strptime(ban_info['until'], "%Y-%m-%d %H:%M:%S")
        if datetime.now() < until:
            return ban_info['reason'], until
    return None, None

def screen_profile():
    apply_ui()
    me = st.session_state.auth_status
    st.title("👤 CÁ NHÂN HÓA TÀI KHOẢN")
    p = st.session_state.profiles.setdefault(me, {"nickname": me, "bio": "Thành viên Nexus", "avatar": ""})
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if p['avatar']: st.image(p['avatar'], width=150)
        else: st.warning("Chưa có ảnh đại diện")
        new_avatar = st.text_input("Link ảnh đại diện (URL)", p['avatar'])
    with col2:
        new_nick = st.text_input("Biệt danh", p['nickname'])
        new_bio = st.text_area("Giới thiệu", p['bio'])
    
    if st.button("LƯU CÁ NHÂN HÓA"):
        st.session_state.profiles[me] = {"nickname": new_nick, "bio": new_bio, "avatar": new_avatar}
        luu_du_lieu(); st.success("Đã cập nhật!"); time.sleep(1); st.rerun()
    if st.button("Quay lại"): st.session_state.stage = "MENU"; st.rerun()

def screen_law():
    apply_ui()
    st.title("📜 LUẬT LỆ NEXUS OS GATEWAY")
    st.markdown("""
    <div class='glass-box'>
    1. <b>Tôn trọng:</b> Không xúc phạm chủ nhân hệ thống (Phát) và người dùng khác.<br>
    2. <b>An toàn:</b> Không cố gắng tấn công, phá hoại hoặc spam dữ liệu lên GitHub.<br>
    3. <b>Nội dung:</b> Không sử dụng AI để tạo nội dung độc hại, vi phạm pháp luật.<br>
    4. <b>Xử phạt:</b> Admin có quyền cấm truy cập vĩnh viễn mà không cần báo trước nếu vi phạm.<br>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Tôi đã hiểu"): st.session_state.stage = "MENU"; st.rerun()

def screen_admin():
    apply_ui()
    st.title("🛡️ ADMIN CONTROL PANEL")
    
    tab1, tab2 = st.tabs(["📊 Logs Truy Cập", "🔨 Xử Phạt Người Dùng"])
    
    with tab1:
        for log in reversed(st.session_state.access_logs):
            st.write(f"**{log['user']}** - {log['time']}")
            st.code(log['info'])
    
    with tab2:
        user_to_ban = st.selectbox("Chọn người dùng", list(st.session_state.users.keys()))
        reason = st.text_area("Lý do phạm tội (Sẽ hiện cho người đó thấy)")
        duration = st.number_input("Số phút cấm", min_value=1, value=60)
        
        c1, c2 = st.columns(2)
        if c1.button("🔥 THỰC THI LỆNH CẤM"):
            until = (datetime.now() + timedelta(minutes=duration)).strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.punishments[user_to_ban] = {"until": until, "reason": reason}
            luu_du_lieu(); st.warning(f"Đã cấm {user_to_ban}!"); st.rerun()
        if c2.button("✨ GỠ CẤM"):
            if user_to_ban in st.session_state.punishments:
                del st.session_state.punishments[user_to_ban]
                luu_du_lieu(); st.success(f"Đã gỡ cấm cho {user_to_ban}"); st.rerun()

    if st.button("Quay lại"): st.session_state.stage = "MENU"; st.rerun()

# --- [6] MAIN ROUTER ---
if st.session_state.stage == "AUTH":
    apply_ui(); draw_logo()
    _, cc, _ = st.columns([1, 1.2, 1])
    with cc:
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("ENTER GATEWAY", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU"
                agent = st.context.headers.get("User-Agent", "Unknown")
                st.session_state.access_logs.append({"user": u, "time": datetime.now().strftime("%H:%M:%S"), "info": agent})
                luu_du_lieu(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    # Kiểm tra xem có bị cấm không
    reason, until = check_ban(st.session_state.auth_status)
    if reason:
        st.error(f"🚫 TÀI KHOẢN ĐANG BỊ KHÓA!")
        st.info(f"**Lý do phạm tội:** {reason}")
        st.warning(f"**Thời hạn đến:** {until}")
        if st.button("Đăng xuất"): st.session_state.stage = "AUTH"; st.rerun()
    else:
        st.title(f"🚀 NEXUS MENU - {st.session_state.auth_status}")
        cols = st.columns(2)
        if cols[0].button("🧠 AI CHAT", use_container_width=True): st.session_state.stage = "CHAT"; st.rerun()
        if cols[1].button("🌐 CỘNG ĐỒNG", use_container_width=True): st.session_state.stage = "SOCIAL"; st.rerun()
        
        c1, c2, c3 = st.columns(3)
        if c1.button("👤 CÁ NHÂN"): st.session_state.stage = "PROFILE"; st.rerun()
        if c2.button("📜 LUẬT LỆ"): st.session_state.stage = "LAW"; st.rerun()
        if c3.button("⚙️ CÀI ĐẶT"): st.session_state.stage = "SETTINGS"; st.rerun()
        
        if st.session_state.auth_status.lower() == "thiên phát":
            if st.button("🛡️ ADMIN PANEL", use_container_width=True): st.session_state.stage = "ADMIN"; st.rerun()
        if st.button("🚪 LOGOUT"): st.session_state.stage = "AUTH"; st.rerun()

elif st.session_state.stage == "PROFILE": screen_profile()
elif st.session_state.stage == "LAW": screen_law()
elif st.session_state.stage == "ADMIN": screen_admin()
# ... (Các stage CHAT, SOCIAL, SETTINGS Phát giữ lại từ bản trước hoặc copy thêm vào) ...
else:
    # Fallback để tránh màn hình trắng
    apply_ui()
    st.write("Tính năng này đang được đồng bộ...")
    if st.button("Về Menu"): st.session_state.stage = "MENU"; st.rerun()
