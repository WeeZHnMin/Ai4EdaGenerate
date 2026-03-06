import json
from itertools import product
from pathlib import Path


PROMPT_STYLES = [
    "设计一个完成{function}功能的 EDA 原理图，包含{component_text}。请输出标准结构化字典中的节点与连接关系。",
    "请生成一个用于实现{function}的基础原理图，电路节点包括{component_text}。请返回不带坐标的结构模板。",
    "构建一个简单的{function}电路模板，要求使用{component_text}。请给出 components、connections 和 layout_type。",
]


LAYOUT_VARIANTS = {
    "chain_horizontal": [
        "chain_horizontal",
        "chain_horizontal_mirrored",
        "chain_horizontal_compact",
        "chain_horizontal_wide",
    ],
    "horizontal_main_vertical_branch": [
        "horizontal_main_vertical_branch",
        "horizontal_main_vertical_branch_mirrored",
        "horizontal_main_vertical_branch_compact",
        "horizontal_main_vertical_branch_wide",
    ],
    "vertical_chain": [
        "vertical_chain",
        "vertical_chain_mirrored",
        "vertical_chain_compact",
        "vertical_chain_wide",
    ],
    "split_branch": [
        "split_branch",
        "split_branch_mirrored",
        "split_branch_compact",
        "split_branch_wide",
    ],
}


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


def component_text(components):
    parts = [NODE_TEXT[item["type"]].format(id=item["id"]) for item in components]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return " 和 ".join(parts)
    return "、".join(parts[:-1]) + " 和 " + parts[-1]


def build_prompt(style, function_name, components):
    return style.format(function=function_name, component_text=component_text(components))


def family_led_indicator():
    packs = [
        {"power": "VCC", "res": "R1", "led": "LED1", "gnd": "GND"},
        {"power": "VDD", "res": "R1", "led": "LED1", "gnd": "GND"},
        {"power": "VIN_PWR", "res": "R_LIMIT", "led": "LED_STATUS", "gnd": "GND"},
        {"power": "PWR_IN", "res": "R_LED", "led": "LED_PWR", "gnd": "GND"},
    ]
    for idx, (pack, prompt_style, layout_type) in enumerate(
        product(packs, PROMPT_STYLES, LAYOUT_VARIANTS["chain_horizontal"]), start=1
    ):
        components = [
            {"id": pack["power"], "type": "power", "role": "power_source"},
            {"id": pack["res"], "type": "resistor", "role": "current_limit"},
            {"id": pack["led"], "type": "led", "role": "indicator"},
            {"id": pack["gnd"], "type": "ground", "role": "reference_ground"},
        ]
        yield {
            "template_id": f"led_indicator_{idx:03d}",
            "family": "led_indicator",
            "function": "LED指示",
            "description": "使用串联限流电阻驱动 LED，形成最基础的指示电路。",
            "components": components,
            "connections": [
                [pack["power"], pack["res"]],
                [pack["res"], pack["led"]],
                [pack["led"], pack["gnd"]],
            ],
            "layout_type": layout_type,
            "prompt_template": build_prompt(prompt_style, "LED指示", components),
        }


def family_rc_lowpass():
    packs = [
        {"vin": "VIN", "res": "R1", "out": "OUT", "cap": "C1", "gnd": "GND"},
        {"vin": "SIG_IN", "res": "R1", "out": "VOUT", "cap": "C1", "gnd": "GND"},
        {"vin": "AIN", "res": "R_FILTER", "out": "AOUT", "cap": "C_FILTER", "gnd": "GND"},
        {"vin": "INPUT", "res": "RLP1", "out": "OUTPUT", "cap": "CLP1", "gnd": "GND"},
    ]
    for idx, (pack, prompt_style, layout_type) in enumerate(
        product(packs, PROMPT_STYLES, LAYOUT_VARIANTS["horizontal_main_vertical_branch"]), start=1
    ):
        components = [
            {"id": pack["vin"], "type": "input", "role": "signal_input"},
            {"id": pack["res"], "type": "resistor", "role": "series_resistor"},
            {"id": pack["out"], "type": "output", "role": "filtered_output"},
            {"id": pack["cap"], "type": "capacitor", "role": "shunt_capacitor"},
            {"id": pack["gnd"], "type": "ground", "role": "reference_ground"},
        ]
        yield {
            "template_id": f"rc_lowpass_{idx:03d}",
            "family": "rc_lowpass",
            "function": "RC低通滤波",
            "description": "输入经串联电阻到输出，输出节点通过电容接地，构成基础 RC 低通结构。",
            "components": components,
            "connections": [
                [pack["vin"], pack["res"]],
                [pack["res"], pack["out"]],
                [pack["out"], pack["cap"]],
                [pack["cap"], pack["gnd"]],
            ],
            "layout_type": layout_type,
            "prompt_template": build_prompt(prompt_style, "RC低通滤波", components),
        }


