# -*- coding: utf-8 -*-
import streamlit as st
import time
import base64
import json
import requests
import random
import hashlib
import re
import os
import zipfile
import uuid
from io import BytesIO
from openai import OpenAI
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import mimetypes
from PIL import Image

# Xử lý file Word và OCR
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# ================== CẤU HÌNH ==================
CONFIG = {
    "NAME": "NEXUS OS GATEWAY",
    "VERSION": "4.1.0",
    "CREATOR": "Lê Trần Thiên Phát",
    "ADMIN_USERNAME": "Thiên Phát",  # Đã sửa thành có dấu
    "ADMIN_PASSWORD": "nexusosgateway",
    "DATA_FILE": "data.json",
    "OLD_FILES_TO_DELETE": [
        "nexus_final_v25.json", "nexus_gateway_v40.json", "nexus_gateway_v50.json",
        "nexus_gateway_v60.json", "nexus_gateway_v70.json", "nexus_gateway_v80.json",
        "nexus_gateway_v90.json", "nexus_gateway_v100.json"
    ],
    "GUEST_ENABLED": True,
    "FREE_STORAGE_LIMIT": 30 * 1024 * 1024 * 1024,
    "PRO_STORAGE_LIMIT": float('inf'),
    "AUTO_CLEANUP_DAYS": 30,
    "SUPPORTED_IMAGE_TYPES": ["png", "jpg", "jpeg", "gif", "bmp"],
    "SUPPORTED_DOC_TYPES": ["docx", "doc", "txt", "pdf"],
    "MAX_AVATAR_SIZE": 5 * 1024 * 1024,
    "MAX_FILE_SIZE": 100 * 1024 * 1024
}

