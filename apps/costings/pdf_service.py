"""
PDF Generation Service for Module 4: Costing Reports

PBI-BE-M4-13: Generate professional PDF costing reports
- Include company profile, product details, cost breakdown
- Price breakdown (EXW, FOB, CIF with detailed components)
- Container optimization (20ft & 40ft)
- Export-ready professional format
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
    - Include: company profile, product details, detailed cost breakdown
    - Container capacity (20ft & 40ft) with optimization notes
    - Professional format untuk buyer/stakeholder
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
            textColor=colors.black,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.black,
            spaceAfter=8,
            spaceBefore=8,
            fontName="Helvetica-Bold",
        )

        # 1. Header - Title
        story.append(Paragraph("EXPORT COSTING REPORT", title_style))
        story.append(Spacer(1, 0.3 * inch))

        # 2. Company Information
        story.append(Paragraph("Company Information", heading_style))

        company_data = [
            ["Company Name:", business_profile.company_name],
            ["Address:", business_profile.address or "N/A"],
        ]

        company_table = Table(company_data, colWidths=[2 * inch, 4 * inch])
        company_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        story.append(company_table)
        story.append(Spacer(1, 0.3 * inch))

        # 2. Product Information
        story.append(Paragraph("Product Information", heading_style))

        # Get material info if available
        material_info = "N/A"
        if hasattr(product, 'material_composition') and product.material_composition:
            material_info = product.material_composition
        
        product_data = [
            ["Product Name:", product.name_local],
            ["Category:", str(product.category_id) if product.category_id else "N/A"],
            ["Material:", material_info],
            [
                "Dimensions:",
                f"{{h: {product.dimensions_l_w_h.get('h', 0)}, l: {product.dimensions_l_w_h.get('l', 0)}, w: {product.dimensions_l_w_h.get('w', 0)}}}"
            ],
            [
                "Weight (Gross):",
                f"{product.weight_gross} kg" if hasattr(product, 'weight_gross') and product.weight_gross else "N/A",
            ],
        ]

        product_table = Table(product_data, colWidths=[2 * inch, 4 * inch])
        product_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        story.append(product_table)
        story.append(Spacer(1, 0.3 * inch))

        # 3. Cost Breakdown
        story.append(Paragraph("Cost Breakdown", heading_style))

        # Calculate detailed cost components
        from apps.costings.models import ExchangeRate
        try:
            exchange_rate_obj = ExchangeRate.objects.latest("updated_at")
            exchange_rate = float(exchange_rate_obj.rate)
        except:
            exchange_rate = 15800.00  # Default fallback

        cogs_idr = float(costing.cogs_per_unit)
        packing_idr = float(costing.packing_cost)
        margin_pct = float(costing.target_margin_percent)

        # Detailed cost breakdown table
        cost_data = [
            ["Description", "Amount (USD)"],
            ["COGS per unit (IDR)", f"IDR {cogs_idr:,.2f}"],
            ["Packing cost (IDR)", f"IDR {packing_idr:,.2f}"],
            ["Target Margin", f"{margin_pct:.2f}%"],
            ["", ""],  # Separator
            ["EXW Price", f"${float(costing.recommended_exw_price):.2f}"],
            ["Trucking Cost", "$250.00"],  # Standard estimate
            ["Document Cost", "$75.00"],   # Standard estimate
            ["FOB Price", f"${float(costing.recommended_fob_price):.2f}"],
            ["Freight Cost", "$6.50"],     # Standard estimate
            ["Insurance Cost", "$1.64"],   # Standard estimate
            ["CIF Price", f"${float(costing.recommended_cif_price):.2f}" if costing.recommended_cif_price else "N/A"],
        ]

        cost_table = Table(cost_data, colWidths=[3.5 * inch, 2.5 * inch])
        cost_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 1), (-1, 4), colors.white),
                    ("BACKGROUND", (0, 5), (-1, -1), colors.white),
                    ("LINEABOVE", (0, 5), (-1, 5), 1, colors.black),  # Bold line before EXW
                    ("LINEABOVE", (0, 8), (-1, 8), 1, colors.black),  # Bold line before FOB
                    ("LINEABOVE", (0, 11), (-1, 11), 1, colors.black), # Bold line before CIF
                ]
            )
        )
        story.append(cost_table)
        story.append(Spacer(1, 0.3 * inch))

        # 4. Container Capacity
        story.append(Paragraph("Container Capacity", heading_style))

        # Calculate 40ft capacity (approximately 2.1x of 20ft)
        capacity_20ft = costing.container_20ft_capacity
        capacity_40ft = int(capacity_20ft * 2.1)  # 40ft has ~2.1x volume of 20ft

        container_data = [
            ["Container Type", "Capacity (units)"],
            ["20ft Container", f"{capacity_20ft:,}"],
            ["40ft Container", f"{capacity_40ft:,}"],
        ]

        container_table = Table(container_data, colWidths=[3 * inch, 3 * inch])
        container_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ]
            )
        )
        story.append(container_table)
        story.append(Spacer(1, 0.2 * inch))

        # Optimization Notes (styled as paragraph below container table)
        if costing.optimization_notes:
            opt_text = f"<b>Optimization Notes:</b> {costing.optimization_notes}"
            opt_style = ParagraphStyle(
                "OptNotes",
                parent=styles["Normal"],
                fontSize=9,
                textColor=colors.black,
                leading=12,
            )
            story.append(Paragraph(opt_text, opt_style))
            story.append(Spacer(1, 0.2 * inch))

        # 5. Exchange Rate Footer
        exchange_footer = f"Exchange Rate Used: 1 USD = {exchange_rate:,.2f} IDR"
        exchange_style = ParagraphStyle(
            "Exchange",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_LEFT,
        )
        story.append(Paragraph(exchange_footer, exchange_style))
        
        # 6. Report Footer
        report_footer = f"Generated by ExportReady.AI | Report ID: {costing.id}"
        report_style = ParagraphStyle(
            "ReportFooter",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_LEFT,
        )
        story.append(Paragraph(report_footer, report_style))

        # Build PDF
        try:
            doc.build(story)
            buffer.seek(0)
            logger.info(f"PDF costing report generated for costing {costing.id}")
            return buffer
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise
