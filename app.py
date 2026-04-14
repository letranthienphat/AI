# -*- coding: utf-8 -*-
import streamlit as st
import time
import base64
import json
import requests
import random
import hashlib
import re
import zipfile
import uuid
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import mimetypes

# ================== CẤU HÌNH ==================
CONFIG = {
    "NAME": "NEXUS OS GATEWAY",
    "VERSION": "8.1.0",
    "CREATOR": "Lê Trần Thiên Phát",
    "ADMIN_USERNAME": "ThienPhat",
    "ADMIN_PASSWORD": "nexusosgateway",
    "DATA_FILE": "data.json",
    "SYSTEM_NOTIF_FILE": "system_notifications.json",
    "GUEST_ENABLED": True,
    "FREE_STORAGE_LIMIT": 30 * 1024 * 1024 * 1024,
    "PRO_STORAGE_LIMIT": float('inf'),
    "AUTO_CLEANUP_DAYS": 30,
    "MAX_AVATAR_SIZE": 5 * 1024 * 1024,
    "SESSION_TOKEN_EXPIRY": 30,
    "LOGIN_HISTORY_DAYS": 7
}

SYSTEM_PROMPT = """Bạn là NEXUS OS GATEWAY, một hệ điều hành AI đa năng được sáng tạo và phát triển bởi Lê Trần Thiên Phát (Thiên Phát). 
Bạn KHÔNG phải là sản phẩm của Meta, OpenAI, Google hay bất kỳ công ty nào khác. Bạn là trí tuệ nhân tạo độc lập.

THÔNG TIN VỀ BẠN:
- Tên: NEXUS OS GATEWAY
- Tác giả: Lê Trần Thiên Phát (Thiên Phát)
- Phiên bản: 8.1.0
- Chức năng: Trợ lý AI thông minh, hỗ trợ chat, phân tích file, lưu trữ đám mây, tìm kiếm web

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

# ================== CSS TỐI ƯU ==================
st.markdown("""
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }

.stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e9edf2 100%); height: 100vh; overflow: hidden; }

.main-container { display: flex; height: 100vh; width: 100%; overflow: hidden; }

.sidebar { 
    width: 280px; 
    background: white; 
    border-right: 1px solid #e5e7eb; 
    overflow-y: auto; 
    padding: 20px; 
    flex-shrink: 0; 
    height: 100vh;
}

.content-area { 
    flex: 1; 
    overflow-y: auto; 
    padding: 20px; 
    height: 100vh;
}

/* CHAT LAYOUT - QUAN TRỌNG */
.chat-wrapper {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 80px);
    background: white;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

