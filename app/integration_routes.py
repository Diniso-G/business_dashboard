import json
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report, User
from app.analytics import analyze_datafrm, generate_charts, detect_columns
from app.ai_recommendations import get_recommendations
from app.auth import get_current_user
from app.integrations import import_google_sheet, import_stripe, import_shopify

router = APIRouter(prefix="/import", tags=["integrations"])

def _finish_imports(df, source_label: str, business_id, db:Session, user: User):
    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="No data came back from that source")

    column_info = detect_columns(df)
    if column_info["mapping_required"]:
        return {"mapping_required": True, "detected_columns": column_info}

    results = analyze_datafrm(df)
    charts = generate_charts(df)
    ai_text = get_recommendations(results)

    report = Report(
        filename=source_label,
        total_revenue=results.get("total_revenue"),
        avg_order_value=results.get("avg_order_value"),
        user_id=user.id,
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

@router.post("/google-sheet")
def import_from_google_sheet(sheet_url: str = Form(...), business_id: int | None = Form(None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        df = import_google_sheet(sheet_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _finish_imports(df, "Google Sheet import", business_id, current_user, db)

@router.post("/stripe")
def import_from_stripe(secret_key: str = Form(...), start_date: str |None = Form(None), end_date: str |None = Form(None), business_id: int | None = Form(None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        df = import_stripe(secret_key, start_date, end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _finish_imports(df, "Stripe import", business_id, current_user, db)

@router.post("/shopify")
def import_from_shopidy(shop_domain: str = Form(...), access_token: str = Form(...), start_date: str |None = Form(None), end_date: str |None = Form(None), business_id: int | None = Form(None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        df = import_shopify(shop_domain, access_token, start_date, end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _finish_imports(df, f"Shopify import ({shop_domain})", business_id, current_user, db)

