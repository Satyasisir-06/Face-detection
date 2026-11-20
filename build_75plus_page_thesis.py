import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from thesis_styles import BURGUNDY, GOLD, BODY, MUTED, BURGUNDY_HEX, GOLD_HEX
from thesis_preliminary import build_preliminary_pages
from thesis_chapters_1_to_3 import build_chapters_1_to_3
from thesis_chapters_4_to_6 import build_chapters_4_to_6
from thesis_chapters_7_to_11 import build_chapters_7_to_11
from thesis_appendices import build_appendices

def build_complete_75plus_thesis():
    print("Initializing AURA Vision 75+ Page Academic Thesis Generator...")
    doc = docx.Document()

    # Configure Margins: Left 1.25" (JNTU-GV Binding Margin), Top/Bottom/Right 1.0"
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.25)
        section.right_margin = Inches(1.0)
        section.different_first_page_header_footer = True

        header = section.header
        p_head = header.paragraphs[0]
        p_head.text = "AURA VISION — AI Computer Vision & Demographic Analysis | Chaitanya Engineering College"
        p_head.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_head.runs[0].font.name = "Times New Roman"
        p_head.runs[0].font.size = Pt(8.5)
        p_head.runs[0].font.color.rgb = RGBColor(120, 113, 108) # Warm Muted Stone

        footer = section.footer
        p_foot = footer.paragraphs[0]
        p_foot.text = "Department of Artificial Intelligence • Regulation: JNTUGV-BTECH-R23"
        p_foot.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_foot.runs[0].font.name = "Times New Roman"
        p_foot.runs[0].font.size = Pt(8.5)
        p_foot.runs[0].font.color.rgb = RGBColor(120, 113, 108)

    figures_dir = r"e:\Projects\Face Recog\docs\figures"
    college_logo = os.path.join(figures_dir, "chaitanya_college_logo.png")
    college_banner = os.path.join(figures_dir, "college_header_banner.png")

    team_members = [
        ("M. BHARGAVI", "24L61A4220"),
        ("P. DEEPIKA", "24L61A4223"),
        ("R. REESHMA", "24L61A4227"),
        ("M. SAI SRAVANTH", "24L61A4217"),
        ("M. MOHAN SAI", "24L61A4218"),
    ]

    # 1. Build Preliminary Pages (Pages 1–13)
    print("Building Preliminary Section (Cover, Certificates, TOC, Lists, Abstract)...")
    build_preliminary_pages(doc, college_logo, college_banner, team_members)

    # 2. Build Chapters 1 to 3 (Introduction, Literature Survey, System Analysis)
    print("Building Chapters 1 to 3...")
    build_chapters_1_to_3(doc)

    # 3. Build Chapters 4 to 6 (System Design, Source Code, Mathematical Formulations)
    print("Building Chapters 4 to 6...")
    build_chapters_4_to_6(doc, figures_dir)

    # 4. Build Chapters 7 to 11 (Testing, Results, Enterprise Security, Conclusion, References)
    print("Building Chapters 7 to 11...")
    build_chapters_7_to_11(doc, figures_dir, team_members)

    # 5. Build Technical Appendices (Appendices A to E)
    print("Building Technical Appendices A to E...")
    build_appendices(doc)

    output_path = r"e:\Projects\Face Recog\AURA_VISION_PROJECT_RECORD.docx"
    doc.save(output_path)
    print(f"Master 75+ Page Thesis Record successfully written to: {output_path}")

if __name__ == '__main__':
    build_complete_75plus_thesis()
