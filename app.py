# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import time, random, json, base64, requests
from openai import OpenAI

# -------------------- [1] CẤU HÌNH --------------------
VERSION = "V5100"
CREATOR = "Lê Trần Thiên Phát"
FILE_DATA = "data.json"

WALLPAPERS = [
    "https://images.unsplash.com/photo-1614850523296-d8c1af93d400?q=80&w=2070",
    "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?q=80&w=2071",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072",
    "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=2070"
]

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except:
    st.error("Cấu hình GitHub/Groq Secrets chưa đúng!")
    st.stop()

st.set_page_config(page_title="NEXUS GATEWAY", layout="wide", initial_sidebar_state="collapsed")

# -------------------- [2] QUẢN LÝ DỮ LIỆU --------------------
def handle_db(u=None, save=False):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    res = requests.get(url, headers=headers)
    db = {"users": {"admin": "123", "Phát": "123"}, "user_versions": {}, "global_chat": []}
    sha = None
    if res.status_code == 200:
        db = json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
        sha = res.json().get("sha")

    if "user_versions" not in db: db["user_versions"] = {}
    if "users" not in db: db["users"] = {"admin": "123", "Phát": "123"}
    if "global_chat" not in db: db["global_chat"] = []

    if save and u:
        db["user_versions"][u] = VERSION
        content = base64.b64encode(json.dumps(db, indent=4, ensure_ascii=False).encode()).decode()
        payload = {"message": f"Update {VERSION}", "content": content, "sha": sha}
        requests.put(url, headers=headers, json=payload)
    
    # Nút lưu dùng chung cho cộng đồng
    if save and not u:
        content = base64.b64encode(json.dumps(db, indent=4, ensure_ascii=False).encode()).decode()
        payload = {"message": "Update Community Data", "content": content, "sha": sha}
        requests.put(url, headers=headers, json=payload)
        
    return db

# -------------------- [3] BOOT ANIMATION 10s --------------------
def show_boot():
    boot_html = """
    <style>
        body { background: black; margin: 0; overflow: hidden; display: flex; align-items: center; justify-content: center; height: 100vh; font-family: 'Arial', sans-serif; }
        .box { position: relative; text-align: center; color: white; }
        .txt { position: absolute; width: 100%; left: 0; top: 50%; transform: translateY(-50%); opacity: 0; font-size: 35px; letter-spacing: 10px; font-weight: 100; }
        .t1 { animation: flow 1.5s ease-in-out 0s forwards; }
        .t2 { animation: flow 1.5s ease-in-out 1.5s forwards; }
        .t3 { animation: flow 1.5s ease-in-out 3s forwards; }
        .t4 { animation: flow 2s ease-in-out 4.5s forwards; color: #00f2ff; text-shadow: 0 0 20px #00f2ff; font-weight: bold; }
        @keyframes flow {
            0% { opacity: 0; filter: blur(10px); transform: translateY(0) scale(0.8); }
            50% { opacity: 1; filter: blur(0px); transform: translateY(-50%) scale(1); }
            100% { opacity: 0; filter: blur(10px); transform: translateY(-100%) scale(1.2); }
        }
        .logo-wrap { opacity: 0; animation: logoIn 3s ease-out 6.5s forwards; }
        @keyframes logoIn { from { opacity: 0; transform: scale(0.5) rotate(-90deg); } to { opacity: 1; transform: scale(1) rotate(0deg); } }
        svg { width: 120px; height: 120px; }
        .p-line { fill: none; stroke: white; stroke-width: 2; stroke-dasharray: 500; stroke-dashoffset: 500; animation: draw 2s ease-in-out 7s forwards; }
        @keyframes draw { to { stroke-dashoffset: 0; } }
        .nexus-txt { letter-spacing: 15px; margin-top: 15px; font-weight: 200; animation: pulse 1s infinite alternate; }
        @keyframes pulse { from { opacity: 0.5; } to { opacity: 1; text-shadow: 0 0 15px white; } }
    </style>
    <div class="box">
        <div class="txt t1">WELCOME</div>
        <div class="txt t2">TO</div>
        <div class="txt t3">THIS SUPER</div>
        <div class="txt t4">A.I! NEXUS OS</div>
        <div class="logo-wrap">
            <svg viewBox="0 0 100 100">
                <circle class="p-line" cx="50" cy="50" r="45" />
                <path class="p-line" d="M30 30 L70 70 M70 30 L30 70" />
                <rect class="p-line" x="20" y="20" width="60" height="60" rx="5" />
            </svg>
            <div class="nexus-txt">GATEWAY</div>
            <p style="font-size: 10px; color: #555; margin-top: 10px;">THE NEW VERSION IS RELEASED</p>
        </div>
    </div>
    """
    components.html(boot_html, height=600)

