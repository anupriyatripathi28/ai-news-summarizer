# 📰 AI News Summarizer

A full-stack web app that scrapes any news article from a URL and uses **Google's Gemini API** to generate a short summary, key points, and sentiment analysis — with all results saved to a local SQLite history.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-black)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- 🔗 Paste any news article URL and scrape its title + body text
- 🧠 AI-generated **summary** (3–5 sentences), **key points**, and **sentiment** (Positive / Negative / Neutral) via the Gemini free tier
- 💾 Every summary is saved to a local SQLite database
- 🕘 Browse, view, and delete past summaries on the History page
- ⏳ Loading indicators and friendly error messages for scraping/API/network failures
- 📱 Clean, responsive UI — works on desktop and mobile

## 🧱 Tech Stack

| Layer          | Technology                          |
|----------------|--------------------------------------|
| Frontend       | HTML, CSS, vanilla JavaScript        |
| Backend        | Python, Flask                        |
| Scraping       | Requests + BeautifulSoup4 (lxml)     |
| AI Summarization | Google Gemini API (free tier)      |
| Database       | SQLite                               |

## 📁 Project Structure

```
ai-news-summarizer/
├── app.py                  # Flask app: routes & request handling
├── scraper.py               # Requests + BeautifulSoup article extraction
├── summarizer.py             # Gemini API integration (summary/points/sentiment)
├── requirements.txt
├── .env.example              # Template for your environment variables
├── .gitignore
├── README.md
├── database/
│   ├── __init__.py
│   ├── db.py                 # SQLite schema + helper functions
│   └── news_summarizer.db    # Created automatically on first run
├── templates/
│   ├── index.html            # Main summarizer dashboard
│   └── history.html          # Saved-article history page
└── static/
    ├── css/
    │   └── style.css
    └── js/
        ├── script.js          # Logic for the summarizer page
        └── history.js         # Logic for the history page
```

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.9 or newer
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 2. Clone / download the project

```bash
git clone <your-repo-url> ai-news-summarizer
cd ai-news-summarizer
```

### 3. Create a virtual environment (recommended)

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure your environment variables

Copy the example file and add your own Gemini API key:

```bash
cp .env.example .env
```

Then edit `.env`:

```
GEMINI_API_KEY=your_actual_key_here
GEMINI_MODEL=gemini-1.5-flash
FLASK_SECRET_KEY=any-random-string
FLASK_DEBUG=True
```

> 🔒 `.env` is already listed in `.gitignore` — never commit your real API key.

### 6. Run the app

```bash
python app.py
```

The app will start at **http://127.0.0.1:5000**. The SQLite database file is created automatically inside `database/` the first time you run it — no manual setup needed.

### 7. Use it

1. Open `http://127.0.0.1:5000` in your browser.
2. Paste a news article URL (e.g. from BBC, Reuters, TechCrunch, etc.).
3. Click **Summarize** and wait a few seconds for the AI results.
4. View the summary, key points, and sentiment badge.
5. Click **History** in the nav bar to browse or delete past summaries.

## ⚠️ Notes & Limitations

- Some sites render articles with JavaScript or sit behind a paywall/bot-protection — the scraper works best on standard server-rendered news pages.
- The Gemini free tier has request-per-minute limits; if you hit them, wait a few seconds and try again (the app shows a friendly rate-limit message).
- Article text is capped at ~12,000 characters before being sent to the API to keep requests fast and within free-tier token limits.

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `No Gemini API key found` | Make sure `.env` exists and `GEMINI_API_KEY` is set, then restart the server. |
| `Couldn't find enough readable article text` | The page may be JS-rendered or paywalled — try a different article/source. |
| `Gemini API rate limit reached` | Wait ~30–60 seconds and try again (free tier limit). |
| Port 5000 already in use | Run `app.run(port=5001)` in `app.py`, or stop the other process using port 5000. |

## 📄 License

MIT — free to use, modify, and share. Great as a portfolio project!
