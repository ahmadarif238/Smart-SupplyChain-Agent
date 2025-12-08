from app.config.llm_config import LLMConfig
from app.config.settings import settings
import logging
import os
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq

logger = logging.getLogger("analyst_agent")

class AnalystAgent:
    """
    Supply Chain Analyst Agent that converts natural language to SQL queries.
    Uses Groq Llama 3.3 and LangChain's SQL Toolkit.
    """
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable not set")
            
        # Initialize Database connection for LangChain
        self.db = SQLDatabase.from_uri(self.db_url)
        
        # Initialize LLM
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
             raise ValueError("GROQ_API_KEY environment variable not set")

        self.llm = ChatGroq(
            temperature=0,
            model_name=LLMConfig.SUMMARY_MODEL, # Use 70b model for better SQL
            groq_api_key=api_key
        )
        
        # Initialize Agent
        self.agent_executor = create_sql_agent(
            llm=self.llm,
            db=self.db,
            agent_type="zero-shot-react-description",
            verbose=True,
            handle_parsing_errors=True
        )
        
    def ask(self, query: str) -> dict:
        """
        Run a query against the specific database tables.
        """
        try:
            logger.info(f"Analyst Agent received query: {query}")
            
            # Add system prompt context to guide the agent
            system_context = """
            You are a Supply Chain Analyst expert. 
            You have access to the following tables: 
            - 'inventory' (stock levels, product names, skus, prices, lead times)
            - 'sales' (historical sales data, daily quantities)
            - 'orders' (purchase orders placed)
            
            When asked about "sales", aggregate from the 'sales' table.
            When asked about "stock" or "inventory", use the 'inventory' table.
            
            Do not make DML statements (INSERT, UPDATE, DELETE). Only SELECT.
            Return a concise, data-driven answer.
            """
            
            full_prompt = f"{system_context}\n\nQuestion: {query}"
            
            # Execute
            response = self.agent_executor.invoke(full_prompt)
            
            output = response.get("output", "I couldn't find an answer to that.")
            return {
                "response": output,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Analyst Agent failed: {e}", exc_info=True)
            return {
                "response": f"I encountered an error analyzing the data: {str(e)}",
                "status": "error"
            }

# Global instance
analyst_agent = None

def get_analyst_agent():
    global analyst_agent
    if analyst_agent is None:
        analyst_agent = AnalystAgent()
    return analyst_agent
