from fastapi import APIRouter, UploadFile, File, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

import pandas as ps
import io, os, json, uuid

from app.analytics import analyze_datafrm, generate_charts, detect_columns, apply_column_mapping, merge_dataframes, compare_results

from  app.database import get_db
from app.models import Report, Business, BusinessMember, User
from app.ai_recommendations import get_recommendations, chat_about_report
from app.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024 #25MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}


@router.get("/")
def home(request:Request):
    return templates.TemplateResponse(request, "index.html")

def _safe_filename(original: str) -> str:
    ext = os.path.splitext(original)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Use .csv or .xlsx")
    return f"{uuid.uuid4().hex}{ext}"




'''
@router.post("/upload")
async def upload_file(file:UploadFile = File(...), current_user = Depends(get_current_user)):
    path = f"uploads/{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if file.filename.endswith(".csv"):
        df = ps.read_csv(path)
    else:
        df = ps.read_excel(path)
    results = analyze_datafrm(df)
    charts = generate_charts(df)

    db = SessionLocal()
    try:
        report = Report(filename=file.filename, total_revenue=results.get("total_revenue"), user_id=current_user.id)
        db.add(report)
        db.commit()
    finally:
        db.close()

    results["ai_recommendations"] = get_recommendations(results)
    results["charts"] = charts
    return results
    #    return {"filename": file.filename}

'''



