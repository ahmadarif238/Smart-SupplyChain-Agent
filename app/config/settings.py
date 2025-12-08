from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Smart Supply Chain Agent"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Finance & Budgeting
    DEFAULT_BUDGET: float = 600.0  # Reduced for demo to trigger negotiation
    REVENUE_REINVESTMENT_RATE: float = 0.3  # 30% of recent revenue added to budget
    AUTO_APPROVAL_THRESHOLD: float = 1000.0
    
    # Negotiation Rules (ANEX Protocol)
    MAX_NEGOTIATION_ROUNDS: int = 3
    NEGOTIATION_ROI_THRESHOLD: float = 1.1  # ROI > 1.1x to accepts a counter-proposal
    CRITICAL_STOCK_ROI_MULTIPLIER: float = 1.5 # Boost ROI for safety stock
    
    # Risk Analysis
    STOCKOUT_RISK_HIGH_MULTIPLIER: float = 10.0
    STOCKOUT_RISK_MEDIUM_MULTIPLIER: float = 2.0
    
    # Linear Programming
    BUDGET_PENALTY_FACTOR: float = 1.5
    
    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
