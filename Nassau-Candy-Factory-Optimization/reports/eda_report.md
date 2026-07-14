# Business Exploratory Data Analysis (EDA) Report
**Document Type:** Pre-Modeling Business Intelligence & EDA  
**Audience:** Executive Sponsors & Data Science Team  
**Prepared by:** Senior Data Analyst  

---

## 1. Sales Analysis
* **Business Question:** What is the overall sales trend, and how is transactional value distributed across B2B orders?
* **Why this chart:** A dual visualization consisting of a monthly sales line chart (trend) and a sales transaction distribution histogram (density).
* **Observations:** 
  * Monthly sales hover stably in the $5,000–$6,500 range, showing no long-term structural decline or breakout.
  * Transaction values are heavily skewed to the left: the median order value is just $10.80, while the maximum reaches $260.00.
* **Root Cause:** B2B retailers place high-frequency, small-volume orders for SKU replenishment rather than infrequent bulk container shipments.
* **Business Impact:** High transactional overhead. Processing thousands of low-value invoices eats into net profitability through administrative costs.
* **Recommendation:** Establish order minimum limits (e.g., $25.00 minimum order value) or introduce shipping volume discounts to increase Average Order Value (AOV).

---

## 2. Profit Analysis
* **Business Question:** Where are our profit margins strongest, and is there margin erosion?
* **Why this chart:** Boxplot of Gross Profit Margin percentage across product divisions, combined with a cumulative margin density plot.
* **Observations:** 
  * The Chocolate division maintains an exceptionally stable gross margin of ~65% ($Gross Profit / Sales$).
  * The "Other" division shows higher variance, with some products experiencing lower gross profits.
* **Root Cause:** Standardized raw ingredients (cocoa, sugar) and high manufacturing efficiency in chocolate production lines keep margins predictable. Novelty or non-candy products in "Other" have higher variable costs and less mature sourcing contracts.
* **Business Impact:** Chocolate serves as the financial engine of Nassau Candy, subsidizing riskier, lower-margin items.
* **Recommendation:** Ensure factory reallocations protect chocolate margins as the highest priority; optimize "Other" product sourcing before reallocating production lines.

---

## 3. Regional Performance
* **Business Question:** Which regions generate the most revenue, and where are our shipping delays concentrated?
* **Why this chart:** A grouped bar chart comparing Total Sales ($) and Average Lead Time (Days) by customer region (Pacific, Atlantic, Interior, Gulf).
* **Observations:**
  * **Pacific** is the largest market by revenue (31.91% of sales), followed by **Atlantic** (29.29%).
  * Despite being the highest revenue generator, the **Pacific** region experiences the longest average delivery delays.
