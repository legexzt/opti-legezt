import os
import io
import json
import re
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.parser import SmartDataParser, STUDENT_MASTER_DB
from app.classifier import PerformanceClassifier
from app.report_generator import ExactAcademicReportGenerator

app = FastAPI(title="Smart Academic Performance & Multi-File Report Studio", version="3.5")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

CURRENT_SESSION = {
    "filename": "",
    "file_bytes": b"",
    "sheet_names": [],
    "current_sheet": "",
    "metadata": {
        "institution": "LORDS INSTITUTE OF ENGINEERING AND TECHNOLOGY",
        "department": "Department of Computer Science and Engineering",
        "academic_year": "2024-25",
        "course_name": "",
        "class_sec": "II/C",
        "semester": "III",
        "year_sem_sec": "Class: II/C    Semester: III",
        "faculty_name": "Faculty Incharge"
    },
    "uploaded_files": [],
    "raw_students": [],
    "classified_data": {},
    "thresholds": PerformanceClassifier.DEFAULT_THRESHOLDS.copy(),
    "cgpa_cache": {}
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
WORKSPACE_DIR = os.path.dirname(BASE_DIR)
REPORTS_DIR = os.path.join(WORKSPACE_DIR, "generated_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def build_export_filename(report_type: str, ext: str, meta: Dict[str, Any]) -> str:
    dept_short = "CSE"
    dept_up = meta.get("department", "").upper()
    if "ECE" in dept_up: dept_short = "ECE"
    elif "MECH" in dept_up: dept_short = "MECH"
    elif "CIVIL" in dept_up: dept_short = "CIVIL"
    elif "IT" in dept_up: dept_short = "IT"

    ay = meta.get("academic_year", "2024-25").replace("/", "-").strip()
    sec = "C"
    sec_up = meta.get("class_sec", "").upper()
    if "A" in sec_up: sec = "A"
    elif "B" in sec_up: sec = "B"
    elif "C" in sec_up: sec = "C"
    elif "D" in sec_up: sec = "D"

    tier = "Advance_learners" if report_type == "advanced" else ("Slow_learners" if report_type == "slow" else "Comprehensive_Report")
    return f"{dept_short}_{ay}_{sec}_{tier}_template.{ext}"

@app.post("/api/reset")
async def reset_session():
    CURRENT_SESSION.update({
        "filename": "",
        "file_bytes": b"",
        "sheet_names": [],
        "current_sheet": "",
        "uploaded_files": [],
        "raw_students": [],
        "classified_data": {},
        "metadata": {
            "institution": "LORDS INSTITUTE OF ENGINEERING AND TECHNOLOGY",
            "department": "Department of Computer Science and Engineering",
            "academic_year": "2024-25",
            "course_name": "",
            "class_sec": "II/C",
            "semester": "III",
            "year_sem_sec": "Class: II/C    Semester: III",
            "faculty_name": "Faculty Incharge"
        }
    })
    return {"status": "success", "message": "Session reset successfully"}

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Academic Report Studio Loading...</h1>")

@app.get("/api/samples")
async def list_sample_files():
    sample_files = []
    for f in ["CSE-C.xlsx", "sem ii results for 24-25 2nd year use.xlsx"]:
        path = os.path.join(WORKSPACE_DIR, f)
        if os.path.exists(path):
            sample_files.append({
                "name": f,
                "size": os.path.getsize(path),
                "type": "CIE Internal Marks" if "CSE-C" in f else "Semester Results & SGPA"
            })
    return {"samples": sample_files}

@app.post("/api/load-sample")
async def load_sample_file(filename: str = Form(...), sheet_name: Optional[str] = Form(None)):
    path = os.path.join(WORKSPACE_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Sample file not found")
    
    with open(path, "rb") as f:
        file_bytes = f.read()

    file_info = SmartDataParser.inspect_file(file_bytes, filename)
    target_sheet = sheet_name if sheet_name else file_info["default_sheet"]
    
    parsed = SmartDataParser.parse_sheet_data(file_bytes, filename, target_sheet)
    
    # Auto enrich student names and CGPA
    for st in parsed["students"]:
        roll = st.get("roll_number")
        if roll in STUDENT_MASTER_DB and (not st.get("student_name") or st["student_name"].startswith("Student ")):
            st["student_name"] = STUDENT_MASTER_DB[roll]

    classified = PerformanceClassifier.classify_students(parsed["students"], CURRENT_SESSION["thresholds"])

    CURRENT_SESSION.update({
        "filename": filename,
        "file_bytes": file_bytes,
        "sheet_names": file_info["sheet_names"],
        "current_sheet": target_sheet,
        "metadata": {**CURRENT_SESSION["metadata"], **parsed["metadata"]},
        "raw_students": parsed["students"],
        "classified_data": classified
    })

    return {
        "status": "success",
        "file_info": file_info,
        "current_sheet": target_sheet,
        "metadata": CURRENT_SESSION["metadata"],
        "classified": classified,
        "summary": parsed["summary"]
    }

# MULTIPLE CSV / EXCEL UPLOAD HANDLER
@app.post("/api/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    all_datasets = []
    uploaded_summaries = []

    for file in files:
        b = await file.read()
        fname = file.filename
        file_info = SmartDataParser.inspect_file(b, fname)
        
        # Parse all sheets in Excel, or the single CSV
        for sname in file_info["sheet_names"]:
            parsed = SmartDataParser.parse_sheet_data(b, fname, sname)
            all_datasets.append(parsed)
            uploaded_summaries.append({
                "filename": fname,
                "sheet": sname,
                "records": len(parsed["students"])
            })

    # Merge all uploaded datasets on roll_number
    merged = SmartDataParser.merge_multiple_datasets(all_datasets)
    classified = PerformanceClassifier.classify_students(merged["students"], CURRENT_SESSION["thresholds"])

    CURRENT_SESSION.update({
        "filename": files[0].filename,
        "file_bytes": b,
        "uploaded_files": uploaded_summaries,
        "metadata": {**CURRENT_SESSION["metadata"], **merged["metadata"]},
        "raw_students": merged["students"],
        "classified_data": classified
    })

    return {
        "status": "success",
        "uploaded_files": uploaded_summaries,
        "total_merged_students": len(merged["students"]),
        "metadata": CURRENT_SESSION["metadata"],
        "classified": classified
    }

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    return await upload_multiple_files([file])

@app.post("/api/change-sheet")
async def change_sheet(sheet_name: str = Form(...)):
    if not CURRENT_SESSION["file_bytes"]:
        raise HTTPException(status_code=400, detail="No active file loaded")
    
    parsed = SmartDataParser.parse_sheet_data(CURRENT_SESSION["file_bytes"], CURRENT_SESSION["filename"], sheet_name)
    
    for st in parsed["students"]:
        roll = st.get("roll_number")
        if roll in STUDENT_MASTER_DB and (not st.get("student_name") or st["student_name"].startswith("Student ")):
            st["student_name"] = STUDENT_MASTER_DB[roll]

    classified = PerformanceClassifier.classify_students(parsed["students"], CURRENT_SESSION["thresholds"])

    CURRENT_SESSION.update({
        "current_sheet": sheet_name,
        "metadata": {**CURRENT_SESSION["metadata"], **parsed["metadata"]},
        "raw_students": parsed["students"],
        "classified_data": classified
    })

    return {
        "status": "success",
        "current_sheet": sheet_name,
        "metadata": CURRENT_SESSION["metadata"],
        "classified": classified,
        "summary": parsed["summary"]
    }

class ClassifyRequest(BaseModel):
    students: Optional[List[Dict[str, Any]]] = None
    thresholds: Optional[Dict[str, Any]] = None

@app.post("/api/classify")
async def reclassify_data(req: ClassifyRequest):
    students = req.students if req.students is not None else CURRENT_SESSION.get("raw_students", [])
    if req.thresholds:
        CURRENT_SESSION["thresholds"] = req.thresholds
    
    classified = PerformanceClassifier.classify_students(students, CURRENT_SESSION["thresholds"])
    CURRENT_SESSION["classified_data"] = classified
    return {"status": "success", "classified": classified}

class ReportGenerateRequest(BaseModel):
    report_type: str
    metadata: Dict[str, Any]
    students: List[Dict[str, Any]]
    statistics: Optional[Dict[str, Any]] = None

@app.post("/api/prepare-download")
async def prepare_download(req: ReportGenerateRequest):
    try:
        rep_type = req.report_type
        meta = req.metadata
        students = req.students
        
        pdf_name = build_export_filename(rep_type, "pdf", meta)
        docx_name = build_export_filename(rep_type, "docx", meta)
        
        pdf_bytes = ExactAcademicReportGenerator.generate_pdf(rep_type, meta, students, req.statistics)
        docx_bytes = ExactAcademicReportGenerator.generate_docx(rep_type, meta, students)
        
        with open(os.path.join(REPORTS_DIR, pdf_name), "wb") as f:
            f.write(pdf_bytes)
        with open(os.path.join(REPORTS_DIR, docx_name), "wb") as f:
            f.write(docx_bytes)

        return {
            "status": "success",
            "pdf_filename": pdf_name,
            "pdf_url": f"/download/{pdf_name}",
            "docx_filename": docx_name,
            "docx_url": f"/download/{docx_name}"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def serve_download_file(filename: str):
    file_path = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(file_path):
        rep_type = "slow" if "Slow" in filename else ("advanced" if "Advance" in filename else "comprehensive")
        meta = CURRENT_SESSION["metadata"]
        students = CURRENT_SESSION["classified_data"].get(f"{rep_type}_learners", CURRENT_SESSION["raw_students"])
        if filename.endswith(".pdf"):
            b = ExactAcademicReportGenerator.generate_pdf(rep_type, meta, students)
            with open(file_path, "wb") as f: f.write(b)
        elif filename.endswith(".docx"):
            b = ExactAcademicReportGenerator.generate_docx(rep_type, meta, students)
            with open(file_path, "wb") as f: f.write(b)
        elif filename.endswith(".xlsx"):
            import pandas as pd
            df = pd.DataFrame(students)
            df.to_excel(file_path, index=False)
        else:
            raise HTTPException(status_code=404, detail="File not found")

    media_type = "application/pdf" if filename.endswith(".pdf") else ("application/vnd.openxmlformats-officedocument.wordprocessingml.document" if filename.endswith(".docx") else "application/octet-stream")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@app.post("/api/download-direct")
async def download_direct(
    report_type: str = Form(...),
    format: str = Form("pdf"),
    metadata_json: str = Form(...),
    students_json: str = Form(...)
):
    try:
        meta = json.loads(metadata_json)
        students = json.loads(students_json)
        filename = build_export_filename(report_type, format, meta)
        file_path = os.path.join(REPORTS_DIR, filename)

        if format.lower() == "pdf":
            file_bytes = ExactAcademicReportGenerator.generate_pdf(report_type, meta, students)
            media_type = "application/pdf"
        elif format.lower() in ["docx", "doc"]:
            file_bytes = ExactAcademicReportGenerator.generate_docx(report_type, meta, students)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            import pandas as pd
            df = pd.DataFrame(students)
            df.to_excel(file_path, index=False)
            with open(file_path, "rb") as f: file_bytes = f.read()
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
