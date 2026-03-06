import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE_PATH = ROOT_DIR / "思路文档" / "eda_template_bank_v2_480.json"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "datasets" / "eda_train_50000.jsonl"

PROMPT_TEMPLATES = [
    "设计一个完成{function}功能的 EDA 原理图，包含{component_text}。请给出所有节点的坐标以及节点之间的连接关系。",
    "请生成一个用于实现{function}的基础原理图，电路节点包括{component_text}。请输出标准字典格式的节点与边信息，并包含坐标。",
    "构建一个简单的{function}电路，要求使用{component_text}。请返回带有节点坐标和 edge 连接关系的结构化结果。",
    "给出一个实现{function}的原理图样本，节点包括{component_text}。请输出标准化的 components 和 edges 数据，并标明坐标。",
]

NODE_TEXT = {
    "power": "电源 {id}",
    "ground": "接地 {id}",
    "input": "输入 {id}",
    "output": "输出 {id}",
    "junction": "中间节点 {id}",
    "resistor": "电阻 {id}",
    "capacitor": "电容 {id}",
    "inductor": "电感 {id}",
    "diode": "二极管 {id}",
    "led": "LED {id}",
    "button": "按键 {id}",
    "switch": "开关 {id}",
    "load": "负载 {id}",
    "bjt": "三极管 {id}",
    "mosfet": "MOS 管 {id}",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Generate EDA training dataset from templates.")
    parser.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATE_PATH, help="Path to template JSON.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Path to output JSONL.")
    parser.add_argument("--count", type=int, default=50000, help="Number of samples to generate.")
    parser.add_argument("--seed", type=int, default=20260307, help="Random seed.")
    return parser.parse_args()


def load_templates(path):
    return json.loads(path.read_text(encoding="utf-8"))


def component_lookup(template):
    return {item["id"]: item for item in template["components"]}


def build_adjacency(connections):
    graph = defaultdict(list)
    for left, right in connections:
        graph[left].append(right)
        graph[right].append(left)
    return graph


def layout_base_and_modifier(layout_type):
    parts = layout_type.split("_")
    if parts[-1] in {"mirrored", "compact", "wide"}:
        return "_".join(parts[:-1]), parts[-1]
    return layout_type, "default"


def spacing_for_modifier(modifier):
    if modifier == "compact":
        return 20, 20
    if modifier == "wide":
        return 40, 40
    return 30, 30


def node_priority(node_id, node):
    type_rank = {
        "power": 0,
        "input": 1,
        "junction": 2,
        "resistor": 3,
        "capacitor": 4,
        "inductor": 5,
        "diode": 6,
        "led": 7,
        "button": 8,
        "switch": 9,
        "load": 10,
        "output": 11,
        "ground": 12,
        "bjt": 13,
        "mosfet": 14,
    }
    return (type_rank.get(node["type"], 99), node_id)


def choose_start_node(components):
    preferred = []
    for node_id, node in components.items():
        if node["type"] == "power":
            preferred.append((0, node_id))
        elif node["type"] == "input":
            preferred.append((1, node_id))
        elif node["type"] == "junction":
            preferred.append((2, node_id))
        elif node["type"] == "output":
            preferred.append((3, node_id))
    if preferred:
        preferred.sort()
        return preferred[0][1]
    return sorted(components.keys())[0]


def path_from_start(start, adjacency):
    visited = set()
    order = []
    current = start
    prev = None
    while current and current not in visited:
        order.append(current)
        visited.add(current)
        candidates = [n for n in adjacency[current] if n != prev and n not in visited]
        if not candidates:
            break
        candidates.sort()
        next_node = candidates[0]
        prev, current = current, next_node
    return order


def backbone_for_chain(template, components, adjacency):
    start = choose_start_node(components)
    order = path_from_start(start, adjacency)
    if len(order) == len(components):
        return order
    remaining = [node for node in components if node not in order]
    remaining.sort(key=lambda node_id: node_priority(node_id, components[node_id]))
    return order + remaining


def backbone_for_branch(template):
    chain = []
    for left, right in template["connections"]:
        if not chain:
            chain.extend([left, right])
            continue
        if chain[-1] == left and right not in chain:
            chain.append(right)
        elif chain[-1] == right and left not in chain:
            chain.append(left)
        if len(chain) >= 3:
            break
    return chain


