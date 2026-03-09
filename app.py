# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests
from datetime import datetime, timedelta

# --- [1] THÔNG TIN CHUNG ---
CREATOR = "Lê Trần Thiên Phát"
VERSION = "V4800 - ULTIMATE PLUS"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

# Kiểm tra "chìa khóa" hệ thống
try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("👉 Anh Phát ơi, nhớ dán Keys vào phần Settings > Secrets trên Streamlit nhé!")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR}", layout="wide")

# --- [2] HÀM BỔ TRỢ (MÃ HÓA & LƯU TRỮ) ---
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
        "chat_library": st.session_state.chat_library, "friends": st.session_state.friends,
        "friend_requests": st.session_state.friend_requests, "groups": st.session_state.groups,
        "access_logs": st.session_state.get("access_logs", [])
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, indent=4).encode()).decode()
        payload = {"message": f"Nexus Update {datetime.now()}", "content": content}
        if sha: payload["sha"] = sha
        requests.put(url, headers=headers, json=payload)
    except: pass

# --- [3] KHỞI TẠO HỆ THỐNG ---
if 'initialized' not in st.session_state:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {"admin": "123", "Thiên Phát": "2002"})
    st.session_state.theme = db.get("theme", {
        "primary_color": "#00f2ff", 
        "bg_url": "", 
        "ai_temp": 0.7,
        "font_size": "16px",
        "glass_opacity": 0.3
    })
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.friends = db.get("friends", {})
    st.session_state.friend_requests = db.get("friend_requests", {})
    st.session_state.groups = db.get("groups", {"Chung": []})
    st.session_state.access_logs = db.get("access_logs", [])
    st.session_state.stage = "AUTH"
    st.session_state.auth_status = None
    st.session_state.current_chat = None
    st.session_state.initialized = True

def ghi_log(user):
    agent = st.context.headers.get("User-Agent", "Không rõ thiết bị")
    log_entry = {
        "user": user,
        "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "info": agent
    }
    st.session_state.access_logs.append(log_entry)
    # Giữ log 14 ngày
    st.session_state.access_logs = st.session_state.access_logs[-100:] # Lưu tối đa 100 lần gần nhất
    luu_du_lieu()

