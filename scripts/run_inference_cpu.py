import argparse
import json
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_DIR = ROOT_DIR / "models" / "mt5-eda-generate"


def parse_args():
    parser = argparse.ArgumentParser(description="Run CPU inference for the local mT5 EDA model.")
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR, help="Local model directory.")
    parser.add_argument(
        "--prompt",
        default="设计一个完成RC低通滤波功能的 EDA 原理图，包含输入 VIN、电阻 R1、输出 OUT、电容 C1 和 接地 GND。请给出所有节点的坐标以及节点之间的连接关系。",
        help="Prompt for model inference.",
    )
    parser.add_argument("--max-input-length", type=int, default=192, help="Maximum tokenizer input length.")
    parser.add_argument("--max-target-length", type=int, default=256, help="Maximum generation length.")
    parser.add_argument("--num-beams", type=int, default=1, help="Beam search width.")
    parser.add_argument("--temperature", type=float, default=1.0, help="Sampling temperature.")
    parser.add_argument("--do-sample", action="store_true", help="Enable sampling during generation.")
    return parser.parse_args()


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

    required_keys = {"function", "components", "edges"}
    missing = required_keys - set(data.keys())
    if missing:
        return False, f"missing keys: {sorted(missing)}"

    if not isinstance(data["components"], dict) or not data["components"]:
        return False, "components is empty or invalid"

    if not isinstance(data["edges"], dict) or not data["edges"]:
        return False, "edges is empty or invalid"

    for edge_name, edge_value in data["edges"].items():
        if not isinstance(edge_value, list) or len(edge_value) != 2:
            return False, f"invalid edge format: {edge_name}"
        left, right = edge_value
        if left not in data["components"] or right not in data["components"]:
            return False, f"edge references unknown nodes: {edge_name}"

    return True, "ok"


def load_model(model_dir):
    tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=False)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_dir)
    model.eval()
    model.to("cpu")
    return tokenizer, model


def generate_text(tokenizer, model, prompt, max_input_length, max_target_length, num_beams, do_sample, temperature):
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_input_length)
    inputs = {key: value.to("cpu") for key, value in inputs.items()}

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_length=max_target_length,
            num_beams=num_beams,
            do_sample=do_sample,
            temperature=temperature,
        )

    return tokenizer.decode(generated_ids[0], skip_special_tokens=True)


def main():
    args = parse_args()
    tokenizer, model = load_model(args.model_dir)

    result_text = generate_text(
        tokenizer=tokenizer,
        model=model,
        prompt=args.prompt,
        max_input_length=args.max_input_length,
        max_target_length=args.max_target_length,
        num_beams=args.num_beams,
        do_sample=args.do_sample,
        temperature=args.temperature,
    )

    parsed = extract_json_object(result_text)

    print("=== PROMPT ===")
    print(args.prompt)
    print()
    print("=== RAW OUTPUT ===")
    print(result_text)
    print()

    if parsed is None:
        print("=== PARSE STATUS ===")
        print("failed: output is not valid JSON")
        return

    is_valid, message = validate_prediction(parsed)
    print("=== PARSE STATUS ===")
    print("json parsed successfully")
    print(f"validation: {message}")
    print()
    print("=== PARSED JSON ===")
    print(json.dumps(parsed, ensure_ascii=False, indent=2))

    if is_valid:
        print()
        print("=== SUMMARY ===")
        print(f"function: {parsed['function']}")
        print(f"components: {len(parsed['components'])}")
        print(f"edges: {len(parsed['edges'])}")


if __name__ == "__main__":
    main()
