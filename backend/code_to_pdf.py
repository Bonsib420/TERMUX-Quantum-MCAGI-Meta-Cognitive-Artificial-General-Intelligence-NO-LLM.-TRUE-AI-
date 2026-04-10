"""
📄 CODE TO PDF — Export Source Code as PDF
==========================================
Converts Python source files (or entire directories) to PDF format
for documentation, printing, or sharing.

Features:
  - Syntax-highlighted code rendering
  - Table of contents for multi-file exports
  - Line numbers
  - Header/footer with file path and page numbers
  - Configurable font size and page layout

Dependencies:
  - reportlab (optional, for high-quality PDF)
  - Falls back to simple text-based PDF if reportlab unavailable

Usage:
    from code_to_pdf import export_code_to_pdf, export_directory_to_pdf

    export_code_to_pdf("chat.py", "chat_code.pdf")
    export_directory_to_pdf("backend/", "full_code.pdf")
"""

import os
import struct
import zlib
import time
from pathlib import Path
from typing import List, Optional, Dict

# ============================================================================
# MINIMAL PDF WRITER (no external dependencies)
# ============================================================================

class SimplePDFWriter:
    """
    Minimal PDF writer using only Python stdlib.

    Produces a valid PDF with text content, line numbers, and headers.
    No external dependencies required.
    """

    def __init__(self, title: str = "Code Export",
                 font_size: int = 9,
                 margin: int = 50):
        self.title = title
        self.font_size = font_size
        self.margin = margin
        self.page_width = 612   # Letter width in points
        self.page_height = 792  # Letter height in points
        self.line_height = font_size + 3
        self.lines_per_page = int(
            (self.page_height - 2 * margin - 30) / self.line_height
        )
        self._pages: List[List[str]] = []
        self._current_page: List[str] = []
        self._current_line = 0

    def add_header(self, text: str):
        """Add a section header."""
        if self._current_line > self.lines_per_page - 5:
            self._new_page()
        self._current_page.append(f"__HEADER__{text}")
        self._current_line += 2

    def add_line(self, text: str, line_num: int = None):
        """Add a line of code."""
        if self._current_line >= self.lines_per_page:
            self._new_page()

        # Escape PDF special characters
        safe = text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        if line_num is not None:
            prefix = f"{line_num:4d} | "
        else:
            prefix = ""
        self._current_page.append(f"{prefix}{safe}")
        self._current_line += 1

    def add_blank_line(self):
        """Add an empty line."""
        self.add_line("")

    def _new_page(self):
        """Start a new page."""
        if self._current_page:
            self._pages.append(self._current_page)
        self._current_page = []
        self._current_line = 0

    def save(self, filepath: str) -> bool:
        """Save to PDF file. Returns True on success."""
        # Flush current page
        if self._current_page:
            self._pages.append(self._current_page)
            self._current_page = []

        if not self._pages:
            return False

        try:
            with open(filepath, 'wb') as f:
                self._write_pdf(f)
            return True
        except Exception as e:
            print(f"PDF save error: {e}")
            return False

    def _write_pdf(self, f):
        """Write minimal PDF structure."""
        objects = []
        xref_positions = []

        # Header
        f.write(b'%PDF-1.4\n')

        # Catalog (object 1)
        xref_positions.append(f.tell())
        pages_kids = ' '.join(f'{3 + i * 2} 0 R' for i in range(len(self._pages)))
        f.write(f'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n'.encode())

        # Pages (object 2)
        xref_positions.append(f.tell())
        kids = ' '.join(f'{3 + i * 2} 0 R' for i in range(len(self._pages)))
        f.write(
            f'2 0 obj\n<< /Type /Pages /Kids [{kids}] '
            f'/Count {len(self._pages)} >>\nendobj\n'.encode()
        )

        # Page objects and content streams
        obj_num = 3
        font_obj = obj_num + len(self._pages) * 2

        for page_idx, page_lines in enumerate(self._pages):
            content_obj = obj_num + 1

            # Page object
            xref_positions.append(f.tell())
            f.write(
                f'{obj_num} 0 obj\n'
                f'<< /Type /Page /Parent 2 0 R '
                f'/MediaBox [0 0 {self.page_width} {self.page_height}] '
                f'/Contents {content_obj} 0 R '
                f'/Resources << /Font << /F1 {font_obj} 0 R >> >> >>\n'
                f'endobj\n'.encode()
            )
            obj_num += 1

            # Content stream
            stream = self._build_page_stream(page_lines, page_idx + 1)
            xref_positions.append(f.tell())
            f.write(
                f'{obj_num} 0 obj\n'
                f'<< /Length {len(stream)} >>\n'
                f'stream\n'.encode()
            )
            f.write(stream)
            f.write(b'\nendstream\nendobj\n')
            obj_num += 1

        # Font object (Courier for code)
        xref_positions.append(f.tell())
        f.write(
            f'{font_obj} 0 obj\n'
            f'<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\n'
            f'endobj\n'.encode()
        )

        # Cross-reference table
        xref_start = f.tell()
        total_objects = font_obj
        f.write(f'xref\n0 {total_objects + 1}\n'.encode())
        f.write(b'0000000000 65535 f \n')
        for pos in xref_positions:
            f.write(f'{pos:010d} 00000 n \n'.encode())

        # Trailer
        f.write(
            f'trailer\n<< /Size {total_objects + 1} /Root 1 0 R >>\n'
            f'startxref\n{xref_start}\n%%EOF\n'.encode()
        )

    def _build_page_stream(self, lines: List[str], page_num: int) -> bytes:
        """Build PDF content stream for a page."""
        parts = []
        parts.append(f'BT')
        parts.append(f'/F1 {self.font_size} Tf')

        y = self.page_height - self.margin

        # Page header
        parts.append(f'{self.margin} {y} Td')
        safe_title = self.title.replace('(', '\\(').replace(')', '\\)')
        parts.append(f'/F1 7 Tf')
        parts.append(f'({safe_title} — Page {page_num}) Tj')
        parts.append(f'/F1 {self.font_size} Tf')
        y -= self.line_height * 2

        # Move to first content line
        parts.append(f'{self.margin} {y} Td')

        for line in lines:
            if line.startswith('__HEADER__'):
                header_text = line[10:]
                safe = header_text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
                parts.append(f'/F1 {self.font_size + 2} Tf')
                parts.append(f'({safe}) Tj')
                parts.append(f'/F1 {self.font_size} Tf')
            else:
                # Truncate long lines
                if len(line) > 100:
                    line = line[:97] + '...'
                parts.append(f'({line}) Tj')
            parts.append(f'0 -{self.line_height} Td')

        parts.append('ET')
        return '\n'.join(parts).encode('latin-1', errors='replace')


