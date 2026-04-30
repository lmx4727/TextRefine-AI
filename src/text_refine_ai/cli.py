from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from text_refine_ai.exceptions import InputError, ProviderConfigurationError, ProviderResponseError
from text_refine_ai.io import write_outputs
from text_refine_ai.llm import create_llm_client
from text_refine_ai.pipeline import TextRefinePipeline
from text_refine_ai.schemas import OutputMode, ProviderName, RefineRequest

app = typer.Typer(help="TextRefineAI: 将混乱文本整理为结构化 Markdown 和 JSON。")

VALID_MODES = {"dialogue", "minutes", "report"}
VALID_PROVIDERS = {"mock", "real"}


@app.command()
def run(
    input_path: Optional[Path] = typer.Option(None, "--input", "-i", help="输入 txt/md 文件路径。"),
    text: Optional[str] = typer.Option(None, "--text", "-t", help="直接传入待整理文本。"),
    mode: str = typer.Option("minutes", "--mode", help="输出模式: dialogue|minutes|report。"),
    refine_rounds: int = typer.Option(1, "--refine-rounds", help="优化轮数: 0 到 2。"),
    provider: str = typer.Option("real", "--provider", help="模型 provider: mock|real。"),
    output_dir: Path = typer.Option(Path("outputs"), "--output-dir", help="输出目录。"),
) -> None:
    try:
        raw_text = _read_input(input_path=input_path, text=text)
        request = RefineRequest(
            raw_text=raw_text,
            mode=_validate_mode(mode),
            refine_rounds=_validate_refine_rounds(refine_rounds),
            provider=_validate_provider(provider),
        )
        llm_client = create_llm_client(request.provider)
        result = TextRefinePipeline(llm_client=llm_client).run(request)
        markdown_path, json_path = write_outputs(result, output_dir)
    except (InputError, ProviderConfigurationError, ProviderResponseError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Markdown: {markdown_path}")
    typer.echo(f"JSON: {json_path}")


def main() -> None:
    app()


def _read_input(input_path: Path | None, text: str | None) -> str:
    if input_path and text is not None:
        raise InputError("请只使用 --input 或 --text 其中一种输入方式")
    if input_path:
        if not input_path.exists():
            raise InputError(f"文件不存在: {input_path}")
        if not input_path.is_file():
            raise InputError(f"不是可读取文件: {input_path}")
        return input_path.read_text(encoding="utf-8")
    if text is not None:
        if not text.strip():
            raise InputError("输入不能为空")
        return text
    raise InputError("请通过 --input 或 --text 提供输入")


def _validate_mode(mode: str) -> OutputMode:
    if mode not in VALID_MODES:
        raise ValueError("mode 只能是 dialogue、minutes 或 report")
    return mode  # type: ignore[return-value]


def _validate_provider(provider: str) -> ProviderName:
    if provider not in VALID_PROVIDERS:
        raise ValueError("provider 只能是 mock 或 real")
    return provider  # type: ignore[return-value]


def _validate_refine_rounds(refine_rounds: int) -> int:
    if refine_rounds < 0 or refine_rounds > 2:
        raise ValueError("refine-rounds 只能是 0 到 2")
    return refine_rounds
