# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH ---
CONFIG = {
    "NAME": "NEXUS OS GATEWAY",
    "CREATOR": "Thiên Phát",
    "VERSION": 19.0, 
    "FILE_DATA": "nexus_core_v21.json"
}

try:
    GH_TOKEN, GH_REPO = st.secrets["GH_TOKEN"], st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except:
    st.error("🛑 THIẾU SECRETS!"); st.stop()

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
            now = datetime.now()
            db["chats"] = [c for c in db.get("chats", []) if not c.get("temp") or (datetime.fromisoformat(c["time"]) + timedelta(hours=24) > now)]
            return db
        return {"users": {CONFIG["CREATOR"]: "nexus os gateway"}, "blacklist": [], "pro_users": [], "pro_devices": [], "rem": {}, "files": {}, "codes": ["PHAT2026"], "chats": [], "update_cfg": {"latest_ver": 21.0}}
    else:
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Sync", "content": content, "sha": sha})

# --- [3] GIAO DIỆN ---
st.markdown("""
<style>
.stApp { background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80'); background-size: cover; background-attachment: fixed; }
.ai-banner { background-color: #0047AB; color: white !important; padding: 15px; border-radius: 5px; font-size: 17px; font-weight: 700 !important; margin: 10px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
h1, h2, h3, p, span, label { color: #111 !important; font-weight: 800 !important; text-shadow: 1px 1px 2px #22d3ee; }
[data-testid="stHeader"] { visibility: hidden; }
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

# AUTO LOGIN
if st.session_state.user is None and fp in st.session_state.db.get("rem", {}):
    st.session_state.user = st.session_state.db["rem"][fp]
    st.session_state.page = "DASHBOARD"

# KIỂM TRA PRO (Lấy từ DB Cloud để không bị mất khi update)
is_pro = False
if st.session_state.user:
    if (st.session_state.user in st.session_state.db.get("pro_users", []) or 
        fp in st.session_state.db.get("pro_devices", [])):
        is_pro = True

# --- [5] SIDEBAR & UPDATE LOGIC ---
if st.session_state.page not in ["BOT_CHECK", "AUTH"]:
    with st.sidebar:
        st.markdown(f"### 🛡️ {CONFIG['NAME']}")
        st.caption(f"v{CONFIG['VERSION']} | {'💎 PRO' if is_pro else '🆓 GUEST'}")
        
        # FIX CẬP NHẬT: Tách riêng logic hiển thị và thực thi
        latest = st.session_state.db["update_cfg"]["latest_ver"]
        if st.button("🔄 Kiểm tra cập nhật", use_container_width=True):
            if CONFIG["VERSION"] < latest:
                if is_pro: st.session_state.show_apply = True
                else: st.warning("⚠️ Bản cập nhật cho chế độ Free chưa khả dụng.")
            else: st.success("✅ Bạn đang ở bản mới nhất.")
        
        if st.session_state.get('show_apply'):
            st.info(f"Đã có bản v{latest}!")
            if st.button("🚀 ÁP DỤNG (30S)", use_container_width=True):
                progress = st.progress(0)
                for i in range(100):
                    time.sleep(0.3) # Giả lập 30 giây
                    progress.progress(i + 1)
                st.session_state.show_apply = False
                st.success("Hệ thống đã cập nhật!")
                st.rerun()

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

# --- [6] AI (BANNER BLUE + AUTO NAME) ---
if st.session_state.page == "AI":
    st.header("🧠 AI NEXUS CORE")
    chat_id = st.session_state.current_chat_id
    if chat_id is None:
        new_chat = {"name": "Hội thoại mới", "msgs": [], "owner": st.session_state.user, "temp": False, "time": str(datetime.now().isoformat())}
        st.session_state.db["chats"].append(new_chat)
        st.session_state.current_chat_id = len(st.session_state.db["chats"]) - 1
        chat_id = st.session_state.current_chat_id

    curr_chat = st.session_state.db["chats"][chat_id]
    curr_chat["temp"] = st.toggle("Hội thoại tạm thời (24h)", value=curr_chat.get("temp", False))

    for m in curr_chat["msgs"]:
        if m["role"] == "user":
            with st.chat_message("user"): st.write(m["content"])
        else:
            st.markdown(f'<div class="ai-banner">{m["content"]}</div>', unsafe_allow_html=True)

    if p := st.chat_input("Nhập lệnh..."):
        curr_chat["msgs"].append({"role": "user", "content": p})
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": "AI NEXUS."}] + curr_chat["msgs"][-5:])
        ans = res.choices[0].message.content
        curr_chat["msgs"].append({"role": "assistant", "content": ans})
        
        limit = 5 if is_pro else 2
        if len(curr_chat["msgs"]) == limit * 2:
            n_res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Đặt tiêu đề 3 từ cho: {p}"}])
            curr_chat["name"] = n_res.choices[0].message.content.strip('"')
        sync_io(st.session_state.db); st.rerun()

# --- [7] ADMIN (FIX NÚT NHẬP MÃ) ---
elif st.session_state.page == "ADMIN":
    st.header("🛠️ ADMIN CONTROL")
    t1, t2 = st.tabs(["🔑 MÃ PRO", "💬 CHAT"])
    with t1:
        new_c = st.text_input("Gõ mã Pro muốn tạo (8 ký tự)").upper()
        if st.button("XÁC NHẬN THÊM MÃ"):
            if len(new_c) == 8:
                st.session_state.db["codes"].append(new_c)
                sync_io(st.session_state.db)
                st.success(f"Đã lưu mã {new_c} vào hệ thống Cloud!")
            else: st.error("Mã phải đủ 8 ký tự!")
        st.write("Mã hiện có:", st.session_state.db["codes"])
    with t2:
        if st.button("XÓA TOÀN BỘ CHAT"):
            st.session_state.db["chats"] = []; sync_io(st.session_state.db); st.rerun()

# --- [8] SETTINGS (FIX NHẬP MÃ NGƯỜI DÙNG) ---
elif st.session_state.page == "SETTINGS":
    st.header("⚙️ SETTINGS")
    if is_pro: st.success("💎 TÀI KHOẢN PRO ĐÃ ĐƯỢC KÍCH HOẠT")
    else:
        u_code = st.text_input("Nhập mã 8 ký tự để nâng cấp").upper()
        if st.button("NÂNG CẤP NGAY"):
            if u_code in st.session_state.db["codes"]:
                st.session_state.db["pro_users"].append(st.session_state.user)
                st.session_state.db["pro_devices"].append(fp)
                # Xóa mã đã dùng để bảo mật (tùy chọn)
                st.session_state.db["codes"].remove(u_code)
                sync_io(st.session_state.db)
                st.balloons()
                st.success("💎 CHÚC MỪNG! BẠN ĐÃ LÀ NGƯỜI DÙNG PRO.")
                time.sleep(2); st.rerun()
            else: st.error("Mã không chính xác hoặc đã được sử dụng!")

# BOT CHECK & AUTH (GIỮ NGUYÊN)
elif st.session_state.page == "BOT_CHECK":
    if st.button("XÁC NHẬN CON NGƯỜI"): st.session_state.page = "AUTH"; st.rerun()
elif st.session_state.page == "AUTH":
    u = st.text_input("User"); p = st.text_input("Pass", type="password")
    if st.button("VÀO"):
        if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
            st.session_state.user = u; st.session_state.page = "DASHBOARD"; st.rerun()
elif st.session_state.page == "DASHBOARD":
    st.title("🚀 DASHBOARD")
    c = st.columns(4)
    if c[0].button("🧠 AI"): st.session_state.page = "AI"; st.rerun()
    if c[1].button("☁️ CLOUD"): st.session_state.page = "CLOUD"; st.rerun()
    if c[2].button("⚙️ SETTINGS"): st.session_state.page = "SETTINGS"; st.rerun()
    if c[3].button("🛠️ ADMIN"): st.session_state.page = "ADMIN"; st.rerun()
