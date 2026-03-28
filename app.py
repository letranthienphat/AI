# -*- coding: utf-8 -*-
import streamlit as st
import time
import base64
import json
import requests
import random
import hashlib
import re
from openai import OpenAI
from datetime import datetime
from typing import Dict, Optional, List
import mimetypes

# ================== CẤU HÌNH ==================
CONFIG = {
    "NAME": "NEXUS OS GATEWAY",
    "CREATOR": "Lê Trần Thiên Phát",
    "FILE_DATA": "nexus_gateway_v80.json",
    "GUEST_ENABLED": True,
    "MAX_RETRIES": 3,
    "RETRY_DELAY": 1,
    "FREE_STORAGE_LIMIT": 30 * 1024 * 1024 * 1024  # 30 GB
}

# Load secrets
try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str):
        GROQ_KEYS = [GROQ_KEYS]
except Exception as e:
    st.error(f"🛑 LỖI: Thiếu cấu hình Secrets trên Streamlit Cloud!")
    st.stop()

st.set_page_config(page_title=CONFIG["NAME"], layout="wide", initial_sidebar_state="expanded")

# ================== CSS ==================
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e9edf2 100%); }
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(0,0,0,0.05);
}
.custom-card {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transition: transform 0.2s;
    margin-bottom: 20px;
}
.custom-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
.ai-banner {
    background: linear-gradient(135deg, #0047AB, #0066CC);
    color: white !important;
    padding: 16px 20px;
    border-radius: 20px;
    margin: 12px 0;
    border-left: 4px solid #FFD966;
}
.stButton>button {
    border-radius: 40px;
    font-weight: 600;
    transition: all 0.2s;
    background: #0047AB;
    color: white;
    border: none;
}
.stButton>button:hover { background: #003399; transform: scale(1.02); }
.guest-badge {
    background: #FFD966;
    color: #1f2937;
    padding: 4px 12px;
    border-radius: 40px;
    font-size: 0.8rem;
    font-weight: bold;
    display: inline-block;
}
.pro-badge { background: linear-gradient(135deg, #FFD700, #FFB347); }
.stTextInput input, .stTextArea textarea {
    border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important;
}
.footer {
    text-align: center;
    padding: 20px;
    font-size: 0.8rem;
    color: #6b7280;
    border-top: 1px solid #e5e7eb;
    margin-top: 40px;
}
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { border-radius: 40px; padding: 8px 20px; }
.success-message {
    background: #d4edda;
    color: #155724;
    padding: 12px;
    border-radius: 8px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ================== HÀM TIỆN ÍCH ==================
def get_device_fp() -> str:
    ua = st.context.headers.get("User-Agent", "Unknown")
    return hashlib.sha256(ua.encode()).hexdigest()[:16]

def safe_load_json(content: str) -> Dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "users": {CONFIG["CREATOR"]: "nexusosgateway"},
            "codes": ["PHAT2026", "VIP2024", "PRO2025"],
            "pro_users": [],
            "chats": [],
            "files": {},
            "emails": {}
        }

def sync_io(data: Optional[Dict] = None, retries: int = CONFIG["MAX_RETRIES"]) -> Optional[Dict]:
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['FILE_DATA']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    for attempt in range(retries):
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if data is None:
                if res.status_code == 200:
                    content = base64.b64decode(res.json()['content']).decode('utf-8')
                    return safe_load_json(content)
                elif res.status_code == 404:
                    default_data = safe_load_json("")
                    sync_io(default_data, retries=1)
                    return default_data
                else:
                    st.error(f"Lỗi đọc GitHub: {res.status_code}")
                    return None
            else:
                if res.status_code in (200, 404):
                    sha = res.json().get("sha") if res.status_code == 200 else None
                    content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode('utf-8')
                    put_res = requests.put(url, headers=headers,
                                           json={"message": "Nexus Sync", "content": content, "sha": sha},
                                           timeout=10)
                    if put_res.status_code in (200, 201):
                        return data
                    elif put_res.status_code == 409 and attempt < retries - 1:
                        time.sleep(CONFIG["RETRY_DELAY"])
                        continue
                    else:
                        st.error(f"Lỗi ghi GitHub: {put_res.status_code}")
                        return None
                else:
                    return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(CONFIG["RETRY_DELAY"])
            else:
                st.error(f"Lỗi kết nối: {str(e)}")
                return None
    return None

@st.cache_data(ttl=60)
def load_db():
    return sync_io()

def init_session():
    if 'db' not in st.session_state:
        st.session_state.db = load_db()
    if 'page' not in st.session_state:
        st.session_state.page = "AUTH"
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'chat_id' not in st.session_state:
        st.session_state.chat_id = None
    if 'guest_mode' not in st.session_state:
        st.session_state.guest_mode = False
    if 'temp_chat' not in st.session_state:
        st.session_state.temp_chat = {"msgs": []}
    if 'current_dir' not in st.session_state:
        st.session_state.current_dir = ""
    if 'preview_file' not in st.session_state:
        st.session_state.preview_file = None
    if 'register_success' not in st.session_state:
        st.session_state.register_success = False

init_session()
fp = get_device_fp()
is_pro = (st.session_state.user in st.session_state.db.get("pro_users", [])) if st.session_state.user else False

def go_to(page):
    st.session_state.page = page
    st.rerun()

def get_used_storage(user: str) -> int:
    total = 0
    for path, info in st.session_state.db.get("files", {}).items():
        if info.get("owner") == user:
            total += info.get("size", 0)
    return total

def list_dir(path: str) -> Dict[str, List]:
    folders = set()
    files = []
    prefix = path + "/" if path else ""
    for full_path, info in st.session_state.db.get("files", {}).items():
        if info.get("owner") != st.session_state.user:
            continue
        if full_path.startswith(prefix):
            rest = full_path[len(prefix):]
            if "/" in rest:
                folder_name = rest.split("/")[0]
                folders.add(folder_name)
            else:
                files.append({"name": rest, "info": info})
    return {"folders": sorted(folders), "files": sorted(files, key=lambda x: x["name"])}

def create_folder(path: str):
    if path and not path.endswith("/"):
        path += "/"
    marker = path + ".folder"
    if marker not in st.session_state.db["files"]:
        st.session_state.db["files"][marker] = {
            "owner": st.session_state.user,
            "data": "",
            "size": 0,
            "type": "inode/directory",
            "upload_time": str(datetime.now())
        }
        sync_io(st.session_state.db)
        return True
    return False

def delete_path(path: str):
    to_delete = []
    for full_path in list(st.session_state.db["files"].keys()):
        if full_path == path or full_path.startswith(path + "/"):
            to_delete.append(full_path)
    for p in to_delete:
        del st.session_state.db["files"][p]
    sync_io(st.session_state.db)

def validate_username(username: str) -> tuple:
    if not username:
        return False, "Tên đăng nhập không được để trống"
    if len(username) < 3:
        return False, "Tên đăng nhập phải có ít nhất 3 ký tự"
    if len(username) > 20:
        return False, "Tên đăng nhập không được quá 20 ký tự"
    if not re.match(r'^[a-zA-Z0-9_\u00C0-\u1EF9]+$', username):
        return False, "Tên đăng nhập chỉ được chứa chữ cái, số và dấu gạch dưới"
    if username in st.session_state.db["users"]:
        return False, "Tên đăng nhập đã tồn tại"
    return True, "OK"

def validate_password(password: str) -> tuple:
    if not password:
        return False, "Mật khẩu không được để trống"
    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"
    return True, "OK"

def validate_email(email: str) -> tuple:
    if not email:
        return True, "OK"
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, email):
        return True, "OK"
    return False, "Email không hợp lệ"

def register_user(username: str, password: str, email: str = "") -> tuple:
    valid, msg = validate_username(username)
    if not valid:
        return False, msg
    valid, msg = validate_password(password)
    if not valid:
        return False, msg
    valid, msg = validate_email(email)
    if not valid:
        return False, msg
    st.session_state.db["users"][username] = password
    if email:
        st.session_state.db["emails"][username] = email
    sync_io(st.session_state.db)
    return True, "Đăng ký thành công! Vui lòng đăng nhập."

# ================== SIDEBAR ==================
with st.sidebar:
    st.markdown(f"### {CONFIG['NAME']}")
    if st.session_state.user:
        st.markdown(f"👤 **{st.session_state.user}**")
        if st.session_state.guest_mode:
            st.markdown('<span class="guest-badge">🔓 CHẾ ĐỘ KHÁCH</span>', unsafe_allow_html=True)
        else:
            badge = "💎 PRO" if is_pro else "🆓 FREE"
            st.markdown(f'<span class="guest-badge pro-badge">{badge}</span>', unsafe_allow_html=True)
    st.divider()

    if st.session_state.page not in ["AUTH", "DASHBOARD"]:
        if st.button("🔙 QUAY LẠI", use_container_width=True, key="back_btn"):
            go_to("DASHBOARD")

    if st.session_state.user:
        st.markdown("---")
        st.caption("🚀 Tiện ích nhanh")
        if st.button("🧠 Chat AI", use_container_width=True, key="quick_chat"):
            go_to("AI")
        if st.button("☁️ Lưu trữ", use_container_width=True, key="quick_cloud"):
            go_to("CLOUD")
        if st.button("⚙️ Cài đặt", use_container_width=True, key="quick_settings"):
            go_to("SETTINGS")
        if st.session_state.user == CONFIG["CREATOR"]:
            if st.button("🛠️ Admin", use_container_width=True, key="quick_admin"):
                go_to("ADMIN")
        if st.button("🚪 Đăng xuất", use_container_width=True, key="logout"):
            st.session_state.user = None
            st.session_state.guest_mode = False
            st.session_state.temp_chat = {"msgs": []}
            st.session_state.current_dir = ""
            go_to("AUTH")

    st.divider()
    st.caption(f"© 2025 {CONFIG['CREATOR']}")
    st.caption("NEXUS OS GATEWAY v8.0")

# ================== TRANG ĐĂNG NHẬP ==================
if st.session_state.page == "AUTH":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 ĐĂNG NHẬP", "📝 ĐĂNG KÝ"])
        
        with tab1:
            st.subheader("Đăng nhập")
            login_username = st.text_input("Tài khoản", key="login_username")
            login_password = st.text_input("Mật khẩu", type="password", key="login_password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("ĐĂNG NHẬP", use_container_width=True, key="login_btn"):
                    if login_username and login_password:
                        username_clean = login_username.strip()
                        if username_clean in st.session_state.db["users"]:
                            if st.session_state.db["users"][username_clean] == login_password:
                                st.session_state.user = username_clean
                                st.session_state.guest_mode = False
                                st.toast(f"✅ Đăng nhập thành công!", icon="🎉")
                                go_to("DASHBOARD")
                            else:
                                st.error("❌ Sai mật khẩu!")
                        else:
                            st.error("❌ Tài khoản không tồn tại!")
                    else:
                        st.warning("Vui lòng nhập đầy đủ thông tin!")
            
            if CONFIG["GUEST_ENABLED"]:
                with col_btn2:
                    if st.button("👤 DÙNG THỬ", use_container_width=True, key="guest_btn"):
                        st.session_state.user = "guest"
                        st.session_state.guest_mode = True
                        st.toast("🔓 Chế độ khách: dữ liệu không được lưu", icon="👋")
                        go_to("DASHBOARD")
        
        with tab2:
            st.subheader("Đăng ký tài khoản mới")
            
            if st.session_state.register_success:
                st.markdown('<div class="success-message">✅ Đăng ký thành công! Vui lòng đăng nhập.</div>', unsafe_allow_html=True)
                st.session_state.register_success = False
            
            reg_username = st.text_input("Tên đăng nhập *", placeholder="3-20 ký tự", key="reg_username")
            reg_password = st.text_input("Mật khẩu *", type="password", placeholder="Ít nhất 6 ký tự", key="reg_password")
            reg_confirm = st.text_input("Xác nhận mật khẩu *", type="password", key="reg_confirm")
            reg_email = st.text_input("Email (tùy chọn)", placeholder="example@email.com", key="reg_email")
            
            st.caption("* Bắt buộc")
            
            if st.button("ĐĂNG KÝ", use_container_width=True, key="register_btn"):
                if not reg_username or not reg_password:
                    st.error("Vui lòng nhập đầy đủ thông tin bắt buộc!")
                elif reg_password != reg_confirm:
                    st.error("Mật khẩu xác nhận không khớp!")
                else:
                    success, message = register_user(reg_username.strip(), reg_password, reg_email.strip())
                    if success:
                        st.session_state.register_success = True
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ================== DASHBOARD ==================
elif st.session_state.page == "DASHBOARD":
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.title(f"🚀 Chào mừng, {st.session_state.user}!")
    if st.session_state.guest_mode:
        st.markdown('<span class="guest-badge">👤 CHẾ ĐỘ KHÁCH</span>', unsafe_allow_html=True)
    else:
        st.write(f"Cấp độ: {'💎 PRO' if is_pro else '🆓 Miễn phí'}")
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🧠 TRÒ CHUYỆN AI", use_container_width=True):
            go_to("AI")
    with col2:
        if st.button("☁️ LƯU TRỮ CLOUD", use_container_width=True):
            go_to("CLOUD")
    with col3:
        if st.button("⚙️ CÀI ĐẶT & VIP", use_container_width=True):
            go_to("SETTINGS")

    if st.session_state.user == CONFIG["CREATOR"]:
        if st.button("🛠️ QUẢN TRỊ VIÊN", use_container_width=True):
            go_to("ADMIN")

# ================== AI CHAT ==================
elif st.session_state.page == "AI":
    st.header("🧠 NEXUS AI")

    if not st.session_state.guest_mode:
        with st.sidebar:
            st.markdown("### 📝 Lịch sử chat")
            if st.button("➕ Hội thoại mới", use_container_width=True):
                st.session_state.chat_id = None
                st.rerun()
            
            chats_to_show = [(i, c) for i, c in enumerate(st.session_state.db["chats"]) if c["owner"] == st.session_state.user]
            if chats_to_show:
                for i, c in chats_to_show:
                    col_t, col_d = st.columns([4, 1])
                    with col_t:
                        if st.button(f"💬 {c['name']}", key=f"chat_{i}", use_container_width=True):
                            st.session_state.chat_id = i
                            st.rerun()
                    with col_d:
                        if st.button("🗑️", key=f"del_{i}"):
                            if st.session_state.get(f"confirm_del_{i}", False):
                                st.session_state.db["chats"].pop(i)
                                if st.session_state.chat_id == i:
                                    st.session_state.chat_id = None
                                sync_io(st.session_state.db)
                                st.toast("Đã xóa", icon="🗑️")
                                st.rerun()
                            else:
                                st.session_state[f"confirm_del_{i}"] = True
                                st.warning("Nhấn lại để xác nhận")
            else:
                st.info("Chưa có hội thoại")
    else:
        with st.sidebar:
            st.info("👤 Chế độ khách: không lưu lịch sử")

    if st.session_state.guest_mode:
        chat = st.session_state.temp_chat
        if "msgs" not in chat:
            chat["msgs"] = []
    else:
        idx = st.session_state.chat_id
        if idx is None or idx >= len(st.session_state.db["chats"]):
            new_chat = {"name": "Hội thoại mới", "msgs": [], "owner": st.session_state.user,
                        "temp": False, "time": str(datetime.now())}
            st.session_state.db["chats"].append(new_chat)
            st.session_state.chat_id = len(st.session_state.db["chats"]) - 1
            idx = st.session_state.chat_id
        chat = st.session_state.db["chats"][idx]
        temp_mode = st.toggle("🧹 Chế độ tạm thời", value=chat.get("temp", False))
        chat["temp"] = temp_mode

    for m in chat["msgs"]:
        if m["role"] == "user":
            with st.chat_message("user"):
                st.write(m["content"])
        else:
            st.markdown(f'<div class="ai-banner">{m["content"]}</div>', unsafe_allow_html=True)

    if p := st.chat_input("Nhập câu hỏi..."):
        chat["msgs"].append({"role": "user", "content": p})
        with st.spinner("🤖 Đang xử lý..."):
            try:
                client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
                context = chat["msgs"][-5:] if not is_pro else chat["msgs"][-10:]
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=context,
                    temperature=0.7,
                    max_tokens=1024
                )
                ans = res.choices[0].message.content
            except Exception as e:
                ans = f"❌ Lỗi: {str(e)}"
            chat["msgs"].append({"role": "assistant", "content": ans})

        if not st.session_state.guest_mode and (chat["name"] == "Hội thoại mới" or len(chat["msgs"]) == (10 if is_pro else 4)):
            try:
                client_small = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
                n_res = client_small.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": f"Tóm tắt thành 5 từ: {p}"}]
                )
                new_name = n_res.choices[0].message.content.strip('".')
                if new_name:
                    chat["name"] = new_name[:30]
            except:
                pass

        if not st.session_state.guest_mode:
            sync_io(st.session_state.db)
        st.rerun()

# ================== CLOUD ==================
elif st.session_state.page == "CLOUD":
    st.header("☁️ NEXUS CLOUD")

    if st.session_state.guest_mode:
        st.warning("Guest không thể sử dụng lưu trữ. Đăng nhập để quản lý file.")
    else:
        used = get_used_storage(st.session_state.user)
        limit = CONFIG["FREE_STORAGE_LIMIT"] if not is_pro else float('inf')
        used_gb = used / (1024**3)
        limit_gb = limit / (1024**3) if limit != float('inf') else "∞"
        progress_val = min(used / limit, 1.0) if limit != float('inf') else 0
        st.progress(progress_val, text=f"Đã dùng: {used_gb:.2f} GB / {limit_gb} GB")
        if not is_pro and used >= limit:
            st.error("Đã vượt quá 30GB. Hãy xóa file hoặc nâng cấp Pro.")

        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"📁 /{st.session_state.current_dir}")
        with col2:
            if st.session_state.current_dir:
                if st.button("⬆️ Lên trên"):
                    parent = "/".join(st.session_state.current_dir.split("/")[:-1])
                    st.session_state.current_dir = parent
                    st.rerun()
        with col3:
            with st.popover("➕ Tạo thư mục"):
                new_folder = st.text_input("Tên thư mục")
                if st.button("Tạo"):
                    if new_folder:
                        path = (st.session_state.current_dir + "/" + new_folder) if st.session_state.current_dir else new_folder
                        if create_folder(path):
                            st.success(f"Đã tạo {new_folder}")
                            st.rerun()
                        else:
                            st.error("Đã tồn tại")

        items = list_dir(st.session_state.current_dir)
        if items["folders"]:
            st.subheader("📂 Thư mục")
            for folder in items["folders"]:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(f"📁 {folder}", key=f"open_{folder}"):
                        new_path = (st.session_state.current_dir + "/" + folder) if st.session_state.current_dir else folder
                        st.session_state.current_dir = new_path
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_folder_{folder}"):
                        full_path = (st.session_state.current_dir + "/" + folder) if st.session_state.current_dir else folder
                        delete_path(full_path)
                        st.toast(f"Đã xóa {folder}", icon="🗑️")
                        st.rerun()

        if items["files"]:
            st.subheader("📄 Tệp tin")
            for file in items["files"]:
                name = file["name"]
                info = file["info"]
                size_kb = info["size"] / 1024
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"📄 {name} ({size_kb:.1f} KB)")
                with col2:
                    st.markdown(f'<a href="data:{info["type"]};base64,{info["data"]}" download="{name}"><button style="background:#0047AB; color:white; border:none; border-radius:20px; padding:5px 12px;">📥 Tải</button></a>', unsafe_allow_html=True)
                with col3:
                    if st.button("👁️ Xem", key=f"view_{name}"):
                        st.session_state.preview_file = {"name": name, "data": info["data"], "type": info["type"]}
                        st.rerun()
                with col4:
                    if st.button("🗑️", key=f"del_{name}"):
                        full_path = (st.session_state.current_dir + "/" + name) if st.session_state.current_dir else name
                        delete_path(full_path)
                        st.toast(f"Đã xóa {name}", icon="🗑️")
                        st.rerun()

        st.divider()
        with st.expander("📤 Tải file lên"):
            uploaded_file = st.file_uploader("Chọn file", type=None)
            if uploaded_file:
                file_size = len(uploaded_file.getvalue())
                if not is_pro and used + file_size > limit:
                    st.error(f"Vượt quá dung lượng {limit_gb} GB")
                else:
                    if st.button("Tải lên"):
                        full_path = (st.session_state.current_dir + "/" + uploaded_file.name) if st.session_state.current_dir else uploaded_file.name
                        if full_path in st.session_state.db["files"]:
                            st.warning("File đã tồn tại")
                        else:
                            mime_type = mimetypes.guess_type(uploaded_file.name)[0] or "application/octet-stream"
                            st.session_state.db["files"][full_path] = {
                                "owner": st.session_state.user,
                                "data": base64.b64encode(uploaded_file.getvalue()).decode(),
                                "size": file_size,
                                "type": mime_type,
                                "upload_time": str(datetime.now())
                            }
                            sync_io(st.session_state.db)
                            st.toast(f"Đã tải lên {uploaded_file.name}", icon="✅")
                            st.rerun()

        if st.session_state.preview_file:
            st.divider()
            st.subheader(f"🔍 {st.session_state.preview_file['name']}")
            p = st.session_state.preview_file
            if p["type"].startswith("image/"):
                st.image(f"data:{p['type']};base64,{p['data']}", use_column_width=True)
            elif p["type"].startswith("text/"):
                try:
                    text = base64.b64decode(p["data"]).decode("utf-8")
                    st.text_area("Nội dung", text, height=300)
                except:
                    st.warning("Không thể hiển thị")
            else:
                st.info("Không hỗ trợ xem trước")
            if st.button("Đóng"):
                st.session_state.preview_file = None
                st.rerun()

