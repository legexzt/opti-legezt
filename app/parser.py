import io
import re
import os
import json
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import openpyxl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STUDENT_MASTER_PATH = os.path.join(BASE_DIR, "student_master.json")

# Load persistent student master lookup
STUDENT_MASTER_DB: Dict[str, str] = {}
if os.path.exists(STUDENT_MASTER_PATH):
    try:
        with open(STUDENT_MASTER_PATH, "r", encoding="utf-8") as f:
            STUDENT_MASTER_DB = json.load(f)
    except Exception as e:
        print("Error loading student_master.json:", e)

import math

def clean_str(val: Any) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() == "nan" or s.lower() == "none":
        return ""
    return s

def safe_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


class SmartDataParser:
    """
    Next-generation smart file parser and merger for university grade-sheets, CIE internal test reports,
    and arbitrary student CSV / Excel files.
    """

    @staticmethod
    def inspect_file(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        is_excel = filename.lower().endswith(('.xlsx', '.xls'))
        sheet_names = []

        if is_excel:
            try:
                wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
                sheet_names = wb.sheetnames
                wb.close()
            except Exception:
                try:
                    xl = pd.ExcelFile(io.BytesIO(file_bytes))
                    sheet_names = xl.sheet_names
                except Exception:
                    sheet_names = ["Sheet1"]
        else:
            sheet_names = ["CSV Data"]

        default_sheet = sheet_names[0]
        # Prefer meaningful subject sheets over TEMP
        for s in sheet_names:
            if s.upper() not in ["TEMP", "SHEET1", "SHEET"]:
                default_sheet = s
                break

        return {
            "filename": filename,
            "is_excel": is_excel,
            "sheet_names": sheet_names,
            "default_sheet": default_sheet
        }

    @staticmethod
    def parse_sheet_data(file_bytes: bytes, filename: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        is_excel = filename.lower().endswith(('.xlsx', '.xls'))
        target_sheet = sheet_name

        if is_excel:
            file_info = SmartDataParser.inspect_file(file_bytes, filename)
            if not target_sheet or target_sheet not in file_info["sheet_names"]:
                target_sheet = file_info["default_sheet"]
            try:
                df_raw = pd.read_excel(io.BytesIO(file_bytes), sheet_name=target_sheet, header=None)
            except Exception:
                df_raw = pd.read_excel(io.BytesIO(file_bytes), header=None)
            raw_rows = df_raw.values.tolist()
        else:
            try:
                df_raw = pd.read_csv(io.BytesIO(file_bytes), header=None, encoding='utf-8')
            except Exception:
                df_raw = pd.read_csv(io.BytesIO(file_bytes), header=None, encoding='latin-1')
            raw_rows = df_raw.values.tolist()

        metadata, header_row_idx, student_rows = SmartDataParser._extract_metadata_and_split(raw_rows)
        parsed_students, summary = SmartDataParser._process_student_rows(raw_rows, header_row_idx, student_rows, metadata)
        
        return {
            "filename": filename,
            "sheet_name": target_sheet or ("CSV Data" if not is_excel else "Sheet1"),
            "metadata": metadata,
            "students": parsed_students,
            "summary": summary,
            "total_records": len(parsed_students)
        }

    @staticmethod
    def _extract_metadata_and_split(raw_rows: List[List[Any]]) -> Tuple[Dict[str, str], int, List[int]]:
        metadata = {
            "institution": "LORDS INSTITUTE OF ENGINEERING AND TECHNOLOGY",
            "department": "Department of Computer Science and Engineering",
            "academic_year": "2024-25",
            "course_name": "",
            "course_code": "",
            "class_sec": "II/C",
            "semester": "III",
            "year_sem_sec": "Class: II/C    Semester: III",
            "faculty_name": "Faculty Incharge",
            "exam_name": "Continuous Internal Evaluation (CIE-1)"
        }

        header_row_idx = -1
        for r_idx in range(min(15, len(raw_rows))):
            row = [clean_str(c) for c in raw_rows[r_idx]]
            row_str = " ".join(row).upper()

            if any(w in row_str for w in ["LORDS", "INSTITUTE", "COLLEGE", "ENGINEERING"]):
                for cell in row:
                    if len(cell) > 10 and any(w in cell.upper() for w in ["INSTITUTE", "COLLEGE", "ENGINEERING"]):
                        metadata["institution"] = cell.strip()
                        break

            if "DEPARTMENT" in row_str or "BRANCH" in row_str:
                for cell in row:
                    if "DEPARTMENT" in cell.upper():
                        metadata["department"] = cell.strip()
                    elif "BRANCH:" in cell.upper() or "BRANCH :" in cell.upper():
                        metadata["department"] = "Department of Computer Science and Engineering"

            if "SECTION-A" in row_str or "SECTION A" in row_str or "SEC-A" in row_str:
                metadata["class_sec"] = "II/A"
                metadata["year_sem_sec"] = "Class: II/A    Semester: III"
            elif "SECTION-B" in row_str or "SECTION B" in row_str or "SEC-B" in row_str:
                metadata["class_sec"] = "II/B"
                metadata["year_sem_sec"] = "Class: II/B    Semester: III"
            elif "SECTION-C" in row_str or "SECTION C" in row_str or "SEC-C" in row_str:
                metadata["class_sec"] = "II/C"
                metadata["year_sem_sec"] = "Class: II/C    Semester: III"
            elif "SECTION-D" in row_str or "SECTION D" in row_str or "SEC-D" in row_str:
                metadata["class_sec"] = "II/D"
                metadata["year_sem_sec"] = "Class: II/D    Semester: III"

            if any(y in row_str for y in ["2024-25", "2025-26", "A.Y.", "A.Y"]):
                ay_match = re.search(r'(20\d\d[-/]\d{2,4})', row_str)
                if ay_match:
                    metadata["academic_year"] = ay_match.group(1).replace('/', '-')

            # Course Name
            for c_idx, cell in enumerate(row):
                cell_up = cell.upper()
                if "COURSE NAME:" in cell_up or cell_up == "COURSE NAME":
                    for next_c in row[c_idx+1:]:
                        if next_c and "COURSE CODE" not in next_c.upper():
                            metadata["course_name"] = next_c.strip()
                            break
                if "COURSE CODE:" in cell_up or cell_up == "COURSE CODE":
                    for next_c in row[c_idx+1:]:
                        if next_c:
                            metadata["course_code"] = next_c.strip()
                            break

            matches = sum(1 for c in row if re.search(r'(S\.?NO|H\.?T\.?NO|ROLL|NAME|TOTAL|MARKS|GRADE|SGPA|CGPA|Q1|Q\.?2)', c, re.IGNORECASE))
            if matches >= 2:
                header_row_idx = r_idx
                break

        if header_row_idx == -1:
            for r_idx in range(min(10, len(raw_rows))):
                row = raw_rows[r_idx]
                for cell in row:
                    c_str = clean_str(cell)
                    if re.search(r'^(1609|1602|1604|\d{8,12})$', c_str):
                        header_row_idx = max(0, r_idx - 1)
                        break
                if header_row_idx != -1:
                    break

        if header_row_idx == -1:
            header_row_idx = 0

        student_row_indices = []
        for r_idx in range(header_row_idx + 1, len(raw_rows)):
            row = raw_rows[r_idx]
            if not any(row):
                continue
            has_roll_or_num = False
            for c in row:
                c_str = clean_str(c)
                if re.search(r'^\d{8,14}$', c_str) or re.search(r'^[0-9A-Z]{8,14}$', c_str):
                    has_roll_or_num = True
                    break
            if has_roll_or_num:
                student_row_indices.append(r_idx)
            elif any(c for c in row if isinstance(c, (int, float)) and c > 0):
                student_row_indices.append(r_idx)

        return metadata, header_row_idx, student_row_indices

    @staticmethod
    def _process_student_rows(raw_rows: List[List[Any]], header_row_idx: int, student_row_indices: List[int], metadata: Dict[str, str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        header_row = [clean_str(c) for c in raw_rows[header_row_idx]] if header_row_idx < len(raw_rows) else []
        
        roll_col = -1
        name_col = -1
        total_marks_col = -1
        sgpa_col = -1
        cgpa_col = -1

        for c_idx, h_text in enumerate(header_row):
            h_up = h_text.upper()
            if re.search(r'(H\.?T\.?NO|ROLL|HALL\s*TICKET|PIN|REG|STUDENT\s*ID)', h_up):
                roll_col = c_idx
            elif re.search(r'(NAME|STUDENT\s*NAME)', h_up):
                name_col = c_idx
            elif "TOTAL (MAX.MARKS" in h_up or "TOTAL MARKS" in h_up or h_up == "TOTAL":
                if total_marks_col == -1:
                    total_marks_col = c_idx
            elif "CGPA" in h_up:
                cgpa_col = c_idx
            elif "SGPA" in h_up or "GPA" in h_up:
                if sgpa_col == -1: sgpa_col = c_idx
                elif cgpa_col == -1: cgpa_col = c_idx

        # Deep scan across data rows to find roll and name columns
        if student_row_indices:
            # Detect roll column
            if roll_col == -1:
                for c_idx in range(len(raw_rows[student_row_indices[0]])):
                    sample_cells = [clean_str(raw_rows[r][c_idx]) for r in student_row_indices[:5] if c_idx < len(raw_rows[r])]
                    if any(re.match(r'^\d{8,14}$', cell) for cell in sample_cells):
                        roll_col = c_idx
                        break

            # Detect name column by scanning all cells for real student names
            if name_col == -1 or name_col == roll_col:
                for c_idx in range(len(raw_rows[student_row_indices[0]]) - 1, -1, -1):
                    if c_idx == roll_col: continue
                    sample_cells = [clean_str(raw_rows[r][c_idx]) for r in student_row_indices[:10] if c_idx < len(raw_rows[r])]
                    valid_names = [c for c in sample_cells if len(c) >= 3 and not re.match(r'^\d+(\.\d+)?$', c) and c.upper() not in ["PASS", "FAIL", "AB", "P", "F", "NAN", "NONE"]]
                    if len(valid_names) >= 3:
                        name_col = c_idx
                        break

            # Detect marks / CGPA columns
            if total_marks_col == -1 and sgpa_col == -1 and cgpa_col == -1:
                for c_idx in range(len(raw_rows[student_row_indices[0]])):
                    if c_idx == roll_col or c_idx == name_col: continue
                    vals = []
                    for r in student_row_indices[:10]:
                        if c_idx < len(raw_rows[r]):
                            try:
                                v = float(raw_rows[r][c_idx])
                                vals.append(v)
                            except: pass
                    if vals:
                        avg_v = sum(vals) / len(vals)
                        if max(vals) <= 10.0:
                            if sgpa_col == -1: sgpa_col = c_idx
                            elif cgpa_col == -1: cgpa_col = c_idx
                        elif max(vals) <= 30.0:
                            total_marks_col = c_idx

        students = []
        for idx, r_idx in enumerate(student_row_indices):
            row = raw_rows[r_idx]
            
            # Roll Number
            roll_num = ""
            if roll_col != -1 and roll_col < len(row):
                r_val = clean_str(row[roll_col])
                if r_val.endswith('.0'): r_val = r_val[:-2]
                roll_num = r_val
            else:
                for c in row:
                    c_s = clean_str(c)
                    if c_s.endswith('.0'): c_s = c_s[:-2]
                    if re.match(r'^\d{8,14}$', c_s):
                        roll_num = c_s
                        break

            # Student Name (lookup from master DB if missing or generic)
            student_name = ""
            if name_col != -1 and name_col < len(row):
                n_val = clean_str(row[name_col])
                if len(n_val) >= 3 and not re.match(r'^\d+(\.\d+)?$', n_val) and n_val.upper() not in ["PASS", "FAIL", "P", "F", "AB"]:
                    student_name = n_val

            if not student_name or student_name.startswith("Student "):
                # Search all columns in this row for a name string
                for c_val in row:
                    c_str = clean_str(c_val)
                    if len(c_str) >= 4 and c_str.replace(' ', '').isalpha() and c_str.upper() not in ["PASS", "FAIL", "PROMOTED", "ABSENT", "REGULAR"]:
                        student_name = c_str
                        break

            # Fallback to persistent master database
            if (not student_name or student_name.startswith("Student ")) and roll_num in STUDENT_MASTER_DB:
                student_name = STUDENT_MASTER_DB[roll_num]

            if not student_name:
                student_name = f"Student {roll_num[-4:]}" if roll_num else f"Student {idx+1}"
            else:
                # Update master database
                if roll_num and roll_num not in STUDENT_MASTER_DB:
                    STUDENT_MASTER_DB[roll_num] = student_name

            # Marks and Grades using safe_float
            cie_marks = None
            if total_marks_col != -1 and total_marks_col < len(row):
                try:
                    v = safe_float(row[total_marks_col])
                    if v is not None and 0 <= v <= 100: cie_marks = v
                except:
                    if clean_str(row[total_marks_col]).upper() in ["AB", "ABSENT"]:
                        cie_marks = 0.0

            sgpa = None
            if sgpa_col != -1 and sgpa_col < len(row):
                try: sgpa = safe_float(row[sgpa_col])
                except: pass

            cgpa = None
            if cgpa_col != -1 and cgpa_col < len(row):
                try: cgpa = safe_float(row[cgpa_col])
                except: pass

            # Backlogs
            backlog_count = 0
            for cell in row:
                c_s = clean_str(cell).upper()
                if c_s in ['F', 'FAIL', 'AB', 'ABSENT']:
                    backlog_count += 1

            students.append({
                "s_no": idx + 1,
                "roll_number": roll_num,
                "student_name": student_name,
                "cie_marks": cie_marks,
                "sgpa": sgpa,
                "cgpa": cgpa,
                "backlog_count": backlog_count,
                "observation_remarks": "Regular & Attentive" if (cie_marks and cie_marks >= 15) or (cgpa and cgpa >= 7.5) else ("Needs continuous mentoring" if (cie_marks and cie_marks < 10) or backlog_count > 0 else "Satisfactory"),
                "action_plan": "Assigned advanced projects & coding mentoring" if (cie_marks and cie_marks >= 15) or (cgpa and cgpa >= 7.5) else ("Remedial classes & question bank assigned" if (cie_marks and cie_marks < 10) or backlog_count > 0 else "Regular monitoring")
            })

        # Save updated master DB
        try:
            with open(STUDENT_MASTER_PATH, "w", encoding="utf-8") as f:
                json.dump(STUDENT_MASTER_DB, f, indent=2)
        except Exception:
            pass

        summary = {
            "total_students": len(students),
            "with_cie": sum(1 for s in students if s["cie_marks"] is not None),
            "with_cgpa": sum(1 for s in students if s["cgpa"] is not None or s["sgpa"] is not None),
            "with_backlogs": sum(1 for s in students if s["backlog_count"] > 0)
        }

        return students, summary
    @staticmethod
    def merge_multiple_datasets(dataset_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merges multiple parsed files/sheets by roll_number into a single unified master cohort.
        Prioritizes primary class cohorts when combined with branch-wide result sheets.
        """
        combined_metadata: Dict[str, Any] = {
            "institution": "LORDS INSTITUTE OF ENGINEERING AND TECHNOLOGY",
            "department": "Department of Computer Science and Engineering",
            "academic_year": "2024-25",
            "course_name": "PYTHON PROGRAMING",
            "class_sec": "II/A",
            "semester": "III",
            "year_sem_sec": "Class: II/A    Semester: III",
            "faculty_name": "Faculty Incharge"
        }

        # Check if any dataset has a specific class/section
        named_datasets = []
        for ds in dataset_list:
            if ds.get("metadata"):
                # Check for section in department / branch metadata or filename
                dept = str(ds["metadata"].get("department", ""))
                fname = str(ds.get("filename", "")).upper()
                csec = str(ds["metadata"].get("class_sec", ""))
                
                if csec and csec not in ["II/C", ""]:
                    combined_metadata["class_sec"] = csec
                    combined_metadata["year_sem_sec"] = f"Class: {csec}    Semester: {combined_metadata.get('semester', 'III')}"
                elif "SECTION-A" in dept or "SEC-A" in dept or "CSE-A" in fname or "SEC-A" in fname:
                    combined_metadata["class_sec"] = "II/A"
                    combined_metadata["year_sem_sec"] = f"Class: II/A    Semester: {combined_metadata.get('semester', 'III')}"
                elif "SECTION-B" in dept or "SEC-B" in dept or "CSE-B" in fname or "SEC-B" in fname:
                    combined_metadata["class_sec"] = "II/B"
                    combined_metadata["year_sem_sec"] = f"Class: II/B    Semester: {combined_metadata.get('semester', 'III')}"
                elif "SECTION-C" in dept or "SEC-C" in dept or "CSE-C" in fname or "SEC-C" in fname:
                    combined_metadata["class_sec"] = "II/C"
                    combined_metadata["year_sem_sec"] = f"Class: II/C    Semester: {combined_metadata.get('semester', 'III')}"
                elif "SECTION-D" in dept or "SEC-D" in dept or "CSE-D" in fname or "SEC-D" in fname:
                    combined_metadata["class_sec"] = "II/D"
                    combined_metadata["year_sem_sec"] = f"Class: II/D    Semester: {combined_metadata.get('semester', 'III')}"

                if ds["metadata"].get("course_name") and not combined_metadata.get("course_name"):
                    combined_metadata["course_name"] = ds["metadata"]["course_name"]

            # Identify datasets with real names (class rosters)
            st_list = ds.get("students", [])
            named_count = sum(1 for s in st_list if s.get("student_name") and not s["student_name"].startswith("Student "))
            if named_count >= 10 and len(st_list) <= 100:
                named_datasets.append(ds)

        # If we have a primary class roster (e.g. CSE-A with ~66 students) along with a whole-branch result sheet (300+ students),
        # use the primary class roster as the base student set and merge grades from other datasets.
        merged_students_map: Dict[str, Dict[str, Any]] = {}
        
        primary_dataset = named_datasets[0] if named_datasets else None
        
        if primary_dataset:
            # Seed with primary class roster
            for st in primary_dataset.get("students", []):
                roll = st.get("roll_number")
                if roll:
                    merged_students_map[roll] = st.copy()
            
            # Enrich from all other datasets
            for ds in dataset_list:
                if ds is primary_dataset: continue
                for st in ds.get("students", []):
                    roll = st.get("roll_number")
                    if roll in merged_students_map:
                        existing = merged_students_map[roll]
                        if (not existing.get("student_name") or existing["student_name"].startswith("Student ")) and st.get("student_name") and not st["student_name"].startswith("Student "):
                            existing["student_name"] = st["student_name"]
                        if existing.get("cie_marks") is None and st.get("cie_marks") is not None:
                            existing["cie_marks"] = st["cie_marks"]
                        if existing.get("cgpa") is None and st.get("cgpa") is not None:
                            existing["cgpa"] = st.get("cgpa")
                        if existing.get("sgpa") is None and st.get("sgpa") is not None:
                            existing["sgpa"] = st.get("sgpa")
                        if st.get("backlog_count", 0) > existing.get("backlog_count", 0):
                            existing["backlog_count"] = st["backlog_count"]
        else:
            # Union of all datasets
            for ds in dataset_list:
                for st in ds.get("students", []):
                    roll = st.get("roll_number")
                    if not roll: continue
                    if roll not in merged_students_map:
                        merged_students_map[roll] = st.copy()
                    else:
                        existing = merged_students_map[roll]
                        if (not existing.get("student_name") or existing["student_name"].startswith("Student ")) and st.get("student_name") and not st["student_name"].startswith("Student "):
                            existing["student_name"] = st["student_name"]
                        if existing.get("cie_marks") is None and st.get("cie_marks") is not None:
                            existing["cie_marks"] = st["cie_marks"]
                        if existing.get("cgpa") is None and st.get("cgpa") is not None:
                            existing["cgpa"] = st.get("cgpa")
                        if existing.get("sgpa") is None and st.get("sgpa") is not None:
                            existing["sgpa"] = st.get("sgpa")
                        if st.get("backlog_count", 0) > existing.get("backlog_count", 0):
                            existing["backlog_count"] = st["backlog_count"]

        # Ensure all names resolved from master DB
        final_students = []
        for idx, (roll, s) in enumerate(merged_students_map.items()):
            if (not s.get("student_name") or s["student_name"].startswith("Student ")) and roll in STUDENT_MASTER_DB:
                s["student_name"] = STUDENT_MASTER_DB[roll]
            s["s_no"] = idx + 1
            final_students.append(s)

        # Update metadata summary
        summary = {
            "total_students": len(final_students),
            "with_cie": sum(1 for s in final_students if s.get("cie_marks") is not None),
            "with_cgpa": sum(1 for s in final_students if s.get("cgpa") is not None or s.get("sgpa") is not None),
            "with_backlogs": sum(1 for s in final_students if s.get("backlog_count", 0) > 0)
        }

        return {
            "metadata": combined_metadata,
            "students": final_students,
            "summary": summary
        }
