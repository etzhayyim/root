from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    temp_log: list
    is_compliant: bool

def validate_purity(state: ProcurementState):
    threshold = 99.5
    return {"is_compliant": state["purity_level"] >= threshold}

def check_gdp_compliance(state: ProcurementState):
    return {"is_compliant": state["is_compliant"] and all(t < 25 for t in state["temp_log"])}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_purity)
graph.add_node("gdp_check", check_gdp_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "gdp_check")
graph.add_edge("gdp_check", END)
compiled_graph = graph.compile()