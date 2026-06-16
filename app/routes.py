from fastapi import APIRouter, UploadFile, File, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
def home(request:Request):
    return templates.TemplateResponse(request, "index.html")

@router.post("/upload")
async def upload_file(file:UploadFile = File(...)):
    return {"filename": file.filename}
