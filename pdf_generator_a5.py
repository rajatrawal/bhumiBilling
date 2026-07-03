import os
import logging
from datetime import datetime

from num2words import num2words

from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib import colors

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)

from reportlab.lib.enums import (
    TA_CENTER,
    TA_RIGHT,
)

logger = logging.getLogger(
    "BhumiBilling.PDFGeneratorA5"
)


def generate_invoice_pdf(
        invoice: dict,
        settings: dict,
        output_path: str):

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True
    )

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A5,
        leftMargin=2 * mm,
        rightMargin=2 * mm,
        topMargin=2 * mm,
        bottomMargin=2 * mm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # =====================================================
    # STYLES
    # =====================================================

    company_style = ParagraphStyle(
        "company",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=20,
        alignment=TA_CENTER,
    )

    address_style = ParagraphStyle(
        "address",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        "heading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
    )


    footer_style = ParagraphStyle(
        "footer",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_CENTER,
    )

    # =====================================================
    # BUSINESS DETAILS
    # =====================================================

    biz_name = settings.get(
        "business_name",
        "BHUMI ART JEWELLERY"
    )

    biz_address = settings.get(
        "business_address",
        "262 C Adinath Apt, Bhende Galli, Kolhapur 416002"
    )

    biz_mobile = settings.get(
        "business_mobile",
        ""
    )

    # =====================================================
    # SHREE
    # =====================================================

    shree_style = ParagraphStyle(
        "Shree",
        fontName="Helvetica-Bold",
        fontSize=10,
        alignment=1,  # Center
        spaceAfter=4,
    )

    elements.append(
        Paragraph(
            "|| Shree ||",
            shree_style
        )
    )

    # =====================================================
    # HEADER
    # =====================================================

    elements.append(
        Paragraph(
            biz_name.upper(),
            company_style
        )
    )

    elements.append(
        Paragraph(
            biz_address,
            address_style
        )
    )

    elements.append(
        Paragraph(
            f"Phone : {biz_mobile}",
            address_style
        )
    )

    elements.append(
        Spacer(1, 5)
    )


    # =====================================================
    # DATE FORMAT
    # =====================================================

    bill_date = invoice.get(
        "date",
        ""
    )

    try:
        bill_date = datetime.fromisoformat(
            str(bill_date)
        ).strftime(
            "%d %b %Y"
        )
    except:
        pass

    # =====================================================
