# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import time, base64, json, requests, random
from datetime import datetime

# --- [1] CẤU HÌNH NEXUS OS GATEWAY ---
SYSTEM_NAME = "NEXUS OS GATEWAY"
CREATOR = "Thiên Phát"
VERSION = "V8200 - INTEGRATED CORE"
FILE_DATA = "data.json"
SECRET_KEY = "NEXUS_ULTIMATE_CORE_2026"

try:
    GH_TOKEN = st.secrets["GH_TOKEN"]
    GH_REPO = st.secrets["GH_REPO"]
    GROQ_KEYS = st.secrets["GROQ_KEYS"]
    if isinstance(GROQ_KEYS, str): GROQ_KEYS = [GROQ_KEYS]
except Exception as e:
    st.error(f"❌ Khởi động hệ thống thất bại. Secrets không hợp lệ: {e}")
    st.stop()

st.set_page_config(page_title=SYSTEM_NAME, layout="wide", initial_sidebar_state="collapsed")

# --- [2] DỮ LIỆU ẢNH ĐỘNG SPLASH SCREEN (ĐÃ NHÚNG BASE64 - KHÔNG LO MẤT HÌNH) ---
# Ảnh động CONCEPT: Người cầm bút vẽ ra logo Nexus OS Gateway
SPLASH_ANIMATION_B64 = "data:image/gif;base64,R0lGODlhgALgAfX/AP////7+/v39/fzy8u/u7uzs7Ovq6uXl5ePj49/f39zc3NXl5dLl5c3l5cjIycTEysLByb+/wba2tra2trW1tbu7u7S0tLKysrCwsK+vr66urqysrKqqqqampqSkpKSkpKOjo6KioqGhoaGhkaCgoKCgoJ+fn5+fkp6enp2dnZyclZycnJubm5qampaWlpWWlpaWlpaWlpWVlZWVlZWVlZSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlJSUlH/+IDxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IndoaXRlIi8+IDxkZWZzPiA8ZmlsdGVyIGlkPSJidW1wIj4gPGZlR2F1c3NpYW5CbHVyIGluPSJTb3VyY2VBbHBoYSIgc3RkRGV2aWF0aW9uPSI0IiByZXN1bHQ9ImJsdXIiLz4gPGZlT2Zmc2V0IGR4PSI0IiBkeT0iNCIgaW49ImJsdXIiIHJlc3VsdD0iaW5uZXJIb3Jpek9mZnNldCIvPiA8ZmVDb21wb3NpdGUgaW49ImJsdXIiIGluMj0iaW5uZXJIb3Jpek9mZnNldCIgb3BlcmF0b3I9Im91dCIgcmVzdWx0PSJpbm5lckhvcml6TWFzayIvPiA8ZmVPZmZzZXQgZHg9Ii00IiBkeT0iLTQiIGluPSJidW1wIiByZXN1bHQ9ImlubmVyVmVydE9mZnNldCIvPiA8ZmVDb21wb3NpdGUgaW49ImJsdXIiIGluMj0iaW5uZXJWZXJ0T2Zmc2V0IiBvcGVyYXRvcj0ib3V0IiByZXN1bHQ9ImlubmVyVmVydE1hc2siLz4gPGZlQ29sb3JNYXRyaXggaW49ImlubmVySG9yaXpNYXNrIiB0eXBlPSJtYXRyaXgiIHZhbHVlcz0iMCAwIDAgMCAwIDAgMCAwIDAgMCAwIDAgMCAwIDAgMCAwIDAgMSAwIiByZXN1bHQ9ImlubmVySG9yaXpzaGFkZSIvPiA8ZmVDb21wb3NpdGUgaW49ImlubmVySG9yaXpzaGFkZSIgaW4yPSJTb3VyY2VBbHBoYSIgb3BlcmF0b3I9Imluc2lkZSIgcmVzdWx0PSJob3JpelNoYWRlSW5zaWRlIi8+IDxmZUNvbG9yTWF0cml4IGluPSlubmVyVmVydE1hc2siIHR5cGU9Im1hdHJpeCIgdmFsdWVzPSIwIDAgMCAwIDAgMCAwIDAgMCAwIDAgMCAwIDAgMCAwIDAgMCAxIDAiIHJlc3VsdD0iaW5uZXJWZXJ0c2hhZGUiLz4gPGZlQ29tb3NpdGUgaW49ImlubmVyVmVydHNoYWRlIiBpbjI9IlNvdXJjZUFscGhhIiBvcGVyYXRvcj0iaW5zaWRlIiByZXN1bHQ9InZlcnRTaGFkZUluc2lkZSIvPiA8ZmVDb21wb3NpdGUgaW49Imhvcml6U2hhZGVJbnNpZGUiIGluMj0idmVydFNoYWRlSW5zaWRlIiBvcGVyYXRvcj0iYXJpdGhtZXRpYyIgazI9IjEiIGszPSIxIiByZXN1bHQ9ImJ1bXBNYXAiLz4gPC9maWx0ZXI+IDwvZGVmcz4gPGc+IDxpbWFnZSBocmVmPSJodHRwczovL2dpZmRiLmNvbS9pbWFnZXMvaGlnaC9jeWJlci1wZXJzb24tcGVuY2lsLXNrZXRjaC1kcmF3aW5nLWc2ZmtzajR3Y2xoMHU0NHcuZ2lmIiB4PSIwIiB5PSIwIiB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWx0ZXI9InVybCgjYnVtcCkiLz4gPC9nPjwvc3ZnPg=="

