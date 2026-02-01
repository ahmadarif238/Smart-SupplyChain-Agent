# app/agents/nodes/finance_node.py
import logging
from typing import Dict, Any, List
from app.agents.state import CycleState

logger = logging.getLogger("finance_node")
from app.config.settings import settings

class FinanceNode:
    """
    Finance Agent: The Budget Controller.
    
    Role:
    - Reviews proposed purchase orders
    - Enforces budget constraints using LP Solver (ROI prioritization)
    - Returns approved orders
    """
    
    def __init__(self):
        self.default_budget = settings.DEFAULT_BUDGET
    
    def review_orders(self, state: CycleState) -> Dict[str, Any]:
        """
        Review decisions and enforce budget constraints.
        """
        
        # 1. Use budget from state (which is dynamically loaded in run_cycle)
        base_budget = state.budget if state.budget > 0 else settings.DEFAULT_BUDGET
        revenue_factor = settings.REVENUE_REINVESTMENT_RATE
        dynamic_budget = base_budget + (state.recent_sales_revenue * revenue_factor)
        
        logger.info(f"💰 Finance Agent: Budget set to ${dynamic_budget:.2f}")
        
        decisions = state.decisions
        reorders = [d for d in decisions if d.get('reorder_required')]
        
        if not reorders:
            return {
                "finance_feedback": f"Budget: ${dynamic_budget:.2f}. No orders proposed.",
                "budget_remaining": dynamic_budget,
                "decisions": [],
                "rejected_decisions": []
            }
        
        scored_decisions = []
        
        # 2. Calculate ROI for each order
        for decision in reorders:
            qty = decision.get("order_quantity", 0)
            details = decision.get("details", {})
            cost_analysis = decision.get("cost_analysis", {})
            
            unit_cost = (
                cost_analysis.get("purchasing_cost_per_unit") or 
                details.get("unit_price") or 
                10.0
            )
            
            total_cost = qty * unit_cost
            
            # ROI calculation
            # For threshold_override decisions, use a high default projected value
            is_override = details.get("type") == "threshold_override" or details.get("type") == "fallback"
            
            daily_demand = float(details.get("daily_avg_demand", 0))
            lead_time = int(details.get("lead_time_days", 7))
            current_stock = int(details.get("current_stock", 0))
            
            # If this is an override decision with no demand data, use threshold-based urgency
            if is_override and daily_demand == 0:
                # High urgency override - give it maximum priority
                projected_value = total_cost * 10  # 10x multiplier ensures approval
                roi = 10.0
                stockout_risk_factor = 10.0  # Maximum urgency
                days_until_stockout = 0  # Critical
            else:
                days_until_stockout = current_stock / daily_demand if daily_demand > 0 else 999
                
                stockout_risk_factor = 1.0
                if days_until_stockout < lead_time:
                    stockout_risk_factor = settings.STOCKOUT_RISK_HIGH_MULTIPLIER
                elif days_until_stockout < lead_time * 2:
                    stockout_risk_factor = settings.STOCKOUT_RISK_MEDIUM_MULTIPLIER
                    
                margin = unit_cost * 0.5
                projected_value = margin * daily_demand * 30 * stockout_risk_factor
                roi = projected_value / max(total_cost, 1.0)
            
            decision['finance_metrics'] = {
                "total_cost": total_cost,
                "roi": roi,
                "stockout_risk_factor": stockout_risk_factor,
                "days_until_stockout": days_until_stockout,
                "projected_value": projected_value
            }
            
            scored_decisions.append(decision)

        # 3. Optimize Budget Allocation
        allocation_result = self._solve_budget_allocation(scored_decisions, dynamic_budget, state)
        
        approved_decisions = allocation_result['approved']
        rejected_decisions = allocation_result['rejected']
        current_spend = allocation_result['total_spend']
        
        logger.info(f"💰 Finance Review: Approved {len(approved_decisions)}, Rejected {len(rejected_decisions)}, Spend ${current_spend:.2f}")
        
        # Update state
        state.decisions = approved_decisions
        state.budget = dynamic_budget
        state.budget_remaining = dynamic_budget - current_spend
        state.finance_rejections = rejected_decisions
        
        feedback = f"Budget: ${dynamic_budget:.2f} | Spent: ${current_spend:.2f} | Approved: {len(approved_decisions)}"
        state.finance_feedback = feedback

        return {
            "decisions": approved_decisions,
            "rejected_decisions": rejected_decisions,
            "finance_feedback": feedback,
            "budget_remaining": dynamic_budget - current_spend
        }

    def _solve_budget_allocation(self, decisions: List[Dict], budget: float, state: CycleState) -> Dict[str, Any]:
        """
        Solves the budget allocation problem using Linear Programming.
        """
        import pulp
        
        if not decisions:
            return {"approved": [], "rejected": [], "total_spend": 0.0, "total_roi": 0.0}
            
        prob = pulp.LpProblem("Budget_Allocation", pulp.LpMaximize)
        decision_vars = pulp.LpVariable.dicts("Order", range(len(decisions)), cat='Binary')
        
        # Objective: Maximize Value
        prob += pulp.lpSum([
            decisions[i]['finance_metrics']['projected_value'] * decision_vars[i] 
            for i in range(len(decisions))
        ]), "Total_Value"
        
        # Constraint: Budget
        prob += pulp.lpSum([
            decisions[i]['finance_metrics']['total_cost'] * decision_vars[i] 
            for i in range(len(decisions))
        ]) <= budget, "Budget_Constraint"
        
        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        
        approved = []
        rejected = []
        total_spend = 0.0
        total_roi = 0.0
        
        for i in range(len(decisions)):
            if pulp.value(decision_vars[i]) == 1:
                approved.append(decisions[i])
                total_spend += decisions[i]['finance_metrics']['total_cost']
                total_roi += decisions[i]['finance_metrics']['projected_value']
            else:
                decision = decisions[i]
                decision['rejection_reason'] = "Budget Constraint"
                rejected.append(decision)
                
        return {
            "approved": approved,
            "rejected": rejected,
            "total_spend": total_spend,
            "total_roi": total_roi
        }
