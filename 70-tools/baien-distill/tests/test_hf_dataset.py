"""Unit tests for the HF dataset adapter (no network — uses stub rows)."""

from __future__ import annotations

from baien_distill.adapters.hf_dataset import (
    DATASET_REGISTRY,
    DatasetSpec,
    _oasst_pairs,
    _row_to_example,
    parse_qwen_chat_text,
)


# ----- registry sanity ----------------------------------------------------

def test_registry_has_core_categories():
    for cat in ("Reasoning", "IFEval", "Multilingual", "General"):
        assert cat in DATASET_REGISTRY


def test_reasoning_has_opus_distill():
    specs = DATASET_REGISTRY["Reasoning"]
    ids = [s.id for s in specs]
    assert "lordx64/reasoning-distill-opus-4-7-max-sft" in ids


def test_multilingual_has_oasst_and_dolly_ja():
    specs = DATASET_REGISTRY["Multilingual"]
    ids = [s.id for s in specs]
    assert "OpenAssistant/oasst1" in ids
    assert "kunishou/databricks-dolly-15k-ja" in ids


def test_oasst_specs_have_ja_filter():
    for spec in DATASET_REGISTRY["Multilingual"]:
        if spec.id.startswith("OpenAssistant/oasst"):
            assert spec.lang_filter == "ja"
            assert spec.format == "oasst"


def test_dolly_ja_is_cc_by_sa_flagged():
    dolly = next(s for s in DATASET_REGISTRY["Multilingual"]
                 if s.id == "kunishou/databricks-dolly-15k-ja")
    assert dolly.license == "cc-by-sa-3.0"
    assert "ShareAlike" in dolly.note


# ----- qwen-text parser ---------------------------------------------------

def test_qwen_chat_parser_basic():
    s = ("<|im_start|>system\nYou are baien.<|im_end|>\n"
         "<|im_start|>user\nhello<|im_end|>\n"
         "<|im_start|>assistant\nhi there<|im_end|>")
    turns = parse_qwen_chat_text(s)
    assert len(turns) == 3
    assert turns[0]["role"] == "system"
    assert turns[1]["content"] == "hello"
    assert turns[2]["content"] == "hi there"


def test_qwen_chat_parser_with_think_block():
    s = ("<|im_start|>user\nq?<|im_end|>\n"
         "<|im_start|>assistant\n<think>step1\nstep2</think>\nfinal<|im_end|>")
    turns = parse_qwen_chat_text(s)
    assert len(turns) == 2
    assert "<think>" in turns[1]["content"]
    assert "final" in turns[1]["content"]


def test_qwen_chat_parser_empty():
    assert parse_qwen_chat_text("") == []
    assert parse_qwen_chat_text("no envelope here") == []


# ----- row-to-example adapters --------------------------------------------

def test_alpaca_row_with_input():
    spec = DatasetSpec(id="x/y", license="apache-2.0", format="alpaca")
    row = {"instruction": "Translate", "input": "Hello", "output": "こんにちは"}
    ex = _row_to_example(row, spec, "Multilingual")
    assert ex is not None
    assert "Translate" in ex.prompt
    assert "Hello" in ex.prompt
    assert ex.response == "こんにちは"
    assert ex.teacher_model == "hf:x/y"


def test_alpaca_row_without_input():
    spec = DatasetSpec(id="x/y", license="apache-2.0", format="alpaca")
    row = {"instruction": "Say hi", "input": "", "output": "hi"}
    ex = _row_to_example(row, spec, "General")
    assert ex is not None
    assert ex.prompt == "Say hi"


def test_alpaca_row_missing_output_dropped():
    spec = DatasetSpec(id="x/y", license="apache-2.0", format="alpaca")
    row = {"instruction": "Foo", "input": "", "output": ""}
    assert _row_to_example(row, spec, "General") is None


def test_qwen_text_row_extracts_last_pair():
    spec = DatasetSpec(id="x/y", license="apache-2.0", format="qwen-text")
    row = {"text": ("<|im_start|>user\nq1<|im_end|>\n"
                    "<|im_start|>assistant\nr1<|im_end|>\n"
                    "<|im_start|>user\nq2<|im_end|>\n"
                    "<|im_start|>assistant\nr2<|im_end|>")}
    ex = _row_to_example(row, spec, "Reasoning")
    assert ex is not None
    assert ex.prompt == "q2"
    assert ex.response == "r2"


def test_qwen_text_row_no_pair_dropped():
    spec = DatasetSpec(id="x/y", license="apache-2.0", format="qwen-text")
    row = {"text": "<|im_start|>system\nsetup<|im_end|>"}
    assert _row_to_example(row, spec, "Reasoning") is None


# ----- oasst tree walker (no network) -------------------------------------

def test_oasst_pair_extraction_with_lang_filter():
    spec = DatasetSpec(id="OpenAssistant/oasst1", license="apache-2.0",
                       format="oasst", lang_filter="ja")
    rows = [
        {"message_id": "p1", "parent_id": None,
         "role": "prompter", "lang": "ja", "text": "日本の首都は?"},
        {"message_id": "a1", "parent_id": "p1",
         "role": "assistant", "lang": "ja", "text": "東京です。", "rank": 0},
        {"message_id": "a2", "parent_id": "p1",
         "role": "assistant", "lang": "ja", "text": "京都です。", "rank": 3},
        # English row should be filtered out
        {"message_id": "p2", "parent_id": None,
         "role": "prompter", "lang": "en", "text": "What's UTC?"},
        {"message_id": "a3", "parent_id": "p2",
         "role": "assistant", "lang": "en", "text": "Coordinated Universal Time."},
    ]
    pairs = list(_oasst_pairs(rows, spec, "Multilingual", limit=None))
    assert len(pairs) == 1
    assert pairs[0].prompt == "日本の首都は?"
    # picked the lower-rank-number (better) reply
    assert pairs[0].response == "東京です。"
    assert pairs[0].category == "Multilingual"


def test_oasst_no_assistant_dropped():
    spec = DatasetSpec(id="o/y", license="apache-2.0",
                       format="oasst", lang_filter="ja")
    rows = [{"message_id": "p1", "parent_id": None,
             "role": "prompter", "lang": "ja", "text": "lone prompter"}]
    assert list(_oasst_pairs(rows, spec, "Multilingual", limit=None)) == []


def test_oasst_limit_respected():
    spec = DatasetSpec(id="o/y", license="apache-2.0",
                       format="oasst", lang_filter="ja")
    rows = []
    for i in range(5):
        rows.append({"message_id": f"p{i}", "parent_id": None,
                     "role": "prompter", "lang": "ja", "text": f"q{i}"})
        rows.append({"message_id": f"a{i}", "parent_id": f"p{i}",
                     "role": "assistant", "lang": "ja", "text": f"r{i}", "rank": 0})
    pairs = list(_oasst_pairs(rows, spec, "Multilingual", limit=3))
    assert len(pairs) == 3
