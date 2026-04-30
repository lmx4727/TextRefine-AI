from text_refine_ai.processing import preprocess_text, split_into_chunks


def test_preprocess_removes_fillers_duplicates_and_normalizes_text():
    raw = "嗯我们今天讨论产品。产品。就是需要推进。\n\n啊需要推进。"

    processed = preprocess_text(raw)

    assert processed == "我们今天讨论产品。需要推进。"


def test_split_into_chunks_keeps_short_text_as_single_chunk():
    assert split_into_chunks("短文本", max_chars=20, overlap=5) == ["短文本"]


def test_split_into_chunks_uses_character_overlap_for_long_text():
    text = "0123456789" * 10

    chunks = split_into_chunks(text, max_chars=30, overlap=5)

    assert len(chunks) == 4
    assert chunks[1].startswith(chunks[0][-5:])
    assert chunks[2].startswith(chunks[1][-5:])
