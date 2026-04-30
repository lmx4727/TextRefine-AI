from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from text_refine_ai.schemas import RefineResult


def write_outputs(
    result: RefineResult,
    output_dir: Path,
    timestamp: datetime | None = None,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = (timestamp or datetime.now()).strftime("%Y%m%d-%H%M%S")
    mode = result.data.mode
    markdown_path = output_dir / f"{stamp}_{mode}.md"
    json_path = output_dir / f"{stamp}_{mode}.json"

    markdown_path.write_text(result.markdown, encoding="utf-8")
    json_path.write_text(
        json.dumps(result.data.to_json_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return markdown_path, json_path
