"""Export a generated TrainMind package to DOCX, PDF, and PPTX."""

from __future__ import annotations

import io
import re
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from pptx import Presentation
from pptx.util import Inches as PptInches, Pt as PptPt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether

LEVEL_TITLES = {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced"}
ARTIFACT_TITLES = {"quiz": "Quiz", "exercise": "Exercise", "session_plan": "90-Minute Session Plan"}


def _all_artifacts(package: dict):
    for level in ("beginner", "intermediate", "advanced"):
        data = package["levels"][level]
        for kind in ("quiz", "exercise", "session_plan"):
            yield level, kind, data[kind]


def _plain_markdown(line: str) -> str:
    line = re.sub(r"^\s*[-*]\s+", "• ", line)
    line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
    line = re.sub(r"`([^`]*)`", r"\1", line)
    return line.strip()


def export_docx(package: dict) -> bytes:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)

    title = doc.add_heading("TrainMind – ITI Trainer Copilot", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle = doc.add_paragraph(f"Training Package: {package['topic']}")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Generated from the uploaded curriculum evidence.")
    doc.add_page_break()

    for index, (level, kind, content) in enumerate(_all_artifacts(package)):
        doc.add_heading(f"{LEVEL_TITLES[level]} — {ARTIFACT_TITLES[kind]}", level=1)
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("### "):
                doc.add_heading(_plain_markdown(stripped[4:]), level=3)
            elif stripped.startswith("## "):
                doc.add_heading(_plain_markdown(stripped[3:]), level=2)
            elif stripped.startswith("# "):
                doc.add_heading(_plain_markdown(stripped[2:]), level=1)
            elif stripped.startswith("- ") or stripped.startswith("* "):
                doc.add_paragraph(_plain_markdown(stripped), style="List Bullet")
            else:
                doc.add_paragraph(_plain_markdown(stripped))
        if index < 8:
            doc.add_page_break()

    output = io.BytesIO()
    doc.save(output)
    return output.getvalue()


def export_pdf(package: dict) -> bytes:
    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=17 * mm, bottomMargin=17 * mm,
        title=f"TrainMind Training Package - {package['topic']}",
    )
    base = getSampleStyleSheet()
    title_style = ParagraphStyle("CoverTitle", parent=base["Title"], alignment=TA_CENTER, spaceAfter=12)
    subtitle_style = ParagraphStyle("CoverSubtitle", parent=base["Normal"], alignment=TA_CENTER, spaceAfter=8)
    h1 = ParagraphStyle("PackageH1", parent=base["Heading1"], spaceBefore=10, spaceAfter=6)
    h2 = ParagraphStyle("PackageH2", parent=base["Heading2"], spaceBefore=8, spaceAfter=4)
    body = ParagraphStyle("PackageBody", parent=base["BodyText"], leading=13, spaceAfter=5, wordWrap="CJK")
    story = [Spacer(1, 45 * mm), Paragraph("TrainMind – ITI Trainer Copilot", title_style),
             Paragraph(f"Training Package: {escape(package['topic'])}", subtitle_style),
             Paragraph("Generated from uploaded curriculum evidence", subtitle_style), PageBreak()]

    for index, (level, kind, content) in enumerate(_all_artifacts(package)):
        story.append(Paragraph(escape(f"{LEVEL_TITLES[level]} — {ARTIFACT_TITLES[kind]}"), h1))
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped:
                story.append(Spacer(1, 2))
                continue
            if stripped.startswith("### "):
                story.append(Paragraph(escape(_plain_markdown(stripped[4:])), h2))
            elif stripped.startswith("## "):
                story.append(Paragraph(escape(_plain_markdown(stripped[3:])), h2))
            elif stripped.startswith("# "):
                story.append(Paragraph(escape(_plain_markdown(stripped[2:])), h1))
            else:
                story.append(Paragraph(escape(_plain_markdown(stripped)), body))
        if index < 8:
            story.append(PageBreak())

    doc.build(story)
    return output.getvalue()


def export_pptx(package: dict) -> bytes:
    prs = Presentation()
    prs.slide_width = PptInches(13.333)
    prs.slide_height = PptInches(7.5)

    cover = prs.slides.add_slide(prs.slide_layouts[0])
    cover.shapes.title.text = "TrainMind – ITI Trainer Copilot"
    cover.placeholders[1].text = f"Training Package\n{package['topic']}\nBased on uploaded curriculum evidence"

    for level, kind, content in _all_artifacts(package):
        paragraphs = [line.strip() for line in content.splitlines() if line.strip()]
        # Keep slides readable: split long artifacts into roughly 7 lines per slide.
        chunks = [paragraphs[i:i + 7] for i in range(0, len(paragraphs), 7)] or [["No content generated."]]
        for chunk_index, chunk in enumerate(chunks, start=1):
            slide = prs.slides.add_slide(prs.slide_layouts[5])
            heading = slide.shapes.title
            heading.text = f"{LEVEL_TITLES[level]} — {ARTIFACT_TITLES[kind]}"
            if len(chunks) > 1:
                heading.text += f" ({chunk_index}/{len(chunks)})"
            left, top, width, height = PptInches(0.7), PptInches(1.35), PptInches(11.9), PptInches(5.6)
            textbox = slide.shapes.add_textbox(left, top, width, height)
            frame = textbox.text_frame
            frame.word_wrap = True
            frame.clear()
            for line_index, line in enumerate(chunk):
                paragraph = frame.paragraphs[0] if line_index == 0 else frame.add_paragraph()
                clean = _plain_markdown(line)
                paragraph.text = clean
                paragraph.font.size = PptPt(19 if line.startswith("## ") or line.startswith("### ") else 15)
                paragraph.space_after = PptPt(8)

    output = io.BytesIO()
    prs.save(output)
    return output.getvalue()


def build_exports(package: dict) -> dict[str, bytes]:
    """Build all three export formats and return file bytes by extension."""
    return {
        "pdf": export_pdf(package),
        "pptx": export_pptx(package),
        "docx": export_docx(package),
    }
