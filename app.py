import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import time

# --- 1. CẤU HÌNH HỆ THỐNG VIP ---
st.set_page_config(page_title="Quantum VIP V23", layout="wide", page_icon="👑")

# --- 2. GIAO DIỆN BLACK & GOLD LUXURY ---
st.markdown("""
<style>
    /* Ẩn header/footer mặc định */
    header, footer {visibility: hidden;}
    
    /* Nền đen sang trọng */
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(147deg, #000000 0%, #1a1a1a 74%);
        color: #d4af37; /* Màu vàng Gold */
        font-family: 'Helvetica Neue', sans-serif;
    }

    /* Thẻ Card VIP */
    .vip-card {
        background: rgba(20, 20, 20, 0.8);
        border: 1px solid #d4af37;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 0 15px rgba(212, 175, 55, 0.2);
        text-align: center;
        margin-bottom: 20px;
    }

    /* Nút bấm mạ vàng */
    .stButton>button {
        background: linear-gradient(45deg, #d4af37, #c5a028);
        color: #000 !important;
        border: none !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        padding: 10px 25px !important;
        text-transform: uppercase;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 0 20px #d4af37;
        transform: scale(1.02);
    }

    /* Input fields tối màu */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #1a1a1a !important;
        color: #d4af37 !important;
        border: 1px solid #333 !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #d4af37;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. KẾT NỐI DỮ LIỆU (CORE ENGINE) ---
url = st.secrets["connections"]["gsheets"]["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    """Hàm tải dữ liệu an toàn, chống lỗi"""
    try:
        # ttl=0 để không bị lưu cache cũ
        df = conn.read(spreadsheet=url, ttl=0)
        df = df.dropna(how='all') # Bỏ dòng trống
        # Ép kiểu dữ liệu để tính toán không bị lỗi
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
        return df
    except Exception:
        # Nếu lỗi (ví dụ file mới chưa có dữ liệu), trả về bảng rỗng
        return pd.DataFrame(columns=['date', 'type', 'category', 'amount', 'note'])

# --- 4. THANH ĐIỀU HƯỚNG ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/6941/6941697.png", width=80)
    st.title("QUANTUM ELITE")
    st.markdown("---")
    
    menu = st.radio(
        "MENU ĐIỀU KHIỂN",
        ["💎 DASHBOARD (Tổng quan)", "💸 GIAO DỊCH (Thêm/Trừ)", "📈 VIP ANALYTICS", "💾 DỮ LIỆU & CÀI ĐẶT"]
    )
    
    st.markdown("---")
    st.caption("© 2025 Quantum Finance OS")

# --- 5. CHỨC NĂNG CHÍNH ---

if menu == "💎 DASHBOARD (Tổng quan)":
    st.header("TỔNG QUAN TÀI SẢN")
    
    df = get_data()
    
    if not df.empty:
        # Tính toán logic: Thu - Chi
        total_thu = df[df['type'] == 'Thu']['amount'].sum()
        total_chi = df[df['type'] == 'Chi']['amount'].sum()
        balance = total_thu - total_chi
        
        # Hiển thị thẻ VIP
        st.markdown(f"""
        <div class="vip-card">
            <h3 style="margin:0; color: #888;">TỔNG TÀI SẢN THỰC TẾ</h3>
            <h1 style="font-size: 3.5rem; margin: 10px 0; text-shadow: 0 0 10px #d4af37;">{balance:,.0f} VNĐ</h1>
            <p>Trạng thái: 🟢 Hoạt động tốt</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 TỔNG THU NHẬP", f"{total_thu:,.0f}")
        c2.metric("💸 TỔNG CHI TIÊU", f"{total_chi:,.0f}")
        
        # Tính năng VIP: Dự báo chi tiêu
        avg_chi = total_chi / max(1, len(df[df['type']=='Chi']))
        c3.metric("📉 CHI TRUNG BÌNH/GIAO DỊCH", f"{avg_chi:,.0f}")

        st.markdown("---")
        st.subheader("Hoạt động gần đây")
        st.dataframe(df.sort_values(by="date", ascending=False).head(5), use_container_width=True)
    else:
        st.info("Chào mừng chủ nhân! Hệ thống chưa có dữ liệu. Hãy vào menu GIAO DỊCH để bắt đầu.")

elif menu == "💸 GIAO DỊCH (Thêm/Trừ)":
    st.header("THỰC HIỆN GIAO DỊCH")
    st.write("Nhập thông tin bên dưới để hệ thống tự động cộng hoặc trừ vào tài khoản.")
    
    with st.container():
        st.markdown('<div class="vip-card" style="text-align:left;">', unsafe_allow_html=True)
        with st.form("vip_transaction_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                date_input = st.date_input("Ngày giao dịch", datetime.now())
                # Logic quan trọng: Chọn Thu hay Chi
                trans_type = st.radio("Loại hành động", ["Chi (Trừ tiền)", "Thu (Cộng tiền)"], horizontal=True)
            
            with col2:
                amount_input = st.number_input("Số tiền (VNĐ)", min_value=0, step=10000)
                category = st.selectbox("Danh mục", ["Ăn uống", "Di chuyển", "Mua sắm", "Lương", "Thưởng", "Đầu tư", "Khác"])
            
            note_input = st.text_input("Ghi chú (Tùy chọn)")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("XÁC NHẬN GIAO DỊCH ➡️")
            
            if submitted:
                if amount_input > 0:
                    with st.spinner("Đang xử lý giao dịch mã hóa..."):
                        # Chuẩn hóa loại giao dịch
                        final_type = "Chi" if "Chi" in trans_type else "Thu"
                        
                        # 1. Lấy dữ liệu cũ
                        current_df = get_data()
                        
                        # 2. Tạo dòng mới
                        new_row = pd.DataFrame([{
                            "date": date_input.strftime('%Y-%m-%d'),
                            "type": final_type,
                            "category": category,
                            "amount": float(amount_input),
                            "note": note_input
                        }])
                        
                        # 3. Gộp và Lưu (Dùng conn.create để ghi đè an toàn tuyệt đối)
                        updated_df = pd.concat([current_df, new_row], ignore_index=True)
                        conn.create(spreadsheet=url, data=updated_df)
                        
                        st.balloons()
                        st.success(f"✅ Đã {'trừ' if final_type == 'Chi' else 'cộng'} {amount_input:,.0f} VNĐ vào hệ thống!")
                        time.sleep(1)
                else:
                    st.error("⚠️ Số tiền phải lớn hơn 0!")
        st.markdown('</div>', unsafe_allow_html=True)

elif menu == "📈 VIP ANALYTICS":
    st.header("PHÂN TÍCH CHUYÊN SÂU")
    df = get_data()
    
    if not df.empty:
        # Lọc dữ liệu Chi
        df_chi = df[df['type'] == 'Chi']
        
        tab1, tab2 = st.tabs(["Biểu đồ Tròn", "Xu hướng theo Ngày"])
        
        with tab1:
            if not df_chi.empty:
                fig = px.pie(df_chi, values='amount', names='category', title='Cơ cấu chi tiêu',
                             color_discrete_sequence=px.colors.sequential.RdBu, hole=0.4)
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#d4af37'))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu chi tiêu.")
                
        with tab2:
            # Biểu đồ cột theo ngày
            daily_sum = df.groupby(['date', 'type'])['amount'].sum().reset_index()
            fig2 = px.bar(daily_sum, x='date', y='amount', color='type', barmode='group',
                          color_discrete_map={'Thu': '#00cc66', 'Chi': '#ff3333'})
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#d4af37'))
            st.plotly_chart(fig2, use_container_width=True)
            
        # Tính năng VIP: Cảnh báo hạn mức
        st.subheader("⚠️ Cảnh báo Hạn mức")
        limit = st.number_input("Đặt hạn mức chi tiêu tháng này (VNĐ)", value=5000000, step=500000)
        current_spent = df_chi['amount'].sum()
        percent = min(current_spent / limit, 1.0)
        
        st.progress(percent)
        if current_spent > limit:
            st.error(f"BẠN ĐÃ VƯỢT HẠN MỨC! (Đã chi: {current_spent:,.0f} / Hạn mức: {limit:,.0f})")
        else:
            st.success(f"An toàn. Còn lại: {limit - current_spent:,.0f} VNĐ")
            
    else:
        st.write("Chưa có dữ liệu để phân tích.")

elif menu == "💾 DỮ LIỆU & CÀI ĐẶT":
    st.header("DATA VAULT")
    df = get_data()
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("Xuất dữ liệu ra Excel để lưu trữ cá nhân.")
        # Chuyển đổi CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 TẢI XUỐNG DỮ LIỆU (.CSV)",
            data=csv,
            file_name=f"Quantum_Backup_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
        )
    
    with col2:
        st.error("Khu vực nguy hiểm")
        if st.checkbox("Tôi muốn xóa sạch dữ liệu để làm lại từ đầu"):
            if st.button("🗑️ XÓA TOÀN BỘ HỆ THỐNG"):
                empty_df = pd.DataFrame(columns=['date', 'type', 'category', 'amount', 'note'])
                conn.create(spreadsheet=url, data=empty_df)
                st.success("Hệ thống đã được reset!")
                time.sleep(1)
                st.rerun()
