from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WiperProcurementState(TypedDict):
    part_specs: dict
    validation_checks: List[str]
    approved: bool

def validate_blade_specs(state: WiperProcurementState):
    checks = []
    if "length" in state["part_specs"]:
        checks.append("Length Verified")
    return {"validation_checks": checks}

def approval_step(state: WiperProcurementState):
    is_approved = all(["Length Verified" in state["validation_checks"]])
    return {"approved": is_approved}

graph = StateGraph(WiperProcurementState)
graph.add_node("validate", validate_blade_specs)
graph.add_node("approve", approval_step)
graph.add_edge("validate", "approve")
graph.add_edge("approve", END)
graph.set_entry_point("validate")
graph = graph.compile()