# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH HỆ THỐNG ---
CONFIG = {
    "NAME": "NEXUS OS GATEWAY",
    "CREATOR": "Thiên Phát",
    "MASTER_PASS": "nexus os gateway",
    "VERSION": "19.0 Supreme",
    "FILE_DATA": "nexus_supreme_core.json"
}

try:
    GH_TOKEN, GH_REPO = st.secrets["GH_TOKEN"], st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS TRÊN CLOUD!"); st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="expanded")

# --- [2] KERNEL DỮ LIỆU ---
def get_device_fp():
    ua = st.context.headers.get("User-Agent", "Unknown")
    return hashlib.sha256(ua.encode()).hexdigest()[:16]

def sync_io(data=None):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    if data is None:
        if res.status_code == 200:
            db = json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
            # Tự động dọn dẹp hội thoại tạm thời (24h)
            now = datetime.now()
            db["chats"] = [c for c in db.get("chats", []) if not c.get("temp") or (datetime.fromisoformat(c["time"]) + timedelta(hours=24) > now)]
            return db
        return {"users": {CONFIG["CREATOR"]: CONFIG["MASTER_PASS"]}, "blacklist": [], "pro_users": [], "pro_devices": [], "rem": {}, "files": {}, "codes": ["PHAT2026"], "chats": [], "update_cfg": {"latest": "20.0", "date": str(datetime.now().date())}}
    else:
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Supreme Sync", "content": content, "sha": sha})

