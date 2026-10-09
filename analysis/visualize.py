"""
Part 2, Task 11 — Two visualizations
Run AFTER clean_and_eda.py (it reuses the same deterministic pipeline):
    python analysis/visualize.py

Saves:
    visualizations/return_rate_by_payment.png
    visualizations/monthly_revenue_trend.png
"""

import os

import matplotlib

matplotlib.use("Agg")  # headless / re-runnable, no display needed
import matplotlib.pyplot as plt

from clean_and_eda import main as build_merged

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "visualizations")


def main():
    os.makedirs(OUT, exist_ok=True)
    merged = build_merged()

    # --- Chart 1: return rate by payment method (descending) ---------------
    pay = merged.groupby("payment_method")["returned"].mean().mul(100).round(1)
    pay = pay.sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(pay.index, pay.values, color=["#c0392b", "#e67e22", "#27ae60"])
    for bar, val in zip(bars, pay.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.6, f"{val:.1f}%",
                ha="center", va="bottom", fontweight="bold")
    ax.set_title("COD Returns at 44.4% - 3x Card")
    ax.set_xlabel("Payment method")
    ax.set_ylabel("Return rate (%)")
    ax.set_ylim(0, max(pay.values) + 8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "return_rate_by_payment.png"), dpi=120)
    plt.close(fig)

    # --- Chart 2: outlier-corrected monthly revenue trend ------------------
    monthly = (
        merged.loc[~merged["is_outlier"]]
        .groupby("year_month")["order_value"].sum().round(2).sort_index()
    )
    peak_month = monthly.idxmax()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(monthly.index, monthly.values, marker="o", color="#2980b9", linewidth=2)
    ax.annotate(f"Peak: {peak_month}\n{monthly.max():,.2f}",
                xy=(peak_month, monthly.max()),
                xytext=(0, 18), textcoords="offset points",
                ha="center", fontweight="bold",
                arrowprops=dict(arrowstyle="->"))
    ax.set_title(f"Outlier-Corrected Monthly Revenue - Peak Month: {peak_month} (March)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (INR)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "monthly_revenue_trend.png"), dpi=120)
    plt.close(fig)

    print("Saved:")
    print("  visualizations/return_rate_by_payment.png")
    print("  visualizations/monthly_revenue_trend.png")


if __name__ == "__main__":
    main()
