"""
generate_notes.py
Generates real, downloadable PDF notes for Unit 1 of each subject.
Run once:  python generate_notes.py
Outputs PDFs to uploads/ and links them to the DB.
"""
import os
from pathlib import Path
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
)

BASE = Path(__file__).parent
UPLOADS = BASE / "uploads"
UPLOADS.mkdir(exist_ok=True)
DB = BASE / "studymate.db"

# ---------- Note content per subject ----------
NOTES = {
    "Python": {
        "title": "Python Programming Notes — Unit 1",
        "subtitle": "Introduction to Python & Programming Basics",
        "sections": [
            ("1. What is Python?",
             "Python is a high-level, interpreted, general-purpose programming language. "
             "It was created by Guido van Rossum and released in 1991. Python emphasizes "
             "code readability with its clean and simple syntax. It supports multiple "
             "programming paradigms including procedural, object-oriented, and functional."),
            ("2. Features of Python",
             "• Easy to learn and read — close to English<br/>"
             "• Interpreted — executes line by line<br/>"
             "• Dynamically typed — no need to declare variable types<br/>"
             "• Free and open source<br/>"
             "• Large standard library<br/>"
             "• Platform independent — runs on Windows, macOS, Linux"),
            ("3. Variables and Data Types",
             "A variable is a named memory location used to store data. Python supports "
             "several data types:<br/><br/>"
             "<b>int</b> — 10, -5, 1000<br/>"
             "<b>float</b> — 3.14, -0.5<br/>"
             "<b>str</b> — 'hello', \"world\"<br/>"
             "<b>bool</b> — True, False<br/>"
             "<b>list</b> — [1, 2, 3]<br/>"
             "<b>tuple</b> — (1, 2, 3)<br/>"
             "<b>dict</b> — {'name': 'Riya', 'age': 18}"),
            ("4. Operators in Python",
             "• Arithmetic: +  -  *  /  //  %  **<br/>"
             "• Relational: ==  !=  &gt;  &lt;  &gt;=  &lt;=<br/>"
             "• Logical: and  or  not<br/>"
             "• Assignment: =  +=  -=  *=  /="),
            ("5. Control Flow",
             "Python provides <b>if</b>, <b>elif</b>, and <b>else</b> for decision-making, "
             "and <b>for</b> and <b>while</b> loops for iteration.<br/><br/>"
             "<b>Example:</b><br/>"
             "for i in range(5):<br/>"
             "&nbsp;&nbsp;&nbsp;&nbsp;if i % 2 == 0:<br/>"
             "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;print(i, 'is even')<br/>"
             "&nbsp;&nbsp;&nbsp;&nbsp;else:<br/>"
             "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;print(i, 'is odd')"),
            ("6. Input and Output",
             "Input: <b>name = input(\"Enter your name: \")</b><br/>"
             "Output: <b>print(\"Hello,\", name)</b>"),
            ("7. Summary",
             "In this unit we covered: what Python is, its key features, variables, "
             "data types, operators, control flow, and basic I/O. In the next unit we "
             "will solve practical problems involving loops, functions, and lists."),
        ],
    },
    "Probability and Statistics": {
        "title": "Probability & Statistics — Unit 1",
        "subtitle": "Probability Foundations",
        "sections": [
            ("1. Definition of Probability",
             "Probability is a numerical measure of the likelihood of an event occurring. "
             "It ranges from 0 (impossible) to 1 (certain)."),
            ("2. Sample Space and Events",
             "The sample space S is the set of all possible outcomes of an experiment. "
             "An event is any subset of the sample space."),
            ("3. Axioms of Probability (Kolmogorov)",
             "1) P(S) = 1<br/>"
             "2) 0 ≤ P(A) ≤ 1 for any event A<br/>"
             "3) If A and B are mutually exclusive, P(A ∪ B) = P(A) + P(B)"),
            ("4. Conditional Probability",
             "P(A | B) = P(A ∩ B) / P(B), provided P(B) > 0."),
            ("5. Bayes' Theorem",
             "P(A | B) = [ P(B | A) × P(A) ] / P(B)<br/><br/>"
             "It is used to update the probability of a hypothesis given new evidence."),
            ("6. Random Variables",
             "A random variable maps each outcome of an experiment to a real number. "
             "It can be discrete (countable values) or continuous (any value in an interval)."),
            ("7. Expected Value and Variance",
             "E(X) = Σ x · P(x)<br/>"
             "Var(X) = E(X²) − [E(X)]²"),
        ],
    },
    "Web Technology": {
        "title": "Web Technology — Unit 1",
        "subtitle": "HTML & CSS Fundamentals",
        "sections": [
            ("1. What is HTML?",
             "HTML (HyperText Markup Language) is the standard language for creating web "
             "pages. It describes the structure of a page using tags."),
            ("2. HTML Document Structure",
             "<b>&lt;!DOCTYPE html&gt;</b><br/>"
             "<b>&lt;html&gt;</b><br/>"
             "<b>&lt;head&gt;</b> — metadata, title, styles<br/>"
             "<b>&lt;body&gt;</b> — visible content"),
            ("3. Common HTML Tags",
             "• Headings: &lt;h1&gt; to &lt;h6&gt;<br/>"
             "• Paragraph: &lt;p&gt;<br/>"
             "• Link: &lt;a href=\"...\"&gt;<br/>"
             "• Image: &lt;img src=\"...\"&gt;<br/>"
             "• List: &lt;ul&gt;, &lt;ol&gt;, &lt;li&gt;<br/>"
             "• Table: &lt;table&gt;, &lt;tr&gt;, &lt;td&gt;"),
            ("4. Introduction to CSS",
             "CSS (Cascading Style Sheets) is used to style HTML. It controls colors, "
             "fonts, spacing, and layout."),
            ("5. CSS Selectors",
             "• Element: p { color: blue; }<br/>"
             "• Class: .card { padding: 20px; }<br/>"
             "• ID: #header { background: black; }"),
            ("6. Box Model",
             "Every element has: content, padding, border, and margin."),
            ("7. Responsive Design",
             "Use <b>@media</b> queries to adapt layout to screen size."),
        ],
    },
    "Design Thinking": {
        "title": "Design Thinking — Unit 1",
        "subtitle": "Empathise & Define",
        "sections": [
            ("1. What is Design Thinking?",
             "Design Thinking is a human-centered approach to problem-solving. It puts "
             "the user at the center of every decision, emphasizes rapid prototyping, "
             "and encourages learning from failure."),
            ("2. The 5 Stages",
             "1) Empathise<br/>2) Define<br/>3) Ideate<br/>4) Prototype<br/>5) Test"),
            ("3. Empathise",
             "Conduct user interviews, observe users in their natural environment, and "
             "build an empathy map covering what users SAY, THINK, DO, and FEEL."),
            ("4. Define",
             "Synthesize research into a clear Problem Statement. Use POV (Point of View) "
             "and HMW (How Might We) questions to frame the problem."),
            ("5. Case Study",
             "A college student wants to find study notes quickly. Instead of assuming, "
             "we interviewed 42 students and discovered that 78% waste 30+ minutes per "
             "search. This evidence drove the StudyMate solution."),
        ],
    },
    "Artificial Intelligence": {
        "title": "Artificial Intelligence — Unit 1",
        "subtitle": "Intelligent Agents & Search Algorithms",
        "sections": [
            ("1. What is AI?",
             "Artificial Intelligence is the branch of computer science that aims to "
             "build machines capable of intelligent behaviour — perception, reasoning, "
             "learning, and decision-making."),
            ("2. Types of Agents",
             "• Simple reflex agents<br/>"
             "• Model-based agents<br/>"
             "• Goal-based agents<br/>"
             "• Utility-based agents<br/>"
             "• Learning agents"),
            ("3. Search Problems",
             "A search problem is defined by: initial state, goal state, actions, "
             "transition model, and path cost."),
            ("4. Uninformed Search",
             "• Breadth-First Search (BFS) — explores level by level<br/>"
             "• Depth-First Search (DFS) — explores deepest path first<br/>"
             "• Uniform Cost Search (UCS) — expands lowest-cost node"),
            ("5. Informed Search",
             "A* search uses f(n) = g(n) + h(n), where g(n) is the cost from start and "
             "h(n) is the heuristic estimate to the goal."),
            ("6. Applications",
             "Robotics, game playing, natural language processing, self-driving cars, "
             "recommendation systems."),
        ],
    },
    "Mathematics": {
        "title": "Engineering Mathematics — Unit 1",
        "subtitle": "Matrices & Determinants",
        "sections": [
            ("1. Matrix Definition",
             "A matrix is a rectangular array of numbers arranged in rows and columns. "
             "An m×n matrix has m rows and n columns."),
            ("2. Types of Matrices",
             "• Square matrix<br/>• Diagonal matrix<br/>• Identity matrix<br/>"
             "• Symmetric matrix<br/>• Skew-symmetric matrix<br/>• Orthogonal matrix"),
            ("3. Determinant",
             "The determinant is a scalar value computed from a square matrix. "
             "For a 2×2 matrix A = [[a, b], [c, d]], det(A) = ad − bc."),
            ("4. Eigenvalues and Eigenvectors",
             "For matrix A, a vector v is an eigenvector if A·v = λ·v, where λ is the "
             "corresponding eigenvalue. To find λ, solve det(A − λI) = 0."),
            ("5. Rank of a Matrix",
             "The rank is the maximum number of linearly independent rows (or columns)."),
            ("6. Cayley-Hamilton Theorem",
             "Every square matrix satisfies its own characteristic equation."),
        ],
    },
    "Data Structures": {
        "title": "Data Structures — Unit 1",
        "subtitle": "Arrays, Linked Lists, Stacks & Queues",
        "sections": [
            ("1. What is a Data Structure?",
             "A data structure is a way of organizing and storing data so it can be "
             "accessed and modified efficiently."),
            ("2. Arrays",
             "An array is a fixed-size collection of elements of the same type stored "
             "in contiguous memory. Access is O(1), insertion/deletion is O(n)."),
            ("3. Linked Lists",
             "A linked list is a sequence of nodes where each node stores data and a "
             "pointer to the next node. Insertion and deletion are O(1) at the head, "
             "but access is O(n)."),
            ("4. Stacks",
             "A stack follows LIFO (Last In, First Out). Operations: push, pop, peek, isEmpty. "
             "Applications: expression evaluation, undo, recursion."),
            ("5. Queues",
             "A queue follows FIFO (First In, First Out). Operations: enqueue, dequeue. "
             "Applications: scheduling, BFS."),
            ("6. Time Complexity Summary",
             "Array: access O(1), search O(n), insert O(n)<br/>"
             "Linked List: access O(n), search O(n), insert O(1) at head<br/>"
             "Stack/Queue: all operations O(1)"),
        ],
    },
    "Operating Systems": {
        "title": "Operating Systems — Unit 1",
        "subtitle": "Processes & Scheduling",
        "sections": [
            ("1. What is an Operating System?",
             "An OS is system software that manages hardware, provides services to "
             "applications, and acts as an interface between the user and the computer."),
            ("2. Process vs Thread",
             "A process is a program in execution with its own memory space. A thread "
             "is a lightweight unit of execution within a process, sharing memory with "
             "other threads."),
            ("3. Process States",
             "New → Ready → Running → Waiting → Terminated"),
            ("4. CPU Scheduling Algorithms",
             "• FCFS (First-Come First-Served)<br/>"
             "• SJF (Shortest Job First)<br/>"
             "• Round Robin (time quantum)<br/>"
             "• Priority Scheduling"),
            ("5. Context Switching",
             "The process of saving the state of a running process and loading the state "
             "of another process so it can run."),
            ("6. Inter-Process Communication",
             "Shared memory and message passing are the two main IPC mechanisms."),
        ],
    },
    "Computer Networks": {
        "title": "Computer Networks — Unit 1",
        "subtitle": "OSI Model & Network Layers",
        "sections": [
            ("1. What is a Computer Network?",
             "A computer network is a set of interconnected devices that can communicate "
             "and share resources."),
            ("2. OSI Reference Model",
             "7 layers from bottom to top:<br/>"
             "1) Physical<br/>2) Data Link<br/>3) Network<br/>4) Transport<br/>"
             "5) Session<br/>6) Presentation<br/>7) Application"),
            ("3. TCP/IP Model",
             "4 layers: Network Access, Internet, Transport, Application."),
            ("4. Physical Layer",
             "Deals with transmission of raw bits over a communication channel — cables, "
             "wireless, signalling."),
            ("5. Data Link Layer",
             "Provides node-to-node data transfer. Uses MAC addresses, framing, error "
             "detection, and flow control."),
            ("6. Network Layer",
             "Handles logical addressing (IP) and routing between networks."),
            ("7. Transport Layer",
             "Provides end-to-end delivery. TCP is reliable, UDP is fast and connectionless."),
        ],
    },
}

