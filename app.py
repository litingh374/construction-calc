"""
Construction Schedule Estimator – Tender Estimation Tool (Python)
Target use: 投標工期估算
Python 3.9+
"""

from datetime import datetime, timedelta
import csv
from typing import Dict

# =============================
# 台北市實務投標參數（保守 / 一般 / 樂觀）
# =============================

PRESET = {
    "conservative": {
        "pre_factor": 1.2,
        "construction_factor": 1.15,
        "admin_factor": 1.2,
    },
    "normal": {
        "pre_factor": 1.0,
        "construction_factor": 1.0,
        "admin_factor": 1.0,
    },
    "optimistic": {
        "pre_factor": 0.9,
        "construction_factor": 0.9,
        "admin_factor": 0.9,
    },
}

# =============================
# 基準工期設定（天）
# =============================

CONFIG = {
    "pre_construction": {
        "general": 120,
        "near_mrt": 210,
        "large_public": 270,
        "environmental": 330,
    },
    "ground_improvement": {
        "none": 0,
        "partial": 45,
        "full": 90,
        "special": 120,
    },
    "building_base": {
        "residential": 540,
        "office": 600,
        "factory": 480,
        "mall": 720,
        "hospital": 840,
    },
    "structure_factor": {
        "RC": 1.0,
        "SRC": 1.1,
        "SS": 0.9,
        "SC": 0.95,
    },
    "method_factor": {
        "forward": 1.0,
        "reverse": 1.15,
        "double_forward": 0.95,
    },
    "completion_admin": {
        "normal": 60,
        "complex": 100,
        "phased": 120,
    },
    "holiday": {
        "chinese_new_year": 10,
    },
}

# =============================
# 日期工具
# =============================

def is_weekend(date: datetime) -> bool:
    return date.weekday() >= 5


def calculate_end_date(start: datetime, days: int, exclude_weekend: bool, exclude_cny: bool) -> datetime:
    current = start
    counted = 0

    while counted < days:
        current += timedelta(days=1)
        if exclude_weekend and is_weekend(current):
            continue
        counted += 1

    if exclude_cny:
        current += timedelta(days=CONFIG["holiday"]["chinese_new_year"])

    return current

# =============================
# 核心工期計算
# =============================

def calculate_schedule(options: Dict) -> Dict:
    preset = PRESET.get(options.get("preset", "normal"))

    pre_days = round(
        CONFIG["pre_construction"][options["pre_construction_type"]]
        * preset["pre_factor"]
    )

    ground_days = CONFIG["ground_improvement"][options["ground_improvement_type"]]

    base = CONFIG["building_base"][options["building_type"]]
    structure = CONFIG["structure_factor"][options["structure_type"]]
    method = CONFIG["method_factor"][options["construction_method"]]

    construction_days = round(
        base * structure * method * preset["construction_factor"]
    )

    admin_days = round(
        CONFIG["completion_admin"][options["completion_admin_type"]]
        * preset["admin_factor"]
    )

    total_days = pre_days + ground_days + construction_days + admin_days

    end_date = calculate_end_date(
        options["start_date"],
        total_days,
        options.get("exclude_weekend", True),
        options.get("exclude_cny", True),
    )

    return {
        "breakdown": {
            "pre_construction": pre_days,
            "ground_improvement": ground_days,
            "main_construction": construction_days,
            "completion_admin": admin_days,
        },
        "total_days": total_days,
        "end_date": end_date.strftime("%Y-%m-%d"),
    }

# =============================
# CSV 匯出（投標用）
# =============================

def export_csv(result: Dict, filename: str = "schedule_breakdown.csv"):
    rows = [
        ["項目", "天數"],
        ["前置作業", result["breakdown"]["pre_construction"]],
        ["地質改良", result["breakdown"]["ground_improvement"]],
        ["主體施工", result["breakdown"]["main_construction"]],
        ["消檢 / 使用執照", result["breakdown"]["completion_admin"]],
        ["總工期", result["total_days"]],
    ]

    with open(filename, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

# =============================
# 使用範例（投標估算）
# =============================

if __name__ == "__main__":
    result = calculate_schedule(
        {
            "preset": "conservative",  # conservative | normal | optimistic
            "building_type": "office",
            "structure_type": "SRC",
            "construction_method": "reverse",
            "pre_construction_type": "near_mrt",
            "ground_improvement_type": "partial",
            "completion_admin_type": "complex",
            "start_date": datetime(2025, 3, 1),
            "exclude_weekend": True,
            "exclude_cny": True,
        }
    )

    print("投標工期估算結果")
    print(result)

    export_csv(result)
    print("\n已輸出 CSV：schedule_breakdown.csv")

"""
說明：
1. 適用於政府 / 民間投標工期估算
2. CSV 可直接作為標書附件或 Excel 工期表
3. 所有參數集中於 CONFIG / PRESET，方便審核與調整
"""