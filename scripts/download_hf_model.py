import argparse
from pathlib import Path

from huggingface_hub import snapshot_download


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_REPO_ID = "wzmmmm/mt5-eda-generate"
DEFAULT_LOCAL_DIR = ROOT_DIR / "models" / "mt5-eda-generate"


def parse_args():
    parser = argparse.ArgumentParser(description="Download a Hugging Face model snapshot to a local directory.")
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID, help="Hugging Face repository id.")
    parser.add_argument("--local-dir", type=Path, default=DEFAULT_LOCAL_DIR, help="Local target directory.")
    parser.add_argument("--revision", default="main", help="Repository revision, branch, or commit.")
    parser.add_argument("--token", default=None, help="Optional Hugging Face token for private or gated repos.")
    return parser.parse_args()


def main():
    args = parse_args()
    args.local_dir.mkdir(parents=True, exist_ok=True)

    local_path = snapshot_download(
        repo_id=args.repo_id,
        revision=args.revision,
        local_dir=str(args.local_dir),
        local_dir_use_symlinks=False,
        token=args.token,
    )

    print(f"downloaded model: {args.repo_id}")
    print(f"revision: {args.revision}")
    print(f"local path: {local_path}")


if __name__ == "__main__":
    main()
