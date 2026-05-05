#!/usr/bin/env python3
"""
Generate a PDF containing all Python source code from the MCAGI backend.
Run this in Termux to create a complete code reference document.

The PDF is both human-readable AND machine-extractable: every .py file
is embedded as a PDF attachment. Recipients can extract the pristine
source files using any PDF reader (Attachments panel) or via CLI:

    python -c "from pypdf import PdfReader; \
        r = PdfReader('quantum_mcagi_code.pdf'); \
        [open(k,'wb').write(v[0]) for k,v in r.attachments.items()]"

Usage:
    python code_to_pdf.py                         # defaults to backend/
    python code_to_pdf.py /path/to/backend/       # custom path
    python code_to_pdf.py /path/ output.pdf       # custom output
"""

import os
import sys
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Preformatted
)
from reportlab.lib.enums import TA_CENTER

try:
    from pypdf import PdfWriter, PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


def get_python_files(directory):
    """
    Collects metadata for Python (.py) files in a directory.
    
    Scans the given directory, selects files whose names end with `.py` and do not start with `__`, and returns a list of metadata dictionaries for each file sorted by filename. File sizes are reported in bytes. Line counts are computed by reading each file as UTF-8 with errors ignored; if a file cannot be read, its `lines` value will be 0.
    
    Parameters:
        directory (str): Path to the directory to scan.
    
    Returns:
        List[dict]: A list of dictionaries, each containing:
            - name (str): The filename.
            - path (str): The full filesystem path to the file.
            - size (int): File size in bytes.
            - lines (int): Number of lines in the file (0 if unreadable).
    """
    files = []
    for f in sorted(os.listdir(directory)):
        if f.endswith('.py') and not f.startswith('__'):
            path = os.path.join(directory, f)
            size = os.path.getsize(path)
            lines = 0
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                    lines = sum(1 for _ in fh)
            except:
                pass
            files.append({
                'name': f,
                'path': path,
                'size': size,
                'lines': lines,
            })
    return files


def escape_xml(text):
    """
    Escape characters in a string for safe inclusion in ReportLab XML.
    
    Replaces the characters: & → &amp;, < → &lt;, > → &gt;, " → &quot;.
    
    Parameters:
        text (str): Input text to escape.
    
    Returns:
        str: Escaped text suitable for embedding in ReportLab XML.
    """
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    return text


