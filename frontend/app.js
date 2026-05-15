const API_BASE = "http://localhost:8000";

const form = document.getElementById("broadcastForm");
const btnText = document.getElementById("btnText");
const btnLoader = document.getElementById("btnLoader");
const generateBtn = document.getElementById("generateBtn");
const result = document.getElementById("result");
const errorBox = document.getElementById("errorBox");
const errorText = document.getElementById("errorText");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = document.getElementById("name").value.trim();
  const city = document.getElementById("city").value.trim();
  const language = document.getElementById("language").value;

  if (!name || !city) return;

  // Reset UI
  result.classList.add("hidden");
  errorBox.classList.add("hidden");
  generateBtn.disabled = true;
  btnText.classList.add("hidden");
  btnLoader.classList.remove("hidden");

  try {
    const response = await fetch(`${API_BASE}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, city, language }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Generation failed");
    }

    const data = await response.json();

    document.getElementById("scriptText").textContent = data.script;

    const video = document.getElementById("broadcastVideo");
    video.src = data.video_url;
    video.load();

    const dl = document.getElementById("downloadLink");
    dl.href = data.video_url;
    dl.download = `newsgen-${name.toLowerCase().replace(/\s+/g, "-")}.mp4`;

    result.classList.remove("hidden");
    video.play().catch(() => {}); // autoplay where allowed

  } catch (err) {
    errorText.textContent = `Error: ${err.message}`;
    errorBox.classList.remove("hidden");
  } finally {
    generateBtn.disabled = false;
    btnText.classList.remove("hidden");
    btnLoader.classList.add("hidden");
  }
});
