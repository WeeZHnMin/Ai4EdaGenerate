import json
from pathlib import Path


SOURCE_PATH = Path("思路文档") / "eda_templates_624.json"
OUTPUT_PATH = Path("思路文档") / "eda_template_bank_v2_480.json"
DOC_PATH = Path("思路文档") / "模板库V2说明.md"


KEEP_FAMILIES = [
    "led_indicator",
    "rc_lowpass",
    "rc_highpass",
    "lc_filter",
    "power_decoupling",
    "voltage_divider",
    "pullup_button",
    "pulldown_button",
    "reverse_protection",
    "halfwave_rectifier",
]


FAMILY_LABELS = {
    "led_indicator": "LED指示",
    "rc_lowpass": "RC低通滤波",
    "rc_highpass": "RC高通滤波",
    "lc_filter": "LC滤波",
    "power_decoupling": "电源去耦",
    "voltage_divider": "电阻分压",
    "pullup_button": "上拉按键输入",
    "pulldown_button": "下拉按键输入",
    "reverse_protection": "二极管防反接",
    "halfwave_rectifier": "简单整流滤波",
}


def load_templates():
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def build_v2(templates):
    keep = []
    for item in templates:
        if item["family"] in KEEP_FAMILIES:
            keep.append(item)
    return keep


def build_doc(templates):
    family_counts = {family: 0 for family in KEEP_FAMILIES}
    layout_counts = {}
    for item in templates:
        family_counts[item["family"]] += 1
        layout_counts[item["layout_type"]] = layout_counts.get(item["layout_type"], 0) + 1

    lines = [
        "# 模板库 V2 说明",
        "",
        "## 1. 目标",
        "",
        "本文件说明模板库 V2 的设计思路。V2 的目标不是直接成为最终数据集，而是成为后续生成 4 到 5 万条训练样本的核心模板池。",
        "",
        "相对于 V1 的 120 条金模板，V2 的重点变化是：",
        "",
        "- 保持第一阶段功能边界不变",
        "- 明显扩大命名方案覆盖",
        "- 显著扩大布局合法变体",
        "- 为大规模程序扩增提供更大的结构母体",
        "",
        "## 2. 为什么需要 V2",
        "",
        "V1 的 120 条金模板适合做：",
        "",
        "- 生成器验证",
        "- 质量校验验证",
        "- 小规模训练闭环",
        "",
        "但如果目标是 4 到 5 万条训练样本，仅靠 V1 容易产生两个问题：",
        "",
        "- 模板源头偏少，模型容易学到平均模板",
        "- 结构母体不足，扩增样本容易虚胖",
        "",
        "因此，V2 需要扩大到 400 到 600 条模板规模，使模板本身就具备更好的分布宽度。",
        "",
        "## 3. V2 的设计原则",
        "",
        "- 仍只保留第一阶段 10 类基础功能族",
        "- 引入全部 4 组命名方案",
        "- 引入全部 4 类布局子变体",
        "- 暂不引入三极管、MOS 等第二阶段功能族",
        "- 暂不引入更复杂的复合电路族",
        "",
        "## 4. V2 的规模构成",
        "",
        "V2 采用以下组合方式：",
        "",
        "- 10 个基础功能族",
        "- 每个功能族 4 组命名方案",
        "- 每组命名方案 3 个 prompt 模板",
        "- 每个 prompt 模板 4 个布局子变体",
        "",
        "因此每个功能族共有：",
        "",
        "- 4 x 3 x 4 = 48 条模板",
        "",
        "总模板数为：",
        "",
        f"- {len(templates)} 条",
        "",
        "## 5. V2 更适合扩增到大数据的原因",
        "",
        "V2 更适合后续生成 4 到 5 万条样本，原因在于：",
        "",
        "- 命名空间更宽，减少模型只记住固定节点名的风险",
        "- prompt 模板更丰富，减少输入表面形式过于单一",
        "- 布局子变体更丰富，减少坐标生成后的版式单一",
        "- 仍然保留清晰功能边界，不会把任务复杂度拉爆",
        "",
        "## 6. 建议用途",
        "",
        "建议按以下方式使用两层模板库：",
        "",
        "- V1：做高质量小规模验证和调试",
        "- V2：做大规模程序扩增的数据母体",
        "",
        "更具体地说：",
        "",
        "- V1 用于验证生成器和训练闭环",
        "- V2 用于生成主训练集",
        "",
        "## 7. 各功能族数量",
        "",
    ]

    for family in KEEP_FAMILIES:
        lines.append(f"- `{family}` / {FAMILY_LABELS[family]}: {family_counts[family]}")

    lines.extend(
        [
            "",
            "## 8. 各布局类型数量",
            "",
        ]
    )

    for layout_type, count in sorted(layout_counts.items()):
        lines.append(f"- `{layout_type}`: {count}")

    lines.extend(
        [
            "",
            "## 9. 后续建议",
            "",
            "如果 V2 扩增后的 4 到 5 万条样本仍不足以支撑目标模型，可继续做 V3，方向包括：",
            "",
            "- 加入第二阶段功能族",
            "- 加入更多等价拓扑变体",
            "- 加入更复杂的节点规模分层",
            "- 加入更细粒度的 prompt 复杂度分层",
        ]
    )

    return "\n".join(lines) + "\n"


def main():
    templates = load_templates()
    v2 = build_v2(templates)
    OUTPUT_PATH.write_text(json.dumps(v2, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(build_doc(v2), encoding="utf-8")
    print(f"v2 templates: {len(v2)}")
    print(OUTPUT_PATH)
    print(DOC_PATH)


if __name__ == "__main__":
    main()
