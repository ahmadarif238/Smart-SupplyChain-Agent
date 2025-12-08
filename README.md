# 🤖 Smart Supply Chain Agent
> **Production-Grade Autonomous Multi-Agent System**

**A showcase of Agentic AI, LangGraph Orchestration, and Hybrid Intelligence.**

This project demonstrates a production-ready **Autonomous Supply Chain System** that moves beyond simple chatbots to complex, stateful multi-agent collaboration. It integrates **Deterministic Logic (Linear Programming)** with **Generative Reasoning (LLMs)** to solve real-world business problems.

---

## 🛠️ Tech Stack & Skills Demonstrated

### **Core AI & Agents**
- **LangGraph**: Orchestrating cyclic, stateful multi-agent workflows with complex dependencies.
- **Agentic AI**: Implementing FIPA negotiation protocols and autonomous conflict resolution.
- **RAG (Retrieval Augmented Generation)**: Natural language SQL generation for database analytics.
- **Hybrid Intelligence**: Combining **PuLP (Linear Programming)** for mathematical optimization with **LLMs (Groq/Llama)** for qualitative reasoning.

### **Backend Engineering**
- **FastAPI**: High-performance async REST API with dependency injection.
- **PostgreSQL**: Complex schema design, relationships, and efficient querying.
- **SQLAlchemy (ORM)**: Advanced database modeling and session management.
- **Server-Sent Events (SSE)**: Real-time streaming infrastructure for agent observability.

### **DevOps & Deployment**
- **Docker & Docker Compose**: Fully containerized application for consistent logic across environments.
- **Microservices Ready**: Decoupled frontend/backend architecture suitable for cloud deployment (AWS/GCP).

### **Frontend & UX**
- **React + TypeScript**: Type-safe, component-driven UI architecture.
- **Tailwind CSS**: Responsive, modern design system.
- **Recharts**: Data visualization for complex supply chain metrics.

---

## 🌟 Key Features

### 🧠 **Autonomous Decision Engine**
- **Stateful Multi-Agent Workflow**: Agents (Forecast, Decision, Finance) maintain state across cyclic executions using LangGraph.
- **Constraint Satisfaction**: The Decision Agent utilizes **Linear Programming** to solve the Budget Knapsack Problem, ensuring 100% financial accuracy.
- **Self-Healing Logic**: Agents autonomously detect errors, retry failed steps, and adapt strategies (e.g., switching from LLM forecast to Statistical baseline for sparse data).

### 💬 **Intelligent Negotiation (ANEX Protocol)**
- **Problem**: Finance rejections usually stop a process.
- **Solution**: Implemented a **FIPA Iterated Contract Net Protocol** where agents negotiate:
    1. Finance rejects order ($$$).
    2. Negotiation Agent proposes **Quantity Reduction** (-40%) based on urgency.
    3. Finance **Re-optimizes** portfolio using LP solver.
    4. **Result**: Optimal allocation of budget to critical items.

