from io import BytesIO

from text_refine_ai.web import create_app


def test_web_index_renders_upload_and_config_controls():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "TextRefineAI" in html
    assert "上传文件" in html
    assert "TEXTREFINE_API_KEY" in html
    assert "refineRounds" in html


def test_web_json_refine_returns_markdown_and_data():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/refine",
        json={
            "text": "嗯我们讨论上线计划。张三负责测试。",
            "mode": "minutes",
            "provider": "mock",
            "refine_rounds": 1,
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"]["mode"] == "minutes"
    assert payload["markdown"].startswith("# ")
    assert payload["data"]["metadata"]["provider"] == "mock"


def test_web_file_upload_refines_text_file():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/refine",
        data={
            "file": (BytesIO("嗯A问进度。B说完成测试。".encode("utf-8")), "input.txt"),
            "mode": "dialogue",
            "provider": "mock",
            "refine_rounds": "0",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"]["mode"] == "dialogue"
    assert payload["data"]["dialogue_turns"]


def test_web_rejects_empty_input():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/api/refine",
        json={
            "text": "   ",
            "mode": "minutes",
            "provider": "mock",
            "refine_rounds": 1,
        },
    )

    assert response.status_code == 400
    assert "输入不能为空" in response.get_json()["error"]
