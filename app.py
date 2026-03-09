# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import time, random, json, base64, requests
from openai import OpenAI

# -------------------- [1] CẤU HÌNH HỆ THỐNG --------------------
VERSION = "V5100"
CREATOR = "Lê Trần Thiên Phát"
FILE_DATA = "data.json"

WALLPAPERS = [
    "https://images.unsplash.com/photo-1614850523296-d8c1af93d400?q=80&w=2070",
    "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?q=80&w=2071",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072",
    "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=2070",
    "https://images.unsplash.com/photo-1506318137071-a8e063b4bec0?q=80&w=2093"
]

try:
    GITHUB_TOKEN = st.secrets["GH_TOKEN"]
    REPO_NAME = st.secrets["GH_REPO"]
    GROQ_API_KEYS = st.secrets["GROQ_KEYS"]
except Exception as e:
    st.error(f"Lỗi cấu hình Secrets: {e}")
    st.stop()

st.set_page_config(page_title="NEXUS GATEWAY", layout="wide", initial_sidebar_state="collapsed")

# -------------------- [2] QUẢN LÝ DỮ LIỆU ĐA TẦNG --------------------
def load_db():
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    db = {
        "users": {"admin": "123", "Phát": "123"}, "user_versions": {},
        "global_chat": [], "friends": {}, "friend_requests": {}, 
        "p2p_chats": {}, "groups": {}
    }
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
            db.update(content) # Cập nhật dữ liệu từ GitHub vào dict mặc định
            st.session_state.sha = res.json().get("sha")
    except: pass
    return db

def save_db(db):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    content = base64.b64encode(json.dumps(db, indent=4, ensure_ascii=False).encode()).decode()
    payload = {"message": f"NEXUS Sync {VERSION}", "content": content}
    if 'sha' in st.session_state and st.session_state.sha:
        payload["sha"] = st.session_state.sha
    try:
        res = requests.put(url, headers=headers, json=payload)
        if res.status_code in [200, 201]:
            st.session_state.sha = res.json().get("content", {}).get("sha")
    except: pass