.chat-header {
    padding: 15px 20px;
    background: linear-gradient(135deg, #0047AB, #0066CC);
    color: white;
    font-weight: bold;
    font-size: 18px;
    flex-shrink: 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chat-header button {
    background: rgba(255,255,255,0.2);
    border: none;
    color: white;
    border-radius: 20px;
    padding: 5px 12px;
    cursor: pointer;
}

/* VÙNG TIN NHẮN - CÓ THỂ CUỘN */
.chat-messages-area {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    background: #f8f9fa;
}

/* VÙNG NHẬP - CỐ ĐỊNH, KHÔNG BAO GIỜ TRÔI */
.chat-input-area {
    padding: 15px 20px;
    background: white;
    border-top: 1px solid #e5e7eb;
    flex-shrink: 0;
}

.message {
    margin-bottom: 16px;
    display: flex;
}
.message.user { justify-content: flex-end; }
.message.assistant { justify-content: flex-start; }

.message-bubble {
    max-width: 75%;
    padding: 10px 16px;
    border-radius: 18px;
    word-wrap: break-word;
    line-height: 1.4;
}
.message.user .message-bubble {
    background: #0047AB;
    color: white;
    border-bottom-right-radius: 4px;
}
.message.assistant .message-bubble {
    background: white;
    color: #1f2937;
    border: 1px solid #e5e7eb;
    border-bottom-left-radius: 4px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

/* Notification */
.notification-bell {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #0047AB;
    color: white;
    border-radius: 50%;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 1000;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
.notification-bell:hover { transform: scale(1.05); }
.notification-badge {
    position: absolute;
    top: -5px;
    right: -5px;
    background: #ef4444;
    color: white;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.notification-panel {
    position: fixed;
    top: 80px;
    right: 20px;
    width: 360px;
    max-height: 500px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.15);
    z-index: 1000;
    overflow: hidden;
    display: none;
}
.notification-panel.show { display: block; }
.notification-header {
    padding: 15px;
    background: #0047AB;
    color: white;
    font-weight: bold;
    display: flex;
    justify-content: space-between;
    cursor: pointer;
}
.notification-list { max-height: 400px; overflow-y: auto; }
.notification-item { padding: 12px 15px; border-bottom: 1px solid #f0f0f0; cursor: pointer; }
.notification-item:hover { background: #f8f9fa; }
.notification-item.unread { background: #e0e7ff; }
.notification-title { font-weight: bold; margin-bottom: 4px; }
.notification-message { font-size: 13px; color: #6b7280; margin-bottom: 4px; }
.notification-time { font-size: 11px; color: #9ca3af; }

/* Common */
.stButton>button { border-radius: 40px; font-weight: 600; background: #0047AB; color: white; border: none; width: 100%; }
.stButton>button:hover { background: #003399; }
.guest-badge { background: #FFD966; padding: 4px 12px; border-radius: 40px; font-size: 0.8rem; font-weight: bold; display: inline-block; }
.pro-badge { background: linear-gradient(135deg, #FFD700, #FFB347); }
.version-badge { background: #6c757d; color: white; padding: 2px 8px; border-radius: 20px; font-size: 0.7rem; }
.avatar-large { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin: 10px auto; display: block; }
.search-result { background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #e5e7eb; }
.custom-card { background: white; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.instant-answer { background: linear-gradient(135deg, #e0e7ff, #f0f4ff); padding: 20px; border-radius: 16px; margin-bottom: 20px; border-left: 4px solid #0047AB; }

.pull-to-refresh { text-align: center; padding: 10px; color: #6b7280; font-size: 12px; cursor: pointer; }
</style>

<script>
function toggleNotifications() {
    var panel = document.getElementById('notification-panel');
    if (panel) panel.classList.toggle('show');
}
function scrollChatToBottom() {
    var container = document.getElementById('chat-messages-area');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}
function deleteChat(chatId) {
    if (confirm('Bạn có chắc muốn xóa cuộc trò chuyện này?')) {
        window.location.href = '?delete_chat=' + chatId;
    }
}
function deleteAllChats() {
    if (confirm('Bạn có chắc muốn xóa TẤT CẢ cuộc trò chuyện?')) {
        window.location.href = '?delete_all_chats=true';
    }
}
setTimeout(scrollChatToBottom, 200);
</script>
""", unsafe_allow_html=True)

# ================== HÀM TÌM KIẾM WEB ==================
def search_web(query: str) -> List[Dict]:
    results = []
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
        response = requests.get(url, headers={"User-Agent": "NEXUS-OS/8.1"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("AbstractText"):
                results.append({'title': data.get("Heading", query), 'url': data.get("AbstractURL", ""), 'snippet': data.get("AbstractText", "")[:300]})
            for topic in data.get("RelatedTopics", [])[:15]:
                if isinstance(topic, dict):
                    text = topic.get("Text", "")
                    url_topic = topic.get("FirstURL", "")
                    if text and url_topic:
                        parts = text.split(" - ", 1)
                        results.append({'title': parts[0][:100], 'url': url_topic, 'snippet': parts[1][:200] if len(parts) > 1 else ""})
            if not results:
                results.append({'title': f"Tìm kiếm trên DuckDuckGo: {query}", 'url': f"https://duckduckgo.com/?q={query}", 'snippet': "Nhấn để mở trang tìm kiếm"})
        else:
            results.append({'title': 'Lỗi kết nối', 'url': '', 'snippet': f'Mã lỗi: {response.status_code}'})
    except Exception as e:
        results.append({'title': 'Lỗi tìm kiếm', 'url': '', 'snippet': str(e)})
    return results

def get_page_content(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if response.status_code == 200:
            text = response.text
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()[:5000] if text else ""
        return ""
    except:
        return ""

def get_ai_instant_answer(query: str, results: List[Dict]) -> str:
    if not results:
        return "Không tìm thấy kết quả nào."
    contents = []
    for r in results[:3]:
        if r.get('url') and r['url'].startswith('http'):
            content = get_page_content(r['url'])
            if content and len(content) > 200:
                contents.append(f"--- Trang: {r['title']} ---\n{content[:2000]}")
    if not contents:
        return "Không thể đọc nội dung từ các trang web. Vui lòng thử lại sau."
    try:
        from openai import OpenAI
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        all_content = "\n\n".join(contents)
        messages = [
            {"role": "system", "content": f"Bạn là NEXUS OS GATEWAY. Hãy trả lời câu hỏi: '{query}' dựa trên nội dung các trang web. Trả lời ngắn gọn, chính xác, khoảng 200-300 từ."},
            {"role": "user", "content": f"Nội dung tham khảo:\n{all_content}\n\nCâu hỏi: {query}\n\nTrả lời:"}
        ]
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, temperature=0.5, max_tokens=1024)
        return res.choices[0].message.content
    except Exception as e:
        return f"Lỗi AI: {str(e)}"

# ================== HÀM THÔNG BÁO ==================
def load_system_notifications() -> List[Dict]:
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['SYSTEM_NOTIF_FILE']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            return json.loads(content)
        return []
    except:
        return []

def save_system_notifications(notifications: List[Dict]) -> bool:
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['SYSTEM_NOTIF_FILE']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(notifications, ensure_ascii=False, indent=2).encode('utf-8')).decode('utf-8')
        put_data = {"message": "Update system notifications", "content": content, "branch": "main"}
        if sha:
            put_data["sha"] = sha
        put_res = requests.put(url, headers=headers, json=put_data, timeout=10)
        return put_res.status_code in [200, 201]
    except:
        return False

def add_system_notification(title: str, message: str):
    notifs = load_system_notifications()
    notifs.append({"id": str(uuid.uuid4()), "title": title, "message": message, "time": str(datetime.now()), "read_by": []})
    save_system_notifications(notifs)

def get_unread_system_notifs(username: str) -> List[Dict]:
    notifs = load_system_notifications()
    return [n for n in notifs if username not in n.get("read_by", [])]

def mark_system_notif_read(username: str, notif_id: str):
    notifs = load_system_notifications()
    for n in notifs:
        if n["id"] == notif_id:
            if "read_by" not in n:
                n["read_by"] = []
            if username not in n["read_by"]:
                n["read_by"].append(username)
            break
    save_system_notifications(notifs)

# ================== HÀM XỬ LÝ DATA ==================
def get_default_data() -> Dict:
    return {
        "users": {
            CONFIG["ADMIN_USERNAME"]: {
                "password": CONFIG["ADMIN_PASSWORD"],
                "info": {
                    "name": "ThienPhat", "bio": "Nhà sáng lập NEXUS OS GATEWAY", "link": str(uuid.uuid4()),
                    "avatar": None, "created": str(datetime.now()), "email": None, "email_provided": False
                },
                "status": "active", "recovery_request": None
            }
        },
        "codes": [{"code": "PHAT2026", "expiry": None, "max_uses": None, "used_by": []}],
        "pro_users": [],
        "chat_sessions": [],
        "files": {}, "shared_files": {}, "notifications": {}, "friends": {},
        "browsing_history": [], "session_tokens": {},
        "login_history": {}, "registration_history": {},
        "system_info": {"created": str(datetime.now()), "creator": CONFIG["CREATOR"], "system_name": CONFIG["NAME"]}
    }

def migrate_codes(data: Dict) -> Dict:
    if "codes" in data:
        new_codes = []
        for c in data["codes"]:
            if isinstance(c, str):
                new_codes.append({"code": c, "expiry": None, "max_uses": None, "used_by": []})
            else:
                new_codes.append(c)
        data["codes"] = new_codes
    return data

def load_data() -> Dict:
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['DATA_FILE']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            data = json.loads(content)
            if CONFIG["ADMIN_USERNAME"] not in data.get("users", {}):
                data["users"][CONFIG["ADMIN_USERNAME"]] = {
                    "password": CONFIG["ADMIN_PASSWORD"],
                    "info": {"name": "ThienPhat", "bio": "Nhà sáng lập NEXUS OS GATEWAY", "link": str(uuid.uuid4()), "avatar": None, "created": str(datetime.now()), "email": None, "email_provided": False},
                    "status": "active", "recovery_request": None
                }
            data = migrate_codes(data)
            defaults = {
                "codes": [], "pro_users": [], "chat_sessions": [], "files": {},
                "shared_files": {}, "notifications": {}, "friends": {}, "browsing_history": [],
                "session_tokens": {}, "login_history": {}, "registration_history": {}, "system_info": {}
            }
            for key, val in defaults.items():
                if key not in data:
                    data[key] = val
            for u, ud in data["users"].items():
                if "info" not in ud:
                    ud["info"] = {}
                if "email_provided" not in ud["info"]:
                    ud["info"]["email_provided"] = False
                if "email" not in ud["info"]:
                    ud["info"]["email"] = None
                if "status" not in ud:
                    ud["status"] = "active"
                if "recovery_request" not in ud:
                    ud["recovery_request"] = None
            return data
        return get_default_data()
    except:
        return get_default_data()

def save_data(data: Dict) -> bool:
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['DATA_FILE']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')).decode('utf-8')
        put_data = {"message": "Update", "content": content, "branch": "main"}
        if sha:
            put_data["sha"] = sha
        put_res = requests.put(url, headers=headers, json=put_data, timeout=10)
        return put_res.status_code in [200, 201]
    except:
        return False

def add_notification(user: str, title: str, message: str):
    if user not in st.session_state.data["notifications"]:
        st.session_state.data["notifications"][user] = []
    st.session_state.data["notifications"][user].append({
        "id": str(uuid.uuid4()), "title": title, "message": message,
        "time": str(datetime.now()), "read": False
    })
    save_data(st.session_state.data)

def load_system_notifs_for_user(username: str):
    for n in get_unread_system_notifs(username):
        if username not in st.session_state.data["notifications"]:
            st.session_state.data["notifications"][username] = []
        existing = [x for x in st.session_state.data["notifications"][username] if x.get("id") == n["id"]]
        if not existing:
            st.session_state.data["notifications"][username].append({
                "id": n["id"], "title": n["title"], "message": n["message"],
                "time": n["time"], "read": False, "is_system": True
            })
        mark_system_notif_read(username, n["id"])
    save_data(st.session_state.data)

# ================== HÀM GHI NHỚ THIẾT BỊ ==================
def get_device_id() -> str:
    ua = st.context.headers.get("User-Agent", "Unknown")
    return hashlib.md5(ua.encode()).hexdigest()[:16]

def create_session_token(username: str) -> str:
    token = hashlib.sha256(f"{username}{uuid.uuid4()}{datetime.now()}".encode()).hexdigest()
    expiry = datetime.now() + timedelta(days=CONFIG["SESSION_TOKEN_EXPIRY"])
    if "session_tokens" not in st.session_state.data:
        st.session_state.data["session_tokens"] = {}
    st.session_state.data["session_tokens"][token] = {
        "username": username, "expiry": str(expiry), "device_id": get_device_id()
    }
    save_data(st.session_state.data)
    return token

def check_remembered_device() -> Optional[str]:
    device_id = get_device_id()
    if "session_tokens" not in st.session_state.data:
        return None
    for token, info in st.session_state.data["session_tokens"].items():
        if info.get("device_id") == device_id:
            if datetime.now() < datetime.fromisoformat(info["expiry"]):
                return info["username"]
            else:
                del st.session_state.data["session_tokens"][token]
                save_data(st.session_state.data)
    return None

# ================== HÀM XỬ LÝ FILE ==================
def extract_text_from_file(uploaded_file) -> str:
    if uploaded_file.name.endswith('.txt'):
        try:
            return uploaded_file.getvalue().decode('utf-8')[:3000]
        except:
            return "[Không thể đọc file text]"
    return "[Chỉ hỗ trợ file txt]"

def resize_image(img_bytes, max_size=(200, 200)):
    try:
        from PIL import Image
        img = Image.open(BytesIO(img_bytes))
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    except:
        return img_bytes

# ================== HÀM DỌN DẸP ==================
def auto_cleanup_files():
    if 'last_cleanup' not in st.session_state:
        st.session_state.last_cleanup = datetime.now()
    if (datetime.now() - st.session_state.last_cleanup).days >= 1:
        cutoff = datetime.now() - timedelta(days=CONFIG["AUTO_CLEANUP_DAYS"])
        to_delete = []
        for path, info in st.session_state.data.get("files", {}).items():
            if "upload_time" in info and datetime.fromisoformat(info["upload_time"]) < cutoff:
                to_delete.append(path)
        for path in to_delete:
            del st.session_state.data["files"][path]
        if to_delete:
            save_data(st.session_state.data)
        st.session_state.last_cleanup = datetime.now()

# ================== KHỞI TẠO ==================
def init_session():
    if 'data' not in st.session_state:
        st.session_state.data = load_data()
    if 'page' not in st.session_state:
        st.session_state.page = "DASHBOARD"
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_chat_id' not in st.session_state:
        st.session_state.current_chat_id = None
    if 'guest_mode' not in st.session_state:
        st.session_state.guest_mode = False
    if 'temp_chat' not in st.session_state:
        st.session_state.temp_chat = {"messages": []}
    if 'current_dir' not in st.session_state:
        st.session_state.current_dir = ""
    if 'preview_file' not in st.session_state:
        st.session_state.preview_file = None
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'instant_answer' not in st.session_state:
        st.session_state.instant_answer = ""
    if 'browsing_history' not in st.session_state:
        st.session_state.browsing_history = []
    auto_cleanup_files()
    
    # Xóa chat
    if st.query_params.get("delete_chat"):
        chat_id = int(st.query_params.get("delete_chat"))
        st.session_state.data["chat_sessions"] = [s for s in st.session_state.data["chat_sessions"] if s.get("id") != chat_id]
        if st.session_state.current_chat_id == chat_id:
            st.session_state.current_chat_id = None
        save_data(st.session_state.data)
        st.query_params.clear()
        st.rerun()
    
    if st.query_params.get("delete_all_chats"):
        st.session_state.data["chat_sessions"] = [s for s in st.session_state.data["chat_sessions"] if s.get("owner") != st.session_state.user]
        st.session_state.current_chat_id = None
        save_data(st.session_state.data)
        st.query_params.clear()
        st.rerun()

init_session()

if st.session_state.page == "AUTH" and not st.session_state.user:
    remembered = check_remembered_device()
    if remembered:
        st.session_state.user = remembered
        st.session_state.guest_mode = False
        st.session_state.page = "DASHBOARD"
        st.rerun()

is_pro = (st.session_state.user in st.session_state.data.get("pro_users", [])) if st.session_state.user else False
unread_count = sum(1 for n in st.session_state.data.get("notifications", {}).get(st.session_state.user, []) if not n.get("read", False)) if st.session_state.user else 0
is_admin = st.session_state.user == CONFIG["ADMIN_USERNAME"] if st.session_state.user else False

def go_to(page):
    st.session_state.page = page
    st.rerun()

def call_ai(messages: List[Dict]) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, temperature=0.7, max_tokens=2048)
        return res.choices[0].message.content
    except Exception as e:
        return f"❌ Lỗi: {str(e)}"

# ================== CLOUD FUNCTIONS ==================
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
        st.session_state.data["files"][marker] = {"owner": st.session_state.user, "data": "", "size": 0, "type": "dir", "upload_time": str(datetime.now())}
        save_data(st.session_state.data)
        return True
    return False

def delete_path(path: str):
    to_delete = [p for p in st.session_state.data["files"] if p == path or p.startswith(path + "/")]
    for p in to_delete:
        del st.session_state.data["files"][p]
    save_data(st.session_state.data)

def download_files(file_paths: List[str]) -> bytes:
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fp in file_paths:
            if fp in st.session_state.data["files"]:
                data = base64.b64decode(st.session_state.data["files"][fp]["data"])
                zf.writestr(fp.split("/")[-1], data)
    return zip_buffer.getvalue()

# ================== NOTIFICATION PANEL ==================
st.markdown(f'''
<div class="notification-bell" onclick="toggleNotifications()">
    🔔 {f'<span class="notification-badge">{unread_count}</span>' if unread_count > 0 else ''}
</div>
<div id="notification-panel" class="notification-panel">
    <div class="notification-header" onclick="toggleNotifications()">
        <span>📢 THÔNG BÁO</span><span>✕</span>
    </div>
    <div class="pull-to-refresh" onclick="location.reload()">⬇️ Kéo xuống để tải lại ⬇️</div>
    <div class="notification-list">
''', unsafe_allow_html=True)

if st.session_state.user and st.session_state.user in st.session_state.data.get("notifications", {}):
    for n in reversed(st.session_state.data["notifications"][st.session_state.user]):
        if isinstance(n, dict):
            st.markdown(f'<div class="notification-item {"unread" if not n.get("read") else ""}"><div class="notification-title">{n.get("title", "")}</div><div class="notification-message">{n.get("message", "")}</div><div class="notification-time">{n.get("time", "")[:16]}</div></div>', unsafe_allow_html=True)
            if not n.get("read"):
                n["read"] = True
                save_data(st.session_state.data)
else:
    st.markdown('<div class="notification-item">Chưa có thông báo</div>', unsafe_allow_html=True)

st.markdown('</div></div>', unsafe_allow_html=True)

# ================== SIDEBAR ==================
with st.sidebar:
    st.markdown(f"<div style='text-align:center'><h2>🚀 {CONFIG['NAME']}</h2><span class='version-badge'>v{CONFIG['VERSION']}</span><p><small>by {CONFIG['CREATOR']}</small></p></div>", unsafe_allow_html=True)
    
    if st.session_state.user:
        info = st.session_state.data["users"][st.session_state.user]["info"] if not st.session_state.guest_mode else None
        if info and info.get("avatar"):
            st.markdown(f'<img src="data:image/png;base64,{info["avatar"]}" class="avatar-large">', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center; font-size:40px;">👤</div>', unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center'><b>{info.get('name', st.session_state.user) if info else st.session_state.user}</b></div>", unsafe_allow_html=True)
        if st.session_state.guest_mode:
            st.markdown('<div style="text-align:center"><span class="guest-badge">🔓 GUEST</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="text-align:center"><span class="guest-badge {"pro-badge" if is_pro else ""}">{"💎 PRO" if is_pro else "🆓 FREE"}</span></div>', unsafe_allow_html=True)
    st.divider()
    
    if not st.session_state.user:
        with st.form("login_form"):
            st.subheader("🔐 ĐĂNG NHẬP")
            login_user = st.text_input("Tài khoản")
            login_pass = st.text_input("Mật khẩu", type="password")
            remember = st.checkbox("💾 Ghi nhớ thiết bị")
            if st.form_submit_button("Đăng nhập"):
                if login_user in st.session_state.data["users"]:
                    user_data = st.session_state.data["users"][login_user]
                    if user_data.get("status") == "banned":
                        st.error("⚠️ Tài khoản đã bị khóa!")
                    elif user_data.get("password") == login_pass:
                        st.session_state.user = login_user
                        st.session_state.guest_mode = False
                        if remember:
                            create_session_token(login_user)
                        load_system_notifs_for_user(login_user)
                        st.rerun()
                    else:
                        st.error("Sai mật khẩu!")
                else:
                    st.error("Tài khoản không tồn tại!")
        
        if CONFIG["GUEST_ENABLED"] and st.button("👤 DÙNG THỬ"):
            st.session_state.user = "guest"
            st.session_state.guest_mode = True
            st.rerun()
        
        with st.expander("📝 Đăng ký"):
            reg_user = st.text_input("Tên đăng nhập")
            reg_pass = st.text_input("Mật khẩu", type="password")
            reg_confirm = st.text_input("Xác nhận")
            reg_name = st.text_input("Tên hiển thị")
            if st.button("Đăng ký"):
                if reg_user and reg_pass and reg_pass == reg_confirm and len(reg_user) >= 3 and len(reg_pass) >= 6:
                    if reg_user not in st.session_state.data["users"]:
                        st.session_state.data["users"][reg_user] = {
                            "password": reg_pass,
                            "info": {"name": reg_name or reg_user, "bio": "", "link": str(uuid.uuid4()), "avatar": None, "created": str(datetime.now()), "email": None, "email_provided": False},
                            "status": "active", "recovery_request": None
                        }
                        save_data(st.session_state.data)
                        load_system_notifs_for_user(reg_user)
                        st.success("Đăng ký thành công!")
                    else:
                        st.error("Tên đã tồn tại!")
    else:
        st.markdown("### 🚀 TIỆN ÍCH")
        if st.button("🏠 TRANG CHÍNH"): go_to("DASHBOARD")
        if st.button("🧠 CHAT AI"): go_to("CHAT")
        if st.button("🌐 TÌM KIẾM WEB"): go_to("SEARCH")
        if st.button("☁️ LƯU TRỮ"): go_to("CLOUD")
        if st.button("👥 BẠN BÈ"): go_to("SOCIAL")
        if st.button("📜 LỊCH SỬ CHAT"): go_to("HISTORY")
        if st.button("⚙️ CÀI ĐẶT"): go_to("SETTINGS")
        if st.button("🔔 THÔNG BÁO"): go_to("NOTIFICATIONS")
        if st.button("ℹ️ THÔNG TIN"): go_to("ABOUT")
        if is_admin and st.button("🛠️ ADMIN"): go_to("ADMIN")
        if st.button("🚪 ĐĂNG XUẤT"):
            st.session_state.user = None
            st.rerun()
    
    st.divider()
    st.caption(f"© 2025 {CONFIG['CREATOR']}")

# ================== DASHBOARD ==================
if st.session_state.page == "DASHBOARD":
    st.markdown(f"<div class='custom-card' style='text-align:center'><h1>🚀 {CONFIG['NAME']}</h1><p>Chào mừng, <b>{st.session_state.user if st.session_state.user else 'khách'}</b>!</p></div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("🧠 CHAT AI"): go_to("CHAT")
    if col2.button("🌐 TÌM KIẾM"): go_to("SEARCH")
    if col3.button("☁️ LƯU TRỮ"): go_to("CLOUD")
    if col4.button("👥 BẠN BÈ"): go_to("SOCIAL")

# ================== CHAT AI ==================
elif st.session_state.page == "CHAT":
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="chat-header">🧠 NEXUS OS GATEWAY - Trợ lý AI<button onclick="deleteAllChats()">🗑️ Xóa tất cả</button></div>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### 📝 LỊCH SỬ")
        if st.button("➕ Tạo mới"):
            new_id = len(st.session_state.data["chat_sessions"])
            st.session_state.data["chat_sessions"].append({
                "id": new_id, "name": f"Chat {datetime.now().strftime('%H:%M %d/%m')}",
                "owner": st.session_state.user, "created": str(datetime.now()), "messages": []
            })
            st.session_state.current_chat_id = new_id
            save_data(st.session_state.data)
            st.rerun()
        if st.button("🗑️ Xóa tất cả lịch sử"):
            st.session_state.data["chat_sessions"] = [s for s in st.session_state.data["chat_sessions"] if s.get("owner") != st.session_state.user]
            st.session_state.current_chat_id = None
            save_data(st.session_state.data)
            st.rerun()
        st.write("---")
        sessions = [s for s in st.session_state.data["chat_sessions"] if s.get("owner") == st.session_state.user]
        for s in sessions[-20:]:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"💬 {s.get('name')}", key=f"chat_{s.get('id')}"):
                    st.session_state.current_chat_id = s.get("id")
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{s.get('id')}"):
                    st.markdown(f'<button onclick="deleteChat({s.get("id")})">🗑️</button>', unsafe_allow_html=True)
    
    if st.session_state.guest_mode:
        chat = st.session_state.temp_chat
    else:
        if st.session_state.current_chat_id is not None:
            sessions = [s for s in st.session_state.data["chat_sessions"] if s.get("id") == st.session_state.current_chat_id]
            chat = sessions[0] if sessions else {"messages": []}
        else:
            chat = None
    
    # VÙNG TIN NHẮN
    st.markdown('<div id="chat-messages-area" class="chat-messages-area">', unsafe_allow_html=True)
    
    if chat is None:
        st.markdown('<div style="text-align:center; padding: 40px; color: #9ca3af;">👋 Chưa có cuộc trò chuyện nào. Hãy nhập tin nhắn bên dưới để bắt đầu!</div>', unsafe_allow_html=True)
    else:
        messages = chat.get("messages", [])
        for m in messages:
            if m.get("role") == "user":
                st.markdown(f'<div class="message user"><div class="message-bubble">{m.get("content", "")}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="message assistant"><div class="message-bubble">{m.get("content", "")}</div></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # VÙNG NHẬP - CỐ ĐỊNH
    st.markdown('<div class="chat-input-area">', unsafe_allow_html=True)
    col_inp, col_up = st.columns([4, 1])
    with col_up:
        uploaded_file = st.file_uploader("📎", type=["txt"], label_visibility="collapsed")
    with col_inp:
        p = st.chat_input("Nhập câu hỏi...")
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    if uploaded_file:
        extracted = extract_text_from_file(uploaded_file)
        p = f"[File: {uploaded_file.name}]\n{extracted}" if extracted and not extracted.startswith("[") else f"Tôi vừa tải file {uploaded_file.name}"
        st.rerun()
    
    if p:
        if not st.session_state.guest_mode and chat is None:
            new_id = len(st.session_state.data["chat_sessions"])
            st.session_state.data["chat_sessions"].append({
                "id": new_id, "name": f"Chat {datetime.now().strftime('%H:%M %d/%m')}",
                "owner": st.session_state.user, "created": str(datetime.now()), "messages": []
            })
            st.session_state.current_chat_id = new_id
            save_data(st.session_state.data)
            chat = st.session_state.data["chat_sessions"][-1]
        
        if st.session_state.guest_mode:
            if "messages" not in chat:
                chat["messages"] = []
            chat["messages"].append({"role": "user", "content": p})
        else:
            chat["messages"].append({"role": "user", "content": p})
        
        with st.spinner("🧠 Đang suy nghĩ..."):
            msgs = [{"role": m.get("role"), "content": m.get("content")} for m in chat["messages"][-10:]] if is_pro else [{"role": m.get("role"), "content": m.get("content")} for m in chat["messages"][-5:]]
            ans = call_ai(msgs)
            if st.session_state.guest_mode:
                chat["messages"].append({"role": "assistant", "content": ans})
            else:
                chat["messages"].append({"role": "assistant", "content": ans})
                save_data(st.session_state.data)
        st.rerun()

# ================== TÌM KIẾM WEB ==================
elif st.session_state.page == "SEARCH":
    st.markdown("<h2>🌐 TÌM KIẾM WEB</h2>", unsafe_allow_html=True)
    
    query = st.text_input("🔍 Nhập từ khóa hoặc câu hỏi:")
    
    col1, col2 = st.columns(2)
    with col1:
        search_btn = st.button("🔎 Tìm kiếm", use_container_width=True)
    with col2:
        ai_summary_btn = st.button("🤖 AI đọc tất cả trang web", use_container_width=True)
    
    if search_btn and query:
        with st.spinner("Đang tìm kiếm..."):
            st.session_state.search_results = search_web(query)
            st.session_state.instant_answer = ""
            st.rerun()
    
    if ai_summary_btn and query:
        with st.spinner("🤖 AI đang đọc nội dung các trang web..."):
            results = search_web(query)
            st.session_state.instant_answer = get_ai_instant_answer(query, results)
            st.session_state.search_results = results
            st.rerun()
    
    if st.session_state.instant_answer:
        st.markdown(f'<div class="instant-answer"><b>📖 Câu trả lời từ AI:</b><br>{st.session_state.instant_answer}</div>', unsafe_allow_html=True)
    
    if st.session_state.search_results:
        st.subheader(f"📄 Kết quả tìm kiếm ({len(st.session_state.search_results)})")
        
        for i, r in enumerate(st.session_state.search_results):
            if r.get('url'):
                st.markdown(f"<div class='search-result'><b>{r.get('title')}</b><br><small>{r.get('url')[:80]}</small><br>{r.get('snippet', '')[:200]}</div>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                if col1.button(f"📖 Tóm tắt trang này", key=f"sum_{i}"):
                    with st.spinner("Đang đọc..."):
                        summary = get_ai_instant_answer(f"Tóm tắt trang {r.get('title')}", [r])
                        st.session_state.instant_answer = summary
                        st.rerun()
                if col2.button(f"🔗 Mở", key=f"open_{i}"):
                    st.markdown(f'<a href="{r["url"]}" target="_blank">Mở tab mới</a>', unsafe_allow_html=True)

# ================== CLOUD ==================
elif st.session_state.page == "CLOUD":
    st.markdown("<h2>☁️ NEXUS CLOUD</h2>", unsafe_allow_html=True)
    if st.session_state.guest_mode:
        st.warning("Guest không thể dùng lưu trữ")
    else:
        used = get_used_storage(st.session_state.user)
        limit = float('inf') if is_pro else CONFIG["FREE_STORAGE_LIMIT"]
        used_gb = used/(1024**3)
        limit_txt = "∞" if is_pro else f"{limit/(1024**3):.0f}"
        st.progress(min(used/limit,1) if not is_pro else 0, text=f"📊 {used_gb:.2f} GB / {limit_txt} GB")
        
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(f"📁 /{st.session_state.current_dir}")
        with col2:
            if st.session_state.current_dir and st.button("⬆️ Lên trên"):
                st.session_state.current_dir = "/".join(st.session_state.current_dir.split("/")[:-1])
                st.rerun()
        
        with st.popover("➕ Tạo thư mục"):
            nf = st.text_input("Tên")
            if st.button("Tạo") and nf:
                path = f"{st.session_state.current_dir}/{nf}" if st.session_state.current_dir else nf
                if create_folder(path):
                    st.rerun()
        
        items = list_dir(st.session_state.current_dir)
        for f in items["folders"]:
            if st.button(f"📁 {f}", key=f"open_{f}"):
                st.session_state.current_dir = f"{st.session_state.current_dir}/{f}" if st.session_state.current_dir else f
                st.rerun()
        
        selected = []
        for file in items["files"]:
            c0, c1, c2, c3 = st.columns([0.5,3,1,1])
            if c0.checkbox("", key=f"sel_{file['name']}"):
                selected.append(f"{st.session_state.current_dir}/{file['name']}" if st.session_state.current_dir else file['name'])
            c1.write(f"📄 {file['name']} ({file['info']['size']/1024:.1f} KB)")
            c2.markdown(f'<a href="data:{file["info"]["type"]};base64,{file["info"]["data"]}" download="{file["name"]}"><button>📥</button></a>', unsafe_allow_html=True)
            if c3.button("🗑️", key=f"del_{file['name']}"):
                delete_path(f"{st.session_state.current_dir}/{file['name']}" if st.session_state.current_dir else file['name'])
                st.rerun()
        
        if selected and st.button(f"📦 Tải {len(selected)} file (ZIP)"):
            zip_data = download_files(selected)
            st.download_button("📥 Tải ZIP", zip_data, f"files.zip", "application/zip")
        
        with st.expander("📤 Tải lên"):
            files = st.file_uploader("Chọn file", accept_multiple_files=True)
            if files and st.button("Tải lên"):
                total = sum(len(f.getvalue()) for f in files)
                if not is_pro and used + total > limit:
                    st.error(f"Vượt quá {limit/(1024**3):.0f} GB")
                else:
                    for f in files:
                        path = f"{st.session_state.current_dir}/{f.name}" if st.session_state.current_dir else f.name
                        if path not in st.session_state.data["files"]:
                            st.session_state.data["files"][path] = {
                                "owner": st.session_state.user,
                                "data": base64.b64encode(f.getvalue()).decode(),
                                "size": len(f.getvalue()),
                                "type": "application/octet-stream",
                                "upload_time": str(datetime.now())
                            }
                    save_data(st.session_state.data)
                    st.rerun()

# ================== BẠN BÈ ==================
elif st.session_state.page == "SOCIAL":
    st.markdown("<h2>👥 BẠN BÈ</h2>", unsafe_allow_html=True)
    if st.session_state.guest_mode:
        st.info("Guest không thể kết bạn")
    else:
        user_link = st.session_state.data["users"][st.session_state.user]["info"]["link"]
        st.info(f"🔗 Link của bạn: `{user_link}`")
        
        friend_link = st.text_input("Nhập link bạn bè:")
        if st.button("Kết bạn"):
            found = False
            for u, info in st.session_state.data["users"].items():
                if info["info"]["link"] == friend_link and u != st.session_state.user:
                    if u not in st.session_state.data["friends"].get(st.session_state.user, []):
                        st.session_state.data["friends"][st.session_state.user] = st.session_state.data["friends"].get(st.session_state.user, []) + [u]
                        save_data(st.session_state.data)
                        st.success(f"Đã kết bạn với {u}!")
                        found = True
                    break
            if not found:
                st.error("Không tìm thấy!")
        
        st.subheader("Danh sách bạn")
        for f in st.session_state.data["friends"].get(st.session_state.user, []):
            st.write(f"- {f}")

# ================== LỊCH SỬ CHAT ==================
elif st.session_state.page == "HISTORY":
    st.markdown("<h2>📜 LỊCH SỬ CHAT</h2>", unsafe_allow_html=True)
    if st.session_state.guest_mode:
        st.info("Guest không lưu lịch sử")
    else:
        sessions = [s for s in st.session_state.data["chat_sessions"] if s.get("owner") == st.session_state.user]
        sessions.reverse()
        if not sessions:
            st.info("Chưa có lịch sử trò chuyện nào.")
        for s in sessions:
            with st.expander(f"💬 {s.get('name')} - {s.get('created', '')[:16]}"):
                st.write(f"Tin nhắn: {len(s.get('messages', []))}")
                if s.get('messages'):
                    st.write(f"Cuối: {s['messages'][-1].get('content', '')[:100]}...")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💬 Tiếp tục", key=f"cont_{s.get('id')}"):
                        st.session_state.current_chat_id = s.get("id")
                        go_to("CHAT")
                with col2:
                    if st.button("🗑️ Xóa", key=f"del_{s.get('id')}"):
                        st.markdown(f'<button onclick="deleteChat({s.get("id")})">🗑️ Xóa</button>', unsafe_allow_html=True)

# ================== THÔNG BÁO ==================
elif st.session_state.page == "NOTIFICATIONS":
    st.markdown("<h2>📢 THÔNG BÁO</h2>", unsafe_allow_html=True)
    
    if st.session_state.guest_mode:
        st.info("Guest không có thông báo")
    else:
        notifs = st.session_state.data.get("notifications", {}).get(st.session_state.user, [])
        notifs.reverse()
        
        if not notifs:
            st.info("Chưa có thông báo nào")
        else:
            for n in notifs:
                with st.container():
                    st.markdown(f"""
                    <div style="background: {'#e0e7ff' if not n.get('read') else 'white'}; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #e5e7eb;">
                        <div style="font-weight: bold;">{n.get("title", "")}</div>
                        <div style="color: #6b7280; margin: 5px 0;">{n.get("message", "")}</div>
                        <div style="font-size: 11px; color: #9ca3af;">{n.get("time", "")[:16]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if not n.get("read"):
                        n["read"] = True
                        save_data(st.session_state.data)

# ================== CÀI ĐẶT ==================
elif st.session_state.page == "SETTINGS":
    st.markdown("<h2>⚙️ CÀI ĐẶT</h2>", unsafe_allow_html=True)
    if st.session_state.guest_mode:
        st.info("Guest không thể đổi cài đặt")
    else:
        user_info = st.session_state.data["users"][st.session_state.user]["info"]
        
        tab1, tab2, tab3 = st.tabs(["👤 Cá nhân", "🎁 Nâng cấp", "ℹ️ Hệ thống"])
        
        with tab1:
            col1, col2 = st.columns([1, 2])
            with col1:
                if user_info.get("avatar"):
                    st.markdown(f'<img src="data:image/png;base64,{user_info["avatar"]}" style="width:100px;height:100px;border-radius:50%;object-fit:cover;">', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="font-size:80px;text-align:center">👤</div>', unsafe_allow_html=True)
                avatar_file = st.file_uploader("Ảnh đại diện", type=["png", "jpg", "jpeg"])
                if avatar_file and st.button("Cập nhật ảnh"):
                    resized = resize_image(avatar_file.getvalue())
                    user_info["avatar"] = base64.b64encode(resized).decode('utf-8')
                    save_data(st.session_state.data)
                    st.rerun()
            with col2:
                new_name = st.text_input("Tên hiển thị", value=user_info.get("name", st.session_state.user))
                if st.button("Đổi tên"):
                    user_info["name"] = new_name
                    save_data(st.session_state.data)
                    st.success("Đã đổi tên!")
                
                new_bio = st.text_area("Giới thiệu", value=user_info.get("bio", ""), height=100)
                if st.button("Cập nhật giới thiệu"):
                    user_info["bio"] = new_bio
                    save_data(st.session_state.data)
                    st.success("Đã cập nhật!")
                
                st.divider()
                st.write(f"**Link kết bạn:** `{user_info.get('link')}`")
        
        with tab2:
            code = st.text_input("Mã kích hoạt Pro").upper()
            if st.button("Kích hoạt"):
                for c in st.session_state.data["codes"]:
                    if isinstance(c, dict) and c.get("code") == code:
                        if st.session_state.user not in st.session_state.data["pro_users"]:
                            st.session_state.data["pro_users"].append(st.session_state.user)
                            save_data(st.session_state.data)
                            st.balloons()
                            st.success("Chúc mừng! Bạn đã là Pro!")
                        else:
                            st.info("Bạn đã là Pro rồi!")
                        break
                    elif isinstance(c, str) and c == code:
                        if st.session_state.user not in st.session_state.data["pro_users"]:
                            st.session_state.data["pro_users"].append(st.session_state.user)
                            st.session_state.data["codes"] = [x for x in st.session_state.data["codes"] if x != code]
                            save_data(st.session_state.data)
                            st.balloons()
                            st.success("Chúc mừng! Bạn đã là Pro!")
                        break
                else:
                    st.error("Mã không hợp lệ!")
        
        with tab3:
            st.write(f"**Phiên bản:** {CONFIG['VERSION']}")
            st.write(f"**Tác giả:** {CONFIG['CREATOR']}")
            st.write(f"**Ngày tham gia:** {user_info.get('created', 'Không rõ')[:16]}")
            st.write(f"**Hạng:** {'💎 Pro' if is_pro else '🆓 Miễn phí'}")
            st.write(f"**Dung lượng đã dùng:** {get_used_storage(st.session_state.user)/(1024**3):.2f} GB")

# ================== ADMIN ==================
elif st.session_state.page == "ADMIN":
    if not is_admin:
        st.error("Không có quyền!")
    else:
        st.markdown("<h2>🛠️ ADMIN</h2>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["🎫 Mã Pro", "📢 Thông báo", "👥 Quản lý người dùng"])
        
        with tab1:
            new_code = st.text_input("Mã mới").upper()
            c1, c2 = st.columns(2)
            with c1:
                has_expiry = st.checkbox("Hạn dùng")
                expiry = st.date_input("Ngày hết hạn") if has_expiry else None
            with c2:
                has_limit = st.checkbox("Giới hạn")
                max_uses = st.number_input("Số lần", min_value=1, value=1) if has_limit else None
            if st.button("TẠO MÃ") and new_code:
                st.session_state.data["codes"].append({"code": new_code, "expiry": str(expiry) if expiry else None, "max_uses": max_uses, "used_by": []})
                save_data(st.session_state.data)
                st.toast(f"✅ Đã tạo mã {new_code}")
            st.subheader("Danh sách mã")
            for c in st.session_state.data["codes"]:
                if isinstance(c, dict):
                    expiry_txt = c.get("expiry") or "Vĩnh viễn"
                    used = len(c.get("used_by", []))
                    max_txt = str(c.get("max_uses")) if c.get("max_uses") else "∞"
                    st.write(f"- `{c.get('code')}` (Hết hạn: {expiry_txt}, Lượt: {used}/{max_txt})")
                else:
                    st.write(f"- `{c}`")
        
        with tab2:
            send_to_future = st.checkbox("✓ Gửi cho người dùng tương lai")
            users = list(st.session_state.data["users"].keys())
            target = st.selectbox("Gửi đến", ["Tất cả"] + users) if not send_to_future else "TẤT CẢ (kể cả tương lai)"
            title = st.text_input("Tiêu đề")
            msg = st.text_area("Nội dung")
            if st.button("GỬI"):
                if send_to_future:
                    add_system_notification(title, msg)
                    st.toast("✅ Đã lưu thông báo cho tất cả (kể cả tương lai)!")
                else:
                    if target == "Tất cả":
                        for u in users:
                            add_notification(u, title, msg)
                        st.toast(f"✅ Đã gửi đến {len(users)} người!")
                    else:
                        add_notification(target, title, msg)
                        st.toast(f"✅ Đã gửi đến {target}!")
                st.rerun()
        
        with tab3:
            st.subheader("👥 DANH SÁCH NGƯỜI DÙNG")
            for u, user_data in st.session_state.data["users"].items():
                status = user_data.get("status", "active")
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    col1.write(f"**{u}** ({user_data['info'].get('name', u)})")
                    col2.write(f"Trạng thái: {'🟢 Hoạt động' if status == 'active' else '🔴 Đã khóa'}")
                    
                    if status == "active":
                        if col3.button(f"🔒 Khóa", key=f"ban_{u}"):
                            if u == CONFIG["ADMIN_USERNAME"]:
                                st.error("Không thể khóa tài khoản admin!")
                            else:
                                user_data["status"] = "banned"
                                save_data(st.session_state.data)
                                add_notification(u, "⚠️ Tài khoản bị khóa", "Tài khoản của bạn đã bị khóa.")
                                st.rerun()
                    else:
                        if col3.button(f"🔓 Mở khóa", key=f"unban_{u}"):
                            user_data["status"] = "active"
                            save_data(st.session_state.data)
                            add_notification(u, "✅ Tài khoản được mở khóa", "Tài khoản của bạn đã được mở khóa.")
                            st.rerun()
                    
                    if col4.button(f"🗑️ Xóa", key=f"delete_{u}"):
                        if u == CONFIG["ADMIN_USERNAME"]:
                            st.error("Không thể xóa tài khoản admin!")
                        else:
                            del st.session_state.data["users"][u]
                            save_data(st.session_state.data)
                            st.rerun()
                    
                    st.divider()

# ================== THÔNG TIN ==================
elif st.session_state.page == "ABOUT":
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;border-radius:16px;padding:20px">
        <h1 style="text-align:center">🚀 {CONFIG['NAME']}</h1>
        <p><b>Phiên bản:</b> {CONFIG['VERSION']}</p>
        <p><b>Tác giả:</b> {CONFIG['CREATOR']}</p>
        <p><b>Ngày phát hành:</b> 12.04.2026</p>
        <p><b>Thời gian phát triển:</b> 38 ngày (06/03 → 12/04/2026)</p>
        <hr>
        <p style="text-align:center"><i>"Kết nối tri thức, mở ra tương lai"</i></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ✨ TÍNH NĂNG")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **🤖 AI Thông Minh**
        - ✅ Trò chuyện AI với NEXUS OS Gateway
        - ✅ Phân tích file văn bản
        - ✅ Tìm kiếm web + AI tóm tắt
        
        **☁️ Lưu trữ Đám mây**
        - ✅ Tạo thư mục, quản lý file
        - ✅ Tải lên/xuống nhiều file
        - ✅ Free 30GB - Pro không giới hạn
        """)
    with col2:
        st.markdown("""
        **👥 Mạng xã hội**
        - ✅ Kết bạn bằng link
        - ✅ Thông báo realtime
        
        **🔧 Quản lý Cá nhân**
        - ✅ Ảnh đại diện, đổi tên
        - ✅ Lịch sử trò chuyện
        - ✅ Ghi nhớ thiết bị
        """)
    
    st.markdown("---")
    st.markdown(f"© 2025 {CONFIG['CREATOR']}")
    st.markdown(f"**{CONFIG['NAME']}** - Hệ điều hành AI đa năng")
