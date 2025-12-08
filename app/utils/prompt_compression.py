# app/utils/prompt_compression.py
"""
Prompt compression utilities to reduce token usage while preserving information.
Compresses sales data, inventory records, and other verbose structures.
"""

import json
import statistics
from typing import List, Dict, Any
from datetime import datetime, timedelta


def compress_sales_data(sales_records: List[Dict[str, Any]], max_records: int = 30) -> Dict[str, Any]:
    """
    Compress sales records into statistical summary.
    Reduces token usage by 80-90% while preserving key information.
    
    Args:
        sales_records: List of sales records with keys: sold_quantity, date, revenue
        max_records: Maximum recent records to consider
        
    Returns:
        Compressed summary with key statistics
    """
    if not sales_records:
        return {
            "count": 0,
            "avg_qty": 0,
            "total_qty": 0,
            "trend": "no_data"
        }
    
    # Sort by date (newest first) and limit to recent records
    try:
        sorted_sales = sorted(
            sales_records,
            key=lambda x: x.get("date", ""),
            reverse=True
        )[:max_records]
    except Exception:
        sorted_sales = sales_records[:max_records]
    
    quantities = [s.get("sold_quantity", 0) for s in sorted_sales]
    
    if not quantities:
        return {"count": 0, "avg_qty": 0, "total_qty": 0, "trend": "no_data"}
    
    # Calculate statistics
    avg_qty = statistics.mean(quantities)
    total_qty = sum(quantities)
    min_qty = min(quantities)
    max_qty = max(quantities)
    
    # Calculate trend (recent vs older)
    trend = "flat"
    if len(quantities) >= 6:
        recent_avg = statistics.mean(quantities[:3])
        older_avg = statistics.mean(quantities[3:6])
        if older_avg > 0:
            change = ((recent_avg - older_avg) / older_avg) * 100
            if change > 10:
                trend = f"+{int(change)}%"
            elif change < -10:
                trend = f"{int(change)}%"
    
    # Calculate volatility
    volatility = "low"
    if len(quantities) > 1:
        std_dev = statistics.stdev(quantities)
        cv = (std_dev / avg_qty) if avg_qty > 0 else 0
        if cv > 0.5:
            volatility = "high"
        elif cv > 0.25:
            volatility = "medium"
    
    return {
        "count": len(quantities),
        "avg_qty": round(avg_qty, 1),
        "total_qty": total_qty,
        "min_qty": min_qty,
        "max_qty": max_qty,
        "trend": trend,
        "volatility": volatility,
        "days_tracked": len(sorted_sales)
    }


def compress_inventory_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract only critical fields from inventory item.
    
    Args:
        item: Full inventory record
        
    Returns:
        Compressed item with essential fields only
    """
    return {
        "sku": item.get("sku"),
        "name": item.get("product_name", "Unknown"),
        "qty": item.get("quantity", 0),
        "threshold": item.get("threshold", 10),
        "price": item.get("unit_price", 0)
    }


def compress_forecast_prompt(sku_data: Dict, sales_summary: Dict) -> str:
    """
    Create compressed forecast prompt.
    
    Args:
        sku_data: SKU information
        sales_summary: Compressed sales summary
        
    Returns:
        Compact JSON prompt string
    """
    prompt_data = {
        "sku": sku_data.get("sku"),
        "product": sku_data.get("product_name", "Unknown"),
        "stock": sku_data.get("quantity", 0),
        "sales": sales_summary
    }
    
    # Use compact JSON (no whitespace)
    return json.dumps(prompt_data, separators=(',', ':'))


def compress_negotiation_prompt(
    rejected_item: Dict,
    inventory_item: Dict,
    budget_info: Dict
) -> Dict[str, Any]:
    """
    Create compressed negotiation context.
    
    Args:
        rejected_item: Rejected order details
        inventory_item: Current inventory state
        budget_info: Budget constraints
        
    Returns:
        Compressed negotiation context
    """
    return {
        "item": {
            "sku": rejected_item.get("sku"),
            "name": rejected_item.get("product_name", "Unknown"),
            "qty_requested": rejected_item.get("order_quantity", 0),
            "cost": rejected_item.get("order_value", 0)
        },
        "inventory": {
            "current": inventory_item.get("quantity", 0),
            "threshold": inventory_item.get("threshold", 10),
            "gap": inventory_item.get("threshold", 10) - inventory_item.get("quantity", 0)
        },
        "budget": {
            "remaining": budget_info.get("remaining", 0),
            "shortfall": rejected_item.get("order_value", 0) - budget_info.get("remaining", 0)
        }
    }


def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    Truncate text to maximum length while preserving readability.
    
    Args:
        text: Text to truncate
        max_length: Maximum character length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    # Try to truncate at sentence boundary
    truncated = text[:max_length]
    last_period = truncated.rfind('.')
    
    if last_period > max_length * 0.7:  # If we can keep 70% of text
        return truncated[:last_period + 1] + "..."
    
    return truncated + "..."


def estimate_token_savings(original_data: Any, compressed_data: Any) -> Dict[str, int]:
    """
    Estimate token savings from compression.
    
    Args:
        original_data: Original data structure
        compressed_data: Compressed version
        
    Returns:
        Dictionary with token estimates and savings
    """
    original_str = json.dumps(original_data) if not isinstance(original_data, str) else original_data
    compressed_str = json.dumps(compressed_data) if not isinstance(compressed_data, str) else compressed_data
    
    # Rough token estimate: 4 chars per token
    original_tokens = len(original_str) // 4
    compressed_tokens = len(compressed_str) // 4
    
    return {
        "original_tokens": original_tokens,
        "compressed_tokens": compressed_tokens,
        "tokens_saved": original_tokens - compressed_tokens,
        "reduction_percentage": ((original_tokens - compressed_tokens) / original_tokens * 100) if original_tokens > 0 else 0
    }