def family_rc_highpass():
    packs = [
        {"vin": "VIN", "cap": "C1", "out": "OUT", "res": "R1", "gnd": "GND"},
        {"vin": "SIG_IN", "cap": "C_HP", "out": "VOUT", "res": "R_HP", "gnd": "GND"},
        {"vin": "AIN", "cap": "C1", "out": "AOUT", "res": "R_LOAD", "gnd": "GND"},
        {"vin": "INPUT", "cap": "CHP1", "out": "OUTPUT", "res": "RHP1", "gnd": "GND"},
    ]
    for idx, (pack, prompt_style, layout_type) in enumerate(
        product(packs, PROMPT_STYLES, LAYOUT_VARIANTS["horizontal_main_vertical_branch"]), start=1
    ):
        components = [
            {"id": pack["vin"], "type": "input", "role": "signal_input"},
            {"id": pack["cap"], "type": "capacitor", "role": "series_capacitor"},
            {"id": pack["out"], "type": "output", "role": "filtered_output"},
            {"id": pack["res"], "type": "resistor", "role": "pull_down_resistor"},
            {"id": pack["gnd"], "type": "ground", "role": "reference_ground"},
        ]
        yield {
            "template_id": f"rc_highpass_{idx:03d}",
            "family": "rc_highpass",
            "function": "RC高通滤波",
            "description": "输入经串联电容耦合到输出，输出通过电阻接地，形成基础 RC 高通结构。",
            "components": components,
            "connections": [
                [pack["vin"], pack["cap"]],
                [pack["cap"], pack["out"]],
                [pack["out"], pack["res"]],
                [pack["res"], pack["gnd"]],
            ],
            "layout_type": layout_type,
            "prompt_template": build_prompt(prompt_style, "RC高通滤波", components),
        }


def family_lc_filter():
    packs = [
        {"power": "VIN", "ind": "L1", "out": "OUT", "cap": "C1", "gnd": "GND"},
        {"power": "VCC", "ind": "L_FILTER", "out": "VOUT", "cap": "C_FILTER", "gnd": "GND"},
        {"power": "PWR_IN", "ind": "LMAIN", "out": "LOAD_IN", "cap": "CMAIN", "gnd": "GND"},
        {"power": "SUPPLY", "ind": "L1", "out": "OUTPUT", "cap": "C1", "gnd": "GND"},
    ]
    for idx, (pack, prompt_style, layout_type) in enumerate(
        product(packs, PROMPT_STYLES, LAYOUT_VARIANTS["horizontal_main_vertical_branch"]), start=1
    ):
        components = [
            {"id": pack["power"], "type": "power", "role": "power_input"},
            {"id": pack["ind"], "type": "inductor", "role": "series_inductor"},
            {"id": pack["out"], "type": "output", "role": "filtered_output"},
            {"id": pack["cap"], "type": "capacitor", "role": "shunt_capacitor"},
            {"id": pack["gnd"], "type": "ground", "role": "reference_ground"},
        ]
        yield {
            "template_id": f"lc_filter_{idx:03d}",
            "family": "lc_filter",
            "function": "LC滤波",
            "description": "电源或信号先经过串联电感，再由输出节点通过电容接地，构成基础 LC 滤波。",
            "components": components,
            "connections": [
                [pack["power"], pack["ind"]],
                [pack["ind"], pack["out"]],
                [pack["out"], pack["cap"]],
                [pack["cap"], pack["gnd"]],
            ],
            "layout_type": layout_type,
            "prompt_template": build_prompt(prompt_style, "LC滤波", components),
        }


