# EDAGenerate

EDAGenerate 是一个面向演示场景的小型 EDA 生成项目。  
项目的核心流程是：

1. 输入中文提示词。
2. 用微调后的 `mT5-small` 模型生成结构化电路字典。
3. 解析模型输出。
4. 根据节点和连线信息渲染出 EDA 原理图图片。

当前仓库已经包含：

- 模板化生成的数据集和说明文档
- 训练后的本地推理脚本
- 原理图渲染脚本
- 可直接演示的 Notebook

## 环境准备

建议使用 Python 3.10 或 3.11。

先安装依赖：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

如果你不使用国内镜像，也可以去掉 `-i` 参数。

## 1. 先拉取模型权重

本项目默认使用已经上传到 Hugging Face 的模型：

- `wzmmmm/mt5-eda-generate`

先执行：

```bash
python .\scripts\download_hf_model.py
```

执行完成后，模型会下载到本地目录：

```text
models/mt5-eda-generate
```

如果你需要指定别的模型仓库，可以这样：

```bash
python .\scripts\download_hf_model.py --repo-id your-name/your-model
```

## 2. 先测试模型是否能正常推理

建议先用命令行脚本确认模型能否被正常加载、推理、解析。

运行：

```bash
python .\scripts\run_inference_cpu.py
```

这个脚本会：

- 从本地加载模型
- 输入一条默认中文提示词
- 输出模型原始结果
- 尝试提取 JSON
- 做基础结构校验

如果你想测试自定义提示词，可以这样：

```bash
python .\scripts\run_inference_cpu.py --prompt "设计一个完成RC低通滤波功能的 EDA 原理图，包含输入 VIN、电阻 R1、输出 OUT、电容 C1 和 接地 GND。请给出所有节点的坐标以及节点之间的连接关系。"
```

如果脚本输出里出现类似这些内容，就说明模型推理已经基本正常：

```text
=== PARSE STATUS ===
json parsed successfully
validation: ok
```

## 3. 使用 Notebook 进行完整演示

当命令行推理测试通过后，再打开：

- `mt5_notebook_interactive_demo.ipynb`

这个 Notebook 用于完整演示以下流程：

1. 加载本地模型
2. 输入提示词或选择 20 条备选提示词
3. 执行模型推理
4. 解析模型输出 JSON
5. 调用外部渲染脚本生成图片
6. 直接在 Notebook 中展示生成的 EDA 图

### Notebook 中的建议使用顺序

1. 先运行依赖导入和路径设置相关单元。
2. 再运行模型加载单元。
3. 再输入你的提示词，或者从备选提示词中选择一条。
4. 最后运行推理与渲染单元。

## 4. 图片生成依赖的脚本

Notebook 里的图片生成并不是手写在单元里的，而是调用仓库中的脚本：

- `scripts/render_schematic.py`
- `scripts/render_from_prediction.py`

它们分别负责：

- 把标准化电路字典渲染成图片
- 把模型输出转换成渲染器所需格式

目前图片中已经支持中文节点说明，例如：

- `输入`
- `输出`
- `电阻`
- `电容`
- `接地`

这样即使不了解元件英文缩写，也能直接看懂生成结果。

## 5. 推荐测试流程

推荐按照下面顺序测试：

1. 安装依赖

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

2. 拉取模型

```bash
python .\scripts\download_hf_model.py
```

3. 测试本地 CPU 推理

```bash
python .\scripts\run_inference_cpu.py
```

4. 打开 Notebook 做完整演示

```text
mt5_notebook_interactive_demo.ipynb
```

## 6. 仓库中的关键文件

- `scripts/download_hf_model.py`
  下载 Hugging Face 模型到本地

- `scripts/run_inference_cpu.py`
  使用本地 CPU 测试模型推理

- `scripts/render_schematic.py`
  根据结构化字典绘制原理图图片

- `scripts/render_from_prediction.py`
  将模型输出衔接到渲染流程

- `mt5_notebook_interactive_demo.ipynb`
  交互式演示 Notebook

- `思路文档/项目介绍与实现说明.pdf`
  项目实现思路和整体说明

## 7. 注意事项

- 请先安装依赖，再执行脚本。
- 首次拉取模型需要网络连接。
- 本地推理默认走 CPU，速度会比 GPU 慢。
- 如果 Notebook 修改了外部脚本但效果没变化，建议重启内核后重新运行。

## 8. 当前项目定位

这个仓库当前更偏“可展示的工程 Demo”，而不是完整工业级 EDA 系统。  
它重点验证的是：

- 中文提示词到结构化电路表示是否可行
- 小型模型在高质量合成数据上是否能学到稳定映射
- 模型输出是否能进一步转成清晰的原理图结果
