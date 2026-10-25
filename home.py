"""Streamlit UI for the one-click TrainMind Trainer Copilot."""

from __future__ import annotations

import hashlib
import html
import os
import re
import tempfile
from pathlib import Path
from typing import Callable

import streamlit as st
from dotenv import load_dotenv

from app.exporters import EXPORT_VERSION, build_exports
from app.package_generator import generate_training_package
from app.ingestion.chunker import chunk_documents
from app.ingestion.loaders import load_pdf
from app.rag.embeddings import create_embeddings
from app.rag.vector_store import (
    add_chunks,
    delete_indexed_source,
    list_indexed_source_details,
    source_is_indexed,
)

load_dotenv()

st.set_page_config(
    page_title="TrainMind | ITI Trainer Copilot",
    page_icon="🎓",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --ink:#202b47; --muted:#74809a; --blue:#5269e8; --teal:#188c80; --line:#e9edf5; }
.stApp { background:#f6f7fb; color:var(--ink); }
.block-container { max-width:1120px; padding-top:2.2rem; padding-bottom:4rem; }
h1,h2,h3 { font-family:'Manrope',sans-serif; letter-spacing:-.035em; color:var(--ink); }
p, label, [data-testid="stMarkdownContainer"] { font-family:'DM Sans',sans-serif; }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color:var(--ink); }
.home-head { background:linear-gradient(110deg,#fff 0%,#fff 65%,#f0f4ff 100%); border:1px solid var(--line); border-left:5px solid #5269e8; border-radius:20px; padding:1.65rem 2rem; margin:0 0 1.1rem; box-shadow:0 9px 28px rgba(31,48,87,.055); }
.home-eyebrow { color:#5269e8; font-size:.72rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; margin-bottom:.55rem; }
.home-head h1 { font-size:2.15rem; line-height:1.2; margin:0 0 .45rem; }
.home-head p { color:#74809a; font-size:1rem; line-height:1.65; margin:0; max-width:750px; }
.home-head .spark { color:#ed9d45; }
.workflow { display:grid; grid-template-columns:repeat(3,1fr); gap:.8rem; margin:1.1rem 0 1.5rem; }
.workflow-item { background:#fff; border:1px solid var(--line); border-radius:15px; padding:.9rem 1rem; display:flex; gap:.8rem; align-items:center; box-shadow:0 4px 14px rgba(31,48,87,.025); transition:transform .18s ease, box-shadow .18s ease; }
.workflow-item:hover { transform:translateY(-2px); box-shadow:0 8px 20px rgba(31,48,87,.08); }
.workflow-num { width:34px; height:34px; flex:0 0 34px; border-radius:11px; display:flex; align-items:center; justify-content:center; background:#eef0ff; color:#5269e8; font-weight:800; }
.workflow-item:nth-child(2) .workflow-num { background:#e4f6f2; color:#188c80; }
.workflow-item:nth-child(3) .workflow-num { background:#fff2e1; color:#c77c20; }
.workflow-label { color:#28334d; font-weight:700; font-size:.92rem; }
.workflow-caption { color:#8a94a8; font-size:.78rem; margin-top:.12rem; }
.section-title { font-family:'Manrope',sans-serif; font-size:1.17rem; font-weight:800; color:#202b47; margin:.2rem 0 .25rem; }
.section-note { color:#7d879c; font-size:.9rem; margin:0 0 1rem; }
.step { display:inline-flex; align-items:center; justify-content:center; width:27px; height:27px; margin-right:.5rem; border-radius:9px; background:#eef0ff; color:#5269e8; font:800 .82rem 'DM Sans',sans-serif; vertical-align:middle; }
div[data-testid="stVerticalBlockBorderWrapper"] { background:#fff; border:1px solid var(--line); border-radius:18px; box-shadow:0 5px 20px rgba(31,48,87,.035); padding:.35rem .45rem; }
div[data-testid="stFileUploader"] { margin-top:.35rem; }
div[data-testid="stFileUploader"] section { min-height:150px; }
div[data-testid="stFileUploader"] section > button { border-radius:9px; }
div[data-testid="stTextInput"] label { font-weight:700; color:#35415d; }
div[data-testid="stFileUploader"] section { background:#fbfcff; border:1px dashed #b9c3e3; border-radius:14px; }
div[data-testid="stTextInput"] input { border-radius:11px; min-height:3rem; background:#fbfcff; }
.stButton>button, div[data-testid="stDownloadButton"] button { border-radius:11px; font-weight:700; min-height:2.8rem; }
div[role="radiogroup"] label { border:1px solid #e5e9f3; border-radius:12px; padding:.55rem .85rem; background:#fff; }
div[role="radiogroup"] label:has(input:checked) { border-color:#5269e8; background:#f0f2ff; }
div[data-testid="stDownloadButton"] button[kind="primary"] { background:#5269e8; border:0; box-shadow:0 6px 16px rgba(82,105,232,.2); }
.stButton>button[kind="primary"] { background:#5269e8; border:0; box-shadow:0 5px 14px rgba(82,105,232,.2); }
.stButton>button[kind="primary"]:hover { background:#4058d5; }
div[data-testid="stDownloadButton"] button[kind="primary"] { background:#5269e8; border:0; box-shadow:0 6px 16px rgba(82,105,232,.2); }
div[data-testid="stDownloadButton"] button { min-height:2.75rem; border:1px solid #dce2f0; transition:all .18s ease; }
div[data-testid="stDownloadButton"] button:hover { border-color:#5269e8; color:#4058d5; background:#f1f3ff; transform:translateY(-1px); }
div[role="radiogroup"] label { border:1px solid #e5e9f3; border-radius:12px; padding:.55rem .85rem; background:#fff; }
div[role="radiogroup"] label:has(input:checked) { border-color:#5269e8; background:#f0f2ff; }
div[data-testid="stTabs"] button { font-weight:700; }
div[data-testid="stTabs"] [role="tablist"] { gap:.35rem; border-bottom:1px solid #e8ecf5; }
div[data-testid="stTabs"] [role="tab"] { border-radius:10px 10px 0 0; padding:.65rem 1rem; color:#7b859b; }
div[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color:#5269e8; background:#eef0ff; }
.artifact-label { display:inline-flex; align-items:center; gap:.45rem; padding:.38rem .72rem; margin:.15rem 0 .8rem; border-radius:999px; background:#eef0ff; color:#5269e8; font:700 .78rem 'DM Sans',sans-serif; }
.artifact-content { color:#33405c; line-height:1.75; }
.artifact-content h1,.artifact-content h2,.artifact-content h3 { color:#263452; margin-top:1rem; }
div[data-testid="stExpander"] { background:white; border-radius:13px; border:1px solid var(--line); }
div[data-testid="stAlert"] { border-radius:12px; }
@media (max-width:700px) { .workflow { grid-template-columns:1fr; } .home-head { padding:1.35rem; } .home-head h1 { font-size:1.8rem; } }
</style>
""", unsafe_allow_html=True)


def render_quiz(quiz_text: str) -> None:
    """Render generated multiple-choice questions as readable cards."""
    question_matches = list(re.finditer(r"(?m)^###\s*Question\s+(\d+)\s*$", quiz_text))
    if not question_matches:
        st.markdown(quiz_text)
        return

    for index, match in enumerate(question_matches):
        end = question_matches[index + 1].start() if index + 1 < len(question_matches) else len(quiz_text)
        lines = quiz_text[match.end():end].strip().splitlines()
        question_lines: list[str] = []
        options: list[tuple[str, str]] = []
        answer_lines: list[str] = []
        explanation_lines: list[str] = []
        evidence_lines: list[str] = []
        section = "question"

        for line in lines:
            option_match = re.match(r"^\s*([A-D])\)\s*(.+)$", line)
            label_match = re.match(r"^\s*\*{0,2}(Correct answer|Explanation|Curriculum evidence):\*{0,2}\s*(.*)$", line, re.I)
            if label_match:
                label = label_match.group(1).lower()
                section = {"correct answer": "answer", "explanation": "explanation", "curriculum evidence": "evidence"}[label]
                value = label_match.group(2).strip()
                if value:
                    {"answer": answer_lines, "explanation": explanation_lines, "evidence": evidence_lines}[section].append(value)
            elif option_match:
                section = "options"
                options.append((option_match.group(1), option_match.group(2).strip()))
            elif section == "question":
                question_lines.append(line)
            elif section == "answer":
                answer_lines.append(line)
            elif section == "explanation":
                explanation_lines.append(line)
            elif section == "evidence":
                evidence_lines.append(line)

        with st.container(border=True):
            st.markdown(f"#### Question {match.group(1)}")
            prompt = "\n".join(question_lines).strip()
            if prompt:
                st.markdown(prompt)

            if options:
                option_columns = st.columns(2)
                for option_index, (letter, option_text) in enumerate(options):
                    with option_columns[option_index % 2]:
                        st.markdown(f"**{letter})** {option_text}")

            if answer_lines or explanation_lines:
                with st.expander("✅ Correct answer & explanation"):
                    if answer_lines:
                        st.markdown("**Correct answer:** " + "\n".join(answer_lines).strip())
                    if explanation_lines:
                        st.markdown("\n".join(explanation_lines).strip())
            if evidence_lines:
                with st.expander("📚 Curriculum evidence"):
                    render_curriculum_evidence("\n".join(evidence_lines).strip())


def render_exercise(exercise_text: str) -> None:
    """Render a generated exercise as labeled sections with clean step numbering."""
    heading_matches = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", exercise_text))
    if not heading_matches:
        st.markdown(exercise_text)
        return

    sections: list[tuple[str, str]] = []
    for index, match in enumerate(heading_matches):
        end = heading_matches[index + 1].start() if index + 1 < len(heading_matches) else len(exercise_text)
        sections.append((match.group(1).strip(), exercise_text[match.end():end].strip()))

    section_map = {name.lower(): value for name, value in sections}
    title = section_map.pop("exercise title", "")
    estimated_time = section_map.pop("estimated time", "")
    prerequisites = section_map.pop("prerequisites", "")
    if title:
        st.markdown(f"### {title}")

    metadata = [(label, value) for label, value in (("⏱️ Estimated time", estimated_time), ("📌 Prerequisites", prerequisites)) if value]
    if metadata:
        columns = st.columns(len(metadata))
        for column, (label, value) in zip(columns, metadata):
            with column:
                with st.container(border=True):
                    st.caption(label)
                    st.markdown(value)

    order = ["objective", "task", "steps", "expected outcome", "hints", "common mistakes", "assessment criteria", "curriculum support note"]
    icons = {"objective": "🎯", "task": "📝", "steps": "🪜", "expected outcome": "✅", "hints": "💡", "common mistakes": "⚠️", "assessment criteria": "📋", "curriculum support note": "📚"}
    for key in order:
        content = section_map.pop(key, None)
        if not content:
            continue
        with st.container(border=True):
            st.markdown(f"#### {icons[key]} {key.title()}")
            if key == "steps":
                cleaned_steps: list[str] = []
                for line in content.splitlines():
                    stripped = line.strip()
                    if not stripped or stripped == "-" or re.fullmatch(r"\d+[.)]", stripped):
                        continue
                    item = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
                    cleaned_steps.append(f"{len(cleaned_steps) + 1}. {item.group(1)}" if item else line)
                st.markdown("\n".join(cleaned_steps))
            else:
                st.markdown(content)

    for name, content in sections:
        if name.lower() not in {"exercise title", "estimated time", "prerequisites", "objective", "task", "steps", "expected outcome", "hints", "common mistakes", "assessment criteria", "curriculum support note", "retrieved curriculum sources"} and content:
            with st.container(border=True):
                st.markdown(f"#### {name}")
                st.markdown(content)

    source_section = next(
        (content for name, content in sections if name.lower() == "retrieved curriculum sources"),
        "",
    )
    if source_section:
        with st.expander("📚 Curriculum evidence"):
            render_curriculum_evidence(source_section)


def render_session_plan(plan_text: str) -> None:
    """Render session objectives and timed agenda as scannable teaching cards."""
    headings = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", plan_text))
    if not headings:
        st.markdown(plan_text)
        return

    sections: list[tuple[str, str]] = []
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(plan_text)
        sections.append((match.group(1).strip(), plan_text[match.end():end].strip()))

    section_order = ["Learning Objectives", "90-Minute Session Schedule", "Expected Learning Outcome", "Curriculum Support Note"]
    consumed: set[str] = set()
    for title in section_order:
        section = next(((name, body) for name, body in sections if name.lower() == title.lower()), None)
        if not section:
            continue
        _, body = section
        consumed.add(title.lower())

        if title == "90-Minute Session Schedule":
            time_blocks = list(re.finditer(r"(?m)^###\s*(\d+)\s*[-–]\s*(\d+)\s*(?:min|minutes)\s*:\s*(.+?)\s*$", body, re.I))
            if not time_blocks:
                with st.container(border=True):
                    st.markdown(f"#### 🗓️ {title}")
                    st.markdown(body)
                continue

            for index, block in enumerate(time_blocks):
                end = time_blocks[index + 1].start() if index + 1 < len(time_blocks) else len(body)
                block_body = body[block.end():end].strip()
                labels = {}
                label_matches = list(re.finditer(r"(?m)^\*\*(Trainer actions|Learner actions|Materials from curriculum):\*\*\s*", block_body, re.I))
                for label_index, label_match in enumerate(label_matches):
                    value_end = label_matches[label_index + 1].start() if label_index + 1 < len(label_matches) else len(block_body)
                    labels[label_match.group(1).lower()] = block_body[label_match.end():value_end].strip()

                with st.container(border=True):
                    st.markdown(f"#### ⏱️ {block.group(1)}–{block.group(2)} min · {block.group(3).strip()}")
                    action_columns = st.columns(2)
                    for column, key, label in zip(action_columns, ("trainer actions", "learner actions"), ("🎙️ Trainer", "👥 Learners")):
                        with column:
                            st.markdown(f"**{label}**")
                            st.markdown(labels.get(key, "—"))
                    if labels.get("materials from curriculum"):
                        st.caption("📎 Materials: " + labels["materials from curriculum"])
        else:
            icon = "🎯" if title == "Learning Objectives" else "🏁" if title == "Expected Learning Outcome" else "📚"
            with st.container(border=True):
                st.markdown(f"#### {icon} {title}")
                st.markdown(body)

    for name, body in sections:
        if name.lower() not in consumed and name.lower() != "retrieved curriculum sources" and body:
            with st.container(border=True):
                st.markdown(f"#### {name}")
                st.markdown(body)

    source_section = next(
        (body for name, body in sections if name.lower() == "retrieved curriculum sources"),
        "",
    )
    if source_section:
        with st.expander("📚 Curriculum evidence"):
            render_curriculum_evidence(source_section)


def index_pdf_bytes(
    filename: str,
    content: bytes,
    progress_callback: Callable[[str], None] | None = None,
) -> tuple[int, int, bool]:
    """Index an uploaded PDF only when its content hash is not already stored."""
    file_hash = hashlib.sha256(content).hexdigest()
    if source_is_indexed(Path(filename).name, file_hash):
        return 0, 0, False

    temp_path = None
    try:
        if progress_callback:
            progress_callback("Extracting text from the PDF...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        pages = load_pdf(temp_path)
        if not pages:
            raise ValueError("No readable text was found in this PDF. Scanned PDFs may need OCR first.")

        source_name = Path(filename).name
        for page in pages:
            page["metadata"]["source"] = source_name
            page["metadata"]["file_hash"] = file_hash

        if progress_callback:
            progress_callback(f"Extracted {len(pages)} pages. Splitting the content...")
        chunks = chunk_documents(pages)
        if not chunks:
            raise ValueError("No text chunks were created from this PDF.")

        if progress_callback:
            progress_callback(f"Created {len(chunks)} chunks. Creating embeddings and indexing...")
        embeddings = create_embeddings([chunk["text"] for chunk in chunks])
        for chunk in chunks:
            chunk["metadata"]["file_hash"] = file_hash
        add_chunks(chunks, embeddings)
        if progress_callback:
            progress_callback(f"Indexed {len(pages)} pages into {len(chunks)} chunks.")
        return len(pages), len(chunks), True
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def render_copy_button(text: str, label: str, key: str) -> None:
    """Render a browser clipboard button with a manual-copy fallback."""
    safe_text = html.escape(text, quote=False)
    copy_id = re.sub(r"[^a-zA-Z0-9_-]", "_", key)
    st.html(
        f"""
        <div id="{copy_id}-root">
          <textarea id="{copy_id}-source" readonly>{safe_text}</textarea>
          <button id="{copy_id}-button" type="button">📋 {html.escape(label)}</button>
          <span id="{copy_id}-status" role="status"></span>
        </div>
        <style>
          #{copy_id}-root {{ font-family: sans-serif; }}
          #{copy_id}-source {{ display: none; width: 100%; height: 100px; box-sizing: border-box; }}
          #{copy_id}-button {{ min-height: 42px; width: 100%; padding: 8px 12px; border: 1px solid #d7ddeb; border-radius: 11px; background: white; color: #202b47; font-size: 14px; font-weight: 700; cursor: pointer; }}
          #{copy_id}-status {{ display: block; color: #188c80; font-size: 12px; padding-top: 3px; }}
        </style>
        <script>
          (() => {{
            const root = document.getElementById("{copy_id}-root");
            const button = root.querySelector("button");
            const source = root.querySelector("textarea");
            const status = root.querySelector("[role='status']");
            button.addEventListener("click", async () => {{
              try {{
                await navigator.clipboard.writeText(source.value);
                status.textContent = "Copied to clipboard.";
              }} catch (error) {{
                source.style.display = "block";
                source.select();
                const copied = document.execCommand("copy");
                status.textContent = copied
                  ? "Copied to clipboard."
                  : "Clipboard unavailable. Select the text above and copy it.";
              }}
            }});
          }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def render_curriculum_evidence(evidence_text: str) -> None:
    """Render source and page citations as separate, readable reference cards."""
    page_matches = list(
        re.finditer(
            r"(?:(?P<source>[^;]*?\.pdf)\s*,\s*)?Page\s+(?P<page>\d+)"
            r"(?:\s*,\s*Question\s+(?P<question>\d+))?",
            evidence_text,
            re.IGNORECASE,
        )
    )
    if not page_matches:
        st.markdown(evidence_text)
        return

    current_source = ""
    prefix = evidence_text[:page_matches[0].start()].strip(" ;,.\n-*")
    if prefix:
        st.markdown(prefix)

    for index, match in enumerate(page_matches):
        if match.group("source"):
            current_source = match.group("source").strip()
        next_start = page_matches[index + 1].start() if index + 1 < len(page_matches) else len(evidence_text)
        excerpt = evidence_text[match.end():next_start].strip(" ;,.\n")

        with st.container(border=True):
            source_column, page_column = st.columns([4, 1])
            with source_column:
                st.write(f"📄 {current_source or 'Curriculum source'}")
            with page_column:
                st.caption(f"Page {match.group('page')}")
            if match.group("question"):
                st.caption(f"Related question: {match.group('question')}")
            if excerpt:
                st.markdown(f"> {excerpt}")


st.markdown("""
<div class="home-head">
  <div class="home-eyebrow">ITI · Trainer Copilot</div>
  <h1>Build a better class with <span class="spark">TrainMind</span></h1>
  <p>Upload your curriculum, choose a topic, and get a complete teaching package—quizzes, practical exercises, and a timed session plan for three learner levels.</p>
</div>
<div class="workflow">
  <div class="workflow-item"><div class="workflow-num">01</div><div><div class="workflow-label">Add your curriculum</div><div class="workflow-caption">PDF files, indexed once</div></div></div>
  <div class="workflow-item"><div class="workflow-num">02</div><div><div class="workflow-label">Choose a topic</div><div class="workflow-caption">Grounded in your materials</div></div></div>
  <div class="workflow-item"><div class="workflow-num">03</div><div><div class="workflow-label">Teach and share</div><div class="workflow-caption">Download in 3 formats</div></div></div>
</div>
""", unsafe_allow_html=True)

if not os.getenv("GEMINI_API_KEY", "").strip():
    st.warning("Add GEMINI_API_KEY to your local .env file before generating a package.")

with st.container(border=True):
    st.markdown('<div class="section-title"><span class="step">1</span>Your curriculum library</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-note">Upload PDFs to extract and index them. Uploading a newer PDF with the same name replaces the indexed version after processing succeeds.</div>', unsafe_allow_html=True)
    upload_key_version = st.session_state.get("trainmind_upload_key_version", 0)
    uploads = st.file_uploader(
        "Choose one or more curriculum PDFs. New or changed files are indexed automatically.",
        type=["pdf"],
        accept_multiple_files=True,
        help="Previously indexed files remain in the local ChromaDB index.",
        key=f"curriculum_upload_{upload_key_version}",
    )

    if uploads:
        for uploaded in uploads:
            status = None
            try:
                file_bytes = uploaded.getvalue()
                file_hash = hashlib.sha256(file_bytes).hexdigest()
                if source_is_indexed(Path(uploaded.name).name, file_hash):
                    st.caption(f"✓ {uploaded.name} · Indexed · unchanged")
                    continue

                with st.status(f"Processing {uploaded.name}...", expanded=True) as status:
                    def report_index_progress(message: str) -> None:
                        status.update(label=f"{uploaded.name}: {message}", state="running")

                    pages_count, chunks_count, indexed = index_pdf_bytes(
                        uploaded.name,
                        file_bytes,
                        progress_callback=report_index_progress,
                    )
                    status.update(
                        label=f"{uploaded.name}: {pages_count} pages · {chunks_count} chunks · Indexed",
                        state="complete",
                        expanded=False,
                    )
                if indexed:
                    st.success(f"{uploaded.name} was indexed successfully.")
            except Exception as exc:
                if status:
                    status.update(label=f"{uploaded.name}: indexing failed", state="error")
                st.error(f"Could not index {uploaded.name}: {exc}")

    sources = list_indexed_source_details()
    if sources:
        st.markdown(f"**Indexed curriculum · {len(sources)} file(s)**")
        for source in sources:
            name_column, status_column, action_column = st.columns([5, 3, 1])
            with name_column:
                st.write(f"📄 {source['source']}")
            with status_column:
                st.caption(f"✓ Indexed · {source['pages']} pages · {source['chunks']} chunks")
            with action_column:
                if st.button(
                    "Remove",
                    key=f"remove_curriculum_{hashlib.sha256(source['source'].encode()).hexdigest()[:12]}",
                    help=f"Remove {source['source']} from the curriculum index",
                ):
                    delete_indexed_source(source["source"])
                    st.session_state["trainmind_upload_key_version"] = upload_key_version + 1
                    st.rerun()
    else:
        st.info("Upload a text-based PDF to begin. Indexed files are kept in the local ChromaDB database.")

with st.container(border=True):
    st.markdown('<div class="section-title"><span class="step">2</span>Create your training package</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-note">One topic generates a quiz, hands-on exercise, and 90-minute session plan for each level.</div>', unsafe_allow_html=True)
    topic = st.text_input(
        "Training topic",
        placeholder="Example: Retrieval-Augmented Generation (RAG)",
        help="TrainMind will generate a quiz, exercise, and 90-minute session plan for each of the three levels.",
    )

    if not sources:
        st.caption("Upload and index a curriculum PDF to enable package generation.")
    elif not topic.strip():
        st.caption("Enter a training topic to enable package generation.")

    if st.button(
        "✨ Generate Package",
        type="primary",
        use_container_width=True,
        disabled=not bool(sources) or not topic.strip(),
    ):
        st.session_state.pop("trainmind_package", None)
        st.session_state.pop("trainmind_exports", None)
        progress = st.progress(5, text="Starting package generation...")
        status = None
        try:
            with st.status(
                "Generating nine curriculum-grounded artifacts...",
                expanded=True,
            ) as status:
                status.write("Creating a Quiz, Exercise, and Session Plan for Beginner, Intermediate, and Advanced levels.")
                progress.progress(15, text="Generating the three learning levels...")
                package = generate_training_package(topic.strip())
                progress.progress(75, text="Building the complete package...")
                status.update(label="All nine artifacts are ready. Preparing downloads...", state="running")
                exports = build_exports(package)
                progress.progress(100, text="Your package is ready.")
                status.update(label="Training package generated successfully.", state="complete", expanded=False)
            st.session_state["trainmind_package"] = package
            st.session_state["trainmind_exports"] = exports
            st.success("Training package generated and all three export formats are ready.")
        except Exception as exc:
            if status:
                status.update(label="Package generation failed.", state="error")
            progress.empty()
            st.error(f"Package generation failed: {exc}")
            st.caption("Check your Gemini API key and connection, then try a topic covered by the indexed curriculum.")

package = st.session_state.get("trainmind_package")
exports = st.session_state.get("trainmind_exports")
if package and exports:
    if exports.get("version") != EXPORT_VERSION:
        with st.spinner("Updating your downloads to the latest professional design..."):
            exports = build_exports(package)
            st.session_state["trainmind_exports"] = exports

    st.divider()
    st.markdown(f'<div class="section-title">📦 Your training package · {package["topic"]}</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-note">Generated from retrieved curriculum passages, with session timing checked to exactly 90 minutes.</div>', unsafe_allow_html=True)

    level_tabs = st.tabs(["Beginner", "Intermediate", "Advanced"])
    for tab, level in zip(level_tabs, ("beginner", "intermediate", "advanced")):
        with tab:
            artifact_tabs = st.tabs(["Quiz", "Exercise", "90-Minute Session Plan"])
            artifact_names = {
                "quiz": ("🧠", "Knowledge check"),
                "exercise": ("🛠️", "Hands-on practice"),
                "session_plan": ("🕒", "90-minute session plan"),
            }
            for artifact_tab, artifact in zip(artifact_tabs, ("quiz", "exercise", "session_plan")):
                with artifact_tab:
                    icon, artifact_name = artifact_names[artifact]
                    with st.container(border=True):
                        st.markdown(
                            f'<div class="artifact-label">{icon} {level.title()} · {artifact_name}</div>',
                            unsafe_allow_html=True,
                        )
                        artifact_text = package["levels"][level][artifact]
                        if artifact == "quiz":
                            render_quiz(artifact_text)
                        elif artifact == "exercise":
                            render_exercise(artifact_text)
                        elif artifact == "session_plan":
                            render_session_plan(artifact_text)
                        else:
                            st.markdown(artifact_text)
                        if artifact == "session_plan":
                            validation = package["levels"][level]["timing_validation"]
                            if validation["valid"] and validation["total_minutes"] == 90:
                                st.success("Timing validated: 0–90 minutes, no gaps or overlaps.")
                            else:
                                st.error("Session timing validation failed.")
                        copy_column, pdf_column, ppt_column, word_column = st.columns([1.3, 1, 1, 1])
                        with copy_column:
                            render_copy_button(
                                artifact_text,
                                "Copy",
                                f"{level}_{artifact}",
                            )
                        artifact_exports = exports["artifacts"][level][artifact]
                        format_buttons = (
                            (pdf_column, "📄 PDF", "pdf", "application/pdf", "pdf"),
                            (ppt_column, "📊 PowerPoint", "pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "pptx"),
                            (word_column, "📝 Word", "docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"),
                        )
                        for column, label, export_key, mime_type, extension in format_buttons:
                            with column:
                                st.download_button(
                                    label,
                                    data=artifact_exports[export_key],
                                    file_name=f"trainmind_{level}_{artifact}.{extension}",
                                    mime=mime_type,
                                    key=f"download_{level}_{artifact}_{extension}",
                                    on_click="ignore",
                                    use_container_width=True,
                                )

    st.markdown("### 📚 Curriculum sources")
    source_pages: dict[str, set[int]] = {}
    for source in package.get("sources", []):
        source_pages.setdefault(source["source"], set()).add(source["page"])

    if source_pages:
        source_columns = st.columns(min(2, len(source_pages)))
        for index, (source_name, pages) in enumerate(source_pages.items()):
            with source_columns[index % len(source_columns)]:
                with st.container(border=True):
                    st.markdown(f"**📄 `{source_name}`**")
                    page_list = ", ".join(str(page) for page in sorted(pages))
                    st.caption(f"Referenced pages: {page_list}")
    else:
        st.info("No source metadata was returned.")

    st.markdown("### 📥 Download your package")
    st.caption("Choose the format that works best for you.")
    export_options = {
        "📕 PDF": ("pdf", "trainmind_training_package.pdf", "application/pdf", "Best for sharing and printing."),
        "📝 Word": ("docx", "trainmind_training_package.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "Best for editing the written materials."),
        "📊 PowerPoint": ("pptx", "trainmind_training_package.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "Best for presenting in class."),
    }
    selected_format = st.radio(
        "File format",
        list(export_options),
        horizontal=True,
        label_visibility="collapsed",
        key="trainmind_export_format",
    )
    export_key, filename, mime_type, format_hint = export_options[selected_format]
    st.caption(format_hint)
    st.download_button(
        f"Download {selected_format}",
        data=exports[export_key],
        file_name=filename,
        mime=mime_type,
        on_click="ignore",
        use_container_width=True,
        type="primary",
    )
