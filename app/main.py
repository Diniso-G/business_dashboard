from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
#from jinja2.lexer import count_newlines

from app.routes import router
from app.auth_routes import router as ar
#from app.models import Base, engine

from fastapi.responses import JSONResponse
import traceback

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Business Analytics Dashboard")
app.mount("/static", StaticFiles(directory="static"), name = "static")
app.include_router(router)
app.include_router(ar)

@app.exception_handler(Exception)
async def debug_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"error": str(exc), "traceback": traceback.format_exc()})

