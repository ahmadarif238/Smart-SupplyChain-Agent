# React Frontend - Smart SupplyChain Agent

Professional React frontend for the Smart SupplyChain Agent system with TypeScript, Tailwind CSS, and real-time API integration.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
cd react-app
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

## 📊 Features

### Dashboard
- Real-time system status
- Key metrics overview
- Quick action buttons
- System health monitoring

### Inventory Management
- View all products
- Add new products with full supply chain data
- Track inventory levels and thresholds
- Monitor stock value
- Status indicators for low stock items
- Download inventory data as CSV

### Sales Tracking
- Record sales transactions
- Monitor sales trends
- Track units sold
- View sales history

### Orders (Coming Soon)
- Create orders
- Track order status
- View order recommendations from AI agent

### Alerts (Coming Soon)
- View critical alerts
- Monitor warnings
- Track alert history

### Agent Control (Coming Soon)
- Run agent manually
- View agent status
- Monitor agent decisions
- Configure agent parameters

## 🏗️ Architecture

### File Structure
```
react-app/
├── src/
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Inventory.tsx
│   │   ├── Sales.tsx
│   │   ├── Orders.tsx (todo)
│   │   ├── Alerts.tsx (todo)
│   │   └── Agent.tsx (todo)
│   ├── App.tsx
│   ├── App.css
│   ├── main.tsx
│   ├── index.css
│   └── api.ts
├── public/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
└── postcss.config.cjs
```

### Technologies

- **React 18** - UI Framework
- **TypeScript** - Type safety
- **React Router v6** - Navigation
- **Tailwind CSS** - Styling
- **Vite** - Build tool
- **Axios** - HTTP client
- **Lucide React** - Icons
- **Recharts** - Charts (for future use)

## 🔌 API Integration

### Configuration

The app connects to the backend API at `http://127.0.0.1:8000`. Modify this in `src/api.ts`:

```typescript
const API_BASE = 'http://127.0.0.1:8000';
```

### Available Endpoints

#### Health Check
```typescript
GET /health
```

#### Inventory
```typescript
GET /inventory/          # List all items
POST /inventory/         # Add new item
```

#### Sales
```typescript
GET /sales/              # List all sales
POST /sales/             # Record new sale
```

#### Orders
```typescript
GET /orders/             # List all orders
POST /orders/            # Create order
GET /orders/recommend    # Get AI recommendations
```

#### Alerts
```typescript
GET /alerts/             # List all alerts
```

#### Agent
```typescript
POST /agent/run_once     # Run agent cycle
GET /agent/status        # Get agent status
```

## 🎨 Design System

### Color Palette
- **Primary**: `#0052CC` (Blue)
- **Secondary**: `#7C3AED` (Purple)
- **Success**: `#059669` (Green)
- **Warning**: `#D97706` (Amber)
- **Error**: `#DC2626` (Red)
- **Info**: `#0284C7` (Cyan)

### Components

All components use Tailwind CSS for styling with consistent spacing and typography.

#### Buttons
```tsx
<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
  Action
</button>
```

#### Cards
```tsx
<div className="bg-white rounded-lg shadow-lg p-6">
  {content}
</div>
```

#### Forms
```tsx
<input
  type="text"
  placeholder="Enter value"
  className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
/>
```

## 🔐 Error Handling

The API service includes automatic error handling with console logging:

```typescript
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.message);
    return Promise.reject(error);
  }
);
```

## 📈 State Management

Components use React hooks (`useState`, `useEffect`) for state management. For larger scale apps, consider Redux or Zustand.

## 🚀 Deployment

### Vercel
```bash
npm install -g vercel
vercel
```

### Netlify
```bash
npm run build
# Deploy the 'dist' folder
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "preview"]
```

## 🐛 Troubleshooting

### CORS Errors
If you get CORS errors, ensure the backend is running on port 8000 and is configured to accept requests from your React app.

### API Not Found
Make sure the backend API endpoints are correct. Check `src/api.ts` for the API_BASE URL.

### Styles Not Applied
Clear your browser cache and restart the dev server:
```bash
npm run dev
```

## 📝 Environment Variables

Create a `.env` file in the `react-app` directory (optional):

```
VITE_API_BASE=http://127.0.0.1:8000
VITE_APP_NAME=Smart SupplyChain Agent
```

Update `src/api.ts` to use environment variables:
```typescript
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';
```

## 🤝 Contributing

1. Create a new branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 📄 License

This project is part of the Smart SupplyChain Agent system.

## 🆘 Support

For issues or questions:
1. Check existing issues on GitHub
2. Create a new issue with detailed information
3. Include error logs and steps to reproduce

---

**Last Updated**: November 17, 2025  
**Version**: 1.0.0  
**Status**: Active Development
