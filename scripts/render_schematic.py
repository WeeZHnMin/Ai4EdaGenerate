import argparse
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT_DIR / "datasets" / "eda_train_smoke_5.jsonl"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "renders"
FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path(r"C:\Windows\Fonts\simsun.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
]

TYPE_COLORS = {
    "power": "#c0392b",
    "ground": "#2c3e50",
    "input": "#2980b9",
    "output": "#27ae60",
    "junction": "#8e44ad",
    "resistor": "#d35400",
    "capacitor": "#16a085",
    "inductor": "#7f8c8d",
    "diode": "#8e44ad",
    "led": "#f39c12",
    "button": "#34495e",
    "switch": "#34495e",
    "load": "#7f8c8d",
    "bjt": "#9b59b6",
    "mosfet": "#9b59b6",
}

NODE_LABELS = {
    "VCC": "电源",
    "VDD": "电源",
    "VIN": "输入",
    "VOUT": "输出",
    "OUT": "输出",
    "INPUT": "输入",
    "OUTPUT": "输出",
    "SIG_IN": "信号输入",
    "SIG_OUT": "信号输出",
    "PWR_IN": "电源输入",
    "SUPPLY": "电源",
    "GND": "接地",
    "MID": "中间节点",
    "NODE1": "中间节点",
    "LOAD": "负载",
    "RL": "负载",
    "RLOAD": "负载",
    "DEVICE": "负载",
    "U_LOAD": "负载",
    "KEY1": "按键",
    "BTN1": "按键",
    "SW1": "开关",
}

TYPE_NAMES_ZH = {
    "power": "电源",
    "ground": "接地",
    "input": "输入",
    "output": "输出",
    "junction": "中间节点",
    "resistor": "电阻",
    "capacitor": "电容",
    "inductor": "电感",
    "diode": "二极管",
    "led": "LED",
    "button": "按键",
    "switch": "开关",
    "load": "负载",
    "bjt": "三极管",
    "mosfet": "MOS管",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Render a schematic image from dataset samples.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to JSONL dataset.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for rendered PNG files.")
    parser.add_argument("--index", type=int, default=0, help="Zero-based sample index to render.")
    parser.add_argument("--count", type=int, default=1, help="Number of consecutive samples to render.")
    return parser.parse_args()


def load_samples(path):
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def font():
    for font_path in FONT_CANDIDATES:
        if font_path.exists():
            try:
                return ImageFont.truetype(str(font_path), 16)
            except OSError:
                continue
    return ImageFont.load_default()


def canvas_metrics(components):
    xs = [node["x"] for node in components.values()]
    ys = [node["y"] for node in components.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    scale = 4
    margin = 60
    width = (max_x - min_x) * scale + margin * 2 + 40
    height = (max_y - min_y) * scale + margin * 2 + 40
    return {
        "min_x": min_x,
        "min_y": min_y,
        "scale": scale,
        "margin": margin,
        "width": max(width, 320),
        "height": max(height, 240),
    }


def to_canvas(point, metrics):
    x = (point["x"] - metrics["min_x"]) * metrics["scale"] + metrics["margin"]
    y = (point["y"] - metrics["min_y"]) * metrics["scale"] + metrics["margin"]
    return int(x), int(y)


def draw_grid(draw, metrics):
    step = 40
    for x in range(0, metrics["width"], step):
        draw.line([(x, 0), (x, metrics["height"])], fill="#f2f2f2", width=1)
    for y in range(0, metrics["height"], step):
        draw.line([(0, y), (metrics["width"], y)], fill="#f2f2f2", width=1)


def draw_edges(draw, components, edges, metrics):
    for edge_name, (left, right) in edges.items():
        start = to_canvas(components[left], metrics)
        end = to_canvas(components[right], metrics)
        draw.line([start, end], fill="#444444", width=3)


def draw_nodes(draw, components, metrics, text_font):
    radius = 7
    for node_id, node in components.items():
        cx, cy = to_canvas(node, metrics)
        color = TYPE_COLORS.get(node["type"], "#555555")
        draw.ellipse(
            [(cx - radius, cy - radius), (cx + radius, cy + radius)],
            fill=color,
            outline="#222222",
            width=1,
        )
        zh_label = NODE_LABELS.get(node_id, TYPE_NAMES_ZH.get(node["type"], node_id))
        title_text = f"{zh_label}"
        draw.text((cx + 10, cy - 18), title_text, fill="#111111", font=text_font)
        coord_text = f"({node['x']},{node['y']})"
        draw.text((cx + 10, cy + 2), coord_text, fill="#666666", font=text_font)


def draw_title(draw, sample, text_font, width):
    title = f"{sample['id']} | {sample['output']['function']} | {sample['source_template_id']}"
    draw.text((20, 16), title, fill="#111111", font=text_font)
    draw.line([(20, 44), (width - 20, 44)], fill="#dddddd", width=1)


def render_sample(sample, output_path):
    image = render_sample_image(sample)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def render_sample_image(sample):
    components = sample["output"]["components"]
    edges = sample["output"]["edges"]
    metrics = canvas_metrics(components)

    image = Image.new("RGB", (metrics["width"], metrics["height"]), "white")
    draw = ImageDraw.Draw(image)
    text_font = font()

    draw_grid(draw, metrics)
    draw_title(draw, sample, text_font, metrics["width"])
    draw_edges(draw, components, edges, metrics)
    draw_nodes(draw, components, metrics, text_font)
    return image


def render_sample_bytes(sample, image_format="PNG"):
    image = render_sample_image(sample)
    buffer = io.BytesIO()
    image.save(buffer, format=image_format)
    return buffer.getvalue()


def main():
    args = parse_args()
    samples = load_samples(args.input)
    start = args.index
    end = min(start + args.count, len(samples))

    for idx in range(start, end):
        sample = samples[idx]
        output_path = args.output_dir / f"{sample['id']}.png"
        render_sample(sample, output_path)
        print(output_path)


if __name__ == "__main__":
    main()
