from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CranberrySpecState(TypedDict):
    origin: str
    moisture_level: float
    pesticide_test_passed: bool
    approved: bool

def validate_quality(state: CranberrySpecState):
    state["approved"] = (state["moisture_level"] < 15.0) and state["pesticide_test_passed"]
    return state

workflow = StateGraph(CranberrySpecState)
workflow.add_node("validate", validate_quality)
workflow.set_entry_point("validate")
workflow.add_edge("validate", END)
graph = workflow.compile()