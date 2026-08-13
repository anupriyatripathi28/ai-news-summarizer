// script.js
// Handles the main "Summarize" page: submitting the URL form, showing a
// loading indicator, rendering the results dashboard, and displaying errors.

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("summarize-form");
  const urlInput = document.getElementById("url-input");
  const submitBtn = document.getElementById("submit-btn");
  const clearNav = document.getElementById("clear-nav");

  const loadingEl = document.getElementById("loading");
  const resultsEl = document.getElementById("results");
  const errorBanner = document.getElementById("error-banner");

  const resultTitle = document.getElementById("result-title");
  const resultUrl = document.getElementById("result-url");
  const resultSummary = document.getElementById("result-summary");
  const resultKeypoints = document.getElementById("result-keypoints");
  const sentimentBadge = document.getElementById("sentiment-badge");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const url = urlInput.value.trim();
    if (!url) return;

    setLoading(true);
    hideError();
    resultsEl.classList.add("hidden");

    try {
      const response = await fetch("/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Something went wrong. Please try again.");
      }

      renderResults(data);
    } catch (err) {
      // Covers both network failures and errors thrown above
      showError(err.message || "Unexpected error. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  });

  function setLoading(isLoading) {
    loadingEl.classList.toggle("hidden", !isLoading);
    submitBtn.disabled = isLoading;
    submitBtn.textContent = isLoading ? "Summarizing…" : "Summarize";
  }

  function showError(message) {
    errorBanner.textContent = message;
    errorBanner.classList.remove("hidden");
  }

  function hideError() {
    errorBanner.classList.add("hidden");
    errorBanner.textContent = "";
  }

  function renderResults(data) {
    resultTitle.textContent = data.title;
    resultUrl.textContent = data.url;
    resultUrl.href = data.url;
    resultSummary.textContent = data.summary;

    resultKeypoints.innerHTML = "";
    data.key_points.forEach((point) => {
      const li = document.createElement("li");
      li.textContent = point;
      resultKeypoints.appendChild(li);
    });

    sentimentBadge.textContent = data.sentiment;
    sentimentBadge.className = "badge badge-" + data.sentiment.toLowerCase();

    resultsEl.classList.remove("hidden");
    resultsEl.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  clearNav.addEventListener("click", (event) => {
    event.preventDefault();

    urlInput.value = "";

    resultsEl.classList.add("hidden");
    loadingEl.classList.add("hidden");

    resultTitle.textContent = "";
    resultUrl.textContent = "";
    resultUrl.href = "#";
    resultSummary.textContent = "";
    resultKeypoints.innerHTML = "";

    sentimentBadge.textContent = "";
    sentimentBadge.className = "badge";

    hideError();

    urlInput.focus();
  });
  
});
