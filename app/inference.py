import json
import threading
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_DIR = ROOT_DIR / "models" / "mt5-eda-generate"


def extract_json_object(text):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = text[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def validate_prediction(data):
    if not isinstance(data, dict):
        return False, "top-level is not a dict"

    required = {"function", "components", "edges"}
    missing = required - set(data.keys())
    if missing:
        return False, f"missing keys: {sorted(missing)}"

    components = data.get("components")
    edges = data.get("edges")

    if not isinstance(components, dict) or not components:
        return False, "components is empty or invalid"

    if not isinstance(edges, dict) or not edges:
        return False, "edges is empty or invalid"

    for node_id, node in components.items():
        if not isinstance(node, dict):
            return False, f"component is not a dict: {node_id}"
        for key in ("type", "x", "y"):
            if key not in node:
                return False, f"component missing field {key}: {node_id}"

    for edge_name, edge_value in edges.items():
        if not isinstance(edge_value, list) or len(edge_value) != 2:
            return False, f"invalid edge format: {edge_name}"
        left, right = edge_value
        if left not in components or right not in components:
            return False, f"edge references unknown nodes: {edge_name}"

    return True, "ok"


def prediction_to_sample(prediction, prompt):
    return {
        "id": "inference_sample",
        "source_template_id": "model_inference",
        "prompt": prompt,
        "output": prediction,
    }


class InferenceService:
    def __init__(self, model_dir=None, max_input_length=192, max_target_length=256):
        self.model_dir = Path(model_dir or DEFAULT_MODEL_DIR)
        self.max_input_length = max_input_length
        self.max_target_length = max_target_length

        self._status = "loading"
        self._message = "模型正在加载。"
        self._tokenizer = None
        self._model = None
        self._lock = threading.Lock()

    @property
    def status(self):
        return self._status

    @property
    def message(self):
        return self._message

    def load(self):
        try:
            if not self.model_dir.exists():
                raise FileNotFoundError(f"模型目录不存在: {self.model_dir}")

            tokenizer = AutoTokenizer.from_pretrained(self.model_dir, use_fast=False)
            model = AutoModelForSeq2SeqLM.from_pretrained(self.model_dir)
            model.eval()
            model.to("cpu")

            with self._lock:
                self._tokenizer = tokenizer
                self._model = model
                self._status = "ready"
                self._message = "模型已加载完成，可以开始推理。"
        except Exception as exc:
            with self._lock:
                self._status = "error"
                self._message = f"模型加载失败: {exc}"

    def generate(self, prompt):
        if self._status != "ready":
            raise RuntimeError(self._message)

        with self._lock:
            tokenizer = self._tokenizer
            model = self._model

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=self.max_input_length)
        inputs = {key: value.to("cpu") for key, value in inputs.items()}

        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_length=self.max_target_length,
                num_beams=1,
            )

        raw_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        parsed = extract_json_object(raw_text)

        if parsed is None:
            raise ValueError("模型输出不是合法 JSON")

        is_valid, message = validate_prediction(parsed)
        if not is_valid:
            raise ValueError(f"模型输出结构不合法: {message}")

        return raw_text, parsed
