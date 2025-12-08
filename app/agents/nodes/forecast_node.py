# app/agents/nodes/forecast_node.py
"""LangGraph node: Generate 7-day demand forecasts using Hybrid approach (Stats + LLM)."""

import json
import logging
import time
import statistics
from typing import Dict, Any, List

from app.config.llm_config import LLMConfig
from app.utils.groq_utils import query_groq, try_parse_json_from_text
from app.agents.reasoning_prompts import FORECAST_PROMPT
from app.agents.state import CycleState
from app.utils.prompt_compression import compress_sales_data, compress_inventory_item

logger = logging.getLogger("forecast_node")

def _calculate_statistical_forecast(sales_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate forecast using statistical methods (SMA + Trend).
    Returns None if insufficient data, otherwise returns forecast dict.
    """
    if not sales_list or len(sales_list) < 3:
        return None
        
    # Sort sales by date (newest first) to ensure correct trend calculation
    # Assuming sales_list has 'date' field, otherwise rely on list order
    try:
        sales_list.sort(key=lambda x: x.get("date", ""), reverse=True)
    except:
        pass # Fallback to existing order
        
    quantities = [int(s.get("sold_quantity", 0)) for s in sales_list]
    
    if not quantities:
        return None
        
    # Simple Moving Average
    avg = statistics.mean(quantities)
    
    # Simple Trend (last 3 vs prev 3)
    # Note: quantities are newest first, so quantities[:3] is recent
    if len(quantities) >= 6:
        recent = statistics.mean(quantities[:3])
        prev = statistics.mean(quantities[3:6])
        # Avoid division by zero or explosive trends on small numbers
        if prev < 5:
            trend = 0 # Ignore trend if base is too small
        else:
            trend = (recent - prev) / prev
            # Cap trend at +/- 50% to prevent wild swings
            trend = max(-0.5, min(0.5, trend))
    else:
        trend = 0
        
    # Apply trend with dampening
    forecast_val = avg * (1 + (trend * 0.5))
    forecast_val = max(0, int(forecast_val))
    
    # Calculate volatility (std dev / mean)
    if len(quantities) > 1:
        volatility = statistics.stdev(quantities) / max(1, avg)
    else:
        volatility = 0
        
    return {
        "forecast": [forecast_val] * 7,
        "confidence": max(0.1, 1.0 - volatility), # High volatility = low confidence
        "explanation": f"Statistical Forecast (SMA: {avg:.1f}, Trend: {trend:.1%})"
    }

def forecast_node(state: CycleState) -> CycleState:
    """
    LangGraph node: Generate 7-day demand forecasts.
    Uses Hybrid approach: Statistical for stable items, LLM for volatile ones.
    """
    
    if state.skip_forecast:
        logger.info(f"[{state.cycle_id}] Skipping forecast (disabled)")
        return state
    
    try:
        logger.info(f"[{state.cycle_id}] Generating forecasts for {len(state.inventory_data)} SKUs...")
        
        forecasts = []
        llm_calls_made = 0
        MAX_LLM_CALLS = LLMConfig.MAX_FORECAST_LLM_CALLS
        
        # Evaluate all items first to prioritize high-value items for LLM
        items_to_forecast = []
        for sku, item in state.inventory_data.items():
            recent_sales = state.sales_by_sku.get(sku, [])
            stat_forecast = _calculate_statistical_forecast(recent_sales)
            
            # Determine if LLM would be beneficial
            needs_llm = False
            priority = 0
            
            if not stat_forecast:
                needs_llm = True
                priority = 3  # No data = high priority
            elif stat_forecast['confidence'] < 0.3:
                needs_llm = True
                priority = 2  # Very uncertain = medium priority
            
            # Boost priority for high-value items
            unit_price = item.get("unit_price", 0) or 0
            if unit_price > 100:
                priority += 1  # Expensive items get LLM attention
            
            items_to_forecast.append({
                "sku": sku,
                "item": item,
                "stat_forecast": stat_forecast,
                "needs_llm": needs_llm,
                "priority": priority
            })
        
        # Sort by priority (high to low)
        items_to_forecast.sort(key=lambda x: x["priority"], reverse=True)
        
        def process_sku_forecast(forecast_data):
            nonlocal llm_calls_made
            
            sku = forecast_data["sku"]
            item = forecast_data["item"]
            stat_forecast = forecast_data["stat_forecast"]
            needs_llm = forecast_data["needs_llm"]
            
            try:
                recent_sales = state.sales_by_sku.get(sku, [])
                
                # Use statistical if we have it and don't need LLM
                if stat_forecast and not needs_llm:
                    return {
                        "sku": sku,
                        "product_name": item.get("product_name"),
                        "forecast": stat_forecast
                    }
                
                # Check if we're under LLM call limit
                if needs_llm and llm_calls_made >= MAX_LLM_CALLS:
                    logger.info(f"LLM call limit reached ({MAX_LLM_CALLS}). Using statistical fallback for {sku}")
                    return {
                        "sku": sku,
                        "product_name": item.get("product_name"),
                        "forecast": stat_forecast or {
                            "forecast": [0]*7,
                            "confidence": 0,
                            "explanation": "No data, LLM limit reached"
                        }
                    }
                
                # LLM Forecast
                sku_summary = compress_inventory_item(item)
                sales_summary = compress_sales_data(recent_sales, max_records=30)
                
                prompt = FORECAST_PROMPT.format(
                    sku_summary=json.dumps(sku_summary, separators=(',', ':')),
                    recent_sales=json.dumps(sales_summary, separators=(',', ':'))
                )
                
                # Call LLM with retry logic
                for attempt in range(2):
                    try:
                        raw = query_groq(
                            LLMConfig.FORECAST_MODEL,  # llama-3.3-70b-versatile
                            prompt,
                            timeout=LLMConfig.FORECAST_TIMEOUT,
                            max_tokens=500
                        )
                        
                        if raw is None:
                            logger.warning(f"LLM unavailable for {sku}. Using statistical fallback.")
                            break
                            
                        parsed = try_parse_json_from_text(raw)
                        
                        if parsed and isinstance(parsed, dict):
                            if parsed.get("confidence", 0) < 0.4:
                                parsed["confidence"] = 0.45
                            
                            llm_calls_made += 1
                            logger.info(f"LLM forecast for {sku} (call {llm_calls_made}/{MAX_LLM_CALLS})")
                            
                            return {
                                "sku": sku,
                                "product_name": item.get("product_name"),
                                "forecast": parsed
                            }
                        else:
                            logger.warning(f"LLM returned invalid format for {sku}: {type(parsed)}. Using fallback.")
                    except Exception as e:
                        logger.warning(f"LLM forecast attempt {attempt+1} failed for {sku}: {e}")
                        time.sleep(1)
                
                # Fallback to stats
                return {
                    "sku": sku,
                    "product_name": item.get("product_name"),
                    "forecast": stat_forecast or {
                        "forecast": [0]*7, 
                        "confidence": 0, 
                        "explanation": "No data"
                    }
                }
                
            except Exception as e:
                logger.error(f"Forecast error for {sku}: {e}")
                return {"error": str(e), "sku": sku}

        from app.agents.streaming import stream_manager
        
        # Process items sequentially (parallel processing causes issues with rate limits)
        logger.info(f"[{state.cycle_id}] Processing {len(items_to_forecast)} items (max {MAX_LLM_CALLS} LLM calls)")
        
        for forecast_data in items_to_forecast:
            result = process_sku_forecast(forecast_data)
            if "error" in result:
                state.add_error(result["sku"], f"Forecast failed: {result['error']}")
            else:
                forecasts.append(result)
                # Emit event immediately for high-demand items
                forecast_dict = result.get('forecast', {})
                if isinstance(forecast_dict, dict):
                    forecast_list = forecast_dict.get('forecast', [])
                    total_demand = sum(forecast_list) if isinstance(forecast_list, list) else 0
                    if total_demand > 100:
                        stream_manager.emit(
                            state.cycle_id, 
                            "forecast", 
                            f"📈 @InventoryManager, I'm seeing a spike in {result['product_name']}. Predicted sales: {int(total_demand)} units (Confidence: {int(forecast_dict.get('confidence', 0)*100)}%).",
                            {"sku": result['sku'], "confidence": forecast_dict.get('confidence')}
                        )
        
        state.forecast_results = forecasts
        
        logger.info(f"[{state.cycle_id}] Generated {len(state.forecast_results)} forecasts ({llm_calls_made} used LLM)")
        logger.info(f"[{state.cycle_id}] Forecast SKUs: {[f['sku'] for f in forecasts[:10]]}...")  # Show first 10
        
        return state
        
    except Exception as e:
        logger.error(f"[{state.cycle_id}] Fatal forecast error: {str(e)}")
        state.add_error("FORECAST_NODE", str(e))
        return state
