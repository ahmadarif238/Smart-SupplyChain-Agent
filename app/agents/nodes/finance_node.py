# app/agents/nodes/finance_node.py
import logging
from typing import Dict, Any, List
from app.agents.state import CycleState

logger = logging.getLogger("finance_node")
from app.config.settings import settings

class FinanceNode:
    """
    Finance Agent: The Budget Controller with LLM-powered Negotiation.
    
    Role:
    - Reviews proposed purchase orders
    - Enforces budget constraints with ROI prioritization
    - Negotiates with Decision Agent using natural language
    - Can override rejections for critical orders
    """
    
    def __init__(self):
        self.default_budget = settings.DEFAULT_BUDGET
    
    def review_orders(self, state: CycleState) -> Dict[str, Any]:
        """
        Review decisions and enforce budget constraints using ROI, Dynamic Budgeting,
        and LLM-powered agent negotiation.
        """
        from app.agents.dialogue_generator import dialogue_generator
        
        # 1. Calculate Dynamic Budget (Cash Flow Model)
        base_budget = settings.DEFAULT_BUDGET
        revenue_factor = settings.REVENUE_REINVESTMENT_RATE
        dynamic_budget = base_budget + (state.recent_sales_revenue * revenue_factor)
        
        logger.info(f"💰 Finance Agent: Budget set to ${dynamic_budget:.2f}")
        
        decisions = state.decisions
        reorders = [d for d in decisions if d.get('reorder_required')]
        
        if not reorders:
            logger.info("💰 Finance Agent: No reorders to review.")
            return {
                "finance_feedback": f"Budget: ${dynamic_budget:.2f}. No orders proposed.",
                "budget_remaining": dynamic_budget,
                "decisions": [],
                "rejected_decisions": []
            }
        
        # Clear old negotiation proposals ONLY at start of cycle (Round 0)
        # If we are in a negotiation loop (Round > 0), we must KEEP them!
        if getattr(state, 'negotiation_rounds', 0) == 0:
            state.negotiation_proposals = []
            state.finance_rejections = []  # Clear old rejections from previous cycle
            logger.info("💰 Finance Agent: Cleared previous negotiation proposals and rejections (Round 0)")
        else:
            logger.info(f"💰 Finance Agent: Preserving negotiation proposals for Round {state.negotiation_rounds}")
            
        scored_decisions = []
        
        # 2. Calculate ROI for each order
        for decision in reorders:
            # CHECK FOR NEGOTIATION PROPOSALS FIRST!
            # If this SKU has been negotiated, use the reduced quantity
            negotiated_qty = None
            negotiated_cost = None
            
            if hasattr(state, 'negotiation_proposals') and state.negotiation_proposals:
                for proposal in state.negotiation_proposals:
                    if proposal.get('sku') == decision.get('sku'):
                        negotiated_qty = proposal.get('new_quantity')
                        negotiated_cost = proposal.get('new_cost')
                        logger.info(f"💬 Using negotiated amount for {decision.get('sku')}: {negotiated_qty} units (was {decision.get('order_quantity')})")
                        break
            
            # Use negotiated values if available, otherwise use original
            if negotiated_qty is not None:
                qty = negotiated_qty
                decision['order_quantity'] = qty  # PERSIST CHANGE for next round!
            else:
                qty = decision.get("order_quantity", 0)
            
            details = decision.get("details", {})
            cost_analysis = decision.get("cost_analysis", {})
            
            # Use the correct purchasing cost, falling back to details, then default
            unit_cost = (
                cost_analysis.get("purchasing_cost_per_unit") or 
                details.get("unit_price") or 
                10.0
            )
            
            # If we have a pre-calculated negotiated cost, use it
            if negotiated_cost is not None:
                total_cost = negotiated_cost
            else:
                total_cost = qty * unit_cost
            
            # DEBUG LOG
            if total_cost > 1000:
                logger.info(f"💰 FinanceNode: {decision.get('sku', 'UNKNOWN')} qty={qty} unit_cost={unit_cost} total={total_cost}")
            
            # Calculate ROI and stockout risk
            daily_demand = float(details.get("daily_avg_demand", 0))
            lead_time = int(details.get("lead_time_days", 7))
            current_stock = int(details.get("current_stock", 0))
            
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

        # 3. Optimize Budget Allocation using LP Solver
        logger.info(f"🧮 Finance Agent: Solving LP for budget ${dynamic_budget:.2f}")
        allocation_result = self._solve_budget_allocation(scored_decisions, dynamic_budget, state)
        
        approved_decisions = allocation_result['approved']
        rejected_decisions = allocation_result['rejected']
        current_spend = allocation_result['total_spend']
        total_roi = allocation_result['total_roi']
        
        # Log results
        logger.info(f"✅ LP Solution: Approved {len(approved_decisions)} orders, Cost ${current_spend:.2f}, Total Value ${total_roi:.2f}")
        
        # 4. Process Rejections and Log Dialogue
        for decision in rejected_decisions:
            sku = decision.get('sku')
            product_name = decision.get('product_name')
            cost = decision['finance_metrics']['total_cost']
            
            budget_exceeded = cost - (dynamic_budget - current_spend) # Rough approximation for reason
            
            # Generate LLM rejection message (Returns FIPA Dict)
            rejection_msg_dict = dialogue_generator.generate_rejection(
                agent="Finance",
                sku=sku,
                product_name=product_name,
                cost=cost,
                budget_remaining=dynamic_budget - current_spend,
                reason=f"Budget exceeded by approx ${budget_exceeded:.2f} (Optimizer dropped this)"
            )
            
            msg_text = rejection_msg_dict['content']['message']
            
            # Add to dialogue log
            state.agent_dialogues.append({
                "agent": "Finance",
                "target": "Decision",
                "message": msg_text,
                "type": "rejection",
                "sku": sku,
                "fipa": rejection_msg_dict
            })
            
            # CRITICAL: Add to finance_rejections list for negotiation!
            state.finance_rejections.append(decision)
            logger.debug(f"Finance stored rejection for {sku}. Total rejections: {len(state.finance_rejections)}")
            
            logger.warning(f"❌ Finance: {msg_text}")
        
        logger.info(f"💰 Finance Agent: {len(approved_decisions)} approved, {len(state.finance_rejections)} rejected for negotiation")
        
        # 5. Handle Negotiation Overrides (Win condition from previous rounds)
        for decision in approved_decisions:
             if decision.get('override_approved'):
                 # It was approved because of negotiation, log the "Yes"
                 sku = decision.get('sku')
                 product_name = decision.get('product_name')
                 cost = decision['finance_metrics']['total_cost']
                 roi = decision['finance_metrics']['roi']
                 
                 override_msg_dict = dialogue_generator.generate_override_approval(
                    agent="Finance",
                    sku=sku,
                    product_name=product_name,
                    roi=roi,
                    cost=cost,
                    justification="Counter-argument accepted (High ROI/Projected Value)."
                 )
                 
                 msg_text = override_msg_dict['content']['message']
                 
                 state.agent_dialogues.append({
                    "agent": "Finance",
                    "target": "Decision",
                    "message": msg_text,
                    "type": "override_approval",
                    "sku": sku,
                    "fipa": override_msg_dict
                })

        # Construct feedback
        overrides = len([d for d in approved_decisions if d.get('override_approved')])
        feedback = f"Budget: ${dynamic_budget:.2f} | Spent: ${current_spend:.2f} | Approved: {len(approved_decisions)} | Rejected: {len(rejected_decisions)}"
        if overrides > 0:
            feedback += f" | {overrides} Override(s) granted"
        
        # Update state
        state.decisions = approved_decisions
        # Note: finance_rejections already populated in rejection loop (line ~171)
        # No need to overwrite here - would cause duplicates or clear negotiation state
        state.finance_feedback = feedback
        state.budget = dynamic_budget
        state.budget_remaining = dynamic_budget - current_spend
        
        return {
            "decisions": approved_decisions,
            "rejected_decisions": rejected_decisions,
            "finance_feedback": feedback,
            "budget_remaining": dynamic_budget - current_spend,
            "overrides": overrides
        }

    def _solve_budget_allocation(self, decisions: List[Dict], budget: float, state: CycleState) -> Dict[str, Any]:
        """
        Solves the budget allocation problem using Linear Programming (Knapsack-style).
        Objective: Maximize Total ROI/Value
        Constraint: Total Cost <= Budget
        """
        import pulp
        
        if not decisions:
            return {"approved": [], "rejected": [], "total_spend": 0.0, "total_roi": 0.0}
            
        # Create LP problem
        prob = pulp.LpProblem("Budget_Allocation", pulp.LpMaximize)
        
        # Create binary variables for each decision (1 = approve, 0 = reject)
        # Use index as ID to avoid special character issues in SKU names
        decision_vars = pulp.LpVariable.dicts("Order", range(len(decisions)), cat='Binary')
        
        # Objective Function: Maximize Total Value (Projected Value)
        # We use 'projected_value' from finance_metrics, which accounts for ROI calculations
        prob += pulp.lpSum([
            decisions[i]['finance_metrics']['projected_value'] * decision_vars[i] 
            for i in range(len(decisions))
        ]), "Total_Value"
        
        # Constraint: Budget
        prob += pulp.lpSum([
            decisions[i]['finance_metrics']['total_cost'] * decision_vars[i] 
            for i in range(len(decisions))
        ]) <= budget, "Budget_Constraint"
        
        # Solve
        # Suppress output
        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        
        # Extract results
        approved = []
        rejected = []
        total_spend = 0.0
        total_roi = 0.0
        
        status = pulp.LpStatus[prob.status]
        logger.info(f"🧮 LP Solver Status: {status}")
        
        for i in range(len(decisions)):
            if pulp.value(decision_vars[i]) == 1:
                approved.append(decisions[i])
                total_spend += decisions[i]['finance_metrics']['total_cost']
                total_roi += decisions[i]['finance_metrics']['projected_value']
                
                # Log if this was a negotiator win (previously rejected, now approved via ROI boost)
                counter_args = getattr(state, 'counter_arguments', [])
                sku = decisions[i]['sku']
                if any(ca['sku'] == sku for ca in counter_args):
                    decision = decisions[i]
                    decision['override_approved'] = True
                    decision['override_reason'] = "LP Solver Selection (Negotiation Boost)"
                    
            else:
                # Add rejection reason
                decision = decisions[i]
                cost = decision['finance_metrics']['total_cost']
                decision['rejection_reason'] = "Budget Optimization (LP Solver)"
                decision['order_value'] = cost
                rejected.append(decision)
                
        return {
            "approved": approved,
            "rejected": rejected,
            "total_spend": total_spend,
            "total_roi": total_roi,
            "status": status
        }

    def evaluate_proposal(self, decision: Dict, state: CycleState) -> Dict:
        """
        Evaluate a single FIPA PROPOSE message from Decision Agent.
        Decides whether to accept the counter-proposal (ACCEPT-PROPOSAL) or reject it.
        """
        sku = decision.get('sku')
        fin_metrics = decision.get('finance_metrics', {})
        stockout_value = fin_metrics.get('projected_value', 0)
        order_cost = fin_metrics.get('total_cost', 0)
        
        # FALLBACK: If Finance calculates 0 value (missing demand data), 
        # but Decision says it's critical, assume high value (Safety Stock).
        heuristic_applied = False
        if stockout_value <= 1.0:
            heuristic_applied = True
            stockout_value = order_cost * settings.CRITICAL_STOCK_ROI_MULTIPLIER  # Boost ROI for critical safety stock
        
        calculated_roi = stockout_value / max(order_cost, 1.0)
        
        # ANEX Decision Logic: Accept if ROI > Threshold
        roi_threshold = settings.NEGOTIATION_ROI_THRESHOLD
        approved = False
        reason_msg = ""
        
        if stockout_value > order_cost * roi_threshold:
            approved = True
            reason_msg = f"ROI {calculated_roi:.2f}x exceeds negotiated threshold"
            if heuristic_applied:
                reason_msg += " (Critical Safety Stock Priority)"
                
        return {
            "approved": approved,
            "reason": reason_msg,
            "roi": calculated_roi
        }
    
    def re_optimize_with_proposals(self, state: CycleState) -> Dict[str, Any]:
        """
        RE-OPTIMIZE budget allocation with quantity-reduced proposals from negotiation.
        This is the PRODUCTION-QUALITY approach: re-run LP solver to find global optimum.
        
        Called in Round 1+ (after negotiation generates proposals).
        """
        from app.agents.dialogue_generator import dialogue_generator
        import copy
        
        logger.info(f"🔄 Finance: Re-optimizing with {len(state.negotiation_proposals)} proposals")
        
        # 1. Calculate budget (same as initial review)
        base_budget = settings.DEFAULT_BUDGET
        revenue_factor = settings.REVENUE_REINVESTMENT_RATE
        dynamic_budget = base_budget + (state.recent_sales_revenue * revenue_factor)
        
        # 2. Collect ALL candidates for re-optimization
        candidates = []
        
        # Process negotiation proposals (reduced quantities)
        for proposal in state.negotiation_proposals:
            sku = proposal['sku']
            
            # Find the original rejected decision
            original_decision = None
            for rejected in state.finance_rejections:
                if rejected.get('sku') == sku:
                    original_decision = rejected
                    break
            
            if not original_decision:
                logger.warning(f"⚠️ Proposal for {sku} has no matching rejection. Skipping.")
                continue
            
            # Create a new decision with reduced quantity
            reduced_decision = copy.deepcopy(original_decision)
            reduced_decision['order_quantity'] = proposal['new_quantity']
            reduced_decision['negotiated'] = True
            reduced_decision['original_quantity'] = proposal['original_quantity']
            reduced_decision['reduction_factor'] = proposal.get('reduction_factor', 0.5)
            
            # Update finance metrics with new cost
            reduced_decision['finance_metrics']['total_cost'] = proposal['new_cost']
            
            # CRITICAL: Ensure projected_value is non-zero
            # If original projected_value was 0 (no demand data), use heuristic
            original_projected_value = reduced_decision['finance_metrics'].get('projected_value', 0)
            
            if original_projected_value <= 1.0:
                # Apply heuristic: critical stock items have value = cost * ROI multiplier
                heuristic_value = proposal['new_cost'] * settings.CRITICAL_STOCK_ROI_MULTIPLIER
                reduced_decision['finance_metrics']['projected_value'] = heuristic_value
                logger.info(f"Applied heuristic value for {sku}: ${heuristic_value:.2f} (was ${original_projected_value:.2f})")
            # Else: Keep original projected_value (it's based on daily demand, not quantity)
            
            # Recalculate ROI with new cost
            projected_value = reduced_decision['finance_metrics']['projected_value']
            new_roi = projected_value / max(proposal['new_cost'], 1.0)
            reduced_decision['finance_metrics']['roi'] = new_roi
            
            candidates.append(reduced_decision)
            logger.info(f"✅ Candidate: {sku} qty={proposal['new_quantity']} cost=${proposal['new_cost']:.2f} value=${projected_value:.2f} ROI={new_roi:.2f}x")

        
        if not candidates:
            logger.warning("⚠️ No valid candidates after negotiation. Returning empty.")
            return {
                "finance_feedback": "No proposals could be processed.",
                "budget_remaining": dynamic_budget,
                "decisions": [],
                "rejected_decisions": []
            }
        
        # 3. RE-RUN LP SOLVER to find optimal allocation
        logger.info(f"🧮 Re-running LP solver with {len(candidates)} negotiated candidates, budget=${dynamic_budget:.2f}")
        
        # DEBUG: Log all candidates before LP
        logger.info("="*80)
        logger.info("CANDIDATES FOR LP SOLVER:")
        for i, cand in enumerate(candidates):
            sku = cand.get('sku')
            cost = cand['finance_metrics']['total_cost']
            value = cand['finance_metrics']['projected_value']
            qty = cand.get('order_quantity')
            logger.info(f"  [{i}] {sku}: qty={qty}, cost=${cost:.2f}, value=${value:.2f}, ratio={value/cost if cost>0 else 0:.2f}")
        logger.info(f"BUDGET: ${dynamic_budget:.2f}")
        logger.info("="*80)
        
        allocation_result = self._solve_budget_allocation(candidates, dynamic_budget, state)
        
        approved_decisions = allocation_result['approved']
        rejected_decisions = allocation_result['rejected']
        current_spend = allocation_result['total_spend']
        total_roi = allocation_result['total_roi']
        
        logger.info(f"✅ Re-optimization: Approved {len(approved_decisions)}, Spend ${current_spend:.2f}, Value ${total_roi:.2f}")
        
        # 4. Generate dialogue for approvals
        for decision in approved_decisions:
            sku = decision.get('sku')
            product_name = decision.get('product_name')
            new_qty = decision.get('order_quantity')
            original_qty = decision.get('original_quantity', new_qty)
            cost = decision['finance_metrics']['total_cost']
            
            # Generate acceptance message
            acceptance_msg = (
                f"✅ ACCEPT-PROPOSAL: {product_name} approved with reduced quantity "
                f"({new_qty} units, {new_qty/original_qty*100:.0f}% of original). "
                f"Cost: ${cost:.2f}"
            )
            
            state.agent_dialogues.append({
                "agent": "Finance",
                "target": "Decision",
                "message": acceptance_msg,
                "type": "accept_proposal",
                "sku": sku,
                "fipa": {
                    "performative": "ACCEPT-PROPOSAL",
                    "sender": "Finance",
                    "receiver": "Decision",
                    "content": {
                        "sku": sku,
                        "approved_quantity": new_qty,
                        "cost": cost
                    }
                }
            })
            
            logger.info(f"✅ {acceptance_msg}")
        
        # 5. Generate dialogue for rejections
        for decision in rejected_decisions:
            sku = decision.get('sku')
            product_name = decision.get('product_name')
            cost = decision['finance_metrics']['total_cost']
            
            rejection_msg = f"❌ REJECT-PROPOSAL: {product_name} - Budget exhausted after optimizing approvals"
            
            state.agent_dialogues.append({
                "agent": "Finance",
                "target": "Decision",
                "message": rejection_msg,
                "type": "reject_proposal",
                "sku": sku
            })
        
        # 6. Construct feedback
        feedback = f"Re-Optimized: Budget ${dynamic_budget:.2f} | Spent ${current_spend:.2f} | Approved {len(approved_decisions)} | Rejected {len(rejected_decisions)}"
        
        # 7. Update state
        state.decisions = approved_decisions
        state.finance_rejections = rejected_decisions  # Update with final rejections
        state.finance_feedback = feedback
        state.budget = dynamic_budget
        state.budget_remaining = dynamic_budget - current_spend
        
        return {
            "decisions": approved_decisions,
            "rejected_decisions": rejected_decisions,
            "finance_feedback": feedback,
            "budget_remaining": dynamic_budget - current_spend,
            "overrides": 0  # No overrides in re-optimization
        }
