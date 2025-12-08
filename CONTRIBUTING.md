# Contributing to Smart Supply Chain Agent

Thank you for your interest in contributing to the Smart Supply Chain Agent! This document provides guidelines and instructions for contributing to the project.

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- **Clear title** describing the issue
- **Steps to reproduce** the behavior
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, Node version)
- **Relevant logs** or error messages

### Suggesting Enhancements

We welcome feature requests! Please:
- Check existing issues to avoid duplicates
- Provide a clear use case
- Explain why this enhancement would be useful
- Consider implementation details if possible

### Pull Request Process

1. **Fork the repository** and create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Test your changes**:
   ```bash
   # Backend tests
   pytest tests/
   
   # Frontend tests (if applicable)
   cd react-app && npm test
   ```

4. **Update documentation** if needed (README, docstrings, etc.)

5. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add new forecasting algorithm"
   ```
   
   Use conventional commits:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `refactor:` for code refactoring
   - `test:` for adding tests
   - `chore:` for maintenance

6. **Push to your fork** and create a Pull Request

7. **Wait for review** - maintainers will review and may request changes

## 🎨 Code Style

### Python (Backend)
- Follow **PEP 8** style guide
- Use **type hints** where appropriate
- Write **docstrings** for all public functions/classes
- Keep functions focused and under 50 lines when possible
- Use **async/await** for I/O operations in FastAPI routes

Example:
```python
from typing import Dict, Any

async def process_inventory(sku: str) -> Dict[str, Any]:
    """
    Process inventory for a given SKU.
    
    Args:
        sku: The stock keeping unit identifier
        
    Returns:
        Dictionary containing inventory status and recommendations
    """
    # Implementation
    pass
```

### TypeScript/React (Frontend)
- Use **TypeScript** with strict mode
- Follow **functional components** with hooks
- Use **descriptive variable names**
- Keep components under 200 lines
- Extract reusable logic into custom hooks

Example:
```typescript
interface InventoryProps {
  sku: string;
  quantity: number;
}

const InventoryCard: React.FC<InventoryProps> = ({ sku, quantity }) => {
  // Implementation
};
```

## 🧪 Testing Guidelines

### Backend Tests
- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use `pytest` fixtures for common setup
- Aim for >70% code coverage for new features

### Frontend Tests
- Use React Testing Library
- Test user interactions, not implementation details
- Mock API calls appropriately

## 🏗️ Project Structure

```
Smart-SupplyChain-Agent/
├── app/                    # Backend application
│   ├── agents/            # LangGraph agents and nodes
│   ├── routes/            # FastAPI route handlers
│   ├── models/            # Database models
│   └── services/          # Business logic
├── react-app/             # Frontend application
│   └── src/
│       ├── pages/         # Main pages
│       ├── components/    # Reusable components
│       └── hooks/         # Custom hooks
├── tests/                 # Test files
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

## 🔧 Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Groq API Key

### Local Development

1. **Backend**:
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # Windows: myenv\Scripts\activate
   pip install -r requirements.txt
   python init_adaptive_learning_db.py
   uvicorn main:app --reload
   ```

2. **Frontend**:
   ```bash
   cd react-app
   npm install
   npm run dev
   ```

### Docker Development

```bash
docker-compose up --build
```

For frontend hot-reload during development:
```bash
docker-compose --profile dev up
```

## 📝 Commit Message Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(forecast): add ARIMA forecasting method
fix(finance): correct ROI calculation for edge cases
docs(readme): update installation instructions
```

## 🌟 Priority Areas for Contribution

We especially welcome contributions in these areas:

1. **Advanced Forecasting Models**
   - ARIMA, Prophet, or neural network implementations
   - Seasonal demand patterns
   - External signal integration (weather, holidays)

2. **Multi-Warehouse Support**
   - Multi-echelon inventory optimization
   - Transfer order logic
   - Warehouse-specific rules

3. **Supplier Management**
   - Multi-sourcing logic
   - Supplier quality ratings
   - Automated bidding system

4. **Testing**
   - Increase test coverage
   - Integration tests for workflows
   - Performance benchmarks

5. **Documentation**
   - Tutorial videos
   - Architecture deep-dives
   - API documentation

## ❓ Questions?

- Open an issue for general questions
- Tag with `question` label
- Check existing discussions first

## 📜 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what's best for the community
- Show empathy towards other contributors

## 🎉 Recognition

Contributors will be:
- Listed in the project's contributors section
- Mentioned in release notes for significant contributions
- Invited to be maintainers after sustained contributions

Thank you for helping make Smart Supply Chain Agent better! 🚀
