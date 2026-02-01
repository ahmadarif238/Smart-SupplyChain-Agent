# app/routes/agent.py
import uuid
import logging
import json
import time
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from threading import Thread
from datetime import datetime
from collections import deque
from sqlalchemy.orm import Session
from app.models.database import SessionLocal, get_db
from app.models import schemas
from app.agents.langgraph_flow import agent_controller
from app.agents.langgraph_workflow import run_cycle
from app.auth.dependencies import get_current_user
from app.agents.streaming import job_stream_manager

logger = logging.getLogger("agent_routes")
router = APIRouter(prefix="/agent", tags=["Agent"])



def log_progress(job_id: str, stage: str, message: str, details: dict = None):
    """Log a progress event for streaming"""
    job_stream_manager.log_event(job_id, "progress", message, details, stage)

def _execute_agent_cycle(job_id: str):
    """
    Execute agent cycle with progress tracking using LangGraph.
    Persists state to Database.
    """
    db = SessionLocal()
    try:
        # 1. Start Job
        job = db.query(schemas.Job).filter(schemas.Job.id == job_id).first()
        if job:
            job.status = "running"
            job.started_at = datetime.utcnow()
            db.commit()
            
        log_progress(job_id, "INIT", "🚀 Agent cycle started. Initializing workflow...", {"job_id": job_id})
        
        # 2. Run LangGraph cycle (Blocking call, emits events internally)
        # Note: We removed the "fake" previous logs. Real logs come from the workflow now.
        result = run_cycle(job_id)
        
        # 3. Complete Job
        # Re-query to avoid stale object issues
        job = db.query(schemas.Job).filter(schemas.Job.id == job_id).first()
        if job:
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.result = json.dumps(result) # Store as JSON string
            db.commit()

        log_progress(job_id, "COMPLETE", "✨ Agent cycle completed successfully!", {
            "skus_processed": result.get("skus_processed", 0),
            "status": "completed"
        })
        
        logger.info(f"Job {job_id}: Completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id}: Failed - {e}", exc_info=True)
        
        # Log error to stream
        log_progress(job_id, "ERROR", f"Agent cycle failed: {str(e)}", {"error_type": type(e).__name__})
        
        # Update DB status
        try:
            job = db.query(schemas.Job).filter(schemas.Job.id == job_id).first()
            if job:
                job.status = "failed"
                job.error = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        except:
            pass # DB connection might be broken
            
    finally:
        db.close()

@router.post("/run_once")
def run_once_async(background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Start agent in background - returns immediately.
    Persists initial job state to DB.
    """
    job_id = str(uuid.uuid4())[:8]
    
    # Create Job in DB
    new_job = schemas.Job(
        id=job_id,
        status="queued",
        created_at=datetime.utcnow()
    )
    db.add(new_job)
    db.commit()
    
    # Start background task using FastAPI BackgroundTasks (ThreadPool)
    background_tasks.add_task(_execute_agent_cycle, job_id)
    
    logger.info(f"Job {job_id}: Queued for execution")
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Agent cycle started in background",
        "created_at": new_job.created_at
    }

@router.post("/run_once_test")
def run_once_test(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Start agent in background (NO AUTH) - for testing only
    """
    job_id = str(uuid.uuid4())[:8]
    
    # Create Job in DB
    new_job = schemas.Job(
        id=job_id,
        status="queued",
        created_at=datetime.utcnow()
    )
    db.add(new_job)
    db.commit()
    
    # Start background task
    background_tasks.add_task(_execute_agent_cycle, job_id)
    
    logger.info(f"Test Job {job_id}: Queued for execution")
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Agent cycle started in background (TEST)",
        "created_at": new_job.created_at
    }