### 🔍 **Retail Analytics RAG Chatbot**
- **Natural Language to SQL**: "Show me top selling items in Electronics" → `SELECT * FROM sales WHERE category='Electronics' ...`
- **Context-Aware Reasoning**: Combines database results with LLM insights to answer strategic questions.

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Frontend (React + TypeScript)"
        UI[Dashboard UI]
        Agent[Agent Control]
        Finance[Finance Dashboard]
        Memory[AI Intelligence]
    end

    subgraph "Backend (FastAPI)"
        API[REST API]
        SSE[SSE Streaming]
        Auth[Authentication]
    end

    subgraph "LangGraph Workflow"
        Start([Start Cycle])
        Fetch[Fetch Data Node]
        Forecast[Forecast Node<br/>Statistical + LLM]
        Decision[Decision Subgraph<br/>Analyze → Constrain → Optimize]
        Finance_Node[Finance Node<br/>Budget Review]
        Negotiate{Rejections?}
        Negotiation[Negotiation Node<br/>LLM Dialogue]
        Action[Action Node<br/>Place Orders]
        Action[Action Node<br/>Place Orders]
        Memory_Node[Memory Node<br/>Persistent Storage]
        End([End])

        Start --> Fetch
        Fetch --> Forecast
        Forecast --> Decision
        Decision --> Finance_Node
        Finance_Node --> Negotiate
        Negotiate -->|Yes| Negotiation
        Negotiation --> Finance_Node
        Negotiate -->|No| Action
        Action --> Memory_Node
        Memory_Node --> End
    end

    subgraph "Data Layer (PostgreSQL)"
        DB[(Database)]
        Inventory[Inventory]
        Sales[Sales]
        Orders[Orders]
        Memory_DB[Agent Memory]
        Checkpoints[Checkpoints]
    end

    UI --> API
    API --> Start
    SSE -.->|Real-time Events| UI
    Memory_Node --> DB
    Fetch --> DB
    Action --> DB
    Action --> DB
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Groq API Key ([Get one here](https://console.groq.com/))

### 1️⃣ **Backend Setup**

```bash
# Clone the repository
git clone https://github.com/ahmadarif238/Smart-SupplyChain-Agent.git
cd Smart-SupplyChain-Agent

# Create virtual environment
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your credentials:
#   DATABASE_URL=postgresql://user:password@localhost:5432/supply_chain
#   GROQ_API_KEY=your_groq_api_key
#   SECRET_KEY=your_secret_key

### 2️⃣ **Database Setup**

1. **Install PostgreSQL** (if not installed)
2. **Create the database**:
   ```sql
   CREATE DATABASE supply_chain;
   ```
3. **Run the App (Auto-Creates Tables)**:
   ```bash
   uvicorn main:app --reload
   ```
   *The application will automatically create all necessary tables on first startup.*

4. **(Optional) Seed Demo Data**:
   Populate the database with a realistic scenario (15 items, critical stock levels, sales history):
   ```bash
   python scripts/seed_demo_data.py
   ```
   *This is recommended for testing the negotiation capabilities immediately.*

The API will be available at `http://localhost:8000`

### 2️⃣ **Frontend Setup**

```bash
cd react-app

# Install dependencies
npm install

# Run development server
npm run dev
```

The UI will be available at `http://localhost:5173`

### 3️⃣ **Default Login**
- **Username**: `admin`
- **Password**: `admin123`

---

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## 📖 How It Works

### 1. **Demand Forecasting**
The **Forecast Node** uses a hybrid approach:
- **Statistical Method**: Simple Moving Average (SMA) + Trend analysis for stable items
- **LLM Method**: Groq Llama 3.3 for volatile/new items with limited historical data
- **Confidence Scoring**: Automatically selects the best method based on data volatility

### 2. **Inventory Optimization**
The **Decision Subgraph** implements classic supply chain formulas:
- **Economic Order Quantity (EOQ)**: Minimizes ordering + holding costs
- **Reorder Point (ROP)**: `(Daily Demand × Lead Time) + Safety Stock`
- **Urgency Levels**: Critical, High, Medium, Low based on days until stockout

### 3. **Budget Management**
The **Finance Node** enforces fiscal responsibility:
- **Dynamic Budget**: `Base + (Recent Revenue × 30%)`
- **ROI Prioritization**: High-ROI items approved first
- **Stockout Risk**: Increases priority for items near stockout

### 4. **Multi-Agent Negotiation**
When Finance rejects an order, the **Negotiation Node** activates:
1. **Decision Agent** generates a counter-argument using LLM
2. **Finance Agent** re-evaluates with boosted ROI consideration
3. **Override Approval** granted if business case is compelling
4. All dialogue is logged and displayed in real-time

---


---

## 📐 Design Decisions

### Why Hybrid Intelligence? (LP + LLM)
This project explicitly chooses a **Hybrid Architecture** over a pure "GenAI" approach for reliability and precision.

1.  **Linear Programming (Pulp) for Budgeting**:
    *   **Reason**: LLMs are notoriously bad at precise math and combinatorial optimization (the Knapsack Problem).
    *   **Implementation**: We use the `pulp` library to solve the budget allocation problem mathematically, ensuring the optimal combination of high-ROI orders that largely fit within the budget.
    *   **Result**: 100% mathematically optimal budget allocation, zero hallucinations on spend.

2.  **LLMs (Groq) for Negotiation**:
    *   **Reason**: Mathematics cannot capture business nuance or "soft" priorities (e.g., "we need to keep this supplier happy" or "this is a strategic launch").
    *   **Implementation**: When the LP solver rejects an item, the Decision Agent uses an LLM to generate a natural language counter-argument based on stockout penalties.
    *   **Result**: A system that is financially rigorous but flexible enough to handle real-world exceptions.

### FIPA Negotiation Protocol
The agents communicate using a **FIPA Iterated Contract Net Protocol** to resolve budget conflicts. The system now supports **autonomous quantity negotiation**:

1. **Finance Rejection**: If an order exceeds budget, Finance rejects it.
2. **Proposal Generation**: Negotiation Node analyzes the rejection and proposes a **Quantity Reduction** (e.g., "Reduce by 40% to fit budget").
3. **LP Re-Optimization**: Finance re-runs the Linear Programming solver with the new lower-cost proposals.
4. **Approval**: If the new combination maximizes value within budget, it is approved.

```mermaid
sequenceDiagram
    participant D as Decision Agent
    participant N as Negotiation Agent
    participant F as Finance Agent (LP Solver)
    
    D->>F: PROPOSE (Order List)
    
    Note over F: Run Linear Programming (Round 0)<br/>Maximize Value s.t. Cost <= Budget
    
    F->>N: REJECT (Budget Exceeded)
    
    Note over N: Analyze Rejection<br/>Calculate Minimum Viable Quantity
    
    N->>F: PROPOSE (Quantity Reduction: -40%)
    
    Note over F: Re-Optimize LP (Round 1)<br/>Include Reduced Proposals
    
    alt Optimal Solution Found?
        F-->>D: ACCEPT-PROPOSAL (Reduced Qty)
    else
        F-->>D: REJECT (Still Over Budget)
    end
    
    D->>D: Execute Approved Orders
```

## 🎯 Key Technologies

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Agent Orchestration** | LangGraph | Multi-agent workflow with cyclic dependencies |
| **LLM Reasoning** | Groq (Llama 3.3 70B) | Natural language dialogue and reasoning |
| **Backend** | FastAPI | High-performance async REST API |
| **Frontend** | React + TypeScript | Modern, responsive UI |
| **Database** | PostgreSQL | Persistent data storage |
| **Real-time** | Server-Sent Events | Live streaming of agent activities |
| **Visualization** | Recharts | Interactive charts and graphs |
| **Authentication** | JWT | Secure token-based auth |
| **Authentication** | JWT | Secure token-based auth |




---

## 📁 Project Structure

```
Smart-SupplyChain-Agent/
├── app/
│   ├── agents/
│   │   ├── langgraph_flow.py          # Main agent controller
│   │   ├── langgraph_workflow.py      # LangGraph workflow definition
│   │   ├── dialogue_generator.py      # LLM-powered dialogue
│   │   └── nodes/                     # Individual agent nodes
│   │       ├── forecast_node.py
│   │       ├── decision_subgraph.py
│   │       ├── finance_node.py
│   │       ├── negotiation_node.py
│   │       ├── action_node.py
│   │       └── learning_node.py
│   ├── routes/                         # FastAPI route handlers
│   ├── models/                         # SQLAlchemy models
│   ├── services/                       # Business logic
│   └── utils/                          # Utilities
├── react-app/
│   └── src/
│       ├── pages/                      # Main pages
│       ├── components/                 # React components
│       └── hooks/                      # Custom hooks
├── scripts/                            # Utility scripts
├── tests/                              # Test files
├── main.py                             # FastAPI entry point
├── docker-compose.yml                  # Docker configuration
└── requirements.txt                    # Python dependencies
```

---

## 🧪 Testing

```bash
# Run backend tests
python -m pytest tests/

# Test negotiation flow
python tests/test_negotiation_flow.py

# Verify adaptive learning
python verify_adaptive_learning.py
```

---

## 🎓 Learning Resources

This project demonstrates:
- **LangGraph**: Building complex multi-agent systems with cyclic workflows
- **LLM Integration**: Using Groq API for reasoning and natural language generation
- **Supply Chain Concepts**: EOQ, ROP, safety stock, lead time management
- **FastAPI Best Practices**: Async operations, dependency injection, JWT auth
- **React Patterns**: Custom hooks, context, real-time updates with SSE
- **Database Design**: Persistent memory, checkpoints, episodic/semantic storage

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LangGraph** by LangChain for the powerful agent orchestration framework
- **Groq** for ultra-fast LLM inference
- **FastAPI** for the excellent web framework
- **React** and the amazing ecosystem of libraries

---

## 🔌 Production Readiness & Integration

**From Portfolio to Production:**
While this project currently utilizes **simulated internal data** to demonstrate its reasoning capabilities (avoiding the need for proprietary datasets), the architecture is designed for **seamless external integration**.

- **🛒 E-Commerce Integration**: The `Fetch Data Node` is modular and can be swapped to pull live data from **Shopify API, Amazon SP-API, or WooCommerce**.
- **🚚 Real Supplier Connectivity**: The `Action Node` can be extended to send **EDI headers, API requests, or automated emails** to real vendors instead of internal logging.
- **Enterprise Scalability**: Built on FastAPI and PostgreSQL, this system is ready to be deployed into existing ERP ecosystems (SAP, Oracle, Microsoft Dynamics).

**I can upgrade this agent to manage your live inventory and place real orders.**

---

## 📧 Contact

**Arif Ahmad Khan** - [ahmadarif238@gmail.com]

Project Link: [https://github.com/ahmadarif238/Smart-SupplyChain-Agent]
---

**⭐ Star this repo if you find it useful!**
