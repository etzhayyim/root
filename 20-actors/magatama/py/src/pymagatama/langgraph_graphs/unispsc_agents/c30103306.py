from typing import TypedDict
from langgraph.graph import StateGraph, END

class ZincProcurementState(TypedDict):
    purity_level: float
    impurity_report: dict
    is_approved: bool

def validate_quality(state: ZincProcurementState):
    if state['purity_level'] >= 99.9:
        state['is_approved'] = True
    else:
        state['is_approved'] = False
    return state

def log_result(state: ZincProcurementState):
    print(f"Procurement status: {state['is_approved']}")
    return state

graph = StateGraph(ZincProcurementState)
graph.add_node("validate", validate_quality)
graph.add_node("logger", log_result)
graph.add_edge("validate", "logger")
graph.add_edge("logger", END)
graph.set_entry_point("validate")