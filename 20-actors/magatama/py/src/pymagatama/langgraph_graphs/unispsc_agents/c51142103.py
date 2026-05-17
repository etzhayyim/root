from typing import TypedDict
from langgraph.graph import StateGraph, END

class DiclofenacState(TypedDict):
    purity: float
    gmp_certified: bool
    compliance_report: str

def validate_purity(state: DiclofenacState):
    return {"compliance_report": "Approved" if state["purity"] >= 99.0 else "Rejected"}

def check_certification(state: DiclofenacState):
    return {"compliance_report": "Requires Audit" if not state["gmp_certified"] else state["compliance_report"]}

graph = StateGraph(DiclofenacState)
graph.add_node("validate_purity", validate_purity)
graph.add_node("check_certification", check_certification)
graph.add_edge("validate_purity", "check_certification")
graph.add_edge("check_certification", END)
graph.set_entry_point("validate_purity")
graph = graph.compile()