# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH BẢO MẬT ---
CREATOR = "Lê Trần Thiên Phát"
VERSION = "V5000 - SUPREME GATEWAY"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("❌ Thiếu Secrets! Hãy kiểm tra lại cấu hình trên Streamlit Cloud.")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR}", layout="wide")

# --- [2] HÀM XỬ LÝ DỮ LIỆU ---
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
        "users": st.session_state.users, "theme": st.session_state.theme,
        "chat_library": st.session_state.chat_library, "profiles": st.session_state.profiles,
        "groups": st.session_state.groups, "access_logs": st.session_state.access_logs,
        "punishments": st.session_state.punishments
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": f"Sync {datetime.now()}", "content": content, "sha": sha} if sha else {"message": "Init", "content": content}
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- [3] KHỞI TẠO HỆ THỐNG ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"Thiên Phát": "2002", "admin": "123"})
    st.session_state.profiles = db.get("profiles", {})
    st.session_state.theme = db.get("theme", {
        "primary_color": "#00f2ff", "bg_list": [], "auto_rotate": False, 
        "rotate_min": 5, "current_bg_idx": 0, "last_rotate": str(datetime.now())
    })
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {"Sảnh Chung": {"type": "FULL_AI", "msgs": []}})
    st.session_state.access_logs = db.get("access_logs", [])
    st.session_state.punishments = db.get("punishments", {})
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.initialized = True

# --- [4] TÍNH NĂNG ĐỔI NỀN TỰ ĐỘNG ---
def update_background():
    t = st.session_state.theme
    if t.get("auto_rotate") and t.get("bg_list"):
        last_time = datetime.strptime(t["last_rotate"], "%Y-%m-%d %H:%M:%S.%f")
        if datetime.now() > last_time + timedelta(minutes=t["rotate_min"]):
            t["current_bg_idx"] = (t["current_bg_idx"] + 1) % len(t["bg_list"])
            t["last_rotate"] = str(datetime.now())
            # Không lưu GitHub ngay để tránh spam API, chỉ đổi trong session
            return t["bg_list"][t["current_bg_idx"]]
    return t.get("bg_list")[t["current_bg_idx"]] if t.get("bg_list") else ""

