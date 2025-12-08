from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.auth.dependencies import get_current_user
from app.agents.analyst import get_analyst_agent
import logging

# Configure logger
logger = logging.getLogger("chat_router")

router = APIRouter(
    prefix="/chat",
    tags=["Analyst Chat"],
    responses={404: {"description": "Not found"}},
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    status: str

@router.post("/", response_model=ChatResponse)
async def chat_with_analyst(
    request: ChatRequest,
    current_user = Depends(get_current_user)
):
    """
    Chat with the Supply Chain Analyst Agent.
    Requires authentication.
    """
    try:
        agent = get_analyst_agent()
        result = agent.ask(request.message)
        
        return ChatResponse(
            response=result["response"],
            status=result["status"]
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
