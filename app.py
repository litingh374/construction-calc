import streamlit as st
import math

# 設定網頁標題
st.title("🏗️ 建築工程工期估算系統 (台北市加強版)")
st.markdown("本系統已整合台北市施工前置作業列管時間，請選擇相關條件進行估算。")

# --- 1. 建立輸入介面 ---
st.header("1. 基地條件與前置作業")

col1, col2 = st.columns(2)

with col1:
    building_type = st.selectbox(
        "建物類型",
        ["住宅大樓", "辦公大樓", "百貨商場", "醫院", "科技廠房"]
    )
    
    # 新增的前置作業下拉選項
    prep_status = st.selectbox(
        "前置作業列管項目",
        [
            "一般案件 (約120天)", 
            "鄰近捷運禁限建範圍 (需影響評估)", 
            "基地含受保護樹木 (需移植審議)", 
            "大型開發案 (需交通維持計畫審查)",
            "複雜案件 (捷運+樹保+交維)"
        ]
    )

    structure_type = st.selectbox(
        "結構型式",
        ["RC (鋼筋混凝土)", "SRC (鋼骨鋼筋混凝土)", "SS/SC (純鋼骨結構)"]
    )

with col2:
    construction_method = st.selectbox(
        "施工方式 (地下室)",
        ["順打工法", "逆打工法", "雙順打工法"]
    )
    
    excavation_method = st.selectbox(
        "開挖/擋土型式",
        ["連續壁工法", "島式開挖", "明挖 (放坡)", "鋼板樁"]
    )
    
    site_condition = st.selectbox(
        "基地現況",
        ["素地 (無建物)", "有舊建物 (需拆除)", "有舊基礎 (需拔樁/破除)"]
    )

st.header("2. 量體規模")
col3, col4 = st.columns(2)
with col3:
    floors_above = st.number_input("地上層數", min_value=1, value=15, step=1)
    floors_below = st.number_input("地下層數", min_value=0, value=3, step=1)
with col4:
    site_area = st.number_input("基地面積 (坪)", min_value=10.0, value=500.0)

# --- 3. 計算邏輯核心 ---

def calculate_duration():
    total_days = 0
    breakdown = {}

    # A. 前置作業時間 (依據您的需求新增)
    if prep_status == "一般案件 (約120天)":
        prep_base = 120
    elif prep_status == "鄰近捷運禁限建範圍 (需影響評估)":
        prep_base = 210  # 增加捷運會審與現況調查時間
    elif prep_status == "基地含受保護樹木 (需移植審議)":
        prep_base = 240  # 台北市樹保審議時程較長
    elif prep_status == "大型開發案 (需交通維持計畫審查)":
        prep_base = 180  # 含交維審查與會勘
    else: # 複雜案件
        prep_base = 300  # 多項列管併行之行政折衝

    # 若有舊建物需拆除，再加計拆除工期
    demolition_days = 0
    if site_condition == "有舊建物 (需拆除)":
        demolition_days = 60
    elif site_condition == "有舊基礎 (需拔樁/破除)":
        demolition_days = 90
    
    total_days += (prep_base + demolition_days)
    breakdown['前置作業 (含行政審查)'] = prep_base
    if demolition_days > 0:
        breakdown['舊建物拆除/基礎處理'] = demolition_days

    # B. 地下室工程
    base_days_per_floor = 45 
    if construction_method == "逆打工法":
        base_days_per_floor = 60 
    
    basement_days = base_days_per_floor * floors_below
    if excavation_method == "連續壁工法":
        wall_days = 60 + (floors_below * 10)
        basement_days += wall_days

    total_days += basement_days
    breakdown['地下室結構工程'] = basement_days

    # C. 地上結構工程
    if "RC" in structure_type:
        days_per_floor = 18
    elif "SRC" in structure_type:
        days_per_floor = 14
    else:
        days_per_floor = 10
    
    structure_days = days_per_floor * floors_above

    # 逆打工期重疊計算
    if construction_method == "逆打工法":
        overlap = min(structure_days, basement_days * 0.7)
        total_days -= overlap
        breakdown['逆打工期重疊扣減'] = -int(overlap)

    total_days += structure_days
    breakdown['地上結構工程'] = structure_days

    # D. 裝修與機電 (扣除重疊進場時間)
    finish_days = floors_above * 15
    factor = {"醫院": 1.5, "百貨商場": 1.3, "科技廠房": 0.8, "住宅大樓": 1.0, "辦公大樓": 1.1}
    finish_total = int(finish_days * factor.get(building_type, 1.0))
    
    finish_overlap = structure_days * 0.5
    finish_net = max(0, finish_total - finish_overlap)

    total_days += finish_net
    breakdown['內裝機電 (扣除重疊期)'] = int(finish_net)

    return int(total_days), breakdown

# --- 4. 輸出結果 ---
st.markdown("---")
if st.button("🚀 開始計算預估工期"):
    estimated_days, details = calculate_duration()
    estimated_months = round(estimated_days / 30, 1)

    st.success(f"### 🚩 預估總工期：約 {estimated_days} 日歷天 (約 {estimated_months} 個月)")
    
    # 顯示詳細計算項目
    st.write("#### 工期組成明細分析：")
    for key, value in details.items():
        if value < 0:
            st.write(f"🟢 **{key}**: {value} 天 (工期優化)")
        else:
            st.write(f"- {key}: {value} 天")

    st.warning("⚠️ 提醒：台北市各項審議時間受限於各局處委員會時程，實際申報開工日請以核定公文為準。")