# INVOICE + CUSTOMER DETAILS
# =====================================================

    customer_name = invoice.get(
        "customer_name",
        "Walk-in Customer"
    )

    customer_mobile = invoice.get(
        "customer_mobile",
        ""
    )

    details_table = Table(
    [
        [
            f"Invoice No : {invoice.get('bill_no', '')}",
            f"Date : {bill_date}"
        ],
        [
            f"Bill To : {customer_name}",
            f"Mobile : {customer_mobile}"
        ]
    ],
    colWidths=[
        70 * mm,
        70 * mm
    ]
)

    details_table.setStyle(
        TableStyle([

            # Outer border
            ("BOX",
            (0,0),
            (-1,-1),
            1,
            colors.black),

            # Horizontal separator
            ("LINEBELOW",
            (0,0),
            (-1,0),
            1,
            colors.black),

            # Fonts
            ("FONTNAME",
            (0,0),
            (-1,0),
            "Helvetica-Bold"),

            ("FONTNAME",
            (0,1),
            (0,1),
            "Helvetica-Bold"),

            ("FONTNAME",
            (1,1),
            (1,1),
            "Helvetica"),

            # Font size
            ("FONTSIZE",
            (0,0),
            (-1,-1),
            9),

            # Alignment
            ("ALIGN",
            (0,0),
            (0,1),
            "LEFT"),

            ("ALIGN",
            (1,0),
            (1,1),
            "RIGHT"),

            ("VALIGN",
            (0,0),
            (-1,-1),
            "MIDDLE"),

            # Padding
            ("TOPPADDING",
            (0,0),
            (-1,-1),
            5),

            ("BOTTOMPADDING",
            (0,0),
            (-1,-1),
            5),

            ("LEFTPADDING",
            (0,0),
            (-1,-1),
            8),

            ("RIGHTPADDING",
            (0,0),
            (-1,-1),
            8),
        ])
    )

    elements.append(details_table)
    elements.append(Spacer(1, 8))

        # =====================================================
    # PRODUCTS TABLE
    # =====================================================

    data = [
        [
            "SR.",
            "PRODUCT",
            "QTY",
            "RATE",
            "AMOUNT"
        ]
    ]

    for idx, item in enumerate(
            invoice.get(
                "items",
                []
            ),
            start=1):

        qty = item.get(
            "qty",
            0
        )

        rate = item.get(
            "rate",
            0
        )

        amount = qty * rate

        if float(qty).is_integer():
            qty = str(int(qty))
        else:
            qty = f"{qty:.3f}"

        data.append([
            str(idx),
            item.get(
                "product_name",
                ""
            ),
            qty,
            f"{rate:.2f}",
            f"{amount:.2f}",
        ])

    item_table = Table(
        data,
        colWidths=[
            10 * mm,     # SR
            62 * mm,     # PRODUCT
            16 * mm,     # QTY
            20 * mm,     # RATE
            24 * mm,     # AMOUNT
        ]
    )

    item_table.setStyle(
        TableStyle([

            # Header Background
            ("BACKGROUND",
             (0,0),
             (-1,0),
             colors.HexColor("#EFEFEF")),

            # Header Font
            ("FONTNAME",
             (0,0),
             (-1,0),
             "Helvetica-Bold"),

            ("FONTSIZE",
             (0,0),
             (-1,0),
             10),

            # Body Font
            ("FONTNAME",
             (0,1),
             (-1,-1),
             "Helvetica"),

            ("FONTSIZE",
             (0,1),
             (-1,-1),
             9),

            # Header Center
            ("ALIGN",
             (0,0),
             (-1,0),
             "CENTER"),

            # SR Center
            ("ALIGN",
             (0,1),
             (0,-1),
             "CENTER"),

            # Numbers Right
            ("ALIGN",
             (2,1),
             (-1,-1),
             "RIGHT"),

            # Vertical Align
            ("VALIGN",
             (0,0),
             (-1,-1),
             "MIDDLE"),

            # Zebra Rows
            ("ROWBACKGROUNDS",
             (0,1),
             (-1,-1),
             [
                 colors.white,
                 colors.HexColor("#FAFAFA")
             ]),

            # Grid
            ("GRID",
             (0,0),
             (-1,-1),
             0.5,
             colors.grey),

            # Outer Border
            ("BOX",
             (0,0),
             (-1,-1),
             1,
             colors.black),

            # Padding
            ("TOPPADDING",
             (0,0),
             (-1,-1),
             5),

            ("BOTTOMPADDING",
             (0,0),
             (-1,-1),
             5),

            ("LEFTPADDING",
             (0,0),
             (-1,-1),
             4),

            ("RIGHTPADDING",
             (0,0),
             (-1,-1),
             4),
        ])
    )

    elements.append(
        item_table
    )

    # Luxury whitespace before totals
    elements.append(
        Spacer(1, 12)
    )



    # =====================================================
    # COMPACT TOTALS SECTION
    # =====================================================

    gross = invoice.get(
        "gross_total",
        0
    )

    net = invoice.get(
        "net_total",
        0
    )

    paid = invoice.get(
        "paid_amount",
        0
    )

    pending = invoice.get(
        "pending_amount",
        0
    )

    discount = gross - net

    headers = [
        "Gross",
        "Discount",
        "Net",
        "Paid",
        "Balance"
    ]

    values = [
        f"{gross:,.2f}",
        f"{discount:,.2f}",
        f"{net:,.2f}",
        f"{paid:,.2f}",
        f"{pending:,.2f}",
    ]

    total_table = Table(
        [
            headers,
            values
        ],
        colWidths=[
            24 * mm,
            24 * mm,
            26 * mm,   # slightly wider for Net
            24 * mm,
            26 * mm,
        ]
    )

    total_table.setStyle(
        TableStyle([

            # Outer Border
            (
                "BOX",
                (0, 0),
                (-1, -1),
                1,
                colors.black
            ),

            # Grid
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            # Header Background
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#EEEEEE")
            ),

            # Default Header Font
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            # Default Value Font
            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica"
            ),

            # Highlight Net Column
            (
                "FONTNAME",
                (2, 0),
                (2, 1),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (2, 0),
                (2, 1),
                12
            ),

            # Light background for Net
            (
                "BACKGROUND",
                (2, 0),
                (2, 1),
                colors.HexColor("#F5F5F5")
            ),

            # Alignment
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            # Default Font Size
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),

            # Compact Padding
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                3
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                3
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                2
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                2
            ),
        ])
    )

    elements.append(
        total_table
    )

    elements.append(
        Spacer(1, 8)
    )
    # =====================================================
    # FOOTER
    # =====================================================

    footer_message = settings.get(
        "footer_message",
        "THANK YOU FOR YOUR BUSINESS"
    )

    elements.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.grey,
        )
    )

    elements.append(
        Spacer(1, 8)
    )

    elements.append(
        Paragraph(
            f"<b>{footer_message}</b>",
            ParagraphStyle(
                "footer",
                alignment=TA_CENTER,
                fontSize=10,
            ),
        )
    )

    elements.append(
        Paragraph(
            "*** VISIT AGAIN ***",
            ParagraphStyle(
                "footer2",
                alignment=TA_CENTER,
                fontSize=8,
            ),
        )
    )

    # =====================================================
    # BUILD PDF
    # =====================================================

    try:
        doc.build(
            elements
        )

        logger.info(
            f"A5 invoice generated at {output_path}"
        )

    except Exception as e:
        logger.exception(
            "Failed to generate invoice"
        )
        raise