def place_chain_horizontal(template, components, rng, modifier):
    adjacency = build_adjacency(template["connections"])
    order = backbone_for_chain(template, components, adjacency)
    dx, dy = spacing_for_modifier(modifier)
    base_x = rng.choice([10, 20, 30])
    base_y = rng.choice([10, 20, 30, 40])
    positions = {}
    for index, node_id in enumerate(order):
        positions[node_id] = {"x": base_x + index * dx, "y": base_y}
    return positions


def place_vertical_chain(template, components, rng, modifier):
    adjacency = build_adjacency(template["connections"])
    order = backbone_for_chain(template, components, adjacency)
    dx, dy = spacing_for_modifier(modifier)
    base_x = rng.choice([20, 30, 40])
    base_y = rng.choice([10, 20, 30])
    positions = {}
    for index, node_id in enumerate(order):
        positions[node_id] = {"x": base_x, "y": base_y + index * dy}
    return positions


def place_horizontal_branch(template, components, rng, modifier):
    dx, dy = spacing_for_modifier(modifier)
    base_x = rng.choice([10, 20, 30])
    base_y = rng.choice([20, 30, 40])
    backbone = backbone_for_branch(template)
    positions = {}

    if not backbone:
        return place_chain_horizontal(template, components, rng, modifier)

    for index, node_id in enumerate(backbone):
        positions[node_id] = {"x": base_x + index * dx, "y": base_y}

    adjacency = build_adjacency(template["connections"])
    branch_index = 1
    for node_id in backbone:
        for neighbor in sorted(adjacency[node_id]):
            if neighbor in positions:
                continue
            anchor = positions[node_id]
            positions[neighbor] = {"x": anchor["x"], "y": base_y + branch_index * dy}
            branch_index += 1

            last = neighbor
            prev = node_id
            while True:
                next_nodes = [n for n in adjacency[last] if n != prev and n not in positions]
                if not next_nodes:
                    break
                next_nodes.sort()
                nxt = next_nodes[0]
                positions[nxt] = {"x": positions[last]["x"], "y": positions[last]["y"] + dy}
                prev, last = last, nxt

    remaining = [node for node in components if node not in positions]
    for node_id in sorted(remaining, key=lambda n: node_priority(n, components[n])):
        positions[node_id] = {"x": base_x + len(backbone) * dx, "y": base_y + branch_index * dy}
        branch_index += 1
    return positions


def place_split_branch(template, components, rng, modifier):
    dx, dy = spacing_for_modifier(modifier)
    base_x = rng.choice([10, 20, 30])
    base_y = rng.choice([20, 30, 40])
    positions = {}
    adjacency = build_adjacency(template["connections"])
    start = choose_start_node(components)
    positions[start] = {"x": base_x, "y": base_y}

    primary_neighbors = sorted(adjacency[start], key=lambda n: node_priority(n, components[n]))
    for index, neighbor in enumerate(primary_neighbors, start=1):
        positions[neighbor] = {"x": base_x + index * dx, "y": base_y}

    branch_index = 1
    for anchor_id in list(positions.keys()):
        for neighbor in sorted(adjacency[anchor_id], key=lambda n: node_priority(n, components[n])):
            if neighbor in positions:
                continue
            anchor = positions[anchor_id]
            direction = 1 if branch_index % 2 else -1
            positions[neighbor] = {"x": anchor["x"], "y": anchor["y"] + direction * dy}
            branch_index += 1

            last = neighbor
            prev = anchor_id
            while True:
                next_nodes = [n for n in adjacency[last] if n != prev and n not in positions]
                if not next_nodes:
                    break
                next_nodes.sort(key=lambda n: node_priority(n, components[n]))
                nxt = next_nodes[0]
                positions[nxt] = {
                    "x": positions[last]["x"],
                    "y": positions[last]["y"] + direction * dy,
                }
                prev, last = last, nxt

    remaining = [node for node in components if node not in positions]
    for node_id in sorted(remaining, key=lambda n: node_priority(n, components[n])):
        positions[node_id] = {"x": base_x + 2 * dx, "y": base_y + branch_index * dy}
        branch_index += 1
    return positions


