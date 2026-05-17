"""Pure tests for kaisya_member_assistant LangGraph + primitive."""

from __future__ import annotations

import asyncio
import unittest


def _make_state(**kw):
    from pymagatama.langgraph_graphs.kaisya_member_assistant import MemberChatState
    s: MemberChatState = {}  # type: ignore[assignment]
    s.update(kw)
    return s


class TestUpnResolution(unittest.TestCase):
    def setUp(self):
        import pymagatama.langgraph_graphs.kaisya_member_assistant as mod
        self._orig_q = mod._db_query
        mod._db_query = lambda *a, **k: [{"display_name": "Test User", "title": "engineer", "department": "eng"}]

    def tearDown(self):
        import pymagatama.langgraph_graphs.kaisya_member_assistant as mod
        mod._db_query = self._orig_q

    def test_known_upn_resolves(self):
        from pymagatama.langgraph_graphs.kaisya_member_assistant import resolve_member
        out = resolve_member(_make_state(user_upn="f-tanaka@gftd.co"))
        self.assertEqual(out["member_did"], "did:web:f-tanaka.etzhayyim.com")
        self.assertTrue(out["ok"])

    def test_lowercase_upn(self):
        from pymagatama.langgraph_graphs.kaisya_member_assistant import resolve_member
        out = resolve_member(_make_state(user_upn="K-Bakshi@gftd.co"))
        self.assertEqual(out["member_did"], "did:web:k-bakshi.etzhayyim.com")

    def test_unknown_upn_denied(self):
        from pymagatama.langgraph_graphs.kaisya_member_assistant import resolve_member
        out = resolve_member(_make_state(user_upn="random@example.com"))
        self.assertEqual(out["route"], "denied")
        self.assertFalse(out["ok"])

    def test_dot_separator_alias(self):
        from pymagatama.langgraph_graphs.kaisya_member_assistant import resolve_member
        out = resolve_member(_make_state(user_upn="y.nishino@gftd.co"))
        self.assertEqual(out["member_did"], "did:web:y-nishino.etzhayyim.com")


class TestRouterFunctions(unittest.TestCase):
    def test_after_resolve_denied(self):
        from pymagatama.langgraph_graphs.kaisya_member_assistant import _after_resolve
        self.assertEqual(_after_resolve(_make_state(route="denied")), "denied")

    def test_after_resolve_ok(self):
        from pymagatama.langgraph_graphs.kaisya_member_assistant import _after_resolve
        self.assertEqual(_after_resolve(_make_state(member_did="did:web:x.etzhayyim.com")), "load_context")

    def test_route_after_supervisor_default(self):
        from pymagatama.langgraph_graphs.kaisya_member_assistant import _route_after_supervisor
        self.assertEqual(_route_after_supervisor(_make_state()), "direct_reply")

    def test_route_after_supervisor_known(self):
        from pymagatama.langgraph_graphs.kaisya_member_assistant import _route_after_supervisor
        for r in ("company_ops", "lawfirm_marketing", "lawfirm_sales", "direct_reply", "escalate"):
            self.assertEqual(_route_after_supervisor(_make_state(route=r)), r)


class TestUpnToDidTable(unittest.TestCase):
    def test_all_known_members_present(self):
        from pymagatama.langgraph_graphs.kaisya_member_assistant import _UPN_TO_DID
        for upn in ("j-kawasaki@gftd.co", "a-nakamura@gftd.co", "k-bakshi@gftd.co",
                    "t-chikada@gftd.co", "f-tanaka@gftd.co", "y-nishino@gftd.co",
                    "t-ichihara@gftd.co", "k-takahashi@gftd.co", "n-takahashi@gftd.co"):
            self.assertIn(upn, _UPN_TO_DID, f"missing UPN: {upn}")


class TestGraphStructure(unittest.TestCase):
    def setUp(self):
        import pymagatama.langgraph_graphs.kaisya_member_assistant as mod
        self._orig_chat = mod._llm_chat
        self._orig_json = mod._llm_json
        self._orig_q = mod._db_query
        self._orig_audit = mod._db_insert_audit
        mod._llm_chat = lambda *a, **k: "stub reply"
        mod._llm_json = lambda *a, **k: {"route": "direct_reply", "reason": "stub"}
        mod._db_query = lambda *a, **k: []
        mod._db_insert_audit = lambda *a, **k: None

    def tearDown(self):
        import pymagatama.langgraph_graphs.kaisya_member_assistant as mod
        mod._llm_chat = self._orig_chat
        mod._llm_json = self._orig_json
        mod._db_query = self._orig_q
        mod._db_insert_audit = self._orig_audit

    def test_graph_compiles(self):
        from pymagatama.langgraph_graphs.kaisya_member_assistant import build_graph
        g = build_graph()
        self.assertIsNotNone(g)

    def test_graph_has_nodes(self):
        from pymagatama.langgraph_graphs.kaisya_member_assistant import build_graph
        g = build_graph()
        nodes = list(g.nodes)
        for expected in ("resolve_member", "load_context", "supervisor",
                         "company_ops", "lawfirm_marketing", "lawfirm_sales",
                         "direct_reply", "emit_audit"):
            self.assertIn(expected, nodes, f"missing node {expected!r}")


class TestPrimitive(unittest.TestCase):
    def test_module_importable(self):
        import pymagatama.primitives.kaisya_member as p
        self.assertTrue(callable(p.task_kaisya_member_chat))

    def test_register_requires_zeebe_worker(self):
        import pymagatama.primitives.kaisya_member as p
        p.register("not_a_worker")  # silent no-op

    def test_missing_inputs_rejected(self):
        from pymagatama.primitives.kaisya_member import task_kaisya_member_chat
        out = asyncio.run(task_kaisya_member_chat(user_upn="", user_message=""))
        self.assertFalse(out["ok"])


if __name__ == "__main__":
    unittest.main()