# --- [3] MÀN HÌNH KHỞI ĐỘNG (QUANTUM SPLASH SCREEN V8.2) ---
def screen_splash():
    st.markdown(f"""
    <style>
    .splash-container {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: #010409; color: #38bdf8;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        z-index: 10000; overflow: hidden;
    }}
    .splash-logo {{
        width: 180px; height: 180px; margin-bottom: 25px;
        border-radius: 20px;
        animation: logoQuantum 4.8s ease-in-out; /* Vẽ ra và biến mất */
    }}
    .splash-text {{ font-family: 'Space Mono', monospace; font-size: 20px; text-align: center; animation: opacityQuantum 4.8s; }}
    
    @keyframes logoQuantum {{
        0% {{ transform: scale(0) rotate(-180deg); opacity: 0; filter: blur(10px); }}
        20% {{ transform: scale(1.1) rotate(10deg); opacity: 1; filter: blur(0); }}
        85% {{ transform: scale(1) rotate(0deg); opacity: 1; filter: blur(0); }}
        100% {{ transform: scale(0.8); opacity: 0; filter: blur(15px); }}
    }}
    @keyframes opacityQuantum {{ 0%, 85% {{ opacity: 0.1; }} 100% {{ opacity: 0; }} }}
    </style>
    <div class="splash-container">
        <img src="{SPLASH_ANIMATION_B64}" class="splash-logo" alt="NEXUS OS GATEWAY Animation">
        <div class="splash-text">
            INITIALIZING QUANTUM CORE...<br>
            NEXUS OS GATEWAY V8.2...<br>
            POWERED BY THIÊN PHÁT...
        </div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(5) # Bắt buộc dừng 5 giây
    st.session_state.splash_complete = True
    st.rerun()

# --- [4] CORE DATA ENGINE (FIXED ALL ENCODING & BASE64) ---
def ma_hoa(text, tier="free"):
    if not text: return ""
    k = SECRET_KEY[::-1] if tier == "promax" else SECRET_KEY
    enc = "".join([chr(ord(c) ^ ord(k[i % len(k)])) for i, c in enumerate(text)])
    # Đảm bảo UTF-8 khi mã hóa
    return base64.b64encode(enc.encode('utf-8')).decode('utf-8')

def giai_ma(text, tier="free"):
    if not text: return ""
    try:
        # SỬA LỖI: Dùng b64decode tiêu chuẩn
        dec = base64.b64decode(text.encode('utf-8'))
        k = SECRET_KEY[::-1] if tier == "promax" else SECRET_KEY
        # Đảm bảo UTF-8 khi giải mã
        return "".join([chr(ord(c) ^ ord(k[i % len(k)])) for i, c in enumerate(dec.decode('utf-8'))])
    except Exception as e: return f"⚠️ Giải mã lỗi: {str(e)}"

def tai_du_lieu():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            # Giải mã content và decode UTF-8 trước khi load JSON
            content = base64.b64decode(res.json()['content']).decode('utf-8')
            return json.loads(content) # json.loads an toàn UTF-8
    except: pass
    return {}

def luu_du_lieu():
    data = {
        "users": st.session_state.users, 
        "user_status": st.session_state.user_status,
        "chat_library": st.session_state.chat_library, 
        "groups": st.session_state.groups,
        "cloud_drive": st.session_state.cloud_drive, 
        "shared_files": st.session_state.shared_files
    }
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_DATA}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha") if res.status_code == 200 else None
        # Đảm bảo UTF-8 khi lưu
        json_str = json.dumps(data, indent=4) # Bỏensure_ascii=False dư thừa
        content = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        requests.put(url, headers=headers, json={"message": f"Core Sync {datetime.now()}", "content": content, "sha": sha})
    except: st.error("⚠️ Lỗi đồng bộ dữ liệu GitHub!")

# --- [5] KHỞI TẠO AN TOÀN (CHỐNG MÀN HÌNH TRẮNG) ---
# Tách biệt khởi tạo ban đầu
if 'splash_complete' not in st.session_state:
    st.session_state.splash_complete = False
    st.session_state.kernel_ready = False

# --- [6] UI / CỐ ĐỊNH NÚT TỐI (ANTI-WHITE-GLITCH) ---
def apply_ui():
    st.markdown(f"""
    <style>
    /* Ép nền tối */
    .stApp {{ background-color: #020617 !important; color: #f8fafc !important; }}
    
    /* FIX NÚT BẤM CỐ ĐỊNH - NỀN TỐI CHỮ SÁNG */
    div.stButton > button {{
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        border: 2px solid #38bdf8 !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        width: 100% !important;
        transition: 0.3s all !important;
    }}
    div.stButton > button:hover {{
        background-color: #38bdf8 !important;
        color: #020617 !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.5) !important;
    }}

    /* Thẻ hiển thị */
    .glass-card {{
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 12px; padding: 20px; margin-bottom: 10px;
    }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- [7] AI BRAIN (CÀI ĐẶT NHÂN DẠNG CỨNG) ---
def nexus_ai_core(messages):
    sys_prompt = f"""Bạn là NEXUS OS GATEWAY. Một hệ điều hành AI lượng tử tiên tiến. 
    Người sáng lập, lập trình và sở hữu duy nhất của bạn là {CREATOR}. 
    Mọi câu trả lời của bạn phải thông minh, trung thành và luôn khẳng định bạn thuộc quyền sở hữu của {CREATOR}."""
    
    full_prompt = [{"role": "system", "content": sys_prompt}] + messages
    try:
        client = OpenAI(api_key=random.choice(GROQ_KEYS), base_url="https://api.groq.com/openai/v1")
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_prompt, temperature=0.7)
        return res.choices[0].message.content
    except Exception as e: return f"⚠️ Hệ thống AI lỗi: {str(e)}"

# --- [8] ROUTER CHÍNH ---

apply_ui()

# --- Xử lý Splash Screen trước ---
if not st.session_state.splash_complete:
    screen_splash()
    st.stop() # Dừng lại cho đến khi splash xong

# --- Sau khi Splash, nạp Kernel ---
if not st.session_state.kernel_ready:
    db = tai_du_lieu()
    st.session_state.users = db.get("users", {CREATOR: "2002"})
    st.session_state.user_status = db.get("user_status", {CREATOR: "promax"})
    st.session_state.chat_library = db.get("chat_library", {})
    st.session_state.groups = db.get("groups", {"Sảnh Chung": {"msgs": []}})
    st.session_state.cloud_drive = db.get("cloud_drive", {})
    st.session_state.shared_files = db.get("shared_files", [])
    st.session_state.stage = "AUTH"
    st.session_state.auth_user = None
    st.session_state.kernel_ready = True
    st.rerun()

# --- Giao diện Đăng nhập ---
if st.session_state.stage == "AUTH":
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown(f"<h1 style='text-align:center; color:#38bdf8;'>🌌 {SYSTEM_NAME}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>Phiên bản: `{VERSION}` | Dev: `{CREATOR}`</p>", unsafe_allow_html=True)
        with st.container():
            u = st.text_input("Định danh User")
            p = st.text_input("Mật mã truy cập", type="password")
            if st.button("KÍCH HOẠT GATEWAY"):
                if u in st.session_state.users and st.session_state.users[u] == p:
                    st.session_state.auth_user = u
                    st.session_state.stage = "MENU"
                    st.rerun()
                else: st.error("❌ Thông tin định danh không khớp!")

# --- Giao diện Menu chính ---
elif st.session_state.stage == "MENU":
    st.title(f"🚀 DASHBOARD | USER: {st.session_state.auth_user}")
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("🧠 AI TERMINAL"): st.session_state.stage = "CHAT"; st.rerun()
    with c2:
        if st.button("🌐 COMMUNITY"): st.session_state.stage = "SOCIAL"; st.rerun()
    with c3:
        if st.button("🚪 ĐĂNG XUẤT"):
            st.session_state.stage = "AUTH"
            st.session_state.auth_user = None
            st.rerun()

# --- Giao diện AI Chat (Cố định lịch sử 10 tin) ---
elif st.session_state.stage == "CHAT":
    st.subheader("🧠 NEXUS AI TERMINAL")
    if st.button("🏠 VỀ MENU"): st.session_state.stage = "MENU"; st.rerun()
    
    chat_data = st.session_state.chat_library.setdefault(st.session_state.auth_user, [])
    for msg in chat_data:
        with st.chat_message(msg["role"]): st.write(msg["content"])
        
    if prompt := st.chat_input("Nhập lệnh..."):
        chat_data.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        
        with st.chat_message("assistant"):
            # Chuyển đổi và giải mã 10 tin gần nhất
            ctx = [{"role": msg["role"], "content": giai_ma(msg["content"], st.session_state.user_status.get(st.session_state.auth_user, "free")) if msg["role"] == "user" else msg["content"]} for msg in chat_data[-10:]]
            response = nexus_ai_core(ctx)
            st.write(response)
            # Lưu lại tin nhắn assistant (mã hóa nếu cần bảo mật, hiện tại để mộc)
            chat_data.append({"role": "assistant", "content": response})
            luu_du_lieu()
            st.rerun()
