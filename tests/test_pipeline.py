from text_refine_ai.llm import MockLLMClient
from text_refine_ai.pipeline import TextRefinePipeline
from text_refine_ai.prompts import build_generation_prompt
from text_refine_ai.schemas import RefineRequest


def test_build_generation_prompt_mentions_mode_and_chinese_output():
    prompt = build_generation_prompt(
        mode="minutes",
        text="我们讨论上线计划。",
        chunk_index=1,
        total_chunks=2,
    )

    assert "会议纪要" in prompt
    assert "默认使用中文" in prompt
    assert "JSON" in prompt


def test_pipeline_returns_stable_json_shape_for_all_modes():
    pipeline = TextRefinePipeline(llm_client=MockLLMClient())

    for mode in ["dialogue", "minutes", "report"]:
        request = RefineRequest(
            raw_text="嗯我们讨论上线计划。张三负责测试。",
            mode=mode,
            refine_rounds=1,
            provider="mock",
        )

        result = pipeline.run(request)

        assert result.data.mode == mode
        assert result.data.title
        assert result.data.summary
        assert result.data.sections
        assert result.data.metadata["chunks"] == 1
        assert result.data.metadata["refine_rounds"] == 1
        assert result.data.metadata["provider"] == "mock"
        assert result.markdown.startswith("# ")

        if mode == "dialogue":
            assert result.data.dialogue_turns
        else:
            assert result.data.action_items


def test_pipeline_does_not_emit_raw_input_verbatim():
    raw_text = "嗯我们开会讨论一个非常敏感的原始输入句子。"
    pipeline = TextRefinePipeline(llm_client=MockLLMClient())

    result = pipeline.run(
        RefineRequest(
            raw_text=raw_text,
            mode="minutes",
            refine_rounds=0,
            provider="mock",
        )
    )

    assert raw_text not in result.markdown
    assert raw_text not in str(result.data.to_json_dict())