# --- [5] GIAO DIỆN MÀU TỐI (DỊU MẮT) ---
def apply_ui():
    bg_url = update_background()
    t = st.session_state.theme
    p_color = t['primary_color']
    bg_css = f"url('{bg_url}')" if bg_url else "#0a0a0c"
    
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg_css} no-repeat center fixed; background-size: cover; color: #E2E8F0; }}
    .glass {{ 
        background: rgba(10, 10, 15, 0.85) !important; 
        backdrop-filter: blur(15px); border-radius: 15px; 
        padding: 25px; border: 1px solid {p_color}44;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    h1, h2, h3 {{ color: {p_color} !important; font-family: 'Segoe UI', sans-serif; text-transform: uppercase; letter-spacing: 2px; }}
    p, label, span, .stMarkdown {{ color: #CBD5E1 !important; font-size: 16px; }}
    .stButton > button {{ 
        background: rgba(0, 242, 255, 0.1); color: {p_color}; 
        border: 1px solid {p_color}; border-radius: 5px; font-weight: bold;
    }}
    .stButton > button:hover {{ background: {p_color}; color: #000; box-shadow: 0 0 20px {p_color}; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

def draw_nexus_logo():
    color = st.session_state.theme.get('primary_color', '#00f2ff')
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; margin-bottom: 30px;">
        <div class="gateway">
            <div class="inner-circle"></div>
            <div class="core"></div>
        </div>
        <div style="color: {color}; font-size: 26px; font-weight: 900; margin-top: 15px; text-shadow: 0 0 15px {color}aa;">NEXUS OS GATEWAY</div>
    </div>
    <style>
    .gateway {{ width: 100px; height: 100px; border-radius: 50%; border: 4px double {color}; display: flex; align-items: center; justify-content: center; animation: rotate 5s linear infinite; }}
    .inner-circle {{ width: 60px; height: 60px; border-radius: 50%; border: 2px dashed {color}; animation: rotate-rev 3s linear infinite; }}
    .core {{ width: 20px; height: 20px; background: {color}; border-radius: 50%; position: absolute; box-shadow: 0 0 20px {color}; animation: pulse 1.5s infinite; }}
    @keyframes rotate {{ 100% {{ transform: rotate(360deg); }} }}
    @keyframes rotate-rev {{ 100% {{ transform: rotate(-360deg); }} }}
    @keyframes pulse {{ 0%, 100% {{ transform: scale(0.8); opacity: 0.6; }} 50% {{ transform: scale(1.2); opacity: 1; }} }}
    </style>
    """, unsafe_allow_html=True)

# --- [6] PHÂN TÍCH THIẾT BỊ (ADMIN) ---
def parse_agent(agent_str):
    os = "Unknown OS"
    if "Windows" in agent_str: os = "Windows"
    elif "Android" in agent_str: os = "Android"
    elif "iPhone" in agent_str: os = "iOS (iPhone)"
    elif "Macintosh" in agent_str: os = "MacOS"

    browser = "Unknown Browser"
    if "CocCoc" in agent_str: browser = "Cốc Cốc"
    elif "Edg/" in agent_str: browser = "MS Edge"
    elif "Chrome" in agent_str: browser = "Google Chrome"
    elif "Safari" in agent_str and "Chrome" not in agent_str: browser = "Safari"
    
    return os, browser

# --- [7] CÁC MÀN HÌNH ---

def screen_admin():
    apply_ui()
    st.title("🛡️ TRUNG TÂM KIỂM SOÁT TỐI CAO")
    
    tab1, tab2, tab3 = st.tabs(["📊 Lịch sử truy cập", "⚖️ Thực thi pháp luật", "📁 Dữ liệu thô"])
    
    with tab1:
        st.write("### Chi tiết thiết bị vào hệ thống")
        for log in reversed(st.session_state.access_logs):
            os, browser = parse_agent(log.get("info", ""))
            with st.expander(f"👤 {log['user']} | 🕒 {log['time']}"):
                col_a, col_b = st.columns(2)
                col_a.metric("Hệ điều hành", os)
                col_b.metric("Trình duyệt", browser)
                st.code(log.get("info"), language="text")

    with tab2:
        st.write("### Danh sách đen & Xử phạt")
        target = st.selectbox("Chọn đối tượng", list(st.session_state.users.keys()))
        crime = st.text_input("Tội danh / Lý do phạm tội")
        min_ban = st.number_input("Thời gian cấm (phút)", 1, 99999, 60)
        
        c1, c2 = st.columns(2)
        if c1.button("🔨 BAN (CẤM TRUY CẬP)"):
            until = (datetime.now() + timedelta(minutes=min_ban)).strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.punishments[target] = {"reason": crime, "until": until}
            luu_du_lieu(); st.warning(f"Đã thực thi lệnh cấm với {target}"); st.rerun()
        if c2.button("🔓 UNBAN (GỠ TỘI)"):
            if target in st.session_state.punishments:
                del st.session_state.punishments[target]
                luu_du_lieu(); st.success(f"Đã gỡ lệnh cấm cho {target}"); st.rerun()

    if st.button("⬅️ QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()

def screen_settings():
    apply_ui()
    st.title("⚙️ CÀI ĐẶT HỆ THỐNG")
    t = st.session_state.theme
    
    st.write("### 🖼️ Quản lý hình nền")
    bg_input = st.text_area("Danh sách Link ảnh nền (mỗi link 1 dòng)", "\n".join(t.get("bg_list", [])))
    col_a, col_b = st.columns(2)
    auto_on = col_a.toggle("Tự động đổi nền", t.get("auto_rotate"))
    rot_time = col_b.number_input("Thời gian đổi (phút)", 1, 60, t.get("rotate_min", 5))
    
    if st.button("💾 LƯU CẤU HÌNH"):
        t["bg_list"] = [link.strip() for link in bg_input.split("\n") if link.strip()]
        t["auto_rotate"] = auto_on
        t["rotate_min"] = rot_time
        luu_du_lieu(); st.success("Đã lưu cấu hình!"); st.rerun()

    if st.button("⬅️ QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()

def screen_profile():
    apply_ui()
    me = st.session_state.auth_status
    st.title("👤 HỒ SƠ CÁ NHÂN")
    prof = st.session_state.profiles.setdefault(me, {"nick": me, "bio": "Nexus Citizen", "avt": ""})
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if prof["avt"]: st.image(prof["avt"], width=200)
        else: st.info("Chưa có ảnh")
        new_avt = st.text_input("Link Avatar", prof["avt"])
    with col2:
        new_nick = st.text_input("Biệt danh", prof["nick"])
        new_bio = st.text_area("Tiểu sử", prof["bio"])
    
    if st.button("💾 CẬP NHẬT HỒ SƠ"):
        st.session_state.profiles[me] = {"nick": new_nick, "bio": new_bio, "avt": new_avt}
        luu_du_lieu(); st.success("Đã cập nhật!"); st.rerun()
    if st.button("⬅️ QUAY LẠI"): st.session_state.stage = "MENU"; st.rerun()

# --- [8] ĐIỀU HƯỚNG CHÍNH (ROUTER) ---
if st.session_state.stage == "AUTH":
    apply_ui(); draw_nexus_logo()
    _, cc, _ = st.columns([1, 1.5, 1])
    with cc:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        u = st.text_input("Định danh")
        p = st.text_input("Mật mã", type="password")
        if st.button("KẾT NỐI GATEWAY", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU"
                # Ghi log chi tiết
                agent = st.context.headers.get("User-Agent", "")
                st.session_state.access_logs.append({
                    "user": u, "time": datetime.now().strftime("%d/%m %H:%M:%S"), "info": agent
                })
                luu_du_lieu(); st.rerun()
            else: st.error("Sai thông tin!")
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    # Kiểm tra lệnh cấm
    me = st.session_state.auth_status
    if me in st.session_state.punishments:
        ban = st.session_state.punishments[me]
        until = datetime.strptime(ban["until"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() < until:
            st.markdown(f"""
            <div class='glass' style='border-color: #ff4b4b;'>
                <h2 style='color: #ff4b4b !important;'>🚫 LỆNH TRUY NÃ & CẤM</h2>
                <p><b>Tội danh:</b> {ban['reason']}</p>
                <p><b>Thời hạn đến:</b> {ban['until']}</p>
                <p>Bạn không thể sử dụng hệ thống cho đến khi hết hạn phạt.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("ĐĂNG XUẤT"): st.session_state.stage = "AUTH"; st.rerun()
            st.stop()

    st.title(f"🚀 DASHBOARD | {me.upper()}")
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    if col1.button("🧠 AI ASSISTANT", use_container_width=True): st.session_state.stage = "CHAT"; st.rerun()
    if col2.button("🌐 COMMUNITY", use_container_width=True): st.session_state.stage = "SOCIAL"; st.rerun()
    if col3.button("👤 PROFILE", use_container_width=True): st.session_state.stage = "PROFILE"; st.rerun()
    
    c1, c2 = st.columns(2)
    if c1.button("⚙️ SETTINGS", use_container_width=True): st.session_state.stage = "SETTINGS"; st.rerun()
    if st.session_state.auth_status.lower() == "thiên phát":
        if c2.button("🛡️ ADMIN PANEL", use_container_width=True): st.session_state.stage = "ADMIN"; st.rerun()
        
    if st.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Thêm logic dự phòng cho các stage khác để không bị trắng màn hình
elif st.session_state.stage == "CHAT":
    apply_ui(); st.title("AI CHAT (Đang nâng cấp...)")
    if st.button("Về Menu"): st.session_state.stage = "MENU"; st.rerun()
elif st.session_state.stage == "SOCIAL":
    apply_ui(); st.title("COMMUNITY (Đang nâng cấp...)")
    if st.button("Về Menu"): st.session_state.stage = "MENU"; st.rerun()
elif st.session_state.stage == "PROFILE": screen_profile()
elif st.session_state.stage == "ADMIN": screen_admin()
elif st.session_state.stage == "SETTINGS": screen_settings()
