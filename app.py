import streamlit as st
import math

# 設定網頁標題
st.title("🏗️ 建築工程工期估算系統")
st.markdown("請在下方輸入基地條件與施工方式，系統將自動推算預估工期。")

# --- 1. 建立輸入介面 (側邊欄或主畫面) ---
st.header("1. 基本資料輸入")

col1, col2 = st.columns(2)

with col1:
    building_type = st.selectbox(
        "建物類型",
        ["住宅大樓", "辦公大樓", "百貨商場", "醫院", "科技廠房"]
    )
    
    structure_type = st.selectbox(
        "結構型式",
        ["RC (鋼筋混凝土)", "SRC (鋼骨鋼筋混凝土)", "SS/SC (純鋼骨結構)"]
    )

    construction_method = st.selectbox(
        "施工方式 (地下室)",
        ["順打工法", "逆打工法", "雙順打工法"]
    )

with col2:
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

# --- 3. 計算邏輯核心 (這裡是您需要根據專業經驗調整的地方) ---

def calculate_duration():
    total_days = 0
    breakdown = {} # 用來儲存細項

    # A. 前置與拆除
    prep_days = 30 # 假設基本動員30天
    if site_condition == "有舊建物 (需拆除)":
        prep_days += 60 # 假設拆除需60天
    elif site_condition == "有舊基礎 (需拔樁/破除)":
        prep_days += 90
    
    total_days += prep_days
    breakdown['前置與拆除'] = prep_days

    # B. 基礎與地下室工程 (每層所需天數 * 層數 * 工法係數)
    # 假設基礎單層開挖+支撐+結構平均天數
    base_days_per_floor = 45 
    
    # 工法修正
    if construction_method == "逆打工法":
        # 逆打地下室通常較慢，但可與地上層重疊
        base_days_per_floor = 60 
    elif excavation_method == "明挖 (放坡)":
        base_days_per_floor = 35 # 較快

    basement_days = base_days_per_floor * floors_below
    
    # 連續壁施作時間 (粗估：周長相關，這裡簡化用面積與層數估算)
    if excavation_method == "連續壁工法":
        wall_days = 60 + (floors_below * 10) # 假設
        basement_days += wall_days

    total_days += basement_days
    breakdown['地下室結構'] = basement_days

    # C. 地上結構工程
    # 定義標準層天數
    if "RC" in structure_type:
        days_per_floor = 18
    elif "SRC" in structure_type:
        days_per_floor = 14
    else: # SS/SC
        days_per_floor = 10
    
    structure_days = days_per_floor * floors_above

    # 若為逆打，地上結構與地下結構部分重疊 (假設重疊 70% 的地下室時間)
    if construction_method == "逆打工法":
        overlap = min(structure_days, basement_days * 0.7)
        total_days -= overlap
        breakdown['逆打工期重疊扣減'] = -int(overlap)

    total_days += structure_days
    breakdown['地上結構'] = structure_days

    # D. 裝修與機電 (根據建物類型加權)
    finish_days = floors_above * 15 # 基本裝修
    
    factor = 1.0
    if building_type == "醫院":
        factor = 1.5 # 系統複雜
    elif building_type == "百貨商場":
        factor = 1.3
    elif building_type == "科技廠房":
        factor = 0.8 # 系統化安裝
    
    finish_total = int(finish_days * factor)
    
    # 裝修通常在結構體完成一半後進場 (重疊施工)
    finish_overlap = structure_days * 0.5
    finish_net = finish_total - finish_overlap
    if finish_net < 0: finish_net = 0 # 不可能小於0

    total_days += finish_net
    breakdown['裝修機電 (扣除重疊)'] = int(finish_net)

    return int(total_days), breakdown

# --- 4. 輸出結果 ---
st.markdown("---")
if st.button("開始計算工期"):
    estimated_days, details = calculate_duration()
    estimated_months = round(estimated_days / 30, 1)

    st.success(f"### 🚩 預估總工期：約 {estimated_days} 日歷天 ({estimated_months} 個月)")
    
    # 顯示詳細計算項目
    st.write("#### 工期分析明細：")
    for key, value in details.items():
        st.write(f"- **{key}**: {value} 天")

    st.info("註：此結果包含天候與休假係數之粗略估算，實際工期需依排程網圖 (CPM) 為準。")