# ---------- PDF generation ----------
def build_pdf(subject, data):
    safe = subject.replace(" ", "_").replace("&", "and")
    filename = f"{safe}_Unit1_Notes.pdf"
    path = UPLOADS / filename

    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=data["title"], author="StudyMate",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Title"],
        fontSize=22, leading=28, textColor=HexColor("#1e3a8a"),
        alignment=1, spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle", parent=styles["Normal"],
        fontSize=12, leading=16, textColor=HexColor("#475569"),
        alignment=1, spaceAfter=20, italic=True,
    )
    heading_style = ParagraphStyle(
        "HeadingStyle", parent=styles["Heading2"],
        fontSize=14, leading=18, textColor=HexColor("#4f46e5"),
        spaceBefore=14, spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyStyle", parent=styles["BodyText"],
        fontSize=10.5, leading=15, textColor=HexColor("#0f172a"),
        spaceAfter=8,
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, alignment=1, textColor=HexColor("#94a3b8"),
    )

    story = []

    # Cover block
    story.append(Paragraph("StudyMate", title_style))
    story.append(Paragraph(data["title"], ParagraphStyle(
        "Sub", parent=styles["Heading1"],
        fontSize=16, leading=20, textColor=HexColor("#0f172a"),
        alignment=1, spaceAfter=4,
    )))
    story.append(Paragraph(data["subtitle"], subtitle_style))
    story.append(Spacer(1, 0.4*cm))

    # Divider line
    story.append(Table([[""]], colWidths=[16*cm],
                       style=TableStyle([
                           ("LINEBELOW", (0,0), (-1,-1), 1.5, HexColor("#4f46e5"))
                       ])))
    story.append(Spacer(1, 0.6*cm))

    # Sections
    for heading, body in data["sections"]:
        story.append(Paragraph(heading, heading_style))
        story.append(Paragraph(body, body_style))

    # Footer
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        "© StudyMate · Educational Sample Notes · Generated for demonstration purposes",
        footer_style))

    doc.build(story)
    return filename