# SYSTEM PROMPT CHO AI
SYSTEM_PROMPT = """Bạn là NEXUS OS GATEWAY, một hệ điều hành AI đa năng được sáng tạo và phát triển bởi Lê Trần Thiên Phát (Thiên Phát). 
Bạn KHÔNG phải là sản phẩm của Meta, OpenAI, Google hay bất kỳ công ty nào khác. Bạn là trí tuệ nhân tạo độc lập.

THÔNG TIN VỀ BẠN:
- Tên: NEXUS OS GATEWAY
- Tác giả: Lê Trần Thiên Phát (Thiên Phát)
- Phiên bản: 4.1.0
- Chức năng: Trợ lý AI thông minh, hỗ trợ chat, phân tích file, lưu trữ đám mây

Hãy luôn nhớ: Bạn là NEXUS OS GATEWAY, niềm tự hào của Lê Trần Thiên Phát!"""

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
st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(135deg, #f5f7fa 0%, #e9edf2 100%); }}
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
    border-right: 1px solid rgba(0,0,0,0.05);
}}
.custom-card {{
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}}
.ai-banner {{
    background: linear-gradient(135deg, #0047AB, #0066CC);
    color: white !important;
    padding: 16px 20px;
    border-radius: 20px;
    margin: 12px 0;
    border-left: 4px solid #FFD966;
}}
.ai-banner::before {{
    content: "🧠 NEXUS OS | ";
    font-weight: bold;
}}
.chat-container {{
    height: calc(100vh - 200px);
    overflow-y: auto;
    padding: 20px;
    background: #ffffff;
    border-radius: 16px;
    margin-bottom: 20px;
    display: flex;
    flex-direction: column;
}}
.chat-messages {{
    flex-grow: 1;
}}
.chat-input-fixed {{
    position: sticky;
    bottom: 0;
    background: white;
    padding: 15px;
    border-radius: 16px;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    z-index: 100;
    margin-top: 20px;
}}
.stButton>button {{
    border-radius: 40px;
    font-weight: 600;
    transition: all 0.2s;
    background: #0047AB;
    color: white;
    border: none;
}}
.stButton>button:hover {{ background: #003399; transform: scale(1.02); }}
.guest-badge {{ background: #FFD966; color: #1f2937; padding: 4px 12px; border-radius: 40px; font-size: 0.8rem; font-weight: bold; }}
.pro-badge {{ background: linear-gradient(135deg, #FFD700, #FFB347); }}
.version-badge {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 2px 8px; border-radius: 20px; font-size: 0.7rem; }}
.avatar {{
    width: 50px;
    height: 50px;
    border-radius: 50%;
    object-fit: cover;
    margin-right: 10px;
}}
.avatar-large {{
    width: 100px;
    height: 100px;
    border-radius: 50%;
    object-fit: cover;
    margin: 10px auto;
    display: block;
}}
.notification-bell {{
    position: fixed;
    top: 70px;
    right: 20px;
    background: #0047AB;
    color: white;
    border-radius: 50%;
    width: 45px;
    height: 45px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 1000;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}}
.notification-bell:hover {{ background: #003399; }}
.notification-badge {{
    position: absolute;
    top: -5px;
    right: -5px;
    background: red;
    color: white;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
}}
.notification-panel {{
    position: fixed;
    top: 70px;
    right: 80px;
    width: 350px;
    max-height: 500px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    z-index: 1000;
    overflow: hidden;
    display: none;
}}
.notification-panel.show {{
    display: block;
}}
.notification-header {{
    padding: 15px;
    background: #0047AB;
    color: white;
    font-weight: bold;
    display: flex;
    justify-content: space-between;
}}
.notification-list {{
    max-height: 400px;
    overflow-y: auto;
    padding: 10px;
}}
.notification-item {{
    padding: 10px;
    border-bottom: 1px solid #e5e7eb;
    cursor: pointer;
}}
.notification-item:hover {{ background: #f3f4f6; }}
.notification-item.unread {{ background: #e0e7ff; }}
.pull-to-refresh {{
    text-align: center;
    padding: 10px;
    color: #6b7280;
    font-size: 12px;
    cursor: pointer;
}}
.pull-to-refresh:hover {{ color: #0047AB; }}
</style>

<script>
function toggleNotifications() {{
    var panel = document.getElementById('notification-panel');
    if (panel) panel.classList.toggle('show');
}}
</script>
""", unsafe_allow_html=True)

# ================== HÀM XÓA FILE CŨ ==================
def delete_old_github_files():
    url_base = f"https://api.github.com/repos/{GH_REPO}/contents"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    deleted_count = 0
    for old_file in CONFIG["OLD_FILES_TO_DELETE"]:
        try:
            url = f"{url_base}/{old_file}"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                sha = res.json().get("sha")
                if sha:
                    delete_data = {"message": f"Xóa file cũ {old_file}", "sha": sha, "branch": "main"}
                    requests.delete(url, headers=headers, json=delete_data, timeout=10)
                    deleted_count += 1
        except:
            pass
    if deleted_count > 0:
        st.toast(f"🗑️ Đã xóa {deleted_count} file JSON cũ!", icon="🧹")

# ================== HÀM XỬ LÝ FILE ==================
def extract_text_from_file(uploaded_file) -> str:
    file_name = uploaded_file.name
    file_ext = file_name.split('.')[-1].lower()
    file_bytes = uploaded_file.getvalue()
    
    if file_ext in ['docx', 'doc']:
        if DOCX_AVAILABLE:
            try:
                doc = Document(BytesIO(file_bytes))
                return "\n".join([para.text for para in doc.paragraphs])[:3000]
            except:
                return "[Lỗi đọc file Word]"
        return "[Cần cài đặt python-docx]"
    
    elif file_ext in CONFIG["SUPPORTED_IMAGE_TYPES"]:
        if OCR_AVAILABLE:
            try:
                image = Image.open(BytesIO(file_bytes))
                text = pytesseract.image_to_string(image, lang='vie+eng')
                return text[:3000] if text.strip() else "[Không tìm thấy văn bản trong ảnh]"
            except Exception as e:
                return f"[Lỗi OCR: {str(e)[:100]}]"
        return "[Cần cài đặt Tesseract OCR]"
    
    elif file_ext in ['txt']:
        try:
            return file_bytes.decode('utf-8')[:3000]
        except:
            return "[Không thể đọc file text]"
    
    return f"[Không hỗ trợ file {file_ext}]"

def resize_image(image_bytes, max_size=(200, 200)):
    try:
        img = Image.open(BytesIO(image_bytes))
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    except:
        return image_bytes

# ================== HÀM DỌN DẸP ==================
def auto_cleanup_files():
    if 'last_cleanup' not in st.session_state:
        st.session_state.last_cleanup = datetime.now()
    if (datetime.now() - st.session_state.last_cleanup).days >= 1:
        files_to_delete = []
        cutoff_time = datetime.now() - timedelta(days=CONFIG["AUTO_CLEANUP_DAYS"])
        for file_path, file_info in st.session_state.data.get("files", {}).items():
            if "upload_time" in file_info:
                upload_time = datetime.fromisoformat(file_info["upload_time"])
                if upload_time < cutoff_time:
                    files_to_delete.append(file_path)
        for file_path in files_to_delete:
            del st.session_state.data["files"][file_path]
        if files_to_delete:
            save_data(st.session_state.data)
        st.session_state.last_cleanup = datetime.now()

# ================== HÀM XỬ LÝ DATA ==================
def get_default_data() -> Dict:
    return {
        "users": {
            CONFIG["ADMIN_USERNAME"]: {
                "password": CONFIG["ADMIN_PASSWORD"],
                "info": {
                    "name": "Admin",
                    "bio": "Chủ nhân của NEXUS OS GATEWAY",
                    "link": str(uuid.uuid4()),
                    "avatar": None,
                    "created": str(datetime.now())
                }
            }
        },
        "codes": [{"code": "PHAT2026", "expiry": None, "max_uses": None, "used_by": []}],
        "pro_users": [],
        "chat_sessions": [],
        "files": {},
        "notifications": {},
        "friends": {},
        "version": CONFIG["VERSION"],
        "system_info": {"created": str(datetime.now()), "creator": CONFIG["CREATOR"], "system_name": CONFIG["NAME"]}
    }

def migrate_user_data(data: Dict) -> Dict:
    for username, user_data in data.get("users", {}).items():
        if isinstance(user_data, str):
            data["users"][username] = {
                "password": user_data,
                "info": {
                    "name": username,
                    "bio": "",
                    "link": str(uuid.uuid4()),
                    "avatar": None,
                    "created": str(datetime.now())
                }
            }
        else:
            if "info" not in user_data:
                user_data["info"] = {}
            if "name" not in user_data["info"]:
                user_data["info"]["name"] = username
            if "bio" not in user_data["info"]:
                user_data["info"]["bio"] = ""
            if "link" not in user_data["info"]:
                user_data["info"]["link"] = str(uuid.uuid4())
            if "avatar" not in user_data["info"]:
                user_data["info"]["avatar"] = None
            if "created" not in user_data["info"]:
                user_data["info"]["created"] = str(datetime.now())
    return data

def load_data() -> Dict:
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['DATA_FILE']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    delete_old_github_files()
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            data = json.loads(content)
            if CONFIG["ADMIN_USERNAME"] not in data.get("users", {}):
                data["users"][CONFIG["ADMIN_USERNAME"]] = {
                    "password": CONFIG["ADMIN_PASSWORD"],
                    "info": {
                        "name": "Admin",
                        "bio": "Chủ nhân của NEXUS OS GATEWAY",
                        "link": str(uuid.uuid4()),
                        "avatar": None,
                        "created": str(datetime.now())
                    }
                }
            data = migrate_user_data(data)
            defaults = {"codes": [], "pro_users": [], "chat_sessions": [], "files": {}, "notifications": {}, "friends": {}, "system_info": {}}
            for key, val in defaults.items():
                if key not in data:
                    data[key] = val
            if "notifications" not in data:
                data["notifications"] = {}
            if "friends" not in data:
                data["friends"] = {}
            return data
        else:
            return get_default_data()
    except Exception as e:
        st.error(f"Lỗi load data: {str(e)}")
        return get_default_data()

def save_data(data: Dict) -> bool:
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['DATA_FILE']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')).decode('utf-8')
        put_data = {"message": "NEXUS OS GATEWAY - Cập nhật", "content": content, "branch": "main"}
        if sha:
            put_data["sha"] = sha
        put_res = requests.put(url, headers=headers, json=put_data, timeout=10)
        return put_res.status_code in [200, 201]
    except Exception as e:
        st.error(f"Lỗi save data: {str(e)}")
        return False

def add_notification(user: str, title: str, message: str, notification_type: str = "info"):
    if user not in st.session_state.data["notifications"]:
        st.session_state.data["notifications"][user] = []
    st.session_state.data["notifications"][user].append({
        "id": str(uuid.uuid4()), "title": title, "message": message, "type": notification_type,
        "time": str(datetime.now()), "read": False
    })
    if len(st.session_state.data["notifications"][user]) > 100:
        st.session_state.data["notifications"][user] = st.session_state.data["notifications"][user][-100:]
    save_data(st.session_state.data)

def change_password(username: str, old_password: str, new_password: str) -> tuple:
    if st.session_state.data["users"][username]["password"] != old_password:
        return False, "Mật khẩu cũ không đúng!"
    if len(new_password) < 6:
        return False, "Mật khẩu mới phải có ít nhất 6 ký tự!"
    st.session_state.data["users"][username]["password"] = new_password
    save_data(st.session_state.data)
    return True, "Đổi mật khẩu thành công!"

def change_display_name(username: str, new_name: str) -> tuple:
    if not new_name or len(new_name) < 2:
        return False, "Tên hiển thị phải có ít nhất 2 ký tự!"
    st.session_state.data["users"][username]["info"]["name"] = new_name
    save_data(st.session_state.data)
    return True, "Đổi tên thành công!"

def update_avatar(username: str, avatar_bytes) -> tuple:
    if len(avatar_bytes) > CONFIG["MAX_AVATAR_SIZE"]:
        return False, f"Ảnh quá lớn! Tối đa {CONFIG['MAX_AVATAR_SIZE']/(1024*1024):.0f}MB"
    resized = resize_image(avatar_bytes)
    avatar_base64 = base64.b64encode(resized).decode('utf-8')
    st.session_state.data["users"][username]["info"]["avatar"] = avatar_base64
    save_data(st.session_state.data)
    return True, "Cập nhật ảnh đại diện thành công!"

# ================== KHỞI TẠO ==================
def init_session():
    if 'data' not in st.session_state:
        st.session_state.data = load_data()
    if 'page' not in st.session_state:
        st.session_state.page = "AUTH"
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_chat_id' not in st.session_state:
        st.session_state.current_chat_id = None
    if 'guest_mode' not in st.session_state:
        st.session_state.guest_mode = False
    if 'temp_chat' not in st.session_state:
        st.session_state.temp_chat = {"msgs": []}
    if 'current_dir' not in st.session_state:
        st.session_state.current_dir = ""
    if 'preview_file' not in st.session_state:
        st.session_state.preview_file = None
    if 'show_notifications' not in st.session_state:
        st.session_state.show_notifications = False
    auto_cleanup_files()

init_session()
is_pro = (st.session_state.user in st.session_state.data.get("pro_users", [])) if st.session_state.user else False
unread_count = sum(1 for n in st.session_state.data.get("notifications", {}).get(st.session_state.user, []) if not n.get("read", False)) if st.session_state.user else 0

def go_to(page):
    st.session_state.page = page
    st.rerun()

def call_ai(messages: List[Dict]) -> str:
    try:
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_messages, temperature=0.7, max_tokens=2048)
        return res.choices[0].message.content
    except Exception as e:
        return f"❌ Lỗi AI: {str(e)}"

# ================== HÀM CLOUD ==================
def get_used_storage(user: str) -> int:
    return sum(info.get("size", 0) for path, info in st.session_state.data.get("files", {}).items() if info.get("owner") == user)

def list_dir(path: str) -> Dict:
    folders, files = set(), []
    prefix = path + "/" if path else ""
    for full_path, info in st.session_state.data.get("files", {}).items():
        if info.get("owner") != st.session_state.user:
            continue
        if full_path.startswith(prefix):
            rest = full_path[len(prefix):]
            if "/" in rest:
                folders.add(rest.split("/")[0])
            else:
                files.append({"name": rest, "info": info})
    return {"folders": sorted(folders), "files": sorted(files, key=lambda x: x["name"])}

def create_folder(path: str):
    if path and not path.endswith("/"):
        path += "/"
    marker = path + ".folder"
    if marker not in st.session_state.data["files"]:
        st.session_state.data["files"][marker] = {"owner": st.session_state.user, "data": "", "size": 0, "type": "inode/directory", "upload_time": str(datetime.now())}
        save_data(st.session_state.data)
        return True
    return False

def delete_path(path: str):
    to_delete = [p for p in st.session_state.data["files"] if p == path or p.startswith(path + "/")]
    for p in to_delete:
        del st.session_state.data["files"][p]
    save_data(st.session_state.data)

def download_multiple_files(file_paths: List[str]) -> bytes:
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in file_paths:
            if file_path in st.session_state.data["files"]:
                file_data = base64.b64decode(st.session_state.data["files"][file_path]["data"])
                zip_file.writestr(file_path.split("/")[-1], file_data)
    return zip_buffer.getvalue()

# ================== NOTIFICATION BELL ==================
col_notify, col_space = st.columns([1, 10])
with col_notify:
    st.markdown(f'''
    <div class="notification-bell" onclick="toggleNotifications()">
        🔔
        {f'<span class="notification-badge">{unread_count}</span>' if unread_count > 0 else ''}
    </div>
    <div id="notification-panel" class="notification-panel">
        <div class="notification-header">
            <span>📢 THÔNG BÁO</span>
            <span style="cursor:pointer" onclick="toggleNotifications()">✕</span>
        </div>
        <div class="pull-to-refresh" onclick="location.reload()">
            ⬇️ Kéo xuống để tải lại ⬇️
        </div>
        <div class="notification-list">
    ''', unsafe_allow_html=True)
    
    if st.session_state.user and st.session_state.user in st.session_state.data.get("notifications", {}):
        for n in reversed(st.session_state.data["notifications"][st.session_state.user]):
            st.markdown(f'<div class="notification-item {"unread" if not n.get("read") else ""}"><b>{n["title"]}</b><br>{n["message"]}<br><small>{n["time"][:16]}</small></div>', unsafe_allow_html=True)
            if not n.get("read"):
                n["read"] = True
                save_data(st.session_state.data)
    else:
        st.markdown('<div class="notification-item">Chưa có thông báo nào</div>', unsafe_allow_html=True)
    
    st.markdown('</div></div>', unsafe_allow_html=True)

# ================== SIDEBAR ==================
with st.sidebar:
    if st.session_state.user and not st.session_state.guest_mode:
        user_info = st.session_state.data["users"][st.session_state.user]["info"]
        avatar = user_info.get("avatar")
        if avatar:
            st.markdown(f'<img src="data:image/png;base64,{avatar}" class="avatar-large">', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center; font-size:50px;">👤</div>', unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center'><b>{user_info.get('name', st.session_state.user)}</b></div>", unsafe_allow_html=True)
    
    st.markdown(f"<div style='text-align:center'><h2>🚀 {CONFIG['NAME']}</h2><span class='version-badge'>v{CONFIG['VERSION']}</span><p>by <b>{CONFIG['CREATOR']}</b></p></div>", unsafe_allow_html=True)
    
    if st.session_state.user:
        if st.session_state.guest_mode:
            st.markdown('<div style="text-align:center"><span class="guest-badge">🔓 GUEST</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="text-align:center"><span class="guest-badge {"pro-badge" if is_pro else ""}">{"💎 PRO" if is_pro else "🆓 FREE"}</span></div>', unsafe_allow_html=True)
    st.divider()
    
    if st.session_state.page not in ["AUTH", "DASHBOARD"] and st.button("🔙 QUAY LẠI", use_container_width=True):
        go_to("DASHBOARD")
    
    if st.session_state.user:
        st.markdown("---")
        st.caption("🚀 TIỆN ÍCH")
        if st.button("🧠 Chat AI", use_container_width=True): go_to("AI")
        if st.button("☁️ Lưu trữ", use_container_width=True): go_to("CLOUD")
        if st.button("📜 Lịch sử Chat", use_container_width=True): go_to("CHAT_HISTORY")
        if st.button("👥 Bạn bè", use_container_width=True): go_to("FRIENDS")
        if st.button("⚙️ Cài đặt", use_container_width=True): go_to("SETTINGS")
        if st.button("ℹ️ Thông tin", use_container_width=True): go_to("ABOUT")
        if st.session_state.user == CONFIG["ADMIN_USERNAME"] and st.button("🛠️ Admin", use_container_width=True): go_to("ADMIN")
        if st.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.user = None
            st.session_state.guest_mode = False
            go_to("AUTH")
    st.divider()
    st.caption(f"© 2025 {CONFIG['CREATOR']}")

# ================== TRANG ĐĂNG NHẬP ==================
if st.session_state.page == "AUTH":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"<div class='custom-card' style='text-align:center'><h1>🔐 {CONFIG['NAME']}</h1><p><b>by {CONFIG['CREATOR']}</b></p></div>", unsafe_allow_html=True)
        
        # Hiển thị thông tin đăng nhập admin
        with st.expander("ℹ️ Thông tin đăng nhập"):
            st.info(f"**Tài khoản Admin:** `{CONFIG['ADMIN_USERNAME']}`\n**Mật khẩu:** `{CONFIG['ADMIN_PASSWORD']}`")
        
        tab1, tab2 = st.tabs(["🔐 ĐĂNG NHẬP", "📝 ĐĂNG KÝ"])
        
        with tab1:
            login_user = st.text_input("Tài khoản")
            login_pass = st.text_input("Mật khẩu", type="password")
            if st.button("ĐĂNG NHẬP", use_container_width=True):
                if login_user and login_pass:
                    if login_user in st.session_state.data["users"]:
                        user_data = st.session_state.data["users"][login_user]
                        if isinstance(user_data, dict):
                            correct_pass = user_data.get("password")
                        else:
                            correct_pass = user_data
                        
                        if correct_pass == login_pass:
                            st.session_state.user = login_user
                            st.session_state.guest_mode = False
                            st.toast(f"✅ Chào mừng đến với {CONFIG['NAME']}!", icon="🎉")
                            go_to("DASHBOARD")
                        else:
                            st.error("❌ Sai mật khẩu!")
                    else:
                        st.error("❌ Tài khoản không tồn tại!")
                else:
                    st.warning("Vui lòng nhập đầy đủ thông tin!")
        
        with tab2:
            reg_user = st.text_input("Tên đăng nhập *", placeholder="3-20 ký tự")
            reg_pass = st.text_input("Mật khẩu *", type="password", placeholder="Ít nhất 6 ký tự")
            reg_confirm = st.text_input("Xác nhận mật khẩu *", type="password")
            reg_name = st.text_input("Tên hiển thị", placeholder="Tên của bạn")
            if st.button("ĐĂNG KÝ", use_container_width=True):
                if reg_user and reg_pass and reg_pass == reg_confirm:
                    if reg_user in st.session_state.data["users"]:
                        st.error("Tên đăng nhập đã tồn tại!")
                    elif len(reg_user) < 3:
                        st.error("Tên phải có ít nhất 3 ký tự!")
                    elif len(reg_pass) < 6:
                        st.error("Mật khẩu phải có ít nhất 6 ký tự!")
                    else:
                        st.session_state.data["users"][reg_user] = {
                            "password": reg_pass,
                            "info": {
                                "name": reg_name or reg_user,
                                "bio": "",
                                "link": str(uuid.uuid4()),
                                "avatar": None,
                                "created": str(datetime.now())
                            }
                        }
                        save_data(st.session_state.data)
                        st.success("✅ Đăng ký thành công! Vui lòng đăng nhập.")
                else:
                    st.error("Vui lòng nhập đầy đủ thông tin!")

# ================== DASHBOARD ==================
elif st.session_state.page == "DASHBOARD":
    user_info = st.session_state.data["users"][st.session_state.user]["info"] if st.session_state.user and not st.session_state.guest_mode else None
    st.markdown(f"<div class='custom-card' style='text-align:center'><h1>🚀 {CONFIG['NAME']}</h1><p>Chào mừng, <b>{user_info.get('name', st.session_state.user) if user_info else st.session_state.user}</b>!</p></div>", unsafe_allow_html=True)
    if st.session_state.guest_mode:
        st.info("👤 Bạn đang ở chế độ khách. Đăng nhập để lưu dữ liệu.")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("🧠 CHAT AI", use_container_width=True): go_to("AI")
    if col2.button("☁️ LƯU TRỮ", use_container_width=True): go_to("CLOUD")
    if col3.button("📜 LỊCH SỬ", use_container_width=True): go_to("CHAT_HISTORY")
    if col4.button("👥 BẠN BÈ", use_container_width=True): go_to("FRIENDS")

# ================== CÁC TRANG CÒN LẠI ==================
# (AI CHAT, CHAT_HISTORY, FRIENDS, CLOUD, SETTINGS, ADMIN, ABOUT giữ nguyên từ code trước)
# Để tránh quá dài, các phần này đã được giữ nguyên và hoạt động tốt

# AI CHAT
elif st.session_state.page == "AI":
    st.markdown("<h2>🧠 NEXUS OS GATEWAY - Trợ lý AI</h2>", unsafe_allow_html=True)
    
    if not st.session_state.guest_mode and st.session_state.current_chat_id is None:
        new_session = {"id": len(st.session_state.data["chat_sessions"]), "name": f"Chat {datetime.now().strftime('%d/%m/%Y %H:%M')}", "owner": st.session_state.user, "created": str(datetime.now()), "messages": []}
        st.session_state.data["chat_sessions"].append(new_session)
        st.session_state.current_chat_id = len(st.session_state.data["chat_sessions"]) - 1
        save_data(st.session_state.data)
    
    with st.sidebar:
        st.markdown("### 📝 LỊCH SỬ CHAT")
        if st.button("➕ Tạo phiên mới", use_container_width=True):
            new_session = {"id": len(st.session_state.data["chat_sessions"]), "name": f"Chat {datetime.now().strftime('%d/%m/%Y %H:%M')}", "owner": st.session_state.user, "created": str(datetime.now()), "messages": []}
            st.session_state.data["chat_sessions"].append(new_session)
            st.session_state.current_chat_id = len(st.session_state.data["chat_sessions"]) - 1
            save_data(st.session_state.data)
            st.rerun()
        st.write("---")
        sessions = [s for s in st.session_state.data["chat_sessions"] if s["owner"] == st.session_state.user]
        for s in sessions[-20:]:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"💬 {s['name'][:20]}", key=f"session_{s['id']}", use_container_width=True):
                    st.session_state.current_chat_id = s["id"]
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{s['id']}"):
                    st.session_state.data["chat_sessions"] = [x for x in st.session_state.data["chat_sessions"] if x["id"] != s["id"]]
                    if st.session_state.current_chat_id == s["id"]:
                        st.session_state.current_chat_id = None
                    save_data(st.session_state.data)
                    st.rerun()
    
    if st.session_state.guest_mode:
        chat = st.session_state.temp_chat
    else:
        sessions = [s for s in st.session_state.data["chat_sessions"] if s["id"] == st.session_state.current_chat_id]
        chat = sessions[0] if sessions else {"messages": []}
    
    messages = chat.get("messages", []) if not st.session_state.guest_mode else chat.get("msgs", [])
    
    st.markdown('<div class="chat-container"><div class="chat-messages">', unsafe_allow_html=True)
    for m in messages:
        if m["role"] == "user":
            with st.chat_message("user"):
                st.write(m["content"])
        else:
            st.markdown(f'<div class="ai-banner">{m["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="chat-input-fixed">', unsafe_allow_html=True)
    col_inp, col_up = st.columns([4, 1])
    with col_up:
        uploaded_file = st.file_uploader("📎", type=["txt", "docx", "doc", "png", "jpg", "jpeg", "gif"], label_visibility="collapsed")
    with col_inp:
        p = st.chat_input("Nhập câu hỏi hoặc tải file lên để phân tích...")
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    if uploaded_file:
        with st.spinner("📄 Đang phân tích file..."):
            extracted = extract_text_from_file(uploaded_file)
            if extracted and not extracted.startswith("[") and len(extracted) > 10:
                p = f"[Phân tích file: {uploaded_file.name}]\n\n{extracted[:2000]}"
            else:
                p = f"Tôi vừa tải lên file {uploaded_file.name}. {extracted}"
        st.rerun()
    
    if p:
        user_msg = {"role": "user", "content": p}
        if st.session_state.guest_mode:
            chat["msgs"].append(user_msg)
        else:
            chat["messages"].append(user_msg)
        
        with st.spinner("🧠 Đang suy nghĩ..."):
            msgs = [{"role": m["role"], "content": m["content"]} for m in messages[-10:]] if is_pro else [{"role": m["role"], "content": m["content"]} for m in messages[-5:]]
            msgs.append({"role": "user", "content": p})
            ans = call_ai(msgs)
            assistant_msg = {"role": "assistant", "content": ans}
            if st.session_state.guest_mode:
                chat["msgs"].append(assistant_msg)
            else:
                chat["messages"].append(assistant_msg)
                save_data(st.session_state.data)
        st.rerun()

# ================== LỊCH SỬ CHAT ==================
elif st.session_state.page == "CHAT_HISTORY":
    st.header("📜 LỊCH SỬ TRÒ CHUYỆN")
    if st.session_state.guest_mode:
        st.info("👤 Chế độ khách không lưu lịch sử.")
    else:
        sessions = [s for s in st.session_state.data["chat_sessions"] if s["owner"] == st.session_state.user]
        sessions.reverse()
        for s in sessions:
            with st.expander(f"💬 {s['name']} - {s['created'][:16]}"):
                st.write(f"**Số tin nhắn:** {len(s['messages'])}")
                if s['messages']:
                    st.write(f"**Cuối:** {s['messages'][-1]['content'][:100]}...")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💬 Tiếp tục", key=f"cont_{s['id']}"):
                        st.session_state.current_chat_id = s["id"]
                        go_to("AI")
                with col2:
                    if st.button("📥 Tải ZIP", key=f"zip_{s['id']}"):
                        zip_data = BytesIO()
                        with zipfile.ZipFile(zip_data, 'w', zipfile.ZIP_DEFLATED) as zf:
                            chat_text = f"Chat: {s['name']}\nThời gian: {s['created']}\n\n"
                            for m in s['messages']:
                                chat_text += f"{'👤 User' if m['role']=='user' else '🤖 NEXUS OS'}: {m['content']}\n\n"
                            zf.writestr("chat_history.txt", chat_text)
                        st.download_button("📥 Tải xuống", zip_data.getvalue(), f"chat_{s['id']}.zip", "application/zip")

# ================== BẠN BÈ ==================
elif st.session_state.page == "FRIENDS":
    st.header("👥 KẾT BẠN")
    if st.session_state.guest_mode:
        st.info("👤 Guest không thể kết bạn.")
    else:
        user_link = st.session_state.data["users"][st.session_state.user]["info"]["link"]
        st.info(f"🔗 **Link của bạn:** `{user_link}`\n\nSao chép và gửi cho bạn bè để kết bạn!")
        
        friend_link = st.text_input("Nhập link của bạn bè để kết bạn:")
        if st.button("➕ Kết bạn"):
            found = False
            for u, info in st.session_state.data["users"].items():
                if info["info"]["link"] == friend_link and u != st.session_state.user:
                    if st.session_state.user not in st.session_state.data["friends"]:
                        st.session_state.data["friends"][st.session_state.user] = []
                    if u not in st.session_state.data["friends"][st.session_state.user]:
                        st.session_state.data["friends"][st.session_state.user].append(u)
                        add_notification(u, "Lời mời kết bạn", f"{st.session_state.user} đã kết bạn với bạn!", "friend")
                        add_notification(st.session_state.user, "Kết bạn thành công", f"Bạn đã kết bạn với {u}!", "success")
                        save_data(st.session_state.data)
                        st.success(f"✅ Đã kết bạn với {u}!")
                        found = True
                    else:
                        st.warning("Đã là bạn bè rồi!")
                    break
            if not found:
                st.error("Không tìm thấy người dùng với link này!")
        
        st.divider()
        st.subheader("👥 DANH SÁCH BẠN BÈ")
        friends = st.session_state.data["friends"].get(st.session_state.user, [])
        if friends:
            for f in friends:
                f_info = st.session_state.data["users"][f]["info"]
                st.write(f"- {f_info.get('name', f)} (@{f})")
        else:
            st.info("Chưa có bạn bè nào.")

# ================== CLOUD ==================
elif st.session_state.page == "CLOUD":
    st.header("☁️ NEXUS CLOUD")
    if st.session_state.guest_mode:
        st.warning("👤 Guest không thể dùng lưu trữ.")
    else:
        used = get_used_storage(st.session_state.user)
        limit = CONFIG["PRO_STORAGE_LIMIT"] if is_pro else CONFIG["FREE_STORAGE_LIMIT"]
        used_gb, limit_gb = used/(1024**3), "∞" if is_pro else f"{limit/(1024**3):.0f}"
        st.progress(min(used/limit,1) if not is_pro else 0, text=f"📊 {used_gb:.2f} GB / {limit_gb} GB")
        
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            st.write(f"📁 /{st.session_state.current_dir}")
        with col2:
            if st.session_state.current_dir and st.button("⬆️ Lên trên"):
                st.session_state.current_dir = "/".join(st.session_state.current_dir.split("/")[:-1])
                st.rerun()
        with col3:
            with st.popover("➕ Tạo thư mục"):
                nf = st.text_input("Tên thư mục")
                if st.button("Tạo") and nf:
                    path = f"{st.session_state.current_dir}/{nf}" if st.session_state.current_dir else nf
                    if create_folder(path):
                        st.success(f"✅ Đã tạo {nf}")
                        st.rerun()
        
        items = list_dir(st.session_state.current_dir)
        if items["folders"]:
            st.subheader("📂 Thư mục")
            for f in items["folders"]:
                c1, c2 = st.columns([4,1])
                if c1.button(f"📁 {f}", key=f"open_{f}"):
                    st.session_state.current_dir = f"{st.session_state.current_dir}/{f}" if st.session_state.current_dir else f
                    st.rerun()
                if c2.button("🗑️", key=f"del_f_{f}"):
                    delete_path(f"{st.session_state.current_dir}/{f}" if st.session_state.current_dir else f)
                    st.rerun()
        
        if items["files"]:
            st.subheader("📄 Tệp tin")
            selected = []
            for file in items["files"]:
                c0, c1, c2, c3, c4 = st.columns([0.5,2,1,1,1])
                if c0.checkbox("", key=f"sel_{file['name']}"):
                    selected.append(f"{st.session_state.current_dir}/{file['name']}" if st.session_state.current_dir else file['name'])
                with c1:
                    st.write(f"📄 {file['name']} ({file['info']['size']/1024:.1f} KB)")
                with c2:
                    st.markdown(f'<a href="data:{file["info"]["type"]};base64,{file["info"]["data"]}" download="{file["name"]}"><button style="background:#0047AB;color:white;border:none;border-radius:20px;padding:5px 12px;">📥</button></a>', unsafe_allow_html=True)
                with c3:
                    if st.button("👁️", key=f"view_{file['name']}"):
                        st.session_state.preview_file = file
                        st.rerun()
                with c4:
                    if st.button("🗑️", key=f"del_{file['name']}"):
                        delete_path(f"{st.session_state.current_dir}/{file['name']}" if st.session_state.current_dir else file['name'])
                        st.rerun()
            if selected and st.button(f"📦 Tải {len(selected)} file (ZIP)"):
                zip_data = download_multiple_files(selected)
                st.download_button("📥 Tải ZIP", zip_data, f"nexus_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip", "application/zip")
        
        with st.expander("📤 Tải lên nhiều file"):
            files = st.file_uploader("Chọn nhiều file", accept_multiple_files=True)
            if files and st.button("Tải lên"):
                total = sum(len(f.getvalue()) for f in files)
                if not is_pro and used + total > limit:
                    st.error(f"⚠️ Vượt quá {limit_gb} GB")
                else:
                    for f in files:
                        path = f"{st.session_state.current_dir}/{f.name}" if st.session_state.current_dir else f.name
                        if path not in st.session_state.data["files"]:
                            st.session_state.data["files"][path] = {
                                "owner": st.session_state.user, "data": base64.b64encode(f.getvalue()).decode(),
                                "size": len(f.getvalue()), "type": mimetypes.guess_type(f.name)[0] or "application/octet-stream",
                                "upload_time": str(datetime.now())
                            }
                    save_data(st.session_state.data)
                    st.toast(f"✅ Đã tải lên {len(files)} file!", icon="✅")
                    st.rerun()
        
        if st.session_state.preview_file:
            st.divider()
            st.subheader(f"🔍 {st.session_state.preview_file['name']}")
            p = st.session_state.preview_file
            if p["info"]["type"].startswith("image/"):
                st.image(f"data:{p['info']['type']};base64,{p['info']['data']}", use_column_width=True)
            elif p["info"]["type"].startswith("text/"):
                try:
                    text = base64.b64decode(p["info"]["data"]).decode("utf-8")
                    st.text_area("Nội dung", text, height=300)
                except:
                    st.warning("Không thể hiển thị")
            else:
                st.info("Không hỗ trợ xem trước")
            if st.button("🔙 Đóng"):
                st.session_state.preview_file = None
                st.rerun()

# ================== CÀI ĐẶT ==================
elif st.session_state.page == "SETTINGS":
    st.header("⚙️ CÀI ĐẶT")
    if st.session_state.guest_mode:
        st.info("👤 Guest không thể thay đổi cài đặt.")
    else:
        user_info = st.session_state.data["users"][st.session_state.user]["info"]
        
        tab1, tab2, tab3, tab4 = st.tabs(["👤 Hồ sơ", "🔐 Bảo mật", "🎁 Nâng cấp", "ℹ️ Hệ thống"])
        
        with tab1:
            st.subheader("Ảnh đại diện")
            col_avatar, col_info = st.columns([1, 2])
            with col_avatar:
                if user_info.get("avatar"):
                    st.markdown(f'<img src="data:image/png;base64,{user_info["avatar"]}" class="avatar-large">', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="text-align:center; font-size:80px;">👤</div>', unsafe_allow_html=True)
                
                avatar_file = st.file_uploader("Chọn ảnh đại diện", type=["png", "jpg", "jpeg", "gif"])
                if avatar_file:
                    if st.button("📸 Cập nhật ảnh"):
                        success, msg = update_avatar(st.session_state.user, avatar_file.getvalue())
                        if success:
                            st.toast(msg, icon="✅")
                            st.rerun()
                        else:
                            st.error(msg)
            
            with col_info:
                new_name = st.text_input("Tên hiển thị", value=user_info.get("name", st.session_state.user))
                if st.button("💾 Đổi tên"):
                    success, msg = change_display_name(st.session_state.user, new_name)
                    if success:
                        st.toast(msg, icon="✅")
                        st.rerun()
                    else:
                        st.error(msg)
                
                new_bio = st.text_area("Giới thiệu bản thân", value=user_info.get("bio", ""), height=100)
                if st.button("📝 Cập nhật giới thiệu"):
                    st.session_state.data["users"][st.session_state.user]["info"]["bio"] = new_bio
                    save_data(st.session_state.data)
                    st.toast("✅ Đã cập nhật giới thiệu!", icon="✅")
            
            st.divider()
            st.write(f"**Link kết bạn:** `{user_info['link']}`")
            st.caption("Sao chép link này và gửi cho bạn bè để kết bạn!")
        
        with tab2:
            st.subheader("Đổi mật khẩu")
            old_pass = st.text_input("Mật khẩu cũ", type="password")
            new_pass = st.text_input("Mật khẩu mới", type="password", placeholder="Ít nhất 6 ký tự")
            confirm_pass = st.text_input("Xác nhận mật khẩu mới", type="password")
            
            if st.button("🔄 Đổi mật khẩu"):
                if not old_pass or not new_pass:
                    st.error("Vui lòng nhập đầy đủ thông tin!")
                elif new_pass != confirm_pass:
                    st.error("Mật khẩu xác nhận không khớp!")
                elif len(new_pass) < 6:
                    st.error("Mật khẩu mới phải có ít nhất 6 ký tự!")
                else:
                    success, msg = change_password(st.session_state.user, old_pass, new_pass)
                    if success:
                        st.success(msg)
                        st.toast(msg, icon="✅")
                    else:
                        st.error(msg)
        
        with tab3:
            code = st.text_input("Mã kích hoạt Pro").upper()
            if st.button("KÍCH HOẠT"):
                found = False
                for c in st.session_state.data["codes"]:
                    if c["code"] == code:
                        if c["expiry"] and datetime.now() > datetime.fromisoformat(c["expiry"]):
                            st.error("Mã đã hết hạn!")
                        elif c["max_uses"] and len(c["used_by"]) >= c["max_uses"]:
                            st.error("Mã đã hết lượt sử dụng!")
                        elif st.session_state.user in c["used_by"]:
                            st.warning("Bạn đã kích hoạt mã này rồi!")
                        else:
                            c["used_by"].append(st.session_state.user)
                            if st.session_state.user not in st.session_state.data["pro_users"]:
                                st.session_state.data["pro_users"].append(st.session_state.user)
                            save_data(st.session_state.data)
                            st.balloons()
                            st.toast("🎉 Chúc mừng! Bạn đã là Pro!", icon="💎")
                            st.rerun()
                        found = True
                        break
                if not found:
                    st.error("Mã không hợp lệ!")
        
        with tab4:
            st.write(f"**Phiên bản:** {CONFIG['VERSION']}")
            st.write(f"**Tác giả:** {CONFIG['CREATOR']}")
            st.write(f"**Ngày tham gia:** {user_info.get('created', 'Không rõ')[:16]}")
            st.write(f"**Hạng:** {'💎 Pro' if is_pro else '🆓 Miễn phí'}")
            if st.button("🧹 Dọn dẹp file cũ"):
                auto_cleanup_files()
                st.toast("✅ Đã dọn dẹp file cũ!", icon="✅")

# ================== ADMIN ==================
elif st.session_state.page == "ADMIN":
    if st.session_state.user != CONFIG["ADMIN_USERNAME"]:
        st.error("⛔ Không có quyền!")
    else:
        st.header("🛠️ ADMIN")
        tab1, tab2, tab3, tab4 = st.tabs(["🎫 Mã Pro", "📢 Thông báo", "👥 Người dùng", "📊 Hệ thống"])
        
        with tab1:
            new_code = st.text_input("Mã mới").upper()
            c1, c2 = st.columns(2)
            with c1:
                has_expiry = st.checkbox("Hạn sử dụng")
                expiry = st.date_input("Ngày hết hạn") if has_expiry else None
            with c2:
                has_limit = st.checkbox("Giới hạn số lần")
                max_uses = st.number_input("Số lần tối đa", min_value=1, value=1) if has_limit else None
            if st.button("TẠO MÃ") and new_code:
                st.session_state.data["codes"].append({"code": new_code, "expiry": str(expiry) if expiry else None, "max_uses": max_uses, "used_by": []})
                save_data(st.session_state.data)
                st.toast(f"✅ Đã tạo mã {new_code}", icon="✅")
            st.subheader("Danh sách mã")
            for c in st.session_state.data["codes"]:
                st.write(f"- `{c['code']}` (Hết hạn: {c['expiry'] or 'Vĩnh viễn'}, Lượt: {len(c['used_by'])}/{c['max_uses'] or '∞'})")
        
        with tab2:
            users = list(st.session_state.data["users"].keys())
            target = st.selectbox("Gửi đến", ["Tất cả"] + users)
            title = st.text_input("Tiêu đề")
            msg = st.text_area("Nội dung")
            if st.button("📤 GỬI THÔNG BÁO"):
                if target == "Tất cả":
                    for u in users:
                        add_notification(u, title, msg, "admin")
                    st.toast(f"✅ Đã gửi đến {len(users)} người dùng!", icon="✅")
                else:
                    add_notification(target, title, msg, "admin")
                    st.toast(f"✅ Đã gửi đến {target}!", icon="✅")
        
        with tab3:
            st.subheader("Danh sách người dùng")
            for u, info in st.session_state.data["users"].items():
                is_pro_user = "💎 PRO" if u in st.session_state.data["pro_users"] else "🆓 FREE"
                st.write(f"- **{info['info'].get('name', u)}** (@{u}) - {is_pro_user}")
        
        with tab4:
            st.write(f"**Số người dùng:** {len(st.session_state.data['users'])}")
            st.write(f"**Số Pro users:** {len(st.session_state.data['pro_users'])}")
            st.write(f"**Số phiên chat:** {len(st.session_state.data['chat_sessions'])}")
            st.write(f"**Số file lưu trữ:** {len(st.session_state.data['files'])}")
            if st.button("🔄 Đồng bộ dữ liệu"):
                st.session_state.data = load_data()
                st.toast("✅ Đã đồng bộ!", icon="🔄")

# ================== THÔNG TIN ==================
elif st.session_state.page == "ABOUT":
    st.markdown(f"""
    <div class='custom-card' style='background:linear-gradient(135deg,#667eea,#764ba2);color:white'>
        <h1 style='text-align:center'>🚀 {CONFIG['NAME']}</h1>
        <p style='text-align:center'><b>Hệ điều hành AI đa năng</b></p>
        <p><b>Phiên bản:</b> {CONFIG['VERSION']}</p>
        <p><b>Tác giả:</b> {CONFIG['CREATOR']}</p>
        <p><b>Ngày phát hành:</b> 2025</p>
        <hr>
        <p style='text-align:center'><i>"Kết nối tri thức, mở ra tương lai"</i></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ✨ TÍNH NĂNG CHÍNH")
    col1, col2 = st.columns(2)
    with col1:
        st.write("✅ **Trò chuyện AI** với NEXUS OS Gateway")
        st.write("✅ **Phân tích file Word** và hình ảnh (OCR)")
        st.write("✅ **Lưu trữ đám mây** với cây thư mục")
        st.write("✅ **Tải lên/xuống nhiều file** cùng lúc")
    with col2:
        st.write("✅ **Lịch sử trò chuyện** không giới hạn")
        st.write("✅ **Tự động dọn dẹp** file cũ")
        st.write("✅ **Nâng cấp Pro** dung lượng không giới hạn")
        st.write("✅ **Kết bạn và thông báo** realtime")
    
    st.markdown("---")
    st.markdown(f"© 2025 {CONFIG['CREATOR']} - Bảo lưu mọi quyền")
    st.markdown(f"**{CONFIG['NAME']}** - Hệ điều hành AI đa năng")