@router.get("/job/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Get job status from Database"""
    job = db.query(schemas.Job).filter(schemas.Job.id == job_id).first()
    
    if not job:
        return {"error": f"Job {job_id} not found"}, 404
    
    # Parse result JSON if it exists
    result_data = None
    if job.result:
        try:
            result_data = json.loads(job.result)
        except:
            result_data = job.result
    
    return {
        "id": job.id,
        "status": job.status,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "result": result_data,
        "error": job.error,
        "summary": job.summary
    }

@router.get("/job_test/{job_id}")
def get_job_status_test(job_id: str, db: Session = Depends(get_db)):
    """Get job status (NO AUTH) - for testing only"""
    job = db.query(schemas.Job).filter(schemas.Job.id == job_id).first()
    
    if not job:
        return {"error": f"Job {job_id} not found"}, 404
        
    # Parse result JSON if it exists
    result_data = None
    if job.result:
        try:
            result_data = json.loads(job.result)
        except:
            result_data = job.result
            
    return {
        "id": job.id,
        "status": job.status,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "result": result_data,
        "error": job.error
    }

@router.get("/stream/{job_id}")
async def stream_job_progress(job_id: str, token: str = None, current_user = None, db: Session = Depends(get_db)):
    """
    Stream job progress with detailed events.
    Polling the stream manager (memory) and fallback to DB for status.
    """
    # Validate authentication
    if token:
        from jose import jwt
        from app.auth.security import SECRET_KEY, ALGORITHM
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception as e:
            logger.warning(f"Invalid token provided for stream: {e}")
            # Strict mode: If token is provided but invalid, reject.
            # If no token provided (token=None), we might allow read-only or fail depending on policy.
            # Here assuming optional token if not provided in arg, but if provided must be valid.
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    # We verify job exists in DB first
    # Note: We need a new session for the generator ideally, or just use one-off query
    # Using SessionLocal inside generator is safer for long-lived streams
    
    async def progress_generator():
        sent_events = set()
        last_status = None
        
        yield f"data: {json.dumps({'type': 'connection', 'job_id': job_id, 'message': '📡 Connected to agent stream...'})}\n\n"
        
        # Poll for updates
        for _ in range(600): # 10 minutes timeout
            # 1. Get events from memory queue
            queue = job_stream_manager.get_queue(job_id)
            queue_snapshot = list(queue)
            
            for event in queue_snapshot:
                event_key = (event["timestamp"], event["stage"], event["message"])
                if event_key not in sent_events:
                    sent_events.add(event_key)
                    
                    # Formatting
                    if event.get("type") == "progress":
                        stage_emoji = {
                            "INIT": "🚀", "FETCH": "📥", "FORECAST": "🔮",
                            "DECISION": "🤔", "ACTION": "⚡", "COMPLETE": "✅", "ERROR": "❌",
                            "FINANCE": "💰", "MEMORY": "💾"
                        }.get(event.get("stage"), "ℹ️")
                        
                        msg = {
                            "type": "progress", 
                            "stage": event["stage"],
                            "message": f"{stage_emoji} {event['message']}",
                            "details": event.get("details"),
                            "timestamp": event["timestamp"]
                        }
                    else:
                        msg = event
                        
                    yield f"data: {json.dumps(msg)}\n\n"

            # 2. Check Job Status from DB (periodically or every loop)
            # We open a short-lived session to check status
            scope_db = SessionLocal()
            try:
                job = scope_db.query(schemas.Job).filter(schemas.Job.id == job_id).first()
                if job:
                    current_status = job.status
                    
                    if current_status != last_status:
                        # Status changed
                        status_msg = {"type": "status", "status": current_status, "timestamp": datetime.utcnow().isoformat()}
                        
                        if current_status == "completed":
                            status_msg["message"] = "🎉 Agent cycle completed!"
                            # Include result in completion message if feasible
                            if job.result:
                                try:
                                    status_msg["result"] = json.loads(job.result)
                                except:
                                    pass
                            yield f"data: {json.dumps(status_msg)}\n\n"
                            break # Done
                            
                        elif current_status == "failed":
                            status_msg["message"] = f"⚠️ Failed: {job.error}"
                            status_msg["error"] = job.error
                            yield f"data: {json.dumps(status_msg)}\n\n"
                            break # Done
                        
                        else:
                            yield f"data: {json.dumps(status_msg)}\n\n"
                            
                        last_status = current_status
                else:
                    # Job not found in DB?
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found in DB'})}\n\n"
                    break
                    
            except Exception as e:
                logger.error(f"Stream DB Error: {e}")
            finally:
                scope_db.close()
                
            await asyncio.sleep(0.5)
            
        yield f"data: {json.dumps({'type': 'close', 'message': 'Stream closed'})}\n\n"

    return StreamingResponse(progress_generator(), media_type="text/event-stream")

@router.get("/jobs")
def list_jobs(limit: int = 50, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """List recent agent jobs from DB"""
    jobs = db.query(schemas.Job).order_by(schemas.Job.created_at.desc()).limit(limit).all()
    
    return {
        "total": len(jobs), # Approximate
        "recent_jobs": [
            {
                "id": j.id,
                "status": j.status,
                "created_at": j.created_at,
                "completed_at": j.completed_at
            } for j in jobs
        ]
    }

@router.get("/finance-summary")
def get_finance_summary(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Get finance summary from persisted jobs"""
    # 1. Load Dynamic Budget
    import os
    current_budget = 5000.0
    try:
        config_path = os.path.join("app", "config", "dynamic_settings.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
                current_budget = float(data.get("budget", 5000.0))
    except:
        pass

    # Get last 10 completed jobs for spending history
    completed_jobs = db.query(schemas.Job).filter(
        schemas.Job.status == "completed",
        schemas.Job.result.isnot(None)
    ).order_by(schemas.Job.completed_at.desc()).limit(10).all()
    
    total_spent = 0
    total_overrides = 0
    total_roi_sum = 0
    roi_count = 0
    total_approved = 0
    
    if completed_jobs:
        for job in completed_jobs:
            try:
                result = json.loads(job.result)
                
                # Extract metrics
                actions = result.get("actions", [])
                total_approved += len(actions)
                
                decisions = result.get("decisions", [])
                for d in decisions:
                    if d.get("override_approved"):
                        total_overrides += 1
                    if d.get("finance_metrics", {}).get("roi"):
                        total_roi_sum += d["finance_metrics"]["roi"]
                        roi_count += 1
                    
            except Exception as e:
                logger.error(f"Error parsing job {job.id}: {e}")
                continue
    
    # Calculate ACTUAL spending from RECENT approved orders (last 7 days only)
    # This prevents old historical orders from eating up the current budget
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    approved_orders = db.query(schemas.Orders).filter(
        schemas.Orders.status.in_(["Approved", "Pending", "Completed"]),
        schemas.Orders.order_date >= seven_days_ago  # Only recent orders
    ).all()
    
    for order in approved_orders:
        # Get unit price from inventory
        inventory_item = db.query(schemas.Inventory).filter(
            schemas.Inventory.sku == order.sku
        ).first()
        
        if inventory_item and inventory_item.unit_price:
            total_spent += order.quantity * inventory_item.unit_price
            
    remaining = max(0, current_budget - total_spent)
    avg_roi = total_roi_sum / roi_count if roi_count > 0 else 0
    
    return {
        "current_budget": current_budget,
        "spent": round(total_spent, 2),
        "remaining": round(remaining, 2),
        "approved_count": total_approved,
        "rejected_count": 0,
        "override_count": total_overrides,
        "avg_roi": round(avg_roi, 2),
        "total_value": round(total_spent, 2),
        "cycles_analyzed": len(completed_jobs)
    }

@router.get("/jobs/{job_id}/summary")
def get_job_summary(job_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Generate or retrieve AI summary for a job"""
    job = db.query(schemas.Job).filter(schemas.Job.id == job_id).first()
    
    if not job:
        return {"error": "Job not found"}, 404
        
    if job.summary:
        return {"summary": job.summary, "job_id": job.id}
        
    if job.status != "completed" or not job.result:
        return {"error": "Job not completed or no result"}, 400
        
    try:
        result = json.loads(job.result)
        from app.services.llm_service import call_gemini_api
        
        # Build context
        decisions = result.get("decisions", [])
        actions = result.get("actions", [])
        finance_feedback = result.get("finance_feedback", "No finance data")
        
        prompt = f"""Analyze this supply chain agent cycle and create a concise executive summary.

AGENT CYCLE RESULTS:
- SKUs Processed: {result.get('skus_processed', 0)}
- Reorder Decisions: {len([d for d in decisions if d.get('reorder_required')])}
- Actions Executed: {len(actions)}
- Finance: {finance_feedback}

DECISIONS DETAIL:
{json.dumps(decisions[:5], indent=2) if decisions else "No decisions made"}

ACTIONS EXECUTED:
{json.dumps(actions[:5], indent=2) if actions else "No actions taken"}

Create a 3-4 sentence summary highlighting:
1. What the agent detected (demand patterns, stock levels)
2. Key decisions and actions taken
3. Budget/finance impact
4. Any notable negotiations or overrides

Be concise and executive-focused."""

        messages = [{"role": "user", "content": prompt}]
        summary_text = call_gemini_api(
            model="gemini-2.5-flash",
            messages=messages,
            temperature=0.3, 
            max_tokens=500
        )
        
        # Save to DB
        job.summary = summary_text
        db.commit()
        
        return {"summary": summary_text, "job_id": job.id}
        
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return {"error": f"Summary generation failed: {str(e)}"}, 500
@router.post("/settings/budget")
def update_budget(data: dict, current_user = Depends(get_current_user)):
    """Update agent operating budget dynamically"""
    import os
    
    new_budget = data.get("budget")
    if new_budget is None:
        raise HTTPException(status_code=400, detail="Budget is required")
        
    try:
        config_path = os.path.join("app", "config", "dynamic_settings.json")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        settings_data = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    settings_data = json.load(f)
            except:
                pass
                
        settings_data["budget"] = float(new_budget)
        
        with open(config_path, "w") as f:
            json.dump(settings_data, f)
            
        return {"message": "Budget updated successfully", "budget": new_budget}
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