# -------------------- [4] MÀN HÌNH ĐĂNG NHẬP --------------------
def show_login():
    if 'bg' not in st.session_state: st.session_state.bg = random.choice(WALLPAPERS)
    
    st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("{st.session_state.bg}"); background-size: cover; }}
    .login-box {{
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(30px);
        padding: 50px; border-radius: 40px; border: 1px solid rgba(255,255,255,0.15);
        text-align: center; max-width: 400px; margin: auto; margin-top: 50px;
    }}
    .nexus-glow {{ font-size: 3.5rem; font-weight: 900; color: #ffffff; text-shadow: 0 0 20px #fff, 0 0 40px #00f2ff; letter-spacing: 10px; margin-bottom: 40px; }}
    .stButton>button {{ background: transparent; color: white; border: 1px solid #fff; border-radius: 20px; transition: 0.3s; width: 100%; }}
    .stButton>button:hover {{ background: #fff; color: #000; box-shadow: 0 0 20px #fff; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("<div class='nexus-glow'>NEXUS</div>", unsafe_allow_html=True)
    
    u = st.text_input("USER IDENTITY")
    p = st.text_input("PASSWORD", type="password")
    
    if st.button("INITIALIZE SYSTEM"):
        db = handle_db()
        if u in db["users"] and db["users"][u] == p:
            with st.spinner("🚀 Security verification in progress..."):
                time.sleep(2)
                handle_db(u, save=True)
                st.session_state.user = u
                st.session_state.stage = "MAIN"
                st.rerun()
        else: st.error("Access Denied!")
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------- [5] GIAO DIỆN CHÍNH (CÓ ĐỦ TÍNH NĂNG) --------------------
def show_main():
    # CSS cho bên trong app
    st.markdown("""
    <style>
        .stApp { background: #0e1117; color: white; }
        .glass-card { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); padding: 20px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar điều hướng
    with st.sidebar:
        st.markdown(f"## 🌌 NEXUS OS")
        st.markdown(f"**Người dùng:** {st.session_state.user}")
        st.markdown("---")
        menu = st.radio("ĐIỀU HƯỚNG", ["🏠 Trang chủ", "🧠 NEXUS A.I", "🌐 Cộng đồng", "⚙️ Cài đặt"])
        st.markdown("---")
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.stage = "LOGIN"
            st.rerun()

    # --- TAB TRANG CHỦ ---
    if menu == "🏠 Trang chủ":
        st.title("📊 TRUNG TÂM ĐIỀU KHIỂN")
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.write("Chào mừng trở lại trạm điều khiển NEXUS. Hệ thống đang hoạt động ổn định.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Phiên bản", VERSION)
        c2.metric("Trạng thái", "ONLINE", "Ping: 12ms")
        c3.metric("Bảo mật", "Lớp 3", "E2E Active")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB A.I CHAT ---
    elif menu == "🧠 NEXUS A.I":
        st.title("🧠 NEXUS SUPER A.I")
        st.caption("Trợ lý trí tuệ nhân tạo được hỗ trợ bởi Groq.")
        
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": f"Xin chào {st.session_state.user}, tôi là NEXUS A.I. Tôi có thể giúp gì cho bạn hôm nay?"}]

        # Hiển thị lịch sử chat
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Input người dùng
        if prompt := st.chat_input("Nhập lệnh cho NEXUS..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    # Kết nối Groq API
                    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
                    sys_prompt = {"role": "system", "content": f"Bạn là NEXUS A.I, trợ lý ảo thông minh. Người đang nói chuyện với bạn là {st.session_state.user}. Trả lời ngắn gọn, thông minh và hữu ích."}
                    
                    # Gọi API
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[sys_prompt] + st.session_state.messages[1:] # Bỏ qua câu chào mặc định để tối ưu token
                    )
                    
                    bot_reply = response.choices[0].message.content
                    st.markdown(bot_reply)
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                except Exception as e:
                    st.error(f"Lỗi kết nối bộ não AI: {e}")

    # --- TAB CỘNG ĐỒNG ---
    elif menu == "🌐 Cộng đồng":
        st.title("🌐 KÊNH GIAO TIẾP TOÀN CẦU")
        st.caption("Nơi các người dùng NEXUS kết nối với nhau.")
        
        db = handle_db()
        chat_data = db.get("global_chat", [])
        
        st.markdown("<div class='glass-card' style='height: 400px; overflow-y: auto;'>", unsafe_allow_html=True)
        if not chat_data:
            st.write("Chưa có tin nhắn nào. Hãy là người đầu tiên!")
        else:
            for c in chat_data[-15:]: # Hiện 15 tin nhắn gần nhất
                st.markdown(f"**{c['user']}**: {c['msg']} *(Lúc {c['time']})*")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Gửi tin nhắn mới
        with st.form("chat_form", clear_on_submit=True):
            new_msg = st.text_input("Gửi tin nhắn vào không gian chung...")
            if st.form_submit_button("Gửi"):
                if new_msg:
                    timestamp = time.strftime("%H:%M:%S")
                    db["global_chat"].append({"user": st.session_state.user, "msg": new_msg, "time": timestamp})
                    handle_db(save=True) # Lưu lên GitHub
                    st.rerun()

    # --- TAB CÀI ĐẶT ---
    elif menu == "⚙️ Cài đặt":
        st.title("⚙️ CÀI ĐẶT HỆ THỐNG")
        
        st.subheader("Thông tin tài khoản")
        st.write(f"- **Tên truy cập:** {st.session_state.user}")
        st.write(f"- **Quyền hạn:** {'Admin' if st.session_state.user == 'Phát' else 'User'}")
        
        st.subheader("Phiên bản hệ điều hành")
        st.info(f"Bạn đang sử dụng NEXUS OS {VERSION} - Bản cập nhật GATEWAY.")
        
        st.subheader("Giao diện")
        st.color_picker("Chọn màu chủ đạo (Tính năng đang phát triển)", "#00f2ff")

# -------------------- [6] ĐIỀU HƯỚNG CHÍNH --------------------
if 'stage' not in st.session_state: st.session_state.stage = "BOOT"

def main():
    if st.session_state.stage == "BOOT":
        show_boot()
        time.sleep(10)
        st.session_state.stage = "LOGIN"
        st.rerun()
    elif st.session_state.stage == "LOGIN":
        show_login()
    elif st.session_state.stage == "MAIN":
        show_main()

if __name__ == "__main__":
    main()
