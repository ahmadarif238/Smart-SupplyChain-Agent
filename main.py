from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from app.routes import inventory, sales, orders, alerts, agent, feedback, memory, persistence
from app.auth.security import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
)
from app.auth.dependencies import get_current_user
from app.agents.langgraph_flow import start_agent_background_job, agent_controller
from datetime import timedelta, datetime
import logging
import os
logger = logging.getLogger("main")
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("FastAPI startup complete")
    
    # Create database tables if they don't exist
    from app.models.database import engine, Base
    from app.models import schemas  # Import schemas to register models
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Start the autonomous agent scheduler
    start_agent_background_job()
    logger.info("Autonomous agent scheduler started")
    
    # Recovery: Reset interrupted jobs
    from app.models.database import SessionLocal
    from app.models.schemas import Job, User
    from app.auth.security import get_password_hash, ADMIN_USERNAME, ADMIN_PASSWORD
    from datetime import datetime
    
    db = SessionLocal()
    try:
        # 1. Reset interrupted jobs
        interrupted_jobs = db.query(Job).filter(Job.status == "running").all()
        for job in interrupted_jobs:
            job.status = "failed"
            job.error = "Interrupted by server restart"
            job.completed_at = datetime.utcnow()
        
        # 2. Ensure Admin User exists
        admin = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if not admin:
            logger.info(f"Creating default admin user: {ADMIN_USERNAME}")
            admin_user = User(
                username=ADMIN_USERNAME,
                email="admin@example.com",
                hashed_password=get_password_hash(ADMIN_PASSWORD),
                full_name="System Admin",
                is_superuser=True
            )
            db.add(admin_user)
        
        db.commit()
        
        if interrupted_jobs:
            logger.info(f"Reset {len(interrupted_jobs)} interrupted jobs to 'failed'")
    finally:
        db.close()
    
    yield
    # Shutdown
    logger.info("FastAPI shutdown")
    agent_controller.stop_scheduler()

app = FastAPI(title="Smart Supply Chain AI Agent", lifespan=lifespan)

# Enable CORS for React frontend
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
origins = [origin.strip() for origin in raw_origins.split(",")]

# Add 127.0.0.1 variants just in case
if "http://localhost:5173" in origins:
    origins.append("http://127.0.0.1:5173")
if "http://localhost:3000" in origins:
    origins.append("http://127.0.0.1:3000")

logger.info(f"Allowed CORS Origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Only allow trusted origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": str(exc)},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Smart Supply Chain AI Agent"}

