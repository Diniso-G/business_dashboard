from fastapi import APIRouter, UploadFile, File, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

import pandas as ps
import io, os, json, uuid

from app.analytics import analyze_datafrm, generate_charts, detect_columns, apply_column_mapping, merge_dataframes, compare_results

from  app.database import get_db
from app.models import Report, Business, BusinessMember, User
from app.access import user_business_ids, assert_business_access
from app.ai_recommendations import get_recommendations, chat_about_report
from app.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024 #25MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}


@router.get("/")
def home(request:Request):
    return templates.TemplateResponse(request, "login.html")

@router.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")

@router.get("/history")
def history_page(request:Request):
    return templates.TemplateResponse(request, "history.html")

@router.get("/settings")
def setting_page(request:Request):
    return templates.TemplateResponse(request, "settings.html")

def _safe_filename(original: str) -> str:
    ext = os.path.splitext(original)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Use .csv or .xlsx")
    return f"{uuid.uuid4().hex}{ext}"

async def _read_upload_to_df(file: UploadFile) -> ps.DataFrame:
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (25MB max)")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Use .csv or .xlsx")

    try:
        if ext == ".csv":
            return ps.read_csv(io.BytesIO(contents))
        return ps.read_excel(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Couldn't parse that file - is it a valid CSV/EXCEL file?")

def _assert_business_access(db: Session, business_id: int | None, user: User):
    assert_business_access(db, business_id, user)
    ''''
    if business_id is None:
        return
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    owned = business.owner_id == user.id
    member = db.query(BusinessMember).filter(BusinessMember.business_id == business_id, BusinessMember.user_id == user.id).first()
    if not (owned or member):
        raise HTTPException(status_code=403, detail="You don't have access to this business")'''

@router.post("/upload/preview")
async def upload_preview(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    df = await _read_upload_to_df(file)
    return detect_columns(df)

@router.post("/upload")
async def upload_file(files :list[UploadFile] = File(...), business_id: int | None = Form(None), column_mapping: str | None = Form(None), start_date: str | None = Form(None), end_date: str | None = Form(None), current_user = Depends(get_current_user), db: Session = Depends(get_db),):
    _assert_business_access(db, business_id, current_user)

    mapping = {}
    if column_mapping:
        try:
            mapping = json.loads(column_mapping)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="column_mapping must be valid JSON")

    dataframes = []
    filenames = []

    for f in files:
        df = await _read_upload_to_df(f)
        if mapping:
            df = apply_column_mapping(df, mapping)
        dataframes.append(df)
        filenames.append(f.filename)

    combined = merge_dataframes(dataframes)
    if combined.empty:
        raise HTTPException(status_code=400, detail="No usable rows found in the uploaded file(s)")

    column_info = detect_columns(combined)
    if column_info["mapping_required"]:
        return {
            "mapping_required": True,
            "detected_columns": column_info,
        }
    
    results = analyze_datafrm(combined, start_date, end_date)
    charts = generate_charts(combined, start_date, end_date)
    ai_text = get_recommendations(results)

    report = Report(
        filename=", ".join(filenames),
        total_revenue=results.get("total_revenue"),
        avg_order_value=results.get("avg_order_value"),
        user_id=current_user.id,
        business_id=business_id,
        results_json=json.dumps(results),
        charts_json=json.dumps(charts),
        ai_recommendations=ai_text,
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    results["ai_recommendations"] = ai_text
    results["charts"] = charts
    results["report_id"] = report.id

    return results
    #    return {"filename": file.filename}

def _report_query_for_user(db: Session, user: User, business_id: int | None = None):
    if business_id is not None:
        assert_business_access(db, business_id, user)
        q = db.query(Report).filter(Report.business_id == business_id)
    else:
        accessible = user_business_ids(db, user)
        if accessible:
            q = db.query(Report).filter(or_(Report.user_id == user.id, Report.business_id.in_(accessible)))
        else:
            q = db.query(Report).filter(Report.user_id == user.id)
    return q.order_by(Report.uploaded_at.desc())

@router.get("/reports")
def list_reports(business_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    reports = _report_query_for_user(db, current_user, business_id).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "uploaded_at": r.uploaded_at.isoformat(),
            "total_revenue": r.total_revenue,
            "avg_order_value": r.avg_order_value,
            "business_id": r.business_id,
            "uploaded_by": r.owner.email if r.owner else None,
        }
        for r in reports
    ]

def _get_owned_report(db: Session, report_id: int, user: User) -> Report:
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.business_id is not None:
        assert_business_access(db, report.business_id, user)

    elif report.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your report")
    return report

@router.get("/reports/compare")
def compare_reports(a: int, b: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    report_a = _get_owned_report(db, a, current_user)
    report_b = _get_owned_report(db, b, current_user)

    results_a = json.loads(report_a.results_json) if report_a.results_json else {}
    results_b = json.loads(report_b.results_json) if report_b.results_json else {}

    return {
        "a": {"id": a, "filename": report_a.filename, "uploaded_at": report_a.uploaded_at.isoformat()},
        "b": {"id": b, "filename": report_b.filename, "uploaded_at": report_b.uploaded_at.isoformat()},
        "comparison": compare_results(results_a, results_b),
    }

@router.get("/reports/trend")
def overall_trend(business_id: int | None = None, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    reports = _report_query_for_user(db, current_user, business_id).order_by(Report.uploaded_at.asc()).all()

    return {
        "points": [
            {
                "uploaded_at": r.uploaded_at.isoformat(),
                "filename": r.filename,
                "total_revenue": r.total_revenue,
            }
            for r in reports
        ]
    }

@router.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    report = _get_owned_report(db, report_id, current_user)
    results = json.loads(report.results_json) if report.results_json else {}
    charts = json.loads(report.charts_json) if report.charts_json else {}

    results["ai_recommendations"] = report.ai_recommendations
    results["charts"] = charts
    results["report_id"] = report.id
    results["filename"] = report.filename
    results["uploaded_at"] = report.uploaded_at.isoformat()
    return results

@router.delete("/reports/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    report = _get_owned_report(db, report_id, current_user)

    is_uploader = report.user_id == current_user.id
    is_business_owner = (report.business_id is not None and db.query(Business).filter(Business.id == report.business_id, Business.owner_id == current_user.id).first() is not None)
    if not (is_uploader or is_business_owner):
        raise HTTPException(status_code=403, detail="Only the uploader or the workspace owner can delete this report")
    db.delete(report)
    db.commit()
    return {"message": "Deleted"}

@router.get("/reports/{report_id}/exports.csv")
def export_csv(report_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    report = _get_owned_report(db, report_id, current_user)
    results = json.loads(report.results_json) if report.results_json else {}

    lines = ["metric, value"]
    for key, value in results.items():
        if isinstance(value, (dict, list)):
            continue
        lines.append(f"{key},{value}")
    csv_data = "\n".join(lines)

    return StreamingResponse(io.StringIO(csv_data), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=report_{report_id}.csv"},)

@router.get("/reports/{report_id}/export.pdf")
def export_pdf(report_id: int, db: Session = Depends(get_db), current_user= Depends(get_current_user)):
    report = _get_owned_report(db, report_id, current_user)
    results = json.loads(report.results_json) if report.results_json else {}

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 60
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Business Dashboard Report - {report.filename}")

    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Uploaded: {report.uploaded_at:%Y-%m-%d %H:%M}")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Key metrics")

    y -= 20
    c.setFont("Helvetica", 10)
    for key, value in results.items():
        if isinstance(value, (dict, list)):
            continue
        c.drawString(60, y, f"{key}: {value}")
        y -= 16
        
        if y < 100:
            c.showPage()
            y = height - 60

    if report.ai_recommendations:
        y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "AI Recommendations")
        y -= 20
        c.setFont("Helvetica", 9)
        for line in report.ai_recommendations.splitlines():
            for chunk in [line[i:i + 95] for i in range(0, max(len(line), 1), 95)]:
                c.drawString(60, y, chunk)
                y -= 13

                if y < 60:
                    c.showPage()
                    y = height - 60

    c.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"})

class ChatMessage(BaseModel):
    content: str

class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []

@router.post("/reports/{report_id}/chat")
def chat_with_report(report_id: int, payload: ChatRequest, db: Session= Depends(get_db), current_user= Depends(get_current_user)):
    report = _get_owned_report(db, report_id, current_user)
    results = json.loads(report.results_json) if report.results_json else {}
    answer = chat_about_report(results, payload.question, payload.history)

    return {"answer": answer}
