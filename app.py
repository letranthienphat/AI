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
    "ADMIN_USERNAME": "Thiên Phát",
    "ADMIN_PASSWORD": "nexusosgateway",
    "FILE_DATA": "data.json",
    "GUEST_ENABLED": True,
    "MAX_RETRIES": 3,
    "RETRY_DELAY": 1,
    "FREE_STORAGE_LIMIT": 30 * 1024 * 1024 * 1024
}

# Load secrets
try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str):
        GROQ_KEYS = [GROQ_KEYS]
except Exception:
    st.error("🛑 LỖI: Thiếu cấu hình Secrets trên Streamlit Cloud!")
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

def get_default_db() -> Dict:
    """Tạo database mặc định với admin"""
    return {
        "users": {CONFIG["ADMIN_USERNAME"]: CONFIG["ADMIN_PASSWORD"]},
        "codes": ["PHAT2026", "VIP2024", "PRO2025"],
        "pro_users": [],
        "chats": [],
        "files": {},
        "emails": {}
    }

def ensure_admin_exists(data: Dict) -> Dict:
    """Đảm bảo admin luôn tồn tại trong database"""
    if "users" not in data:
        data["users"] = {}
    # Force tạo admin, ghi đè nếu cần
    data["users"][CONFIG["ADMIN_USERNAME"]] = CONFIG["ADMIN_PASSWORD"]
    
    # Đảm bảo các key khác
    if "codes" not in data:
        data["codes"] = ["PHAT2026", "VIP2024", "PRO2025"]
    if "pro_users" not in data:
        data["pro_users"] = []
    if "chats" not in data:
        data["chats"] = []
    if "files" not in data:
        data["files"] = {}
    if "emails" not in data:
        data["emails"] = {}
    
    return data

def safe_load_json(content: str) -> Dict:
    try:
        data = json.loads(content)
        return ensure_admin_exists(data)
    except json.JSONDecodeError:
        return get_default_db()

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
                    default_data = get_default_db()
                    sync_io(default_data, retries=1)
                    return default_data
                else:
                    st.error(f"Lỗi đọc GitHub: {res.status_code}")
                    return get_default_db()
            else:
                # Đảm bảo admin tồn tại trước khi ghi
                data = ensure_admin_exists(data)
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
                        return data
                else:
                    return data
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(CONFIG["RETRY_DELAY"])
            else:
                st.error(f"Lỗi kết nối: {str(e)}")
                return get_default_db()
    return None

@st.cache_data(ttl=60)
def load_db():
    return sync_io()

def init_session():
    if 'db' not in st.session_state:
        st.session_state.db = load_db()
        # Force đảm bảo admin tồn tại
        st.session_state.db = ensure_admin_exists(st.session_state.db)
        sync_io(st.session_state.db)
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
    if username == CONFIG["ADMIN_USERNAME"]:
        return False, "Tên đăng nhập này đã được sử dụng"
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
        if st.session_state.user == CONFIG["ADMIN_USERNAME"]:
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
    st.caption("NEXUS OS GATEWAY")

# ================== TRANG ĐĂNG NHẬP ==================
if st.session_state.page == "AUTH":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        
        # Debug info (có thể bỏ sau khi ổn định)
        with st.expander("ℹ️ Thông tin đăng nhập"):
            st.write("**Tài khoản mặc định:**")
            st.write(f"- Tên: `{CONFIG['ADMIN_USERNAME']}`")
            st.write(f"- Mật khẩu: `{CONFIG['ADMIN_PASSWORD']}`")
            st.write("**Lưu ý:** Mật khẩu viết liền, không dấu, không khoảng trắng")
        
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
                        # Debug
                        st.session_state.debug_user = username_clean
                        st.session_state.debug_pass = login_password
                        
                        if username_clean in st.session_state.db["users"]:
                            stored_pass = st.session_state.db["users"][username_clean]
                            if stored_pass == login_password:
                                st.session_state.user = username_clean
                                st.session_state.guest_mode = False
                                st.toast(f"✅ Đăng nhập thành công!", icon="🎉")
                                go_to("DASHBOARD")
                            else:
                                st.error(f"❌ Sai mật khẩu!")
                                st.info(f"Debug: Mật khẩu nhập: '{login_password}', Mật khẩu đúng: '{stored_pass}'")
                        else:
                            st.error(f"❌ Tài khoản không tồn tại!")
                            st.info(f"Debug: Các tài khoản hiện có: {list(st.session_state.db['users'].keys())}")
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

# ================== CÁC TRANG KHÁC ==================
# (Giữ nguyên các trang DASHBOARD, AI, CLOUD, SETTINGS, ADMIN từ code trước)
# Để tránh quá dài, tôi sẽ giữ nguyên các phần này

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

    if st.session_state.user == CONFIG["ADMIN_USERNAME"]:
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

# ================== CLOUD, SETTINGS, ADMIN ==================
# (Giữ nguyên các phần này từ code trước để tránh trùng lặp)
# ... [các phần CLOUD, SETTINGS, ADMIN giống code trước] ...
