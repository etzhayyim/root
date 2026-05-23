from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    api_purity: float
    compliance_docs: bool
    storage_temp_ok: bool

def validate_purity(state: ProcurementState):
    return {"api_purity_validated": state['api_purity'] >= 99.0}

def check_compliance(state: ProcurementState):
    return {"ready_for_procurement": state['compliance_docs'] and state['storage_temp_ok']}

graph = StateGraph(ProcurementState)
graph.add_node("validate_api", validate_purity)
graph.add_node("check_compliance", check_compliance)
graph.set_entry_point("validate_api")
graph.add_edge("validate_api", "check_compliance")
graph.add_edge("check_compliance", END)
graph = graph.compile()
