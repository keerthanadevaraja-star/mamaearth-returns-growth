"""
Part 2 — Python/Pandas Data Wrangling & EDA

"""

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")


def banner(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    # ------------------------------------------------------------------
    # Task 1 — Load and inspect
    # ------------------------------------------------------------------
    banner("Task 1 — Load and inspect")
    orders = pd.read_csv(os.path.join(DATA, "orders.csv"))
    customers = pd.read_csv(os.path.join(DATA, "customers.csv"))
    products = pd.read_csv(os.path.join(DATA, "products.csv"))
    print("orders.shape  :", orders.shape)      # (180, 9)
    print("customers.shape:", customers.shape)   # (45, 6)
    print("products.shape :", products.shape)    # (16, 4)
    assert orders.shape == (180, 9)

    # ------------------------------------------------------------------
    # Task 2 — Standardize payment_method casing
    # ------------------------------------------------------------------
    banner("Task 2 — Standardize payment_method casing")
    raw_methods = sorted(orders["payment_method"].unique().tolist())
    print("Raw distinct payment_method values (", len(raw_methods), "):", raw_methods)
    orders["payment_method"] = orders["payment_method"].str.strip().str.upper()
    clean_counts = orders["payment_method"].value_counts()
    print("Cleaned distinct values (", orders["payment_method"].nunique(), "):")
    print(clean_counts.to_string())
    assert orders["payment_method"].nunique() == 3

    # ------------------------------------------------------------------
    # Task 3 — Remove duplicate orders
    # ------------------------------------------------------------------
    banner("Task 3 — Remove duplicate orders")
    natural_key = [
        "customer_id", "product_id", "order_date", "quantity",
        "discount_pct", "payment_method", "rating", "returned",
    ]
    dup_mask = orders.duplicated(subset=natural_key, keep="first")
    dropped_ids = orders.loc[dup_mask, "order_id"].tolist()
    print("Duplicate rows flagged:", int(dup_mask.sum()))
    print("Dropped order_id values:", dropped_ids)
    orders_clean = orders.loc[~dup_mask].copy()
    print("orders_clean.shape:", orders_clean.shape)   # (175, 9)
    assert orders_clean.shape == (175, 9)
    assert dropped_ids == ["O0176", "O0177", "O0178", "O0179", "O0180"]

    # ------------------------------------------------------------------
    # Task 4 — Impute missing values (on the deduplicated frame)
    # ------------------------------------------------------------------
    banner("Task 4 — Impute missing values")
    disc_missing = int(orders_clean["discount_pct"].isnull().sum())
    print("discount_pct NaN before impute:", disc_missing)
    orders_clean["discount_pct"] = orders_clean["discount_pct"].fillna(0)

    rating_median = orders_clean["rating"].median()
    rating_missing = int(orders_clean["rating"].isnull().sum())
    print("rating median (non-null):", rating_median)
    print("rating NaN before impute:", rating_missing)
    orders_clean["rating"] = orders_clean["rating"].fillna(rating_median)

    print("Null counts after impute:")
    print(orders_clean[["discount_pct", "rating"]].isnull().sum().to_string())
    assert disc_missing == 12
    assert rating_median == 3.0
    assert rating_missing == 15
    assert orders_clean[["discount_pct", "rating"]].isnull().sum().sum() == 0

    # ------------------------------------------------------------------
    # Task 5 — Merge and reconcile against Part 1
    # ------------------------------------------------------------------
    banner("Task 5 — Merge and reconcile against Part 1")
    merged = orders_clean.merge(products, on="product_id", how="left").merge(
        customers, on="customer_id", how="left"
    )
    merged["order_value"] = (
        merged["quantity"] * merged["price"] * (1 - merged["discount_pct"] / 100)
    )
    cleaned_total = round(merged["order_value"].sum(), 2)
    raw_total = 99860.20
    delta = round(raw_total - cleaned_total, 2)
    print("Cleaned total order_value (175 rows): %.2f" % cleaned_total)
    print("Part 1 raw total order_value (180 rows): %.2f" % raw_total)
    print("Delta: %.2f" % delta)

    # Independent check: value of the 5 dropped duplicate rows.
    dropped = orders.loc[dup_mask].copy()
    dropped["discount_pct"] = dropped["discount_pct"].fillna(0)
    dropped = dropped.merge(products, on="product_id", how="left")
    dropped_value = round(
        (dropped["quantity"] * dropped["price"] * (1 - dropped["discount_pct"] / 100)).sum(),
        2,
    )
    print("Independent sum of the 5 dropped duplicate rows' order_value: %.2f" % dropped_value)
    print(
        "\nRECONCILIATION NOTE: The cleaned revenue of Rs %.2f is exactly Rs %.2f "
        "lower than Part 1's raw total of Rs %.2f. This entire delta is attributable "
        "to the 5 exact-duplicate orders (O0176-O0180) removed in Task 3, whose "
        "combined order_value is Rs %.2f (verified independently above). The missing-"
        "value imputation in Task 4 does NOT change any order_value total: filling a "
        "blank discount with 0%% leaves revenue identical (it was already treated as "
        "0%% via COALESCE in Part 1), and rating imputation touches no monetary field."
        % (cleaned_total, delta, raw_total, dropped_value)
    )
    assert cleaned_total == 97358.30
    assert delta == 2501.90
    assert dropped_value == 2501.90

    # ------------------------------------------------------------------
    # Task 6 — IQR outlier detection on quantity
    # ------------------------------------------------------------------
    banner("Task 6 — IQR outlier detection on quantity")
    q1 = merged["quantity"].quantile(0.25)
    q3 = merged["quantity"].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    print(f"Q1={q1}, Q3={q3}, IQR={iqr}, lower={lower}, upper={upper}")
    merged["is_outlier"] = (merged["quantity"] < lower) | (merged["quantity"] > upper)
    outliers = merged.loc[merged["is_outlier"], ["order_id", "quantity"]]
    print("Outlier rows (flagged, NOT dropped):")
    print(outliers.to_string(index=False))
    assert (q1, q3, iqr, lower, upper) == (1.0, 2.0, 1.0, -0.5, 3.5)
    assert set(outliers["order_id"]) == {"O0011", "O0098"}

    # ------------------------------------------------------------------
    # Task 7 — Hypothesis: does COD have a higher return rate?
    # ------------------------------------------------------------------
    banner("Task 7 — Hypothesis: does COD have a higher return rate?")
    print("Hypothesis: Cash-on-Delivery (COD) orders are returned at a higher rate "
          "than prepaid (CARD/UPI) orders.")
    pay = merged.groupby("payment_method")["returned"].agg(["count", "mean"])
    pay["return_rate_pct"] = (pay["mean"] * 100).round(1)
    print(pay.to_string())
    rates = pay["return_rate_pct"].to_dict()
    print("Return rates -> CARD: %.1f%%, COD: %.1f%%, UPI: %.1f%%"
          % (rates["CARD"], rates["COD"], rates["UPI"]))
    cod_confirmed = rates["COD"] > max(rates["CARD"], rates["UPI"])
    print("Hypothesis verdict:", "Confirmed" if cod_confirmed else "Rejected")
    assert rates == {"CARD": 14.7, "COD": 44.4, "UPI": 18.9}
    assert cod_confirmed

    # ------------------------------------------------------------------
    # Task 8 — Multi-level segmentation
    # ------------------------------------------------------------------
    banner("Task 8 — Multi-level segmentation (payment_method x city_tier)")
    seg = merged.groupby(["payment_method", "city_tier"])["returned"].agg(["count", "mean"])
    seg["return_rate_pct"] = (seg["mean"] * 100).round(1)
    print(seg.to_string())
    top_seg = seg["return_rate_pct"].idxmax()
    top_val = seg["return_rate_pct"].max()
    print(f"\nHighest-risk segment: payment_method={top_seg[0]}, city_tier={top_seg[1]}, "
          f"return_rate={top_val}%")
    print("COD risk is NOT uniform across tiers: Tier-1 COD = %.1f%% vs Tier-2 COD = %.1f%%."
          % (seg.loc[("COD", 1), "return_rate_pct"], seg.loc[("COD", 2), "return_rate_pct"]))
    assert top_seg == ("COD", 2)
    assert top_val == 54.5
    assert seg.loc[("COD", 1), "return_rate_pct"] == 37.5

    # ------------------------------------------------------------------
    # Task 9 — Correlation analysis
    # ------------------------------------------------------------------
    banner("Task 9 — Correlation analysis")
    corr = merged[["rating", "returned", "discount_pct", "quantity"]].corr()
    print(corr.round(3).to_string())

    def band(r):
        a = abs(r)
        if a < 0.2:
            return "negligible"
        if a < 0.4:
            return "weak"
        if a < 0.7:
            return "moderate"
        return "strong"

    print("\nPairwise strength bands:")
    cols = ["rating", "returned", "discount_pct", "quantity"]
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r = corr.loc[cols[i], cols[j]]
            print(f"  {cols[i]} vs {cols[j]}: r={r:+.3f} -> {band(r)}")
            assert band(r) == "negligible"
    disc_ret = corr.loc["discount_pct", "returned"]
    print('\nHypothesis "higher discounts reduce returns": BUSTED '
          f"(discount_pct vs returned r={disc_ret:+.2f}, negligible).")

    # ------------------------------------------------------------------
    # Task 10 — Outlier-corrected time series
    # ------------------------------------------------------------------
    banner("Task 10 — Outlier-corrected monthly revenue")
    merged["order_date"] = pd.to_datetime(merged["order_date"])
    merged["year_month"] = merged["order_date"].dt.strftime("%Y-%m")

    monthly_all = merged.groupby("year_month")["order_value"].sum().round(2)
    monthly_corrected = (
        merged.loc[~merged["is_outlier"]].groupby("year_month")["order_value"].sum().round(2)
    )
    print("(1) Monthly revenue INCLUDING outliers:")
    print(monthly_all.to_string())
    print("\n(2) Monthly revenue EXCLUDING the 2 bulk outliers:")
    print(monthly_corrected.to_string())

    peak_all = monthly_all.idxmax()
    peak_corrected = monthly_corrected.idxmax()
    print(f"\nApparent peak (with outliers): {peak_all} = {monthly_all.max():.2f}")
    print(f"True peak (corrected):          {peak_corrected} = {monthly_corrected.max():.2f}")
    print("January's apparent lead is an ARTIFACT of two bulk orders landing in Jan "
          "(O0011 on 2026-01-28 qty 25, O0098 on 2026-01-10 qty 30). Once excluded, "
          "March 2026 is the genuine peak month. This is why Task 6 must precede Task 10.")
    assert peak_all == "2026-01"
    assert monthly_all.loc["2026-01"] == 29582.10
    assert peak_corrected == "2026-03"
    assert monthly_corrected.loc["2026-03"] == 20318.90
    assert monthly_corrected.loc["2026-01"] == 11637.10

    # ------------------------------------------------------------------
    # Export verified figures -> narrator/findings.json (Part 3, Task 1)
    # ------------------------------------------------------------------
    banner("Export -> narrator/findings.json")
    findings = {
        "cleaned_total_revenue_inr": cleaned_total,
        "raw_total_revenue_inr": raw_total,
        "duplicate_reconciliation_delta_inr": delta,
        "return_rate_by_payment": {
            "COD": rates["COD"],
            "CARD": rates["CARD"],
            "UPI": rates["UPI"],
        },
        "highest_risk_segment": {
            "payment_method": top_seg[0],
            "city_tier": int(top_seg[1]),
            "return_rate_pct": float(top_val),
        },
        "true_peak_month": {
            "month": peak_corrected,
            "revenue_inr": float(monthly_corrected.max()),
        },
        "outlier_inflated_month": {
            "month": peak_all,
            "apparent_revenue_inr": float(monthly_all.loc["2026-01"]),
            "corrected_revenue_inr": float(monthly_corrected.loc["2026-01"]),
        },
    }
    narrator_dir = os.path.join(ROOT, "narrator")
    os.makedirs(narrator_dir, exist_ok=True)
    with open(os.path.join(narrator_dir, "findings.json"), "w", encoding="utf-8") as fh:
        json.dump(findings, fh, indent=2)
    print("Wrote narrator/findings.json:")
    print(json.dumps(findings, indent=2))

    print("\nAll assertions passed. Pipeline reproduced every number in the brief.")
    return merged


if __name__ == "__main__":
    main()
