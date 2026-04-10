"""
PDF Generator
Creates a professional day-by-day itinerary PDF using ReportLab.
"""
import os, re
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


PRIMARY   = colors.HexColor("#003580")
ACCENT    = colors.HexColor("#0071c2")
LIGHT_BG  = colors.HexColor("#e8eef8")
GOLD      = colors.HexColor("#f5a623")
TEXT      = colors.HexColor("#1a1a2e")
MUTED     = colors.HexColor("#6b7280")
WHITE     = colors.white
GREEN     = colors.HexColor("#00865a")


def clean(text: str) -> str:
    """Remove markdown and emojis for PDF."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'^#{1,3}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Remove emojis
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'[\u2600-\u27BF]', '', text)
    text = re.sub(r'[\u2B00-\u2BFF]', '', text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text.strip()


def generate_itinerary_pdf(requirements: dict, flight_data: dict,
                            hotel_data: dict, weather_data: dict,
                            itinerary_text: str, output_path: str) -> str:
    """Generate a professional PDF itinerary. Returns path to PDF."""

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=15*mm, bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()

    # Custom styles
    s_title    = ParagraphStyle("Title2", fontName="Helvetica-Bold", fontSize=22,
                                 textColor=WHITE, alignment=TA_CENTER, spaceAfter=4)
    s_subtitle = ParagraphStyle("Sub", fontName="Helvetica", fontSize=11,
                                 textColor=colors.HexColor("#d1e3ff"), alignment=TA_CENTER)
    s_h1       = ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=14,
                                 textColor=PRIMARY, spaceBefore=12, spaceAfter=4)
    s_h2       = ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=11,
                                 textColor=ACCENT, spaceBefore=8, spaceAfter=3)
    s_body     = ParagraphStyle("Body", fontName="Helvetica", fontSize=9,
                                 textColor=TEXT, spaceAfter=3, leading=14)
    s_small    = ParagraphStyle("Small", fontName="Helvetica", fontSize=8,
                                 textColor=MUTED, spaceAfter=2)
    s_bold     = ParagraphStyle("Bold", fontName="Helvetica-Bold", fontSize=9,
                                 textColor=TEXT, spaceAfter=2)
    s_center   = ParagraphStyle("Center", fontName="Helvetica", fontSize=9,
                                 textColor=TEXT, alignment=TA_CENTER)

    story = []

    # ── COVER HEADER ──
    dest = requirements.get("destination", "Your Destination")
    origin = requirements.get("origin", "")
    checkin = requirements.get("checkin", "")
    checkout = requirements.get("checkout", "")
    nights = requirements.get("nights", 1)
    budget = requirements.get("budget", 0)
    travelers = requirements.get("travelers", 1)
    profiles = requirements.get("travelers_profiles", [])

    header_data = [[Paragraph(f"VOYAGO TRAVEL ITINERARY", s_title)]]
    header_table = Table(header_data, colWidths=[170*mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), PRIMARY),
        ("ROWPADDING", (0,0), (-1,-1), 16),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4*mm))

    # Trip summary banner
    summary_data = [[
        Paragraph(f"<b>{dest.upper()}</b>", ParagraphStyle("DS", fontName="Helvetica-Bold", fontSize=16, textColor=PRIMARY, alignment=TA_CENTER)),
        Paragraph(f"{checkin} to {checkout}<br/>{nights} nights | {travelers} traveler(s)", ParagraphStyle("DD", fontName="Helvetica", fontSize=9, textColor=MUTED, alignment=TA_CENTER)),
        Paragraph(f"Budget: ${budget:,.0f}", ParagraphStyle("DB", fontName="Helvetica-Bold", fontSize=11, textColor=GREEN, alignment=TA_CENTER)),
    ]]
    sum_table = Table(summary_data, colWidths=[65*mm, 65*mm, 40*mm])
    sum_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_BG),
        ("ROWPADDING", (0,0), (-1,-1), 10),
        ("LINEAFTER", (0,0), (1,-1), 0.5, colors.HexColor("#c5d5ea")),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 5*mm))

    # ── TRAVELER PROFILES ──
    if profiles:
        story.append(Paragraph("TRAVELER DETAILS", s_h1))
        story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BG))
        story.append(Spacer(1, 2*mm))
        t_header = [["#", "Full Name", "Age", "Gender"]]
        t_rows = [[str(i+1),
                   f"{p.get('first_name','')} {p.get('last_name','')}",
                   str(p.get('age','?')),
                   p.get('gender','?')]
                  for i, p in enumerate(profiles)]
        t_table = Table(t_header + t_rows,
                        colWidths=[10*mm, 80*mm, 30*mm, 50*mm])
        t_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), PRIMARY),
            ("TEXTCOLOR", (0,0), (-1,0), WHITE),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_BG]),
            ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#d1d5db")),
            ("ROWPADDING", (0,0), (-1,-1), 6),
        ]))
        story.append(t_table)
        story.append(Spacer(1, 5*mm))

    # ── FLIGHT & HOTEL ──
    story.append(Paragraph("BOOKING SUMMARY", s_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BG))
    story.append(Spacer(1, 2*mm))

    book_rows = []
    if flight_data.get("flights"):
        f = flight_data["flights"][0]
        book_rows.append(["Flight", f"{f['airline']} {f['flight_number']}",
                          f"${f['total_price']:,.2f}", f"{'Non-stop' if f['stops']==0 else str(f['stops'])+' stop(s)'}"])
    if hotel_data.get("hotels"):
        h = hotel_data["hotels"][0]
        rooms = hotel_data.get("rooms", 1)
        total = h["price_per_night_per_room"] * rooms * nights
        book_rows.append(["Hotel", h["name"], f"${total:,.2f}", f"{nights} nights, {rooms} room(s)"])

    if book_rows:
        bk_header = [["Type", "Details", "Cost", "Notes"]]
        bk_table = Table(bk_header + book_rows,
                         colWidths=[20*mm, 80*mm, 35*mm, 35*mm])
        bk_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), ACCENT),
            ("TEXTCOLOR", (0,0), (-1,0), WHITE),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_BG]),
            ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#d1d5db")),
            ("ROWPADDING", (0,0), (-1,-1), 7),
        ]))
        story.append(bk_table)
    story.append(Spacer(1, 5*mm))

    # ── WEATHER SUMMARY ──
    if weather_data.get("forecast"):
        story.append(Paragraph("WEATHER FORECAST", s_h1))
        story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_BG))
        story.append(Spacer(1, 2*mm))
        w_header = [["Date", "Condition", "Max/Min Temp", "Rain Chance", "Humidity"]]
        w_rows = []
        for d in weather_data["forecast"]:
            w_rows.append([
                d.get("day_name", d.get("date", "")),
                clean(d.get("condition", "")),
                f"{d.get('max_temp_c','?')}C / {d.get('min_temp_c','?')}C",
                f"{d.get('rain_chance','?')}%",
                f"{d.get('humidity','?')}%"
            ])
        w_table = Table(w_header + w_rows,
                        colWidths=[38*mm, 40*mm, 35*mm, 28*mm, 29*mm])
        w_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0369a1")),
            ("TEXTCOLOR", (0,0), (-1,0), WHITE),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, colors.HexColor("#f0f9ff")]),
            ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#bae6fd")),
            ("ROWPADDING", (0,0), (-1,-1), 6),
        ]))
        story.append(w_table)
        story.append(Spacer(1, 5*mm))

    # ── DAY-BY-DAY ITINERARY ──
    story.append(PageBreak())
    story.append(Paragraph("DAY-BY-DAY ITINERARY", s_h1))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
    story.append(Spacer(1, 3*mm))

    # Parse itinerary text into day sections
    lines = itinerary_text.split('\n')
    current_day_lines = []
    day_sections = []
    in_day = False

    for line in lines:
        stripped = line.strip()
        if re.match(r'^#{1,3}\s*Day\s+\d+', stripped, re.IGNORECASE) or re.match(r'^\*\*Day\s+\d+', stripped, re.IGNORECASE):
            if current_day_lines:
                day_sections.append('\n'.join(current_day_lines))
            current_day_lines = [stripped]
            in_day = True
        elif in_day:
            current_day_lines.append(stripped)

    if current_day_lines:
        day_sections.append('\n'.join(current_day_lines))

    if day_sections:
        for section in day_sections:
            sec_lines = section.split('\n')
            day_title = clean(sec_lines[0]) if sec_lines else "Day"

            # Day header box
            day_data = [[Paragraph(day_title, ParagraphStyle("DT", fontName="Helvetica-Bold",
                                    fontSize=11, textColor=WHITE, alignment=TA_LEFT))]]
            day_table = Table(day_data, colWidths=[170*mm])
            day_table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), ACCENT),
                ("ROWPADDING", (0,0), (-1,-1), 8),
            ]))
            story.append(day_table)

            for l in sec_lines[1:]:
                cl = clean(l)
                if not cl: continue
                if re.match(r'^(Morning|Afternoon|Evening|Night)', cl, re.IGNORECASE):
                    story.append(Paragraph(cl, s_h2))
                elif cl.startswith('-') or cl.startswith('*'):
                    story.append(Paragraph(f"  • {cl.lstrip('-* ')}", s_body))
                elif re.match(r'^\d+\.', cl):
                    story.append(Paragraph(f"  {cl}", s_body))
                elif cl.upper() == cl and len(cl) > 3:
                    story.append(Paragraph(cl, s_bold))
                else:
                    story.append(Paragraph(cl, s_body))
            story.append(Spacer(1, 4*mm))
    else:
        # Fallback: just dump cleaned text
        for line in lines:
            cl = clean(line)
            if not cl: continue
            if re.match(r'^(##|###)', line):
                story.append(Paragraph(cl, s_h1))
            elif line.strip().startswith('-') or line.strip().startswith('*'):
                story.append(Paragraph(f"  • {cl.lstrip('-* ')}", s_body))
            else:
                story.append(Paragraph(cl, s_body))

    # ── FOOTER ──
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MUTED))
    story.append(Spacer(1, 2*mm))
    generated = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    story.append(Paragraph(f"Generated by Voyago AI Travel Planner | {generated}",
                            ParagraphStyle("Footer", fontName="Helvetica", fontSize=7,
                                           textColor=MUTED, alignment=TA_CENTER)))

    doc.build(story)
    return output_path
