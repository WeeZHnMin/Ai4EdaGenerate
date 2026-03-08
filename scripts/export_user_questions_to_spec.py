import argparse
import json
import re
from pathlib import Path


DEFAULT_INPUT = Path(
    r"C:\Users\34619\.codex\sessions\2026\03\06\rollout-2026-03-06T23-15-19-019cc3b7-aa57-78a0-9a33-d85ac3f14fe1.jsonl"
)
DEFAULT_OUTPUT = Path(r"C:\Users\34619\Desktop\Interview\EdaGenerate\思路文档\spec.md")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export only user questions from a Codex session JSONL into a Markdown spec file."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to Codex session JSONL.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output Markdown path.")
    return parser.parse_args()


def content_to_text(content):
    parts = []
    for item in content or []:
        text = item.get("text")
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def normalize_text(text):
    if "<turn_aborted>" in text:
        return ""
    return text.strip()


def redact_secrets(text):
    return re.sub(r"hf_[A-Za-z0-9]+", "[HF_TOKEN_REDACTED]", text)


def is_real_user_prompt(text):
    if not text:
        return False

    noise_prefixes = (
        "# AGENTS.md instructions",
        "<INSTRUCTIONS>",
        "<environment_context>",
    )
    if text.startswith(noise_prefixes):
        return False

    return True


def extract_user_questions(session_path):
    questions = []
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
            if payload.get("type") != "message" or payload.get("role") != "user":
                continue

            text = redact_secrets(normalize_text(content_to_text(payload.get("content", []))))
            if not is_real_user_prompt(text):
                continue

            questions.append(text)

    return questions


def to_markdown(questions, source_path):
    lines = [
        "# 用户提问记录",
        "",
        f"- 来源文件: `{source_path}`",
        f"- 提问总数: `{len(questions)}`",
        "",
    ]

    for idx, question in enumerate(questions, start=1):
        lines.append(f"## 提问 {idx}")
        lines.append("")
        lines.append(question)
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main():
    args = parse_args()
    questions = extract_user_questions(args.input)
    markdown = to_markdown(questions, args.input)
    args.output.write_text(markdown, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