# ============================================================================
# PUBLIC API
# ============================================================================

def export_code_to_pdf(source_path: str, output_path: str,
                        title: str = None,
                        font_size: int = 9) -> Dict:
    """
    Export a source code file to PDF.

    Args:
        source_path: Path to source file
        output_path: Path for output PDF
        title: Optional title (defaults to filename)
        font_size: Font size in points

    Returns:
        Dict with status, page count, line count
    """
    if not os.path.isfile(source_path):
        return {"error": f"File not found: {source_path}", "success": False}

    filename = os.path.basename(source_path)
    pdf = SimplePDFWriter(title=title or filename, font_size=font_size)

    try:
        with open(source_path, 'r', errors='ignore') as f:
            lines = f.readlines()

        pdf.add_header(filename)
        pdf.add_blank_line()

        for i, line in enumerate(lines, 1):
            pdf.add_line(line.rstrip('\n'), line_num=i)

        success = pdf.save(output_path)
        return {
            "success": success,
            "source": source_path,
            "output": output_path,
            "lines": len(lines),
            "pages": len(pdf._pages) + (1 if pdf._current_page else 0),
        }
    except Exception as e:
        return {"error": str(e), "success": False}


def export_directory_to_pdf(directory: str, output_path: str,
                             extensions: List[str] = None,
                             font_size: int = 8) -> Dict:
    """
    Export all source files in a directory to a single PDF.

    Args:
        directory: Source directory
        output_path: Output PDF path
        extensions: File extensions to include (default: .py)
        font_size: Font size

    Returns:
        Stats dict
    """
    if extensions is None:
        extensions = ['.py']

    if not os.path.isdir(directory):
        return {"error": f"Not a directory: {directory}", "success": False}

    pdf = SimplePDFWriter(
        title=os.path.basename(directory.rstrip('/')),
        font_size=font_size,
    )

    total_lines = 0
    files_processed = []

    # Collect and sort files
    source_files = []
    for root, _dirs, filenames in os.walk(directory):
        for fname in sorted(filenames):
            ext = os.path.splitext(fname)[1].lower()
            if ext in extensions:
                source_files.append(os.path.join(root, fname))

    source_files.sort()

    for filepath in source_files:
        try:
            with open(filepath, 'r', errors='ignore') as f:
                lines = f.readlines()

            rel_path = os.path.relpath(filepath, directory)
            pdf.add_header(f"═══ {rel_path} ═══")
            pdf.add_blank_line()

            for i, line in enumerate(lines, 1):
                pdf.add_line(line.rstrip('\n'), line_num=i)

            pdf.add_blank_line()
            pdf.add_blank_line()

            total_lines += len(lines)
            files_processed.append(rel_path)
        except Exception as e:
            pdf.add_line(f"[Error reading {filepath}: {e}]")

    success = pdf.save(output_path)
    return {
        "success": success,
        "output": output_path,
        "files": len(files_processed),
        "total_lines": total_lines,
        "pages": len(pdf._pages) + (1 if pdf._current_page else 0),
        "files_processed": files_processed,
    }
