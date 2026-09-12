"""
Regenerates resume.pdf from the structured content below. Run, review the
output, then only overwrite resume.pdf once the user has actually approved
it — this writes to resume_new.pdf by default so nothing gets clobbered
silently.

    .venv/bin/python scripts/build_resume_pdf.py
"""
import os

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem,
)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "resume_new.pdf")

NAME = "Harsh Sharma"
CONTACT = "hsharm68@asu.edu | +1 623 285 5824 | LinkedIn | GitHub"

SUMMARY = (
    "Computer Science M.S. student focused on building agentic AI systems, observability infrastructure, and "
    "ML-backed software systems, with hands-on experience across backend services, ML pipelines, and "
    "cloud-native infrastructure."
)

EDUCATION = [
    {
        "school": "Arizona State University",
        "dates": "08/2025 - 05/2027",
        "line2": "Master of Science in Computer Science — Tempe, AZ",
        "line3": "GPA: 3.89/4.00 | Coursework: Machine Learning, Artificial Intelligence, Data Mining, Deep Learning, Knowledge Representation",
    },
    {
        "school": "Netaji Subhas University of Technology (NSUT)",
        "dates": "11/2021 - 05/2025",
        "line2": "Bachelor of Engineering in Electronics and Communication Engineering — New Delhi, India",
        "line3": "GPA: 8.32/10.0 | Coursework: Data Structures, Probability, Statistics, Machine Learning, Digital Signal Processing",
    },
]

SKILLS = [
    ("Languages & Systems", "Python, C++, Go, SQL, Bash, Linux, Git"),
    ("Backend & Cloud Infrastructure", "FastAPI, REST APIs, Docker, Kubernetes, Helm, GitHub Actions, Service-Oriented Design"),
    ("Observability & Reliability", "OpenTelemetry, OpenObserve, OTLP, Distributed Tracing, Metrics, Structured Logging, Drift Monitoring"),
    ("Agentic AI & ML", "LangGraph, LLM Tool Calling, RAG, Vector Retrieval, PyTorch, TensorFlow, scikit-learn, Transformers, Anomaly Detection"),
    ("Data & Evaluation", "NumPy, Pandas, ChromaDB, PM4Py, Evaluation Pipelines, Experiment Tracking"),
]

EXPERIENCE = [
    {
        "org": "Arizona State University",
        "dates": "08/2026 - Present",
        "title": "Agentic AI Instructor & Systems Developer — Semantic Web Mining — Tempe, AZ",
        "bullets": [
            "Designed and built Agent Harness, a self-built multi-agent orchestration platform (LangGraph, "
            "FastAPI, Streamlit), from scratch as the course's hands-on teaching tool for agentic AI system "
            "design (full architecture detailed under Selected Projects).",
            "Authored course materials, architecture documentation, and cross-platform setup guides, and "
            "delivered lectures introducing students to agentic AI concepts, LangGraph orchestration, and "
            "observability.",
            "Graded student assignments and projects, providing technical feedback on agentic system design, "
            "reasoning-loop correctness, and debugging practices.",
        ],
    },
    {
        "org": "VISA Lab, Arizona State University",
        "dates": "04/2026 - 07/2026",
        "title": "Graduate Researcher – Process Mining & Agentic AI Systems — Tempe, AZ",
        "bullets": [
            "Developed a process-mining digital twin over BPIC20 event logs, exposing event, resource, process, "
            "and historical-resolution context through structured tool interfaces for evidence-grounded LLM "
            "agent analysis.",
            "Designed a LangGraph-based workflow integrating investigator, recommendation, explanation, and "
            "evaluation stages with PM4Py process models and replay-based what-if analysis for corrective-action "
            "ranking.",
        ],
    },
    {
        "org": "Sysmat Research Solutions Pvt. Ltd. | Remote",
        "dates": "06/2024 - 08/2024",
        "title": "Machine Learning Engineer Intern – ML Infrastructure & Signal Pipelines",
        "bullets": [
            "Built modular Python pipelines for preprocessing 64-channel EEG datasets and implemented dynamic "
            "neural-graph generation with spatio-temporal GCN-GRU workflows for multichannel classification, "
            "improving validation accuracy by 9%.",
            "Orchestrated preprocessing, model-input generation, evaluation, and structured logging through "
            "reusable workflows, reducing experimentation and handoff time by 40%.",
        ],
    },
    {
        "org": "Bow Creek Financial | Remote",
        "dates": "06/2023 - 08/2023",
        "title": "Machine Learning Engineer Intern – Time-Series & Anomaly Detection",
        "bullets": [
            "Implemented Python pipelines for financial time-series ingestion and feature engineering, "
            "integrating ARIMA and autoencoder models with automated threshold tuning, improving rare-event "
            "recall by 22%.",
            "Built reproducible training, inference, and evaluation workflows with Docker, structured metric "
            "logging, and reusable experiment artifacts.",
        ],
    },
]

