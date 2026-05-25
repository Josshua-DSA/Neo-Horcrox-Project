import os
import json
from pathlib import Path
import numpy as np
import pandas as pd

# Set paths
workspace_root = Path(__file__).resolve().parent
raw_path = workspace_root / "model" / "dataset" / "raw" / "DataCoSupplyChainDataset.csv"
output_dir = workspace_root / "model" / "artifacts" / "metrics" / "supplier_selection_outputs"
output_dir.mkdir(parents=True, exist_ok=True)

print("Loading raw dataset from:", raw_path)
df = pd.read_csv(raw_path, encoding="latin1")
print("Raw dataset loaded. Shape:", df.shape)

# Create engineered features matching mlops_supplier_selection.ipynb
df_work = df.copy()
df_work["is_consumer_segment"] = (df_work["Customer Segment"].str.lower() == "consumer").astype(int)
df_work["order_row"] = 1

# Preprocessing features required
df_work["order_date"] = pd.to_datetime(df_work["order date (DateOrders)"], errors="coerce")
df_work["order_year"] = df_work["order_date"].dt.year
df_work["order_month"] = df_work["order_date"].dt.month
df_work["order_day"] = df_work["order_date"].dt.day
df_work["order_dayofweek"] = df_work["order_date"].dt.dayofweek
df_work["order_hour"] = df_work["order_date"].dt.hour
df_work["order_is_weekend"] = df_work["order_dayofweek"].isin([5, 6]).astype(int)

# Shipping speed & delays
df_work["actual_delay"] = df_work["Days for shipping (real)"] - df_work["Days for shipment (scheduled)"]
df_work["shipping_speed_ratio"] = df_work["Days for shipping (real)"] / (df_work["Days for shipment (scheduled)"] + 1e-5)
df_work["is_late"] = (df_work["actual_delay"] > 0).astype(int)
df_work["severe_delay"] = (df_work["actual_delay"] > 5).astype(int)
df_work["avg_actual_delay"] = df_work["actual_delay"]

# Financial inconsistency
df_work["calculated_item_total"] = df_work["Order Item Product Price"] * df_work["Order Item Quantity"] - df_work["Order Item Discount"]
df_work["item_total_gap"] = df_work["Order Item Total"] - df_work["calculated_item_total"]
df_work["abs_item_total_gap"] = df_work["item_total_gap"].abs()
df_work["has_price_inconsistency"] = (df_work["abs_item_total_gap"] > 1e-3).astype(int)

# Geo mismatch
df_work["country_mismatch"] = (df_work["Customer Country"] != df_work["Order Country"]).astype(int)
df_work["state_mismatch"] = (df_work["Customer State"] != df_work["Order State"]).astype(int)
df_work["city_mismatch"] = (df_work["Customer City"] != df_work["Order City"]).astype(int)

# Pricing/Margin mismatch
df_work["profit_margin"] = df_work["Order Profit Per Order"] / (df_work["Sales"] + 1e-5)
df_work["benefit_margin"] = df_work["Benefit per order"] / (df_work["Sales"] + 1e-5)
df_work["is_product_inactive"] = (df_work["Product Status"] == 0).astype(int)
df_work["high_discount_flag"] = (df_work["Order Item Discount Rate"] > 0.2).astype(int)
df_work["negative_profit_flag"] = (df_work["Order Profit Per Order"] < 0).astype(int)
df_work["negative_margin_flag"] = (df_work["Order Item Profit Ratio"] < 0).astype(int)
df_work["expected_gross_sales"] = df_work["Product Price"] * df_work["Order Item Quantity"]

# Grouping candidates
group_cols = [
    "Category Id",
    "Category Name",
    "Product Card Id",
    "Product Name",
]

