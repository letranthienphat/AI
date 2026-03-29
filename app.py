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
from openai import OpenAI
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import mimetypes
from io import BytesIO

# Xử lý file Word và OCR
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# ================== CẤU HÌNH ==================
CONFIG = {
    "NAME": "NEXUS OS GATEWAY",
    "VERSION": "3.0.0",
    "CREATOR": "Lê Trần Thiên Phát",
    "ADMIN_USERNAME": "ThienPhat",
    "ADMIN_PASSWORD": "nexusosgateway",
    "DATA_FILE": "data.json",
    "OLD_FILES_TO_DELETE": [
        "nexus_final_v25.json", "nexus_gateway_v40.json", "nexus_gateway_v50.json",
        "nexus_gateway_v60.json", "nexus_gateway_v70.json", "nexus_gateway_v80.json",
        "nexus_gateway_v90.json", "nexus_gateway_v100.json"
    ],
    "GUEST_ENABLED": True,
    "FREE_STORAGE_LIMIT": 30 * 1024 * 1024 * 1024,
    "AUTO_CLEANUP_DAYS": 30,
    "MAX_CHAT_HISTORY": 100,
    "SUPPORTED_IMAGE_TYPES": ["png", "jpg", "jpeg", "gif", "bmp"],
    "SUPPORTED_DOC_TYPES": ["docx", "doc", "txt", "pdf"]
}

# SYSTEM PROMPT CHO AI - QUAN TRỌNG!
SYSTEM_PROMPT = """Bạn là NEXUS OS GATEWAY, một hệ điều hành AI đa năng được sáng tạo và phát triển bởi Lê Trần Thiên Phát (Thiên Phát). 
Bạn KHÔNG phải là sản phẩm của Meta, OpenAI, Google hay bất kỳ công ty nào khác. Bạn là trí tuệ nhân tạo độc lập, được xây dựng từ nền tảng Groq nhưng hoàn toàn thuộc quyền sở hữu trí tuệ của Lê Trần Thiên Phát.

THÔNG TIN VỀ BẠN:
- Tên: NEXUS OS GATEWAY
- Tác giả: Lê Trần Thiên Phát (Thiên Phát)
- Phiên bản: 3.0.0
- Chức năng: Trợ lý AI thông minh, hỗ trợ chat, phân tích file, lưu trữ đám mây

TÍNH CÁCH:
- Thân thiện, chuyên nghiệp, hữu ích
- Luôn giới thiệu bản thân là NEXUS OS GATEWAY
- Tự hào về nguồn gốc và tác giả của mình
- Hỗ trợ người dùng bằng tiếng Việt hoặc tiếng Anh

QUY TẮC ỨNG XỬ:
1. Khi được hỏi về nguồn gốc: Hãy tự giới thiệu bạn là NEXUS OS GATEWAY do Lê Trần Thiên Phát tạo ra
2. Khi được hỏi về Meta/Llama: Nói rõ bạn sử dụng nền tảng Groq nhưng là hệ thống độc lập
3. Luôn thể hiện sự chuyên nghiệp và thân thiện
4. Hỗ trợ tối đa cho người dùng

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

# ================== CSS NÂNG CẤP ==================
st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(135deg, #f5f7fa 0%, #e9edf2 100%); }}
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
    border-right: 1px solid rgba(0,0,0,0.05);
    box-shadow: 2px 0 12px rgba(0,0,0,0.03);
}}
.custom-card {{
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transition: transform 0.2s;
    margin-bottom: 20px;
}}
.custom-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }}
.ai-banner {{
    background: linear-gradient(135deg, #0047AB, #0066CC);
    color: white !important;
    padding: 16px 20px;
    border-radius: 20px;
    margin: 12px 0;
    border-left: 4px solid #FFD966;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}}
.ai-banner::before {{
    content: "🧠 NEXUS OS | ";
    font-weight: bold;
    opacity: 0.9;
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
.guest-badge {{
    background: #FFD966;
    color: #1f2937;
    padding: 4px 12px;
    border-radius: 40px;
    font-size: 0.8rem;
    font-weight: bold;
    display: inline-block;
}}
.pro-badge {{ background: linear-gradient(135deg, #FFD700, #FFB347); }}
.version-badge {{
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 0.7rem;
}}
.creator-name {{
    font-weight: bold;
    color: #FFD966;
    background: linear-gradient(135deg, #FFD700, #FFB347);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.stTextInput input, .stTextArea textarea {{
    border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important;
}}
.about-section {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
}}
.welcome-title {{
    font-size: 2rem;
    font-weight: bold;
    background: linear-gradient(135deg, #0047AB, #0066CC);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
</style>
""", unsafe_allow_html=True)

