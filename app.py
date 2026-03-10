# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests
from datetime import datetime

# --- [1] THÔNG TIN CHUNG ---
CREATOR = "Lê Trần Thiên Phát"
VERSION = "NEXUS OS GATEWAY - STABLE"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_KEY_2024"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("👉 Vui lòng cấu hình Keys trong phần Settings > Secrets trên Streamlit.")
    st.stop()

st.set_page_config(page_title=f"NEXUS OS | {CREATOR}", layout="wide")

# --- [2] HÀM BỔ TRỢ ---
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
    st.session_state.access_logs = st.session_state.access_logs[-100:] 
    luu_du_lieu()

def draw_animated_logo():
    color = st.session_state.theme.get('primary_color', '#00f2ff')
    st.markdown(f"""
    <style>
    .logo-box {{ display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 30px; }}
    .gateway-ring {{
        width: 100px; height: 100px;
        border-radius: 50%;
        border: 3px solid rgba(255,255,255,0.1);
        border-top: 4px solid {color};
        border-bottom: 4px solid {color};
        animation: spin 3s linear infinite;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 0 25px {color}66;
    }}
    .gateway-core {{
        width: 40px; height: 40px;
        background: {color};
        border-radius: 50%;
        animation: pulse 1.5s ease-in-out infinite;
        box-shadow: 0 0 15px {color};
    }}
    .gateway-text {{
        margin-top: 15px; font-size: 24px; font-weight: 800;
        letter-spacing: 3px; color: #F8F9FA;
        text-shadow: 0px 0px 10px {color}88;
    }}
    @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
    @keyframes pulse {{ 0%, 100% {{ transform: scale(0.8); opacity: 0.7;}} 50% {{ transform: scale(1.1); opacity: 1; }} }}
    </style>
    <div class="logo-box">
        <div class="gateway-ring"><div class="gateway-core"></div></div>
        <div class="gateway-text">NEXUS OS GATEWAY</div>
    </div>
    """, unsafe_allow_html=True)

