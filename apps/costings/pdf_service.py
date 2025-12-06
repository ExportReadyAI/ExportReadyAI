"""
PDF Generation Service for Module 4: Costing Reports

PBI-BE-M4-13: Generate professional PDF costing reports
- Include company profile
- Product details
- Price breakdown
- Container optimization info
- Export-ready format
"""

import io
import logging
from decimal import Decimal
from datetime import datetime

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
    Image,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)


class CostingPDFService:
    """
    Service untuk generate PDF report untuk costing
    
    PBI-BE-M4-13: Generate PDF costing report
    - Include: company profile, product details, price breakdown, container info
    - Professional format untuk buyer
    - Response: PDF file (application/pdf)
    """

    # Paper size
    PAGE_SIZE = A4
    PAGE_WIDTH = A4[0]
    PAGE_HEIGHT = A4[1]

    # Margins
    LEFT_MARGIN = 0.5 * inch
    RIGHT_MARGIN = 0.5 * inch
    TOP_MARGIN = 0.5 * inch
    BOTTOM_MARGIN = 0.5 * inch

    @staticmethod
    def generate_costing_pdf(costing, business_profile, product):
        """
        Generate professional PDF costing report

        Args:
            costing: Costing instance
            business_profile: BusinessProfile instance
            product: Product instance

        Returns:
            BytesIO: PDF file content
        """
        buffer = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=CostingPDFService.PAGE_SIZE,
            leftMargin=CostingPDFService.LEFT_MARGIN,
            rightMargin=CostingPDFService.RIGHT_MARGIN,
            topMargin=CostingPDFService.TOP_MARGIN,
            bottomMargin=CostingPDFService.BOTTOM_MARGIN,
        )

        # Content elements
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=20,
            textColor=colors.HexColor("#1f3a93"),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#1f3a93"),
            spaceAfter=8,
            spaceBefore=8,
            fontName="Helvetica-Bold",
        )

        # 1. Header - Company Info
        story.append(Paragraph("COSTING REPORT", title_style))
        story.append(Spacer(1, 0.2 * inch))

        company_data = [
            ["Company Name:", business_profile.company_name],
            ["Contact Email:", business_profile.user.email],
            ["Contact Person:", business_profile.user.full_name],
            ["Address:", business_profile.address],
            ["Year Established:", str(business_profile.year_established)],
            ["Report Date:", datetime.now().strftime("%d %B %Y")],
        ]

        company_table = Table(company_data, colWidths=[2 * inch, 3.5 * inch])
        company_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        story.append(company_table)
        story.append(Spacer(1, 0.3 * inch))

        # 2. Product Information
        story.append(Paragraph("PRODUCT INFORMATION", heading_style))

        product_data = [
            ["Field", "Value"],
            ["Product Name (Local)", product.name_local],
            ["Category ID", str(product.category_id) if product.category_id else "N/A"],
            [
                "Dimensions (L×W×H)",
                f"{product.dimensions_l_w_h.get('l', 0)} × {product.dimensions_l_w_h.get('w', 0)} × {product.dimensions_l_w_h.get('h', 0)} cm",
            ],
            [
                "Weight",
                f"{product.weight_net} kg" if product.weight_net else "N/A",
            ],
            ["Description", product.description_local or "N/A"],
        ]

        product_table = Table(product_data, colWidths=[2 * inch, 3.5 * inch])
        product_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a93")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
                ]
            )
        )
        story.append(product_table)
        story.append(Spacer(1, 0.3 * inch))

        # 3. Costing Inputs
        story.append(Paragraph("COSTING INPUTS", heading_style))

        inputs_data = [
            ["Parameter", "Value"],
            ["COGS per Unit (IDR)", f"Rp {costing.cogs_per_unit:,.0f}"],
            ["Packing Cost (IDR)", f"Rp {costing.packing_cost:,.0f}"],
            ["Target Margin (%)", f"{costing.target_margin_percent}%"],
        ]

        inputs_table = Table(inputs_data, colWidths=[2 * inch, 3.5 * inch])
        inputs_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a93")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
                ]
            )
        )
        story.append(inputs_table)
        story.append(Spacer(1, 0.3 * inch))

        # 4. Price Breakdown
        story.append(Paragraph("PRICING BREAKDOWN (USD)", heading_style))

        pricing_data = [
            ["Price Type", "Amount"],
            ["EXW (Ex-Works)", f"${float(costing.recommended_exw_price):.2f}"],
            ["FOB (Free on Board)", f"${float(costing.recommended_fob_price):.2f}"],
        ]

        if costing.recommended_cif_price:
            pricing_data.append(["CIF (Cost, Insurance, Freight)", f"${float(costing.recommended_cif_price):.2f}"])

        pricing_table = Table(pricing_data, colWidths=[2 * inch, 3.5 * inch])
        pricing_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a93")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
                ]
            )
        )
        story.append(pricing_table)
        story.append(Spacer(1, 0.3 * inch))

        # 5. Container Optimization
        story.append(Paragraph("CONTAINER OPTIMIZATION (20ft)", heading_style))

        container_data = [
            ["Parameter", "Value"],
            ["Capacity (Units)", f"{costing.container_20ft_capacity:,} units"],
            ["Optimization Notes", costing.optimization_notes or "Standard packing efficiency"],
        ]

        container_table = Table(container_data, colWidths=[2 * inch, 3.5 * inch])
        container_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a93")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 1), (1, 1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
                ]
            )
        )
        story.append(container_table)
        story.append(Spacer(1, 0.3 * inch))

        # 6. Footer
        footer_text = "This document is confidential and intended for authorized recipients only. Generated by ExportReady.AI"
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(footer_text, footer_style))

        # Build PDF
        try:
            doc.build(story)
            buffer.seek(0)
            logger.info(f"PDF costing report generated for costing {costing.id}")
            return buffer
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise
