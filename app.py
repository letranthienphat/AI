# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH CỐ ĐỊNH ---
CONFIG = {
    "NAME": "NEXUS OS",
    "CREATOR": "Thiên Phát",
    "FILE_DATA": "nexus_final_v25.json"
}

# Load secrets
try:
    GH_TOKEN, GH_REPO = st.secrets["GH_TOKEN"], st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 LỖI: Thiếu cấu hình Secrets trên Streamlit Cloud!"); st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide")

# --- [2] HỆ THỐNG DỮ LIỆU ---
def get_device_fp():
    ua = st.context.headers.get("User-Agent", "Unknown")
    return hashlib.sha256(ua.encode()).hexdigest()[:16]

def sync_io(data=None):
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    if data is None:
        if res.status_code == 200:
            return json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
        return {"users": {CONFIG["CREATOR"]: "nexus os gateway"}, "codes": ["PHAT2026"], "pro_users": [], "chats": [], "files": {}}
    else:
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Sync", "content": content, "sha": sha})

# --- [3] STYLE GIAO DIỆN (BANNER BLUE) ---
st.markdown("""
<style>
.stApp { background-color: #f0f2f6; }
.ai-banner { 
    background-color: #0047AB; color: white !important; padding: 15px; 
    border-radius: 8px; font-weight: 600; margin: 10px 0;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
}
.stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
[data-testid="stHeader"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- [4] KHỞI TẠO ---
if 'db' not in st.session_state:
    st.session_state.db = sync_io()
    st.session_state.page = "AUTH"
    st.session_state.user = None
    st.session_state.chat_id = None

fp = get_device_fp()
is_pro = (st.session_state.user in st.session_state.db.get("pro_users", []))

# --- [5] ĐIỀU HƯỚNG ---
def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- [6] MÀN HÌNH ĐĂNG NHẬP ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.title("🔐 NEXUS LOGIN")
        u = st.text_input("Tài khoản")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("ĐĂNG NHẬP"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                go_to("DASHBOARD")
            else: st.error("Sai thông tin!")

# --- [7] TRUNG TÂM ĐIỀU KHIỂN ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"🚀 Xin chào, {st.session_state.user}")
    st.write(f"Cấp độ: {'💎 PRO' if is_pro else '🆓 Miễn phí'}")
    st.divider()
    
    c1, c2, c3 = st.columns(3)
    if c1.button("🧠 TRÒ CHUYỆN AI"): go_to("AI")
    if c2.button("☁️ LƯU TRỮ CLOUD"): go_to("CLOUD")
    if c3.button("⚙️ CÀI ĐẶT & VIP"): go_to("SETTINGS")
    
    if st.session_state.user == CONFIG["CREATOR"]:
        if st.button("🛠️ QUẢN TRỊ VIÊN"): go_to("ADMIN")
    
    if st.button("🚪 Đăng xuất"):
        st.session_state.user = None
        go_to("AUTH")

# --- [8] TRÒ CHUYỆN AI ---
elif st.session_state.page == "AI":
    if st.button("🔙 QUAY LẠI"): go_to("DASHBOARD")
    st.header("🧠 NEXUS AI")
    
    # Quản lý danh sách chat bên sidebar
    with st.sidebar:
        if st.button("➕ Hội thoại mới"): st.session_state.chat_id = None; st.rerun()
        st.write("---")
        for i, c in enumerate(st.session_state.db["chats"]):
            if c["owner"] == st.session_state.user:
                col_t, col_d = st.columns([4, 1])
                if col_t.button(f"💬 {c['name']}", key=f"t_{i}"):
                    st.session_state.chat_id = i; st.rerun()
                if col_d.button("🗑️", key=f"d_{i}"):
                    st.session_state.db["chats"].pop(i)
                    st.session_state.chat_id = None
                    sync_io(st.session_state.db); st.rerun()

    # Xử lý nội dung chat
    idx = st.session_state.chat_id
    if idx is None or idx >= len(st.session_state.db["chats"]):
        new_chat = {"name": "Hội thoại mới", "msgs": [], "owner": st.session_state.user, "temp": False, "time": str(datetime.now())}
        st.session_state.db["chats"].append(new_chat)
        st.session_state.chat_id = len(st.session_state.db["chats"]) - 1
        idx = st.session_state.chat_id

    chat = st.session_state.db["chats"][idx]
    temp_mode = st.toggle("Chế độ tạm thời (Xóa sau 24h)", value=chat.get("temp", False))
    chat["temp"] = temp_mode

    for m in chat["msgs"]:
        if m["role"] == "user": with st.chat_message("user"): st.write(m["content"])
        else: st.markdown(f'<div class="ai-banner">{m["content"]}</div>', unsafe_allow_html=True)

    if p := st.chat_input("Nhập câu hỏi..."):
        chat["msgs"].append({"role": "user", "content": p})
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=chat["msgs"][-5:])
        ans = res.choices[0].message.content
        chat["msgs"].append({"role": "assistant", "content": ans})
        
        # Đặt tên tự động
        if len(chat["msgs"]) == (10 if is_pro else 4):
            n_res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Tóm tắt 3 từ: {p}"}])
            chat["name"] = n_res.choices[0].message.content.strip('".')
        
        sync_io(st.session_state.db); st.rerun()

# --- [9] LƯU TRỮ CLOUD (CÓ TẢI XUỐNG) ---
elif st.session_state.page == "CLOUD":
    if st.button("🔙 QUAY LẠI"): go_to("DASHBOARD")
    st.header("☁️ NEXUS CLOUD")
    
    files = {k:v for k,v in st.session_state.db["files"].items() if v.get("owner") == st.session_state.user}
    
    up = st.file_uploader("Chọn tệp")
    if up and st.button("TẢI LÊN"):
        st.session_state.db["files"][up.name] = {"data": base64.b64encode(up.getvalue()).decode(), "owner": st.session_state.user}
        sync_io(st.session_state.db); st.success("Đã tải lên!"); st.rerun()
    
    st.write("---")
    for name, info in files.items():
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(f"📄 {name}")
        # NÚT TẢI XUỐNG
        c2.markdown(f'<a href="data:application/octet-stream;base64,{info["data"]}" download="{name}" style="text-decoration:none;">📥 Tải về</a>', unsafe_allow_html=True)
        if c3.button("🗑️ Xóa", key=name):
            del st.session_state.db["files"][name]; sync_io(st.session_state.db); st.rerun()

# --- [10] CÀI ĐẶT & ADMIN ---
elif st.session_state.page == "SETTINGS":
    if st.button("🔙 QUAY LẠI"): go_to("DASHBOARD")
    st.header("⚙️ CÀI ĐẶT")
    code = st.text_input("Nhập mã kích hoạt Pro").upper()
    if st.button("KÍCH HOẠT"):
        if code in st.session_state.db["codes"]:
            st.session_state.db["pro_users"].append(st.session_state.user)
            st.session_state.db["codes"].remove(code)
            sync_io(st.session_state.db); st.balloons(); st.rerun()

elif st.session_state.page == "ADMIN":
    if st.button("🔙 QUAY LẠI"): go_to("DASHBOARD")
    st.header("🛠️ ADMIN")
    new_code = st.text_input("Tạo mã Pro mới").upper()
    if st.button("TẠO MÃ"):
        st.session_state.db["codes"].append(new_code)
        sync_io(st.session_state.db); st.success("Đã tạo!"); st.rerun()
