from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from services.ledger_service import transactions_with_running_balance


PAGE_SIZE = landscape(A4)
PRIMARY = colors.HexColor("#0f766e")
INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")
BORDER = colors.HexColor("#cbd5e1")
SOFT = colors.HexColor("#f8fafc")
SUCCESS = colors.HexColor("#047857")
DANGER = colors.HexColor("#be123c")
BODY_FONT = "Helvetica"
BODY_FONT_BOLD = "Helvetica-Bold"
INDIC_FONT = "Nirmala"
INDIC_FONT_PATH = "C:/Windows/Fonts/Nirmala.ttc"


try:
    pdfmetrics.registerFont(TTFont(INDIC_FONT, INDIC_FONT_PATH))
except Exception:
    INDIC_FONT = BODY_FONT


def build_supplier_ledger_pdf(db, supplier, shop_name, start_date=None, end_date=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=PAGE_SIZE,
        rightMargin=28,
        leftMargin=28,
        topMargin=26,
        bottomMargin=30,
        title=f"{supplier.get('supplier_name', 'Supplier')} Ledger",
    )

    styles = build_styles()
    story = []

    all_rows = transactions_with_running_balance(db, supplier)
    rows = [
        row
        for row in all_rows
        if (not start_date or row["date"] >= start_date) and (not end_date or row["date"] <= end_date)
    ]

    totals = calculate_totals(rows, supplier)
    story.extend(build_header(shop_name, supplier, start_date, end_date, totals, styles))
    story.append(Spacer(1, 0.18 * inch))
    story.append(build_ledger_table(rows, supplier, styles))
    story.append(Spacer(1, 0.18 * inch))
    story.append(build_footer_note(styles))

    doc.build(story, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
    buffer.seek(0)
    return buffer


def build_styles():
    base = getSampleStyleSheet()
    base.add(
        ParagraphStyle(
            name="ShopTitle",
            parent=base["Title"],
            fontName=BODY_FONT_BOLD,
            fontSize=22,
            leading=26,
            textColor=INK,
            spaceAfter=2,
        )
    )
    base.add(
        ParagraphStyle(
            name="ReportLabel",
            parent=base["Normal"],
            fontName=BODY_FONT_BOLD,
            fontSize=8,
            leading=10,
            textColor=MUTED,
        )
    )
    base.add(
        ParagraphStyle(
            name="ReportValue",
            parent=base["Normal"],
            fontName=BODY_FONT_BOLD,
            fontSize=10,
            leading=13,
            textColor=INK,
        )
    )
    base.add(
        ParagraphStyle(
            name="SmallMuted",
            parent=base["Normal"],
            fontName=BODY_FONT,
            fontSize=8,
            leading=11,
            textColor=MUTED,
        )
    )
    base.add(
        ParagraphStyle(
            name="Description",
            parent=base["Normal"],
            fontName=INDIC_FONT,
            fontSize=8,
            leading=12,
            textColor=INK,
        )
    )
    base.add(
        ParagraphStyle(
            name="Right",
            parent=base["Normal"],
            fontName=BODY_FONT,
            alignment=TA_RIGHT,
            fontSize=8,
            leading=10,
            textColor=INK,
        )
    )
    base.add(
        ParagraphStyle(
            name="Center",
            parent=base["Normal"],
            fontName=BODY_FONT,
            alignment=TA_CENTER,
            fontSize=8,
            leading=10,
            textColor=INK,
        )
    )
    base.add(
        ParagraphStyle(
            name="HeaderCell",
            parent=base["Normal"],
            fontName=BODY_FONT_BOLD,
            alignment=TA_CENTER,
            fontSize=8,
            leading=10,
            textColor=colors.white,
        )
    )
    base.add(
        ParagraphStyle(
            name="IndicValue",
            parent=base["Normal"],
            fontName=INDIC_FONT,
            fontSize=10,
            leading=13,
            textColor=INK,
        )
    )
    return base


def build_header(shop_name, supplier, start_date, end_date, totals, styles):
    generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p")
    period = f"{format_date(start_date) if start_date else 'Opening'} to {format_date(end_date) if end_date else 'Today'}"

    title_block = [
        Paragraph(escape_text(shop_name), styles["ShopTitle"]),
        Paragraph("Supplier Ledger Statement", styles["ReportValue"]),
        Paragraph(f"Generated: {generated_at}", styles["SmallMuted"]),
    ]

    supplier_lines = [
        [Paragraph("SUPPLIER", styles["ReportLabel"])],
        [Paragraph(escape_text(supplier.get("supplier_name", "-")), styles["IndicValue"])],
    ]
    if supplier.get("mobile_number"):
        supplier_lines.append([Paragraph(f"Mobile: {escape_text(supplier.get('mobile_number'))}", styles["SmallMuted"])])
    if supplier.get("address"):
        supplier_lines.append([Paragraph(f"Address: {escape_text(supplier.get('address'))}", styles["SmallMuted"])])

    header = Table(
        [[title_block, supplier_lines]],
        colWidths=[4.7 * inch, 5.9 * inch],
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
                ("LINEBEFORE", (1, 0), (1, 0), 0.7, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    summary_rows = [
        [
            summary_cell("Report Period", period, styles),
            summary_cell("Opening Balance", money(totals["opening_balance"]), styles),
            summary_cell("Total Credit", money(totals["total_credit"]), styles, SUCCESS),
            summary_cell("Total Debit", money(totals["total_debit"]), styles, DANGER),
            summary_cell("Final Balance", money(totals["final_balance"]), styles, PRIMARY),
        ]
    ]
    summary = Table(summary_rows, colWidths=[2.1 * inch, 2.1 * inch, 2.1 * inch, 2.1 * inch, 2.2 * inch])
    summary.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    return [header, Spacer(1, 0.12 * inch), summary]


def summary_cell(label, value, styles, value_color=INK):
    value_style = ParagraphStyle(
        name=f"Value{label}",
        parent=styles["ReportValue"],
        textColor=value_color,
        fontSize=12,
        leading=15,
    )
    return [Paragraph(label.upper(), styles["ReportLabel"]), Paragraph(value, value_style)]


def build_ledger_table(rows, supplier, styles):
    table_data = [
        [
            Paragraph("DATE", styles["HeaderCell"]),
            Paragraph("PARTICULARS", styles["HeaderCell"]),
            Paragraph("QTY / UNIT", styles["HeaderCell"]),
            Paragraph("RATE", styles["HeaderCell"]),
            Paragraph("CREDIT", styles["HeaderCell"]),
            Paragraph("DEBIT", styles["HeaderCell"]),
            Paragraph("BALANCE", styles["HeaderCell"]),
        ]
    ]

    if rows:
        for row in rows:
            is_credit = row["transaction_type"] == "credit"
            amount = float(row["amount"])
            table_data.append(
                [
                    Paragraph(format_date(row["date"]), styles["Center"]),
                    Paragraph(escape_text(row["description"] or row["transaction_type"].title()), styles["Description"]),
                    Paragraph(f"{row['quantity']:g} {escape_text(row['unit'])}", styles["Right"]),
                    Paragraph(money(row["rate"]), styles["Right"]),
                    Paragraph(money(amount) if is_credit else "-", styles["Right"]),
                    Paragraph(money(amount) if not is_credit else "-", styles["Right"]),
                    Paragraph(money(row["balance"]), styles["Right"]),
                ]
            )
    else:
        table_data.append(
            [
                Paragraph("-", styles["Center"]),
                Paragraph("No transactions found for this period.", styles["Description"]),
                Paragraph("-", styles["Right"]),
                Paragraph("-", styles["Right"]),
                Paragraph("-", styles["Right"]),
                Paragraph("-", styles["Right"]),
                Paragraph(money(supplier.get("opening_balance", 0)), styles["Right"]),
            ]
        )

    table = Table(
        table_data,
        repeatRows=1,
        colWidths=[1.05 * inch, 3.45 * inch, 1.0 * inch, 1.1 * inch, 1.2 * inch, 1.2 * inch, 1.4 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), BODY_FONT_BOLD),
                ("GRID", (0, 0), (-1, -1), 0.45, BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbfdff")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 9),
                ("TOPPADDING", (0, 1), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (4, 1), (4, -1), colors.HexColor("#f0fdf4")),
                ("BACKGROUND", (5, 1), (5, -1), colors.HexColor("#fff1f2")),
                ("BACKGROUND", (6, 1), (6, -1), colors.HexColor("#f8fafc")),
            ]
        )
    )
    return table


def build_footer_note(styles):
    return Paragraph(
        "Note: Balance is calculated as Opening Balance + Credit - Debit. Please verify all entries before sharing as a final account statement.",
        styles["SmallMuted"],
    )


def calculate_totals(rows, supplier):
    opening_balance = float(supplier.get("opening_balance", 0))
    total_credit = sum(float(row["amount"]) for row in rows if row["transaction_type"] == "credit")
    total_debit = sum(float(row["amount"]) for row in rows if row["transaction_type"] == "debit")
    final_balance = rows[-1]["balance"] if rows else opening_balance
    return {
        "opening_balance": opening_balance,
        "total_credit": total_credit,
        "total_debit": total_debit,
        "final_balance": float(final_balance),
    }


def draw_page_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDER)
    canvas.line(doc.leftMargin, 20, PAGE_SIZE[0] - doc.rightMargin, 20)
    canvas.setFont(BODY_FONT, 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 10, "Computer generated supplier ledger statement")
    canvas.drawRightString(PAGE_SIZE[0] - doc.rightMargin, 10, f"Page {doc.page}")
    canvas.restoreState()


def money(value):
    return f"Rs. {float(value or 0):,.2f}"


def format_date(value):
    if not value:
        return "-"
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d-%m-%Y")
    except ValueError:
        return str(value)


def escape_text(value):
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