print("Aggregating candidates per category...")
supplier_df = (
    df_work.groupby(group_cols)
    .agg(
        total_transactions=("order_row", "sum"),
        total_orders=("Order Id", "nunique"),
        total_quantity=("Order Item Quantity", "sum"),
        total_sales=("Sales", "sum"),
        total_profit=("Order Profit Per Order", "sum"),
        gross_purchase_cost=("expected_gross_sales", "sum"),
        total_discount=("Order Item Discount", "sum"),
        total_item_gap=("abs_item_total_gap", "sum"),
        avg_product_price=("Product Price", "mean"),
        avg_discount_rate=("Order Item Discount Rate", "mean"),
        avg_profit_margin=("profit_margin", "mean"),
        avg_benefit_margin=("benefit_margin", "mean"),
        late_rate=("is_late", "mean"),
        severe_delay_rate=("severe_delay", "mean"),
        avg_actual_delay=("actual_delay", "mean"),
        avg_shipping_speed_ratio=("shipping_speed_ratio", "mean"),
        price_inconsistency_rate=("has_price_inconsistency", "mean"),
        country_mismatch_rate=("country_mismatch", "mean"),
        state_mismatch_rate=("state_mismatch", "mean"),
        city_mismatch_rate=("city_mismatch", "mean"),
        inactive_rate=("is_product_inactive", "mean"),
        high_discount_rate=("high_discount_flag", "mean"),
        negative_profit_rate=("negative_profit_flag", "mean"),
        negative_margin_rate=("negative_margin_flag", "mean"),
        consumer_order_rate=("is_consumer_segment", "mean"),
        market_count=("Market", "nunique"),
        order_country_count=("Order Country", "nunique"),
        customer_country_count=("Customer Country", "nunique"),
    )
    .reset_index()
    .rename(
        columns={
            "Category Id": "category_id",
            "Category Name": "category_name",
            "Product Card Id": "candidate_id",
            "Product Name": "candidate_name",
        }
    )
)

supplier_df["category_total_sales"] = supplier_df.groupby("category_name")["total_sales"].transform("sum")
supplier_df["category_total_orders"] = supplier_df.groupby("category_name")["total_orders"].transform("sum")
supplier_df["category_sales_share"] = supplier_df["total_sales"] / supplier_df["category_total_sales"]
supplier_df["category_order_share"] = supplier_df["total_orders"] / supplier_df["category_total_orders"]

# Helper Normalisasi
def category_minmax_score(df, column, score_type="benefit", group_col="category_name"):
    def transform(series):
        min_value = series.min()
        max_value = series.max()
        if pd.isna(min_value) or pd.isna(max_value) or max_value == min_value:
            return pd.Series(3.0, index=series.index)
        if score_type == "benefit":
            return 1 + 4 * ((series - min_value) / (max_value - min_value))
        return 1 + 4 * ((max_value - series) / (max_value - min_value))
    return df.groupby(group_col)[column].transform(transform)

def risk_level(score):
    if score >= 4.0: return "Low"
    if score >= 3.0: return "Medium"
    if score >= 2.0: return "High"
    return "Critical"

# Screening & Prequalification
order_threshold = supplier_df.groupby("category_name")["total_orders"].transform(
    lambda series: max(5, series.quantile(0.25))
)
supplier_df["prequalified"] = (
    (supplier_df["total_orders"] >= order_threshold)
    & (supplier_df["total_sales"] > 0)
    & (supplier_df["total_quantity"] > 0)
)
supplier_df["prequalification_note"] = np.where(
    supplier_df["prequalified"],
    "Passed",
    "Failed: transaksi kategori terlalu rendah atau data sales/quantity tidak valid"
)
supplier_df["compliance_passed"] = (
    (supplier_df["price_inconsistency_rate"] <= 0.10)
    & (supplier_df["negative_margin_rate"] <= 0.85)
)
supplier_df["compliance_note"] = np.where(
    supplier_df["compliance_passed"],
    "Passed",
    "Failed: price inconsistency atau negative margin terlalu tinggi"
)

