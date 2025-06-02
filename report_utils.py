# report_utils.py
import io
import os
import logging
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor, black, lightgrey, darkgrey
from reportlab.lib.units import inch

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

PDF_ACCENT_COLOR_HEX = "#6A0DAD"
PDF_PRIMARY_TEXT_COLOR_HEX = "#222222"
PDF_SECONDARY_TEXT_COLOR_HEX = "#555555"
PDF_TABLE_HEADER_BG_HEX = "#D8D8D8"
PDF_SUCCESS_COLOR_HEX = "#2E8B57"
PDF_ERROR_COLOR_HEX = "#C70039"
PDF_LIGHTGREY_HEX = "#cccccc"
PDF_DARKGREY_HEX = "#999999"
PDF_GRID_COLOR_RL = black

RL_ACCENT_COLOR = HexColor(PDF_ACCENT_COLOR_HEX)
RL_PRIMARY_TEXT_COLOR = HexColor(PDF_PRIMARY_TEXT_COLOR_HEX)
RL_SECONDARY_TEXT_COLOR = HexColor(PDF_SECONDARY_TEXT_COLOR_HEX)
RL_SUCCESS_COLOR = HexColor(PDF_SUCCESS_COLOR_HEX)
RL_ERROR_COLOR = HexColor(PDF_ERROR_COLOR_HEX)

def generate_overall_confidence_pie_chart(classification: str, confidence_percent: float) -> io.BytesIO:
    logger.debug(f"Generating pie chart. Classification: {classification}, Confidence: {confidence_percent}")
    try:
        plt.style.use('classic')
        fig, ax = plt.subplots(figsize=(4.5, 3.15))

        chart_text_color = PDF_PRIMARY_TEXT_COLOR_HEX

        confidence_percent = float(confidence_percent)
        other_percent = 100.0 - confidence_percent

        if classification == "REAL":
            labels = [f'REAL ({confidence_percent:.1f}%)', f'Uncertain ({other_percent:.1f}%)']
            sizes = [confidence_percent, other_percent]
            colors_for_pie = [PDF_SUCCESS_COLOR_HEX, PDF_LIGHTGREY_HEX]
        elif classification == "FAKE":
            labels = [f'FAKE ({confidence_percent:.1f}%)', f'Uncertain ({other_percent:.1f}%)']
            sizes = [confidence_percent, other_percent]
            colors_for_pie = [PDF_ERROR_COLOR_HEX, PDF_LIGHTGREY_HEX]
        else:
            labels = ['N/A (50.0%)', 'N/A (50.0%)']
            sizes = [50.0, 50.0]
            colors_for_pie = [PDF_LIGHTGREY_HEX, PDF_DARKGREY_HEX]

        sizes = [float(s) for s in sizes]

        ax.pie(sizes, labels=labels, colors=colors_for_pie, autopct='%1.1f%%', startangle=90,
               wedgeprops={'edgecolor': 'white'}, textprops={'color': chart_text_color, 'fontsize': 7})
        ax.axis('equal')

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=90, bbox_inches='tight', transparent=True)
        plt.close(fig)
        buf.seek(0)
        logger.debug("Pie chart generated successfully.")
        return buf
    except Exception as e:
        logger.error(f"Exception in generate_overall_confidence_pie_chart: {e}", exc_info=True)
        raise