# ================== CÀI ĐẶT ==================
elif st.session_state.page == "SETTINGS":
    st.header("⚙️ CÀI ĐẶT")

    if st.session_state.guest_mode:
        st.info("Guest không thể kích hoạt VIP.")
    else:
        with st.container():
            st.subheader("Kích hoạt Pro")
            code = st.text_input("Mã kích hoạt", placeholder="Nhập mã Pro").upper()
            if st.button("KÍCH HOẠT", use_container_width=True):
                if code in st.session_state.db["codes"]:
                    if st.session_state.user not in st.session_state.db["pro_users"]:
                        st.session_state.db["pro_users"].append(st.session_state.user)
                        st.session_state.db["codes"].remove(code)
                        sync_io(st.session_state.db)
                        st.balloons()
                        st.toast("🎉 Chúc mừng! Bạn đã là Pro!", icon="💎")
                        st.rerun()
                    else:
                        st.info("Bạn đã là Pro rồi!")
                else:
                    st.error("Mã không hợp lệ!")

        st.divider()
        st.subheader("Thông tin")
        st.write(f"**Tên:** {st.session_state.user}")
        st.write(f"**Hạng:** {'Pro' if is_pro else 'Miễn phí'}")
        if st.session_state.user in st.session_state.db.get("emails", {}):
            st.write(f"**Email:** {st.session_state.db['emails'][st.session_state.user]}")

