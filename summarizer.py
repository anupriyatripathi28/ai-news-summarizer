"""
summarizer.py
-------------
Wraps calls to Google's Gemini API (free tier) to turn raw article text
into a short summary, a list of key points, and a sentiment label.

The Gemini API key is read from the environment (never hard-coded), via
a .env file loaded in app.py with python-dotenv.

We call the REST endpoint directly with `requests` so the project has
no dependency on the (larger, faster-changing) google-generativeai SDK.
"""

import os
import json
import re
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1/models/"
    f"{GEMINI_MODEL}:generateContent"
)

REQUEST_TIMEOUT = 30  # seconds

# Cap how much article text we send, to stay comfortably inside free-tier
# token limits and keep responses fast.
MAX_CONTENT_CHARS = 12000


class SummarizerError(Exception):
    """Raised when the Gemini API call fails or returns something we can't use."""
    pass


PROMPT_TEMPLATE = """You are a professional news analyst. Read the article below and
respond with ONLY a valid JSON object (no markdown fences, no extra text) with this
exact shape:

{{
  "summary": "A concise 3 to 5 sentence summary of the article.",
  "key_points": ["First key point", "Second key point", "Third key point", "..."],
  "sentiment": "Positive" | "Negative" | "Neutral"
}}

Guidelines:
- "summary" must be 3-5 complete sentences, in your own words.
- "key_points" should be 4-6 short bullet-point style strings capturing the most
  important facts/takeaways.
- "sentiment" must reflect the overall tone of the article's subject matter and be
  exactly one of: Positive, Negative, Neutral.

Article title: {title}

Article text:
\"\"\"
{content}
\"\"\"
"""


def summarize_article(title, content):
    """
    Send the article to Gemini and return a dict:
        {"summary": str, "key_points": [str, ...], "sentiment": str}
    Raises SummarizerError on any failure (missing key, network error,
    unparseable response, etc.) so app.py can show a friendly message.
    """
    if not GEMINI_API_KEY:
        raise SummarizerError(
            "No Gemini API key found. Set GEMINI_API_KEY in your .env file "
            "(see .env.example)."
        )

    trimmed_content = content[:MAX_CONTENT_CHARS]
    prompt = PROMPT_TEMPLATE.format(title=title, content=trimmed_content)

    payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": prompt
                }
            ]
        }
    ],
    "generationConfig": {
    "temperature": 0.2,
    "maxOutputTokens": 4096,
    "responseMimeType": "application/json",
    "responseSchema": {
        "type": "OBJECT",
        "properties": {
            "summary": {
                "type": "STRING"
            },
            "key_points": {
                "type": "ARRAY",
                "items": {
                    "type": "STRING"
                }
            },
            "sentiment": {
                "type": "STRING",
                "enum": ["Positive", "Negative", "Neutral"]
            }
        },
        "required": ["summary", "key_points", "sentiment"]
    }
}
}

    try:
        response = requests.post(
    GEMINI_URL,
    headers={
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json",
    },
    json=payload,
    timeout=REQUEST_TIMEOUT,
)
    except requests.exceptions.RequestException as e:
        raise SummarizerError(f"Could not reach the Gemini API: {e}")

    if response.status_code == 429:
        raise SummarizerError(
            "Gemini API rate limit reached (free tier). Please wait a moment and try again."
        )
    if response.status_code != 200:
        raise SummarizerError(
            f"Gemini API returned an error (status {response.status_code}): {response.text[:300]}"
        )

    data = response.json()
    print("Gemini finish reason:", data["candidates"][0].get("finishReason"))
    print("Gemini usage:", data.get("usageMetadata"))

    try:
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise SummarizerError("Unexpected response format from Gemini API.")

    return _parse_model_output(raw_text)


def _parse_model_output(raw_text):
    """
    Parse Gemini's JSON response safely.
    """

    cleaned = raw_text.strip()

    # Remove markdown code fences if present
    cleaned = re.sub(
        r"^```json\s*",
        "",
        cleaned,
        flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r"^```\s*",
        "",
        cleaned
    )
    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned
    )

    # Find the JSON object if Gemini returned extra text
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]

    try:
        result = json.loads(cleaned)

    except json.JSONDecodeError as e:
        print("GEMINI RAW RESPONSE:")
        print(raw_text)

        raise SummarizerError(
            f"Could not parse the AI's response as JSON: {e}"
        ) from e

    summary = str(result.get("summary", "")).strip()

    key_points = result.get("key_points", [])

    sentiment = str(
        result.get("sentiment", "Neutral")
    ).strip().capitalize()

    if not summary:
        raise SummarizerError(
            "The AI response did not include a summary."
        )

    if not isinstance(key_points, list):
        key_points = [str(key_points)]

    if sentiment not in (
        "Positive",
        "Negative",
        "Neutral"
    ):
        sentiment = "Neutral"

    return {
        "summary": summary,
        "key_points": [
            str(point).strip()
            for point in key_points
            if str(point).strip()
        ],
        "sentiment": sentiment,
    }