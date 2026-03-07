import base64
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from scripts.render_schematic import render_sample_bytes
from app.inference import InferenceService, prediction_to_sample


ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT_DIR / "app" / "static"

app = FastAPI(title="EDA Generate Demo")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
inference_service = InferenceService()


class GenerateRequest(BaseModel):
    prompt: str


@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=inference_service.load, daemon=True)
    thread.start()


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    return {"status": "ok", "model_status": inference_service.status}


@app.get("/api/status")
def status():
    return {
        "status": inference_service.status,
        "message": inference_service.message,
    }


@app.post("/api/generate")
def generate(payload: GenerateRequest):
    if inference_service.status == "loading":
        raise HTTPException(status_code=503, detail="模型仍在加载中，请稍后再试。")
    if inference_service.status == "error":
        raise HTTPException(status_code=500, detail=inference_service.message)

    try:
        raw_text, prediction = inference_service.generate(payload.prompt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    sample = prediction_to_sample(prediction, payload.prompt)
    image_bytes = render_sample_bytes(sample)
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    return {
        "prompt": payload.prompt,
        "message": "模型推理完成，已根据输出结构生成图片。",
        "image_base64": image_b64,
        "function": prediction["function"],
        "raw_output": raw_text,
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    favicon_path = STATIC_DIR / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return HTMLResponse(status_code=204, content="")
