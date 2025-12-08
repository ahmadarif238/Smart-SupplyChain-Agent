# app/agents/reasoning_prompts.py
# Centralized prompts used by the agent nodes

FORECAST_PROMPT = (
    "You are an inventory forecaster. Predict next 7 days demand based on stats.\n"
    "Return valid JSON with keys: forecast (7 daily numbers), confidence (0-1), explanation (text)\n\n"
    "SKU: {sku_summary}\nSales Stats: {recent_sales}\nReturn only JSON, no extra text."
)

DECISION_PROMPT = (
    "Supply chain decision. Given stock and forecast, decide if reorder needed.\n"
    "Return JSON with: reorder_required (bool), qty_to_order (int), reason (text)\n\n"
    "Stock/forecast: {stock_forecast}\nReturn only JSON."
)

SALES_SUMMARY_PROMPT = (
    "You are a sales analytics assistant. Given these sales records (list of objects with 'sku','sold_quantity','date'), "
    "return JSON with keys: 'Top Products' (list), 'Declining Products' (list), 'Revenue Trend' (short string), 'Actionable Insights' (list).\n"
    "Return JSON only."
)

ORDERS_RECOMMEND_PROMPT = (
    "You are a procurement analyst. Given these supplier orders and inventory, "
    "return JSON with keys: 'Urgent Orders', 'Upcoming Orders', 'Low Priority Orders'. "
    "Each entry should include 'sku','product_name','suggested_qty' and a short 'reason'.\nReturn JSON only."
)

ALERTS_ANALYZE_PROMPT = (
    "You are a supply chain safety specialist. Analyze these alert records and return JSON with keys: "
    "'Critical Issues' (list), 'Warnings' (list), 'Resolved Issues' (list), 'Recommended Actions' (list).\nReturn JSON only."
)