def apply_ui():
    t = st.session_state.theme
    p_color = t['primary_color']
    bg = f"url('{t['bg_url']}')" if t['bg_url'] else "#0f172a" # Màu nền mặc định tối, dịu mắt
    st.markdown(f"""
    <style>
    .stApp {{ background: {bg} no-repeat center fixed; background-size: cover; }}
    
    /* Làm hộp nền mờ tối màu hơn để chữ sáng nổi bật, không bị chói */
    .glass-box {{
        background: rgba(15, 23, 42, 0.75) !important; 
        backdrop-filter: blur(12px);
        border-radius: 12px;
        padding: 25px;
        border: 1px solid {p_color}44;
        color: #F8F9FA;
    }}
    
    /* Chữ dịu mắt, bóng mờ nhẹ nhàng */
    h1, h2, h3, p, label, .stMarkdown {{ 
        color: #F8F9FA !important; 
        text-shadow: 0px 2px 5px rgba(0,0,0,0.5);
    }}
    
    /* Ô chat AI mượt mà */
    [data-testid="stChatMessage"] {{
        background: rgba(30, 41, 59, 0.8) !important;
        border-radius: 10px;
        border-left: 3px solid {p_color};
    }}
    
    /* Nút bấm tinh tế */
    .stButton > button {{ 
        background: rgba(15, 23, 42, 0.8) !important;
        color: #F8F9FA !important;
        border: 1px solid {p_color} !important; 
        border-radius: 8px; 
        transition: 0.3s;
    }}
    .stButton > button:hover {{ background: {p_color} !important; color: #000 !important; box-shadow: 0 0 10px {p_color}; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [4] MÀN HÌNH CHỨC NĂNG ---
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

    if c_id and c_id in lib:
        for m in lib[c_id]:
            with st.chat_message(m["role"]): st.write(giai_ma(m["content"]))

    if p := st.chat_input("Nhập câu hỏi của bạn..."):
        if not c_id:
            c_id = f"Chat_{datetime.now().strftime('%H%M%S')}"
            st.session_state.current_chat = c_id
            lib[c_id] = []
        
        lib[c_id].append({"role": "user", "content": ma_hoa(p)})
        with st.chat_message("user"): st.write(p)
        
        with st.chat_message("assistant"):
            res_box = st.empty(); full_res = ""
            try:
                client = OpenAI(api_key=GROQ_KEYS[0], base_url="https://api.groq.com/openai/v1")
                context = [{"role": m["role"], "content": giai_ma(m["content"])} for m in lib[c_id][-6:]]
                stream = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role":"system","content":f"Bạn là NEXUS OS. Phục vụ người dùng thân thiện, dễ hiểu."}] + context,
                    stream=True,
                    temperature=st.session_state.theme.get('ai_temp', 0.7)
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_box.markdown(full_res + "▌")
                res_box.markdown(full_res)
                lib[c_id].append({"role": "assistant", "content": ma_hoa(full_res)})
                luu_du_lieu()
            except Exception as e:
                st.error("Kết nối AI đang bận, vui lòng thử lại sau.")

def screen_admin():
    apply_ui()
    st.title("🛡️ BẢNG ĐIỀU KHIỂN QUẢN TRỊ")
    
    tab1, tab2 = st.tabs(["📊 Lịch sử truy cập", "👥 Người dùng"])
    
    with tab1:
        st.write("Danh sách thiết bị truy cập gần đây:")
        for log in reversed(st.session_state.access_logs):
            with st.expander(f"👤 {log['user']} - 🕒 {log['time']}"):
                # SỬA LỖI KEYERROR TẠI ĐÂY: Dùng .get() để an toàn với dữ liệu cũ
                info = log.get('info', log.get('device', 'Không xác định được thiết bị'))
                
                st.write(f"**Chi tiết:** {info}")
                if "Windows" in info: st.info("🖥️ Máy tính Windows")
                elif "Android" in info: st.info("📱 Điện thoại Android")
                elif "iPhone" in info or "Mac OS" in info: st.info("🍎 Thiết bị Apple")
                
                if "Edg/" in info: st.write("Trình duyệt: Edge")
                elif "Chrome/" in info: st.write("Trình duyệt: Chrome")
                elif "CocCoc/" in info: st.write("Trình duyệt: Cốc Cốc")

    with tab2:
        st.json(st.session_state.users)

    if st.button("🏠 QUAY LẠI"):
        st.session_state.stage = "MENU"; st.rerun()

def screen_settings():
    apply_ui()
    st.title("⚙️ TÙY CHỈNH HỆ THỐNG")
    t = st.session_state.theme
    
    st.write("Cá nhân hóa giao diện và trải nghiệm của bạn.")
    new_bg = st.text_input("Đường dẫn ảnh nền (Link URL)", t['bg_url'])
    new_color = st.color_picker("Màu nhấn (Accent Color)", t['primary_color'])
    new_temp = st.slider("Mức độ sáng tạo của AI", 0.0, 1.0, t.get('ai_temp', 0.7))
    
    if st.button("💾 LƯU THAY ĐỔI", use_container_width=True):
        st.session_state.theme.update({
            "bg_url": new_bg, "primary_color": new_color, "ai_temp": new_temp
        })
        luu_du_lieu()
        st.success("Đã cập nhật cấu hình thành công!")
        time.sleep(1); st.rerun()

    if st.button("🏠 QUAY LẠI"):
        st.session_state.stage = "MENU"; st.rerun()

# --- [5] ĐIỀU HƯỚNG CHÍNH ---
if st.session_state.stage == "AUTH":
    apply_ui()
    st.write("<br><br>", unsafe_allow_html=True)
    draw_animated_logo() # Hiển thị Logo động
    
    _, cc, _ = st.columns([1, 1.5, 1])
    with cc:
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("TIẾN VÀO GATEWAY", use_container_width=True):
            if u in st.session_state.users and st.session_state.users[u] == p:
                st.session_state.auth_status = u
                st.session_state.stage = "MENU"
                ghi_log(u)
                st.rerun()
            else: st.error("Thông tin không chính xác. Vui lòng thử lại!")
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "MENU":
    apply_ui()
    st.title(f"Chào mừng trở lại, {st.session_state.auth_status}")
    
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    if st.session_state.auth_status.lower() == "thiên phát":
        if st.button("🛡️ QUẢN TRỊ HỆ THỐNG", use_container_width=True):
            st.session_state.stage = "ADMIN"; st.rerun()
    
    c1, c2 = st.columns(2)
    if c1.button("🧠 TRỢ LÝ AI", use_container_width=True):
        st.session_state.stage = "CHAT"; st.rerun()
    if c2.button("⚙️ CÀI ĐẶT", use_container_width=True):
        st.session_state.stage = "SETTINGS"; st.rerun()
    
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True):
        st.session_state.auth_status = None; st.session_state.stage = "AUTH"; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.stage == "CHAT": screen_chat()
elif st.session_state.stage == "ADMIN": screen_admin()
elif st.session_state.stage == "SETTINGS": screen_settings()
