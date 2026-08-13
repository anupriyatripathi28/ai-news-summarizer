// history.js
// Handles the "History" page: expanding a saved article to view full
// details, and deleting entries.

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".history-item").forEach((item) => {
    const id = item.dataset.id;
    const toggleBtn = item.querySelector(".toggle-detail-btn");
    const deleteBtn = item.querySelector(".delete-btn");
    const detailEl = item.querySelector(".history-detail");

    toggleBtn.addEventListener("click", async () => {
      const isHidden = detailEl.classList.contains("hidden");

      if (isHidden && !detailEl.dataset.loaded) {
        toggleBtn.textContent = "Loading…";
        try {
          const res = await fetch(`/history/${id}`);
          const data = await res.json();
          if (!data.success) throw new Error(data.error);
          detailEl.innerHTML = renderDetail(data.article);
          detailEl.dataset.loaded = "true";
        } catch (err) {
          detailEl.innerHTML = `<p class="error-banner">Could not load details.</p>`;
        }
      }

      detailEl.classList.toggle("hidden");
      toggleBtn.textContent = detailEl.classList.contains("hidden") ? "View" : "Hide";
    });

    deleteBtn.addEventListener("click", async () => {
      if (!confirm("Delete this saved summary? This can't be undone.")) return;
      try {
        const res = await fetch(`/history/${id}/delete`, { method: "POST" });
        const data = await res.json();
        if (data.success) {
          item.remove();
        }
      } catch (err) {
        alert("Failed to delete. Please try again.");
      }
    });
  });
});

function renderDetail(article) {
  const points = article.key_points
    .map((p) => `<li>${escapeHtml(p)}</li>`)
    .join("");

  return `
    <h4>Full Summary</h4>
    <p>${escapeHtml(article.summary)}</p>
    <h4>Key Points</h4>
    <ul>${points}</ul>
  `;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
