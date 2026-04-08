# ✈️ TravelAI — Multi-Agent Travel Planning System

A Flask-based intelligent travel planning website powered by multiple AI agents and Google Gemini.

**By Ram Khandelwal**

---

## 🏗️ Architecture

```
User (Chat Interface)
        ↓
Flask Web App
        ↓
Agent Orchestrator (Central Hub)
   ├── Requirement Checker Agent  → Validates travelers, dates, budget
   ├── Flight Agent               → Skyscanner via RapidAPI
   ├── Hotel Agent                → Booking.com via RapidAPI
   ├── Climate Agent              → WeatherAPI via RapidAPI
   └── Planning Agent             → Google Gemini AI → Full Itinerary
```

---

## 🤖 Agents Explained

| Agent | Role |
|-------|------|
| **Orchestrator** | Coordinates all agents, manages conversation flow |
| **Requirement Checker** | Validates travelers count, dates, budget, destination |
| **Flight Agent** | Searches flights via Skyscanner (RapidAPI) |
| **Hotel Agent** | Finds hotels via Booking.com (RapidAPI) |
| **Climate Agent** | Gets weather forecast via WeatherAPI (RapidAPI) |
| **Planning Agent** | Generates full day-by-day itinerary using Gemini AI |

---

## 🛠️ Tech Stack

- **Backend**: Python + Flask
- **AI/LLM**: Google Gemini 1.5 Flash
- **Flight API**: Skyscanner via RapidAPI
- **Hotel API**: Booking.com via RapidAPI
- **Weather API**: WeatherAPI via RapidAPI
- **Deployment**: Railway

---

## 🚀 Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/travel-agent-ai.git
cd travel-agent-ai
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
```

Edit `.env` and add your keys:
```
GEMINI_API_KEY=your_gemini_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
```

### 5. Run the app
```bash
python app.py
```

Visit: **http://localhost:5000**

---

## 🌐 Deploy on Railway

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit - TravelAI Multi-Agent System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/travel-agent-ai.git
git push -u origin main
```

### Step 2: Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Railway auto-detects Python + Flask ✅

### Step 3: Add Environment Variables
In Railway dashboard → Your project → **Variables** tab:
```
GEMINI_API_KEY = your_gemini_key
RAPIDAPI_KEY   = your_rapidapi_key
SECRET_KEY     = any_random_string_here
```

### Step 4: Deploy!
Railway automatically builds and deploys. Your URL will be:
`https://your-app-name.railway.app`

---

## 📦 APIs Used

| API | Provider | Free Tier |
|-----|----------|-----------|
| Gemini 1.5 Flash | Google AI Studio | ✅ Yes |
| Skyscanner Flight Search | RapidAPI | ✅ Yes |
| Booking.com Hotels | RapidAPI | ✅ Yes |
| WeatherAPI | RapidAPI | ✅ Yes |

---

## 📋 Deliverables

1. ✅ **Website hosted on Railway** — Live URL above
2. ✅ **GitHub Link** — This repository
3. ✅ **Demo** — Chat interface with full trip planning

---

## 🎯 Features

- 💬 **Conversational Chat Interface** — Natural language trip planning
- 🤖 **Multi-Agent Architecture** — 6 specialized AI agents
- ✈️ **Real Flight Search** — Live data from Skyscanner
- 🏨 **Hotel Recommendations** — Top-rated stays via Booking.com
- 🌤️ **Weather Forecast** — Current & 7-day forecast
- 🗺️ **AI Itinerary** — Full day-by-day plan via Gemini
- 📱 **Responsive Design** — Works on mobile & desktop
- 🔄 **Session Management** — Multiple trips per session
