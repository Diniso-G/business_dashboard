from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
#from jinja2.lexer import count_newlines

from app.routes import router
from app.auth_routes import router as auth_router
from app.business_routes import router as business_router
from app.integration_routes import router as integration_router
from app.admin_routes import router as admin_router
#from app.models import Base, engine

from fastapi.responses import JSONResponse
import traceback, os

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

app = FastAPI(title="Business Analytics Dashboard")
app.mount("/static", StaticFiles(directory="static"), name = "static")

app.include_router(router)
app.include_router(auth_router)
app.include_router(business_router)
app.include_router(admin_router)
app.include_router(integration_router)

@app.on_event("startup")
def ensure_uploads_dir():
    os.makedirs("uploads", exist_ok=True)

@app.exception_handler(Exception)
async def debug_exception_handler(request, exc):
    if DEBUG:
        return JSONResponse(status_code=500, content={"error": str(exc), "traceback": traceback.format_exc()})
    return JSONResponse(status_code=500, content={"error": "Something went wrong. Please try again."})

if os.getenv("ENABLE_EMAIL_DIGEST", "false").lower() == "true":
    from apscheduler.schedulers.background import BackgroundScheduler
    from app.database import SessionLocal
    from.email_utils import send_all_digests

    def _weekly_digest_job():
        db= SessionLocal()
        try:
            send_all_digests(db)
        finally:
            db.close()

    scheduler = BackgroundScheduler()
    scheduler.add_job(_weekly_digest_job, "interval", weeks=1)
    scheduler.start()
    