def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    op = t.get('glass_opacity', 0.3)
    bg = f"url('{t['bg_url']}')" if t['bg_url'] else "#0e1117"
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg} no-repeat center fixed; background-size: cover; }}
    .glass-box {{
        background: rgba(255, 255, 255, {op}) !important;
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid {p_color}55;
    }}
    h1, h2, h3, p, label {{ 
        color: white !important; 
        text-shadow: 2px 2px 8px {p_color};
        font-size: {t.get('font_size', '16px')};
    }}
    .stButton > button {{ border: 2px solid {p_color} !important; border-radius: 20px; font-weight: bold; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [4] MÀN HÌNH AI CHAT (SỬA LỖI KHÔNG TRẢ LỜI) ---
def screen_chat():
    apply_ui()
    user = st.session_state.auth_status
    lib = st.session_state.chat_library.setdefault(user, {})
    
    with st.sidebar:
        st.title("🧠 NEXUS AI")
        if st.button("➕ TẠO CHAT MỚI", use_container_width=True):
            st.session_state.current_chat = None; st.rerun()
        
        st.divider()
        for t in list(lib.keys()):
            c1, c2 = st.columns([0.8, 0.2])
            if c1.button(f"📄 {t[:15]}", key=f"s_{t}", use_container_width=True):
                st.session_state.current_chat = t; st.rerun()
            if c2.button("🗑️", key=f"d_{t}"):
                del lib[t]; luu_du_lieu(); st.rerun()
        
        if st.button("⬅️ VỀ MENU", use_container_width=True):
            st.session_state.stage = "MENU"; st.rerun()

    c_id = st.session_state.current_chat
    st.subheader(f"💬 {c_id if c_id else 'Phiên làm việc mới'}")

    # Hiển thị lịch sử
    if c_id and c_id in lib:
        for m in lib[c_id]:
            with st.chat_message(m["role"]): st.write(giai_ma(m["content"]))

    # Ô nhập liệu
    if p := st.chat_input("Anh Phát muốn hỏi gì nè?"):
        if not c_id:
            c_id = f"Chat_{datetime.now().strftime('%H%M%S')}"
            st.session_state.current_chat = c_id
            lib[c_id] = []
        
        # Lưu câu hỏi
        lib[c_id].append({"role": "user", "content": ma_hoa(p)})
        with st.chat_message("user"): st.write(p)
        
        # AI Trả lời
        with st.chat_message("assistant"):
            res_box = st.empty(); full_res = ""
            try:
                client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
                # Lấy lịch sử 5 câu gần nhất để AI hiểu ngữ cảnh
                context = [{"role": m["role"], "content": giai_ma(m["content"])} for m in lib[c_id][-6:]]
                stream = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role":"system","content":f"Bạn là NEXUS OS, người tạo ra bạn là {CREATOR}."}] + context,
                    stream=True,
                    temperature=st.session_state.theme.get('ai_temp', 0.7)
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_box.markdown(full_res + "▌")
                res_box.markdown(full_res)
                # Lưu câu trả lời
                lib[c_id].append({"role": "assistant", "content": ma_hoa(full_res)})
                luu_du_lieu()
            except Exception as e:
                st.error(f"Lỗi AI rồi anh ơi: {str(e)}")

# --- [5] MÀN HÌNH ADMIN (CHO ANH PHÁT) ---
def screen_admin():
    apply_ui()
    st.title("🛡️ BẢNG ĐIỀU KHIỂN CHỦ NHÂN")
    
    tab1, tab2 = st.tabs(["📊 Lịch sử truy cập", "👥 Quản lý User"])
    
    with tab1:
        st.write("### Danh sách thiết bị vào hệ thống (14 ngày)")
        for log in reversed(st.session_state.access_logs):
            with st.expander(f"👤 {log['user']} - 🕒 {log['time']}"):
                # Phân tích chuỗi Agent cho bình dân dễ hiểu
                info = log['info']
                st.write(f"**Chi tiết:** {info}")
                if "Windows" in info: st.info("🖥️ Máy tính Windows")
                elif "Android" in info: st.info("📱 Điện thoại Android")
                elif "iPhone" in info: st.info("🍎 Điện thoại iPhone")
                
                if "Edg/" in info: st.write("Trình duyệt: Microsoft Edge")
                elif "Chrome/" in info: st.write("Trình duyệt: Google Chrome")
                elif "CocCoc/" in info: st.write("Trình duyệt: Cốc Cốc")

    with tab2:
        st.write("### Danh sách tài khoản")
        st.json(st.session_state.users)

    if st.button("🏠 QUAY LẠI"):
        st.session_state.stage = "MENU"; st.rerun()

# --- [6] MÀN HÌNH SETTINGS (NHIỀU OPTION) ---
def screen_settings():
    apply_ui()
    st.title("⚙️ TÙY CHỈNH HỆ THỐNG")
    t = st.session_state.theme
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("#### 🎨 Giao diện")
        new_bg = st.text_input("Link ảnh nền", t['bg_url'], placeholder="Dán link ảnh từ Google vào đây...")
        new_color = st.color_picker("Màu Neon chủ đạo", t['primary_color'])
        new_op = st.slider("Độ trong suốt của bảng (Glass)", 0.1, 1.0, float(t.get('glass_opacity', 0.3)))
        new_font = st.select_slider("Kích cỡ chữ", options=["12px", "14px", "16px", "18px", "20px"], value=t.get('font_size', '16px'))

    with col2:
        st.write("#### 🧠 Trí tuệ AI")
        new_temp = st.slider("Độ 'phiêu' của AI (Sáng tạo)", 0.0, 1.0, t.get('ai_temp', 0.7))
        st.info("Thấp: AI trả lời chính xác, thực tế. Cao: AI trả lời văn vẻ, bay bổng.")
    
    if st.button("💾 LƯU TẤT CẢ THAY ĐỔI", use_container_width=True):
        st.session_state.theme.update({
            "bg_url": new_bg, "primary_color": new_color, 
            "ai_temp": new_temp, "glass_opacity": new_op,
            "font_size": new_font
        })
        luu_du_lieu()
        st.success("Đã lưu rồi nhé anh Phát!")
        time.sleep(1); st.rerun()

    if st.button("🏠 QUAY LẠI"):
        st.session_state.stage = "MENU"; st.rerun()

# --- [7] ĐIỀU HƯỚNG CHÍNH ---
if st.session_state.stage == "AUTH":
    apply_ui()
    st.markdown("<h1 style='text-align:center;'>🔐 ĐĂNG NHẬP NEXUS</h1>", unsafe_allow_html=True)
    _, cc, _ = st.columns([1, 2, 1])
    with cc:
        u = st.text_input("Tên của anh")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("VÀO HỆ THỐNG", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU"
                ghi_log(u)
                st.rerun()
            else: st.error("Sai tên hoặc mật khẩu rồi!")

elif st.session_state.stage == "MENU":
    apply_ui()
    st.title(f"🚀 XIN CHÀO {st.session_state.auth_status.upper()}")
    
    with st.container():
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        if st.session_state.auth_status.lower() == "thiên phát":
            if st.button("🛡️ BẢNG ĐIỀU KHIỂN ADMIN", use_container_width=True):
                st.session_state.stage = "ADMIN"; st.rerun()
        
        c1, c2 = st.columns(2)
        if c1.button("🧠 CHAT VỚI AI", use_container_width=True):
            st.session_state.stage = "CHAT"; st.rerun()
        if c2.button("⚙️ CÀI ĐẶT HỆ THỐNG", use_container_width=True):
            st.session_state.stage = "SETTINGS"; st.rerun()
        
        if st.button("🚪 THOÁT HỆ THỐNG", use_container_width=True):
            st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "ADMIN": screen_admin()
elif st.session_state.stage == "SETTINGS": screen_settings()
