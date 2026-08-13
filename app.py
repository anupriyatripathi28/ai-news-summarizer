"""
app.py
------
Entry point for the AI News Summarizer Flask application.

Routes:
    GET  /               -> main dashboard (URL input + results area)
    POST /summarize       -> scrape a URL, summarize with Gemini, save to DB, return JSON
    GET  /history          -> page listing all previously summarized articles
    GET  /history/<id>     -> JSON detail for one saved article (used by history page)
    POST /history/<id>/delete -> remove one saved article

Run locally with:  python app.py
"""

import os
import json
import logging

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load variables from .env into the environment (GEMINI_API_KEY, etc.)
load_dotenv()


from database import db
from scraper import fetch_article, ScraperError
from summarizer import summarize_article, SummarizerError


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the SQLite table (if needed) as soon as the app starts.
db.init_db()


@app.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("index.html")


@app.route("/summarize", methods=["POST"])
def summarize():
    """
    Main API endpoint used by the frontend (via fetch/AJAX).
    Expects JSON body: {"url": "https://..."}
    Returns JSON: {success, title, url, summary, key_points, sentiment, id}
    or {success: false, error: "..."} with an appropriate HTTP status code.
    """
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify(success=False, error="Please provide a URL."), 400

    # Step 1: Scrape the article
    try:
        title, content = fetch_article(url)
    except ScraperError as e:
        logger.warning("Scraping failed for %s: %s", url, e)
        return jsonify(success=False, error=str(e)), 422

    # Step 2: Summarize with Gemini
    try:
        result = summarize_article(title, content)
    except SummarizerError as e:
        logger.warning("Summarization failed for %s: %s", url, e)
        return jsonify(success=False, error=str(e)), 502

    # Step 3: Save to SQLite history
    try:
        article_id = db.save_article(
            url=url,
            title=title,
            content=content,
            summary=result["summary"],
            key_points_json=json.dumps(result["key_points"]),
            sentiment=result["sentiment"],
        )
    except Exception as e:
        # Saving history failing shouldn't block showing the user their result
        logger.error("Failed to save article to DB: %s", e)
        article_id = None

    return jsonify(
        success=True,
        id=article_id,
        url=url,
        title=title,
        summary=result["summary"],
        key_points=result["key_points"],
        sentiment=result["sentiment"],
    )


@app.route("/history")
def history():
    """Render the history page listing all saved articles."""
    articles = db.get_all_articles()
    return render_template("history.html", articles=articles)


@app.route("/history/<int:article_id>")
def history_detail(article_id):
    """Return full JSON detail for one saved article (used to expand a history row)."""
    article = db.get_article_by_id(article_id)
    if not article:
        return jsonify(success=False, error="Article not found."), 404

    article["key_points"] = json.loads(article["key_points"])
    return jsonify(success=True, article=article)


@app.route("/history/<int:article_id>/delete", methods=["POST"])
def history_delete(article_id):
    """Delete one saved article from history."""
    db.delete_article(article_id)
    return jsonify(success=True)


@app.errorhandler(404)
def not_found(e):
    return jsonify(success=False, error="Not found."), 404


@app.errorhandler(500)
def server_error(e):
    logger.exception("Unhandled server error")
    return jsonify(success=False, error="Internal server error."), 500


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    app.run(debug=debug_mode, port=5000)
