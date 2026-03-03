# 👉 讀 OBD-II CSV
# 👉 清洗數據
# 👉 插值補 missing
# 👉 過濾異常值
# 👉 計算 L/100km
# 👉 儲存 cleaned CSV
# 👉 合併成一個總 
import pandas as pd
import glob
import os

print(f"Current working directory: {os.getcwd()}")

# Path to your dataset folder (note nested folder in this repo)
DATA_PATH = "10.35097-1130/10.35097-1130/data/dataset/OBD-II-Dataset/OBD-II-Dataset/*.csv"
print(f"Looking for files at: {DATA_PATH}")
print(f"Files found: {len(glob.glob(DATA_PATH))}")

# Constants
AFR = 14.7          # Air-Fuel Ratio for petrol
FUEL_DENSITY = 745  # g/L

COLUMN_CANDIDATES = {
    "RPM": ["Engine RPM [RPM]", "RPM"],
    "Speed": ["Vehicle Speed Sensor [km/h]", "Speed", "Speed [km/h]"],
    "MAF": ["Air Flow Rate from Mass Flow Sensor [g/s]", "MAF", "Mass Air Flow [g/s]"],
    "Throttle": ["Absolute Throttle Position [%]", "Throttle"]
}


def estimate_fuel_l_per_100km(maf, speed):
    """Estimate fuel consumption in L/100km"""
    try:
        if speed <= 0 or maf <= 0:
            return 0.0
    except Exception:
        return 0.0
    fuel_rate_lps = maf / (AFR * FUEL_DENSITY)  # L/s
    fuel_lph = fuel_rate_lps * 3600             # L/h
    return (fuel_lph / speed) * 100


