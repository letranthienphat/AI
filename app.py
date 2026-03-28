# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH ---
CONFIG = {
    "NAME": "NEXUS OS",
    "CREATOR": "Thiên Phát",
    "FILE_DATA": "nexus_final_v26.json"
}

try:
    GH_TOKEN, GH_REPO = st.secrets["GH_TOKEN"], st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 LỖI: Thiếu Secrets!"); st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide")

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
            # Tự động dọn dẹp chat tạm (24h)
            now = datetime.now()
            db["chats"] = [c for c in db.get("chats", []) if not c.get("temp") or (datetime.fromisoformat(c["time"]) + timedelta(hours=24) > now)]
            return db
        return {"users": {CONFIG["CREATOR"]: "nexus os gateway"}, "codes": ["PHAT2026"], "pro_users": [], "chats": [], "files": {}, "rem": {}}
    else:
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Sync", "content": content, "sha": sha})

# --- [3] GIAO DIỆN ---
st.markdown("""
<style>
.stApp { background-color: #f8fafc; }
.ai-banner { 
    background-color: #0047AB; color: white !important; padding: 16px; 
    border-radius: 10px; font-weight: 600; margin: 12px 0;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); 
}
.stButton>button { width: 100%; border-radius: 8px; height: 45px; }
.download-btn {
    display: inline-block; padding: 8px 16px; background-color: #10b981;
    color: white !important; text-decoration: none; border-radius: 6px;
    font-weight: bold; text-align: center; width: 100%;
}
[data-testid="stHeader"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- [4] KHỞI TẠO HỆ THỐNG ---
if 'boot' not in st.session_state:
    st.session_state.db = sync_io()
    st.session_state.user = None
    st.session_state.page = "AUTH"
    st.session_state.chat_id = None
    st.session_state.boot = True

fp = get_device_fp()

# TỰ ĐỘNG ĐĂNG NHẬP (Ghi nhớ)
if st.session_state.user is None and fp in st.session_state.db.get("rem", {}):
    st.session_state.user = st.session_state.db["rem"][fp]
    st.session_state.page = "DASHBOARD"

is_pro = (st.session_state.user in st.session_state.db.get("pro_users", []))

# --- [5] XỬ LÝ ĐĂNG NHẬP ---
if st.session_state.page == "AUTH":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h1 style='text-align:center;'>NEXUS OS</h1>", unsafe_allow_html=True)
        u = st.text_input("Tên đăng nhập").strip()
        p = st.text_input("Mật khẩu", type="password").strip()
        rem = st.checkbox("Ghi nhớ đăng nhập trên thiết bị này")
        if st.button("🚀 TRUY CẬP"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                if rem:
                    st.session_state.db["rem"][fp] = u
                    sync_io(st.session_state.db)
                st.session_state.page = "DASHBOARD"
                st.rerun()
            else: st.error("Sai tài khoản hoặc mật khẩu!")

# --- [6] DASHBOARD ---
elif st.session_state.page == "DASHBOARD":
    st.title(f"👋 Chào Phát, Nexus OS đã sẵn sàng")
    st.write(f"Trạng thái: {'💎 PRO' if is_pro else '🆓 FREE'}")
    st.divider()
    
    c1, c2, c3 = st.columns(3)
    if c1.button("🧠 TRÒ CHUYỆN AI"): st.session_state.page = "AI"; st.rerun()
    if c2.button("☁️ KHO LƯU TRỮ"): st.session_state.page = "CLOUD"; st.rerun()
    if c3.button("⚙️ CÀI ĐẶT VIP"): st.session_state.page = "SETTINGS"; st.rerun()
    
    if st.session_state.user == CONFIG["CREATOR"]:
        if st.button("🛠️ QUẢN TRỊ HỆ THỐNG"): st.session_state.page = "ADMIN"; st.rerun()
    
    if st.button("🔌 Đăng xuất & Quên thiết bị"):
        if fp in st.session_state.db["rem"]: del st.session_state.db["rem"][fp]
        sync_io(st.session_state.db)
        st.session_state.user = None
        st.session_state.page = "AUTH"; st.rerun()

# --- [7] TRÒ CHUYỆN AI ---
elif st.session_state.page == "AI":
    if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    
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
                    st.session_state.chat_id = None; sync_io(st.session_state.db); st.rerun()

    idx = st.session_state.chat_id
    if idx is None or idx >= len(st.session_state.db["chats"]):
        new_chat = {"name": "Hội thoại mới", "msgs": [], "owner": st.session_state.user, "temp": False, "time": str(datetime.now().isoformat())}
        st.session_state.db["chats"].append(new_chat)
        st.session_state.chat_id = len(st.session_state.db["chats"]) - 1
        idx = st.session_state.chat_id

    chat = st.session_state.db["chats"][idx]
    chat["temp"] = st.toggle("Hội thoại tạm thời (Tự xóa sau 24h)", value=chat.get("temp", False))

    for m in chat["msgs"]:
        if m["role"] == "user": with st.chat_message("user"): st.write(m["content"])
        else: st.markdown(f'<div class="ai-banner">{m["content"]}</div>', unsafe_allow_html=True)

    if p := st.chat_input("Nhập câu hỏi..."):
        chat["msgs"].append({"role": "user", "content": p})
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=chat["msgs"][-5:])
        ans = res.choices[0].message.content
        chat["msgs"].append({"role": "assistant", "content": ans})
        
        # Đặt tên AI (Free: 2 tin, Pro: 5 tin)
        limit = 5 if is_pro else 2
        if len(chat["msgs"]) == limit * 2:
            n_res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Tóm tắt 3 từ cho: {p}"}])
            chat["name"] = n_res.choices[0].message.content.strip('".')
        
        sync_io(st.session_state.db); st.rerun()

# --- [8] KHO LƯU TRỮ (TẢI XUỐNG CỰC MẠNH) ---
elif st.session_state.page == "CLOUD":
    if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    st.header("☁️ CLOUD STORAGE")
    
    up = st.file_uploader("Chọn file từ máy")
    if up and st.button("📤 TẢI LÊN HỆ THỐNG"):
        f_base64 = base64.b64encode(up.getvalue()).decode()
        st.session_state.db["files"][up.name] = {"data": f_base64, "owner": st.session_state.user}
        sync_io(st.session_state.db); st.success("Đã lưu vào mây!"); st.rerun()
    
    st.divider()
    my_files = {k:v for k,v in st.session_state.db["files"].items() if v.get("owner") == st.session_state.user}
    
    for name, info in my_files.items():
        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"📄 **{name}**")
            # Nút tải xuống chuẩn HTML
            c2.markdown(f'<a href="data:application/octet-stream;base64,{info["data"]}" download="{name}" class="download-btn">📥 TẢI VỀ</a>', unsafe_allow_html=True)
            if c3.button("🗑️ XÓA", key=name):
                del st.session_state.db["files"][name]; sync_io(st.session_state.db); st.rerun()

# --- [9] CÀI ĐẶT & ADMIN ---
elif st.session_state.page == "SETTINGS":
    if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    st.header("⚙️ CÀI ĐẶT")
    if is_pro: st.success("💎 BẠN ĐANG LÀ NGƯỜI DÙNG PRO")
    else:
        code = st.text_input("Nhập mã Pro").upper()
        if st.button("KÍCH HOẠT VIP"):
            if code in st.session_state.db["codes"]:
                st.session_state.db["pro_users"].append(st.session_state.user)
                st.session_state.db["codes"].remove(code)
                sync_io(st.session_state.db); st.balloons(); st.rerun()

elif st.session_state.page == "ADMIN":
    if st.button("🔙 QUAY LẠI"): st.session_state.page = "DASHBOARD"; st.rerun()
    new_c = st.text_input("Tạo mã Pro mới").upper()
    if st.button("TẠO MÃ"):
        st.session_state.db["codes"].append(new_c); sync_io(st.session_state.db); st.success("Đã tạo!")