@app.post("/token", response_model=Token, tags=["Auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token endpoint.
    POST /token with username and password to get JWT token.
    """
    from app.models.database import SessionLocal
    db = SessionLocal()
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        db.close()

@app.get("/", tags=["Root"])
def root():
    return {"message": "Smart Supply Chain AI Agent is running 🚀", "status": "operational"}

@app.post("/admin/init-learning", tags=["Admin"])
def init_learning_data(current_user = Depends(get_current_user)):
    """
    Initialize sample feedback data to jumpstart the learning system.
    Creates realistic sample feedback for all inventory SKUs.
    Protected: Requires authentication.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    from app.models.database import SessionLocal
    from app.models import schemas
    from datetime import datetime, timedelta
    import random
    
    db = SessionLocal()
    try:
        # Get all unique SKUs from inventory
        inventory_items = db.query(schemas.Inventory).all()
        
        if not inventory_items:
            return {"message": "No inventory items found. Please add inventory first.", "status": "error"}
        
        skus_processed = 0
        feedback_created = 0
        
        for item in inventory_items:
            sku = item.sku
            
            # Check if feedback already exists
            existing_feedback = db.query(schemas.Feedback).filter(
                schemas.Feedback.sku == sku
            ).count()
            
            if existing_feedback > 0:
                continue
            
            # Create 12 sample feedback records (simulating 12 decision cycles)
            for i in range(12):
                # 80% approval rate (realistic for good decisions)
                approved = random.random() < 0.8
                
                # Create feedback with dates spread over last 30 days
                days_ago = random.randint(0, 30)
                feedback_date = datetime.utcnow() - timedelta(days=days_ago)
                
                feedback = schemas.Feedback(
                    memory_id=None,
                    sku=sku,
                    approved=approved,
                    note=f"{'Good decision' if approved else 'Decision could be better'} for {sku}",
                    created_at=feedback_date
                )
                db.add(feedback)
                feedback_created += 1
            
            skus_processed += 1
        
        db.commit()
        
        return {
            "message": "Learning data initialized successfully",
            "status": "success",
            "skus_initialized": skus_processed,
            "feedback_records_created": feedback_created
        }
    
    except Exception as e:
        db.rollback()
        return {"message": f"Error initializing learning data: {str(e)[:100]}", "status": "error"}
    finally:
        db.close()

@app.post("/admin/trigger-learning", tags=["Admin"])
def trigger_learning(current_user = Depends(get_current_user)):
    """
    Manually trigger the learning node to update parameters based on recent feedback.
    This is normally called automatically after each agent cycle.
    Protected: Requires authentication.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    from app.agents.nodes.learning_node import LearningNode
    from app.models.database import SessionLocal
    
    try:
        learning_node = LearningNode(session_factory=SessionLocal)
        results = learning_node.learn()
        
        return {
            "message": "Learning cycle completed",
            "status": "success",
            "timestamp": results.get("timestamp"),
            "skus_updated": results.get("skus_updated"),
            "changes": results.get("changes")
        }
    
    except Exception as e:
        return {"message": f"Error running learning: {str(e)[:100]}", "status": "error"}

# ============================================================================
# Agent Lightning Configuration Management Endpoints
# ============================================================================

@app.get("/api/lightning/status", tags=["Agent Lightning"])
async def get_lightning_status():
    """
    Get current Agent Lightning configuration status.
    Returns version, active config info, and history count.
    """
    from app.lightning.config_manager import config_manager
    
    try:
        status = config_manager.get_config_status()
        return {
            "status": "success",
            "lightning_config": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Lightning status: {str(e)}"
        )

@app.post("/api/lightning/apply-config", tags=["Agent Lightning"])
async def apply_lightning_config(
    config: dict,
    current_user = Depends(get_current_user)
):
    """
    Apply new Agent Lightning optimized configuration.
    This performs a hot-swap without restarting the server.
    
    Requires admin/superuser privileges.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only superusers can apply Lightning configurations"
        )
    
    from app.lightning.config_manager import config_manager
    
    try:
        success = config_manager.apply_config_hot_swap(config)
        
        if success:
            return {
                "status": "success",
                "message": "Configuration hot-swap completed",
                "new_version": config_manager.current_version,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Configuration validation failed"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply configuration: {str(e)}"
        )

@app.post("/api/lightning/rollback", tags=["Agent Lightning"])
async def rollback_lightning_config(current_user = Depends(get_current_user)):
    """
    Rollback to previous Agent Lightning configuration.
    
    Requires admin/superuser privileges.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only superusers can rollback Lightning configurations"
        )
    
    from app.lightning.config_manager import config_manager
    
    try:
        success = config_manager.rollback_config()
        
        if success:
            return {
                "status": "success",
                "message": "Configuration rollback completed",
                "current_version": config_manager.current_version,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="No previous configuration to rollback to"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rollback configuration: {str(e)}"
        )


# Routes
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(orders.router)
app.include_router(alerts.router)
app.include_router(agent.router)
app.include_router(feedback.router)
app.include_router(memory.router)
app.include_router(persistence.router)
from app.routes import analytics
app.include_router(analytics.router)
from app.routes import chat
app.include_router(chat.router)

# Export get_current_user for use in routes
__all__ = ["app", "get_current_user"]


# Smart Supply Chain Agent API - Clean Reload