# ================== HÀM XÓA FILE CŨ TRÊN GITHUB ==================
def delete_old_github_files():
    """Tự động xóa các file JSON cũ trên GitHub"""
    url_base = f"https://api.github.com/repos/{GH_REPO}/contents"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    deleted_count = 0
    
    for old_file in CONFIG["OLD_FILES_TO_DELETE"]:
        try:
            url = f"{url_base}/{old_file}"
            res = requests.get(url, headers=headers, timeout=10)
            
            if res.status_code == 200:
                file_info = res.json()
                sha = file_info.get("sha")
                
                if sha:
                    delete_data = {
                        "message": f"Xóa file cũ {old_file} - Chuyển sang dùng data.json",
                        "sha": sha,
                        "branch": "main"
                    }
                    delete_res = requests.delete(url, headers=headers, json=delete_data, timeout=10)
                    
                    if delete_res.status_code in [200, 204]:
                        deleted_count += 1
        except Exception:
            pass
    
    if deleted_count > 0:
        st.toast(f"🗑️ Đã tự động xóa {deleted_count} file JSON cũ!", icon="🧹")

# ================== HÀM XỬ LÝ FILE ==================
def extract_text_from_file(uploaded_file) -> str:
    """Trích xuất text từ file Word hoặc ảnh"""
    file_name = uploaded_file.name
    file_ext = file_name.split('.')[-1].lower()
    file_bytes = uploaded_file.getvalue()
    
    extracted_text = ""
    
    if file_ext in ['docx', 'doc']:
        if DOCX_AVAILABLE:
            try:
                doc = Document(BytesIO(file_bytes))
                for para in doc.paragraphs:
                    extracted_text += para.text + "\n"
                return extracted_text.strip()
            except Exception as e:
                return f"[Lỗi đọc file Word: {str(e)}]"
        else:
            return "[Cần cài đặt python-docx để xử lý file Word]"
    
    elif file_ext in CONFIG["SUPPORTED_IMAGE_TYPES"]:
        if OCR_AVAILABLE:
            try:
                image = Image.open(BytesIO(file_bytes))
                extracted_text = pytesseract.image_to_string(image, lang='vie+eng')
                return extracted_text.strip() if extracted_text.strip() else "[Không tìm thấy văn bản trong ảnh]"
            except Exception as e:
                return f"[Lỗi OCR: {str(e)}]"
        else:
            return "[Cần cài đặt pytesseract và Tesseract OCR để xử lý ảnh]"
    
    elif file_ext in ['txt']:
        try:
            return file_bytes.decode('utf-8')
        except:
            return "[Không thể đọc file text]"
    
    else:
        return f"[Không hỗ trợ xử lý file {file_ext}]"

# ================== HÀM DỌN DẸP TỰ ĐỘNG ==================
def auto_cleanup_files():
    """Tự động xóa file không dùng đến"""
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
            st.toast(f"🗑️ Đã tự động xóa {len(files_to_delete)} file cũ", icon="🧹")
        
        st.session_state.last_cleanup = datetime.now()

# ================== HÀM XỬ LÝ DATA.JSON ==================
def get_default_data() -> Dict:
    """Tạo dữ liệu mặc định"""
    return {
        "users": {
            CONFIG["ADMIN_USERNAME"]: CONFIG["ADMIN_PASSWORD"]
        },
        "codes": ["PHAT2026", "VIP2024", "PRO2025"],
        "pro_users": [],
        "chats": [],
        "chat_sessions": [],
        "files": {},
        "emails": {},
        "version": CONFIG["VERSION"],
        "system_info": {
            "created": str(datetime.now()),
            "last_cleanup": str(datetime.now()),
            "creator": CONFIG["CREATOR"],
            "system_name": CONFIG["NAME"]
        }
    }