def build_pdf(source_dir, output_path):
    """
    Generate a multi-page PDF containing all Python source files found under source_dir.
    
    Builds a styled document with a title page, table of contents, and one section per .py file showing file metadata and the file contents (split into chunks when large). If pypdf is available, embeds each original .py as a PDF attachment for lossless extraction. The function writes the resulting PDF to output_path and prints progress and summary information to stdout.
    
    Parameters:
        source_dir (str): Path to the directory to scan for `.py` files (top-level files only).
        output_path (str): Filesystem path where the generated PDF will be written.
    """
    files = get_python_files(source_dir)
    total_lines = sum(f['lines'] for f in files)
    total_size = sum(f['size'] for f in files)

    print(f"Found {len(files)} Python files")
    print(f"Total: {total_lines:,} lines, {total_size/1024:.0f}KB")
    print(f"Generating PDF...")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=HexColor('#1a1a2e'),
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=HexColor('#555555'),
        alignment=TA_CENTER,
        spaceAfter=20,
    )

    file_header_style = ParagraphStyle(
        'FileHeader',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=HexColor('#0a3d62'),
        spaceBefore=10,
        spaceAfter=6,
        borderWidth=1,
        borderColor=HexColor('#0a3d62'),
        borderPadding=4,
    )

    file_meta_style = ParagraphStyle(
        'FileMeta',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#888888'),
        spaceAfter=8,
    )

    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=5.5,
        leading=7,
        leftIndent=4,
        rightIndent=4,
        textColor=HexColor('#1a1a1a'),
        backColor=HexColor('#f5f5f5'),
    )

    story = []

    # Title Page
    story.append(Spacer(1, 100))
    story.append(Paragraph("Quantum MCAGI", title_style))
    story.append(Paragraph("Complete Source Code", ParagraphStyle(
        'Sub', parent=styles['Heading2'], alignment=TA_CENTER, textColor=HexColor('#333')
    )))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"Files: {len(files)} | Lines: {total_lines:,} | Size: {total_size/1024:.0f}KB",
        subtitle_style
    ))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        subtitle_style
    ))
    story.append(Paragraph(
        "By Cory Nathaniel Bonsib Blackburn",
        subtitle_style
    ))
    story.append(Paragraph(
        "No LLM. No API. Pure algorithms. Built on Android/Termux.",
        subtitle_style
    ))

    if HAS_PYPDF:
        story.append(Spacer(1, 30))
        extract_note = ParagraphStyle(
            'ExtractNote', parent=styles['Normal'],
            fontSize=9, textColor=HexColor('#0a3d62'),
            alignment=TA_CENTER, spaceAfter=4,
        )
        story.append(Paragraph(
            "This PDF contains embedded .py source files as attachments.",
            extract_note
        ))
        story.append(Paragraph(
            "Open Attachments panel in your PDF reader, or extract via CLI:",
            extract_note
        ))
        extract_code = ParagraphStyle(
            'ExtractCode', parent=styles['Code'],
            fontName='Courier', fontSize=7, leading=10,
            alignment=TA_CENTER, textColor=HexColor('#333'),
        )
        story.append(Paragraph(
            'python -c "from pypdf import PdfReader; r = PdfReader(\'FILE.pdf\'); '
            '[open(k,\'wb\').write(v[0]) for k,v in r.attachments.items()]"',
            extract_code
        ))

    story.append(PageBreak())

    # Table of Contents
    story.append(Paragraph("Table of Contents", styles['Heading1']))
    story.append(Spacer(1, 10))

    toc_data = [['#', 'File', 'Lines', 'Size']]
    for i, f in enumerate(files, 1):
        toc_data.append([
            str(i),
            f['name'],
            f"{f['lines']:,}",
            f"{f['size']/1024:.1f}KB"
        ])

    toc_table = Table(toc_data, colWidths=[30, 300, 60, 60])
    toc_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#0a3d62')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f0f0f0')]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(toc_table)
    story.append(PageBreak())

    # Code Files
    for i, f in enumerate(files, 1):
        print(f"  [{i}/{len(files)}] {f['name']} ({f['lines']} lines)")

        story.append(Paragraph(
            f"{i}. {escape_xml(f['name'])}",
            file_header_style
        ))
        story.append(Paragraph(
            f"{f['lines']:,} lines | {f['size']/1024:.1f}KB | {f['path']}",
            file_meta_style
        ))

        try:
            with open(f['path'], 'r', encoding='utf-8', errors='ignore') as fh:
                code = fh.read()
        except Exception as e:
            code = f"# Error reading file: {e}"

        escaped = escape_xml(code)
        code_lines = escaped.split("\n")
        max_lines = 500

        for chunk_start in range(0, len(code_lines), max_lines):
            chunk = "\n".join(code_lines[chunk_start:chunk_start + max_lines])
            story.append(Preformatted(chunk, code_style))

        story.append(PageBreak())

    print(f"Building PDF...")
    doc.build(story)

    # Embed raw .py files as PDF attachments for lossless extraction
    if HAS_PYPDF:
        print(f"Embedding {len(files)} source files as PDF attachments...")
        reader = PdfReader(output_path)
        writer = PdfWriter()
        writer.append_pages_from_reader(reader)
        writer.add_metadata(reader.metadata or {})

        for f in files:
            try:
                with open(f['path'], 'rb') as fh:
                    writer.add_attachment(f['name'], fh.read())
            except Exception as e:
                print(f"  Warning: could not embed {f['name']}: {e}")

        with open(output_path, 'wb') as out:
            writer.write(out)
        print(f"Attachments embedded. Extract with:")
        print(f"  python -c \"from pypdf import PdfReader; ")
        print(f"    r = PdfReader('{os.path.basename(output_path)}'); ")
        print(f"    [open(k,'wb').write(v[0]) for k,v in r.attachments.items()]\"")
    else:
        print("Note: install pypdf to embed source files as extractable attachments")
        print("  pip install pypdf")

    size = os.path.getsize(output_path)
    print(f"Done: {output_path} ({size/1024/1024:.1f}MB)")


if __name__ == '__main__':
    source = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/Quantum_MCAGI_NO_LLM_V⁰²/backend')
    output = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser('~/storage/downloads/quantum_mcagi_code.pdf')

    if not os.path.isdir(source):
        print(f"Directory not found: {source}")
        sys.exit(1)

    build_pdf(source, output)

