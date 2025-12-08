# app/agents/nodes/intelligent_decision_node.py
"""
Advanced Decision Node - Leverages supply chain data and state management
for more robust and intelligent reorder decisions.

Features:
  1. Economic Order Quantity (EOQ) - Minimizes total ordering/holding costs
  2. Lead Time Buffers - Accounts for supplier lead times
  3. Dynamic Safety Stock - Varies by demand volatility and service level
  4. Supplier Performance - Considers lead time reliability
  5. Cost-Based Optimization - Balances stockout risk vs holding costs
  6. Multi-Factor Scoring - Integrates all factors into urgency levels
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import statistics
import logging

logger = logging.getLogger(__name__)


class UrgencyLevel(str, Enum):
    """Reorder urgency classification"""
    CRITICAL = "critical"      # Immediate action needed
    HIGH = "high"              # Within 1 day
    MEDIUM = "medium"          # Within 3 days
    LOW = "low"                # Within 1 week
    DEFERRED = "deferred"      # No action needed
    OBSOLETE = "obsolete"      # Product inactive


@dataclass
class InventoryMetrics:
    """Calculated inventory metrics for a SKU"""
    current_stock: int
    pending_orders: int
    forecast_7day: int
    daily_avg_demand: float
    demand_volatility: float
    lead_time_days: int
    unit_cost: float
    holding_cost_percent: float
    reorder_cost: float
    safety_stock: int
    min_order_qty: int
    max_order_qty: Optional[int]
    forecast_confidence: float
    
    def get_annual_holding_cost(self, qty: int) -> float:
        """Calculate annual holding cost for quantity"""
        return qty * self.unit_cost * self.holding_cost_percent


@dataclass
class DecisionResult:
    """Structured decision output"""
    reorder_required: bool
    order_quantity: int
    urgency_level: UrgencyLevel
    reason: str
    details: Dict[str, Any]
    cost_analysis: Dict[str, float]
    utility_score: float = 0.0  # New: Stockout Penalty / Value of Action


class IntelligentDecisionNode:
    """
    Advanced decision engine using supply chain optimization techniques.
    """

    def __init__(
        self,
        service_level: float = 0.95,  # 95% service level (avoid stockouts)
        min_confidence_to_order: float = 0.3,
        cost_multiplier: float = 1.0  # Adjust aggressiveness of cost optimization
    ):
        """
        Args:
            service_level: Target service level (0-1). Higher = less stockout risk.
            min_confidence_to_order: Min forecast confidence to trigger reorder.
            cost_multiplier: 1.0 = balanced, >1.0 = conservative, <1.0 = aggressive.
        """
        self.service_level = service_level
        self.min_confidence_to_order = min_confidence_to_order
        self.cost_multiplier = cost_multiplier

    def extract_metrics(
        self,
        sku_item: Dict[str, Any],
        forecast: Dict[str, Any],
        recent_sales: List[Dict[str, Any]],
        pending_orders: int = 0
    ) -> InventoryMetrics:
        """Extract and calculate inventory metrics from raw data"""

        # Extract current state
        current_stock = sku_item.get("quantity", 0)
        forecast_confidence = forecast.get("confidence", 0.8)

        # Extract forecast
        forecast_list = forecast.get("forecast", [])
        forecast_7day = sum(forecast_list[:7]) if forecast_list else 0

        # Calculate demand statistics from recent sales
        daily_demands = [s.get("sold_quantity", 0) for s in recent_sales]
        daily_avg = statistics.mean(daily_demands) if daily_demands else forecast_7day / 7
        
        # Volatility: standard deviation of demand (normalized by mean)
        if len(daily_demands) > 1:
            std_dev = statistics.stdev(daily_demands) if len(daily_demands) > 1 else 0
            volatility = std_dev / max(0.1, daily_avg)
        else:
            volatility = 0.3  # Default moderate volatility

        # Extract supply chain parameters (with defaults)
        lead_time = sku_item.get("lead_time_days", 7)
        unit_price = sku_item.get("unit_price", 10.0)
        holding_cost_pct = sku_item.get("holding_cost_percent", 0.15)
        reorder_cost = sku_item.get("reorder_cost", 25.0)
        safety_stock = sku_item.get("safety_stock", 10)
        min_order_qty = sku_item.get("min_order_qty", 1)
        max_order_qty = sku_item.get("max_order_qty")

        return InventoryMetrics(
            current_stock=current_stock,
            pending_orders=pending_orders,
            forecast_7day=forecast_7day,
            daily_avg_demand=daily_avg,
            demand_volatility=volatility,
            lead_time_days=lead_time,
            unit_cost=unit_price,
            holding_cost_percent=holding_cost_pct,
            reorder_cost=reorder_cost,
            safety_stock=safety_stock,
            min_order_qty=min_order_qty,
            max_order_qty=max_order_qty,
            forecast_confidence=forecast_confidence
        )
    
    def calculate_utility_score(self, metrics: InventoryMetrics) -> float:
        """
        Calculate the Utility Score (Stockout Penalty) of NOT ordering.
        Higher score = Higher penalty for stockout = Higher urgency.
        
        Formula: 
          Daily Revenue * Days Out of Stock (if no order) * Criticality Factor
        """
        daily_revenue = metrics.daily_avg_demand * metrics.unit_cost
        
        # Estimate days out of stock if we don't order until next cycle (assume 7 days)
        # Effective stock covers how many days?
        effective_stock = metrics.current_stock + metrics.pending_orders
        days_coverage = effective_stock / max(0.1, metrics.daily_avg_demand)
        
        days_out_of_stock = max(0, 7 + metrics.lead_time_days - days_coverage)
        
        # Base penalty: Lost Revenue
        lost_revenue = days_out_of_stock * daily_revenue
        
        # Criticality Multiplier (Non-linear penalty for stockouts)
        penalty_factor = 1.0
        if days_coverage < metrics.lead_time_days:
            penalty_factor = 2.0  # Immediate risk
        if days_coverage <= 0:
            penalty_factor = 5.0  # Already stocked out
            
        return lost_revenue * penalty_factor

    def calculate_eoq(self, metrics: InventoryMetrics) -> int:
        """
        Calculate Economic Order Quantity (EOQ).
        Minimizes total annual ordering + holding costs.
        
        Formula: EOQ = sqrt(2 * D * S / H)
        where:
          D = annual demand
          S = reorder cost per order
          H = holding cost per unit per year
        """
        annual_demand = metrics.daily_avg_demand * 365
        
        if annual_demand < 1 or metrics.reorder_cost < 0.01:
            return metrics.min_order_qty
        
        holding_cost_per_unit = metrics.unit_cost * metrics.holding_cost_percent
        
        if holding_cost_per_unit < 0.01:
            return metrics.min_order_qty
        
        eoq = (2 * annual_demand * metrics.reorder_cost / holding_cost_per_unit) ** 0.5
        eoq = int(eoq)
        
        # Respect min/max order quantities
        eoq = max(eoq, metrics.min_order_qty)
        if metrics.max_order_qty:
            eoq = min(eoq, metrics.max_order_qty)
        
        return eoq

    def calculate_dynamic_reorder_point(self, metrics: InventoryMetrics) -> int:
        """
        Calculate dynamic reorder point accounting for lead time and demand variability.
        
        Formula: ROP = (Daily Demand * Lead Time) + Safety Stock Adjustment
        where Safety Stock varies by volatility and service level.
        """
        # Base: expected demand during lead time
        lead_time_demand = metrics.daily_avg_demand * metrics.lead_time_days
        
        # Safety stock adjustment based on volatility and service level
        # Higher volatility and service level → more safety stock
        volatility_factor = max(0.5, min(2.0, metrics.demand_volatility))
        
        # Service level multiplier (0.95 → ~1.65 sigma, 0.99 → ~2.33 sigma)
        service_level_z_score = {
            0.90: 1.28,
            0.95: 1.65,
            0.99: 2.33,
            0.999: 3.09
        }
        z_score = service_level_z_score.get(
            self.service_level,
            1.65 + (self.service_level - 0.95) * 10  # Linear interpolation
        )
        
        dynamic_safety = z_score * metrics.daily_avg_demand * volatility_factor
        
        return int(lead_time_demand + dynamic_safety)

    def calculate_urgency(
        self,
        metrics: InventoryMetrics,
        reorder_point: int,
        eoq: int,
        days_until_stockout: Optional[float]
    ) -> UrgencyLevel:
        """
        Calculate urgency level based on multiple factors.
        """
        
        if not metrics.current_stock or not eoq:
            return UrgencyLevel.OBSOLETE

        # Factor 1: Stock depletion time
        if days_until_stockout is not None:
            if days_until_stockout < 0:
                return UrgencyLevel.CRITICAL
            elif days_until_stockout < metrics.lead_time_days * 0.5:
                return UrgencyLevel.CRITICAL
            elif days_until_stockout < metrics.lead_time_days:
                return UrgencyLevel.HIGH
            elif days_until_stockout < metrics.lead_time_days * 2:
                return UrgencyLevel.MEDIUM

        # Factor 2: Distance from reorder point
        effective_stock = metrics.current_stock + metrics.pending_orders
        if effective_stock < reorder_point * 0.5:
            return UrgencyLevel.CRITICAL
        elif effective_stock < reorder_point:
            return UrgencyLevel.HIGH
        elif effective_stock < reorder_point * 1.5:
            return UrgencyLevel.MEDIUM

        # Factor 3: Forecast confidence
        if metrics.forecast_confidence < 0.4:
            return UrgencyLevel.LOW  # Uncertain demand → defer if safe

        return UrgencyLevel.LOW

    def calculate_cost_analysis(
        self,
        metrics: InventoryMetrics,
        order_qty: int
    ) -> Dict[str, float]:
        """Calculate cost metrics for the proposed order"""
        
        annual_demand = metrics.daily_avg_demand * 365
        
        # Ordering costs
        orders_per_year = annual_demand / order_qty if order_qty > 0 else 0
        annual_ordering_cost = orders_per_year * metrics.reorder_cost
        
        # Holding costs (average inventory = order_qty / 2)
        avg_inventory = (order_qty / 2) + metrics.safety_stock
        annual_holding_cost = metrics.get_annual_holding_cost(avg_inventory)
        
        # Total cost
        total_cost = annual_ordering_cost + annual_holding_cost
        
        return {
            "annual_demand": annual_demand,
            "orders_per_year": orders_per_year,
            "annual_ordering_cost": annual_ordering_cost,
            "avg_inventory": avg_inventory,
            "annual_holding_cost": annual_holding_cost,
            "total_annual_cost": total_cost,
            "cost_per_unit": total_cost / max(annual_demand, 1)
        }

    def decide(
        self,
        sku_item: Dict[str, Any],
        forecast: Dict[str, Any],
        recent_sales: List[Dict[str, Any]],
        pending_orders: int = 0
    ) -> DecisionResult:
        """
        Make intelligent reorder decision using all available data.
        
        Args:
            sku_item: Inventory record with supply chain parameters
            forecast: 7-day forecast from LLM
            recent_sales: Recent sales records for volatility calculation
        
        Returns:
            DecisionResult with structured decision information
        """

        try:
            sku = sku_item.get("sku", "UNKNOWN")
            product_name = sku_item.get("product_name", "Unknown Product")
            is_active = sku_item.get("is_active", True)

            # Check if product is active
            if not is_active:
                return DecisionResult(
                    reorder_required=False,
                    order_quantity=0,
                    urgency_level=UrgencyLevel.OBSOLETE,
                    reason=f"{sku} is marked inactive",
                    details={"status": "inactive"},
                    cost_analysis={}
                )

            # Extract metrics from data
            metrics = self.extract_metrics(sku_item, forecast, recent_sales, pending_orders)
            
            # DEBUG LOG
            if metrics.unit_cost > 50:
                logger.info(f"💰 DecisionNode: {sku} unit_cost={metrics.unit_cost}")

            # Calculate effective stock (current + pending)
            effective_stock = metrics.current_stock + metrics.pending_orders

            # Check forecast confidence
            if metrics.forecast_confidence < self.min_confidence_to_order:
                logger.warning(
                    f"{sku}: Low forecast confidence ({metrics.forecast_confidence:.2f}), "
                    f"using conservative approach"
                )
                # Low confidence: Trust static threshold over dynamic forecast
                threshold = sku_item.get("threshold", 10)
                
                # Only order if we are actually below the safety threshold
                if metrics.current_stock < threshold:
                    # Order enough to get to 2x threshold (safe buffer)
                    target_stock = int(threshold * 2)
                    order_qty = max(metrics.min_order_qty, target_stock - metrics.current_stock)
                    
                    return DecisionResult(
                        reorder_required=True,
                        order_quantity=order_qty,
                        urgency_level=UrgencyLevel.HIGH,
                        reason=f"Low confidence fallback: Stock {metrics.current_stock} < Threshold {threshold}",
                        details={
                            "forecast_confidence": metrics.forecast_confidence,
                            "type": "threshold_fallback"
                        },
                        cost_analysis={}
                    )
                else:
                    # Above threshold + low confidence = Wait and see
                    return DecisionResult(
                        reorder_required=False,
                        order_quantity=0,
                        urgency_level=UrgencyLevel.DEFERRED,
                        reason=f"Low forecast confidence & Stock {metrics.current_stock} > Threshold {threshold}",
                        details={
                            "forecast_confidence": metrics.forecast_confidence,
                            "type": "threshold_hold"
                        },
                        cost_analysis={}
                    )

            # Calculate key metrics
            eoq = self.calculate_eoq(metrics)
            reorder_point = self.calculate_dynamic_reorder_point(metrics)

            # Calculate days until stockout (using effective stock)
            if metrics.daily_avg_demand > 0:
                days_until_stockout = effective_stock / metrics.daily_avg_demand
            else:
                days_until_stockout = None

            # Determine if reorder is needed (using effective stock)
            reorder_required = (
                effective_stock < reorder_point or
                effective_stock == 0
            )

            # Initialize defaults
            order_qty = 0
            urgency = UrgencyLevel.LOW

            # Calculate order quantity using EOQ with cost optimization
            if reorder_required:
                # Target: bring stock to (reorder_point + EOQ)
                target_stock = reorder_point + eoq
                order_qty = max(
                    0,
                    target_stock - effective_stock
                )
                
                # Apply cost multiplier from default
                # if learned_params:
                #     cost_multiplier = learned_params.get("cost_multiplier", self.cost_multiplier)

            # Calculate urgency
            urgency = self.calculate_urgency(
                metrics, reorder_point, eoq, days_until_stockout
            )

            # Prepare detailed explanation
            details = {
                "current_stock": metrics.current_stock,
                "pending_orders": metrics.pending_orders,
                "effective_stock": effective_stock,
                "reorder_point": reorder_point,
                "eoq": eoq,
                "lead_time_days": metrics.lead_time_days,
                "daily_avg_demand": f"{metrics.daily_avg_demand:.1f}",
                "forecast_7day": metrics.forecast_7day,
                "demand_volatility": f"{metrics.demand_volatility:.2f}",
                "forecast_confidence": metrics.forecast_confidence,
                "days_until_stockout": f"{days_until_stockout:.1f}" if days_until_stockout else "N/A",
                "safety_stock": metrics.safety_stock,
                "unit_price": metrics.unit_cost  # Add unit price for Finance
            }

            # Calculate cost analysis
            cost_analysis = self.calculate_cost_analysis(metrics, eoq)
            # Add purchasing cost to analysis for clarity
            cost_analysis["purchasing_cost_per_unit"] = metrics.unit_cost

            # Build reason string
            if reorder_required:
                reason = (
                    f"{sku}: Effective Stock {effective_stock} (Cur: {metrics.current_stock} + Pend: {metrics.pending_orders}) < ROP {reorder_point}. "
                    f"Order {order_qty} units (EOQ: {eoq}, Lead: {metrics.lead_time_days}d, "
                    f"Demand: {metrics.daily_avg_demand:.1f}/day). "
                    f"Urgency: {urgency.value}."
                )
            else:
                reason = (
                    f"{sku}: Effective Stock {effective_stock} >= ROP {reorder_point}. "
                    f"No reorder needed (EOQ: {eoq}, Lead: {metrics.lead_time_days}d). "
                    f"Next review in {max(1, int(effective_stock / max(1, metrics.daily_avg_demand)))} days."
                )

            # Calculate Utility Score (Stockout Penalty)
            utility_score = self.calculate_utility_score(metrics)

            return DecisionResult(
                reorder_required=reorder_required,
                order_quantity=order_qty,
                urgency_level=urgency,
                reason=reason,
                details=details,
                cost_analysis=cost_analysis,
                utility_score=utility_score
            )

        except Exception as e:
            logger.error(f"Decision error for {sku_item.get('sku', 'UNKNOWN')}: {str(e)}")
            # Fallback: conservative reorder
            current = sku_item.get("quantity", 0)
            threshold = sku_item.get("threshold", 10)
            if current < threshold:
                order_qty = int(threshold * 1.5 - current)
            else:
                order_qty = 0
            
            return DecisionResult(
                reorder_required=order_qty > 0,
                order_quantity=order_qty,
                urgency_level=UrgencyLevel.MEDIUM if order_qty > 0 else UrgencyLevel.DEFERRED,
                reason=f"Decision calculation failed; using baseline",
                details={"error": str(e)},
                cost_analysis={},
                utility_score=100.0 # Default fallback utility
            )