# Risk scores
print("Calculating risk scores...")
supplier_df["financial_risk_score"] = (
    0.45 * category_minmax_score(supplier_df, "avg_profit_margin", "benefit")
    + 0.35 * category_minmax_score(supplier_df, "total_profit", "benefit")
    + 0.20 * category_minmax_score(supplier_df, "negative_profit_rate", "cost")
)
supplier_df["delivery_risk_score"] = (
    0.45 * category_minmax_score(supplier_df, "late_rate", "cost")
    + 0.35 * category_minmax_score(supplier_df, "avg_actual_delay", "cost")
    + 0.20 * category_minmax_score(supplier_df, "severe_delay_rate", "cost")
)
supplier_df["quality_risk_score"] = (
    0.40 * category_minmax_score(supplier_df, "price_inconsistency_rate", "cost")
    + 0.35 * category_minmax_score(supplier_df, "negative_margin_rate", "cost")
    + 0.25 * category_minmax_score(supplier_df, "inactive_rate", "cost")
)
supplier_df["supply_disruption_risk_score"] = (
    0.35 * category_minmax_score(supplier_df, "severe_delay_rate", "cost")
    + 0.30 * category_minmax_score(supplier_df, "late_rate", "cost")
    + 0.20 * category_minmax_score(supplier_df, "total_orders", "benefit")
    + 0.15 * category_minmax_score(supplier_df, "market_count", "benefit")
)
supplier_df["geographical_risk_score"] = (
    0.40 * category_minmax_score(supplier_df, "country_mismatch_rate", "cost")
    + 0.30 * category_minmax_score(supplier_df, "state_mismatch_rate", "cost")
    + 0.30 * category_minmax_score(supplier_df, "city_mismatch_rate", "cost")
)
supplier_df["compliance_risk_score"] = (
    0.45 * category_minmax_score(supplier_df, "price_inconsistency_rate", "cost")
    + 0.30 * category_minmax_score(supplier_df, "high_discount_rate", "cost")
    + 0.25 * category_minmax_score(supplier_df, "inactive_rate", "cost")
)
supplier_df["consumer_fit_score"] = (
    0.60 * category_minmax_score(supplier_df, "consumer_order_rate", "benefit")
    + 0.40 * category_minmax_score(supplier_df, "category_order_share", "benefit")
)
supplier_df["cyber_data_risk_score"] = 3.0

risk_weights = {
    "financial_risk_score": 0.18,
    "delivery_risk_score": 0.20,
    "quality_risk_score": 0.20,
    "supply_disruption_risk_score": 0.14,
    "geographical_risk_score": 0.08,
    "compliance_risk_score": 0.10,
    "consumer_fit_score": 0.05,
    "cyber_data_risk_score": 0.05,
}

supplier_df["risk_score"] = sum(
    supplier_df[column] * weight for column, weight in risk_weights.items()
).round(4)
supplier_df["risk_level"] = supplier_df["risk_score"].apply(risk_level)

# TCO
supplier_df["delay_penalty"] = (
    supplier_df["total_sales"]
    * supplier_df["late_rate"]
    * supplier_df["avg_actual_delay"].clip(lower=0)
    * 0.01
)
supplier_df["quality_penalty"] = (
    supplier_df["total_item_gap"]
    + supplier_df["total_sales"] * supplier_df["price_inconsistency_rate"] * 0.02
    + supplier_df["total_sales"] * supplier_df["negative_margin_rate"] * 0.02
)
supplier_df["discount_penalty"] = supplier_df["total_discount"] * 0.10
supplier_df["tco"] = (
    supplier_df["gross_purchase_cost"]
    + supplier_df["delay_penalty"]
    + supplier_df["quality_penalty"]
    + supplier_df["discount_penalty"]
).round(2)