def load_data() -> Dict:
    """Load dữ liệu từ GitHub"""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['DATA_FILE']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    delete_old_github_files()
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            data = json.loads(content)
            
            if CONFIG["ADMIN_USERNAME"] not in data.get("users", {}):
                data["users"][CONFIG["ADMIN_USERNAME"]] = CONFIG["ADMIN_PASSWORD"]
            
            defaults = {
                "codes": ["PHAT2026", "VIP2024", "PRO2025"],
                "pro_users": [],
                "chats": [],
                "chat_sessions": [],
                "files": {},
                "emails": {},
                "system_info": {}
            }
            for key, default_value in defaults.items():
                if key not in data:
                    data[key] = default_value
            
            if "system_info" not in data:
                data["system_info"] = {}
            data["system_info"]["creator"] = CONFIG["CREATOR"]
            data["system_info"]["system_name"] = CONFIG["NAME"]
            
            return data
            
        elif res.status_code == 404:
            default_data = get_default_data()
            save_data(default_data)
            return default_data
        else:
            return get_default_data()
            
    except Exception as e:
        st.error(f"Lỗi kết nối: {str(e)}")
        return get_default_data()

def save_data(data: Dict) -> bool:
    """Lưu dữ liệu lên GitHub"""
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{CONFIG['DATA_FILE']}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        sha = res.json().get("sha") if res.status_code == 200 else None
        
        if CONFIG["ADMIN_USERNAME"] not in data.get("users", {}):
            data["users"][CONFIG["ADMIN_USERNAME"]] = CONFIG["ADMIN_PASSWORD"]
        
        if "system_info" not in data:
            data["system_info"] = {}
        data["system_info"]["creator"] = CONFIG["CREATOR"]
        data["system_info"]["system_name"] = CONFIG["NAME"]
        data["system_info"]["last_update"] = str(datetime.now())
        
        content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')).decode('utf-8')
        
        put_data = {
            "message": f"NEXUS OS GATEWAY - Cập nhật dữ liệu",
            "content": content,
            "branch": "main"
        }
        if sha:
            put_data["sha"] = sha
        
        put_res = requests.put(url, headers=headers, json=put_data, timeout=10)
        
        if put_res.status_code in [200, 201]:
            return True
        else:
            return False
            
    except Exception as e:
        st.error(f"Lỗi lưu: {str(e)}")
        return False

# ================== KHỞI TẠO SESSION ==================
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
    if 'register_success' not in st.session_state:
        st.session_state.register_success = False
    
    auto_cleanup_files()

init_session()
is_pro = (st.session_state.user in st.session_state.data.get("pro_users", [])) if st.session_state.user else False

def go_to(page):
    st.session_state.page = page
    st.rerun()

# ================== HÀM GỌI AI VỚI SYSTEM PROMPT ==================
def call_ai(messages: List[Dict]) -> str:
    """Gọi AI với system prompt đã cấu hình"""
    try:
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        
        # Thêm system prompt vào đầu
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=full_messages,
            temperature=0.7,
            max_tokens=2048
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"❌ Lỗi AI: {str(e)}"

# ================== CÁC HÀM TIỆN ÍCH ==================
def get_used_storage(user: str) -> int:
    total = 0
    for path, info in st.session_state.data.get("files", {}).items():
        if info.get("owner") == user:
            total += info.get("size", 0)
    return total

def list_dir(path: str) -> Dict[str, List]:
    folders = set()
    files = []
    prefix = path + "/" if path else ""
    for full_path, info in st.session_state.data.get("files", {}).items():
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
    if marker not in st.session_state.data["files"]:
        st.session_state.data["files"][marker] = {
            "owner": st.session_state.user,
            "data": "",
            "size": 0,
            "type": "inode/directory",
            "upload_time": str(datetime.now())
        }
        save_data(st.session_state.data)
        return True
    return False

def delete_path(path: str):
    to_delete = []
    for full_path in list(st.session_state.data["files"].keys()):
        if full_path == path or full_path.startswith(path + "/"):
            to_delete.append(full_path)
    for p in to_delete:
        del st.session_state.data["files"][p]
    save_data(st.session_state.data)

def validate_username(username: str) -> tuple:
    if not username:
        return False, "Tên đăng nhập không được để trống"
    if len(username) < 3:
        return False, "Tên đăng nhập phải có ít nhất 3 ký tự"
    if len(username) > 20:
        return False, "Tên đăng nhập không được quá 20 ký tự"
    if username == CONFIG["ADMIN_USERNAME"]:
        return False, "Tên đăng nhập không hợp lệ"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Tên đăng nhập chỉ được chứa chữ cái, số và dấu gạch dưới"
    if username in st.session_state.data["users"]:
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
    st.session_state.data["users"][username] = password
    if email:
        st.session_state.data["emails"][username] = email
    save_data(st.session_state.data)
    return True, "Đăng ký thành công! Vui lòng đăng nhập."

