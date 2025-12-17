import streamlit as st
import math

# 設定網頁標題與分欄配置
st.set_page_config(page_title="建築工程工期估算系統", layout="wide")
st.title("🏗️ 建築工程工期估算系統 (台北市全流程版)")
st.markdown("本系統已整合前置作業、地質改良、結構施工及**末端消檢領證**之工期估算。")

# --- 1. 建立輸入介面 ---
with st.container():
    st.header("1. 基礎資訊與前置作業")
    col1, col2, col3 = st.columns(3)

    with col1:
        building_type = st.selectbox(
            "建物類型",
            ["住宅大樓", "辦公大樓", "百貨商場", "醫院", "科技廠房"]
        )
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

    with col2:
        structure_type = st.selectbox(
            "結構型式",
            ["RC (鋼筋混凝土)", "SRC (鋼骨鋼筋混凝土)", "SS/SC (純鋼骨結構)"]
        )
        construction_method = st.selectbox(
            "施工方式 (地下室)",
            ["順打工法", "逆打工法", "雙順打工法"]
        )

    with col3:
        soil_improvement = st.selectbox(
            "地質改良需求",
            ["無", "局部地質改良 (如抽水解壓、CCP樁)", "全區地質改良 (如攪拌樁、JSP樁)"]
        )
        # 新增消檢與使照選項
        inspection_type = st.selectbox(
            "消檢與使照複雜度",
            ["一般建築 (消檢+領證約90-120天)", "公眾使用/高層建築 (消檢+領證約150-180天)"]
        )

st.header("2. 工程規模與現況")
col4, col5, col6 = st.columns(3)
with col4:
    floors_above = st.number_input("地上層數", min_value=1, value=15, step=1)
    site_condition = st.selectbox(
            "基地現況",
            ["素地 (無建物)", "有舊建物 (需拆除)", "有舊基礎 (需拔樁/破除)"]
        )
with col5:
    floors_below = st.number_input("地下層數", min_value=0, value=3, step=1)
with col6:
    site_area = st.number_input("基地面積 (坪)", min_value=10.0, value=500.0)

# --- 2. 計算邏輯 ---

def calculate_duration():
    total_days = 0
    breakdown = {}

    # A. 前置作業與行政審查
    prep_map = {
        "一般案件 (約120天)": 120,
        "鄰近捷運禁限建範圍 (需影響評估)": 210,
        "基地含受保護樹木 (需移植審議)": 240,
        "大型開發案 (需交通維持計畫審查)": 180,
        "複雜案件 (捷運+樹保+交維)": 300
    }
    prep_base = prep_map[prep_status]
    
    demolition_days = 0
    if site_condition == "有舊建物 (需拆除)":
        demolition_days = 60
    elif site_condition == "有舊基礎 (需拔樁/破除)":
        demolition_days = 90
    
    total_days += (prep_base + demolition_days)
    breakdown['1. 前置作業與拆除'] = prep_base + demolition_days

    # B. 地下室工程
    base_days_per_floor = 45 if construction_method != "逆打工法" else 60
    basement_days = base_days_per_floor * floors_below
    
    improvement_days = 0
    if soil_improvement == "局部地質改良 (如抽水解壓、CCP樁)":
        improvement_days = 25
    elif soil_improvement == "全區地質改良 (如攪拌樁、JSP樁)":
        improvement_days = math.ceil((site_area / 500) * 45)
    
    total_days += (basement_days + improvement_days)
    breakdown['2. 地下室結構及改良'] = basement_days + improvement_days

    # C. 地上結構工程
    structure_map = {"RC (鋼筋混凝土)": 18, "SRC (鋼骨鋼筋混凝土)": 14, "SS/SC (純鋼骨結構)": 10}
    days_per_floor = structure_map[structure_type]
    structure_days = days_per_floor * floors_above

    # 逆打工期重疊計算
    overlap = 0
    if construction_method == "逆打工法":
        overlap = min(structure_days, basement_days * 0.7)
        total_days -= overlap
        breakdown['3. 逆打工期縮短(扣減)'] = -int(overlap)

    total_days += structure_days
    breakdown['4. 地上結構工程'] = structure_days

    # D. 裝修與機電
    finish_base = floors_above * 15
    factor_map = {"醫院": 1.5, "百貨商場": 1.3, "科技廠房": 0.8, "住宅大樓": 1.0, "辦公大樓": 1.1}
    finish_total = int(finish_base * factor_map.get(building_type, 1.0))
    finish_overlap = structure_days * 0.5
    finish_net = max(30, finish_total - finish_overlap)

    total_days += finish_net
    breakdown['5. 內裝機電工程'] = int(finish_net)

    # E. 新增：消檢與使用執照取得
    if inspection_type == "一般建築 (消檢+領證約90-120天)":
        admin_days = 105
    else: # 公眾使用
        admin_days = 165
    
    total_days += admin_days
    breakdown['6. 消檢與領得使照'] = admin_days

    return int(total_days), breakdown

# --- 3. 顯示結果 ---
st.markdown("---")
if st.button("🚀 點此計算預估總工期"):
    estimated_days, details = calculate_duration()
    estimated_months = round(estimated_days / 30, 1)

    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.metric(label="預估總工期 (從前置到使照)", value=f"{estimated_days} 天")
    with col_res2:
        st.metric(label="約合月份", value=f"{estimated_months} 個月")
    
    with st.expander("查看工期組成細節 (Step by Step)"):
        for key, value in details.items():
            if value < 0:
                st.write(f"✅ **{key}**: `{value}` 天")
            else:
                st.write(f"**{key}**: `{value}` 天")

    st.warning("💡 註：本估算包含消檢與使照流程。實際時程可能因消防圖說審查次數、缺失改進速度及都發局現勘排程而異。")