# -------------------- [3] BOOT ANIMATION (10s) --------------------
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
        @keyframes flow { 0% { opacity: 0; filter: blur(10px); transform: translateY(0) scale(0.8); } 50% { opacity: 1; filter: blur(0px); transform: translateY(-50%) scale(1); } 100% { opacity: 0; filter: blur(10px); transform: translateY(-100%) scale(1.2); } }
        .logo-wrap { opacity: 0; animation: logoIn 3s ease-out 6.5s forwards; }
        @keyframes logoIn { from { opacity: 0; transform: scale(0.5) rotate(-90deg); } to { opacity: 1; transform: scale(1) rotate(0deg); } }
        svg { width: 120px; height: 120px; }
        .p-line { fill: none; stroke: white; stroke-width: 2; stroke-dasharray: 500; stroke-dashoffset: 500; animation: draw 2s ease-in-out 7s forwards; }
        @keyframes draw { to { stroke-dashoffset: 0; } }
        .nexus-txt { letter-spacing: 15px; margin-top: 15px; font-weight: 200; animation: pulse 1s infinite alternate; }
        @keyframes pulse { from { opacity: 0.5; } to { opacity: 1; text-shadow: 0 0 15px white; } }
    </style>
    <div class="box">
        <div class="txt t1">WELCOME</div><div class="txt t2">TO</div><div class="txt t3">THIS SUPER</div><div class="txt t4">A.I! NEXUS OS</div>
        <div class="logo-wrap">
            <svg viewBox="0 0 100 100">
                <circle class="p-line" cx="50" cy="50" r="45" /><path class="p-line" d="M30 30 L70 70 M70 30 L30 70" /><rect class="p-line" x="20" y="20" width="60" height="60" rx="5" />
            </svg>
            <div class="nexus-txt">GATEWAY</div>
        </div>
    </div>
    """
    components.html(boot_html, height=600)

# -------------------- [4] GIAO DIỆN ĐĂNG NHẬP (SƯƠNG MỜ) --------------------
def show_login():
    if 'bg' not in st.session_state: st.session_state.bg = random.choice(WALLPAPERS)
    
    st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("{st.session_state.bg}"); background-size: cover; background-position: center; }}
    .login-box {{
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(25px);
        padding: 50px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.2);
        text-align: center; max-width: 400px; margin: 100px auto; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .nexus-glow {{ font-size: 3rem; font-weight: 900; color: white; text-shadow: 0 0 20px #fff, 0 0 40px #00f2ff; letter-spacing: 8px; margin-bottom: 30px; }}
    .stButton>button {{ border: 1px solid white; color: white; background: transparent; transition: 0.3s; width: 100%; border-radius: 10px; }}
    .stButton>button:hover {{ background: white; color: black; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-box'><div class='nexus-glow'>NEXUS</div>", unsafe_allow_html=True)
    u = st.text_input("Tài khoản")
    p = st.text_input("Mật khẩu", type="password")
    
    if st.button("XÁC THỰC HỆ THỐNG"):
        db = load_db()
        if u in db["users"] and db["users"][u] == p:
            with st.spinner("🚀 Kích hoạt trạm không gian..."):
                time.sleep(1.5)
                db["user_versions"][u] = VERSION
                save_db(db)
                st.session_state.user = u
                st.session_state.stage = "MAIN"
                st.rerun()
        else: st.error("Lỗi bảo mật: Sai thông tin!")
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------- [5] GIAO DIỆN CHÍNH (FULL TÍNH NĂNG + SƯƠNG MỜ) --------------------
def show_main():
    bg_url = st.session_state.get('bg', WALLPAPERS[0])
    
    # CSS: Hiệu ứng sương mờ cho toàn bộ App
    st.markdown(f"""
    <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("{bg_url}");
            background-size: cover; background-attachment: fixed; color: white;
        }}
        /* Sương mờ cho Sidebar */
        [data-testid="stSidebar"] {{
            background: rgba(0, 0, 0, 0.4) !important;
            backdrop-filter: blur(20px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }}
        /* Sương mờ cho Card, Chat, Form */
        .glass-panel, .stChatMessage, div[data-testid="stForm"] {{
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(15px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 15px !important; padding: 20px; color: white !important;
        }}
        h1, h2, h3, p, label, span {{ color: white !important; }}
        .stTextInput input {{ background: rgba(0,0,0,0.5) !important; color: white !important; border: 1px solid #555 !important; }}
        .stTabs [data-baseweb="tab-list"] {{ background: transparent; }}
        .stTabs [data-baseweb="tab"] {{ color: white; }}
    </style>
    """, unsafe_allow_html=True)

    user = st.session_state.user
    db = load_db()

    with st.sidebar:
        st.markdown(f"<h2 style='text-align:center; text-shadow: 0 0 10px #00f2ff;'>NEXUS OS</h2>", unsafe_allow_html=True)
        st.write(f"🧑‍🚀 **Phi hành gia:** {user}")
        st.markdown("---")
        menu = st.radio("ĐIỀU HƯỚNG", ["🏠 Bảng điều khiển", "🧠 NEXUS A.I", "🌐 Mạng Xã Hội", "⚙️ Cài đặt"])
        st.markdown("---")
        if st.button("🚪 Thoát Hệ Thống", use_container_width=True):
            st.session_state.stage = "LOGIN"
            st.rerun()

    # --- TAB 1: BẢNG ĐIỀU KHIỂN ---
    if menu == "🏠 Bảng điều khiển":
        st.title("📊 TRẠM ĐIỀU KHIỂN TRUNG TÂM")
        st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
        st.write(f"Chào mừng {user}. Hệ thống đang ở trạng thái tối ưu.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Phiên Bản", VERSION)
        c2.metric("Số lượng User", len(db["users"]))
        c3.metric("Lõi A.I", "Llama 3.3 70B", "Online")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 2: NEXUS A.I ---
    elif menu == "🧠 NEXUS A.I":
        st.title("🧠 TRÍ TUỆ NHÂN TẠO NEXUS")
        if "ai_msgs" not in st.session_state:
            st.session_state.ai_msgs = [{"role": "assistant", "content": "Hệ thống A.I đã sẵn sàng. Bạn cần phân tích dữ liệu gì?"}]

        for msg in st.session_state.ai_msgs:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input("Giao tiếp với lõi A.I..."):
            st.session_state.ai_msgs.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                try:
                    client = OpenAI(api_key=GROQ_API_KEYS[0], base_url="https://api.groq.com/openai/v1")
                    sys_prompt = {"role": "system", "content": f"Bạn là NEXUS OS A.I. Cư xử thông minh, ngầu. User hiện tại: {user}."}
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[sys_prompt] + st.session_state.ai_msgs[1:])
                    reply = res.choices[0].message.content
                    st.markdown(reply)
                    st.session_state.ai_msgs.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"Lõi A.I gián đoạn: {e}")

    # --- TAB 3: MẠNG XÃ HỘI (PHÂN CHIA KỸ CÀNG) ---
    elif menu == "🌐 Mạng Xã Hội":
        st.title("🌐 KẾT NỐI KHÔNG GIAN")
        t_global, t_friends, t_p2p, t_group = st.tabs(["🌍 Kênh Thế Giới", "👥 Bạn Bè", "💬 Tin Nhắn Riêng", "🏢 Nhóm"])

        # 1. Kênh Thế Giới
        with t_global:
            st.markdown("<div class='glass-panel' style='height: 300px; overflow-y: auto;'>", unsafe_allow_html=True)
            for c in db.get("global_chat", [])[-15:]:
                st.markdown(f"**{c['user']}**: {c['msg']} *(Lúc {c['time']})*")
            st.markdown("</div>", unsafe_allow_html=True)
            with st.form("f_global", clear_on_submit=True):
                msg = st.text_input("Gửi tin nhắn toàn cầu...")
                if st.form_submit_button("Phát sóng") and msg:
                    db["global_chat"].append({"user": user, "msg": msg, "time": time.strftime("%H:%M")})
                    save_db(db); st.rerun()

        # 2. Bạn Bè
        with t_friends:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Thêm bạn bè")
                all_users = [u for u in db["users"].keys() if u != user]
                friend_target = st.selectbox("Chọn phi hành gia:", all_users)
                if st.button("Gửi lời mời"):
                    if friend_target not in db["friend_requests"]: db["friend_requests"][friend_target] = []
                    if user not in db["friend_requests"][friend_target]:
                        db["friend_requests"][friend_target].append(user)
                        save_db(db); st.success(f"Đã gửi yêu cầu đến {friend_target}!")
            with c2:
                st.subheader("Lời mời đến bạn")
                my_reqs = db.get("friend_requests", {}).get(user, [])
                if not my_reqs: st.write("Không có lời mời nào.")
                for req in my_reqs:
                    if st.button(f"Chấp nhận {req}"):
                        if user not in db["friends"]: db["friends"][user] = []
                        if req not in db["friends"]: db["friends"][req] = []
                        db["friends"][user].append(req)
                        db["friends"][req].append(user)
                        db["friend_requests"][user].remove(req)
                        save_db(db); st.rerun()

        # 3. Tin Nhắn Riêng (P2P)
        with t_p2p:
            my_friends = db.get("friends", {}).get(user, [])
            if not my_friends:
                st.warning("Bạn chưa có bạn bè nào để nhắn tin.")
            else:
                chat_target = st.selectbox("Trò chuyện với:", my_friends)
                chat_key = "_".join(sorted([user, chat_target])) # Tạo mã kênh chung giữa 2 người
                if chat_key not in db["p2p_chats"]: db["p2p_chats"][chat_key] = []
                
                st.markdown("<div class='glass-panel' style='height: 300px; overflow-y: auto;'>", unsafe_allow_html=True)
                for c in db["p2p_chats"][chat_key]:
                    st.markdown(f"**{c['sender']}**: {c['msg']}")
                st.markdown("</div>", unsafe_allow_html=True)

                with st.form("f_p2p", clear_on_submit=True):
                    msg = st.text_input(f"Nhắn cho {chat_target}...")
                    if st.form_submit_button("Gửi mã hóa") and msg:
                        db["p2p_chats"][chat_key].append({"sender": user, "msg": msg})
                        save_db(db); st.rerun()

        # 4. Nhóm
        with t_group:
            st.write("Tính năng Nhóm đang được cập nhật giao thức mã hóa đa tầng. Hãy quay lại sau!")

    # --- TAB 4: CÀI ĐẶT ---
    elif menu == "⚙️ Cài đặt":
        st.title("⚙️ TÙY CHỈNH HỆ THỐNG")
        st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
        st.subheader("Cá nhân hóa")
        if st.button("Đổi hình nền ngẫu nhiên 🎲"):
            st.session_state.bg = random.choice(WALLPAPERS)
            st.rerun()
        
        st.subheader("Quản lý tài khoản")
        st.write(f"- Tên: **{user}**")
        st.write("- Trạng thái GitHub Sync: **Hoạt động**")
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------- [6] ĐIỀU HƯỚNG --------------------
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
