import json
from pathlib import Path

from typer.testing import CliRunner

from text_refine_ai.cli import app


runner = CliRunner()


def test_cli_text_input_writes_markdown_and_json(tmp_path: Path):
    raw_text = "嗯我们开会讨论上线。张三负责测试。"

    result = runner.invoke(
        app,
        [
            "run",
            "--text",
            raw_text,
            "--mode",
            "minutes",
            "--provider",
            "mock",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    markdown_files = list(tmp_path.glob("*_minutes.md"))
    json_files = list(tmp_path.glob("*_minutes.json"))
    assert len(markdown_files) == 1
    assert len(json_files) == 1

    data = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert data["mode"] == "minutes"
    assert data["metadata"]["provider"] == "mock"
    assert raw_text not in markdown_files[0].read_text(encoding="utf-8")
    assert raw_text not in json_files[0].read_text(encoding="utf-8")


def test_cli_file_input_supports_dialogue_mode(tmp_path: Path):
    input_file = tmp_path / "input.txt"
    input_file.write_text("嗯A问项目进展。B说今天完成测试。", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "run",
            "--input",
            str(input_file),
            "--mode",
            "dialogue",
            "--provider",
            "mock",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(next(tmp_path.glob("*_dialogue.json")).read_text(encoding="utf-8"))
    assert data["mode"] == "dialogue"
    assert data["dialogue_turns"]


def test_cli_rejects_invalid_refine_rounds(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "run",
            "--text",
            "有效输入",
            "--mode",
            "minutes",
            "--provider",
            "mock",
            "--refine-rounds",
            "3",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "refine" in result.output.lower()


def test_cli_rejects_empty_input(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "run",
            "--text",
            "   ",
            "--mode",
            "minutes",
            "--provider",
            "mock",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "输入不能为空" in result.output


def test_cli_rejects_missing_file(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "run",
            "--input",
            str(tmp_path / "missing.txt"),
            "--mode",
            "minutes",
            "--provider",
            "mock",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "文件不存在" in result.output


def test_cli_real_provider_requires_environment(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("TEXTREFINE_API_KEY", raising=False)
    monkeypatch.delenv("TEXTREFINE_BASE_URL", raising=False)
    monkeypatch.delenv("TEXTREFINE_MODEL", raising=False)

    result = runner.invoke(
        app,
        [
            "run",
            "--text",
            "有效输入",
            "--mode",
            "minutes",
            "--provider",
            "real",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "TEXTREFINE_API_KEY" in result.output