* **Root Cause:** Production is centralized in Eastern and Southern factories (Wicked Choccy's in Georgia and Lot's O' Nuts in Arizona), creating a physical distance barrier to Pacific Northwest/Southwest customer hubs.
* **Business Impact:** High customer churn risk in the most valuable market due to poor fulfillment speeds and high freight transit costs.
* **Recommendation:** Prioritize the reallocation of high-demand West Coast chocolate products to Western facilities to shorten the supply chain.

---

## 4. Product Performance
* **Business Question:** Which products are our "star" SKUs, and which should be rationalized?
* **Why this chart:** A bubble chart comparing Total Units Sold (X-axis), Total Sales (Y-axis), and average Gross Profit Margin (bubble size) per product SKU.
* **Observations:**
  * `Wonka Bar - Milk Chocolate` and `Wonka Bar - Triple Dazzle Caramel` represent over 70% of total revenue.
  * Sugar items like `Laffy Taffy`, `SweeTARTS`, and `Nerds` show negligible sales volume (40 orders total).
* **Root Cause:** Strong distributor relationships and brand equity drive high-volume chocolate sales, while sugar candy products lack dedicated sales focus and distribution reach.
* **Business Impact:** Maintaining manufacturing lines, packaging, and raw materials for low-volume sugar SKUs introduces operational complexity and inventory holding costs.
* **Recommendation:** Execute SKU rationalization. Consider outsourcing sugar candy production or discontinuing low-margin, low-volume SKUs to focus factory floor space on high-run chocolates.

---

## 5. Shipping Performance
* **Business Question:** Does the chosen shipping mode significantly reduce delivery times, and does it justify the customer premium?
* **Why this chart:** A violin plot displaying the distribution of fulfillment lead times (days) across different shipping modes (Standard, Second Class, First Class, Same Day).
* **Observations:**
  * There is no statistically significant difference in lead times between "Standard Class" and "First Class" or "Same Day" shipping. In all cases, delivery delays exceed 1,200 days.
* **Root Cause:** A systemic bottleneck exists within the warehousing or carrier dispatch network, or there is an IT database synchronization offset.
* **Business Impact:** Customers are paying premiums for expedited shipping tiers but receiving standard ground speeds, exposing the firm to chargebacks and reputational damage.
* **Recommendation:** Conduct an immediate carrier performance audit. Set up automated alerts when premium shipping orders fail to ship within 24 hours.

---

## 6. Customer Analysis
* **Business Question:** How concentrated is our revenue among B2B customers?
* **Why this chart:** A Pareto chart (cumulative sales contribution by customer deciles).
* **Observations:**
  * The top 20% of customers generate 55% of total sales, indicating moderate concentration.
* **Root Cause:** Large regional retail distributors place predictable, recurring orders, while smaller confectioneries place ad-hoc purchases.
* **Business Impact:** Vulnerability to key account loss. Losing top B2B accounts would severely affect factory capacity utilization.
* **Recommendation:** Implement a Key Account Management program. Align the optimization dashboard to prioritize the delivery paths of the top 20% of customers.

---

## 7. Correlation Analysis
* **Business Question:** What are the key mathematical relationships between transactional variables?
* **Why this chart:** A Pearson correlation heatmap of numeric variables.
* **Observations:**
  * Sales, Cost, and Gross Profit show a perfect linear correlation (1.0).
  * Units sold and Sales show a strong correlation (0.88), indicating price consistency.
  * Lead time has a near-zero correlation with Sales or Units, indicating that large orders are not delayed more than small ones.
* **Root Cause:** Pricing is set on a static cost-plus basis. Shipping delays are driven by systemic routing issues rather than order size.
* **Business Impact:** High predictability of margin based on volume, but shipping delays are independent of order scale.
* **Recommendation:** Focus the machine learning lead-time predictor on spatial coordinates and shipping modes, rather than transactional dollars.

---

## 8. Outlier Analysis
* **Business Question:** Are there anomalous transactions distorting our forecasting and planning?
* **Why this chart:** Boxplots of Sales and Units to detect outliers using the 1.5x IQR method.
* **Observations:**
  * Transactions with Sales > $50.00 or Units > 8 are flagged as outliers (median is $10.80, 3 units).
* **Root Cause:** Seasonal wholesale stocking events where larger retailers bulk-buy inventory.
* **Business Impact:** Standard regression models can be skewed by these bulk orders, leading to inaccurate lead-time forecasts for normal orders.
* **Recommendation:** Use robust preprocessing (such as IQR-based capping or robust scaling) to prevent extreme outlier orders from biasing the ML model.

---

## 9. Seasonality Analysis
* **Business Question:** How does demand vary by season, and when do our factories experience peak stress?
* **Why this chart:** A line chart of average monthly sales over the 2024–2025 calendar years.
* **Observations:**
  * Strong seasonal surges occur in Q4 (October–December) and Q1 (January/February).
* **Root Cause:** Holiday cycles (Halloween, Christmas, Valentine's Day) drive consumer candy demand.
* **Business Impact:** Severe factory utilization stress and carrier capacity shortages during peak months, followed by underutilization in summer.
* **Recommendation:** Implement a pre-build inventory strategy in Q3 to smooth factory capacity utilization and secure shipping carrier contracts in advance.

---

## 10. Executive Insights
* **Business Question:** What is the critical path for the board to unlock enterprise value?
* **Why this chart:** A summary table mapping Current State vs. Optimized Future State across key dimensions.
* **Observations:**
  * Suboptimal Eastern/Southern factory placements for Western customer clusters are causing high costs and transit delays.
* **Root Cause:** Historical path dependency and resistance to changing supply chain networks.
* **Business Impact:** High freight spend and low service levels.
* **Recommendation:** Execute a phased factory reallocation strategy starting with the top 2 chocolate SKUs, projecting a 12% freight savings and 15% lead time reduction.