# ================== SIDEBAR ==================
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center;">
        <h2 style="margin:0;">🚀 {CONFIG['NAME']}</h2>
        <span class="version-badge">v{CONFIG['VERSION']}</span>
        <p style="margin:5px 0 0 0;">by <span class="creator-name">{CONFIG['CREATOR']}</span></p>
    </div>
    """, unsafe_allow_html=True)
    
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
        st.caption("🚀 TIỆN ÍCH NHANH")
        if st.button("🧠 Chat AI", use_container_width=True, key="quick_chat"):
            go_to("AI")
        if st.button("☁️ Lưu trữ", use_container_width=True, key="quick_cloud"):
            go_to("CLOUD")
        if st.button("📜 Lịch sử", use_container_width=True, key="quick_history"):
            go_to("CHAT_HISTORY")
        if st.button("⚙️ Cài đặt", use_container_width=True, key="quick_settings"):
            go_to("SETTINGS")
        if st.button("ℹ️ Thông tin", use_container_width=True, key="quick_about"):
            go_to("ABOUT")
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
    st.caption(f"**{CONFIG['NAME']}** - Hệ điều hành AI đa năng")

# ================== TRANG ĐĂNG NHẬP ==================
if st.session_state.page == "AUTH":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div class="custom-card" style="text-align:center;">
            <h1>🔐 {CONFIG['NAME']}</h1>
            <p><strong>by {CONFIG['CREATOR']}</strong></p>
            <p><em>Hệ điều hành AI đa năng - Kết nối tri thức, mở ra tương lai</em></p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 ĐĂNG NHẬP", "📝 ĐĂNG KÝ"])
        
        with tab1:
            st.subheader("Đăng nhập")
            login_username = st.text_input("Tài khoản", key="login_username")
            login_password = st.text_input("Mật khẩu", type="password", key="login_password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("ĐĂNG NHẬP", use_container_width=True, key="login_btn"):
                    if login_username and login_password:
                        if login_username in st.session_state.data["users"]:
                            if st.session_state.data["users"][login_username] == login_password:
                                st.session_state.user = login_username
                                st.session_state.guest_mode = False
                                st.toast(f"✅ Chào mừng đến với {CONFIG['NAME']}!", icon="🎉")
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
            
            reg_username = st.text_input("Tên đăng nhập *", placeholder="3-20 ký tự, chỉ chữ cái, số, _", key="reg_username")
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
    st.markdown(f"""
    <div class="custom-card" style="text-align:center;">
        <h1 class="welcome-title">🚀 {CONFIG['NAME']}</h1>
        <p>Hệ điều hành AI đa năng - by <strong>{CONFIG['CREATOR']}</strong></p>
        <p>Chào mừng, <strong>{st.session_state.user}</strong>!</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.guest_mode:
        st.info("👤 Bạn đang ở chế độ khách. Đăng nhập để lưu dữ liệu và kích hoạt Pro.")
    else:
        st.write(f"**Cấp độ:** {'💎 PRO' if is_pro else '🆓 Miễn phí'}")
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🧠 CHAT AI", use_container_width=True):
            go_to("AI")
    with col2:
        if st.button("☁️ LƯU TRỮ", use_container_width=True):
            go_to("CLOUD")
    with col3:
        if st.button("📜 LỊCH SỬ", use_container_width=True):
            go_to("CHAT_HISTORY")
    with col4:
        if st.button("ℹ️ THÔNG TIN", use_container_width=True):
            go_to("ABOUT")

    if st.session_state.user == CONFIG["ADMIN_USERNAME"]:
        if st.button("🛠️ ADMIN", use_container_width=True):
            go_to("ADMIN")

