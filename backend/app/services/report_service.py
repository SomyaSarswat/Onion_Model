import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models import BatchAnalysisResult, ImageAnalysisResult
from app.config import settings

class ReportService:
    @staticmethod
    def generate_pdf_report(
        batch_result: BatchAnalysisResult,
        standard_name: str = "NAFED_Relaxed_2026",
        output_filename: str = None
    ) -> str:
        """
        Generates a formal PDF Quality Assessment & Grading Report.
        Returns the path to the generated PDF file.
        """
        if not output_filename:
            output_filename = f"report_{batch_result.batch_id}.pdf"

        pdf_path = settings.REPORTS_DIR / output_filename

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'DocSubTitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=12
        )
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#334155')
        )
        warning_style = ParagraphStyle(
            'WarningText',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#9A3412')
        )

        elements = []

        # ---------------------------------------------------------
        # HEADER & METADATA
        # ---------------------------------------------------------
        elements.append(Paragraph("ONION QUALITY ASSESSMENT & GRADING REPORT", title_style))
        elements.append(Paragraph(f"Official Procurement Inspection Report | Standard: {standard_name}", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284C7'), spaceAfter=10))

        meta_data = [
            [
                Paragraph(f"<b>Batch ID:</b> {batch_result.batch_id}", body_style),
                Paragraph(f"<b>Inspection Date:</b> {batch_result.timestamp}", body_style)
            ],
            [
                Paragraph(f"<b>Total Images:</b> {batch_result.total_images}", body_style),
                Paragraph(f"<b>Total Onions Analyzed:</b> {batch_result.total_onions}", body_style)
            ],
            [
                Paragraph(f"<b>Grading Ruleset:</b> {standard_name}", body_style),
                Paragraph("<b>Vision Model:</b> Roboflow YOLOv8x (veg1-hcqsf-2/4)", body_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 10))

        # ---------------------------------------------------------
        # BATCH SUMMARY & DISTRIBUTION
        # ---------------------------------------------------------
        elements.append(Paragraph("1. Executive Grading Summary", section_heading))
        
        summary_data = [
            ["Grade Category", "Count", "Percentage", "Status Compliance"],
            ["Grade A (Premium)", str(batch_result.grade_a_count), f"{batch_result.grade_a_percent}%", "Compliant"],
            ["URS (Under Sized / Relaxed Spec)", str(batch_result.urs_count), f"{batch_result.urs_percent}%", "Accepted with Discount"],
            ["Non-Compliant (Rejected)", str(batch_result.non_compliant_count), f"{batch_result.non_compliant_percent}%", "Rejected"]
        ]
        summary_table = Table(summary_data, colWidths=[180, 80, 100, 180])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('ALIGN', (1,0), (2,-1), 'CENTER'),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F0FDF4')),
            ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#FEFCE8')),
            ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#FEF2F2')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 10))

        # ---------------------------------------------------------
        # SIZE DISTRIBUTION & DEFECT BREAKDOWN
        # ---------------------------------------------------------
        elements.append(Paragraph("2. Physical Size & Defect Statistics", section_heading))
        
        st = batch_result.stats
        mean_str = f"{st['mean']} mm" if st['mean'] is not None else "N/A"
        median_str = f"{st['median']} mm" if st['median'] is not None else "N/A"
        min_str = f"{st['min']} mm" if st['min'] is not None else "N/A"
        max_str = f"{st['max']} mm" if st['max'] is not None else "N/A"

        stats_data = [
            ["Metric", "Value", "Defect Type", "Detected Count"],
            ["Mean Diameter", mean_str, "Sprouted", str(batch_result.defect_counts.get('sprouted', 0))],
            ["Median Diameter", median_str, "Spoiled / Rot", str(batch_result.defect_counts.get('spoiled', 0))],
            ["Min Diameter", min_str, "Double Split", str(batch_result.defect_counts.get('double_split', 0))],
            ["Max Diameter", max_str, "Black Smut / Staining", str(batch_result.defect_counts.get('black_smut', 0) + batch_result.defect_counts.get('staining', 0))]
        ]
        stats_table = Table(stats_data, colWidths=[130, 140, 140, 130])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 10))

        # ---------------------------------------------------------
        # WARNINGS & DISCLOSURES
        # ---------------------------------------------------------
        elements.append(Paragraph("3. Technical Disclosures & System Warnings", section_heading))
        
        warning_rows = [
            [Paragraph("<b>Notice / Warning Item</b>", warning_style), Paragraph("<b>Description</b>", warning_style)],
            [
                Paragraph("Model Accuracy & Confidence", body_style),
                Paragraph("Roboflow YOLOv8x vision model provides visual evidence only (reported mAP@50 43.4%, Precision 57.3%). Deterministic rules engine made all final grade decisions.", body_style)
            ],
            [
                Paragraph("Bounding-Box Size Estimation", body_style),
                Paragraph("Size measurements are based on 2D bounding-box pixel geometry calibrated against reference coins. Bounding-box estimates are approximate compared to 3D volume/segmentation.", body_style)
            ],
            [
                Paragraph("Staining Surface Measurement", body_style),
                Paragraph("Staining is detected via bounding box cues; exact surface area percentage is unmeasurable without pixel-level segmentation masks.", body_style)
            ]
        ]

        for w in batch_result.warnings:
            warning_rows.append([
                Paragraph("Batch Warning", warning_style),
                Paragraph(w, body_style)
            ])

        warn_table = Table(warning_rows, colWidths=[160, 380])
        warn_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFF7ED')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#FDBA74')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#FED7AA')),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(warn_table)
        elements.append(Spacer(1, 12))

        # ---------------------------------------------------------
        # INDIVIDUAL ONION BREAKDOWN
        # ---------------------------------------------------------
        elements.append(Paragraph("4. Individual Onion Breakdown", section_heading))
        
        all_onions_list = []
        for img_res in batch_result.images:
            all_onions_list.extend(img_res.onions)

        if not all_onions_list:
            elements.append(Paragraph("No individual onions were detected in this analysis.", body_style))
        else:
            onion_rows = [["Onion ID", "Diameter (mm)", "Grade", "Defects Detected", "Grading Reasons"]]
            for o in all_onions_list:
                dia_text = f"{o.diameter_mm:.1f} mm" if o.diameter_mm is not None else "Unmeasured"
                defect_names = ", ".join([d.status_text for d in o.defects]) if o.defects else "None (Clean)"
                reasons_text = "; ".join(o.reasons) if o.reasons else "N/A"
                
                grade_label = o.grade or "PENDING"

                onion_rows.append([
                    Paragraph(f"<b>{o.id}</b>", body_style),
                    Paragraph(dia_text, body_style),
                    Paragraph(f"<b>{grade_label}</b>", body_style),
                    Paragraph(defect_names, body_style),
                    Paragraph(reasons_text, body_style)
                ])

            onion_table = Table(onion_rows, colWidths=[65, 85, 95, 145, 150])
            onion_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                ('PADDING', (0,0), (-1,-1), 5),
            ]))
            elements.append(onion_table)

        doc.build(elements)
        return str(pdf_path)
