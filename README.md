# AI-Powered Product Discovery Assistant

A mini AI-powered product discovery assistant that recommends the right products based on open-ended and abstract user queries. Built with FastAPI, React, and Google Gemini AI.

![Product Discovery](https://img.shields.io/badge/AI-Product%20Discovery-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![React](https://img.shields.io/badge/React-18+-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688)

## 🎯 Features

- **Smart Product Search**: Uses semantic embeddings to find relevant products
- **AI Chat Assistant**: Natural language product recommendations powered by Google Gemini
- **Web Scraping**: Automated product data collection from e-commerce sites
- **RAG Pipeline**: Retrieval-Augmented Generation for accurate recommendations
- **Modern UI**: Clean React frontend with responsive design
- **Search & Filter**: Client-side product filtering

## 🧠 Design Decisions & Assumptions

### Product Thinking

1. **Target Use Case**: Users with vague health concerns (e.g., "I'm losing hair") who need product guidance
2. **Recommendation Strategy**: 
   - Semantic search finds products based on meaning, not just keywords
   - LLM provides human-like explanations for WHY products match
   - Top 3 recommendations to avoid overwhelming users

3. **User Experience Assumptions**:
   - Users may not know exact product names
   - Natural language queries are preferred over filters
   - Quick responses are more important than exhaustive results

### Technical Decisions

1. **SQLite over PostgreSQL**: Simpler setup, sufficient for demo scale (< 1000 products)
2. **sentence-transformers**: Local embeddings for privacy and no API costs
3. **Gemini 2.0 Flash**: Fast, cost-effective LLM for conversational responses
4. **KNN Search**: Simple but effective for small-medium product catalogs
5. **Pre-computed Embeddings**: Embeddings are generated locally and shipped with the database, enabling deployment on memory-constrained platforms (e.g., Render free tier) without loading large ML models at runtime

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React Frontend │────▶│  FastAPI Backend │────▶│   SQLite DB     │
│   (Vite + React) │     │   (Python)       │     │   (Products)    │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ Scraper  │ │Embeddings│ │ Gemini   │
              │(BS4/httpx)│ │(MiniLM)  │ │   API    │
              └──────────┘ └──────────┘ └──────────┘
```

### Data Flow

1. **Scraping**: BeautifulSoup extracts products → SQLite storage
2. **Embedding**: Product text → 384-dim vectors (MiniLM-L6-v2)
3. **Query**: User message → Embedding → KNN search → Top matches
4. **Response**: Context + Query → Gemini → Natural language recommendation

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Backend Setup

```bash
# Navigate to project
cd "AI-powered product discovery assistant"

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
# Edit .env file and add your Gemini API key
cp .env.example .env
# GEMINI_API_KEY=your_api_key_here

# Run the backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend Setup

```bash
# In a new terminal
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Project Structure

```
AI-powered product discovery assistant/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app entry
│   │   ├── api.py           # API routes
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── crud.py          # Database operations
│   │   ├── database.py      # DB connection
│   │   ├── retrieval.py     # Embeddings & search
│   │   └── llm.py           # Gemini API client
│   ├── scraper/
│   │   ├── scraper.py       # Scraper dispatcher
│   │   └── traya_scraper.py # Traya.health scraper
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx     # Product grid
│   │   │   ├── ProductDetail.jsx
│   │   │   └── Chat.jsx     # AI chat interface
│   │   ├── api.js           # API client
│   │   └── App.jsx          # Main app
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/products` | List all products |
| GET | `/api/products/{id}` | Get product details |
| POST | `/api/scrape?site=traya` | Run web scraper |
| POST | `/api/chat` | AI chat endpoint |

### Chat API Example

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I have hair fall problem, what can help?"}'
```

Response:
```json
{
  "message": "Based on your hair fall concerns, I recommend...",
  "recommendations": [
    {
      "product_id": 37,
      "title": "Customized Hair Fall Plans",
      "score": 0.59,
      "reason": "Get custom hair fall solutions..."
    }
  ]
}
```

## How It Works

1. **Web Scraping**: Products are scraped from traya.health using BeautifulSoup and httpx
2. **Embeddings**: Product descriptions are converted to 384-dim vectors using sentence-transformers (all-MiniLM-L6-v2)
3. **Pre-computed Storage**: Embeddings are stored in SQLite and shipped with the deployment for memory efficiency
4. **Semantic Search**: User queries are matched against pre-computed embeddings using enhanced text similarity
5. **RAG Generation**: Top matching products provide context for Gemini to generate personalized recommendations

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **SQLite** - Lightweight database
- **sentence-transformers** - Text embeddings
- **httpx** - Async HTTP client
- **BeautifulSoup4** - HTML parsing

### Frontend
- **React 18** - UI library
- **Vite** - Build tool
- **React Router** - Navigation
- **Axios** - HTTP client

### AI/ML
- **Google Gemini** - LLM for chat responses
- **all-MiniLM-L6-v2** - Embedding model

## Docker Deployment

```bash
# Build and run
docker-compose up --build

# Access
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
```

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
DATABASE_URL=sqlite:///./dev.db
```

## 🎥 Demo

[Loom Video Demo](YOUR_LOOM_LINK_HERE)

## ⚡ Edge Cases Handled

| Scenario | Handling |
|----------|----------|
| Empty/short query | Returns helpful prompt to user |
| No matching products | Suggests alternative query phrasing |
| LLM API failure | Graceful fallback to template response |
| Invalid product ID | Returns 404 with clear message |
| Scraper timeout | Error handling with retry logic |
| Missing product images | Placeholder image fallback |
| CORS issues | Properly configured for frontend |

## 🚀 Extra Features (Beyond Requirements)

1. **Product Search Bar**: Filter products on the home page
2. **Typed API Responses**: Pydantic models for request/response validation
3. **Configurable Recommendations**: `top_k` parameter in chat API
4. **Production Docker Setup**: Separate dev and prod configurations
5. **Nginx Config**: Ready for production deployment
6. **Query Echo**: Returns user's query in response for context

## 📊 Performance Notes

- **Embedding Model**: ~400MB download on first run, cached thereafter
- **Response Time**: ~2-5 seconds (embedding + LLM call)
- **Concurrent Users**: Handles multiple requests (FastAPI async)

## License

MIT License

---

Built for Neusearch AI Technical Assignment
