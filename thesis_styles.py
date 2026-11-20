import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

# ---------------------------------------------------------------------------
# COLOR PALETTE TOKENS: Imperial Royal Burgundy / Crimson & Antique Bronze
# ---------------------------------------------------------------------------
BURGUNDY_HEX = "6B1724"      # Primary Accent: Deep Imperial Burgundy
BURGUNDY_DARK_HEX = "54111B" # Deep Crimson Header Accent
GOLD_HEX = "B45309"           # Secondary Accent: Warm Antique Bronze
GOLD_DARK_HEX = "92400E"      # Dark Bronze
ROSE_HEX = "9E2A2B"           # Warm Rose Accent
BODY_DARK_HEX = "1E293B"      # Body Text: Deep Slate Charcoal
MUTED_HEX = "64748B"          # Captions & Meta: Warm Muted Slate
ZEBRA_HEX = "FAF7F2"          # Table Alternating Rows: Warm Pearl Alabaster
BORDER_HEX = "D1C2A5"         # Table Borders: Muted Antique Bronze / Stone
CALLOUT_BG_HEX = "FDF9F5"     # Callout Box: Warm Cream Parchment
CODE_BG_HEX = "F9F7F4"        # Code Blocks: Warm Alabaster Linen

BURGUNDY = RGBColor(107, 23, 36)
GOLD = RGBColor(180, 83, 9)
ROSE = RGBColor(158, 42, 43)
BODY = RGBColor(30, 41, 59)
MUTED = RGBColor(100, 116, 139)

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=55, bottom=55, left=90, right=90):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color=BORDER_HEX, sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:left w:val="none"/>
            <w:right w:val="none"/>
            <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:insideV w:val="none"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders)

def add_styled_table(doc, headers, data, col_widths=None):
    """Generates an institutionally styled academic table where each row is prevented
       from splitting across page boundaries (cantSplit) and header repeats (tblHeader),
       ensuring the entire table stays strictly unified on a single page."""
    table = doc.add_table(rows=len(data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table, color=BORDER_HEX, sz="5")

    # Header Row
    hdr_cells = table.rows[0].cells
    hdr_trPr = table.rows[0]._tr.get_or_add_trPr()
    hdr_trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    hdr_trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

    for i, header_text in enumerate(headers):
        hdr_cells[i].text = header_text
        set_cell_background(hdr_cells[i], BURGUNDY_HEX)
        set_cell_margins(hdr_cells[i], top=80, bottom=80, left=95, right=95)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(255, 255, 255)

    # Data Rows
    for row_idx, row_data in enumerate(data):
        row = table.rows[row_idx + 1]
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

        row_cells = row.cells
        bg_col = ZEBRA_HEX if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, cell_value in enumerate(row_data):
            row_cells[col_idx].text = str(cell_value)
            set_cell_background(row_cells[col_idx], bg_col)
            set_cell_margins(row_cells[col_idx], top=50, bottom=50, left=85, right=85)
            p = row_cells[col_idx].paragraphs[0]
            if col_idx == 0 or (len(row_data) > 3 and col_idx == len(row_data) - 1):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(9.0)
                run.font.color.rgb = BODY

    if col_widths:
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = Inches(width)

    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_before = Pt(2)
    p_space.paragraph_format.space_after = Pt(4)
    return table

def add_code_block(doc, code_text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_background(cell, CODE_BG_HEX)
    set_cell_margins(cell, top=65, bottom=65, left=120, right=120)

    trPr = table.rows[0]._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="4" w:space="0" w:color="{BORDER_HEX}"/>
            <w:left w:val="single" w:sz="20" w:space="0" w:color="{BURGUNDY_HEX}"/>
            <w:bottom w:val="single" w:sz="4" w:space="0" w:color="{BORDER_HEX}"/>
            <w:right w:val="single" w:sz="4" w:space="0" w:color="{BORDER_HEX}"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)

    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(code_text)
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(28, 25, 23)

    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_after = Pt(4)

def add_callout_box(doc, title, content_text, border_col=BURGUNDY_HEX, bg_col=CALLOUT_BG_HEX):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_background(cell, bg_col)
    set_cell_margins(cell, top=60, bottom=60, left=110, right=110)

    trPr = table.rows[0]._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="none"/>
            <w:left w:val="single" w:sz="18" w:space="0" w:color="{border_col}"/>
            <w:bottom w:val="none"/>
            <w:right w:val="none"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)

    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.18
    r_t = p.add_run(f"📌 {title}: ")
    r_t.font.name = "Times New Roman"
    r_t.font.size = Pt(9.5)
    r_t.font.bold = True
    r_t.font.color.rgb = BURGUNDY

    r_c = p.add_run(content_text)
    r_c.font.name = "Times New Roman"
    r_c.font.size = Pt(9.5)
    r_c.font.color.rgb = BODY

    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_after = Pt(4)

def add_figure_image(doc, img_path, caption_text, width=Inches(5.5)):
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(3)
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=width)

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(8)
        run_cap = p_cap.add_run(caption_text)
        run_cap.font.name = "Times New Roman"
        run_cap.font.size = Pt(9.5)
        run_cap.font.bold = True
        run_cap.font.italic = True
        run_cap.font.color.rgb = BURGUNDY

def add_chap_title(doc, chap_num, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(f"Chapter {chap_num}. {title}")
    r.font.name = "Times New Roman"
    r.font.size = Pt(14.5)
    r.font.bold = True
    r.font.color.rgb = BURGUNDY

def add_app_title(doc, app_id, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(f"Appendix {app_id}. {title}")
    r.font.name = "Times New Roman"
    r.font.size = Pt(14.5)
    r.font.bold = True
    r.font.color.rgb = BURGUNDY

def add_sec_title(doc, sec_num, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(f"{sec_num} {title}")
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.color.rgb = BURGUNDY

def add_subsec_title(doc, subsec_num, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(f"{subsec_num} {title}")
    r.font.name = "Times New Roman"
    r.font.size = Pt(10.5)
    r.font.bold = True
    r.font.color.rgb = GOLD

def add_p(doc, text, bold_prefix=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.25
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Times New Roman"
        r_pre.font.size = Pt(10.5)
        r_pre.font.bold = True
        r_pre.font.color.rgb = BURGUNDY
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(10.5)
    r.font.color.rgb = BODY