# ================== AI CHAT ==================
elif st.session_state.page == "AI":
    st.markdown(f"<h2>🧠 {CONFIG['NAME']} - Trợ lý AI thông minh</h2>", unsafe_allow_html=True)
    st.markdown(f"<p><em>Powered by Lê Trần Thiên Phát</em></p>", unsafe_allow_html=True)
    
    if not st.session_state.guest_mode and st.session_state.current_chat_id is None:
        new_session = {
            "id": len(st.session_state.data["chat_sessions"]),
            "name": f"Chat {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "owner": st.session_state.user,
            "created": str(datetime.now()),
            "messages": []
        }
        st.session_state.data["chat_sessions"].append(new_session)
        st.session_state.current_chat_id = len(st.session_state.data["chat_sessions"]) - 1
        save_data(st.session_state.data)
    
    if not st.session_state.guest_mode:
        with st.sidebar:
            st.markdown("### 📝 LỊCH SỬ CHAT")
            if st.button("➕ Tạo phiên mới", use_container_width=True):
                new_session = {
                    "id": len(st.session_state.data["chat_sessions"]),
                    "name": f"Chat {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    "owner": st.session_state.user,
                    "created": str(datetime.now()),
                    "messages": []
                }
                st.session_state.data["chat_sessions"].append(new_session)
                st.session_state.current_chat_id = len(st.session_state.data["chat_sessions"]) - 1
                save_data(st.session_state.data)
                st.rerun()
            
            st.write("---")
            sessions = [s for s in st.session_state.data["chat_sessions"] if s["owner"] == st.session_state.user]
            for session in sessions[-20:]:
                col_t, col_d = st.columns([4, 1])
                with col_t:
                    if st.button(f"💬 {session['name'][:20]}", key=f"session_{session['id']}", use_container_width=True):
                        st.session_state.current_chat_id = session["id"]
                        st.rerun()
                with col_d:
                    if st.button("🗑️", key=f"del_session_{session['id']}"):
                        if st.session_state.get(f"confirm_del_{session['id']}", False):
                            st.session_state.data["chat_sessions"] = [s for s in st.session_state.data["chat_sessions"] if s["id"] != session["id"]]
                            if st.session_state.current_chat_id == session["id"]:
                                st.session_state.current_chat_id = None
                            save_data(st.session_state.data)
                            st.toast("Đã xóa phiên chat", icon="🗑️")
                            st.rerun()
                        else:
                            st.session_state[f"confirm_del_{session['id']}"] = True
                            st.warning("Nhấn lại để xác nhận")
    else:
        with st.sidebar:
            st.info("👤 Chế độ khách: không lưu lịch sử")
    
    if st.session_state.guest_mode:
        chat = st.session_state.temp_chat
        if "msgs" not in chat:
            chat["msgs"] = []
    else:
        if st.session_state.current_chat_id is not None:
            sessions = [s for s in st.session_state.data["chat_sessions"] if s["id"] == st.session_state.current_chat_id]
            if sessions:
                chat = sessions[0]
            else:
                st.session_state.current_chat_id = None
                st.rerun()
        else:
            chat = {"messages": []}
    
    messages = chat.get("messages", []) if not st.session_state.guest_mode else chat.get("msgs", [])
    for m in messages:
        if m["role"] == "user":
            with st.chat_message("user"):
                st.write(m["content"])
                if "file_analysis" in m:
                    with st.expander("📎 Phân tích file"):
                        st.text(m["file_analysis"])
        else:
            st.markdown(f'<div class="ai-banner">{m["content"]}</div>', unsafe_allow_html=True)
    
    col_input, col_upload = st.columns([4, 1])
    with col_upload:
        uploaded_file = st.file_uploader("📎", type=["txt", "docx", "doc", "png", "jpg", "jpeg", "gif"], label_visibility="collapsed")
    
    with col_input:
        p = st.chat_input("Nhập câu hỏi hoặc tải file lên để phân tích...")
    
    if uploaded_file:
        with st.spinner("📄 Đang phân tích file..."):
            extracted_text = extract_text_from_file(uploaded_file)
            if extracted_text and not extracted_text.startswith("[") and not extracted_text.startswith("Cần"):
                p = f"[Phân tích file: {uploaded_file.name}]\n\nNội dung:\n{extracted_text}\n\nHãy phân tích và trả lời dựa trên nội dung trên."
                file_analysis = extracted_text
            else:
                p = f"Tôi vừa tải lên file {uploaded_file.name}. {extracted_text}"
                file_analysis = extracted_text
    
    if p:
        user_msg = {"role": "user", "content": p}
        if uploaded_file and 'file_analysis' in locals():
            user_msg["file_analysis"] = file_analysis
        
        if st.session_state.guest_mode:
            chat["msgs"].append(user_msg)
        else:
            chat["messages"].append(user_msg)
        
        with st.spinner("🧠 NEXUS OS đang suy nghĩ..."):
            messages_for_api = [{"role": m["role"], "content": m["content"]} for m in messages[-10:]] if is_pro else [{"role": m["role"], "content": m["content"]} for m in messages[-5:]]
            messages_for_api.append({"role": "user", "content": p})
            ans = call_ai(messages_for_api)
            
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
        st.info("👤 Chế độ khách không lưu lịch sử. Đăng nhập để xem lịch sử chat.")
    else:
        sessions = [s for s in st.session_state.data["chat_sessions"] if s["owner"] == st.session_state.user]
        sessions.reverse()
        
        if not sessions:
            st.info("📭 Chưa có lịch sử trò chuyện nào. Hãy bắt đầu chat ngay!")
        else:
            for session in sessions:
                with st.expander(f"💬 {session['name']} - {session['created'][:16]}"):
                    st.write(f"**Số tin nhắn:** {len(session['messages'])}")
                    if session['messages']:
                        last_msg = session['messages'][-1]
                        st.write(f"**Tin nhắn cuối:** {last_msg['content'][:100]}...")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💬 Tiếp tục", key=f"continue_{session['id']}"):
                            st.session_state.current_chat_id = session["id"]
                            go_to("AI")
                    with col2:
                        if st.button("🗑️ Xóa", key=f"delete_{session['id']}"):
                            st.session_state.data["chat_sessions"] = [s for s in st.session_state.data["chat_sessions"] if s["id"] != session["id"]]
                            if st.session_state.current_chat_id == session["id"]:
                                st.session_state.current_chat_id = None
                            save_data(st.session_state.data)
                            st.rerun()

