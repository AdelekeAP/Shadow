"""
CGPA Export Service - Generate CSV and PDF exports of CGPA data
"""
import csv
import io
from datetime import datetime, timezone
from fpdf import FPDF
from app.utils.pau_grading import get_classification, get_letter_grade, get_grade_point


def generate_csv(cgpa_data: dict) -> bytes:
    """
    Generate CSV export of CGPA data.

    Args:
        cgpa_data: Dict from CGPACalculator.get_user_cgpa_data()

    Returns:
        UTF-8 encoded CSV bytes

    Raises:
        ValueError: If cgpa_data is invalid or empty
    """
    if not cgpa_data or not isinstance(cgpa_data, dict):
        raise ValueError("Invalid CGPA data provided")

    semesters = cgpa_data.get("semesters")
    if semesters is None:
        semesters = []

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Semester", "Course Code", "Course Name", "Credits",
        "Score", "Grade", "Grade Points"
    ])

    for semester in semesters:
        for course in semester.get("courses", []):
            writer.writerow([
                semester.get("name", "Unknown"),
                course.get("code", ""),
                course.get("name", ""),
                course.get("credits", 0),
                round(course.get("score", 0), 2),
                course.get("grade", "N/A"),
                course.get("grade_point", 0.0),
            ])

    # Add UTF-8 BOM for Excel compatibility
    return b'\xef\xbb\xbf' + output.getvalue().encode("utf-8")


def generate_pdf(cgpa_data: dict, student_name: str) -> bytes:
    """
    Generate PDF transcript of CGPA data.

    Args:
        cgpa_data: Dict from CGPACalculator.get_user_cgpa_data()
        student_name: Student's display name

    Returns:
        PDF bytes

    Raises:
        ValueError: If cgpa_data is invalid or student_name is empty
    """
    if not cgpa_data or not isinstance(cgpa_data, dict):
        raise ValueError("Invalid CGPA data provided")

    if not student_name or not student_name.strip():
        student_name = "Student"

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    current = cgpa_data.get("current", {})
    cgpa = current.get("cgpa", 0.0)
    total_credits = current.get("total_credits", 0)
    total_courses = cgpa_data.get("total_courses", 0)
    classification = get_classification(cgpa)
    target_analysis = cgpa_data.get("target_analysis", {})

    # ── Header ──
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(15, 23, 42)  # navy-900
    pdf.cell(0, 10, "Shadow - CGPA Report", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)  # surface-400
    pdf.cell(0, 5, f"Generated on {datetime.now(timezone.utc).strftime('%B %d, %Y at %I:%M %p')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # ── Student Info ──
    pdf.set_draw_color(226, 232, 240)
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(10, pdf.get_y(), 190, 32, style="DF")

    y_start = pdf.get_y() + 4
    pdf.set_xy(14, y_start)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(90, 6, student_name)

    pdf.set_xy(14, y_start + 7)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(90, 5, f"Classification: {classification}")

    pdf.set_xy(14, y_start + 13)
    pdf.cell(90, 5, f"Total Credits: {total_credits}  |  Total Courses: {total_courses}")

    if target_analysis:
        pdf.set_xy(14, y_start + 19)
        target = target_analysis.get("target_cgpa", "N/A")
        difficulty = target_analysis.get("difficulty", "N/A")
        pdf.cell(90, 5, f"Target CGPA: {target}  |  Status: {difficulty}")

    # CGPA badge on right
    pdf.set_xy(150, y_start)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(40, 12, f"{cgpa:.2f}", align="C")

    pdf.set_xy(150, y_start + 12)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(40, 5, "Cumulative GPA", align="C")

    pdf.set_y(y_start + 30)
    pdf.ln(4)

    # ── Semester Tables ──
    semesters = cgpa_data.get("semesters", [])
    for semester in semesters:
        courses = semester.get("courses", [])
        if not courses:
            continue

        # Calculate semester GPA
        sem_credits = 0
        sem_quality_points = 0.0
        for c in courses:
            cr = c.get("credits", 0)
            sc = c.get("score", 0)
            if sc > 0 and cr > 0:
                sem_credits += cr
                sem_quality_points += get_grade_point(sc) * cr
        sem_gpa = sem_quality_points / sem_credits if sem_credits > 0 else 0.0

        # Check page space: header (8) + table header (7) + rows (6 each) + margin
        needed = 8 + 7 + len(courses) * 6 + 10
        if pdf.get_y() + needed > 270:
            pdf.add_page()

        # Semester header bar
        pdf.set_fill_color(15, 23, 42)  # navy
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(150, 8, f"  {semester.get('name', 'Unknown')}", fill=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(40, 8, f"GPA: {sem_gpa:.2f}  ", fill=True, align="R")
        pdf.ln()

        # Table header
        pdf.set_fill_color(241, 245, 249)
        pdf.set_text_color(71, 85, 105)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(28, 7, "Code", fill=True)
        pdf.cell(72, 7, "Course Name", fill=True)
        pdf.cell(20, 7, "Credits", fill=True, align="C")
        pdf.cell(22, 7, "Score", fill=True, align="C")
        pdf.cell(20, 7, "Grade", fill=True, align="C")
        pdf.cell(28, 7, "Points", fill=True, align="C")
        pdf.ln()

        # Course rows
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(30, 41, 59)
        for i, course in enumerate(courses):
            if i % 2 == 0:
                pdf.set_fill_color(255, 255, 255)
            else:
                pdf.set_fill_color(248, 250, 252)

            name = course.get("name", "")
            if len(name) > 28:
                name = name[:26] + ".."

            pdf.cell(28, 6, course.get("code", ""), fill=True)
            pdf.cell(72, 6, name, fill=True)
            pdf.cell(20, 6, str(course.get("credits", 0)), fill=True, align="C")
            pdf.cell(22, 6, f"{course.get('score', 0):.1f}", fill=True, align="C")
            pdf.cell(20, 6, course.get("grade", "N/A"), fill=True, align="C")
            pdf.cell(28, 6, f"{course.get('grade_point', 0.0):.1f}", fill=True, align="C")
            pdf.ln()

        pdf.ln(4)

    # ── Footer ──
    pdf.ln(4)
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 4, "PAU Grading: A(5.0)=70-100, B(4.0)=60-69, C(3.0)=50-59, D(2.0)=45-49, E(1.0)=40-44, F(0.0)=0-39", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 4, "This report is generated by Shadow and is for personal reference only. Not an official university transcript.", new_x="LMARGIN", new_y="NEXT")

    return pdf.output()
