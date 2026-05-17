from typing import TypedDict
from langgraph.graph import StateGraph, END
class JuiceState(TypedDict):
    brix: float
    safety_check: bool
def validate_quality(state: JuiceState):
    return {"safety_check": state["brix"] > 10.0}
def workflow():
    graph = StateGraph(JuiceState)
    graph.add_node("quality_check", validate_quality)
    graph.set_entry_point("quality_check")
    graph.add_edge("quality_check", END)
    return graph.compile()
graph = workflow()