def mirror_positions(positions):
    max_x = max(item["x"] for item in positions.values())
    min_x = min(item["x"] for item in positions.values())
    mirrored = {}
    for node_id, point in positions.items():
        mirrored[node_id] = {"x": max_x - (point["x"] - min_x), "y": point["y"]}
    return mirrored


def jitter_positions(positions, rng):
    shifted = {}
    x_offset = rng.choice([0, 10])
    y_offset = rng.choice([0, 10])
    for node_id, point in positions.items():
        shifted[node_id] = {"x": point["x"] + x_offset, "y": point["y"] + y_offset}
    return shifted


def generate_positions(template, rng):
    components = component_lookup(template)
    base_layout, modifier = layout_base_and_modifier(template["layout_type"])

    if base_layout == "chain_horizontal":
        positions = place_chain_horizontal(template, components, rng, modifier)
    elif base_layout == "vertical_chain":
        positions = place_vertical_chain(template, components, rng, modifier)
    elif base_layout == "horizontal_main_vertical_branch":
        positions = place_horizontal_branch(template, components, rng, modifier)
    elif base_layout == "split_branch":
        positions = place_split_branch(template, components, rng, modifier)
    else:
        positions = place_chain_horizontal(template, components, rng, modifier)

    if template["layout_type"].endswith("_mirrored"):
        positions = mirror_positions(positions)
    return jitter_positions(positions, rng)


def component_text(items):
    parts = [NODE_TEXT[item["type"]].format(id=item["id"]) for item in items]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return " 和 ".join(parts)
    return "、".join(parts[:-1]) + " 和 " + parts[-1]


def build_prompt(template, sample_index):
    prompt_template = PROMPT_TEMPLATES[sample_index % len(PROMPT_TEMPLATES)]
    return prompt_template.format(
        function=template["function"],
        component_text=component_text(template["components"]),
    )


def build_output(template, positions):
    components = {}
    for item in template["components"]:
        point = positions[item["id"]]
        components[item["id"]] = {
            "type": item["type"],
            "x": point["x"],
            "y": point["y"],
        }

    edges = {}
    for index, (left, right) in enumerate(template["connections"], start=1):
        edges[f"edge{index}"] = [left, right]

    return {
        "function": template["function"],
        "layout_type": template["layout_type"],
        "components": components,
        "edges": edges,
    }


def validate_sample(sample):
    output = sample["output"]
    components = output["components"]
    edges = output["edges"]

    if not sample["prompt"]:
        raise ValueError("prompt is empty")
    if not output["function"]:
        raise ValueError("function is empty")
    if not components:
        raise ValueError("components is empty")
    if not edges:
        raise ValueError("edges is empty")

    seen_coords = set()
    for node_id, node in components.items():
        if not isinstance(node["x"], int) or not isinstance(node["y"], int):
            raise ValueError(f"non-integer coordinate for {node_id}")
        coord = (node["x"], node["y"])
        if coord in seen_coords:
            raise ValueError("overlapping coordinates detected")
        seen_coords.add(coord)

    for index in range(1, len(edges) + 1):
        edge_key = f"edge{index}"
        if edge_key not in edges:
            raise ValueError("edge numbering is not continuous")
        left, right = edges[edge_key]
        if left not in components or right not in components:
            raise ValueError(f"edge references undefined node: {edge_key}")
        if left == right:
            raise ValueError(f"self-loop detected: {edge_key}")


def cycle_templates(templates):
    while True:
        for template in templates:
            yield template


def generate_samples(templates, count, seed):
    rng = random.Random(seed)
    pool = list(templates)
    rng.shuffle(pool)
    template_stream = cycle_templates(pool)

    for index in range(count):
        template = next(template_stream)
        positions = generate_positions(template, rng)
        sample = {
            "id": f"sample_{index + 1:06d}",
            "source_template_id": template["template_id"],
            "prompt": build_prompt(template, index),
            "output": build_output(template, positions),
        }
        validate_sample(sample)
        yield sample


def write_jsonl(samples, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for sample in samples:
            fh.write(json.dumps(sample, ensure_ascii=False) + "\n")


def main():
    args = parse_args()
    templates = load_templates(args.templates)
    samples = generate_samples(templates, args.count, args.seed)
    write_jsonl(samples, args.output)
    print(f"generated {args.count} samples")
    print(args.output)


if __name__ == "__main__":
    main()