# Criteria config & weights
criteria = [
    {"name": "Cost", "column": "tco", "type": "cost"},
    {"name": "Profitability", "column": "avg_profit_margin", "type": "benefit"},
    {"name": "Delivery", "column": "delivery_risk_score", "type": "benefit"},
    {"name": "Quality", "column": "quality_risk_score", "type": "benefit"},
    {"name": "Risk", "column": "risk_score", "type": "benefit"},
    {"name": "Demand", "column": "category_order_share", "type": "benefit"},
    {"name": "Consumer Fit", "column": "consumer_fit_score", "type": "benefit"},
]

criteria_names = [item["name"] for item in criteria]
target_weights = {
    "Cost": 0.18,
    "Profitability": 0.17,
    "Delivery": 0.18,
    "Quality": 0.16,
    "Risk": 0.14,
    "Demand": 0.10,
    "Consumer Fit": 0.07,
}

base_weights = np.array([target_weights[name] for name in criteria_names])
ahp_pairwise_matrix = base_weights[:, None] / base_weights[None, :]
eigenvalues, eigenvectors = np.linalg.eig(ahp_pairwise_matrix)
max_index = np.argmax(eigenvalues.real)
lambda_max = eigenvalues[max_index].real
ahp_weights_array = np.abs(eigenvectors[:, max_index].real)
ahp_weights_array = ahp_weights_array / ahp_weights_array.sum()
ahp_weights = dict(zip(criteria_names, ahp_weights_array.round(6)))

ahp_weight_table = pd.DataFrame({
    "criteria": criteria_names,
    "weight": ahp_weights_array.round(6)
})

# TOPSIS
def get_matrix(data, criteria_config):
    return data[[item["column"] for item in criteria_config]].astype(float).to_numpy()

def topsis_one_group(data, criteria_config, weights):
    result = data.copy()
    if len(result) == 1:
        result["topsis_score"] = 1.0
        result["topsis_rank"] = 1
        return result
    matrix = get_matrix(result, criteria_config)
    weight_vector = np.array([weights[item["name"]] for item in criteria_config])
    denominator = np.sqrt((matrix ** 2).sum(axis=0))
    denominator[denominator == 0] = 1
    weighted_matrix = (matrix / denominator) * weight_vector
    ideal_best = []
    ideal_worst = []
    for idx, item in enumerate(criteria_config):
        values = weighted_matrix[:, idx]
        if item["type"] == "benefit":
            ideal_best.append(values.max())
            ideal_worst.append(values.min())
        else:
            ideal_best.append(values.min())
            ideal_worst.append(values.max())
    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)
    distance_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    distance_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))
    denominator_score = distance_best + distance_worst
    result["topsis_score"] = np.where(
        denominator_score == 0,
        1.0,
        distance_worst / denominator_score,
    )
    result["topsis_score"] = result["topsis_score"].round(6)
    result["topsis_rank"] = result["topsis_score"].rank(ascending=False, method="dense").astype(int)
    return result

# VIKOR
def vikor_one_group(data, criteria_config, weights, v=0.5):
    result = data.copy()
    if len(result) == 1:
        result["vikor_s"] = 0.0
        result["vikor_r"] = 0.0
        result["vikor_q"] = 0.0
        result["vikor_rank"] = 1
        return result
    matrix = get_matrix(result, criteria_config)
    weight_vector = np.array([weights[item["name"]] for item in criteria_config])
    weighted_regret = np.zeros_like(matrix, dtype=float)
    for idx, item in enumerate(criteria_config):
        values = matrix[:, idx]
        if item["type"] == "benefit":
            best = values.max()
            worst = values.min()
            denominator = best - worst
            regret = np.zeros(len(values)) if denominator == 0 else (best - values) / denominator
        else:
            best = values.min()
            worst = values.max()
            denominator = worst - best
            regret = np.zeros(len(values)) if denominator == 0 else (values - best) / denominator
        weighted_regret[:, idx] = regret * weight_vector[idx]
    s_values = weighted_regret.sum(axis=1)
    r_values = weighted_regret.max(axis=1)
    s_best, s_worst = s_values.min(), s_values.max()
    r_best, r_worst = r_values.min(), r_values.max()
    s_term = np.zeros(len(s_values)) if s_worst == s_best else (s_values - s_best) / (s_worst - s_best)
    r_term = np.zeros(len(r_values)) if r_worst == r_best else (r_values - r_best) / (r_worst - r_best)
    q_values = (v * s_term) + ((1 - v) * r_term)
    result["vikor_s"] = s_values.round(6)
    result["vikor_r"] = r_values.round(6)
    result["vikor_q"] = q_values.round(6)
    result["vikor_rank"] = result["vikor_q"].rank(ascending=True, method="dense").astype(int)
    return result

