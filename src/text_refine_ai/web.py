from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

from text_refine_ai.exceptions import InputError, ProviderConfigurationError, ProviderResponseError
from text_refine_ai.llm import MockLLMClient, OpenAICompatibleClient
from text_refine_ai.pipeline import TextRefinePipeline
from text_refine_ai.schemas import RefineRequest


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.post("/api/refine")
    def refine():
        try:
            payload = _read_payload()
            text = payload["text"]
            if not text.strip():
                raise InputError("输入不能为空")

            provider = payload["provider"]
            request_model = RefineRequest(
                raw_text=text,
                mode=payload["mode"],
                refine_rounds=payload["refine_rounds"],
                provider=provider,
            )
            pipeline = TextRefinePipeline(llm_client=_create_web_client(provider, payload))
            result = pipeline.run(request_model)
            return jsonify({"markdown": result.markdown, "data": result.data.to_json_dict()})
        except (InputError, ProviderConfigurationError, ProviderResponseError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400

    return app


def main() -> None:
    host = os.getenv("TEXTREFINE_WEB_HOST", "127.0.0.1")
    port = int(os.getenv("TEXTREFINE_WEB_PORT", "7860"))
    create_app().run(host=host, port=port, debug=False)


def _read_payload() -> dict[str, Any]:
    if request.is_json:
        data = request.get_json(silent=True) or {}
        return {
            "text": str(data.get("text") or ""),
            "mode": str(data.get("mode") or "minutes"),
            "provider": str(data.get("provider") or "mock"),
            "refine_rounds": int(data.get("refine_rounds") or 0),
            "api_key": str(data.get("api_key") or ""),
            "base_url": str(data.get("base_url") or ""),
            "model": str(data.get("model") or ""),
        }

    text = request.form.get("text", "")
    uploaded = request.files.get("file")
    if uploaded and uploaded.filename:
        text = uploaded.read().decode("utf-8")

    return {
        "text": text,
        "mode": request.form.get("mode", "minutes"),
        "provider": request.form.get("provider", "mock"),
        "refine_rounds": int(request.form.get("refine_rounds", "0")),
        "api_key": request.form.get("api_key", ""),
        "base_url": request.form.get("base_url", ""),
        "model": request.form.get("model", ""),
    }


def _create_web_client(provider: str, payload: dict[str, Any]):
    if provider == "mock":
        return MockLLMClient()
    if provider != "real":
        raise ProviderConfigurationError("provider 只能是 mock 或 real")

    api_key = payload.get("api_key") or os.getenv("TEXTREFINE_API_KEY", "")
    base_url = payload.get("base_url") or os.getenv("TEXTREFINE_BASE_URL", "")
    model = payload.get("model") or os.getenv("TEXTREFINE_MODEL", "")
    missing = [
        name
        for name, value in {
            "TEXTREFINE_API_KEY": api_key,
            "TEXTREFINE_BASE_URL": base_url,
            "TEXTREFINE_MODEL": model,
        }.items()
        if not value
    ]
    if missing:
        raise ProviderConfigurationError(f"缺少真实模型配置: {', '.join(missing)}")
    return OpenAICompatibleClient(api_key=api_key, base_url=base_url, model=model)


if __name__ == "__main__":
    main()