def family_power_decoupling():
    packs = [
        {"power": "VCC", "load": "LOAD", "cap": "C1", "gnd": "GND"},
        {"power": "VDD", "load": "U_LOAD", "cap": "C_DECOUPLE", "gnd": "GND"},
        {"power": "PWR_IN", "load": "MCU_PWR", "cap": "C_BYPASS", "gnd": "GND"},
        {"power": "SUPPLY", "load": "IC_PWR", "cap": "C1", "gnd": "GND"},
    ]
    for idx, (pack, prompt_style, layout_type) in enumerate(
        product(packs, PROMPT_STYLES, LAYOUT_VARIANTS["split_branch"]), start=1
    ):
        components = [
            {"id": pack["power"], "type": "power", "role": "power_source"},
            {"id": pack["load"], "type": "load", "role": "powered_load"},
            {"id": pack["cap"], "type": "capacitor", "role": "decoupling_capacitor"},
            {"id": pack["gnd"], "type": "ground", "role": "reference_ground"},
        ]
        yield {
            "template_id": f"power_decoupling_{idx:03d}",
            "family": "power_decoupling",
            "function": "电源去耦",
            "description": "电源直接供给负载，同时并联一个去耦电容到地，用于旁路高频噪声。",
            "components": components,
            "connections": [
                [pack["power"], pack["load"]],
                [pack["power"], pack["cap"]],
                [pack["cap"], pack["gnd"]],
            ],
            "layout_type": layout_type,
            "prompt_template": build_prompt(prompt_style, "电源去耦", components),
        }


def family_voltage_divider():
    packs = [
        {"power": "VCC", "r1": "R1", "mid": "MID", "r2": "R2", "gnd": "GND", "out": "OUT"},
        {"power": "VIN", "r1": "R_TOP", "mid": "MID", "r2": "R_BOTTOM", "gnd": "GND", "out": "VOUT"},
        {"power": "VDD", "r1": "R_A", "mid": "NODE1", "r2": "R_B", "gnd": "GND", "out": "SIG_OUT"},
        {"power": "SUPPLY", "r1": "RUP", "mid": "MID", "r2": "RDOWN", "gnd": "GND", "out": "OUT"},
    ]
    for idx, (pack, prompt_style, layout_type) in enumerate(
        product(packs, PROMPT_STYLES, LAYOUT_VARIANTS["vertical_chain"]), start=1
    ):
        components = [
            {"id": pack["power"], "type": "power", "role": "power_source"},
            {"id": pack["r1"], "type": "resistor", "role": "upper_resistor"},
            {"id": pack["mid"], "type": "junction", "role": "divider_midpoint"},
            {"id": pack["r2"], "type": "resistor", "role": "lower_resistor"},
            {"id": pack["gnd"], "type": "ground", "role": "reference_ground"},
            {"id": pack["out"], "type": "output", "role": "divider_output"},
        ]
        yield {
            "template_id": f"voltage_divider_{idx:03d}",
            "family": "voltage_divider",
            "function": "电阻分压",
            "description": "两个串联电阻在电源与地之间构成分压，中间抽头作为输出。",
            "components": components,
            "connections": [
                [pack["power"], pack["r1"]],
                [pack["r1"], pack["mid"]],
                [pack["mid"], pack["r2"]],
                [pack["r2"], pack["gnd"]],
                [pack["mid"], pack["out"]],
            ],
            "layout_type": layout_type,
            "prompt_template": build_prompt(prompt_style, "电阻分压", components),
        }


def family_pullup_button():
    packs = [
        {"power": "VCC", "res": "R1", "node": "KEY_IN", "btn": "KEY1", "gnd": "GND", "out": "OUT"},
        {"power": "VDD", "res": "R_PULLUP", "node": "BTN_NODE", "btn": "BTN1", "gnd": "GND", "out": "SIG_OUT"},
        {"power": "VIN", "res": "RPU1", "node": "NODE1", "btn": "SW1", "gnd": "GND", "out": "MCU_IN"},
        {"power": "SUPPLY", "res": "R1", "node": "KEY_SIG", "btn": "KEY1", "gnd": "GND", "out": "OUT"},
    ]
    for idx, (pack, prompt_style, layout_type) in enumerate(
        product(packs, PROMPT_STYLES, LAYOUT_VARIANTS["split_branch"]), start=1
    ):
        components = [
            {"id": pack["power"], "type": "power", "role": "power_source"},
            {"id": pack["res"], "type": "resistor", "role": "pullup_resistor"},
            {"id": pack["node"], "type": "junction", "role": "button_node"},
            {"id": pack["btn"], "type": "button", "role": "momentary_button"},
            {"id": pack["gnd"], "type": "ground", "role": "reference_ground"},
            {"id": pack["out"], "type": "output", "role": "button_output"},
        ]
        yield {
            "template_id": f"pullup_button_{idx:03d}",
            "family": "pullup_button",
            "function": "上拉按键输入",
            "description": "节点通过电阻上拉到电源，按键按下时将节点拉到地，用于按键输入检测。",
            "components": components,
            "connections": [
                [pack["power"], pack["res"]],
                [pack["res"], pack["node"]],
                [pack["node"], pack["btn"]],
                [pack["btn"], pack["gnd"]],
                [pack["node"], pack["out"]],
            ],
            "layout_type": layout_type,
            "prompt_template": build_prompt(prompt_style, "上拉按键输入", components),
        }


