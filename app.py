"""StudyMate - Flask backend.
Serves the resource finder, stores uploads, and records usability-test data
(task time, clicks, searches, wrong opens, success, SUS) for the statistics stage."""
import csv, io, os, random, re, sqlite3, time
from datetime import datetime
from pathlib import Path
from flask import (Flask, Response, abort, jsonify, render_template, request,
                   send_from_directory, session)
from werkzeug.utils import secure_filename

BASE = Path(__file__).parent
DB_PATH = BASE / "studymate.db"
UPLOADS = BASE / "uploads"
UPLOADS.mkdir(exist_ok=True)
ADMIN_KEY = os.environ.get("STUDYMATE_ADMIN_KEY", "studymate")
ALLOWED = {"pdf", "doc", "docx", "ppt", "pptx", "txt", "zip", "png", "jpg", "jpeg"}

app = Flask(__name__)
app.secret_key = os.environ.get("STUDYMATE_SECRET", "dev-only-change-me")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# --- Test tasks: EDIT these to resources that really exist in your class WhatsApp
# groups AND are seeded/uploaded in StudyMate, so both methods look for the same kind of thing.
TASKS = {
    1: {"text": "Find the Python Unit 2 practical programs file.",
        "title": "Python Practical Programs", "subject": "Python", "unit": "Unit 2"},
    2: {"text": "Find the Probability and Statistics Unit 1 notes.",
        "title": "Probability and Statistics Notes", "subject": "Statistics", "unit": "Unit 1"},
}
# Counterbalanced plans (method order and task-method pairing) -> participant_id % 4
PLANS = [
    [("current", 1), ("studymate", 2)],
    [("studymate", 1), ("current", 2)],
    [("current", 2), ("studymate", 1)],
    [("studymate", 2), ("current", 1)],
]
SEED = [
    # ---------- Python ----------
    ("Python Programming Notes - Unit 1", "Python", "Unit 1", "Notes",
     "Complete introduction to Python: variables, data types, operators, input/output, and control flow."),
    ("Python Practical Programs - Unit 2", "Python", "Unit 2", "Practical",
     "25 solved practical programs: loops, functions, lists, dictionaries, and file handling."),
    ("Python Functions & Modules - Unit 3", "Python", "Unit 3", "Notes",
     "Functions, scope, recursion, modules, packages, and the standard library."),
    ("Python OOP & File Handling - Unit 4", "Python", "Unit 4", "Notes",
     "Classes, objects, inheritance, exception handling, and file read/write operations."),

    # ---------- Probability and Statistics ----------
    ("Probability & Statistics - Unit 1 Notes", "Probability and Statistics", "Unit 1", "Notes",
     "Probability axioms, conditional probability, Bayes' theorem, and random variables."),
    ("Statistics Practical Problems - Unit 2", "Probability and Statistics", "Unit 2", "Practical",
     "40 solved numerical problems: mean, median, mode, variance, and standard deviation."),
    ("Hypothesis Testing Cheat Sheet", "Probability and Statistics", "Unit 3", "Notes",
     "t-test, chi-square, ANOVA, p-values, confidence intervals, and decision rules."),
    ("Correlation & Regression Notes", "Probability and Statistics", "Unit 4", "Notes",
     "Pearson & Spearman correlation, simple linear regression, and interpretation guidelines."),

    # ---------- Web Technology ----------
    ("HTML & CSS Fundamentals - Unit 1", "Web Technology", "Unit 1", "Notes",
     "Page structure, semantic HTML, CSS selectors, box model, flexbox, and grid."),
    ("Web Technology Practical File - Unit 2", "Web Technology", "Unit 2", "Practical",
     "10 complete practical exercises: forms, tables, responsive layouts, and CSS animations."),
    ("JavaScript Basics - Unit 3", "Web Technology", "Unit 3", "Notes",
     "DOM manipulation, events, fetch API, async/await, and form validation."),
    ("Previous Year Paper - Web Tech (2023)", "Web Technology", "Unit 5", "Previous Year Paper",
     "End-semester question paper with solutions and marking scheme."),

    # ---------- Design Thinking ----------
    ("Design Thinking Handbook", "Design Thinking", "Unit 1", "Notes",
     "The 5 stages: Empathise, Define, Ideate, Prototype, Test — with real case studies."),
    ("Empathy Map Templates - Unit 2", "Design Thinking", "Unit 2", "Template",
     "Blank and filled empathy map examples with user persona worksheets."),
    ("Ideation Techniques Cheat Sheet", "Design Thinking", "Unit 3", "Notes",
     "SCAMPER, mind mapping, brainstorming rules, and selection matrices."),

    # ---------- Artificial Intelligence ----------
    ("AI Search Algorithms - Unit 1", "Artificial Intelligence", "Unit 1", "Notes",
     "BFS, DFS, UCS, A* search with worked examples and complexity analysis."),
    ("AI Knowledge Representation - Unit 2", "Artificial Intelligence", "Unit 2", "Notes",
     "Propositional logic, first-order logic, inference rules, and resolution."),
    ("AI Practical File - Unit 3", "Artificial Intelligence", "Unit 3", "Practical",
     "Python implementations: BFS, DFS, A*, minimax, and alpha-beta pruning."),

    # ---------- Mathematics ----------
    ("Engineering Mathematics - Unit 1 Notes", "Mathematics", "Unit 1", "Notes",
     "Matrices, determinants, eigenvalues, and eigenvectors with solved examples."),
    ("Engineering Mathematics - Unit 2 Notes", "Mathematics", "Unit 2", "Notes",
     "Differential calculus, partial derivatives, and applications."),
    ("Maths Previous Year Paper (2023)", "Mathematics", "Unit 5", "Previous Year Paper",
     "Full end-semester paper with step-by-step solutions."),

    # ---------- Data Structures ----------
    ("Data Structures - Unit 1 Notes", "Data Structures", "Unit 1", "Notes",
     "Arrays, linked lists, stacks, queues, and their time complexities."),
    ("Data Structures Practical - Unit 2", "Data Structures", "Unit 2", "Practical",
     "15 C/Python programs: stack, queue, linked list, and tree operations."),
    ("Trees & Graphs - Unit 3 Notes", "Data Structures", "Unit 3", "Notes",
     "Binary trees, BST, AVL, graph representation, BFS, and DFS."),

    # ---------- Operating Systems ----------
    ("Operating Systems - Unit 1 Notes", "Operating Systems", "Unit 1", "Notes",
     "Processes, threads, scheduling algorithms (FCFS, SJF, Round Robin), and IPC."),
    ("OS Practical File - Unit 2", "Operating Systems", "Unit 2", "Practical",
     "Shell scripts and C programs: fork, exec, pipes, and semaphores."),
    ("Deadlocks & Memory Management", "Operating Systems", "Unit 3", "Notes",
     "Deadlock detection, Banker's algorithm, paging, and segmentation."),

    # ---------- Computer Networks ----------
    ("Computer Networks - Unit 1 Notes", "Computer Networks", "Unit 1", "Notes",
     "OSI model, TCP/IP stack, physical and data-link layer protocols."),
    ("CN Practical - Unit 2", "Computer Networks", "Unit 2", "Practical",
     "Packet Tracer simulations and socket programming examples."),
    ("Routing & Switching Notes", "Computer Networks", "Unit 3", "Notes",
     "Distance-vector, link-state routing, RIP, OSPF, and subnetting."),
]

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS resources(
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, subject TEXT NOT NULL,
            unit TEXT NOT NULL, resource_type TEXT NOT NULL, description TEXT, file_path TEXT,
            downloads INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS participants(
            id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, year TEXT, plan_index INTEGER,
            consent_at TEXT);
        CREATE TABLE IF NOT EXISTS task_runs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, participant_id INTEGER, method TEXT, task_id INTEGER,
            started_at REAL, finished_at REAL, duration_sec REAL, clicks INTEGER DEFAULT 0,
            searches INTEGER DEFAULT 0, wrong_opens INTEGER DEFAULT 0, success INTEGER);
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER, type TEXT, detail TEXT,
            ts TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS sus(
            participant_id INTEGER PRIMARY KEY, q1 INT,q2 INT,q3 INT,q4 INT,q5 INT,q6 INT,q7 INT,q8 INT,q9 INT,q10 INT,
            score REAL, sat_current INT, sat_studymate INT, comment TEXT);
        """)
        if db.execute("SELECT COUNT(*) FROM resources").fetchone()[0] == 0:
            for t, s, u, ty, d in SEED:
                # Placeholder file so downloads work in the demo. Replace via the Upload page.
                name = re.sub(r"\W+", "_", t) + ".txt"
                (UPLOADS / name).write_text(f"PLACEHOLDER for: {t} ({s}, {u}). Upload the real file.\n")
                db.execute("INSERT INTO resources(title,subject,unit,resource_type,description,file_path) VALUES(?,?,?,?,?,?)",
                           (t, s, u, ty, d, name))

init_db()

# ---------------- Pages ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return render_template("upload.html")
    f = request.files.get("file")
    title = request.form.get("title", "").strip()
    subject = request.form.get("subject", "").strip()
    unit = request.form.get("unit", "").strip()
    rtype = request.form.get("resource_type", "Notes").strip()
    if not (f and f.filename and title and subject and unit):
        return jsonify(error="Title, subject, unit and a file are required."), 400
    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
    if ext not in ALLOWED:
        return jsonify(error=f"File type .{ext} is not allowed."), 400
    name = f"{int(time.time())}_{secure_filename(f.filename)}"
    f.save(UPLOADS / name)
    with get_db() as db:
        db.execute("INSERT INTO resources(title,subject,unit,resource_type,description,file_path) VALUES(?,?,?,?,?,?)",
                   (title, subject, unit, rtype, request.form.get("description", "").strip(), name))
    return jsonify(ok=True)

@app.route("/download/<int:rid>")
def download(rid):
    with get_db() as db:
        row = db.execute("SELECT file_path FROM resources WHERE id=?", (rid,)).fetchone()
        if not row or not row["file_path"] or not (UPLOADS / row["file_path"]).exists():
            abort(404)
        db.execute("UPDATE resources SET downloads=downloads+1 WHERE id=?", (rid,))
    return send_from_directory(UPLOADS, row["file_path"], as_attachment=True)

# ---------------- Search API ----------------
@app.route("/api/resources")
def search_resources():
    q = request.args.get("q", "").strip()
    subject = request.args.get("subject", "").strip()
    unit = request.args.get("unit", "").strip()
    where, vals, score = [], [], []
    for tok in re.findall(r"\w+", q.lower())[:6]:
        like = f"%{tok}%"
        where.append("(LOWER(title||' '||subject||' '||unit||' '||resource_type||' '||COALESCE(description,'')) LIKE ?)")
        vals.append(like)
        score.append("(CASE WHEN LOWER(title) LIKE ? THEN 2 ELSE 1 END)")
    if subject: where.append("subject=?"); vals.append(subject)
    if unit: where.append("unit=?"); vals.append(unit)
    order_vals = [f"%{t}%" for t in re.findall(r"\w+", q.lower())[:6]]
    order = f"ORDER BY {'+'.join(score)} DESC, subject, unit, title" if score else "ORDER BY subject, unit, title"
    sql = "SELECT * FROM resources" + (" WHERE " + " AND ".join(where) if where else "") + " " + order
    with get_db() as db:
        rows = db.execute(sql, vals + order_vals).fetchall()
    return jsonify(resources=[dict(r) for r in rows], count=len(rows))

@app.route("/api/subjects")
def subjects():
    with get_db() as db:
        return jsonify([r[0] for r in db.execute("SELECT DISTINCT subject FROM resources ORDER BY subject")])

@app.route("/api/units")
def units():
    s = request.args.get("subject", "").strip()
    with get_db() as db:
        rows = db.execute("SELECT DISTINCT unit FROM resources" + (" WHERE subject=?" if s else "") + " ORDER BY unit",
                          (s,) if s else ()).fetchall()
    return jsonify([r[0] for r in rows])

# ---------------- Usability test ----------------
@app.route("/test")
def test_page():
    return render_template("test.html")

@app.route("/api/test/state")
def test_state():
    pid = session.get("pid")
    if not pid:
        return jsonify(started=False)
    with get_db() as db:
        p = db.execute("SELECT * FROM participants WHERE id=?", (pid,)).fetchone()
        done_runs = db.execute("SELECT COUNT(*) FROM task_runs WHERE participant_id=? AND finished_at IS NOT NULL", (pid,)).fetchone()[0]
        sus_done = db.execute("SELECT 1 FROM sus WHERE participant_id=?", (pid,)).fetchone() is not None
    plan = [{"method": m, "task_id": t, "text": TASKS[t]["text"]} for m, t in PLANS[p["plan_index"]]]
    return jsonify(started=True, code=p["code"], plan=plan, step=done_runs, sus_done=sus_done)

@app.route("/api/test/start", methods=["POST"])
def test_start():
    d = request.get_json(force=True)
    if not d.get("consent"):
        return jsonify(error="Consent is required."), 400
    with get_db() as db:
        n = db.execute("SELECT COUNT(*) FROM participants").fetchone()[0]
        cur = db.execute("INSERT INTO participants(code,year,plan_index,consent_at) VALUES(?,?,?,?)",
                         (f"P{n+1:02d}", d.get("year", ""), n % 4, datetime.now().isoformat()))
        session["pid"] = cur.lastrowid
    return jsonify(ok=True)

@app.route("/api/test/reset", methods=["POST"])
def test_reset():
    session.pop("pid", None)
    return jsonify(ok=True)

@app.route("/api/run/start", methods=["POST"])
def run_start():
    pid = session.get("pid") or abort(400)
    d = request.get_json(force=True)
    with get_db() as db:
        cur = db.execute("INSERT INTO task_runs(participant_id,method,task_id,started_at) VALUES(?,?,?,?)",
                         (pid, d["method"], d["task_id"], time.time()))
        t = TASKS[d["task_id"]]
        tgt = db.execute("SELECT id FROM resources WHERE title=? AND subject=? AND unit=?",
                         (t["title"], t["subject"], t["unit"])).fetchone()
    return jsonify(run_id=cur.lastrowid, target_id=tgt["id"] if tgt else None, text=t["text"])

def _finish(db, run_id, success, clicks=None):
    r = db.execute("SELECT started_at, finished_at FROM task_runs WHERE id=?", (run_id,)).fetchone()
    if not r or r["finished_at"]:
        return
    now = time.time()
    db.execute("UPDATE task_runs SET finished_at=?, duration_sec=?, success=?, clicks=COALESCE(?,clicks) WHERE id=?",
               (now, round(now - r["started_at"], 2), int(success), clicks, run_id))

@app.route("/api/run/event", methods=["POST"])
def run_event():
    d = request.get_json(force=True)
    rid, typ = d["run_id"], d["type"]
    with get_db() as db:
        run = db.execute("SELECT task_id FROM task_runs WHERE id=?", (rid,)).fetchone() or abort(400)
        db.execute("INSERT INTO events(run_id,type,detail) VALUES(?,?,?)", (rid, typ, str(d.get("detail", ""))[:200]))
        if typ == "search":
            db.execute("UPDATE task_runs SET searches=searches+1 WHERE id=?", (rid,))
        elif typ == "open":
            t = TASKS[run["task_id"]]
            hit = db.execute("SELECT 1 FROM resources WHERE id=? AND title=? AND subject=? AND unit=?",
                             (d["resource_id"], t["title"], t["subject"], t["unit"])).fetchone()
            if hit:
                _finish(db, rid, True, d.get("clicks"))
                return jsonify(finished=True, success=True)
            db.execute("UPDATE task_runs SET wrong_opens=wrong_opens+1 WHERE id=?", (rid,))
    return jsonify(finished=False)

@app.route("/api/run/finish", methods=["POST"])
def run_finish():
    d = request.get_json(force=True)
    with get_db() as db:
        _finish(db, d["run_id"], d.get("success", False), d.get("clicks"))
    return jsonify(ok=True)

@app.route("/api/test/sus", methods=["POST"])
def test_sus():
    pid = session.get("pid") or abort(400)
    d = request.get_json(force=True)
    a = d.get("answers", [])
    if len(a) != 10 or not all(isinstance(x, int) and 1 <= x <= 5 for x in a):
        return jsonify(error="Answer all 10 questions (1-5)."), 400
    score = sum((x - 1) if i % 2 == 0 else (5 - x) for i, x in enumerate(a)) * 2.5
    with get_db() as db:
        db.execute("INSERT OR REPLACE INTO sus VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (pid, *a, score, d.get("sat_current"), d.get("sat_studymate"), (d.get("comment") or "")[:500]))
    return jsonify(ok=True, score=score)

# ---------------- Export (anonymous data for analysis/submission) ----------------
@app.route("/admin/export/<table>.csv")
def export(table):
    if request.args.get("key") != ADMIN_KEY:
        abort(403)
    if table not in {"task_runs", "sus", "participants", "events"}:
        abort(404)
    with get_db() as db:
        cur = db.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow([c[0] for c in cur.description])
        w.writerows([tuple(r) for r in rows])
    return Response(buf.getvalue(), mimetype="text/csv")

if __name__ == "__main__":
    app.run(debug=True)