# ================== ADMIN ==================
elif st.session_state.page == "ADMIN":
    if st.session_state.user != CONFIG["CREATOR"]:
        st.error("Không có quyền truy cập!")
        go_to("DASHBOARD")
    else:
        st.header("🛠️ ADMIN")
        
        tab1, tab2, tab3 = st.tabs(["Mã Pro", "Người dùng", "Đồng bộ"])
        
        with tab1:
            st.subheader("Tạo mã Pro")
            new_code = st.text_input("Mã mới").upper()
            if st.button("TẠO"):
                if new_code and new_code not in st.session_state.db["codes"]:
                    st.session_state.db["codes"].append(new_code)
                    sync_io(st.session_state.db)
                    st.toast(f"Đã tạo mã {new_code}", icon="✅")
                    st.rerun()
                else:
                    st.error("Mã đã tồn tại!")
            st.subheader("Danh sách mã")
            for code in st.session_state.db["codes"]:
                st.write(f"- {code}")
        
        with tab2:
            st.subheader("Người dùng")
            for user in st.session_state.db["users"]:
                is_pro = "PRO" if user in st.session_state.db["pro_users"] else "FREE"
                st.write(f"- {user} ({is_pro})")
            
            st.divider()
            st.subheader("Pro Users")
            for u in st.session_state.db["pro_users"]:
                col1, col2 = st.columns([3, 1])
                col1.write(f"- {u}")
                if col2.button("Xóa", key=f"remove_{u}"):
                    st.session_state.db["pro_users"].remove(u)
                    sync_io(st.session_state.db)
                    st.toast(f"Đã xóa {u}", icon="🗑️")
                    st.rerun()
        
        with tab3:
            if st.button("Đồng bộ từ GitHub"):
                with st.spinner("Đang đồng bộ..."):
                    st.session_state.db = sync_io()
                    st.toast("Đã đồng bộ!", icon="🔄")
                    st.rerun()
            if st.button("Lưu lên GitHub"):
                with st.spinner("Đang lưu..."):
                    sync_io(st.session_state.db)
                    st.toast("Đã lưu!", icon="💾")
