import os
import sys
from app.parser import SmartDataParser
from app.classifier import PerformanceClassifier
from app.report_generator import AcademicReportGenerator

def test_all():
    print("="*60)
    print("1. TESTING SMART PARSER WITH CSE-C.xlsx")
    print("="*60)
    with open("CSE-C.xlsx", "rb") as f:
        bytes1 = f.read()
    
    info1 = SmartDataParser.inspect_file(bytes1, "CSE-C.xlsx")
    print("Sheets in CSE-C.xlsx:", info1["sheet_names"])
    
    # Parse sheet 'PP' (Python Programming)
    parsed_pp = SmartDataParser.parse_sheet_data(bytes1, "CSE-C.xlsx", "PP")
    print("Metadata extracted:", parsed_pp["metadata"])
    print(f"Total students parsed: {len(parsed_pp['students'])}")
    print("Sample student 1:", parsed_pp["students"][0])
    if len(parsed_pp["students"]) > 1:
        print("Sample student 2:", parsed_pp["students"][1])

    print("\n" + "="*60)
    print("2. TESTING CLASSIFIER")
    print("="*60)
    classified_pp = PerformanceClassifier.classify_students(parsed_pp["students"])
    stats_pp = classified_pp["statistics"]
    print("Classification Stats for PP:")
    print(f"Total: {stats_pp['total_count']}, Advanced: {stats_pp['advanced_count']} ({stats_pp['advanced_percentage']}%), Average: {stats_pp['average_count']}, Slow: {stats_pp['slow_count']} ({stats_pp['slow_percentage']}%)")

    print("\n" + "="*60)
    print("3. TESTING SMART PARSER WITH sem ii results for 24-25 2nd year use.xlsx")
    print("="*60)
    with open("sem ii results for 24-25 2nd year use.xlsx", "rb") as f:
        bytes2 = f.read()
    
    info2 = SmartDataParser.inspect_file(bytes2, "sem ii results for 24-25 2nd year use.xlsx")
    print("Sheets in sem ii results:", info2["sheet_names"])
    parsed_sem = SmartDataParser.parse_sheet_data(bytes2, "sem ii results for 24-25 2nd year use.xlsx", "Table 2")
    print(f"Total students parsed: {len(parsed_sem['students'])}")
    classified_sem = PerformanceClassifier.classify_students(parsed_sem["students"])
    stats_sem = classified_sem["statistics"]
    print("Classification Stats for Semester Results:")
    print(f"Total: {stats_sem['total_count']}, Advanced: {stats_sem['advanced_count']} ({stats_sem['advanced_percentage']}%), Average: {stats_sem['average_count']}, Slow: {stats_sem['slow_count']} ({stats_sem['slow_percentage']}%)")

    print("\n" + "="*60)
    print("4. TESTING PDF & DOCX REPORT GENERATOR")
    print("="*60)
    os.makedirs("generated_reports", exist_ok=True)
    
    # Advanced PDF & DOCX
    adv_pdf = AcademicReportGenerator.generate_pdf("advanced", parsed_pp["metadata"], classified_pp["advanced_learners"], stats_pp)
    with open("generated_reports/Test_Advanced_Learners.pdf", "wb") as f:
        f.write(adv_pdf)
    print("Generated: generated_reports/Test_Advanced_Learners.pdf (size:", len(adv_pdf), "bytes)")

    adv_docx = AcademicReportGenerator.generate_docx("advanced", parsed_pp["metadata"], classified_pp["advanced_learners"])
    with open("generated_reports/Test_Advanced_Learners.docx", "wb") as f:
        f.write(adv_docx)
    print("Generated: generated_reports/Test_Advanced_Learners.docx (size:", len(adv_docx), "bytes)")

    # Slow PDF & DOCX
    slow_pdf = AcademicReportGenerator.generate_pdf("slow", parsed_pp["metadata"], classified_pp["slow_learners"], stats_pp)
    with open("generated_reports/Test_Slow_Learners.pdf", "wb") as f:
        f.write(slow_pdf)
    print("Generated: generated_reports/Test_Slow_Learners.pdf (size:", len(slow_pdf), "bytes)")

    slow_docx = AcademicReportGenerator.generate_docx("slow", parsed_pp["metadata"], classified_pp["slow_learners"])
    with open("generated_reports/Test_Slow_Learners.docx", "wb") as f:
        f.write(slow_docx)
    print("Generated: generated_reports/Test_Slow_Learners.docx (size:", len(slow_docx), "bytes)")

    # Comprehensive PDF
    comp_pdf = AcademicReportGenerator.generate_pdf("comprehensive", parsed_pp["metadata"], classified_pp["all_students"], stats_pp)
    with open("generated_reports/Test_Comprehensive_Report.pdf", "wb") as f:
        f.write(comp_pdf)
    print("Generated: generated_reports/Test_Comprehensive_Report.pdf (size:", len(comp_pdf), "bytes)")

    print("\nALL BACKEND & REPORT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_all()