def family_pulldown_button():
    packs = [
        {"power": "VCC", "btn": "KEY1", "node": "KEY_IN", "res": "R1", "gnd": "GND", "out": "OUT"},
        {"power": "VDD", "btn": "BTN1", "node": "BTN_NODE", "res": "R_PULLDOWN", "gnd": "GND", "out": "SIG_OUT"},
        {"power": "VIN", "btn": "SW1", "node": "NODE1", "res": "RPD1", "gnd": "GND", "out": "MCU_IN"},
        {"power": "SUPPLY", "btn": "KEY1", "node": "KEY_SIG", "res": "R1", "gnd": "GND", "out": "OUT"},
    ]
    for idx, (pack, prompt_style, layout_type) in enumerate(
        product(packs, PROMPT_STYLES, LAYOUT_VARIANTS["split_branch"]), start=1
    ):
        components = [
            {"id": pack["power"], "type": "power", "role": "power_source"},
            {"id": pack["btn"], "type": "button", "role": "momentary_button"},
            {"id": pack["node"], "type": "junction", "role": "button_node"},
            {"id": pack["res"], "type": "resistor", "role": "pulldown_resistor"},
            {"id": pack["gnd"], "type": "ground", "role": "reference_ground"},
            {"id": pack["out"], "type": "output", "role": "button_output"},
        ]
        yield {
            "template_id": f"pulldown_button_{idx:03d}",
            "family": "pulldown_button",
            "function": "下拉按键输入",
            "description": "节点通过电阻下拉到地，按键按下时将节点拉到电源，用于按键输入检测。",
            "components": components,
            "connections": [
                [pack["power"], pack["btn"]],
                [pack["btn"], pack["node"]],
                [pack["node"], pack["res"]],
                [pack["res"], pack["gnd"]],
                [pack["node"], pack["out"]],
            ],
            "layout_type": layout_type,
            "prompt_template": build_prompt(prompt_style, "下拉按键输入", components),
        }


def family_reverse_protection():
    packs = [
        {"vin": "VIN", "dio": "D1", "vout": "VOUT", "load": "LOAD", "gnd": "GND"},
        {"vin": "PWR_IN", "dio": "D_PROTECT", "vout": "PWR_SAFE", "load": "U_LOAD", "gnd": "GND"},
        {"vin": "SUPPLY", "dio": "D1", "vout": "SAFE_OUT", "load": "IC_PWR", "gnd": "GND"},
        {"vin": "BAT_IN", "dio": "D_REV", "vout": "BAT_SAFE", "load": "LOAD", "gnd": "GND"},
    ]
    for idx, (pack, prompt_style, layout_type) in enumerate(
        product(packs, PROMPT_STYLES, LAYOUT_VARIANTS["chain_horizontal"]), start=1
    ):
        components = [
            {"id": pack["vin"], "type": "power", "role": "raw_power_input"},
            {"id": pack["dio"], "type": "diode", "role": "reverse_protection_diode"},
            {"id": pack["vout"], "type": "output", "role": "protected_power_output"},
            {"id": pack["load"], "type": "load", "role": "powered_load"},
            {"id": pack["gnd"], "type": "ground", "role": "reference_ground"},
        ]
        yield {
            "template_id": f"reverse_protection_{idx:03d}",
            "family": "reverse_protection",
            "function": "二极管防反接",
            "description": "输入电源经过串联二极管后再供给后级负载，用于最基础的反接保护。",
            "components": components,
            "connections": [
                [pack["vin"], pack["dio"]],
                [pack["dio"], pack["vout"]],
                [pack["vout"], pack["load"]],
                [pack["load"], pack["gnd"]],
            ],
            "layout_type": layout_type,
            "prompt_template": build_prompt(prompt_style, "二极管防反接", components),
        }


