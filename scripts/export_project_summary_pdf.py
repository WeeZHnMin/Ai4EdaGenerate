from pathlib import Path

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ROOT_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT_DIR / "思路文档" / "项目介绍与实现说明.md"
OUTPUT_PATH = ROOT_DIR / "思路文档" / "项目介绍与实现说明.pdf"
FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path(r"C:\Windows\Fonts\simsun.ttc"),
]


def register_font():
    for font_path in FONT_CANDIDATES:
        if font_path.exists():
            pdfmetrics.registerFont(TTFont("ProjectFont", str(font_path)))
            return "ProjectFont"
    raise FileNotFoundError("No suitable Chinese font found on this machine.")


def build_styles(font_name):
    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "ProjectTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=20,
        leading=26,
        spaceAfter=18,
    )
    heading1 = ParagraphStyle(
        "Heading1CN",
        parent=styles["Heading1"],
        fontName=font_name,
        fontSize=15,
        leading=22,
        spaceBefore=10,
        spaceAfter=8,
    )
    heading2 = ParagraphStyle(
        "Heading2CN",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=12,
        leading=18,
        spaceBefore=8,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "BodyCN",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10.5,
        leading=17,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    code = ParagraphStyle(
        "CodeCN",
        parent=styles["Code"],
        fontName=font_name,
        fontSize=9,
        leading=13,
        leftIndent=12,
        backColor="#F5F5F5",
        spaceAfter=8,
    )
    return title, heading1, heading2, body, code


def escape_html(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def markdown_to_story(markdown_text, styles):
    title_style, heading1_style, heading2_style, body_style, code_style = styles
    story = []
    in_code_block = False
    code_lines = []

    def flush_code():
        nonlocal code_lines
        if code_lines:
            code_text = "<br/>".join(escape_html(line) for line in code_lines)
            story.append(Paragraph(code_text, code_style))
            code_lines = []

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code_block:
                flush_code()
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        if not line.strip():
            story.append(Spacer(1, 6))
            continue

        if line.startswith("# "):
            story.append(Paragraph(escape_html(line[2:].strip()), title_style))
            continue

        if line.startswith("## "):
            story.append(Paragraph(escape_html(line[3:].strip()), heading1_style))
            continue

        if line.startswith("### "):
            story.append(Paragraph(escape_html(line[4:].strip()), heading2_style))
            continue

        if line.startswith("- "):
            bullet_text = f"• {line[2:].strip()}"
            story.append(Paragraph(escape_html(bullet_text), body_style))
            continue

        if line[:2].isdigit() and line[1:3] == ". ":
            story.append(Paragraph(escape_html(line), body_style))
            continue

        story.append(Paragraph(escape_html(line), body_style))

    flush_code()
    return story


def main():
    font_name = register_font()
    styles = build_styles(font_name)
    markdown_text = INPUT_PATH.read_text(encoding="utf-8")
    story = markdown_to_story(markdown_text, styles)

    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=42,
        bottomMargin=42,
        title="EDAGenerate 项目介绍与实现说明",
    )
    doc.build(story)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