PROJECTS = [
    {
        "name": "Agent Harness – Modular Multi-Agent Orchestration System",
        "bullets": [
            "Built a modular multi-agent orchestration harness with LangGraph, FastAPI, and Streamlit, featuring "
            "a Base Orchestrator that routes requests to specialized agents through isolated private execution "
            "graphs.",
            "Designed a Text2SQL agent with bounded schema discovery, deterministic SQL safety validation, and "
            "iterative multi-loop reasoning, using structured Pydantic outputs and LangSmith tracing for full "
            "observability.",
            "Containerized the system with Docker Compose and authored cross-platform setup scripts for "
            "reproducible deployment.",
        ],
    },
    {
        "name": "RepoScope – Repository-Aware Code Analysis and Review System",
        "bullets": [
            "Built a repository-aware AI backend that indexes source code into a persistent vector database and "
            "retrieves relevant cross-file context for LLM-based code review, using semantic chunking, bounded "
            "context expansion, and FastAPI services separating indexing, retrieval, and generation.",
        ],
    },
]


def build():
    styles = {
        "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=16, leading=19, alignment=TA_CENTER, spaceAfter=2),
        "contact": ParagraphStyle("contact", fontName="Helvetica", fontSize=9, leading=11, alignment=TA_CENTER, spaceBefore=1, spaceAfter=5),
        "section": ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=10.8, spaceBefore=3, spaceAfter=1),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.2, alignment=TA_JUSTIFY, leading=10.8),
        "entry_title": ParagraphStyle("entry_title", fontName="Helvetica-Bold", fontSize=9.7, leading=11.5),
        "entry_dates": ParagraphStyle("entry_dates", fontName="Helvetica-Bold", fontSize=9.7, alignment=2, leading=11.5),
        "entry_sub": ParagraphStyle("entry_sub", fontName="Helvetica-Oblique", fontSize=9.2, leading=10.8, spaceAfter=1),
        "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.2, leading=10.8),
        "skill_line": ParagraphStyle("skill_line", fontName="Helvetica", fontSize=9.2, leading=11, spaceAfter=1),
    }

    doc = SimpleDocTemplate(
        OUTPUT_PATH, pagesize=LETTER,
        topMargin=0.3 * inch, bottomMargin=0.3 * inch,
        leftMargin=0.5 * inch, rightMargin=0.5 * inch,
    )
    story = []

    def section_header(title):
        story.append(Paragraph(title, styles["section"]))
        story.append(HRFlowable(width="100%", thickness=0.75, color="#000000", spaceAfter=2))

    def bullets(items):
        story.append(ListFlowable(
            [ListItem(Paragraph(b, styles["bullet"]), leftIndent=0, spaceAfter=1) for b in items],
            bulletType="bullet", start="•", leftIndent=13, bulletFontSize=7.5,
        ))

    story.append(Paragraph(NAME, styles["name"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(CONTACT, styles["contact"]))

    section_header("Professional Summary")
    story.append(Paragraph(SUMMARY, styles["body"]))

    section_header("Education")
    for e in EDUCATION:
        story.append(Paragraph(f"<b>{e['school']}</b>  {e['dates']}", styles["entry_title"]))
        story.append(Paragraph(f"<i>{e['line2']}</i>", styles["entry_sub"]))
        story.append(Paragraph(e["line3"], styles["entry_sub"]))

    section_header("Technical Skills")
    for label, values in SKILLS:
        story.append(Paragraph(f"<b>{label}:</b> {values}", styles["skill_line"]))

    section_header("Experience")
    for job in EXPERIENCE:
        story.append(Paragraph(f"<b>{job['org']}</b>  {job['dates']}", styles["entry_title"]))
        story.append(Paragraph(f"<i>{job['title']}</i>", styles["entry_sub"]))
        bullets(job["bullets"])
        story.append(Spacer(1, 2))

    section_header("Selected Projects")
    for p in PROJECTS:
        story.append(Paragraph(f"<b>{p['name']}</b>", styles["entry_title"]))
        bullets(p["bullets"])
        story.append(Spacer(1, 2))

    doc.build(story)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
