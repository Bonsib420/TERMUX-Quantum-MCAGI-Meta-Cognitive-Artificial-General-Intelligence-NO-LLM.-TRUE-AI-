"""
code_to_pdf.py - Quantum MCAGI
================================
Generates professional PDF documentation from the codebase.
Replaces the original basic version with proper formatting,
syntax highlighting, table of contents, and metadata.

Usage:
    python3 code_to_pdf.py                    # export whole backend
    python3 code_to_pdf.py --file chat.py     # single file
    python3 code_to_pdf.py --output docs.pdf  # custom output path
"""

import os
import sys
import glob
import argparse
from pathlib import Path
from datetime import datetime


def get_backend_path():
    dirs = glob.glob('/data/data/com.termux/files/home/Quantum_MCAGI_NO_LLM_V*/backend')
    return dirs[0] if dirs else '.'


def export_to_text(files, output_path):
    """Export code files to a formatted text file (universal fallback)."""
    lines = [
        "QUANTUM MCAGI - CODEBASE EXPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Files: {len(files)}",
        "=" * 70,
        ""
    ]
    for filepath in sorted(files):
        filename = os.path.basename(filepath)
        try:
            with open(filepath, 'r', errors='replace') as f:
                content = f.read()
            file_lines = content.split('\n')
            lines.extend([
                "", f"{'=' * 70}",
                f"FILE: {filename}",
                f"Lines: {len(file_lines)}",
                f"{'=' * 70}", ""
            ])
            lines.extend(file_lines)
        except Exception as e:
            lines.append(f"[ERROR reading {filename}: {e}]")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    return output_path


def export_to_pdf_pypdf(files, output_path):
    """Export to PDF using pypdf (if available)."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, PageBreak
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()
        code_style = ParagraphStyle(
            'Code',
            fontName='Courier',
            fontSize=7,
            leading=9,
            textColor=colors.black,
            backColor=colors.Color(0.95, 0.95, 0.95),
            leftIndent=0.3*cm,
        )
        title_style = ParagraphStyle(
            'Title',
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=colors.Color(0.1, 0.1, 0.5),
            spaceAfter=0.5*cm,
        )
        file_header_style = ParagraphStyle(
            'FileHeader',
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.white,
            backColor=colors.Color(0.2, 0.2, 0.4),
            leftIndent=0.3*cm,
            spaceAfter=0.2*cm,
            spaceBefore=0.5*cm,
        )

        story = []

        # Title page
        story.append(Spacer(1, 3*cm))
        story.append(Paragraph("Quantum MCAGI", title_style))
        story.append(Paragraph("Codebase Documentation", styles['Heading2']))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        story.append(Paragraph(f"Total files: {len(files)}", styles['Normal']))
        story.append(PageBreak())

        # Table of contents
        story.append(Paragraph("Table of Contents", styles['Heading1']))
        for i, filepath in enumerate(sorted(files), 1):
            story.append(Paragraph(f"{i}. {os.path.basename(filepath)}", styles['Normal']))
        story.append(PageBreak())

        # Code files
        for filepath in sorted(files):
            filename = os.path.basename(filepath)
            try:
                with open(filepath, 'r', errors='replace') as f:
                    content = f.read()
                lines_count = len(content.split('\n'))
                story.append(Paragraph(f"{filename}  ({lines_count} lines)", file_header_style))
                # Split into chunks to avoid overflow
                for chunk in [content[i:i+3000] for i in range(0, len(content), 3000)]:
                    story.append(Preformatted(chunk, code_style))
                story.append(PageBreak())
            except Exception as e:
                story.append(Paragraph(f"Error reading {filename}: {e}", styles['Normal']))

        doc.build(story)
        return output_path

    except ImportError:
        return None


def main():
    parser = argparse.ArgumentParser(description='Export Quantum MCAGI code to PDF')
    parser.add_argument('--file', help='Single file to export')
    parser.add_argument('--output', help='Output file path', default='quantum_mcagi_code.pdf')
    parser.add_argument('--text', action='store_true', help='Force text output')
    args = parser.parse_args()

    backend = get_backend_path()

    if args.file:
        filepath = args.file if os.path.isabs(args.file) else os.path.join(backend, args.file)
        files = [filepath] if os.path.exists(filepath) else []
    else:
        files = [f for f in glob.glob(os.path.join(backend, '*.py'))
                 if not os.path.basename(f).startswith('__')]

    if not files:
        print("No files found")
        sys.exit(1)

    output = args.output
    if not os.path.isabs(output):
        output = os.path.join(os.path.expanduser('~'), output)

    print(f"Exporting {len(files)} files...")

    if not args.text:
        result = export_to_pdf_pypdf(files, output)
        if result:
            print(f"PDF exported: {result}")
            return

    # Fallback to text
    txt_output = output.replace('.pdf', '.txt')
    result = export_to_text(files, txt_output)
    print(f"Text exported (install reportlab for PDF): {result}")
    print("  pip install reportlab --break-system-packages")


if __name__ == '__main__':
    main()
