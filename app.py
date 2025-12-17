import streamlit as st
import math
from datetime import datetime, timedelta

# --- 0. 網頁配置與自定義 CSS ---
st.set_page_config(page_title="建築工程工期估算系統", layout="wide")

st.markdown("""
    <style>
    /* 全域背景顏色 */
    .main {
        background-color: #F8F9FA;
    }
    /* 標題樣式 */
    .main-title {
        color: #263238;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        border-bottom: 4px solid #FFC107;
        padding-bottom: 10px;
    }
    /* 卡片樣式 */
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-top: 5px solid #FFC107;
    }
    /* 按鈕樣式 */
    div.stButton > button:first-child {
        background-color: #FFC107;
        color: #263238;
        border: none;
        font-weight: bold;
        width: 100%;
        height: 3em;
        border-radius: 5px;
    }
    div.stButton > button:hover {
        background-color: #FFB300;
        color: black;
    }
    /* 警告/備註樣式 */
    .warning-text {
        color: #FF5722;
        font-size: 0.9em;
        font-weight: bold;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 頁面標題 ---
st.markdown('<h1 class="main-title">🏗️ 建築工程工期估算系統 <span style="font-size:0.5em; color:gray;">(專業精用版)</span></h1>', unsafe_allow_html=True)
st.write("")

# --- 2. 輸入介面 (使用卡片式布局) ---
with st.form("input_form"):
    st.subheader("1. 工程條件設定")
    col1, col2, col3 = st.columns(3)

    with col1:
        building_type = st.selectbox("🏢 建物類型", ["住宅大樓", "辦公大樓", "百貨商場", "醫院", "科技廠房"])
        prep_status = st.selectbox("📝 前置作業列管", ["一般案件 (約120天)", "鄰近捷運", "含受保護樹木", "大型開發案(交維)", "複雜案件"])
        structure_type = st.selectbox("🏗️ 結構型式", ["RC (鋼筋混凝土)", "SRC (鋼骨鋼筋混凝土)", "SS/SC (純鋼骨結構)"])

    with col2:
        construction_method = st.selectbox("🚜 施工方式 (地下室)", ["順打工法", "逆打工法", "雙順打工法"])
        soil_improvement = st.selectbox("🧪 地質改良", ["無", "局部地質改良", "全區地質改良"])
        inspection_type = st.selectbox("🚒 消檢與使照複雜度", ["一般建築 (約90-120天)", "公眾使用/高層建築 (約150-180天)"])

    with col3:
        floors_above = st.number_input("⬆️ 地上層數", min_value=1, value=15)
        floors_below = st.number_input("⬇️ 地下層數", min_value=0, value=3)
        site_condition = st.selectbox("🏁 基地現況", ["素地", "有舊建物 (需拆除)", "有舊基礎 (需拔樁)"])
        site_area = st.number_input("📐 基地面積 (坪)", min_value=10.0, value=500.0)

    st.markdown("---")
    st.subheader("📅 進階時間計算 (選用)")
    use_date_calc = st.checkbox("啟用日期詳細計算 (自動計算週日與春節)", value=True)
    
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        start_date = st.date_input("🗓️ 預計開工日期", datetime.now())
    with d_col2:
        exclude_sunday = st.checkbox("🚫 排除週日施工 (台北市管制)", value=True)
        exclude_cny = st.checkbox("🏮 自動排除春節連假 (每年7天)", value=True)

    submit_button = st.form_submit_button("🚀 開始估算總工期")

# --- 3. 計算邏輯 (維持先前優化的邏輯) ---
def calculate_duration():
    details = {}
    # A. 前置
    prep_map = {"一般案件 (約120天)": 120, "鄰近捷運": 210, "含受保護樹木": 240, "大型開發案(交維)": 180, "複雜案件": 300}
    days = prep_map[prep_status]
    if "拆除" in site_condition: days += 60
    elif "拔樁" in site_condition: days += 90
    details['前置準備與拆除'] = days

    # B. 地下室
    b_days = (60 if construction_method == "逆打工法" else 45) * floors_below
    if soil_improvement == "局部地質改良": b_days += 25
    elif soil_improvement == "全區地質改良": b_days += math.ceil((site_area / 500) * 45)
    details['地下室與地改工程'] = b_days

    # C. 地上層
    s_map = {"RC (鋼筋混凝土)": 18, "SRC (鋼骨鋼筋混凝土)": 14, "SS/SC (純鋼骨結構)": 10}
    s_days = s_map[structure_type] * floors_above
    details['地上結構體工程'] = s_days

    # D. 逆打重疊
    if construction_method == "逆打工法":
        overlap = int(min(s_days, b_days * 0.7))
        details['逆打工期縮短'] = -overlap

    # E. 裝修
    f_base = floors_above * 15
    f_factor = {"醫院": 1.5, "百貨商場": 1.3, "科技廠房": 0.8, "住宅大樓": 1.0, "辦公大樓": 1.1}
    f_net = max(30, int(f_base * f_factor.get(building_type, 1.0)) - int(s_days * 0.5))
    details['內裝機電與裝修'] = f_net

    # F. 使照
    admin_days = 105 if "一般" in inspection_type else 165
    details['消檢及取得使照'] = admin_days

    base_total_days = sum(details.values())