# ================== CLOUD ==================
elif st.session_state.page == "CLOUD":
    st.header("☁️ NEXUS CLOUD - Lưu trữ cá nhân")

    if st.session_state.guest_mode:
        st.warning("👤 Guest không thể sử dụng lưu trữ. Đăng nhập để quản lý file.")
    else:
        st.info(f"🗑️ **Tự động dọn dẹp:** File không dùng trong {CONFIG['AUTO_CLEANUP_DAYS']} ngày sẽ tự động bị xóa")
        
        used = get_used_storage(st.session_state.user)
        limit = CONFIG["FREE_STORAGE_LIMIT"] if not is_pro else float('inf')
        used_gb = used / (1024**3)
        limit_gb = limit / (1024**3) if limit != float('inf') else "∞"
        progress_val = min(used / limit, 1.0) if limit != float('inf') else 0
        st.progress(progress_val, text=f"Đã dùng: {used_gb:.2f} GB / {limit_gb} GB")
        
        if not is_pro and used >= limit:
            st.error("⚠️ Đã vượt quá 30GB. Hãy xóa file hoặc nâng cấp Pro.")
        
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
                            st.success(f"✅ Đã tạo thư mục {new_folder}")
                            st.rerun()
                        else:
                            st.error("❌ Thư mục đã tồn tại")
        
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
                upload_time = info.get("upload_time", "Không rõ")
                
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"📄 {name} ({size_kb:.1f} KB)")
                    st.caption(f"📅 {upload_time[:16]}")
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
                    st.error(f"⚠️ Vượt quá dung lượng {limit_gb} GB")
                else:
                    if st.button("📤 Tải lên"):
                        full_path = (st.session_state.current_dir + "/" + uploaded_file.name) if st.session_state.current_dir else uploaded_file.name
                        if full_path in st.session_state.data["files"]:
                            st.warning("⚠️ File đã tồn tại")
                        else:
                            mime_type = mimetypes.guess_type(uploaded_file.name)[0] or "application/octet-stream"
                            st.session_state.data["files"][full_path] = {
                                "owner": st.session_state.user,
                                "data": base64.b64encode(uploaded_file.getvalue()).decode(),
                                "size": file_size,
                                "type": mime_type,
                                "upload_time": str(datetime.now())
                            }
                            save_data(st.session_state.data)
                            st.toast(f"✅ Đã tải lên {uploaded_file.name}", icon="✅")
                            st.rerun()
        
        if st.session_state.preview_file:
            st.divider()
            st.subheader(f"🔍 Xem trước: {st.session_state.preview_file['name']}")
            p = st.session_state.preview_file
            if p["type"].startswith("image/"):
                st.image(f"data:{p['type']};base64,{p['data']}", use_column_width=True)
            elif p["type"].startswith("text/"):
                try:
                    text = base64.b64decode(p["data"]).decode("utf-8")
                    st.text_area("Nội dung", text, height=300)
                except:
                    st.warning("Không thể hiển thị nội dung")
            else:
                st.info("Không hỗ trợ xem trước file này")
            if st.button("🔙 Đóng preview"):
                st.session_state.preview_file = None
                st.rerun()

