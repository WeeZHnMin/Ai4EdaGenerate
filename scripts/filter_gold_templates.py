import json
from pathlib import Path


SOURCE_PATH = Path("思路文档") / "eda_templates_624.json"
OUTPUT_PATH = Path("思路文档") / "eda_gold_templates_v1_120.json"
DOC_PATH = Path("思路文档") / "金模板筛选说明.md"


KEEP_FAMILIES = {
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
}

KEEP_LAYOUTS = {
    "chain_horizontal",
    "chain_horizontal_compact",
    "horizontal_main_vertical_branch",
    "horizontal_main_vertical_branch_compact",
    "vertical_chain",
    "vertical_chain_compact",
    "split_branch",
    "split_branch_compact",
}


def template_index(template_id):
    return int(template_id.rsplit("_", 1)[1])


def should_keep(template):
    if template["family"] not in KEEP_FAMILIES:
        return False
    idx = template_index(template["template_id"])
    if idx > 24:
        return False
    if template["layout_type"] not in KEEP_LAYOUTS:
        return False
    return True


def build_doc(templates):
    family_counts = {}
    for item in templates:
        family_counts[item["family"]] = family_counts.get(item["family"], 0) + 1

    lines = [
        "# 金模板筛选说明",
        "",
        "## 1. 目标",
        "",
        "本文件说明第一批金模板的筛选原则。金模板不是为了覆盖全部可能电路，而是为了作为第一阶段数据集生成的稳定地基。",
        "",
        "当前目标是：",
        "",
        "- 保留基础功能明确的模板",
        "- 保留命名更标准的模板",
        "- 保留布局更稳定的模板",
        "- 控制 prompt 多样性，但避免过宽分布",
        "- 先服务于第一阶段高质量数据生成",
        "",
        "## 2. 筛选规则",
        "",
        "本次从 `eda_templates_624.json` 中筛选出第一版金模板，规则如下：",
        "",
        "- 只保留第一阶段基础功能族",
        "- 只保留每个功能族前两组命名方案",
        "- 只保留基础布局和 compact 布局",
        "- 暂不保留 mirrored 和 wide 布局",
        "- 暂不保留三极管、MOS 等第二阶段模板",
        "",
        "## 3. 保留的功能族",
        "",
        "- LED指示",
        "- RC低通滤波",
        "- RC高通滤波",
        "- LC滤波",
        "- 电源去耦",
        "- 电阻分压",
        "- 上拉按键输入",
        "- 下拉按键输入",
        "- 二极管防反接",
        "- 简单整流滤波",
        "",
        "## 4. 暂不纳入第一批金模板的功能族",
        "",
        "- 三极管LED驱动",
        "- MOS负载开关",
        "- 串联电阻负载",
        "",
        "原因：",
        "",
        "- 它们更适合第二阶段",
        "- 命名和拓扑变化更宽",
        "- 容易在第一阶段拉大任务分布",
        "",
        "## 5. 布局保留规则",
        "",
        "保留：",
        "",
        "- 基础布局",
        "- compact 布局",
        "",
        "不保留：",
        "",
        "- mirrored 布局",
        "- wide 布局",
        "",
        "这样做的原因是第一阶段先让模型学稳，不急着扩大版式变化范围。",
        "",
        "## 6. 数量统计",
        "",
        f"- 金模板总数：{len(templates)}",
        "",
        "各功能族数量：",
        "",
    ]

    for family, count in sorted(family_counts.items()):
        lines.append(f"- `{family}`: {count}")

    lines.extend(
        [
            "",
            "## 7. 使用建议",
            "",
            "第一阶段建议优先使用这批金模板生成带坐标数据。等第一版生成器、校验器和训练流程稳定后，再逐步引入：",
            "",
            "- mirrored 布局",
            "- wide 布局",
            "- 三极管驱动类模板",
            "- MOS 开关类模板",
            "- 更复杂的复合功能模板",
        ]
    )

    return "\n".join(lines) + "\n"


def main():
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    filtered = [item for item in source if should_keep(item)]

    OUTPUT_PATH.write_text(json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8")
    DOC_PATH.write_text(build_doc(filtered), encoding="utf-8")

    print(f"gold templates: {len(filtered)}")
    print(OUTPUT_PATH)
    print(DOC_PATH)


if __name__ == "__main__":
    main()
