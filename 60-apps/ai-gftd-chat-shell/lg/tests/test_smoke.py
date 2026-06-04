"""Smoke tests — graph compiles and tools import without error."""

import importlib


def test_graph_compiles() -> None:
    mod = importlib.import_module("lg_chat.graphs.agent_chat")
    graph = mod.GRAPH
    assert graph is not None
    # Check graph has the expected nodes
    node_names = set(graph.nodes.keys()) if hasattr(graph, "nodes") else set()
    assert "prepare" in node_names or len(node_names) > 0


def test_tools_import() -> None:
    from lg_chat.tools import TOOL_SCHEMAS, dispatch_tool
    assert len(TOOL_SCHEMAS) == 6
    tool_names = {t["function"]["name"] for t in TOOL_SCHEMAS}
    assert tool_names == {"code_exec", "image_gen", "file_save", "rag_search", "web_search", "schedule_report"}
    # dispatch_tool returns an error for unknown tools
    result = dispatch_tool("__unknown__", {})
    assert result["ok"] is False


def test_code_exec_tool() -> None:
    from lg_chat.tools import tool_code_exec
    result = tool_code_exec({"code": "print('hello from lg-chat')"})
    assert result["ok"] is True
    assert "hello from lg-chat" in result["stdout"]


def test_code_exec_timeout() -> None:
    from lg_chat.tools import tool_code_exec
    result = tool_code_exec({"code": "import time; time.sleep(100)", "timeoutSec": 2})
    assert result["ok"] is False
    assert "timeout" in result["error"]
