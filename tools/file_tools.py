"""
tools/file_tools.py — NayePankh AI Workforce
=============================================
Export tools: CSV generation and PDF reports.
"""
import csv
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Exports directory relative to project root
EXPORTS_DIR = Path(__file__).parent.parent / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)


def export_to_csv(data: list[dict], filename: str = None) -> dict:
    """
    Export a list of dicts to a CSV file.

    Args:
        data:     List of row dicts (all dicts must share the same keys)
        filename: Optional filename (without path). Auto-generated if None.

    Returns:
        {"success": bool, "path": str, "rows": int}
    """
    if not data:
        return {"success": False, "path": None, "error": "No data to export"}

    filename = filename or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = EXPORTS_DIR / filename

    try:
        headers = list(data[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"[FileTools] CSV exported: {filepath}")
        return {"success": True, "path": str(filepath), "rows": len(data)}
    except Exception as e:
        logger.error(f"[FileTools] CSV export failed: {e}")
        return {"success": False, "path": None, "error": str(e)}


def export_to_pdf(title: str, sections: list[dict], filename: str = None) -> dict:
    """
    Generate a PDF report using fpdf2.

    Args:
        title:    Report title
        sections: List of {"heading": str, "body": str} dicts
        filename: Optional filename (without path).

    Returns:
        {"success": bool, "path": str}
    """
    filename = filename or f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = EXPORTS_DIR / filename

    try:
        from fpdf import FPDF  # lazy import to keep startup fast

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Title
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(0, 78, 137)  # NayePankh secondary blue
        pdf.cell(0, 12, title, ln=True, align="C")
        pdf.set_text_color(0, 0, 0)

        # Metadata line
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')} | NayePankh Foundation", ln=True, align="C")
        pdf.ln(6)

        # Sections
        for section in sections:
            # Section heading
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_fill_color(245, 245, 245)
            pdf.cell(0, 9, section.get("heading", ""), ln=True, fill=True)
            pdf.ln(2)

            # Section body
            pdf.set_font("Helvetica", "", 10)
            body = section.get("body", "")
            pdf.multi_cell(0, 6, body)
            pdf.ln(4)

        pdf.output(str(filepath))
        logger.info(f"[FileTools] PDF exported: {filepath}")
        return {"success": True, "path": str(filepath)}

    except ImportError:
        logger.warning("[FileTools] fpdf2 not installed. Install with: pip install fpdf2")
        return {"success": False, "path": None, "error": "fpdf2 not installed"}
    except Exception as e:
        logger.error(f"[FileTools] PDF export failed: {e}")
        return {"success": False, "path": None, "error": str(e)}


def get_csv_as_bytes(data: list[dict]) -> bytes:
    """Return CSV content as bytes for Streamlit download buttons."""
    if not data:
        return b""
    output = io.StringIO()
    headers = list(data[0].keys())
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue().encode("utf-8")
