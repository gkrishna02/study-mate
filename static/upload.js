const $ = (id) => document.getElementById(id);
const form = $("uploadForm");
const fileDrop = $("fileDrop");
const fileInput = $("file");
const fileName = $("fileName");
const message = $("formMessage");

// Show file name when selected
fileInput.addEventListener("change", () => {
  const f = fileInput.files[0];
  fileName.textContent = f ? `📎 ${f.name} (${(f.size / 1024).toFixed(1)} KB)` : "";
});

// Drag and drop visuals
["dragenter", "dragover"].forEach(evt =>
  fileDrop.addEventListener(evt, (e) => { e.preventDefault(); fileDrop.classList.add("dragover"); })
);
["dragleave", "drop"].forEach(evt =>
  fileDrop.addEventListener(evt, (e) => { e.preventDefault(); fileDrop.classList.remove("dragover"); })
);
fileDrop.addEventListener("drop", (e) => {
  const f = e.dataTransfer.files[0];
  if (f) {
    fileInput.files = e.dataTransfer.files;
    fileName.textContent = `📎 ${f.name} (${(f.size / 1024).toFixed(1)} KB)`;
  }
});

// Submit
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  message.textContent = "Uploading…";
  message.className = "message";

  const data = new FormData(form);
  try {
    const res = await fetch("/upload", { method: "POST", body: data });
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || "Upload failed.");

    message.textContent = "✅ Uploaded successfully! Redirecting…";
    message.className = "message";
    message.style.color = "#16a34a";

    setTimeout(() => (location.href = "/"), 1200);
  } catch (err) {
    message.textContent = `⚠️ ${err.message}`;
    message.className = "message error";
  }
});