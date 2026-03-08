import argparse
import json
import re
from pathlib import Path


DEFAULT_INPUT = Path(
    r"C:\Users\34619\.codex\sessions\2026\03\06\rollout-2026-03-06T23-15-19-019cc3b7-aa57-78a0-9a33-d85ac3f14fe1.jsonl"
)


def parse_args():
    parser = argparse.ArgumentParser(description="Export Codex session JSONL to a readable Markdown file.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to Codex session JSONL.")
    parser.add_argument("--output", type=Path, default=None, help="Output markdown path.")
    parser.add_argument("--include-meta", action="store_true", help="Include system/developer/session metadata.")
    return parser.parse_args()


def content_to_text(content):
    parts = []
    for item in content or []:
        text = item.get("text")
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def should_keep_message(role, include_meta):
    if role in {"user", "assistant"}:
        return True
    return include_meta and role in {"developer", "system"}


def normalize_turn_aborted(text):
    if "<turn_aborted>" in text:
        return "本轮对话被用户中断。"
    return text


def redact_secrets(text):
    return re.sub(r"hf_[A-Za-z0-9]+", "[HF_TOKEN_REDACTED]", text)


def extract_messages(session_path, include_meta=False):
    messages = []
    with session_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if record.get("type") != "response_item":
                continue

            payload = record.get("payload", {})
            if payload.get("type") != "message":
                continue

            role = payload.get("role")
            if not should_keep_message(role, include_meta):
                continue

            text = content_to_text(payload.get("content", []))
            if not text:
                continue

            messages.append(
                {
                    "role": role,
                    "text": redact_secrets(normalize_turn_aborted(text)),
                }
            )
    return messages


def merge_adjacent_messages(messages):
    merged = []
    for message in messages:
        if merged and merged[-1]["role"] == message["role"]:
            merged[-1]["text"] += "\n\n" + message["text"]
            continue
        merged.append(message.copy())
    return merged


def pair_messages(messages):
    pairs = []
    pending_user_parts = []

    for message in messages:
        role = message["role"]
        text = message["text"].strip()
        if not text:
            continue

        if role == "user":
            pending_user_parts.append(text)
            continue

        if role == "assistant":
            user_text = "\n\n".join(pending_user_parts).strip() if pending_user_parts else "无明确用户输入。"
            pairs.append({"user": user_text, "assistant": text})
            pending_user_parts = []

    if pending_user_parts:
        pairs.append({"user": "\n\n".join(pending_user_parts).strip(), "assistant": "无助手回复。"})

    return pairs


def to_markdown(messages, source_path):
    pairs = pair_messages(messages)
    lines = [
        "# 对话记录",
        "",
        f"- 来源文件: `{source_path}`",
        f"- 消息条数: `{len(messages)}`",
        f"- 问答轮数: `{len(pairs)}`",
        "",
    ]

    for idx, pair in enumerate(pairs, start=1):
        lines.append(f"## 第 {idx} 轮")
        lines.append("")
        lines.append("### 用户")
        lines.append("")
        lines.append(pair["user"])
        lines.append("")
        lines.append("### 助手")
        lines.append("")
        lines.append(pair["assistant"])
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main():
    args = parse_args()
    output_path = args.output or args.input.with_suffix(".md")
    messages = extract_messages(args.input, include_meta=args.include_meta)
    messages = merge_adjacent_messages(messages)
    markdown = to_markdown(messages, args.input)
    output_path.write_text(markdown, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
