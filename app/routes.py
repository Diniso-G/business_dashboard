from fastapi import APIRouter, UploadFile, File, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
def home(request:Request):
    return templates.TemplateResponse(request, "index.html")

import pandas as ps
import shutil, os
from app.analytics import analyze_datafrm
from app.models import SessionLocal, Report
from app.ai_recommendations import get_recommendations

@router.post("/upload")
async def upload_file(file:UploadFile = File(...)):
    path = f"uploads/{file.filename}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if file.filename.endswith(".csv"):
        df = ps.read_csv(path)
    else:
        df = ps.read_excel(path)
    results = analyze_datafrm(df)

    db = SessionLocal()
    try:
        report = Report(filename=file.filename, total_revenue=results.get("total_revenue"))
        db.add(report)
        db.commit()
    finally:
        db.close()

    results["ai_recommendations"] = get_recommendations(results)
    return results
    #    return {"filename": file.filename}





