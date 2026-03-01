# Financial Intelligence Engine

AI-powered strategic competitor analysis from raw financial data.

Generate executive-ready financial performance reports from CSV files using a multi-step AI workflow.

---

## 🚀 Overview

Financial Intelligence Engine transforms structured financial data into board-level strategic analysis.

Upload a CSV file, define competitors, and receive a comprehensive performance report including:

- Revenue growth trends
- Margin evolution
- Competitive positioning
- Strategic risks & opportunities
- Executive summary insights

The system combines structured data parsing with LLM-driven reasoning to produce clean, presentation-ready analysis.

---

## 🌐 Live Demo

Frontend (Lovable):  
→ [Add your Lovable public URL here]

Backend (Render API Docs):  
→ https://financial-report-writing-agent.onrender.com/docs

> Note: Free-tier backend may take ~30 seconds to wake after inactivity (cold start).

---

## 🏗 Architecture

### Frontend
- Built using Lovable
- Modern dark UI
- CSV upload interface
- Real-time report rendering

### Backend
- FastAPI
- LangGraph workflow orchestration
- Gemini LLM integration
- Pandas for CSV parsing
- CORS-enabled API

### Hosting
- Backend deployed on Render
- Frontend deployed via Lovable

---

## ⚙️ How It Works

1. User uploads financial CSV data.
2. User enters competitor names.
3. Frontend sends structured JSON to backend.
4. Backend:
   - Parses CSV
   - Extracts key financial metrics
   - Runs multi-step reasoning workflow
   - Generates structured strategic analysis
5. Frontend renders formatted report preview.

---

## 📡 API Endpoint

### POST `/analyze`

#### Request Body

```json
{
  "task": "Analyze financial performance compared to competitors.",
  "competitors": ["Microsoft", "Nvidia", "Google"],
  "csv_file": "raw CSV text here",
  "max_revisions": 3
}
