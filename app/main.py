from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import router

app = FastAPI(title="Business Analytics Dashboard")
app.mount("/static", StaticFiles(), name = "static")
app.include_router(router)