def generate_detector_scores_bar_chart(details: Dict[str, float]) -> io.BytesIO:
    logger.debug(f"Generating bar chart with details: {details}")
    try:
        plt.style.use('classic')
        fig, ax = plt.subplots(figsize=(4.5, 2.7))

        chart_text_color = PDF_PRIMARY_TEXT_COLOR_HEX
        chart_secondary_text_color = PDF_SECONDARY_TEXT_COLOR_HEX

        components = ['CNN', 'LSTM', 'Transformer']
        scores = [
            float(details.get('cnn_score_real', 0.0)) * 100.0,
            float(details.get('lstm_score_real', 0.0)) * 100.0,
            float(details.get('transformer_score_real', 0.0)) * 100.0
        ]
        bar_colors_hex = ["#4A90E2", "#50E3C2", "#B57EDC"]

        bars = ax.barh(components, scores, color=bar_colors_hex, edgecolor='white', height=0.6)
        ax.set_xlabel('Likelihood of REAL (%)', color=chart_text_color, fontsize=8)
        ax.set_xlim(0, 100)

        for bar_idx, bar in enumerate(bars):
            width = bar.get_width()
            ha_align = 'left'
            text_x_pos = width + 1
            text_color_for_bar_label = chart_text_color
            if width < 15:
                text_x_pos = width / 2
                ha_align = 'center'
                if sum(matplotlib.colors.to_rgb(bar_colors_hex[bar_idx % len(bar_colors_hex)])) < 1.5 :
                    text_color_for_bar_label = 'white'

            ax.text(text_x_pos, bar.get_y() + bar.get_height()/2., f'{width:.0f}%',
                    ha=ha_align, va='center', color=text_color_for_bar_label, fontsize=7)

        ax.tick_params(axis='x', colors=chart_secondary_text_color, labelsize=7)
        ax.tick_params(axis='y', colors=chart_secondary_text_color, labelsize=7)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(chart_secondary_text_color)
        ax.spines['left'].set_color(chart_secondary_text_color)
        fig.tight_layout(pad=0.3)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=90, bbox_inches='tight', transparent=True)
        plt.close(fig)
        buf.seek(0)
        logger.debug("Bar chart generated successfully.")
        return buf
    except Exception as e:
        logger.error(f"Exception in generate_detector_scores_bar_chart: {e}", exc_info=True)
        raise

