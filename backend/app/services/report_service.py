import io
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.db.models import InterviewSessionModel
from app.utils.logger import logger

class ReportService:
    @classmethod
    def generate_pdf_report(cls, session: InterviewSessionModel, user_name: str = "Candidate") -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=10
        )
        
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=15
        )

        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=12,
            spaceAfter=8
        )

        normal_text = ParagraphStyle(
            'NormalText',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155")
        )

        bold_text = ParagraphStyle(
            'BoldText',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor("#0F172A")
        )

        elements = []

        # 1. Header Block
        elements.append(Paragraph("AI INTERVIEW COACH — EVALUATION REPORT", title_style))
        elements.append(Paragraph(f"Candidate: <b>{user_name}</b> | Session ID: {session.id[:8]}... | Date: {session.created_at.strftime('%Y-%m-%d %H:%M')}", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3B82F6"), spaceAfter=15))

        # 2. Executive Score Summary Card Table
        scores = session.scores
        score_data = [
            [
                Paragraph("<b>Overall Score</b>", bold_text),
                Paragraph("<b>Technical Knowledge</b>", bold_text),
                Paragraph("<b>SQL Score (Q12-Q13)</b>", bold_text),
                Paragraph("<b>Communication</b>", bold_text),
                Paragraph("<b>Presentation & Gaze</b>", bold_text)
            ],
            [
                Paragraph(f"<font size=16 color='#2563EB'><b>{scores.overall_score}/100</b></font>", normal_text),
                Paragraph(f"<font size=13><b>{scores.technical_knowledge}/100</b></font>", normal_text),
                Paragraph(f"<font size=13 color='#0D9488'><b>{scores.sql_score}%</b></font>", normal_text),
                Paragraph(f"<font size=13><b>{scores.communication}/100</b></font>", normal_text),
                Paragraph(f"<font size=13><b>{scores.presentation}/100</b></font>", normal_text)
            ]
        ]
        score_table = Table(score_data, colWidths=[105, 105, 110, 100, 100])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 15))

        # 3. Speech & Vision Metrics Section
        elements.append(Paragraph("Speech, Coding & Behavioral Dynamics", section_heading))
        metrics_data = [
            [Paragraph("<b>Metric</b>", bold_text), Paragraph("<b>Value</b>", bold_text), Paragraph("<b>Assessment</b>", bold_text)],
            [Paragraph("SQL Coding Assessment (Q12 & Q13)", normal_text), Paragraph(f"{scores.sql_score}%", normal_text), Paragraph("All SQL queries verified correct" if scores.sql_score == 100 else ("1 SQL query passed" if scores.sql_score == 50 else "Practice SQL queries & joins"), normal_text)],
            [Paragraph("Average Eye Contact", normal_text), Paragraph(f"{scores.eye_contact}%", normal_text), Paragraph("Optimal camera gaze" if scores.eye_contact >= 75 else "Improve camera alignment", normal_text)],
            [Paragraph("Average Speaking Rate", normal_text), Paragraph(f"{session.speech_metrics.average_wpm} WPM", normal_text), Paragraph("Optimal pace (110-160 WPM)" if 110 <= session.speech_metrics.average_wpm <= 160 else "Pacing adjustment recommended", normal_text)],
            [Paragraph("Total Filler Words", normal_text), Paragraph(f"{session.speech_metrics.total_fillers} words", normal_text), Paragraph("Minimal fillers" if session.speech_metrics.total_fillers <= 5 else "Reduce vocal pauses", normal_text)],
            [Paragraph("Pseudocode Performance", normal_text), Paragraph(f"{scores.pseudocode_score}/100", normal_text), Paragraph("Strong code tracing" if scores.pseudocode_score >= 80 else "Practice output prediction", normal_text)]
        ]
        metrics_table = Table(metrics_data, colWidths=[160, 120, 240])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 15))

        # 4. Face Monitoring Proctoring Summary Section
        fm = session.vision_metrics.face_monitoring
        if fm:
            elements.append(Paragraph("Face Proctoring & Integrity Summary", section_heading))
            proctor_data = [
                [Paragraph("<b>Proctor Metric</b>", bold_text), Paragraph("<b>Value</b>", bold_text), Paragraph("<b>Integrity Status</b>", bold_text)],
                [Paragraph("Single Face Presence", normal_text), Paragraph(f"{fm.single_face_percentage}%", normal_text), Paragraph("Normal candidate posture" if fm.single_face_percentage >= 90 else "Intermittent face presence", normal_text)],
                [Paragraph("Missing Face Events", normal_text), Paragraph(f"{fm.missing_face_events} events ({fm.missing_face_percentage}%)", normal_text), Paragraph("Clean attendance" if fm.missing_face_events == 0 else "Face stepped out of frame", normal_text)],
                [Paragraph("Multiple Face Events", normal_text), Paragraph(f"{fm.multiple_face_events} events ({fm.multiple_face_percentage}%)", normal_text), Paragraph("No unauthorized persons" if fm.multiple_face_events == 0 else "Multiple persons detected", normal_text)]
            ]
            proctor_table = Table(proctor_data, colWidths=[160, 120, 240])
            proctor_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#FEF3C7")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#FCD34D")),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            elements.append(proctor_table)
            elements.append(Spacer(1, 15))

        # 5. Gemini AI Suggestions & Coaching Section
        sug = getattr(session, "suggestions", None)
        fb = session.gemini_feedback

        if sug:
            elements.append(Paragraph("AI Performance Feedback & Actionable Coaching", section_heading))
            summary_txt = sug.get("overallSummary") or sug.get("overall_summary") or ""
            elements.append(Paragraph(f"<b>Executive Summary:</b> {summary_txt}", normal_text))
            elements.append(Spacer(1, 6))

            strengths_list = sug.get("strengths", [])
            if strengths_list:
                elements.append(Paragraph("<b>Key Strengths:</b>", bold_text))
                for st in strengths_list[:4]:
                    elements.append(Paragraph(f"• {st}", normal_text))
                elements.append(Spacer(1, 6))

            improvements_list = sug.get("improvementAreas") or sug.get("areas_to_improve") or []
            if improvements_list:
                elements.append(Paragraph("<b>Areas for Growth:</b>", bold_text))
                for imp in improvements_list[:4]:
                    elements.append(Paragraph(f"• {imp}", normal_text))
                elements.append(Spacer(1, 6))

            comm_fb = sug.get("communicationFeedback")
            if comm_fb and isinstance(comm_fb, dict):
                elements.append(Paragraph("<b>Communication Coaching:</b>", bold_text))
                for k, v in comm_fb.items():
                    elements.append(Paragraph(f"• <b>{k.capitalize()}:</b> {v}", normal_text))
                elements.append(Spacer(1, 6))

            topics_list = sug.get("recommendedTopics") or sug.get("recommended_topics") or []
            if topics_list:
                elements.append(Paragraph(f"<b>Recommended Study Topics:</b> {', '.join(topics_list[:6])}", normal_text))
                elements.append(Spacer(1, 6))

            practice_plan = sug.get("practicePlan")
            if practice_plan and isinstance(practice_plan, list):
                elements.append(Paragraph("<b>5-Day Structured Practice Plan:</b>", bold_text))
                for day_item in practice_plan[:5]:
                    d_num = day_item.get("day", 1)
                    d_focus = day_item.get("focus", "")
                    d_tasks = ", ".join(day_item.get("tasks", []))
                    elements.append(Paragraph(f"• <b>Day {d_num} ({d_focus}):</b> {d_tasks}", normal_text))
                elements.append(Spacer(1, 6))

            goals_list = sug.get("nextInterviewGoals") or []
            if goals_list:
                elements.append(Paragraph("<b>Goals for Next Mock Interview:</b>", bold_text))
                for g in goals_list[:4]:
                    elements.append(Paragraph(f"• {g}", normal_text))
                elements.append(Spacer(1, 10))

        elif fb:
            elements.append(Paragraph("AI Performance Feedback & Actionable Recommendations", section_heading))
            elements.append(Paragraph(f"<b>Summary:</b> {fb.overall_summary}", normal_text))
            elements.append(Spacer(1, 6))

            if fb.strengths:
                elements.append(Paragraph("<b>Key Strengths:</b>", bold_text))
                for st in fb.strengths[:3]:
                    elements.append(Paragraph(f"• {st}", normal_text))
                elements.append(Spacer(1, 6))

            if fb.areas_to_improve:
                elements.append(Paragraph("<b>Areas for Growth:</b>", bold_text))
                for imp in fb.areas_to_improve[:3]:
                    elements.append(Paragraph(f"• {imp}", normal_text))
                elements.append(Spacer(1, 6))

            if fb.recommended_topics:
                elements.append(Paragraph(f"<b>Recommended Practice Topics:</b> {', '.join(fb.recommended_topics)}", normal_text))
                elements.append(Spacer(1, 10))

        # 6. Question-by-Question Detailed Breakdown Table
        elements.append(PageBreak())
        elements.append(Paragraph("Detailed Question-by-Question Breakdown", section_heading))

        q_table_data = [
            [Paragraph("<b>#</b>", bold_text), Paragraph("<b>Question</b>", bold_text), Paragraph("<b>Candidate Answer / Response</b>", bold_text), Paragraph("<b>Score</b>", bold_text)]
        ]

        for i, q in enumerate(session.questions):
            ans = session.answers[i] if i < len(session.answers) else None
            ans_text = ""
            if ans:
                if q.type == "sql":
                    ans_text = (ans.candidate_query or (ans.transcript if ans.transcript != 'SQL Query Submitted' else '') or "No query submitted").strip()
                elif q.type in ["pseudocode", "pseudocode_mcq"]:
                    sel_id = ans.selected_option_id or ans.selected_option
                    ans_text = f"Selected Option: {sel_id}" if sel_id else "Not answered"
                else:
                    ans_text = (ans.transcript or "No response recorded").strip()
                    if ans_text.startswith("-- Write your MySQL query"):
                        ans_text = "No response recorded"
            else:
                ans_text = "Not answered" if q.type in ["pseudocode", "pseudocode_mcq"] else "No response recorded"

            transcript_snippet = (ans_text[:150] + "...") if len(ans_text) > 150 else (ans_text or "No response recorded")
            score_val = f"{ans.technical_score}/100" if ans else "N/A"
            
            q_table_data.append([
                Paragraph(str(i + 1), normal_text),
                Paragraph(f"<b>[{str(q.type).upper()}] ({q.skill})</b><br/>{q.question[:120]}", normal_text),
                Paragraph(transcript_snippet, normal_text),
                Paragraph(f"<b>{score_val}</b>", normal_text)
            ])

        q_table = Table(q_table_data, colWidths=[25, 180, 255, 60])
        q_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(q_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
