const $ = (id) => document.getElementById(id);
const searchInput = $("searchInput"), unitFilter = $("unitFilter"), chips = $("chips");
const resourceList = $("resourceList"), resultCount = $("resultCount"), message = $("message");
let subject = "";

// ---- Test-mode task bar ----
const run = JSON.parse(sessionStorage.getItem("sm_run") || "null");
let clicks = 0, timerId = null;

function post(url, body) {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  }).then(r => r.json());
}

function endRun(success) {
  clearInterval(timerId);
  sessionStorage.removeItem("sm_run");
  post("/api/run/finish", { run_id: run.run_id, success, clicks })
    .then(() => (location.href = "/test"));
}

if (run) {
  const bar = $("taskbar");
  bar.hidden = false;
  bar.innerHTML = `<div><strong>Task:</strong> ${run.text}</div><div class="tb-right"><span id="clock">0:00</span><button class="btn ghost" id="giveUp" type="button">I finished / Found it</button></div>`;
  const tick = () => {
    const s = Math.floor((Date.now() - run.start) / 1000);
    $("clock").textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  };
  tick();
  timerId = setInterval(tick, 500);
  document.addEventListener("click", () => clicks++, true);
  $("giveUp").addEventListener("click", () => endRun(false));
}

// ---- Helpers ----
const PALETTE = [
  "#4f46e5", // indigo — Python
  "#06b6d4", // cyan — Probability and Statistics
  "#f59e0b", // amber — Web Technology
  "#ec4899", // pink — Design Thinking
  "#8b5cf6", // violet — AI
  "#10b981", // emerald — Mathematics
  "#ef4444", // red — Data Structures
  "#0ea5e9", // sky — Operating Systems
  "#14b8a6", // teal — Computer Networks
  "#f97316", // orange — fallback
];
const colourOf = (s) => PALETTE[[...s].reduce((a, c) => a + c.charCodeAt(0), 0) % PALETTE.length];
const el = (tag, cls, text) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
};

// ---- Load data ----
async function loadUnits() {
  try {
    const list = await (await fetch("/api/units?subject=" + encodeURIComponent(subject))).json();
    const keep = unitFilter.value;
    unitFilter.innerHTML = `<option value="">All units</option>` + list.map(o => `<option>${o}</option>`).join("");
    if (list.includes(keep)) unitFilter.value = keep;
  } catch (e) { console.error(e); }
}

async function loadChips() {
  try {
    const list = await (await fetch("/api/subjects")).json();
    chips.replaceChildren();
    ["", ...list].forEach(s => {
      const b = el("button", "chip" + (s === subject ? " on" : ""), s || "All subjects");
      b.type = "button";
      b.setAttribute("aria-pressed", s === subject);
      if (s) {
        const dot = el("i", "dot");
        dot.style.background = colourOf(s);
        b.prepend(dot);
      }
      b.addEventListener("click", async () => {
        subject = s;
        unitFilter.value = "";
        await loadChips();
        await loadUnits();
        searchResources(true);
      });
      chips.appendChild(b);
    });
  } catch (e) { console.error(e); }
}

// ---- Card ----
function card(r, index = 0) {
  const a = el("article", "resource-card");
  a.style.setProperty("--spine", colourOf(r.subject));
  a.style.animationDelay = `${Math.min(index * 40, 400)}ms`;

  const top = el("div", "rc-top");
  top.append(el("span", "badge", r.resource_type), el("span", "unit", r.unit));

  const subj = el("p", "subj");
  const dot = el("i", "dot");
  dot.style.cssText = `width:8px;height:8px;border-radius:50%;display:inline-block;background:${colourOf(r.subject)}`;
  subj.append(dot, r.subject);

  const foot = el("div", "rc-foot");
  const n = r.downloads || 0;
  const dl = el("span", "dl", n ? `${n} download${n === 1 ? "" : "s"}` : "New");

  const btn = el("a", "btn small", "Download");
  btn.href = `/download/${r.id}`;
  btn.addEventListener("click", async (e) => {
    if (!run) return;
    e.preventDefault();
    const res = await post("/api/run/event", {
      run_id: run.run_id, type: "open", resource_id: r.id, clicks
    });
    if (res.finished) {
      clearInterval(timerId);
      sessionStorage.removeItem("sm_run");
      location.href = "/test";
    } else {
      message.textContent = "That's not the file for this task. Keep looking.";
      message.className = "message error";
    }
  });

  foot.append(dl, btn);
  a.append(top, el("h3", "", r.title), subj, el("p", "desc", r.description || ""), foot);
  return a;
}

function skeletons() {
  resourceList.replaceChildren(
    ...Array.from({ length: 6 }, () => el("div", "resource-card skeleton"))
  );
}

function emptyState() {
  const d = el("div", "empty");
  d.innerHTML = `
    <svg viewBox="0 0 64 64" width="56" height="56" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true">
      <circle cx="28" cy="28" r="16"/><path d="m40 40 14 14M22 28h12"/>
    </svg>
    <h3>Nothing matches yet</h3>
    <p>Try fewer words, or clear the subject and unit filters.</p>`;
  const b = el("button", "btn ghost dark", "Clear filters");
  b.type = "button";
  b.onclick = async () => {
    subject = "";
    searchInput.value = "";
    unitFilter.value = "";
    await loadChips();
    await loadUnits();
    searchResources(true);
  };
  d.appendChild(b);
  return d;
}

// ---- Search ----
async function searchResources(logEvent) {
  resultCount.textContent = "Searching…";
  message.textContent = "";
  message.className = "message";
  skeletons();

  const params = new URLSearchParams({
    q: searchInput.value.trim(),
    subject,
    unit: unitFilter.value
  });

  try {
    const res = await fetch(`/api/resources?${params}`);
    if (!res.ok) throw new Error();
    const data = await res.json();
    resultCount.textContent =
      `${data.count} ${data.count === 1 ? "resource" : "resources"}${subject ? " in " + subject : ""}`;

    resourceList.replaceChildren(
      ...(data.count ? data.resources.map((r, i) => card(r, i)) : [emptyState()])
    );

    if (run && logEvent) {
      post("/api/run/event", {
        run_id: run.run_id, type: "search", detail: params.toString()
      });
    }
  } catch (e) {
    resultCount.textContent = "";
    resourceList.replaceChildren();
    message.textContent = "Could not load resources. Is the Python server running?";
    message.className = "message error";
  }
}

$("searchButton").addEventListener("click", () => searchResources(true));
searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") searchResources(true);
});
let typing;
searchInput.addEventListener("input", () => {
  clearTimeout(typing);
  typing = setTimeout(() => searchResources(false), 300);
});
unitFilter.addEventListener("change", () => searchResources(true));

(async () => {
  await Promise.all([loadChips(), loadUnits()]);
  searchResources(false);
})();