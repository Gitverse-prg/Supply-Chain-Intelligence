import os
from datetime import datetime

REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_pdf_report(report_text: str, filename: str = None) -> str:
    """Generate PDF from report text using ReportLab"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from reportlab.lib import colors

        if not filename:
            filename = f"CEO_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        filepath = os.path.join(REPORTS_DIR, filename)
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                 leftMargin=inch, rightMargin=inch,
                                 topMargin=inch, bottomMargin=inch)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Title'],
                                     fontSize=18, textColor=colors.HexColor('#1a1a2e'),
                                     spaceAfter=20, alignment=TA_CENTER)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
                                       fontSize=13, textColor=colors.HexColor('#16213e'),
                                       spaceBefore=15, spaceAfter=8,
                                       borderPad=4)
        body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                    fontSize=10, leading=16,
                                    textColor=colors.HexColor('#333333'))
        meta_style = ParagraphStyle('Meta', parent=styles['Normal'],
                                    fontSize=9, textColor=colors.grey,
                                    alignment=TA_CENTER)

        story = []
        story.append(Paragraph("GLOBAL SUPPLY CHAIN SHOCK INTELLIGENCE PLATFORM", title_style))
        story.append(Paragraph("CEO EXECUTIVE REPORT", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}", meta_style))
        story.append(Spacer(1, 0.2 * inch))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0f3460')))
        story.append(Spacer(1, 0.2 * inch))

        lines = report_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.1 * inch))
                continue

            if line.startswith('##') or line.upper() == line and len(line) > 5:
                clean = line.replace('#', '').strip()
                story.append(Paragraph(clean, heading_style))
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc')))
            elif line.startswith('-') or line.startswith('•'):
                story.append(Paragraph(f"&bull; {line[1:].strip()}", body_style))
            elif line[0].isdigit() and len(line) > 3 and line[1] in '.):':
                story.append(Paragraph(f"<b>{line[0]}.</b> {line[2:].strip()}", body_style))
            else:
                story.append(Paragraph(line, body_style))

        story.append(Spacer(1, 0.5 * inch))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0f3460')))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("CONFIDENTIAL — Supply Chain Shock Intelligence Platform", meta_style))

        doc.build(story)
        return filepath

    except ImportError:
        # Fallback: plain text file
        if not filename:
            filename = f"CEO_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(REPORTS_DIR, filename.replace('.pdf', '.txt'))
        with open(filepath, 'w') as f:
            f.write(f"GLOBAL SUPPLY CHAIN SHOCK INTELLIGENCE PLATFORM\n")
            f.write(f"CEO EXECUTIVE REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%B %d, %Y')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(report_text)
        return filepath
    except Exception as e:
        raise RuntimeError(f"PDF generation failed: {e}")
