# -*- coding: utf-8 -*-
import streamlit as st
import time, base64, json, requests, random, hashlib
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime, timedelta

# --- [1] CẤU HÌNH ---
if 'current_ver' not in st.session_state:
    st.session_state.current_ver = 19.0

CONFIG = {
    "NAME": "NEXUS OS GATEWAY",
    "CREATOR": "Thiên Phát",
    "FILE_DATA": "nexus_core_v24.json"
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
            now = datetime.now()
            # Dọn dẹp hội thoại tạm thời (24h)
            db["chats"] = [c for c in db.get("chats", []) if not c.get("temp", False) or (datetime.fromisoformat(c["time"]) + timedelta(hours=24) > now)]
            return db
        return {"users": {CONFIG["CREATOR"]: "nexus os gateway"}, "codes": ["PHAT2026"], "pro_users": [], "pro_devices": [], "chats": [], "update_cfg": {"latest_ver": 24.0}, "files": {}, "rem": {}}
    else:
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": "Nexus Sync", "content": content, "sha": sha})

# --- [3] GIAO DIỆN ---
st.markdown("""
<style>
.stApp { background-image: url('https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=1920&q=80'); background-size: cover; background-attachment: fixed; }
.ai-banner { background-color: #0047AB; color: white !important; padding: 15px; border-radius: 8px; font-size: 16px; font-weight: 600 !important; margin: 10px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.2); line-height: 1.5; }
h1, h2, h3, p, span, label { color: #111 !important; font-weight: 800 !important; text-shadow: 1px 1px 2px #22d3ee; }
.back-btn { margin-bottom: 20px; }
[data-testid="stHeader"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- [4] KHỞI CHẠY ---
if 'boot' not in st.session_state:
    st.session_state.db = sync_io()
    st.session_state.page = "BOT_CHECK"; st.session_state.user = None
    st.session_state.current_chat_id = None; st.session_state.boot = True

fp = get_device_fp()
is_pro = (st.session_state.user in st.session_state.db.get("pro_users", []) or fp in st.session_state.db.get("pro_devices", []))

# --- [5] NÚT QUAY LẠI DÙNG CHUNG ---
def back_button():
    if st.button("🔙 QUAY LẠI DASHBOARD", key=f"back_{st.session_state.page}"):
        st.session_state.page = "DASHBOARD"
        st.session_state.current_chat_id = None
        st.rerun()

# --- [6] SIDEBAR & CẬP NHẬT ---
if st.session_state.page not in ["BOT_CHECK", "AUTH"]:
    with st.sidebar:
        st.markdown(f"### 🛡️ {CONFIG['NAME']}")
        st.caption(f"v{st.session_state.current_ver} | {'💎 PRO' if is_pro else '🆓 GUEST'}")
        
        latest = st.session_state.db["update_cfg"]["latest_ver"]
        if st.button("🔄 Kiểm tra cập nhật", use_container_width=True):
            if st.session_state.current_ver < latest:
                if is_pro: st.session_state.upgrade_ready = True
                else: st.warning("⚠️ Bản cập nhật cho Free chưa khả dụng.")
            else: st.success("✅ Đã ở bản mới nhất.")

        if st.session_state.get('upgrade_ready'):
            if st.button("🚀 ÁP DỤNG NGAY (30S)", use_container_width=True):
                with st.status("Đang cài đặt hệ thống..."):
                    st.write("Đang tải dữ liệu..."); time.sleep(10)
                    st.write("Đang ghi đè Kernel..."); time.sleep(10)
                    st.write("Hoàn tất!"); time.sleep(10)
                st.session_state.current_ver = latest
                st.session_state.upgrade_ready = False
                st.write("Đang khởi động lại...")
                time.sleep(1)
                streamlit_js_eval(js_expressions="parent.window.location.reload()")
                st.stop()

        st.divider()
        if st.button("➕ Hội thoại mới", use_container_width=True):
            st.session_state.current_chat_id = None; st.session_state.page = "AI"; st.rerun()
            
        st.markdown("📂 **Lịch sử Chat**")
        for idx, c in enumerate(st.session_state.db["chats"]):
            if c.get("owner") == st.session_state.user:
                col_c, col_d = st.columns([4, 1])
                chat_label = f"💬 {c['name']} {'(Tạm)' if c.get('temp') else ''}"
                if col_c.button(chat_label, key=f"chat_{idx}", use_container_width=True):
                    st.session_state.current_chat_id = idx; st.session_state.page = "AI"; st.rerun()
                if col_d.button("🗑️", key=f"del_{idx}"):
                    st.session_state.db["chats"].pop(idx)
                    # Sửa lỗi IndexError: Nếu chat đang mở bị xóa, reset ID
                    if st.session_state.current_chat_id == idx:
                        st.session_state.current_chat_id = None
                    sync_io(st.session_state.db); st.rerun()

# --- [7] CÁC PHÂN HỆ MÀN HÌNH ---

if st.session_state.page == "AI":
    back_button() # Nút quay lại
    st.header("🧠 AI NEXUS CORE")
    
    chat_id = st.session_state.current_chat_id
    
    # BẢO VỆ KÉP CHỐNG LỖI INDEX: Rà soát xem chat_id có hợp lệ không
    if chat_id is not None and (chat_id < 0 or chat_id >= len(st.session_state.db["chats"])):
        chat_id = None
        st.session_state.current_chat_id = None

    # Khởi tạo hội thoại mới nếu chưa có
    if chat_id is None:
        new_chat = {"name": "Hội thoại mới", "msgs": [], "owner": st.session_state.user, "temp": False, "time": str(datetime.now().isoformat())}
        st.session_state.db["chats"].append(new_chat)
        st.session_state.current_chat_id = len(st.session_state.db["chats"]) - 1
        chat_id = st.session_state.current_chat_id

    curr_chat = st.session_state.db["chats"][chat_id]
    
    is_temp = st.toggle("Chế độ trò chuyện tạm thời (Tự xóa sau 24h)", value=curr_chat.get("temp", False))
    if is_temp != curr_chat.get("temp"):
        curr_chat["temp"] = is_temp; sync_io(st.session_state.db)

    for m in curr_chat["msgs"]:
        if m["role"] == "user":
            with st.chat_message("user"): st.write(m["content"])
        else:
            st.markdown(f'<div class="ai-banner">{m["content"]}</div>', unsafe_allow_html=True)

    if p := st.chat_input("Gửi tin nhắn..."):
        curr_chat["msgs"].append({"role": "user", "content": p})
        with st.chat_message("user"): st.write(p)
        
        try:
            client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":"Bạn là AI của Nexus."}] + curr_chat["msgs"][-5:])
            ans = res.choices[0].message.content
            curr_chat["msgs"].append({"role": "assistant", "content": ans})
            st.markdown(f'<div class="ai-banner">{ans}</div>', unsafe_allow_html=True)
            
            # Đặt tên tự động (Có try-except để không sập nếu mạng chậm)
            limit = 5 if is_pro else 2
            if len(curr_chat["msgs"]) == limit * 2:
                try:
                    n_res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": f"Tóm tắt 3 từ: {p}"}])
                    curr_chat["name"] = n_res.choices[0].message.content.strip('".')
                except: pass
        except Exception as e:
            st.error("Lỗi kết nối AI. Vui lòng thử lại sau.")
            curr_chat["msgs"].pop() # Xóa tin nhắn vừa gửi nếu lỗi

        sync_io(st.session_state.db); st.rerun()

elif st.session_state.page == "CLOUD":
    back_button()
    st.header("☁️ CLOUD STORAGE")
    files = {k:v for k,v in st.session_state.db["files"].items() if v.get("owner")==st.session_state.user}
    st.write(f"Sức chứa: {len(files)}/{'∞' if is_pro else 2}")
    if len(files) < (999 if is_pro else 2):
        up = st.file_uploader("Upload")
        if up and st.button("LƯU"):
            st.session_state.db["files"][up.name] = {"data": base64.b64encode(up.getvalue()).decode(), "owner": st.session_state.user}
            sync_io(st.session_state.db); st.rerun()
    for n, i in files.items():
        c1, c2 = st.columns([3, 1])
        c1.write(f"📄 {n}")
        if c2.button(f"🗑️ Xóa", key=f"del_{n}"): 
            del st.session_state.db["files"][n]; sync_io(st.session_state.db); st.rerun()

elif st.session_state.page == "SETTINGS":
    back_button()
    st.header("⚙️ SETTINGS")
    if is_pro: st.success("💎 TÀI KHOẢN PRO ĐÃ KÍCH HOẠT")
    else:
        u_code = st.text_input("Nhập mã Pro (8 ký tự)").upper()
        if st.button("NÂNG CẤP"):
            if u_code in st.session_state.db["codes"]:
                st.session_state.db["pro_users"].append(st.session_state.user)
                st.session_state.db["pro_devices"].append(fp)
                st.session_state.db["codes"].remove(u_code) # Xóa mã sau khi dùng
                sync_io(st.session_state.db); st.balloons(); st.rerun()
            else: st.error("Mã không hợp lệ hoặc đã sử dụng!")

elif st.session_state.page == "ADMIN":
    back_button()
    st.header("🛠️ ADMIN CONTROL")
    t1, t2 = st.tabs(["🔑 MÃ PRO", "💬 CHAT & LOG"])
    with t1:
        new_code = st.text_input("Mã mới (8 ký tự)").upper()
        if st.button("LƯU MÃ"):
            if len(new_code) == 8:
                st.session_state.db["codes"].append(new_code)
                sync_io(st.session_state.db); st.success("Đã thêm!"); st.rerun()
            else: st.error("Đúng 8 ký tự nhé!")
        st.write("Mã chưa dùng:", st.session_state.db["codes"])
    with t2:
        if st.button("XÓA TẤT CẢ LỊCH SỬ CHAT HỆ THỐNG"):
            st.session_state.db["chats"] = []; sync_io(st.session_state.db); st.rerun()

# --- TRANG ĐĂNG NHẬP & DASHBOARD ---
elif st.session_state.page == "BOT_CHECK":
    if st.button("XÁC NHẬN VÀO HỆ THỐNG", use_container_width=True): st.session_state.page = "AUTH"; st.rerun()

elif st.session_state.page == "AUTH":
    st.markdown("<h2 style='text-align:center;'>LOGIN GATEWAY</h2>", unsafe_allow_html=True)
    u = st.text_input("User"); p = st.text_input("Pass", type="password")
    if st.button("ĐĂNG NHẬP", use_container_width=True):
        if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
            st.session_state.user = u; st.session_state.page = "DASHBOARD"; st.rerun()
        else: st.error("Sai tài khoản hoặc mật khẩu!")

elif st.session_state.page == "DASHBOARD":
    st.title("🚀 TRUNG TÂM ĐIỀU KHIỂN")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🧠 MỞ AI NEXUS", use_container_width=True): st.session_state.page = "AI"; st.rerun()
    if c2.button("☁️ MỞ CLOUD", use_container_width=True): st.session_state.page = "CLOUD"; st.rerun()
    if c3.button("⚙️ CÀI ĐẶT", use_container_width=True): st.session_state.page = "SETTINGS"; st.rerun()
    if st.session_state.user == CONFIG["CREATOR"] and c4.button("🛠️ QUẢN TRỊ ADMIN", use_container_width=True): 
        st.session_state.page = "ADMIN"; st.rerun()
