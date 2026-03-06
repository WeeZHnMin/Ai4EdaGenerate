import argparse
import json
from pathlib import Path

from transformers import AutoTokenizer


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = ROOT_DIR / "datasets" / "eda_train_50000.jsonl"
DEFAULT_MODEL_NAME = "google/mt5-small"


def parse_args():
    parser = argparse.ArgumentParser(description="Measure token length distribution for EDA dataset.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help="Path to JSONL dataset.")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_NAME, help="Tokenizer model name.")
    return parser.parse_args()


def percentile(sorted_values, q):
    if not sorted_values:
        return 0
    index = int((len(sorted_values) - 1) * q)
    return sorted_values[index]


def summarize(name, values):
    values = sorted(values)
    print(f"\n{name}")
    print(f"count: {len(values)}")
    print(f"min:   {values[0]}")
    print(f"p50:   {percentile(values, 0.50)}")
    print(f"p90:   {percentile(values, 0.90)}")
    print(f"p95:   {percentile(values, 0.95)}")
    print(f"p99:   {percentile(values, 0.99)}")
    print(f"max:   {values[-1]}")


def main():
    args = parse_args()
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=False)
    except ImportError as exc:
        raise SystemExit(
            "当前环境缺少 sentencepiece。请先安装：pip install sentencepiece，然后重启运行环境后再执行脚本。"
        ) from exc

    input_lengths = []
    target_lengths = []

    with args.data.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            item = json.loads(line)
            input_text = item["prompt"]
            target_text = json.dumps(item["output"], ensure_ascii=False, separators=(",", ":"))

            input_ids = tokenizer(input_text, add_special_tokens=True)["input_ids"]
            target_ids = tokenizer(target_text, add_special_tokens=True)["input_ids"]

            input_lengths.append(len(input_ids))
            target_lengths.append(len(target_ids))

    print(f"model: {args.model}")
    print(f"data:  {args.data}")
    summarize("input lengths", input_lengths)
    summarize("target lengths", target_lengths)


if __name__ == "__main__":
    main()
