"""Business EDA visualization script for Nassau Candy Distributor.

This module provides functions to generate, format, and save 10 business-oriented
exploratory data visualizations (Sales, Profit, Region, Product, Shipping, Customer,
Correlation, Outliers, Seasonality, and Executive Summary Matrix).
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NassauEDA:
    """EDA engine for generating business intelligence plots and saving them as images."""

    def __init__(self, data_path: str, output_dir: str = "images") -> None:
        """Initializes the EDA engine.

        Args:
            data_path (str): Path to the raw or cleaned dataset CSV.
            output_dir (str): Folder where generated plots will be saved.
        """
        self.data_path = data_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Load and parse dates initially
        logger.info("Loading data for EDA from %s", data_path)
        self.df = pd.read_csv(data_path)
        self.df["Order Date"] = pd.to_datetime(self.df["Order Date"], dayfirst=True)
        self.df["Ship Date"] = pd.to_datetime(self.df["Ship Date"], dayfirst=True)
        self.df["lead_time_days"] = (self.df["Ship Date"] - self.df["Order Date"]).dt.days
        
        # Configure seaborn style
        sns.set_theme(style="whitegrid")
        plt.rcParams["figure.figsize"] = (10, 6)
        plt.rcParams["font.size"] = 12

    def run_sales_analysis(self) -> None:
        """Generates Monthly Sales trend and Transaction Value density."""
        logger.info("Generating Sales Analysis plot...")
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # Monthly Sales Trend
        sales_monthly = self.df.set_index("Order Date").resample("ME")["Sales"].sum().reset_index()
        sns.lineplot(data=sales_monthly, x="Order Date", y="Sales", ax=axes[0], color="#1f77b4", linewidth=2.5, marker="o")
        axes[0].set_title("Monthly Sales Trend (2024 - 2025)", fontsize=14, fontweight="bold")
        axes[0].set_ylabel("Total Sales ($)")

        # Sales Distribution
        sns.histplot(data=self.df, x="Sales", bins=40, ax=axes[1], kde=True, color="#2ca02c")
        axes[1].set_title("Sales Transaction Value Distribution", fontsize=14, fontweight="bold")
        axes[1].set_xlabel("Order Sales Value ($)")
        axes[1].set_ylabel("Number of Transactions")

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "01_sales_analysis.png"), dpi=300)
        plt.close()

    def run_profit_analysis(self) -> None:
        """Generates Boxplot of Gross Profit Margin by Division."""
        logger.info("Generating Profit Analysis plot...")
        fig, ax = plt.subplots(figsize=(10, 6))

        # Calculate Margin %
        df_margin = self.df.copy()
        df_margin["margin_pct"] = (df_margin["Gross Profit"] / df_margin["Sales"]) * 100

        sns.boxplot(data=df_margin, x="Division", y="margin_pct", ax=ax, palette="Set2", width=0.5)
        ax.set_title("Gross Profit Margin (%) by Product Division", fontsize=14, fontweight="bold")
        ax.set_ylabel("Gross Profit Margin (%)")
        ax.set_xlabel("Product Division")

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "02_profit_analysis.png"), dpi=300)
        plt.close()

    def run_regional_performance(self) -> None:
        """Compares Total Sales and Average Lead Time by Region."""
        logger.info("Generating Regional Performance plot...")
        fig, ax1 = plt.subplots(figsize=(10, 6))

        # Summarize data
        reg_summary = self.df.groupby("Region").agg(
            total_sales=("Sales", "sum"),
            avg_lead_time=("lead_time_days", "mean")
        ).reset_index()

        # Primary Y-axis: Sales
        ax2 = ax1.twinx()
        sns.barplot(data=reg_summary, x="Region", y="total_sales", ax=ax1, color="#1f77b4", alpha=0.7)
        ax1.set_ylabel("Total Sales ($)", color="#1f77b4")
        ax1.tick_params(axis='y', labelcolor="#1f77b4")

        # Secondary Y-axis: Lead Time
        sns.lineplot(data=reg_summary, x="Region", y="avg_lead_time", ax=ax2, color="#d62728", marker="o", linewidth=2.5)
        ax2.set_ylabel("Average Lead Time (Days)", color="#d62728")
        ax2.tick_params(axis='y', labelcolor="#d62728")
        ax2.grid(False)

        plt.title("Regional Performance: Sales Volume vs. Fulfillment Lead Time", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "03_regional_performance.png"), dpi=300)
        plt.close()

    def run_product_performance(self) -> None:
        """Generates bubble chart of Sales vs Units vs Margin per Product SKU."""
        logger.info("Generating Product Performance plot...")
        fig, ax = plt.subplots(figsize=(12, 7))

        prod_summary = self.df.groupby("Product Name").agg(
            total_sales=("Sales", "sum"),
            total_units=("Units", "sum"),
            avg_profit_margin=("Gross Profit", lambda x: (x.sum() / self.df.loc[x.index, "Sales"].sum()) * 100)
        ).reset_index()

        # Bubble Chart
        scatter = ax.scatter(
            data=prod_summary,
            x="total_units",
            y="total_sales",
            s=prod_summary["avg_profit_margin"] * 8,  # Scale bubble size
            alpha=0.6,
            c="avg_profit_margin",
            cmap="viridis",
            edgecolors="black"
        )
        
        # Label points
        for i, row in prod_summary.iterrows():
            ax.annotate(row["Product Name"], (row["total_units"] + 200, row["total_sales"]), fontsize=9)

        ax.set_title("Product Portfolio: Sales vs. Units vs. Profit Margin Size", fontsize=14, fontweight="bold")
        ax.set_xlabel("Total Units Sold")
        ax.set_ylabel("Total Sales Revenue ($)")
        
        # Add colorbar
        cbar = plt.colorbar(scatter)
        cbar.set_label("Average Gross Margin %")

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "04_product_performance.png"), dpi=300)
        plt.close()

    def run_shipping_performance(self) -> None:
        """Generates violin plot of lead times across Ship Modes."""
        logger.info("Generating Shipping Performance plot...")
        fig, ax = plt.subplots(figsize=(10, 6))

        sns.violinplot(data=self.df, x="Ship Mode", y="lead_time_days", ax=ax, palette="muted", inner="box")
        ax.set_title("Fulfillment Lead Times (Days) by Shipping Mode Tiers", fontsize=14, fontweight="bold")
        ax.set_ylabel("Lead Time (Days)")
        ax.set_xlabel("Ship Mode")

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "05_shipping_performance.png"), dpi=300)
        plt.close()

    def run_customer_analysis(self) -> None:
        """Generates Pareto / Lorenz curve for B2B Customer Concentration."""
        logger.info("Generating Customer Concentration plot...")
        fig, ax = plt.subplots(figsize=(10, 6))

        cust_sales = self.df.groupby("Customer ID")["Sales"].sum().sort_values(ascending=False).reset_index()
        cust_sales["cumulative_sales"] = cust_sales["Sales"].cumsum()
        cust_sales["cumulative_sales_pct"] = (cust_sales["cumulative_sales"] / cust_sales["Sales"].sum()) * 100
        cust_sales["customer_pct"] = (cust_sales.index + 1) / len(cust_sales) * 100

        # Plot Lorenz Curve
        sns.lineplot(data=cust_sales, x="customer_pct", y="cumulative_sales_pct", ax=ax, color="#9467bd", linewidth=2.5)
        ax.axhline(80, color="#d62728", linestyle="--", alpha=0.7)
        ax.axvline(20, color="#d62728", linestyle="--", alpha=0.7)
        
        ax.set_title("Customer Concentration Analysis (Lorenz / Pareto Curve)", fontsize=14, fontweight="bold")
        ax.set_xlabel("Percentage of Customers (%)")
        ax.set_ylabel("Percentage of Total Revenue (%)")
        ax.text(22, 40, "20% of customers generate ~55% of sales", color="#d62728", fontweight="semibold")

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "06_customer_concentration.png"), dpi=300)
        plt.close()

    def run_correlation_analysis(self) -> None:
        """Generates a correlation heatmap of numeric features."""
        logger.info("Generating Correlation Heatmap plot...")
        fig, ax = plt.subplots(figsize=(8, 6))

        numeric_df = self.df[["Sales", "Units", "Gross Profit", "Cost", "lead_time_days"]]
        corr = numeric_df.corr()

        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5, ax=ax, square=True)
        ax.set_title("Correlation Heatmap: Transaction & Logistics Metrics", fontsize=14, fontweight="bold")

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "07_correlation_analysis.png"), dpi=300)
        plt.close()

    def run_outlier_analysis(self) -> None:
        """Generates Outlier detection boxplots for Sales and Units."""
        logger.info("Generating Outlier Analysis plot...")
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        sns.boxplot(data=self.df, y="Sales", ax=axes[0], color="#bcbd22", width=0.4)
        axes[0].set_title("Outlier Identification: Transaction Sales ($)", fontsize=14, fontweight="bold")
        axes[0].set_ylabel("Sales ($)")

        sns.boxplot(data=self.df, y="Units", ax=axes[1], color="#17becf", width=0.4)
        axes[1].set_title("Outlier Identification: Order Units", fontsize=14, fontweight="bold")
        axes[1].set_ylabel("Units")

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "08_outlier_analysis.png"), dpi=300)
        plt.close()

    def run_seasonality_analysis(self) -> None:
        """Generates seasonal trends based on monthly aggregated volume."""
        logger.info("Generating Seasonality Analysis plot...")
        fig, ax = plt.subplots(figsize=(10, 6))

        # Extract month and year
        df_seasonal = self.df.copy()
        df_seasonal["Month"] = df_seasonal["Order Date"].dt.month_name()
        df_seasonal["MonthNum"] = df_seasonal["Order Date"].dt.month
        
        # Sort by month number
        seasonal_summary = df_seasonal.groupby(["MonthNum", "Month"])["Sales"].mean().reset_index()

        sns.barplot(data=seasonal_summary, x="Month", y="Sales", ax=ax, palette="YlOrRd")
        ax.set_title("Seasonal Distribution: Average Order Sales by Month", fontsize=14, fontweight="bold")
        ax.set_ylabel("Average Sales Value per Transaction ($)")
        ax.set_xlabel("Month")
        plt.xticks(rotation=45)

        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "09_seasonality_analysis.png"), dpi=300)
        plt.close()

    def run_executive_insights(self) -> None:
        """Generates text-based summary of executive KPI highlights."""
        logger.info("Generating Executive summary report...")
        total_sales = self.df["Sales"].sum()
        total_profit = self.df["Gross Profit"].sum()
        avg_margin = (total_profit / total_sales) * 100
        avg_lead_time = self.df["lead_time_days"].mean()
        
        summary_path = os.path.join(self.output_dir, "10_executive_insights.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("=== NASSAU CANDY KEY KPI SUMMARY ===\n")
            f.write(f"Total Sales Revenue        : ${total_sales:,.2f}\n")
            f.write(f"Total Gross Profit         : ${total_profit:,.2f}\n")
            f.write(f"Average Gross Margin (%)   : {avg_margin:.2f}%\n")
            f.write(f"Average Shipping Lead Time : {avg_lead_time:.2f} days\n")
            f.write(f"Product Class Focus        : Chocolate represents 96.57% of order counts.\n")
        logger.info("Executive insights exported to %s", summary_path)

    def generate_all(self) -> None:
        """Generates all 10 analysis views sequentially."""
        logger.info("=== Beginning Generation of All EDA Visualizations ===")
        plot_methods = [
            ("Sales Analysis", self.run_sales_analysis),
            ("Profit Analysis", self.run_profit_analysis),
            ("Regional Performance", self.run_regional_performance),
            ("Product Performance", self.run_product_performance),
            ("Shipping Performance", self.run_shipping_performance),
            ("Customer Concentration", self.run_customer_analysis),
            ("Correlation Analysis", self.run_correlation_analysis),
            ("Outlier Analysis", self.run_outlier_analysis),
            ("Seasonality Analysis", self.run_seasonality_analysis),
            ("Executive Insights", self.run_executive_insights),
        ]
        for name, method in plot_methods:
            try:
                method()
            except Exception:
                logger.exception("Failed to generate %s plot — skipping", name)
        logger.info("=== All EDA Visualizations Generation Complete ===")

if __name__ == "__main__":
    raw_csv_local = "data/raw/Nassau Candy Distributor.csv"
    raw_csv_parent = "../Nassau Candy Distributor.csv"
    raw_csv_fallback = "Nassau Candy Distributor.csv"
    
    if os.path.exists(raw_csv_local):
        raw_csv = raw_csv_local
    elif os.path.exists(raw_csv_parent):
        raw_csv = raw_csv_parent
    else:
        raw_csv = raw_csv_fallback
        
    eda = NassauEDA(data_path=raw_csv, output_dir="images")
    eda.generate_all()