# Running ranking per category
print("Running TOPSIS & VIKOR per category...")
ranked_groups = []
for category_name, group in supplier_df.groupby("category_name", sort=False):
    ranked_group = topsis_one_group(group, criteria, ahp_weights)
    ranked_group = vikor_one_group(ranked_group, criteria, ahp_weights)
    ranked_groups.append(ranked_group)

ranking_df = pd.concat(ranked_groups, ignore_index=True)

ranking_df["average_rank"] = (
    ranking_df["topsis_rank"] + ranking_df["vikor_rank"]
) / 2
ranking_df["final_rank_in_category"] = ranking_df.groupby("category_name")["average_rank"].rank(
    ascending=True,
    method="dense",
).astype(int)

def recommendation(row):
    if not row["prequalified"]:
        return "Rejected - Not Prequalified"
    if not row["compliance_passed"]:
        return "Rejected - Compliance Risk"
    if row["risk_level"] == "Critical":
        return "Not Recommended"
    if row["risk_level"] == "High":
        return "Conditional Supplier"
    if row["final_rank_in_category"] == 1:
        return "Primary Supplier"
    if row["final_rank_in_category"] <= 3:
        return "Backup Supplier"
    return "Not Priority"

ranking_df["recommendation"] = ranking_df.apply(recommendation, axis=1)

final_result = ranking_df.sort_values(
    ["category_name", "final_rank_in_category", "average_rank", "candidate_name"]
).reset_index(drop=True)

# Select primary per category
primary_per_category = (
    final_result[~final_result["recommendation"].str.contains("Rejected")]
    .sort_values(["category_name", "final_rank_in_category", "risk_score"], ascending=[True, True, False])
    .groupby("category_name")
    .head(1)
    .reset_index(drop=True)
)

# Export
print("Saving output files to:", output_dir)
final_result.to_csv(output_dir / "supplier_selection_by_category_full_result.csv", index=False)
primary_per_category.to_csv(output_dir / "supplier_selection_primary_per_category.csv", index=False)
ahp_weight_table.to_csv(output_dir / "supplier_selection_ahp_weights.csv", index=False)

RI_TABLE = {1:0.0, 2:0.0, 3:0.58, 4:0.90, 5:1.12, 6:1.24, 7:1.32, 8:1.41, 9:1.45, 10:1.49}
n = ahp_pairwise_matrix.shape[0]
ci = (lambda_max - n) / (n - 1)
ri = RI_TABLE[n]
cr = ci / ri if ri != 0 else 0.0
cr = 0.0 if abs(cr) < 1e-12 else cr

summary = {
    "total_categories": int(final_result["category_name"].nunique()),
    "total_candidates": int(len(final_result)),
    "prequalified_candidates": int(final_result["prequalified"].sum()),
    "compliance_passed_candidates": int(final_result["compliance_passed"].sum()),
    "ahp_consistency_ratio": float(round(cr, 6)),
    "output_files": [
        "supplier_selection_by_category_full_result.csv",
        "supplier_selection_primary_per_category.csv",
        "supplier_selection_ahp_weights.csv",
    ],
}

with open(output_dir / "supplier_selection_by_category_summary.json", "w", encoding="utf-8") as file:
    json.dump(summary, file, indent=2)

print("Supplier selection metrics successfully generated!")
print(summary)
