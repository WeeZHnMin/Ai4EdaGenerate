import base64
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from scripts.render_schematic import render_sample_bytes


ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT_DIR / "datasets" / "eda_train_smoke_5.jsonl"
STATIC_DIR = ROOT_DIR / "app" / "static"


def load_fixed_sample():
    with DATASET_PATH.open("r", encoding="utf-8") as fh:
        line = next(fh).strip()
    sample = json.loads(line)
    sample["id"] = "demo_sample"
    sample["source_template_id"] = "fixed_demo_template"
    return sample


FIXED_SAMPLE = load_fixed_sample()

app = FastAPI(title="EDA Generate Demo")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class GenerateRequest(BaseModel):
    prompt: str


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/generate")
def generate(payload: GenerateRequest):
    image_bytes = render_sample_bytes(FIXED_SAMPLE)
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    return {
        "prompt": payload.prompt,
        "message": "当前为演示模式，后端固定使用一份结构化字典生成图片。",
        "image_base64": image_b64,
        "function": FIXED_SAMPLE["output"]["function"],
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    favicon_path = STATIC_DIR / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return HTMLResponse(status_code=204, content="")
