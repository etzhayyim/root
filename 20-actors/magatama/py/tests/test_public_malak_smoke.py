from __future__ import annotations

from pymagatama import public_malak_smoke as smoke


def test_build_smoke_observation_is_synthetic_telegram() -> None:
    run_id, run, fetch_result = smoke.build_smoke_observation("public malak smoke", now=1778123456)

    assert run_id == "run-smoke-1778123456"
    assert run["platform"] == "telegram"
    assert run["query_kind"] == "search"
    assert run["query_value"] == "public malak smoke 1778123456"
    assert run["vertex_id"].endswith("/run-smoke-1778123456")
    assert fetch_result["httpStatus"] == 200
    assert "Public Malak smoke artifact" in fetch_result["text"]
    assert str(fetch_result["finalUrl"]).startswith("https://ads.telegram.org/")


def test_config_from_env_reads_expected_defaults(monkeypatch) -> None:
    monkeypatch.setenv("RW_URL", "postgresql://rw.example/db")
    monkeypatch.delenv("PUBLIC_MALAK_SMOKE_PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("PUBLIC_MALAK_SMOKE_DISPATCHER_URL", raising=False)
    monkeypatch.delenv("PUBLIC_MALAK_SMOKE_QUERY", raising=False)
    monkeypatch.delenv("DISPATCHER_INTERNAL_SECRET", raising=False)

    config = smoke.config_from_env()

    assert config.public_base_url == "https://public-malak.gftd.ai"
    assert config.dispatcher_url == "http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080"
    assert config.query_base == "public malak smoke"
    assert config.rw_url == "postgresql://rw.example/db"
    assert config.internal_trust == ""


def test_wait_for_artifact_sends_explicit_user_agent(monkeypatch) -> None:
    seen_headers: dict[str, str] = {}

    class FakeResponse:
        status = 200
        headers = {"x-artifact-store": "s3"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return b"artifact"

    def fake_urlopen(req, timeout=0):
        assert timeout == 30
        seen_headers.update(dict(req.header_items()))
        return FakeResponse()

    monkeypatch.setattr(smoke.urllib.request, "urlopen", fake_urlopen)

    out = smoke.wait_for_artifact(
        public_base_url="https://public-malak.gftd.ai",
        kind="html",
        cid="html-abc",
        timeout_sec=1,
        sleep_sec=0,
    )

    assert out == {"status": 200, "bytes": 8, "store": "s3"}
    assert seen_headers["User-agent"] == smoke.PUBLIC_USER_AGENT
    assert seen_headers["Accept"] == "*/*"


def test_run_smoke_orchestrates_paths(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        smoke.ads,
        "_write_observation",
        lambda run, fetch_result: {"creativeVertexId": "creative-1"},
    )
    monkeypatch.setattr(
        smoke,
        "wait_for_snapshot",
        lambda **kwargs: ("html-1", "har-1", "2026-05-07T00:00:00Z"),
    )
    monkeypatch.setattr(smoke, "wait_for_list_snapshots", lambda **kwargs: {"status": 200, "count": 1})
    monkeypatch.setattr(
        smoke,
        "wait_for_artifact",
        lambda kind, **kwargs: {"status": 200, "bytes": 10 if kind == "html" else 8, "store": "s3"},
    )

    out = smoke.run_smoke(
        smoke.SmokeConfig(
            public_base_url="https://public-malak.gftd.ai",
            dispatcher_url="http://dispatcher",
            query_base="public malak smoke",
            rw_url="postgresql://rw",
            sleep_sec=0,
        )
    )

    assert out["ok"] is True
    assert out["creativeVertexId"] == "creative-1"
    assert out["htmlCid"] == "html-1"
    assert out["harCid"] == "har-1"
    assert out["html"]["store"] == "s3"
    assert '"phase": "written"' in capsys.readouterr().out


def test_main_prints_final_json(monkeypatch, capsys) -> None:
    monkeypatch.setenv("RW_URL", "postgresql://rw")
    monkeypatch.setattr(
        smoke,
        "run_smoke",
        lambda config: {"ok": True, "publicBaseUrl": config.public_base_url},
    )

    smoke.main()

    assert capsys.readouterr().out.strip() == '{"ok": true, "publicBaseUrl": "https://public-malak.gftd.ai"}'