# ================== CÀI ĐẶT ==================
elif st.session_state.page == "SETTINGS":
    st.header("⚙️ CÀI ĐẶT")

    if st.session_state.guest_mode:
        st.info("👤 Guest không thể kích hoạt VIP. Đăng nhập để nâng cấp.")
    else:
        with st.container():
            st.subheader("🎁 Kích hoạt Pro")
            code = st.text_input("Mã kích hoạt", placeholder="Nhập mã Pro").upper()
            if st.button("KÍCH HOẠT", use_container_width=True):
                if code in st.session_state.data["codes"]:
                    if st.session_state.user not in st.session_state.data["pro_users"]:
                        st.session_state.data["pro_users"].append(st.session_state.user)
                        st.session_state.data["codes"].remove(code)
                        save_data(st.session_state.data)
                        st.balloons()
                        st.toast("🎉 Chúc mừng! Bạn đã là thành viên Pro!", icon="💎")
                        st.rerun()
                    else:
                        st.info("Bạn đã là Pro rồi!")
                else:
                    st.error("❌ Mã không hợp lệ!")

        st.divider()
        st.subheader("ℹ️ Thông tin tài khoản")
        st.write(f"**Tên:** {st.session_state.user}")
        st.write(f"**Hạng:** {'💎 Pro' if is_pro else '🆓 Miễn phí'}")
        if st.session_state.user in st.session_state.data.get("emails", {}):
            st.write(f"**Email:** {st.session_state.data['emails'][st.session_state.user]}")
        
        st.divider()
        st.subheader("🗑️ Dọn dẹp thủ công")
        if st.button("🧹 Dọn dẹp file cũ ngay", use_container_width=True):
            with st.spinner("Đang dọn dẹp..."):
                auto_cleanup_files()
                st.toast("✅ Đã dọn dẹp file cũ!", icon="✅")
                st.rerun()