def link_to_db(subject, filename, data):
    db = sqlite3.connect(DB)
    cur = db.execute("SELECT id FROM resources WHERE subject=? AND unit='Unit 1' LIMIT 1",
                     (subject,))
    row = cur.fetchone()
    if row:
        db.execute("UPDATE resources SET file_path=? WHERE id=?", (filename, row[0]))
        print(f"  ✅ Linked {filename} → resource #{row[0]} ({subject})")
    else:
        print(f"  ⚠️  No matching resource found for subject '{subject}'. "
              f"Expected an entry with unit='Unit 1'.")
    db.commit()
    db.close()


def main():
    print("=" * 60)
    print("StudyMate — Real PDF Notes Generator")
    print("=" * 60)
    if not DB.exists():
        print("❌ studymate.db not found. Run `python app.py` once first.")
        return

    for subject, data in NOTES.items():
        print(f"\n📘 Generating PDF for: {subject}")
        filename = build_pdf(subject, data)
        print(f"  📄 Saved: uploads/{filename}")
        link_to_db(subject, filename, data)

    print("\n" + "=" * 60)
    print("✅ All PDFs generated and linked to the database!")
    print("   Restart `python app.py` and the Download buttons")
    print("   will serve these real PDF notes.")
    print("=" * 60)


if __name__ == "__main__":
    main()