def find_and_rename(df):
    rename_map = {}
    for canon, candidates in COLUMN_CANDIDATES.items():
        for c in candidates:
            if c in df.columns:
                rename_map[c] = canon
                break
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def main():
    all_trips = []
    cleaned_dir = "10.35097-1130/cleaned_trips"
    os.makedirs(cleaned_dir, exist_ok=True)

    summary = {"files_processed": 0, "rows_before": 0, "rows_after": 0}

    for file in glob.glob(DATA_PATH):
        try:
            summary["files_processed"] += 1
            df = pd.read_csv(file)

            df = find_and_rename(df)

            # Ensure numeric columns exist before coercion
            for col in ["RPM", "Speed", "MAF"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            initial_rows = len(df)
            summary["rows_before"] += initial_rows

            # Require at least Speed and MAF to estimate fuel; RPM optional
            if not {"Speed", "MAF"}.issubset(set(df.columns)):
                print(f"Skipping {os.path.basename(file)}: required columns missing")
                continue

            # Interpolate small gaps (limit consecutive NaNs)
            cols_to_interp = [c for c in ["Speed", "MAF", "RPM"] if c in df.columns]
            if cols_to_interp:
                df[cols_to_interp] = df[cols_to_interp].interpolate(method="linear", limit=5, limit_direction="both")

            # Drop rows where Speed or MAF are missing after interpolation
            df = df.dropna(subset=["Speed", "MAF"])

            # Remove duplicates
            df = df.drop_duplicates()

            # Filter unrealistic values
            df = df[df["Speed"].between(0, 250)]
            if "RPM" in df.columns:
                df = df[df["RPM"].between(0, 10000)]
            df = df[df["MAF"].between(0.0, 500.0)]

            # Recount
            cleaned_rows = len(df)
            summary["rows_after"] += cleaned_rows

            # Compute fuel estimate
            df["Fuel_L_per_100km"] = df.apply(lambda row: estimate_fuel_l_per_100km(row["MAF"], row["Speed"]), axis=1)

            # Add trip name and save per-trip cleaned CSV
            trip_name = os.path.basename(file)
            df["Trip"] = trip_name
            out_path = os.path.join(cleaned_dir, trip_name)
            df.to_csv(out_path.replace('.csv', '_cleaned.csv'), index=False)

            all_trips.append(df)
        except Exception as e:
            print(f"Error processing {file}: {str(e)}")
            continue

    if all_trips:
        final_df = pd.concat(all_trips, ignore_index=True)
        out_combined = "10.35097-1130/cleaned_data.csv"
        final_df.to_csv(out_combined, index=False)
        print(f"Cleaned data saved to {out_combined}")
        print(f"Files processed: {summary['files_processed']}")
        print(f"Rows before: {summary['rows_before']}, after: {summary['rows_after']}")
        print(final_df.head())
    else:
        print("No trips processed. Check DATA_PATH and CSV files.")


if __name__ == '__main__':
    main()



# 好 👌 我用好清晰、technical 但易明嘅方式答你：

# 你呢個 program **實際上會計算同分析啲咩？**

# 我會分成兩部分講：

# 1️⃣ 它「真正計算」咗啲咩
# 2️⃣ 它「實際分析能力」去到邊個程度

# ---

# # 🔵 一、佢真正計算咗啲咩？

# ## 1️⃣ 讀取所有 OBD-II CSV

# ```python
# glob.glob(DATA_PATH)
# ```

# 👉 讀取資料夾入面每一個行車紀錄檔
# 👉 每一個 file 當作一個 trip

# ---

# ## 2️⃣ 數據清洗 (Data Cleaning)

# 佢會做：

# ### ✅ 統一欄位名稱

# 例如：

# * "Engine RPM [RPM]" → "RPM"
# * "Speed [km/h]" → "Speed"

# ---

# ### ✅ 轉成數字

# ```python
# pd.to_numeric(errors="coerce")
# ```

# 無效數字變 NaN。

# ---

# ### ✅ 線性插值補小量 missing

# ```python
# interpolate(limit=5)
# ```

# 補最多 5 行連續空值。

# ---

# ### ✅ 刪除仍然 missing 行

# ```python
# dropna(subset=["Speed","MAF"])
# ```

# ---

# ### ✅ 刪除重複行

# ```python
# drop_duplicates()
# ```

# ---

# ### ✅ 過濾不合理數值

# | 變數    | 範圍         |
# | ----- | ---------- |
# | Speed | 0–250 km/h |
# | RPM   | 0–10000    |
# | MAF   | 0–500 g/s  |

# 👉 防止 sensor error 影響計算。

# ---

# # 🔵 二、佢真正「計算」咗咩？

# ## ⭐ 唯一真正計算出嚟嘅新指標：

# # 👉 Fuel_L_per_100km（瞬時油耗）

# 用公式：

# [
# Fuel = \frac{MAF}{AFR × FuelDensity}
# ]

# 步驟：

# 1️⃣ MAF (g/s) → 計 fuel 流量 (L/s)
# 2️⃣ 轉成 L/h
# 3️⃣ 用車速轉成 L/100km

# ---

# ## 每一行會變成：

# | Speed | MAF | Fuel_L_per_100km |
# | ----- | --- | ---------------- |
# | 60    | 12  | 5.8              |
# | 80    | 18  | 6.3              |
# | 40    | 15  | 9.2              |

# 👉 呢個係「即時油耗」

# ⚠ 注意：
# 呢個唔係整個 trip 總油耗
# 只係每秒嘅瞬時估算。

# ---

# # 🔵 三、佢有冇真正分析駕駛行為？

# ❌ 冇。

# 你而家呢個版本：

# 冇做：

# * High RPM detection
# * Harsh acceleration
# * Hard braking
# * Efficiency scoring
# * Trip-level behaviour analysis

# ---

# # 🔵 四、佢最終輸出咗咩？

# ### 1️⃣ 每個 trip cleaned CSV

# 包括：

# * RPM
# * Speed
# * MAF
# * Fuel_L_per_100km
# * Trip name

# ---

# ### 2️⃣ 一個總 dataset

# ```python
# final_df = pd.concat(all_trips)
# ```

# 👉 把所有 trip 疊埋
# 👉 變成 cleaned_data.csv

# ---

# ### 3️⃣ Summary statistics

# ```python
# Files processed
# Rows before
# Rows after
# ```

# 👉 只係基本數據量統計。

# ---

# # 🔵 五、所以你個 program 「真正分析能力」去到邊？

# 目前等級：

# ## Level 1 – Data Preprocessing + Fuel Estimation

# ✔ 數據清洗
# ✔ 基本油耗估算
# ✔ 整合 dataset

# 但未到：

# ## Level 2 – Driving Behaviour Analysis

# 冇：

# * 加速模式分析
# * RPM pattern
# * 油門使用模式
# * 制動模式
# * 效率分數

# ---

# # 🔵 六、佢實際可以俾你做咩分析？

# 因為你有 Fuel_L_per_100km

# 你可以之後做：

# * 計平均油耗
# * 畫油耗趨勢圖
# * 分析速度 vs 油耗關係
# * 分析 RPM vs 油耗

# 但而家個 code 本身未自動做呢啲。

# ---

# # 🔵 七、用一句話總結

# 你呢個程式：

# 👉 將原始 OBD-II 數據轉換成「乾淨 + 有油耗指標」嘅 dataset。

# 但未真正做：

# 👉 駕駛效率分析
# 👉 不良駕駛識別
# 👉 AI coaching

# ---

# # 🔥 如果對照你 Project Requirement：

# ### Must:

# ✔ Estimate fuel usage → ✅ 做咗

# ### Should:

# ❌ Visualize efficiency → 未做
# ❌ Trip feedback → 未做

# ### Could:

# ❌ Strategy advice → 未做

# ### Won’t:

# ✔ 冇 interactive Q&A → 正確

# ---

# # 🚀 如果你想升級到「真正分析」

# 下一步應該加：

# ```python
# high_rpm_events
# harsh_acceleration
# hard_braking
# trip_average_fuel
# efficiency_score
# ```

# ---

# # 🎯 超重要現實提醒

# 你而家計嘅：

# ```python
# df.apply(...)
# ```

# 係逐行計瞬時油耗。

# 但真正專業計整個 trip 油耗應該：

# * 積分 fuel rate over time
# * 積分距離
# * 再計整個 trip L/100km

# 呢個會準好多。

# ---

# 如果你想，我可以幫你：

# 1️⃣ 解釋你而家 fuel estimation 準唔準
# 2️⃣ 幫你升級成真正 trip fuel calculation
# 3️⃣ 幫你畫圖解釋數據流

# 你而家其實只差一層 analysis layer 👌