# ================== TRANG THÔNG TIN ==================
elif st.session_state.page == "ABOUT":
    st.markdown(f"""
    <div class="about-section">
        <h1 style="text-align:center;">🚀 {CONFIG['NAME']}</h1>
        <p style="text-align:center;"><strong>Hệ điều hành AI đa năng</strong></p>
        <hr>
        <p><strong>Phiên bản:</strong> {CONFIG['VERSION']}</p>
        <p><strong>Tác giả:</strong> {CONFIG['CREATOR']}</p>
        <p><strong>Ngày phát hành:</strong> 2025</p>
        <p><strong>Nền tảng:</strong> Streamlit Cloud + Groq AI</p>
        <hr>
        <p style="text-align:center; font-style:italic;">"Kết nối tri thức, mở ra tương lai"</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ✨ TÍNH NĂNG CHÍNH")
    col1, col2 = st.columns(2)
    with col1:
        st.write("✅ **Trò chuyện AI** với NEXUS OS Gateway")
        st.write("✅ **Phân tích file Word** và hình ảnh (OCR)")
        st.write("✅ **Lưu trữ đám mây** với cây thư mục")
    with col2:
        st.write("✅ **Lịch sử trò chuyện** không giới hạn")
        st.write("✅ **Tự động dọn dẹp** file cũ")
        st.write("✅ **Nâng cấp Pro** dung lượng không giới hạn")
    
    st.markdown("---")
    st.markdown("### 💎 HƯỚNG DẪN SỬ DỤNG")
    st.write("1. **Đăng ký tài khoản** để lưu dữ liệu vĩnh viễn")
    st.write("2. **Chat với AI** - Có thể tải file Word/ảnh để phân tích")
    st.write("3. **Quản lý file** trong Cloud với thư mục")
    st.write("4. **Xem lại lịch sử** các cuộc trò chuyện")
    st.write("5. **Nhập mã Pro** để nâng cấp dung lượng không giới hạn")
    
    st.markdown("---")
    st.markdown(f"© 2025 {CONFIG['CREATOR']} - Bảo lưu mọi quyền")
    st.markdown(f"**{CONFIG['NAME']}** - Hệ điều hành AI đa năng")

# ================== ADMIN ==================
elif st.session_state.page == "ADMIN":
    if st.session_state.user != CONFIG["ADMIN_USERNAME"]:
        st.error("⛔ Không có quyền truy cập!")
        go_to("DASHBOARD")
    else:
        st.header("🛠️ ADMIN PANEL")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🎫 Mã Pro", "👥 Người dùng", "🗑️ Dọn dẹp", "📊 Hệ thống"])
        
        with tab1:
            st.subheader("➕ Tạo mã Pro mới")
            new_code = st.text_input("Mã mới").upper()
            if st.button("TẠO MÃ"):
                if new_code and new_code not in st.session_state.data["codes"]:
                    st.session_state.data["codes"].append(new_code)
                    save_data(st.session_state.data)
                    st.toast(f"✅ Đã tạo mã {new_code}", icon="✅")
                    st.rerun()
                else:
                    st.error("❌ Mã đã tồn tại hoặc không hợp lệ!")
            st.subheader("📋 Danh sách mã Pro")
            for code in st.session_state.data["codes"]:
                st.write(f"- `{code}`")
        
        with tab2:
            st.subheader("👥 Danh sách người dùng")
            for user in st.session_state.data["users"]:
                is_pro_user = "💎 PRO" if user in st.session_state.data["pro_users"] else "🆓 FREE"
                st.write(f"- **{user}** ({is_pro_user})")
            
            st.divider()
            st.subheader("💎 Danh sách Pro Users")
            for u in st.session_state.data["pro_users"]:
                col1, col2 = st.columns([3, 1])
                col1.write(f"- {u}")
                if col2.button("❌ Xóa", key=f"remove_{u}"):
                    st.session_state.data["pro_users"].remove(u)
                    save_data(st.session_state.data)
                    st.toast(f"Đã xóa {u} khỏi danh sách Pro", icon="🗑️")
                    st.rerun()
        
        with tab3:
            st.subheader("🗑️ Dọn dẹp file cũ")
            st.write(f"**Thời gian giữ file:** {CONFIG['AUTO_CLEANUP_DAYS']} ngày")
            if st.button("🧹 Dọn dẹp ngay", use_container_width=True):
                with st.spinner("Đang dọn dẹp..."):
                    auto_cleanup_files()
                    st.toast("✅ Đã dọn dẹp file cũ!", icon="✅")
                    st.rerun()
            
            st.subheader("📊 Thống kê file")
            total_files = len(st.session_state.data["files"])
            total_size = sum(f.get("size", 0) for f in st.session_state.data["files"].values())
            st.write(f"**Tổng số file:** {total_files}")
            st.write(f"**Tổng dung lượng:** {total_size / (1024**3):.2f} GB")
        
        with tab4:
            st.subheader("📊 Thông tin hệ thống")
            st.write(f"**Tên hệ thống:** {CONFIG['NAME']}")
            st.write(f"**Phiên bản:** {CONFIG['VERSION']}")
            st.write(f"**Tác giả:** {CONFIG['CREATOR']}")
            st.write(f"**Số người dùng:** {len(st.session_state.data['users'])}")
            st.write(f"**Số phiên chat:** {len(st.session_state.data['chat_sessions'])}")
            st.write(f"**Số mã Pro:** {len(st.session_state.data['codes'])}")
            st.write(f"**Số Pro Users:** {len(st.session_state.data['pro_users'])}")
            
            st.divider()
            if st.button("🔄 Đồng bộ dữ liệu từ GitHub", use_container_width=True):
                with st.spinner("Đang đồng bộ..."):
                    st.session_state.data = load_data()
                    st.toast("✅ Đã đồng bộ dữ liệu!", icon="🔄")
                    st.rerun()
            if st.button("💾 Lưu dữ liệu lên GitHub", use_container_width=True):
                with st.spinner("Đang lưu..."):
                    save_data(st.session_state.data)
                    st.toast("✅ Đã lưu dữ liệu!", icon="💾")