def family_halfwave_rectifier():
    packs = [
        {"vin": "VIN_AC", "dio": "D1", "out": "VRECT", "cap": "C1", "load": "LOAD", "gnd": "GND"},
        {"vin": "AC_IN", "dio": "D_RECT", "out": "DC_OUT", "cap": "C_FILTER", "load": "RL", "gnd": "GND"},
        {"vin": "SIG_AC", "dio": "D1", "out": "RECT_OUT", "cap": "C1", "load": "LOAD", "gnd": "GND"},
        {"vin": "INPUT_AC", "dio": "D_HALF", "out": "VDC", "cap": "C_SMOOTH", "load": "RLOAD", "gnd": "GND"},
    ]
    for idx, (pack, prompt_style, layout_type) in enumerate(
        product(packs, PROMPT_STYLES, LAYOUT_VARIANTS["horizontal_main_vertical_branch"]), start=1
    ):
        components = [
            {"id": pack["vin"], "type": "input", "role": "ac_input"},
            {"id": pack["dio"], "type": "diode", "role": "rectifier_diode"},
            {"id": pack["out"], "type": "output", "role": "rectified_output"},
            {"id": pack["cap"], "type": "capacitor", "role": "filter_capacitor"},
            {"id": pack["load"], "type": "load", "role": "dc_load"},
            {"id": pack["gnd"], "type": "ground", "role": "reference_ground"},
        ]
        yield {
            "template_id": f"halfwave_rectifier_{idx:03d}",
            "family": "halfwave_rectifier",
            "function": "简单整流滤波",
            "description": "交流输入通过单个二极管整流，再用电容滤波并驱动负载，形成基础整流滤波结构。",
            "components": components,
            "connections": [
                [pack["vin"], pack["dio"]],
                [pack["dio"], pack["out"]],
                [pack["out"], pack["cap"]],
                [pack["cap"], pack["gnd"]],
                [pack["out"], pack["load"]],
                [pack["load"], pack["gnd"]],
            ],
            "layout_type": layout_type,
            "prompt_template": build_prompt(prompt_style, "简单整流滤波", components),
        }


def family_bjt_led_driver():
    packs = [
        {"vin": "VIN", "rb": "R1", "base": "BASE", "q": "Q1", "led": "LED1", "rled": "R2", "vcc": "VCC", "gnd": "GND"},
        {"vin": "CTRL_IN", "rb": "R_BASE", "base": "B_NODE", "q": "Q1", "led": "LED_STATUS", "rled": "R_LED", "vcc": "VDD", "gnd": "GND"},
        {"vin": "SIG_IN", "rb": "RB1", "base": "BASE", "q": "QDRIVE", "led": "LED1", "rled": "RLIM", "vcc": "SUPPLY", "gnd": "GND"},
        {"vin": "MCU_OUT", "rb": "R1", "base": "NODE1", "q": "Q1", "led": "LED_DRV", "rled": "R2", "vcc": "VCC", "gnd": "GND"},
    ]
    for idx, (pack, prompt_style, layout_type) in enumerate(
        product(packs, PROMPT_STYLES, LAYOUT_VARIANTS["split_branch"]), start=1
    ):
        components = [
            {"id": pack["vin"], "type": "input", "role": "control_input"},
            {"id": pack["rb"], "type": "resistor", "role": "base_resistor"},
            {"id": pack["base"], "type": "junction", "role": "base_node"},
            {"id": pack["q"], "type": "bjt", "role": "switch_transistor"},
            {"id": pack["led"], "type": "led", "role": "indicator"},
            {"id": pack["rled"], "type": "resistor", "role": "current_limit"},
            {"id": pack["vcc"], "type": "power", "role": "power_source"},
            {"id": pack["gnd"], "type": "ground", "role": "reference_ground"},
        ]
        yield {
            "template_id": f"bjt_led_driver_{idx:03d}",
            "family": "bjt_led_driver",
            "function": "三极管LED驱动",
            "description": "控制输入经基极电阻驱动三极管，三极管控制串联限流电阻和 LED 的导通。",
            "components": components,
            "connections": [
                [pack["vin"], pack["rb"]],
                [pack["rb"], pack["base"]],
                [pack["base"], pack["q"]],
                [pack["vcc"], pack["rled"]],
                [pack["rled"], pack["led"]],
                [pack["led"], pack["q"]],
                [pack["q"], pack["gnd"]],
            ],
            "layout_type": layout_type,
            "prompt_template": build_prompt(prompt_style, "三极管LED驱动", components),
        }


