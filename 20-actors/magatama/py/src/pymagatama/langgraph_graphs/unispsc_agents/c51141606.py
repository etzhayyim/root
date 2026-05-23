from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    purity: float
    compliance_docs: List[str]
    status: str

def validate_purity(state: ProcurementState):
    return {"status": "validated" if state['purity'] >= 99.0 else "rejected"}

def check_compliance(state: ProcurementState):
    required = {"gmp", "coa"}
    if required.issubset(set(state['compliance_docs'])):
        return {"status": "compliant"}
    return {"status": "missing_docs"}

graph = StateGraph(ProcurementState)
graph.add_node("validate_purity", validate_purity)
graph.add_node("check_compliance", check_compliance)
graph.set_entry_point("validate_purity")
graph.add_edge("validate_purity", "check_compliance")
graph.add_edge("check_compliance", END)
graph = graph.compile()
