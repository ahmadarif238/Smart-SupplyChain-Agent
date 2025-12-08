# 🧠 Smart Supply Chain Agent: Capability Overview

A production-ready autonomous agent system that manages supply chain operations through multi-agent orchestration, hybrid intelligence (LP + LLM), and real-time negotiation.

## 🌟 Core Capabilities

### 1. **Autonomous Budget Negotiation (ANEX Protocol)**
The system features a sophisticated negotiation engine that mimics real-world procurement discussions:
- **Quantity Reduction Strategy**: When budget is tight, the agent doesn't just reject orders. It intelligently proposes reducing quantities (e.g., "Reduce by 40%") to fit critical items within budget constraints.
- **LP Re-Optimization**: After receiving reduction proposals, the Finance Agent re-runs a **Linear Programming solver** to find the mathematically optimal combination of orders that maximizes value while strictly adhering to the budget.
- **Result**: Approves 5-6 critical items within budget instead of rejecting everything or blowing the budget on one expensive item.

### 2. **Hybrid Intelligence Architecture**
We combine the best of both worlds:
- **Deterministic Precision**: Uses **Linear Programming (PuLP)** for budget allocation, ensuring 100% mathematical accuracy and zero hallucinations on financial decisions.
- **Cognitive Flexibility**: Uses **Large Language Models (Groq Llama 3.3)** for qualitative reasoning, generating natural language arguments, and understanding "soft" constraints like supplier relationships or urgency nuances.

### 3. **Interactive "War Room" UI**
A real-time command center for observing agent thought processes:
- **Live Agent Dialogue**: Watch the Decision, Finance, and Negotiation agents debate in real-time.
- **Visualized Negotiation**: See the specific proposals, counter-arguments, and final agreements as they happen.
- **Streaming Updates**: Built with **Server-Sent Events (SSE)** for millisecond-latency updates without page refreshes.

### 4. **Retail Analytics Chatbot**
An integrated RAG + SQL agent that answers natural language questions about your data:
- **Natural Queries**: Ask "What are my top 5 selling items?" or "Which products are running low?"
- **SQL Generation**: The agent converts questions into precise SQL queries to fetch real-time data from the database.
- **Contextual Answers**: Combines data with LLM reasoning to provide actionable insights.

## 🛠️ Technical Highlights

- **Orchestration**: Built on **LangGraph** for managing cyclic, stateful multi-agent workflows.
- **Backend**: High-performance **FastAPI** application with async processing.
- **Frontend**: Modern **React + TypeScript** interface with Tailwind CSS.
- **Database**: **PostgreSQL** for persistent storage of inventory, sales, and agent memory.
- **Performance**: Optimized for speed using **Groq's LPU inference engine**.

---
*Ready for deployment. Star us on GitHub!* ⭐
