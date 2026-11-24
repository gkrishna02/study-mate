const $ = (id) => document.getElementById(id);
const post = (url, body) => fetch(url, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body)
}).then(r => r.json());

const SUS_QUESTIONS = [
  "I think I would like to use StudyMate frequently.",
  "I found StudyMate unnecessarily complex.",
  "I thought StudyMate was easy to use.",
  "I think I would need the support of a technical person to use StudyMate.",
  "I found the various functions in StudyMate were well integrated.",
  "I thought there was too much inconsistency in StudyMate.",
  "I would imagine most people would learn StudyMate very quickly.",
  "I found StudyMate very awkward to use.",
  "I felt very confident using StudyMate.",
  "I needed to learn a lot of things before I could get going with StudyMate.",
];

let state = { started: false, plan: [], step: 0, sus_done: false };

// ---------- Step switching ----------
function showStep(name) {
  ["stepStart", "stepRun", "stepSus", "stepDone"].forEach(id => ($(id).hidden = true));
  $(name).hidden = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ---------- Start button ----------
const consent = $("consent"), yearSel = $("year"), startBtn = $("startBtn");
function checkStart() { startBtn.disabled = !(consent.checked && yearSel.value); }
consent.addEventListener("change", checkStart);
yearSel.addEventListener("change", checkStart);

startBtn.addEventListener("click", async () => {
  await post("/api/test/start", { consent: true, year: yearSel.value });
  await refreshState();
});

// ---------- State machine ----------
async function refreshState() {
  const res = await fetch("/api/test/state");
  state = await res.json();

  if (!state.started) return showStep("stepStart");
  if (state.sus_done) return showStep("stepDone");
  if (state.step >= state.plan.length) return showSusForm();
  showRunStep();
}

// ---------- Run step ----------
function showRunStep() {
  showStep("stepRun");
  const current = state.plan[state.step];
  const methodLabel = current.method === "current" ? "WhatsApp / Current Method" : "StudyMate";

  $("runTitle").textContent = `Task ${state.step + 1} of ${state.plan.length}`;
  $("runText").textContent = current.text;
  $("runMeta").innerHTML = `
    <span class="meta-pill"><strong>Method:</strong> ${methodLabel}</span>
    <span class="meta-pill"><strong>Task ID:</strong> ${current.task_id}</span>
  `;

  $("beginBtn").onclick = () => beginRun(current);
}

async function beginRun(current) {
  $("beginBtn").disabled = true;
  $("beginBtn").textContent = "Starting…";

  const run = await post("/api/run/start", {
    method: current.method,
    task_id: current.task_id
  });

  sessionStorage.setItem("sm_run", JSON.stringify({
    run_id: run.run_id,
    start: Date.now(),
    text: run.text,
    target_id: run.target_id,
    method: current.method
  }));

  // For the "current" (WhatsApp) method, we still go to the search page but the
  // user is told to search within WhatsApp first, then return. To keep the demo
  // simple, both methods use the same StudyMate UI. The taskbar tracks their time.
  location.href = "/";
}

// ---------- SUS form ----------
function showSusForm() {
  showStep("stepSus");
  const container = $("susQuestions");
  if (container.children.length) return;

  SUS_QUESTIONS.forEach((q, i) => {
    const item = document.createElement("div");
    item.className = "sus-item";
    item.innerHTML = `
      <p>${i + 1}. ${q}</p>
      <div class="sus-scale">
        ${[1,2,3,4,5].map(n => `
          <label>
            <input type="radio" name="sus_${i}" value="${n}">
            <span>${n}</span>
          </label>`).join("")}
      </div>`;
    container.appendChild(item);
  });

  container.querySelectorAll("input").forEach(input => {
    input.addEventListener("change", () => {
      const labels = input.closest(".sus-scale").querySelectorAll("label");
      labels.forEach(l => { l.style.background = ""; l.style.color = ""; });
      input.closest("label").style.background = "var(--brand-1)";
      input.closest("label").style.color = "white";
    });
  });
}

$("submitSusBtn").addEventListener("click", async () => {
  const answers = [];
  for (let i = 0; i < 10; i++) {
    const sel = document.querySelector(`input[name="sus_${i}"]:checked`);
    if (!sel) {
      $("susMessage").textContent = `Please answer question ${i + 1}.`;
      $("susMessage").className = "message error";
      return;
    }
    answers.push(parseInt(sel.value));
  }

  const res = await post("/api/test/sus", {
    answers,
    sat_current: parseInt($("satCurrent").value) || null,
    sat_studymate: parseInt($("satStudyMate").value) || null,
    comment: $("comment").value
  });

  if (res.ok) {
    $("susMessage").textContent = `SUS Score: ${res.score.toFixed(1)} / 100. Thank you!`;
    $("susMessage").style.color = "#16a34a";
    setTimeout(() => showStep("stepDone"), 1500);
  }
});

// ---------- Start New Test button ----------
document.addEventListener("click", async (e) => {
  if (e.target.id === "newTestBtn") {
    await post("/api/test/reset", {});
    sessionStorage.removeItem("sm_run");
    $("consent").checked = false;
    $("year").value = "";
    $("startBtn").disabled = true;
    $("susMessage").textContent = "";
    $("susQuestions").innerHTML = "";
    document.querySelectorAll("input[type=number], textarea").forEach(i => i.value = "");
    showStep("stepStart");
  }
});

// ---------- Init ----------
(async () => {
  // If user just returned from a task via taskbar finish
  const run = JSON.parse(sessionStorage.getItem("sm_run") || "null");
  if (!run) await refreshState();
})();