# --- [3] GIAO DIỆN HÓA (BANNER BLUE) ---
st.markdown(f"""
<style>
.stApp {{ background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80'); background-size: cover; background-attachment: fixed; }}
h1, h2, h3, p, span, label, .stMarkdown {{ color: #111 !important; font-weight: 800 !important; text-shadow: 1px 1px 2px #22d3ee; }}
/* Style dòng chữ AI giống ảnh yêu cầu */
.ai-banner {{
    background-color: #0047AB; color: white !important; 
    padding: 15px; border-radius: 5px; font-size: 18px;
    line-height: 1.6; margin: 10px 0; font-weight: 700 !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-shadow: none !important;
}}
[data-testid="stHeader"] {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)

# --- [4] KHỞI CHẠY ---
if 'boot' not in st.session_state:
    st.session_state.db = sync_io()
    st.session_state.page = "BOT_CHECK"
    st.session_state.user = None
    st.session_state.current_chat_id = None
    st.session_state.boot = True

fp = get_device_fp()
if fp in st.session_state.db.get("blacklist", []): st.error("🛑 BỊ KHÓA."); st.stop()

# AUTO LOGIN & PRO CHECK
if st.session_state.user is None and fp in st.session_state.db.get("rem", {}):
    st.session_state.user = st.session_state.db["rem"][fp]
    st.session_state.page = "DASHBOARD"

is_pro = False
if st.session_state.user:
    if (st.session_state.user in st.session_state.db.get("pro_users", []) or fp in st.session_state.db.get("pro_devices", [])):
        is_pro = True

# --- [5] SIDEBAR SUPREME ---
if st.session_state.page not in ["BOT_CHECK", "AUTH"]:
    with st.sidebar:
        st.markdown(f"### 🛡️ {CONFIG['NAME']}")
        st.caption(f"Phiên bản: {CONFIG['VERSION']}")
        if st.button("🔄 Kiểm tra cập nhật", use_container_width=True):
            st.toast(f"Đang kiểm tra... Bản {st.session_state.db['update_cfg']['latest']} khả dụng cho PRO.")
        
        st.divider()
        if st.button("➕ Hội thoại mới", use_container_width=True):
            st.session_state.current_chat_id = None; st.session_state.page = "AI"; st.rerun()
            
        st.markdown("📂 **Lịch sử Chat**")
        for idx, c in enumerate(st.session_state.db["chats"]):
            if c["owner"] == st.session_state.user:
                col_c, col_d = st.columns([4, 1])
                if col_c.button(f"💬 {c['name']}", key=f"chat_{idx}", use_container_width=True):
                    st.session_state.current_chat_id = idx; st.session_state.page = "AI"; st.rerun()
                if col_d.button("🗑️", key=f"del_{idx}"):
                    st.session_state.db["chats"].pop(idx); sync_io(st.session_state.db); st.rerun()
        
        st.divider()
        if st.button("🏠 DASHBOARD", use_container_width=True): st.session_state.page = "DASHBOARD"; st.rerun()
        if st.button("🔌 ĐĂNG XUẤT", use_container_width=True):
            if fp in st.session_state.db["rem"]: del st.session_state.db["rem"][fp]
            sync_io(st.session_state.db); st.session_state.user = None; st.session_state.page = "AUTH"; st.rerun()

# --- [6] PHÂN HỆ AI (HÀNH CHÍNH & XỬ LÝ) ---
if st.session_state.page == "AI":
    st.header("🧠 AI NEXUS CORE")
    
    # Lấy hoặc tạo hội thoại
    chat_id = st.session_state.current_chat_id
    if chat_id is None:
        new_chat = {"name": "Hội thoại mới", "msgs": [], "owner": st.session_state.user, "temp": False, "time": str(datetime.now().isoformat())}
        st.session_state.db["chats"].append(new_chat)
        st.session_state.current_chat_id = len(st.session_state.db["chats"]) - 1
        chat_id = st.session_state.current_chat_id

    curr_chat = st.session_state.db["chats"][chat_id]
    temp_mode = st.toggle("Chế độ hội thoại tạm thời (Tự xóa sau 24h)", value=curr_chat.get("temp", False))
    curr_chat["temp"] = temp_mode

    # Hiển thị hội thoại
    for m in curr_chat["msgs"]:
        if m["role"] == "user":
            with st.chat_message("user"): st.write(m["content"])
        else:
            st.markdown(f'<div class="ai-banner">{m["content"]}</div>', unsafe_allow_html=True)

    if p := st.chat_input("Gửi lệnh cho AI..."):
        curr_chat["msgs"].append({"role": "user", "content": p})
        with st.chat_message("user"): st.write(p)
        
        # Gọi AI
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": "Bạn là AI của NEXUS OS."}] + curr_chat["msgs"][-5:])
        ans = res.choices[0].message.content
        
        curr_chat["msgs"].append({"role": "assistant", "content": ans})
        
        # Logic đặt tên AI (Free: 2 lần, Pro: 5 lần)
        trigger = 5 if is_pro else 2
        if len(curr_chat["msgs"]) == trigger * 2:
            name_res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Đặt 1 tiêu đề ngắn 3-5 từ cho nội dung này: {p}"}])
            curr_chat["name"] = name_res.choices[0].message.content.strip('"')
        
        sync_io(st.session_state.db); st.rerun()

# --- [7] CÁC TRANG KHÁC (GIỮ NGUYÊN TÍNH NĂNG) ---
elif st.session_state.page == "BOT_CHECK":
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<h2 style='text-align:center;'>SECURITY GATEWAY</h2>", unsafe_allow_html=True)
        scr_w = streamlit_js_eval(js_expressions="window.innerWidth", key="bot_monitor")
        chk = st.checkbox("Xác thực con người")
        if st.button("VÀO HỆ THỐNG", use_container_width=True):
            if chk and scr_w: st.session_state.page = "AUTH"; st.rerun()
            else:
                st.session_state.strikes = st.session_state.get('strikes', 0) + 1
                if st.session_state.strikes >= 3:
                    st.session_state.db["blacklist"].append(fp); sync_io(st.session_state.db); st.stop()
                st.error(f"Sai {st.session_state.strikes}/3")
    st.stop()

elif st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("<h1 style='text-align:center;'>LOGIN</h1>", unsafe_allow_html=True)
        u = st.text_input("Username").strip()
        p = st.text_input("Password", type="password").strip()
        if st.button("XÁC THỰC", use_container_width=True):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u; st.session_state.page = "DASHBOARD"; st.rerun()
            else: st.error("Sai thông tin!")

elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 DASHBOARD")
    c = st.columns(4)
    if c[0].button("🧠 AI"): st.session_state.page = "AI"; st.rerun()
    if c[1].button("☁️ CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
    if c[2].button("⚙️ SETTINGS"): st.session_state.page = "SETTINGS"; st.rerun()
    if c[3].button("🛠️ ADMIN") and st.session_state.user == CONFIG["CREATOR"]: st.session_state.page = "ADMIN"; st.rerun()

elif st.session_state.page == "CLOUD":
    st.header("☁️ CLOUD STORAGE")
    user_files = {k: v for k, v in st.session_state.db["files"].items() if v.get("owner") == st.session_state.user}
    limit = 999 if is_pro else 2
    st.write(f"Sức chứa: {len(user_files)}/{'∞' if is_pro else 2}")
    up = st.file_uploader("Upload (<1MB)")
    if up and len(user_files) < limit and st.button("SAVE"):
        f_64 = base64.b64encode(up.getvalue()).decode()
        st.session_state.db["files"][up.name] = {"data": f_64, "owner": st.session_state.user}
        sync_io(st.session_state.db); st.rerun()

elif st.session_state.page == "SETTINGS":
    st.header("⚙️ SETTINGS")
    code = st.text_input("Mã Pro (8 ký tự)").upper()
    if st.button("KÍCH HOẠT"):
        if code in st.session_state.db["codes"]:
            st.session_state.db["pro_users"].append(st.session_state.user)
            st.session_state.db["pro_devices"].append(fp)
            sync_io(st.session_state.db); st.balloons(); st.rerun()

elif st.session_state.page == "ADMIN":
    st.header("🛠️ ADMIN")
    if st.button("XÓA TẤT CẢ CHAT HỆ THỐNG"):
        st.session_state.db["chats"] = []; sync_io(st.session_state.db); st.rerun()
    new_c = st.text_input("Tạo mã Pro mới").upper()
    if st.button("THÊM MÃ"):
        if len(new_c) == 8: st.session_state.db["codes"].append(new_c); sync_io(st.session_state.db)
