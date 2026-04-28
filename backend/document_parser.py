import os
import io
import csv
import json
import re

def parse_document(file_path=None, file_bytes=None, filename=None):
    if file_path:
        filename = filename or os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
    
    if not filename or not file_bytes:
        return {"error": "No file provided", "text": ""}
    
    ext = os.path.splitext(filename)[1].lower()
    
    parsers = {
        '.txt': _parse_txt,
        '.md': _parse_txt,
        '.py': _parse_txt,
        '.js': _parse_txt,
        '.ts': _parse_txt,
        '.tsx': _parse_txt,
        '.jsx': _parse_txt,
        '.json': _parse_json,
        '.csv': _parse_csv,
        '.docx': _parse_docx,
        '.doc': _parse_doc,
        '.pdf': _parse_pdf,
        '.xlsx': _parse_xlsx,
        '.xls': _parse_xlsx,
        '.ods': _parse_ods,
        '.html': _parse_html,
        '.htm': _parse_html,
        '.xml': _parse_xml,
        '.rtf': _parse_rtf,
        '.yaml': _parse_txt,
        '.yml': _parse_txt,
        '.toml': _parse_txt,
        '.ini': _parse_txt,
        '.cfg': _parse_txt,
        '.log': _parse_txt,
        '.sh': _parse_txt,
        '.bash': _parse_txt,
        '.bat': _parse_txt,
        '.sql': _parse_txt,
        '.r': _parse_txt,
        '.java': _parse_txt,
        '.c': _parse_txt,
        '.cpp': _parse_txt,
        '.h': _parse_txt,
        '.rb': _parse_txt,
        '.go': _parse_txt,
        '.rs': _parse_txt,
        '.swift': _parse_txt,
        '.kt': _parse_txt,
        '.lua': _parse_txt,
        '.php': _parse_txt,
        '.pl': _parse_txt,
        '.css': _parse_txt,
        '.scss': _parse_txt,
        '.sass': _parse_txt,
        '.less': _parse_txt,
    }
    
    parser = parsers.get(ext)
    if not parser:
        try:
            text = file_bytes.decode('utf-8', errors='replace')
            return {"text": text, "format": "unknown_text", "chars": len(text)}
        except:
            return {"error": f"Unsupported format: {ext}", "text": ""}
    
    try:
        result = parser(file_bytes, filename)
        result['format'] = ext
        return result
    except Exception as e:
        return {"error": f"Parse error ({ext}): {str(e)}", "text": ""}


def _parse_txt(data, filename=""):
    text = data.decode('utf-8', errors='replace')
    return {"text": text, "chars": len(text)}


def _parse_json(data, filename=""):
    text = data.decode('utf-8', errors='replace')
    try:
        obj = json.loads(text)
        flat = _flatten_json(obj)
        return {"text": flat, "chars": len(flat)}
    except:
        return {"text": text, "chars": len(text)}


def _flatten_json(obj, prefix=""):
    parts = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                parts.append(f"{k}: {v}")
            elif isinstance(v, (int, float, bool)):
                parts.append(f"{k}: {v}")
            else:
                parts.append(_flatten_json(v, f"{prefix}{k}."))
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, str):
                parts.append(item)
            else:
                parts.append(_flatten_json(item, prefix))
    else:
        parts.append(str(obj))
    return "\n".join(parts)


def _parse_csv(data, filename=""):
    text = data.decode('utf-8', errors='replace')
    reader = csv.reader(io.StringIO(text))
    rows = []
    for row in reader:
        rows.append(" ".join(row))
    result = "\n".join(rows)
    return {"text": result, "chars": len(result), "rows": len(rows)}


def _parse_docx(data, filename=""):
    from docx import Document
    doc = Document(io.BytesIO(data))
    paragraphs = []
    for para in doc.paragraphs:
        t = para.text.strip()
        if t:
            paragraphs.append(t)
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                paragraphs.append(" | ".join(cells))
    text = "\n\n".join(paragraphs)
    return {"text": text, "chars": len(text), "paragraphs": len(paragraphs)}


def _parse_doc(data, filename=""):
    try:
        text = data.decode('utf-8', errors='replace')
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return {"text": text, "chars": len(text)}
    except:
        return {"error": "Legacy .doc format — save as .docx for best results", "text": ""}


def _parse_pdf(data, filename=""):
    from PyPDF2 import PdfReader
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            pages.append(t.strip())
    text = "\n\n".join(pages)
    return {"text": text, "chars": len(text), "pages": len(pages)}


def _parse_xlsx(data, filename=""):
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    rows = []
    for sheet in wb.sheetnames:
        ws = wb[sheet]
        rows.append(f"Sheet: {sheet}")
        for row in ws.iter_rows(values_only=True):
            cells = [str(c) if c is not None else "" for c in row]
            if any(cells):
                rows.append(" | ".join(cells))
    text = "\n".join(rows)
    return {"text": text, "chars": len(text), "rows": len(rows)}


def _parse_ods(data, filename=""):
    from odf.opendocument import load as odf_load
    from odf.table import Table, TableRow, TableCell
    from odf.text import P
    doc = odf_load(io.BytesIO(data))
    rows = []
    for table in doc.getElementsByType(Table):
        rows.append(f"Sheet: {table.getAttribute('name')}")
        for row in table.getElementsByType(TableRow):
            cells = []
            for cell in row.getElementsByType(TableCell):
                text_parts = []
                for p in cell.getElementsByType(P):
                    t = ""
                    for child in p.childNodes:
                        t += str(child)
                    text_parts.append(t)
                cells.append(" ".join(text_parts))
            if any(cells):
                rows.append(" | ".join(cells))
    text = "\n".join(rows)
    return {"text": text, "chars": len(text), "rows": len(rows)}


def _parse_html(data, filename=""):
    text = data.decode('utf-8', errors='replace')
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return {"text": text, "chars": len(text)}


def _parse_xml(data, filename=""):
    text = data.decode('utf-8', errors='replace')
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return {"text": text, "chars": len(text)}


def _parse_rtf(data, filename=""):
    text = data.decode('utf-8', errors='replace')
    text = re.sub(r'\\[a-z]+\d*\s?', '', text)
    text = re.sub(r'[{}]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return {"text": text, "chars": len(text)}


SUPPORTED_FORMATS = [
    '.txt', '.md', '.py', '.js', '.ts', '.tsx', '.json', '.csv',
    '.docx', '.doc', '.pdf', '.xlsx', '.xls', '.ods',
    '.html', '.htm', '.xml', '.rtf', '.yaml', '.yml', '.toml',
    '.sh', '.sql', '.java', '.c', '.cpp', '.go', '.rs', '.rb',
    '.php', '.css', '.scss', '.log', '.ini', '.cfg',
]
