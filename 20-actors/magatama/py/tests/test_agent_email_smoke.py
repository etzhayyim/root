from __future__ import annotations

from pymagatama import agent_email_smoke


def test_build_autonomous_email_plan_derives_sender() -> None:
    plan = agent_email_smoke.build_autonomous_email_plan(
        agent_did="did:web:kami-agent.gftd.ai",
        to="ops@example.com",
        subject="Ping",
        text="hello",
        authority_ref="capability://agent/email/outbound/smoke",
        policy_ref="policy://agent/autonomous-email-v1",
    )

    assert plan["dispatchAllowed"] is True
    assert plan["taskType"] == "mailer.sendEmail"
    assert plan["channelPayload"]["fromAddress"] == "kami-agent@gftd.ai"


def test_send_if_requested_does_not_send_without_live(monkeypatch) -> None:
    def fail_send_email(**kwargs):  # pragma: no cover - must not be called
        raise AssertionError("send_email must not run")

    monkeypatch.setattr("pymagatama.ingest.mailer.send_email", fail_send_email)

    plan = {"dispatchAllowed": True, "channelPayload": {"to": "ops@example.com"}}
    result = agent_email_smoke.send_if_requested(plan, live=False)

    assert result == {"live": False, "dispatchPlan": plan}