def family_mosfet_load_switch():
    packs = [
        {"vin": "CTRL_IN", "rg": "R1", "gate": "GATE", "mos": "M1", "load": "LOAD", "vcc": "VCC", "gnd": "GND"},
        {"vin": "MCU_OUT", "rg": "R_GATE", "gate": "G_NODE", "mos": "Q1", "load": "RL", "vcc": "VDD", "gnd": "GND"},
        {"vin": "SIG_IN", "rg": "RG1", "gate": "GATE", "mos": "M_SWITCH", "load": "DEVICE", "vcc": "SUPPLY", "gnd": "GND"},
        {"vin": "EN", "rg": "R1", "gate": "NODE1", "mos": "M1", "load": "LOAD1", "vcc": "VIN_PWR", "gnd": "GND"},
    ]
    for idx, (pack, prompt_style, layout_type) in enumerate(
        product(packs, PROMPT_STYLES, LAYOUT_VARIANTS["split_branch"]), start=1
    ):
        components = [
            {"id": pack["vin"], "type": "input", "role": "control_input"},
            {"id": pack["rg"], "type": "resistor", "role": "gate_resistor"},
            {"id": pack["gate"], "type": "junction", "role": "gate_node"},
            {"id": pack["mos"], "type": "mosfet", "role": "switch_device"},
            {"id": pack["load"], "type": "load", "role": "controlled_load"},
            {"id": pack["vcc"], "type": "power", "role": "power_source"},
            {"id": pack["gnd"], "type": "ground", "role": "reference_ground"},
        ]
        yield {
            "template_id": f"mosfet_load_switch_{idx:03d}",
            "family": "mosfet_load_switch",
            "function": "MOS负载开关",
            "description": "控制输入通过栅极电阻控制 MOS 管导通，从而控制负载与地之间的回路。",
            "components": components,
            "connections": [
                [pack["vin"], pack["rg"]],
                [pack["rg"], pack["gate"]],
                [pack["gate"], pack["mos"]],
                [pack["vcc"], pack["load"]],
                [pack["load"], pack["mos"]],
                [pack["mos"], pack["gnd"]],
            ],
            "layout_type": layout_type,
            "prompt_template": build_prompt(prompt_style, "MOS负载开关", components),
        }


def family_resistor_load():
    packs = [
        {"vcc": "VCC", "res": "R1", "load": "LOAD", "gnd": "GND"},
        {"vcc": "VDD", "res": "R_LIMIT", "load": "RL", "gnd": "GND"},
        {"vcc": "VIN_PWR", "res": "R_SERIES", "load": "DEVICE", "gnd": "GND"},
        {"vcc": "SUPPLY", "res": "R1", "load": "LOAD1", "gnd": "GND"},
    ]
    for idx, (pack, prompt_style, layout_type) in enumerate(
        product(packs, PROMPT_STYLES, LAYOUT_VARIANTS["chain_horizontal"]), start=1
    ):
        components = [
            {"id": pack["vcc"], "type": "power", "role": "power_source"},
            {"id": pack["res"], "type": "resistor", "role": "series_resistor"},
            {"id": pack["load"], "type": "load", "role": "resistive_load"},
            {"id": pack["gnd"], "type": "ground", "role": "reference_ground"},
        ]
        yield {
            "template_id": f"resistor_load_{idx:03d}",
            "family": "resistor_load",
            "function": "串联电阻负载",
            "description": "电源经串联电阻驱动负载，是最简单的功率或限流链路之一。",
            "components": components,
            "connections": [
                [pack["vcc"], pack["res"]],
                [pack["res"], pack["load"]],
                [pack["load"], pack["gnd"]],
            ],
            "layout_type": layout_type,
            "prompt_template": build_prompt(prompt_style, "串联电阻负载", components),
        }


def generate_templates():
    families = [
        family_led_indicator,
        family_rc_lowpass,
        family_rc_highpass,
        family_lc_filter,
        family_power_decoupling,
        family_voltage_divider,
        family_pullup_button,
        family_pulldown_button,
        family_reverse_protection,
        family_halfwave_rectifier,
        family_bjt_led_driver,
        family_mosfet_load_switch,
        family_resistor_load,
    ]
    templates = []
    for family in families:
        templates.extend(list(family()))
    return templates


def main():
    templates = generate_templates()
    output_path = Path("思路文档") / "eda_templates_624.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(templates, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"generated {len(templates)} templates")
    print(output_path)


if __name__ == "__main__":
    main()
