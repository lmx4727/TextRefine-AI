# TextRefineAI

TextRefineAI 是一个基于大模型的文本结构化处理系统，用来把语音转写、聊天记录、草稿文档等混乱文本整理成可以直接使用的结构化内容。

它支持将原始文本转换为：

- 对话稿
- 会议纪要
- 报告初稿

项目提供两种使用方式：

- WebUI：适合可视化上传、配置和预览结果
- CLI：适合命令行批处理或快速测试

## 功能特性

- 上传 `.txt` / `.md` 文件
- 直接粘贴文本
- 支持三种输出模式：`dialogue`、`minutes`、`report`
- 支持 Markdown 和 JSON 双格式结果
- 支持 0 到 2 轮优化
- 支持 Mock 模型模式，方便无 API Key 测试
- 支持 OpenAI-compatible API，可接入真实大模型
- WebUI 采用接近 Apple 风格的简洁玻璃质感界面

## 环境要求

- Python 3.12+

项目主要依赖：

- Flask
- Click
- Pydantic
- HTTPX
- Pytest

## 安装

在项目根目录执行：

```powershell
python -m pip install --no-build-isolation -e ".[dev]"
```

如果不需要运行测试，也可以执行：

```powershell
python -m pip install --no-build-isolation -e .
```

## 启动 WebUI

在项目根目录执行：

```powershell
textrefine-web
```

默认访问地址：

```text
http://127.0.0.1:7860
```

如果想修改监听地址或端口：

```powershell
$env:TEXTREFINE_WEB_HOST="127.0.0.1"
$env:TEXTREFINE_WEB_PORT="7860"
textrefine-web
```

WebUI 支持：

- 上传文件
- 粘贴文本
- 选择输出类型
- 选择 Mock / Real 模型
- 填写真实模型配置
- 调整优化轮数
- 查看 Markdown / JSON
- 复制 Markdown
- 下载 JSON

## 使用 CLI

### 使用 Mock 模型测试

```powershell
textrefine run --text "嗯我们今天讨论上线计划。张三负责测试。" --mode minutes --provider mock
```

读取文件：

```powershell
textrefine run --input test.txt --mode minutes --provider mock
```

输出结果默认保存在：

```text
outputs/
```

每次转换会生成两个文件：

```text
YYYYMMDD-HHMMSS_minutes.md
YYYYMMDD-HHMMSS_minutes.json
```

### 输出模式

```text
dialogue   对话稿
minutes    会议纪要
report     报告初稿
```

### 优化轮数

```powershell
textrefine run --input test.txt --mode report --provider mock --refine-rounds 2
```

`--refine-rounds` 支持：

```text
0
1
2
```

默认值是 `1`。

## 配置真实大模型

真实模型模式使用 OpenAI-compatible HTTP API。

需要配置：

```powershell
$env:TEXTREFINE_API_KEY="你的 API Key"
$env:TEXTREFINE_BASE_URL="https://api.openai.com/v1"
$env:TEXTREFINE_MODEL="你的模型名"
```

然后运行：

```powershell
textrefine run --input test.txt --mode minutes --provider real
```

WebUI 中也可以直接在页面里填写：

- `TEXTREFINE_API_KEY`
- `TEXTREFINE_BASE_URL`
- `TEXTREFINE_MODEL`

## 项目结构

```text
TextRefineAI/
  src/
    text_refine_ai/
      cli.py              # CLI 入口
      web.py              # WebUI 后端入口
      pipeline.py         # 核心流水线
      processing.py       # 文本预处理与分块
      prompts.py          # Prompt 模板
      llm.py              # Mock / Real 模型适配
      renderer.py         # Markdown 渲染
      schemas.py          # 数据结构
      templates/          # WebUI HTML
      static/             # WebUI CSS / JS
  tests/                  # 自动化测试
  outputs/                # 默认输出目录
  memory/                 # 项目记忆与计划文件
  pyproject.toml
```

## 运行测试

```powershell
python -m pytest -q
```

当前测试覆盖：

- 文本预处理
- 长文本分块
- Prompt 生成
- Pipeline 结构化输出
- CLI 输入与错误处理
- WebUI 页面和接口

## 设计思路

TextRefineAI 使用轻量级多阶段 Agent 流水线：

```text
输入文本
  ↓
预处理
  ↓
长文本分块
  ↓
结构化生成
  ↓
多轮优化
  ↓
Markdown / JSON 输出
```

第一版没有引入复杂 Agent 框架，核心目标是保持系统简单、可测试、可扩展。

## 隐私说明

默认情况下，系统只保存最终 Markdown 和 JSON 结果。

CLI 和 WebUI 不会主动保存完整原文或中间 Prompt。使用真实模型时，文本会发送到你配置的模型服务，请根据实际 API 服务的隐私政策自行判断是否适合处理敏感文本。