def generate_pdf_report(analysis_data: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=0.75*inch, leftMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('Title', parent=styles['h1'], alignment=TA_CENTER, fontSize=18,
                                 textColor=HexColor(PDF_ACCENT_COLOR_HEX), spaceAfter=16, fontName='Helvetica-Bold')
    heading_style = ParagraphStyle('Heading2Custom', parent=styles['h2'], fontSize=13,
                                   textColor=HexColor(PDF_ACCENT_COLOR_HEX), spaceBefore=14, spaceAfter=7, fontName='Helvetica-Bold')
    sub_heading_style = ParagraphStyle('SubHeading', parent=styles['h3'], fontSize=11,
                                    textColor=HexColor(PDF_PRIMARY_TEXT_COLOR_HEX), spaceBefore=8, spaceAfter=3, fontName='Helvetica-Bold', alignment=TA_CENTER)
    body_text_style = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], textColor=HexColor(PDF_PRIMARY_TEXT_COLOR_HEX),
                                     spaceAfter=6, leading=14, alignment=TA_JUSTIFY, fontSize=10)
    label_style = ParagraphStyle('Label', parent=styles['Normal'], textColor=HexColor(PDF_SECONDARY_TEXT_COLOR_HEX),
                                 alignment=TA_LEFT, fontName='Helvetica', fontSize=10)
    value_style = ParagraphStyle('Value', parent=styles['Normal'], textColor=HexColor(PDF_PRIMARY_TEXT_COLOR_HEX),
                                 fontName='Helvetica-Bold', alignment=TA_LEFT, fontSize=10)
    classification_style_real = ParagraphStyle('Classification', parent=styles['h2'], alignment=TA_CENTER,
                                               fontSize=22, textColor=HexColor(PDF_SUCCESS_COLOR_HEX), fontName='Helvetica-Bold', spaceAfter=4)
    classification_style_fake = ParagraphStyle('Classification', parent=styles['h2'], alignment=TA_CENTER,
                                               fontSize=22, textColor=HexColor(PDF_ERROR_COLOR_HEX), fontName='Helvetica-Bold', spaceAfter=4)
    confidence_style = ParagraphStyle('Confidence', parent=styles['Normal'], alignment=TA_CENTER,
                                      fontSize=14, textColor=HexColor(PDF_PRIMARY_TEXT_COLOR_HEX), spaceAfter=18, fontName='Helvetica-Bold')
    italic_style = ParagraphStyle('ItalicCustom', parent=styles['Italic'], textColor=HexColor(PDF_SECONDARY_TEXT_COLOR_HEX),
                                  alignment=TA_CENTER, spaceAfter=8, fontSize=9)

    story.append(Paragraph("DeepFake Analysis Report", title_style))
    story.append(Paragraph(f"Video File: <i>{analysis_data.get('filename', 'N/A')}</i>", italic_style))

    classification = analysis_data.get("classification", "N/A")
    if classification == "REAL":
        story.append(Paragraph(classification, classification_style_real))
    else:
        story.append(Paragraph(classification, classification_style_fake))
    story.append(Paragraph(f"Confidence: {analysis_data.get('confidence', 0):.2f}%", confidence_style))

    story.append(Paragraph("Analysis Overview", heading_style))
    details_data = [
        [Paragraph("Frames Analyzed:", label_style), Paragraph(str(analysis_data.get("frames_analyzed", "N/A")), value_style)],
        [Paragraph("Processing Time:", label_style), Paragraph(f"{analysis_data.get('processing_time', 0):.2f}s", value_style)],
    ]
    details_table = Table(details_data, colWidths=[2.5*inch, 4*inch])
    details_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('GRID', (0,0), (-1,-1), 0.8, PDF_GRID_COLOR_RL),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Visual Insights", heading_style))

    try:
        pie_chart_img_data = generate_overall_confidence_pie_chart(
            analysis_data.get("classification", "N/A"),
            analysis_data.get("confidence", 0.0)
        )
        pie_img = Image(pie_chart_img_data, width=3.5*inch, height=2.45*inch, kind='bound')
        chart_table_data_pie = [[pie_img], [Paragraph("Overall Confidence Distribution", sub_heading_style)]]
        chart_table_pie = Table(chart_table_data_pie, colWidths=[doc.width])
        chart_table_pie.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'CENTER'), ('ALIGN', (0,1), (0,1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BOTTOMPADDING', (0,0), (0,0), 5),
            ('TOPPADDING', (0,1), (0,1), 0)
        ]))
        story.append(chart_table_pie)
    except Exception as e:
        logger.error(f"Error generating or adding pie chart for PDF: {e}", exc_info=True)
        story.append(Paragraph("Error: Overall confidence pie chart could not be generated.", body_text_style))
    story.append(Spacer(1, 0.15 * inch))

    detector_scores_data = analysis_data.get("details", {})
    if detector_scores_data:
        try:
            bar_chart_img_data = generate_detector_scores_bar_chart(detector_scores_data)
            bar_img = Image(bar_chart_img_data, width=4*inch, height=2.16*inch, kind='bound')
            chart_table_data_bar = [[bar_img], [Paragraph("Detector Component Scores", sub_heading_style)]]
            chart_table_bar = Table(chart_table_data_bar, colWidths=[doc.width])
            chart_table_bar.setStyle(TableStyle([
                ('ALIGN', (0,0), (0,0), 'CENTER'), ('ALIGN', (0,1), (0,1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BOTTOMPADDING', (0,0), (0,0), 5),
                ('TOPPADDING', (0,1), (0,1), 0)
            ]))
            story.append(chart_table_bar)
        except Exception as e:
            logger.error(f"Error generating or adding bar chart for PDF: {e}", exc_info=True)
            story.append(Paragraph("Error: Detector scores bar chart could not be generated.", body_text_style))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Detector Scores (Tabular Data)", heading_style))
    scores_data_table = [
        [Paragraph("Component", label_style), Paragraph("Score (Likelihood of REAL)", label_style)],
        [Paragraph("CNN (Spatial)", body_text_style), Paragraph(f"{detector_scores_data.get('cnn_score_real', 0):.3f}", value_style)],
        [Paragraph("LSTM (Temporal)", body_text_style), Paragraph(f"{detector_scores_data.get('lstm_score_real', 0):.3f}", value_style)],
        [Paragraph("Transformer (Global)", body_text_style), Paragraph(f"{detector_scores_data.get('transformer_score_real', 0):.3f}", value_style)],
    ]
    scores_table = Table(scores_data_table, colWidths=[3*inch, 3.5*inch])
    scores_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor(PDF_TABLE_HEADER_BG_HEX)),
        ('TEXTCOLOR', (0,0), (-1,0), HexColor(PDF_PRIMARY_TEXT_COLOR_HEX)),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica'), ('FONTNAME', (1,1), (1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.8, PDF_GRID_COLOR_RL),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(scores_table)
    story.append(Spacer(1, 0.15 * inch))

    frame_previews = analysis_data.get("frame_previews", [])
    if frame_previews:
        story.append(Paragraph("Key Frame Previews", heading_style))
        frame_img_width = 1.5*inch
        frame_img_height = 0.9*inch
        frames_per_row = 3
        table_data_frames = []
        current_row_frames = []

        for i, fp in enumerate(frame_previews):
            try:
                if os.path.exists(fp['path']):
                    img = Image(fp['path'], width=frame_img_width, height=frame_img_height, kind='bound')
                    status_text = f"Status: {fp['status'].capitalize()}"
                    status_rl_color = RL_SECONDARY_TEXT_COLOR
                    if fp['status'] == 'suspicious': status_rl_color = RL_ERROR_COLOR
                    elif fp['status'] == 'normal': status_rl_color = RL_SUCCESS_COLOR
                    
                    status_p_style = ParagraphStyle(f'status_{i}', textColor=status_rl_color, fontSize=7, alignment=TA_CENTER, leading=8)
                    status_p = Paragraph(status_text, status_p_style)
                    
                    cell_content = [img, Spacer(1, 0.03*inch), status_p]
                    current_row_frames.append(cell_content)

                    if len(current_row_frames) == frames_per_row or i == len(frame_previews) - 1:
                        table_data_frames.append(current_row_frames)
                        current_row_frames = []
                else:
                    missing_frame_text = Paragraph(f"Frame N/A:\n{os.path.basename(fp['path'])}", ParagraphStyle('missing', fontSize=7, textColor=RL_SECONDARY_TEXT_COLOR, alignment=TA_CENTER))
                    current_row_frames.append(missing_frame_text)
                    if len(current_row_frames) == frames_per_row or i == len(frame_previews) - 1:
                        table_data_frames.append(current_row_frames)
                        current_row_frames = []
            except Exception as e:
                logger.error(f"Error adding frame {fp.get('path', 'N/A')} to PDF: {e}", exc_info=True)
                error_frame_text = Paragraph(f"Error:\n{os.path.basename(fp.get('path', 'Unknown'))}", ParagraphStyle('error_frame', fontSize=7, textColor=RL_ERROR_COLOR, alignment=TA_CENTER))
                current_row_frames.append(error_frame_text)
                if len(current_row_frames) == frames_per_row or i == len(frame_previews) - 1:
                    table_data_frames.append(current_row_frames)
                    current_row_frames = []
        
        if table_data_frames:
            available_width = doc.width - (frames_per_row -1) * 0.1*inch
            col_width_frames = available_width / frames_per_row
            frames_display_table = Table(table_data_frames, colWidths=[col_width_frames]*frames_per_row)
            frames_display_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('LEFTPADDING', (0,0), (-1,-1), 1), ('RIGHTPADDING', (0,0), (-1,-1), 1),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(frames_display_table)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Method Summary & System Insights", heading_style))
    story.append(Paragraph(
        "This DeepFake detection system employs a hybrid approach, integrating simulated CNN, LSTM, "
        "and Transformer-like components. The CNN focuses on spatial artifacts, the LSTM on temporal "
        "inconsistencies, and the Transformer on global contextual patterns. Scores are weighted to "
        "produce a final classification.", body_text_style
    ))
    story.append(Paragraph(
        "Note: This is a prototype system with simulated detectors. "
        "Actual performance would depend on fully trained deep learning models.", body_text_style 
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes