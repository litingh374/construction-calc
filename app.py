import streamlit as st
import math
from datetime import datetime, timedelta

# 設定網頁標題與分欄配置
st.set_page_config(page_title="建築工程工期估算系統", layout="wide")
st.title("🏗️ 建築工程工期估算系統 (專業精確版)")

# --- 1. 建立輸入介面 ---
with st.container():
    st.header("1. 工程條件設定")
    col1, col2, col3 = st.columns(3)

    with col1:
        building_type = st.selectbox("建物類型", ["住宅大樓", "辦公大樓", "百貨商場", "醫院", "科技廠房"])
        prep_status = st.selectbox("前置作業列管", ["一般案件 (約120天)", "鄰近捷運", "含受保護樹木", "大型開發案(交維)", "複雜案件"])
        structure_type = st.selectbox("結構型式", ["RC (鋼筋混凝土)", "SRC (鋼骨鋼筋混凝土)", "SS/SC (純鋼骨結構)"])

    with col2:
        construction_method = st.selectbox("施工方式 (地下室)", ["順打工法", "逆打工法", "雙順打工法"])
        soil_improvement = st.selectbox("地質改良", ["無", "局部地質改良", "全區地質改良"])
        inspection_type = st.selectbox("消檢與使照複雜度", ["一般建築 (約90-120天)", "公眾使用/高層建築 (約150-180天)"])

    with col3:
        floors_above = st.number_input("地上層數", min_value=1, value=15)
        floors_below = st.number_input("地下層數", min_value=0, value=3)
        site_condition = st.selectbox("基地現況", ["素地", "有舊建物 (需拆除)", "有舊基礎 (需拔樁)"])

# --- 2. 新增：日期與休假進階選項 ---
st.markdown("---")
st.header("📅 進階時間計算 (選用)")
use_date_calc = st.checkbox("啟用日期詳細計算 (考慮週末與春節)")

if use_date_calc:
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        start_date = st.date_input("預計開工日期", datetime.now())
    with d_col2:
        exclude_sunday = st.checkbox("排除週日施工 (台北市法令管制)", value=True)
        exclude_cny = st.checkbox("自動排除春節連假 (每年固定扣除7天)", value=True)

# --- 3. 計算邏輯 ---

def calculate_duration():
    details = {}
    
    # [基礎工期計算邏輯 - 保持與先前一致]
    prep_map = {"一般案件 (約120天)": 120, "鄰近捷運": 210, "含受保護樹木": 240, "大型開發案(交維)": 180, "複雜案件": 300}
    days = prep_map[prep_status]
    if "拆除" in site_condition: days += 60
    elif "拔樁" in site_condition: days += 90
    details['前置與準備'] = days

    b_days = (60 if construction_method == "逆打工法" else 45) * floors_below
    if soil_improvement == "局部地質改良": b_days += 25
    elif soil_improvement == "全區地質改良": b_days += 45
    details['地下室工程'] = b_days

    s_map = {"RC (鋼筋混凝土)": 18, "SRC (鋼骨鋼筋混凝土)": 14, "SS/SC (純鋼骨結構)": 10}
    s_days = s_map[structure_type] * floors_above
    details['地上結構工程'] = s_days

    if construction_method == "逆打工法":
        overlap = int(min(s_days, b_days * 0.7))
        days -= overlap
        details['逆打重疊縮短'] = -overlap

    f_base = floors_above * 15
    f_factor = {"醫院": 1.5, "百貨商場": 1.3, "科技廠房": 0.8, "住宅大樓": 1.0, "辦公大樓": 1.1}
    f_net = max(30, int(f_base * f_factor.get(building_type, 1.0)) - int(s_days * 0.5))
    details['內裝機電'] = f_net

    admin_days = 105 if "一般" in inspection_type else 165
    details['消檢使照'] = admin_days

    base_total_days = sum(details.values())
    
    # --- 進階修正邏輯 ---
    final_total = base_total_days
    if use_date_calc:
        # A. 排除週日 (工作天轉日曆天: 6天工作 = 7天日曆)
        if exclude_sunday:
            sunday_extra = base_total_days // 6
            final_total += sunday_extra
            details['週日停工加計'] = int(sunday_extra)

        # B. 排除春節 (每365天加7天)
        if exclude_cny:
            cny_years = math.ceil(final_total / 365)
            cny_extra = cny_years * 7
            final_total += cny_extra
            details['春節停工加計'] = int(cny_extra)

    return int(final_total), details

# --- 4. 顯示結果 ---
if st.button("🚀 計算結果"):
    total_days, breakdown = calculate_duration()
    
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.metric("總預估日曆天", f"{total_days} 天")
    with col_res2:
        st.metric("預計完工月份", f"{round(total_days/30, 1)} 個月")

    if use_date_calc:
        finish_date = start_date + timedelta(days=total_days)
        st.success(f"📅 預計完工日期：{finish_date.strftime('%Y年%m月%d日')}")

    with st.expander("查看明細"):
        for k, v in breakdown.items():
            st.write(f"{k}: `{v}` 天")